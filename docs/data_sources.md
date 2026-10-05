# JalRakshak 360 — Data Sources

JalRakshak 360 is designed to combine publicly available Indian government data sources for explainable drinking-water risk prioritisation.

## 1. JJM Water Quality Management Information System (WQMIS)

Organisation: Department of Drinking Water & Sanitation, Ministry of Jal Shakti, Government of India.

Used for:
- Drinking-water quality testing
- Chemical contamination
- Bacteriological contamination
- Village-level contamination reporting
- Water-quality testing coverage

Official source:
https://ejalshakti.gov.in/WQMIS/

Relevant reports:
- WQ4: Parameter-wise Lab Testing
- WQ5: Testing in Villages
- WQ6: Contaminant-wise details of villages

## 2. Central Ground Water Board (CGWB)

Organisation: Ministry of Jal Shakti, Government of India.

Used for:
- Groundwater quality
- Fluoride
- Nitrate
- Iron
- Arsenic
- Other groundwater-quality indicators

Official source:
https://cgwb.gov.in/en/ground-water-quality

## 3. India Meteorological Department (IMD)

Organisation: Ministry of Earth Sciences, Government of India.

Used for:
- Rainfall
- District-level rainfall information
- Rainfall anomaly features

Official source:
https://mausam.imd.gov.in/

## 4. Prototype Data

The current file in `data/sample/` contains synthetic demonstration data only.

It must not be represented as official government observations.

The prototype will progressively replace synthetic values with verified public data and retain source attribution for each dataset.

## Data Governance

JalRakshak 360 is a decision-support prototype.

Its risk score is not a medical diagnosis, water-safety certification, or official government risk classification.

The system is intended to help prioritise inspection and monitoring based on available evidence.
