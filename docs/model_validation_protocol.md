# JalRakshak 360 — Independent Model Validation Protocol

## Current evidence

The 12-location prototype is synthetic. Its baseline scores and sensitivity
experiments demonstrate software/model behaviour only; they are not evidence
of real-world predictive accuracy.

The repository now includes an independent evaluation workflow. **Real-world
validation remains pending** until verified training observations and separate
expert-reviewed calibration and holdout labels are supplied. Do not claim
real-world accuracy from the synthetic prototype.

## Three disjoint partitions

- **Training:** verified, non-synthetic feature records used to fit Isolation
  Forest. Labels are not required.
- **Calibration:** different sites and geographic groups with expert-reviewed
  binary labels. Used to select candidate fusion weight and alert cutoff.
- **Holdout test:** untouched sites and groups with expert-reviewed labels.
  Used only for final metrics, never for tuning.

The same `site_id` or `group_id` cannot occur in more than one partition.
Use meaningful geographic groups such as districts, watersheds or monitoring
regions to reduce spatial leakage. The code checks declared IDs but cannot
authenticate their real-world correctness.

## Required columns

All partitions require `site_id`, `group_id`, `data_source`,
`is_synthetic`, and the model features:

- `water_contamination_rate` (0–1)
- `rainfall_7d`
- `rainfall_normal`
- `groundwater_stress` (0–1)
- `previous_contamination` (0–1)

Calibration and test additionally require `population`, `water_tests`,
`contaminated_tests`, `ground_truth_label`, `label_review_status` and
`label_source`. Labels must be 0 or 1, marked `EXPERT_VERIFIED`, and follow
one documented expert-approved definition. Do not derive labels from
JalRakshak scores, synthetic assumptions or the same rule outputs being tested.

## Evaluation approach

Isolation Forest is fitted on training data only. Anomaly severity is mapped
to an empirical percentile using the training-score distribution, rather
than normalising against the evaluation batch.

Calibration searches anomaly weights from 0.00 to 0.50 in 0.05 steps and
risk cutoffs 30, 60 and 80. It preserves the existing rule-score safety floor
and selects the candidate with maximum calibration F1. The untouched holdout
then reports ROC-AUC, average precision, precision, recall, F1, specificity
and confusion-matrix counts for rule-only, anomaly-only and calibrated fusion.

Selected settings are research suggestions only. Experts must review false
negative and false positive costs before operational adoption. Production
risk weights, thresholds and scores are not modified by the evaluator.

## Run

Populate the templates in `data/validation/templates/` and place real files
locally at `data/validation/input/train.csv`,
`data/validation/input/calibration.csv` and
`data/validation/input/test.csv`. Then run:

```powershell
.\venv\Scripts\python.exe scripts\evaluate_model.py
```

Results are written to `reports/model_validation/`. Both the input and
report folders are git-ignored to protect site-level evidence.

## Safeguards and limitations

The evaluator rejects synthetic records, missing provenance, non-expert or
non-binary labels, non-finite values, geographic/site overlap between splits,
and impossible test counts. These checks validate declared metadata only.
Source documents, lab records, reviewer qualifications and label definitions
must be independently authenticated by the project team.
