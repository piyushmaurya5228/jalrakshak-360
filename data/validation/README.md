# Independent model-validation data

Use the templates in `templates/` for three separate partitions:

- `input/train.csv`: verified real feature rows for Isolation Forest.
- `input/calibration.csv`: different geographic groups with expert-reviewed
  future outcome labels.
- `input/test.csv`: untouched expert-reviewed future outcome groups; never
  tune on this file.

The `input/` directory is ignored by Git so site records and labels are not
accidentally published.

Use traceable sources and set `is_synthetic=false`. `site_id` identifies a
monitoring site; `group_id` identifies a broader geographic group. Groups
must be disjoint across partitions. `feature_as_of_date` is the cutoff for
all predictors. Historical test counts must end on or before this cutoff.
Outcome labels must cover a later `label_window_start` to
`label_window_end`, and be reviewed after the window closes.

Calibration and holdout labels must follow one expert-approved protocol
(`1` elevated, `0` not elevated), with
`label_review_status=EXPERT_VERIFIED`, a traceable `label_source` and
`label_evidence_id`, a `label_protocol_version`, a non-personal
`reviewer_code`, and `label_reviewed_at`.

Do not derive labels from JalRakshak model scores or synthetic assumptions.
Avoid personal information and use site codes. Read
`docs/model_validation_protocol.md` before preparing data.

The software checks declared provenance and review fields but cannot
authenticate source records or reviewer credentials.
