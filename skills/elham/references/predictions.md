# Prediction and monitoring

Call `get_model_schema` for the selected model. Build rows using its required columns,
types, and enforced categorical values. Exclude the target, IDs, and removed features.
Do not invent a category or silently replace an invalid value. Read the schema again
when the model version changes.

Call `estimate_cost` with `event_type: "inference"`, row count and the number of columns
actually submitted per row. Use consistently shaped rows. Explain the estimate and
obtain spending authorization if not already given. API-key-only credentials cannot
call this estimator: obtain a full account session for this workflow rather than
bypassing the pricing step.

Read `predict`'s schema: it requires the model ID, model name, and a list of row
dictionaries. The model must be Running. Submit once; report returned predictions
and actual charge if present. Validation failure is not a successful prediction.
An ambiguous network failure is not safe to replay automatically.

`get_model_monitoring` reads monitoring information. `submit_prediction_labels`
writes observed outcomes; inspect its schema and use genuine ground truth linked to
the returned prediction identifiers. Never substitute predicted values for ground
truth or fabricate monitoring statistics when no data exists.
