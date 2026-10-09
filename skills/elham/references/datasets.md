# Datasets

Use `list_datasets`, `get_dataset_records`, `get_dataset_columns`, and
`get_dataset_quality` to inspect existing data. Quality measures data health; a high
quality score does not guarantee predictive accuracy.

Before upload, inspect the user's file and propose handling missing values, duplicate
rows, inconsistent types, and leakage. Preserve the original. Do not remove meaningful
repeated events, impute values, or discard columns without appropriate user intent.

Upload sequence:

1. Call `generate_upload_url` with the actual filename using `--private-output`.
2. Run `python <skill>/scripts/elham.py upload --ticket <private-result-file> --file <dataset-file>`.
   This PUT sends file bytes to the returned HTTPS storage URL without Elham auth.
3. After PUT succeeds, read `object_key` from the private result and call
   `commit_dataset_upload` with `dataset_name` and `object_key`. For a new version of
   an existing dataset use `commit_dataset_new_version` instead.
4. Delete the private ticket file. Inspect quality and columns for the returned dataset.

The object key must come from this upload. A successful PUT alone does not create a
dataset. Expired upload URLs require a new ticket; do not silently resubmit a commit
whose outcome is unknown. Tool schemas describe optional storage location settings.

`rename_dataset`, `delete_dataset`, and `update_column_semantic_type` change existing
resources. A null semantic type clears an override; it is not a missing argument.
