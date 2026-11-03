# JalRakshak 360 — CGWB Historical BIS Reference Screening

## 1. Objective

This module performs historical reference screening of CGWB
groundwater-quality observations against selected BIS IS 10500:2012
drinking-water reference limits.

It is intended for historical research and prioritisation only.
It does not certify drinking-water safety.

## 2. Source Dataset

- Source: Central Ground Water Board (CGWB)
- Portal: National Water Data Portal
- Raw file: `data/raw/cgwb_uttarakhand_groundwater_quality_1961_2025.csv`
- Total observations: 903
- Stations: 156
- Districts represented: 8
- Observation period: 25 May 2000 to 18 April 2023

## 3. Reference Criteria

| Parameter | Unit | Acceptable limit | Permissible limit |
|---|---|---:|---:|
| TDS | mg/L | 500 | 2000 |
| Chloride | mg/L | 250 | 1000 |
| Sulphate | mg/L | 200 | 400 |
| Total Hardness | mg/L as CaCO3 | 200 | 600 |
| pH | — | 6.5–8.5 | No relaxation |

Reference: BIS IS 10500:2012. The applicable amendments and
current requirements should be verified before any operational use.

Permissible limits are not equivalent to preferred acceptable
quality and should not be interpreted as unconditional approval.

## 4. Screening Results

### Total Dissolved Solids

| Classification | Records |
|---|---:|
| Within acceptable | 13 |
| Above acceptable, within permissible | 48 |
| Above permissible | 16 |
| Zero review | 10 |
| Missing | 816 |

### Chloride

| Classification | Records |
|---|---:|
| Within acceptable | 846 |
| Above acceptable, within permissible | 29 |
| Above permissible | 4 |
| Missing | 24 |

### Sulphate

| Classification | Records |
|---|---:|
| Within acceptable | 620 |
| Above acceptable, within permissible | 19 |
| Above permissible | 14 |
| Zero review | 26 |
| Missing | 224 |

### Total Hardness

| Classification | Records |
|---|---:|
| Within acceptable | 483 |
| Above acceptable, within permissible | 301 |
| Above permissible | 13 |
| Missing | 106 |

### pH

| Classification | Records |
|---|---:|
| Within reference range | 835 |
| Below reference range | 1 |
| Above reference range | 15 |
| Missing | 52 |

Each parameter is classified independently. Counts across parameters
must not be added to represent unique affected locations or samples.

## 5. Zero and Missing Value Policy

- Missing values are classified as MISSING.
- Zero TDS and sulphate values are classified as ZERO_REVIEW.
- Negative measurements are classified as INVALID_NEGATIVE.
- Non-finite and invalid values are excluded from normal classification.
- Zero values are not automatically interpreted as clean water.
- Raw source values are preserved.

The ten zero TDS records share the sampling date 25 May 2018.
The 26 zero sulphate records have multiple sampling dates.
Their source-specific reporting conventions require confirmation.

## 6. Parameters Not Included

Nitrate and fluoride had no available observations in the audited
dataset.

Iron and arsenic had very sparse observations and are not included
in this screening module.

Their absence must not be interpreted as zero concentration or
absence of contamination.

## 7. Generated Files

Screening implementation:
`src/cgwb_screening.py`

Audit script:
`scripts/audit_cgwb_bis_screening.py`

Processed output:
`data/processed/cgwb_bis_historical_screening.csv`

Automated tests:
`tests/test_cgwb_screening.py`

The raw CGWB dataset remains unchanged.

## 8. Dashboard Presentation

The selected-location dashboard presents a separate summary for:
- Values within acceptable limits or the pH reference range
- Values above acceptable but within permissible limits
- Values above permissible limits
- pH values outside the reference range
- Values requiring source review
- Parameters not reported

Parameter statuses use green, amber, red and grey visual labels.
The summary keeps pH range checks separate from chemical concentration
limits. These categories are display summaries only and do not create
a water-safety certification or alter the project risk score.

A selected-location CSV export is available beside the dashboard table.
It includes parameter values, individual sampling dates, units, screening
labels, reference limits and the station/location matching context. The
export preserves the historical-context-only and non-risk-fusion status.

## 8. Limitations

1. Observations are historical, with the latest dated 18 April 2023.
2. CGWB groundwater samples are not automatically equivalent to
   household drinking-water supply samples.
3. Station-level observations are not village-level measurements.
4. Parameter availability varies substantially.
5. Zero-value reporting conventions remain under review.
6. This screening is not an independent laboratory verification.
7. Historical results cannot establish present-day water safety.

## 10. Risk-Fusion Policy

The screening output is a historical research layer.

No screened CGWB values are added to the current risk score.
No risk-fusion eligibility is implied by passing a reference limit.

Any future integration requires validation of sampling purpose,
units, dates, station relevance and geographic applicability.

## 11. Conclusion

The screening module classifies available historical CGWB observations
without changing the raw source values.

It provides transparent parameter-level reference comparisons while
preserving missing, zero-review and invalid-value distinctions.

JalRakshak 360 remains a decision-support prototype, not an official
drinking-water safety certification system.
