# Data connections

For databases, discover the schemas for `create_db_connection`,
`list_db_connections`, `test_db_connection`, `preview_db_query`,
`execute_db_query_to_dataset`, and `delete_db_connection`. Supported engines and
connection fields come from the server. Credentials must travel through a private
file or secure input, never chat or command arguments. Preview SELECT queries before
an authorized import. Do not execute SQL that modifies the source database.

For external sources, start with `list_data_source_providers` and
`get_data_source_provider`. Use their actual configuration schemas rather than
assuming every provider has the same fields or OAuth support.

Use `test_data_source_configuration` before saving, then `create_external_connection`
when authorized. `list_external_connections`, `test_external_connection`,
`browse_external_connection`, and `preview_external_data` support inspection. Use the
IDs returned by browsing as stream identifiers; do not invent provider paths.
`import_external_dataset` creates an import job; follow `get_external_import_status`
or `list_external_imports` until it completes or the bounded wait expires. Inspect
dataset quality and columns after a successful import. Surface `truncated` results:
the dataset may contain only part of the source. `delete_external_connection` deletes
a saved connection and requires authorization for that connection.
