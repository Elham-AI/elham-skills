import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "elham", Path(__file__).resolve().parents[1] / "skills/elham/scripts/elham.py")
client = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(client)


class Response(io.BytesIO):
    def __init__(self, data, headers=None, status=200):
        super().__init__(json.dumps(data).encode() if not isinstance(data, bytes) else data)
        self.headers = headers or {"Content-Type": "application/json"}
        self.status = status


class Transport:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []

    def open(self, request, timeout):
        self.requests.append(request)
        result = next(self.responses)
        if isinstance(result, Exception):
            raise result
        return result


def rpc(number, result, headers=None):
    return Response({"jsonrpc": "2.0", "id": number, "result": result}, headers)


class ClientTests(unittest.TestCase):
    def test_initialize_discovery_pagination_and_call(self):
        transport = Transport([
            rpc(1, {"protocolVersion": client.PROTOCOL}, {"Mcp-Session-Id": "session-1"}),
            Response(b"", status=202),
            rpc(3, {"tools": [{"name": "one"}], "nextCursor": "next"}),
            rpc(4, {"tools": [{"name": "two"}]}),
            rpc(5, {"content": [{"type": "text", "text": '{"success": true}'}]})])
        connection = client.Client({"Authorization": "Bearer example"})
        connection.opener = transport
        connection.initialize()
        self.assertEqual([t["name"] for t in connection.tools()], ["one", "two"])
        self.assertTrue(connection.call("one", {})["success"])
        self.assertEqual(transport.requests[-1].get_header("Mcp-session-id"), "session-1")
        self.assertEqual(json.loads(transport.requests[3].data)["params"], {"cursor": "next"})
        self.assertNotIn("id", json.loads(transport.requests[1].data))

    def test_sse_skips_notification_and_reads_multiline_result(self):
        stream = io.BytesIO(b'data: {"method":"notify"}\n\ndata: {"jsonrpc":"2.0",\n'
                            b'data: "id":7,"result":{}}\n\n')
        self.assertEqual(client.Client.read_sse(stream, 7)["result"], {})

    def test_application_failure_exits_nonzero_even_on_http_success(self):
        with patch.object(client, "load_auth", return_value={"Authorization": "Bearer test"}), \
             patch.object(client.Client, "initialize"), \
             patch.object(client.Client, "call", return_value={"success": False, "status_code": 422}), \
             patch("sys.argv", ["elham", "call", "predict"]), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(client.main(), 1)

    def test_structured_content_and_tool_error(self):
        self.assertEqual(client.unwrap({"structuredContent": {"success": True}}), {"success": True})
        with self.assertRaises(client.ClientError):
            client.unwrap({"isError": True, "content": []})

    def test_describe_preserves_secret_field_schemas(self):
        schema = {"name": "create_db_connection", "inputSchema": {
            "properties": {"password": {"type": "string"}}}}
        output = io.StringIO()
        with patch.object(client, "load_auth", return_value={}), \
             patch.object(client.Client, "initialize"), \
             patch.object(client.Client, "tools", return_value=[schema]), \
             patch("sys.argv", ["elham", "describe", "create_db_connection"]), \
             contextlib.redirect_stdout(output):
            self.assertEqual(client.main(), 0)
        self.assertEqual(json.loads(output.getvalue()), schema)

    def test_timeout_is_not_retried(self):
        connection = client.Client()
        connection.opener = Transport([TimeoutError()])
        with self.assertRaisesRegex(client.ClientError, "unknown"):
            connection.call("train_model", {})
        self.assertEqual(len(connection.opener.requests), 1)

    def test_rpc_error_and_mismatched_id(self):
        for payload in [{"jsonrpc": "2.0", "id": 1, "error": {"code": -32602}},
                        {"jsonrpc": "2.0", "id": 99, "result": {}}]:
            connection = client.Client()
            connection.opener = Transport([Response(payload)])
            with self.assertRaises(client.ClientError):
                connection.rpc("tools/list")

    def test_credentials_are_mutually_exclusive(self):
        with patch.dict(os.environ, {"ELHAM_ACCESS_TOKEN": "token", "ELHAM_API_KEY": "key"}):
            with self.assertRaises(client.ClientError):
                client.load_auth()

    def test_prediction_key_cannot_manage_account(self):
        with patch.object(client, "load_auth", return_value={"X-API-KEY": "example"}), \
             patch("sys.argv", ["elham", "call", "delete_dataset"]), \
             patch.object(client.Client, "initialize") as init:
            with self.assertRaisesRegex(client.ClientError, "full account"):
                client.main()
            init.assert_not_called()

    def test_private_file_permissions_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "result.json"
            client.write_private(path, {"token": "example"})
            self.assertEqual(json.loads(path.read_text()), {"token": "example"})
            if os.name != "nt":
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                client.write_private(path, {})

    def test_private_storage_failure_leaves_no_secret_file(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(client, "restrict", side_effect=OSError):
            path = Path(folder) / "result.json"
            with self.assertRaises(OSError):
                client.write_private(path, {"token": "example"})
            self.assertFalse(path.exists())

    def test_redacts_nested_secrets_urls_and_auth_echo(self):
        value = client.redact({"api_key": "a", "items": [{"password": "b"}],
                               "error": "example-token https://store.invalid/secret/path"}, ["example-token"])
        serialized = json.dumps(value)
        self.assertNotIn("example-token", serialized)
        self.assertNotIn("secret/path", serialized)
        self.assertEqual(value["items"][0]["password"], "[REDACTED]")

    def test_sensitive_input_echo_is_redacted(self):
        arguments = {"password": "database-secret", "config": {"nested": ["provider-secret"]}}
        result = client.redact({"error": "Rejected database-secret and provider-secret"},
                               client.input_secrets(arguments))
        self.assertEqual(result["error"], "Rejected [REDACTED] and [REDACTED]")

    def test_redirect_is_refused(self):
        with self.assertRaises(client.ClientError):
            client.NoRedirect().redirect_request(None, None, 307, "", {}, "https://other.invalid")

    def test_upload_uses_no_account_auth_and_does_not_commit(self):
        transport = Transport([Response(b"", status=200)])
        with tempfile.TemporaryDirectory() as folder:
            ticket, dataset = Path(folder) / "ticket.json", Path(folder) / "data.csv"
            ticket.write_text(json.dumps({"success": True, "upload_url": "https://store.invalid/upload"}))
            dataset.write_text("a,b\n1,2\n")
            with patch.object(client.urllib.request, "build_opener", return_value=transport):
                self.assertFalse(client.upload(ticket, dataset)["committed"])
            req = transport.requests[0]
            self.assertEqual(req.method, "PUT")
            self.assertIsNone(req.get_header("Authorization"))
            self.assertIsNone(req.get_header("X-api-key"))
            self.assertEqual(int(req.get_header("Content-length")), dataset.stat().st_size)

    def test_upload_refuses_insecure_url(self):
        with tempfile.TemporaryDirectory() as folder:
            ticket = Path(folder) / "ticket.json"
            ticket.write_text(json.dumps({"success": True, "upload_url": "http://store.invalid/upload"}))
            with self.assertRaisesRegex(client.ClientError, "HTTPS"):
                client.upload(ticket, "unused")


if __name__ == "__main__":
    unittest.main()
