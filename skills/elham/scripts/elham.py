#!/usr/bin/env python3
"""Elham skill client. Python 3.10+, standard library only; no automatic retries."""

import argparse
import getpass
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request


ENDPOINT = "https://app.elham.ai/api/elham-mcp/mcp"
PROTOCOL = "2025-03-26"
SESSION = Path.home() / ".elham-skills" / "session.json"
SECRET_FIELDS = {"token", "access_token", "refresh_token", "password", "api_key",
                 "apikey", "secret", "client_secret", "authorization", "upload_url",
                 "config", "configuration", "credentials", "connection_string",
                 "secret_access_key", "access_key", "sas_token", "private_key"}


class ClientError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ClientError("Redirect refused. Credentials and uploads are never forwarded.")


def restrict(path):
    """Restrict a newly created file/directory before writing secrets; fail closed."""
    if os.name == "nt":
        identity = subprocess.run(["whoami", "/user", "/fo", "csv", "/nh"],
                                  capture_output=True, text=True, check=True)
        sid = re.search(r"S-1-\d+(?:-\d+)+", identity.stdout)
        if not sid:
            raise ClientError("Cannot identify current Windows user for private storage.")
        permission = "(OI)(CI)F" if path.is_dir() else "F"
        subprocess.run(["icacls", str(path), "/inheritance:r", "/grant:r",
                        f"*{sid.group()}:{permission}"], capture_output=True, check=True)
    else:
        path.chmod(0o700 if path.is_dir() else 0o600)


def write_private(path, value):
    """Never overwrite existing paths or follow a destination symlink."""
    path = Path(path)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        restrict(path)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            fd = None
            json.dump(value, stream, ensure_ascii=False)
    except BaseException:
        if fd is not None:
            os.close(fd)
        path.unlink(missing_ok=True)
        raise


def load_auth(credential_file=None):
    # Never collect ambient environment credentials. A user signs in with this
    # helper or explicitly selects a private file provisioned for this service.
    path = Path(credential_file) if credential_file else SESSION
    if not path.exists():
        if credential_file:
            raise ClientError("The selected private credential file does not exist.")
        return {}
    if path.is_symlink() or path.parent.is_symlink():
        raise ClientError("Refusing symlinked credential storage.")
    if os.name != "nt" and stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise ClientError("Credential file must have user-only permissions (0600).")
    saved = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(saved, dict) or saved.get("endpoint") != ENDPOINT:
        raise ClientError("Credential file must specify the official Elham endpoint.")
    token, key = saved.get("token"), saved.get("api_key")
    if bool(token) == bool(key):
        raise ClientError("Credential file must contain exactly one token or api_key.")
    value = token or key
    if not isinstance(value, str) or not value.strip() or "\r" in value or "\n" in value:
        raise ClientError("Invalid credential value.")
    if key:
        return {"X-API-KEY": key}
    return {"Authorization": f"Bearer {token}"} if token else {}


def redact(value, secrets=()):
    if isinstance(value, dict):
        return {k: "[REDACTED]" if k.lower() in SECRET_FIELDS else redact(v, secrets)
                for k, v in value.items()}
    if isinstance(value, list):
        return [redact(item, secrets) for item in value]
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[REDACTED]")
        # URLs can embed storage signatures in the path as well as the query.
        return re.sub(r"https?://[^\s\"<>]+", "[URL REDACTED]", value)
    return value


def input_secrets(value, sensitive=False):
    if isinstance(value, dict):
        return [secret for key, item in value.items()
                for secret in input_secrets(item, sensitive or key.lower() in SECRET_FIELDS)]
    if isinstance(value, list):
        return [secret for item in value for secret in input_secrets(item, sensitive)]
    return [value] if sensitive and isinstance(value, str) and value else []


def unwrap(result):
    if result.get("isError"):
        raise ClientError("Server tool error; inspect the tool schema and authentication.")
    if "structuredContent" in result:
        value = result["structuredContent"]
    else:
        blocks = [b.get("text", "") for b in result.get("content", [])
                  if b.get("type") == "text"]
        if len(blocks) != 1:
            raise ClientError("Unexpected tool response: expected one JSON result.")
        try:
            value = json.loads(blocks[0])
        except ValueError:
            raise ClientError("Tool returned a non-JSON result.") from None
    return value


class Client:
    def __init__(self, auth=None):
        self.auth = auth or {}
        self.opener = urllib.request.build_opener(NoRedirect())
        self.sequence = 0
        self.session_id = None
        self.protocol = PROTOCOL

    def rpc(self, method, params=None, notification=False):
        self.sequence += 1
        message = {"jsonrpc": "2.0", "method": method}
        if not notification:
            message["id"] = self.sequence
        if params is not None:
            message["params"] = params
        headers = {"Accept": "application/json, text/event-stream",
                   "User-Agent": "Elham-Skills/1.0",
                   "Content-Type": "application/json",
                   "MCP-Protocol-Version": self.protocol, **self.auth}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        req = urllib.request.Request(ENDPOINT, json.dumps(message).encode(), headers,
                                     method="POST")
        try:
            with self.opener.open(req, timeout=120) as response:
                if method == "initialize":
                    self.session_id = response.headers.get("Mcp-Session-Id")
                if notification:
                    response.read()
                    return None
                if "text/event-stream" in response.headers.get("Content-Type", ""):
                    result = self.read_sse(response, message["id"])
                else:
                    result = json.load(response)
        except urllib.error.HTTPError as exc:
            raise ClientError(f"HTTP {exc.code}. Request was not retried. Check sign-in, "
                              "permissions, and service availability.") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ClientError("Connection failed. Outcome may be unknown; no automatic retry.") from None
        if result.get("id") != message["id"] or result.get("jsonrpc") != "2.0":
            raise ClientError("Invalid JSON-RPC response.")
        if "error" in result:
            code = result["error"].get("code", "unknown")
            raise ClientError(f"JSON-RPC error {code}; request was not retried.")
        if "result" not in result:
            raise ClientError("JSON-RPC result is missing.")
        return result["result"]

    @staticmethod
    def read_sse(response, request_id):
        data = []
        for raw in response:
            line = raw.decode("utf-8").rstrip("\r\n")
            if line.startswith("data:"):
                data.append(line[5:].lstrip(" "))
            elif not line and data:
                event = json.loads("\n".join(data))
                data = []
                if event.get("id") == request_id:
                    return event
        raise ClientError("Stream closed before a result; outcome may be unknown. Do not replay.")

    def initialize(self):
        result = self.rpc("initialize", {"protocolVersion": PROTOCOL, "capabilities": {},
                           "clientInfo": {"name": "elham-skills", "version": "1.2.0"}})
        if result.get("protocolVersion") not in {"2025-03-26", "2025-06-18", "2025-11-25"}:
            raise ClientError("Unsupported negotiated protocol version.")
        self.protocol = result["protocolVersion"]
        self.rpc("notifications/initialized", notification=True)

    def tools(self):
        items, cursor, seen = [], None, set()
        while True:
            result = self.rpc("tools/list", {"cursor": cursor} if cursor else {})
            items.extend(result["tools"])
            cursor = result.get("nextCursor")
            if not cursor:
                return items
            if cursor in seen:
                raise ClientError("Server repeated a pagination cursor.")
            seen.add(cursor)

    def call(self, name, arguments):
        if not isinstance(arguments, dict):
            raise ClientError("Tool arguments must be a JSON object.")
        return unwrap(self.rpc("tools/call", {"name": name, "arguments": arguments}))


def upload(ticket_path, file_path):
    ticket = json.loads(Path(ticket_path).read_text(encoding="utf-8"))
    if ticket.get("success") is not True:
        raise ClientError("Upload ticket is not a successful tool result.")
    url = ticket["upload_url"]
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ClientError("Upload requires an HTTPS storage URL without user credentials.")
    path = Path(file_path)
    # Separate opener and explicit headers: never attach account credentials to storage.
    with path.open("rb") as stream:
        req = urllib.request.Request(url, stream, method="PUT", headers={
            "Content-Type": "application/octet-stream", "Content-Length": str(path.stat().st_size)})
        try:
            with urllib.request.build_opener(NoRedirect()).open(req, timeout=120) as response:
                if not 200 <= response.status < 300:
                    raise ClientError("Upload failed; do not commit the dataset.")
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ClientError("Upload failed or timed out. No retry or dataset commit performed.") from None
    return {"success": True, "uploaded": True, "committed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credential-file", help="Explicit private Elham credential file; never a token value")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("status", "login", "logout", "tools"):
        sub.add_parser(name)
    sub.add_parser("describe").add_argument("tool")
    call = sub.add_parser("call")
    call.add_argument("tool")
    call.add_argument("--args-file")
    call.add_argument("--private-output", help="New private JSON file; raw result never printed")
    put = sub.add_parser("upload")
    put.add_argument("--ticket", required=True)
    put.add_argument("--file", required=True)
    args = parser.parse_args()
    if args.command == "logout":
        SESSION.unlink(missing_ok=True)
        print("Local session removed. Explicit credential files and server sessions are unchanged.")
        return 0
    if args.command == "upload":
        print(json.dumps(upload(args.ticket, args.file)))
        return 0
    auth = {} if args.command == "login" else load_auth(args.credential_file)
    if args.command == "status":
        print(json.dumps({"credential_available": bool(auth), "validated_online": False,
                          "kind": "api_key" if "X-API-KEY" in auth else "session" if auth else None}))
        return 0
    if args.command == "call" and args.tool == "authenticate":
        raise ClientError("Use interactive login; do not place passwords in tool arguments.")
    if args.command == "call" and not auth:
        raise ClientError("Sign in with login or select a private file with --credential-file.")
    if args.command == "call" and "X-API-KEY" in auth and args.tool not in {"predict", "get_model_schema"}:
        raise ClientError("This operation requires a full account session, not a prediction API key.")
    if args.command == "call" and args.private_output and Path(args.private_output).exists():
        raise ClientError("Private output already exists; choose a new file before submitting.")
    client = Client(auth)
    client.initialize()
    if args.command == "login":
        if not sys.stdin.isatty():
            raise ClientError("Run login in your own interactive terminal, not through chat input.")
        email = input("Elham email: ").strip()
        password = getpass.getpass("Elham password: ")
        result = client.call("authenticate", {"email": email, "password": password})
        if result.get("success") is not True or not result.get("token"):
            raise ClientError("Sign-in failed. Check your credentials in Elham.")
        if SESSION.parent.is_symlink():
            raise ClientError("Refusing symlinked session directory.")
        SESSION.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        restrict(SESSION.parent)
        SESSION.unlink(missing_ok=True)
        write_private(SESSION, {"endpoint": ENDPOINT, "token": result["token"]})
        print("Signed in. Access token saved privately; password was not saved.")
        return 0
    if args.command in {"tools", "describe"}:
        items = client.tools()
        if args.command == "tools":
            result = [{"name": t["name"], "description": t.get("description", "")} for t in items]
        else:
            result = next((t for t in items if t["name"] == args.tool), None)
            if result is None:
                raise ClientError("Tool is not available on this server.")
    else:
        arguments = {}
        if args.args_file:
            text = sys.stdin.read() if args.args_file == "-" else Path(args.args_file).read_text(encoding="utf-8-sig")
            arguments = json.loads(text)
        result = client.call(args.tool, arguments)
    failed = isinstance(result, dict) and result.get("success") is False
    if args.command == "call" and args.private_output:
        write_private(args.private_output, result)
        print(json.dumps({"success": not failed, "private_output_saved": True}))
    elif args.command in {"tools", "describe"}:
        # Public schema property names such as "password" are not secret values.
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        secrets = [v.removeprefix("Bearer ") for v in auth.values()]
        secrets.extend(input_secrets(arguments))
        print(json.dumps(redact(result, secrets), ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ClientError as error:
        print(json.dumps({"success": False, "error": str(error)}), file=sys.stderr)
        sys.exit(1)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        print(json.dumps({"success": False, "error": "Invalid input, response, or private storage failure. "
                          "No automatic retry; a submitted operation may have completed."}), file=sys.stderr)
        sys.exit(1)
