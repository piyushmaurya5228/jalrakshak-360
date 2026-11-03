# JalRakshak 360 — Groundwater Data Audit

## 1. Source
- Source: National Water Data Portal
- Agency: Central Ground Water Board telemetry dataset
- State: Uttarakhand
- Frequency: Six-hourly telemetry
- Raw file: data/raw/groundwater_telemetry_uttarakhand.csv

## 2. Dataset Summary
- Total records: 71,950
- Monitoring stations: 65
- Agencies: 1
- Date format: DD-MM-YYYY HH:MM
- Earliest observation: 2026-01-01
- Latest observation: 2026-10-23 12:00
- Invalid timestamps after explicit parsing: 0
- Future timestamps: 0

## 3. Reading Distribution
- Negative readings: 71,647 (99.58%)
- Positive readings: 303 (0.42%)
- Zero readings: 0
- Entirely negative stations: 63
- Mixed-sign stations: 2
- Missing RL_MSL records: 71,950

Negative readings have not been automatically classified as invalid.
The telemetry field's exact sign convention remains unverified.

## 4. Quality Audit
- Stations audited: 65
- Negative-value review flags: 63 stations
- Mixed-sign review flags: 2 stations
- Stations with large-change review flags: 12
- Total large-change flags: 212
- Exploratory change threshold: 10 metres
- Maximum consecutive-pair gap: 12 hours

The 10-metre threshold is exploratory and is not an official
CGWB quality standard.

## 5. Geographic Mapping
- Sample locations mapped: 12
- Same-district stations within 15 km: 7
- Distant same-district stations: 3
- No same-district station: 2

Spatial proximity alone does not establish measurement validity.

## 6. Current Usage Decision

STATUS: MONITORING_ONLY_NOT_FOR_RISK_FUSION

Groundwater readings must not contribute to final risk scores
until their measurement convention, vertical reference,
quality and spatial suitability are independently verified.

No absolute-value conversion or sign correction is permitted
without authoritative source documentation.

## 7. Future Work
1. Obtain the official telemetry field data dictionary.
2. Verify the sign and measurement reference.
3. Investigate mixed-sign stations.
4. Review the 212 large-change flags.
5. Investigate missing RL_MSL metadata.
6. Validate spatial and temporal suitability.
7. Add groundwater risk fusion only after approval.

Raw source observations remain preserved.
Groundwater stress scores were not generated from this telemetry.
