# Models and training

1. Identify the dataset and prediction target. Read `get_dataset_columns` and
   `get_dataset_quality`. Resolve the target's numeric column ID from this dataset.
2. Use `list_algorithms` if algorithm selection is requested. Read the live schema for
   `train_model` (or `train_model_new_version` for an existing model).
3. Call `estimate_cost` with `event_type: "train"` and the dataset ID. Report the
   returned estimate/balance and resolve spending authorization before submission.
4. Supply required names and target ID. `training_level` controls thoroughness, not
   pricing. `id_columns` are logical grouping keys for validation; `to_delete_columns`
   removes features. These lists must be disjoint and exclude the target. Do not
   guess which columns identify repeated entities. Interpretation and ensemble
   settings should follow the user's needs and the live schema.
5. Submit once. Preserve `model_id`; use `get_training_progress`, `get_training_live`
   and `get_model` to follow progress. Never claim success from submission alone.

Use `list_models` to find models and `get_model_columns` for column metadata associated
with a model. Use `get_model_schema` for the exact prediction input contract.
`stop_training` requests graceful stop: finalization
may continue to save the best available model. Do not promise an immediate stop or
refund. `update_model_status` changes serving status; inspect its schema and current
state before using it. A model must be Running for prediction. Delete only a model
the user has authorized you to delete.
