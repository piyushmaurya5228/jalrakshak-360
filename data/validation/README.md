# Independent model-validation data

Use the templates in `templates/` for three separate partitions:

- `input/train.csv`: verified real feature rows for Isolation Forest.
- `input/calibration.csv`: distinct geographic groups with expert-reviewed labels.
- `input/test.csv`: untouched expert-reviewed holdout groups; never tune on this file.

The `input/` directory is ignored by Git so location records and labels are
not accidentally published.

Use traceable sources. Set `is_synthetic=false`. `site_id` identifies a
monitoring site; `group_id` identifies a broader geographic group. Groups
must be disjoint across partitions. Labels must follow one expert-approved
protocol (`1` elevated, `0` not elevated), with
`label_review_status=EXPERT_VERIFIED` and a traceable `label_source`.

Do not derive labels from JalRakshak model scores or synthetic assumptions.
Avoid personal information and use site codes. Read
`docs/model_validation_protocol.md` before preparing data.

The software checks declared provenance and review fields but cannot
authenticate source records or reviewer credentials.
