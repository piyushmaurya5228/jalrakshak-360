# CGWB Uttarakhand Historical Groundwater Quality Mapping

## 1. Source

- Agency: Central Ground Water Board (CGWB)
- Source portal: National Water Data Portal
- Dataset: Ground Water Quality Manual ? Chemical Parameters
- Raw file: `data/raw/cgwb_uttarakhand_groundwater_quality_1961_2025.csv`
- Observed record period in the downloaded file: 25 May 2000 to 18 April 2023

## 2. Dataset Audit

| Metric | Result |
|---|---:|
| Laboratory observations | 903 |
| Unique stations | 156 |
| Districts represented | 8 |
| Invalid observation dates | 0 |
| Invalid/missing coordinates | 0 |
| Duplicate station-date records | 0 |

The dataset contains pH, electrical conductivity, TDS, chloride,
sulphate, hardness and other chemical parameters. Parameter availability
varies substantially. Nitrate and fluoride were unavailable in the
downloaded records audited.

## 3. Prototype Location Matching

Twelve prototype locations were matched against the nearest CGWB station.

| Match category | Locations |
|---|---:|
| Same district, within 15 km | 8 |
| Same district, beyond 15 km | 2 |
| Cross-district review | 2 |
| Total | 12 |

The 15 km threshold is a project screening threshold, not an official
CGWB rule or proof of hydrological equivalence.

## 4. Parameter Mapping

For each same-district matched station, the latest non-null observation
was selected independently for each chemical parameter. Its individual
sampling date is preserved.

This matters because different parameters at one station may have
different latest sampling dates.

For cross-district matches, station and distance context may be shown,
but chemical values are deliberately left blank.

## 5. Interpretation and Limitations

- These are historical CGWB groundwater-quality observations.
- The latest observation in the downloaded source is from 18 April 2023.
- A nearby monitoring station does not necessarily represent the same
  aquifer, well, drinking-water source or village supply.
- CGWB groundwater samples must not automatically be treated as
  household drinking-water samples.
- Missing chemical parameters must remain missing; they are not zero.
- Units and sampling dates must be retained when interpreting values.
- Historical observations do not establish present-day water safety.

## 6. Risk-Fusion Decision

All twelve mapped records are marked:

`HISTORICAL_CONTEXT_ONLY`

All twelve have:

`risk_fusion_eligible = False`

No CGWB values from this mapping are added to the existing risk score.
Any future integration requires separate scientific, temporal and
geographical validation.

## 7. Generated Output

`data/processed/cgwb_uttarakhand_location_quality_history.csv`

The output preserves location ID, matched station, district,
distance, match classification, station history and parameter-specific
latest values and sampling dates.
