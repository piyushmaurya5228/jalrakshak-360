# 💧 JalRakshak 360

### AI-Powered Drinking-Water Risk Monitoring and Intervention Prioritisation

JalRakshak 360 is an AI-enabled decision-support platform designed to help identify, analyse and prioritise drinking-water risks at vulnerable locations.

The system combines:

* Explainable rule-based risk scoring
* AI-based anomaly detection
* AI + rule-based risk fusion
* Intervention recommendation
* What-if rainfall simulation
* Interactive geospatial visualisation
* Verified government water-quality information from JJM/WQMIS WQ6

The objective is to transform fragmented water and environmental risk information into an understandable and actionable decision-support workflow.

---

## 🚨 Problem Statement

Water-quality risks can arise from contamination, rainfall anomalies, groundwater stress and recurring water-quality issues. Relevant information may be distributed across different datasets and systems, making it difficult to identify higher-risk locations and prioritise timely intervention.

There is a need for an explainable system that can:

1. Combine multiple water and environmental risk indicators.
2. Identify unusual combinations of risk conditions.
3. Assign a location-wise risk score and priority.
4. Explain the major factors contributing to risk.
5. Recommend appropriate intervention actions.
6. Present information through an easy-to-use geographic dashboard.

JalRakshak 360 addresses this gap through a unified decision-support platform.

---

## 🎯 Objectives

The major objectives of JalRakshak 360 are:

* To provide explainable drinking-water risk assessment.
* To detect unusual environmental and water-risk patterns using AI.
* To prioritise locations requiring intervention.
* To provide actionable recommendations based on risk conditions.
* To support rainfall scenario analysis through what-if simulation.
* To integrate verified government water-quality information.
* To provide an interactive map-based monitoring dashboard.

---

## 💡 Solution Overview

JalRakshak 360 follows a layered decision-support architecture.

```text
                    INPUT DATA
                         │
          ┌──────────────┴──────────────┐
          │                             │
   Prototype Risk Data           JJM / WQMIS WQ6
          │                             │
          ▼                             ▼
   Risk Processing              Government Data Layer
          │
          ▼
   Explainable Risk Engine
          │
          ▼
   AI Anomaly Detection
          │
          ▼
      Risk Fusion
          │
          ▼
  Final Risk Assessment
          │
     ┌────┼───────────────┐
     │    │               │
     ▼    ▼               ▼
Intervention      Dashboard      What-If Analysis
Recommendation      │
                    ▼
              Map + Priority Queue
```

The current implementation keeps the verified WQ6 government-data layer separate from the full AI risk-fusion pipeline because WQ6 provides contaminant-wise reported indicators at an aggregated level, while the current risk engine expects additional location-level variables such as rainfall, groundwater stress and population exposure.

This separation prevents unsupported assumptions from being introduced into the final risk score.

---

# ⭐ Key Features

## 1. Explainable Risk Engine

A rule-based risk engine calculates a risk score from multiple factors:

* Water contamination
* Rainfall anomaly
* Groundwater stress
* Historical contamination
* Population exposure

The resulting score is classified into:

| Risk Score | Risk Level | Priority |
| ---------: | ---------- | -------- |
|     80–100 | CRITICAL   | P1       |
|   60–79.99 | HIGH       | P1       |
|   30–59.99 | WATCH      | P2       |
|    0–29.99 | LOW        | P3       |

The weighted explainable risk model currently uses:

```text
35%  Water Contamination
25%  Rainfall Anomaly
20%  Groundwater Stress
10%  Historical Contamination
10%  Population Exposure
```

---

## 2. AI-Based Anomaly Detection

JalRakshak 360 uses an **Isolation Forest** model to identify unusual combinations of environmental and water-risk features.

The current anomaly model uses:

```text
water_contamination_rate
rainfall_7d
rainfall_normal
groundwater_stress
previous_contamination
```

The resulting anomaly score is normalised to a range of **0–100**.

A higher anomaly score indicates a more unusual combination of observed risk features within the modelled dataset.

---

## 3. AI + Rule-Based Risk Fusion

The AI anomaly signal is combined with the explainable rule-based risk score.

Current fusion logic:

```text
Final Risk Score
=
70% Explainable Risk
+
30% AI Anomaly Score
```

The fused result is then classified into:

```text
LOW
WATCH
HIGH
CRITICAL
```

with corresponding intervention priorities:

```text
P3
P2
P1
P1
```

---

## 4. Intervention Recommendation Engine

The intervention module converts risk conditions into actionable recommendations.

Examples include:

* Priority water-quality testing
* Water-source inspection
* Post-rainfall sampling
* Drainage inspection
* Alternate water-source assessment

The intention is to move from:

```text
Risk Detection
      ↓
Risk Explanation
      ↓
Action Recommendation
```

---

## 5. What-If Rainfall Simulator

The dashboard includes an interactive rainfall scenario simulator.

Users can:

* Increase rainfall
* Decrease rainfall
* Observe simulated rainfall values
* Observe the resulting change in explainable risk
* Compare original and simulated risk levels

The simulator provides scenario-based decision support without retraining the AI anomaly model for every scenario.

---

## 6. Interactive Risk Dashboard

The Streamlit dashboard provides:

* Total monitored locations
* Critical locations
* High-risk locations
* P1 intervention count
* Population coverage
* Interactive risk map
* Intervention priority queue
* Location-wise risk analysis
* Risk-factor visualisation
* Recommended actions
* Rainfall what-if simulator
* Government WQ6 intelligence panel

---

# 🏛️ Government Data Integration — JJM/WQMIS WQ6

JalRakshak 360 integrates water-quality information from the official **JJM/WQMIS WQ6 contaminant-wise report**.

The integration includes:

* WQMIS page analysis
* Identification of the application's AES request mechanism
* Programmatic API requests
* Uttar Pradesh state-level data retrieval
* Automatic financial-year detection
* JSON and CSV data storage
* WQ6 data mapping into a normalised water-contamination component

### Current WQ6 integration

```text
State: Uttar Pradesh
State ID: 31
Financial Year: 2026–2027
Districts Reported: 75
Districts with Non-Zero Contamination Indicators: 15
Total Contamination Indicators: 262
Highest Reported Burden: Firozabad (77)
```

### WQ6 parameters currently captured

```text
pH
TDS
Turbidity
Chloride
Total Alkalinity
Total Hardness
Sulphate
Iron
Total Arsenic
Fluoride
Nitrate
Residual Chlorine
Others
Bacteriological Contamination
Total Coliform
Total E. coli
```

### Important data interpretation note

WQ6 values used in this project are treated as **reported contamination indicators/counts**, not as raw laboratory concentration measurements.

The current WQ6 integration is therefore presented as a **verified government water-quality intelligence layer**.

It is not incorrectly interpreted as a direct concentration dataset.

---

# 🔄 Automatic WQ6 Data Refresh

The project includes:

```text
scripts/fetch_wqmis.py
```

This script automatically:

1. Detects the current financial year.
2. Connects to the WQMIS WQ6 endpoint.
3. Requests Uttar Pradesh data.
4. Retrieves the JSON response.
5. Saves raw JSON data.
6. Saves a flat CSV version.

Generated files are stored under:

```text
data/raw/
```

Example:

```text
data/raw/wqmis_up_2026_2027.json
data/raw/wqmis_up_2026_2027.csv
```

---

# 🧠 WQ6 Data Mapping

The project contains:

```text
src/wqmis_mapper.py
```

The mapper:

* Reads raw WQ6 CSV data.
* Calculates a contamination burden from WQ6 indicator columns.
* Normalises the burden to a 0–1 water-contamination component.
* Preserves the original WQ6 parameters.
* Keeps unavailable risk dimensions explicitly separated.

The current mapped output is stored under:

```text
data/processed/
```

Example:

```text
data/processed/wqmis_up_2026_2027_risk.csv
```

---

# 📊 Risk Calculation Methodology

## Explainable Risk

For a location, the current rule-based model is:

```text
Water Risk
   × 0.35

Rainfall Risk
   × 0.25

Groundwater Risk
   × 0.20

Historical Risk
   × 0.10

Exposure Risk
   × 0.10

             ↓

Explainable Risk Score
```

## AI + Rule Fusion

```text
Explainable Risk Score
          × 0.70
              +
AI Anomaly Score
          × 0.30

              ↓

       Final Risk Score
```

This design allows the system to retain an explainable baseline while also incorporating an AI-based anomaly signal.

---

# 🧰 Technology Stack

## Programming

* Python 3.x

## Data Processing

* Pandas

## Machine Learning

* Scikit-learn
* Isolation Forest

## Dashboard

* Streamlit

## Mapping / GIS Visualisation

* Folium
* Streamlit-Folium

## API / Government Data Integration

* Requests
* Cryptography

## Testing

* Python `unittest`

## Version Control

* Git
* GitHub

---

# 📁 Project Structure

```text
jalrakshak-360/
│
├── app/
│   └── app.py
│
├── data/
│   ├── sample/
│   │   └── water_risk_sample.csv
│   │
│   ├── raw/
│   │   └── WQMIS downloaded data
│   │
│   └── processed/
│       └── WQMIS mapped data
│
├── scripts/
│   └── fetch_wqmis.py
│
├── src/
│   ├── risk_engine.py
│   ├── anomaly_model.py
│   ├── risk_fusion.py
│   ├── intervention.py
│   ├── scenario.py
│   └── wqmis_mapper.py
│
├── tests/
│   ├── test_risk_engine.py
│   ├── test_anomaly_model.py
│   ├── test_risk_fusion.py
│   ├── test_scenario.py
│   └── test_wqmis_mapper.py
│
├── requirements.txt
├── README.md
└── LICENSE
```

---

# 🚀 Installation

## 1. Clone the Repository

```bash
git clone https://github.com/piyushmaurya5228/jalrakshak-360.git
cd jalrakshak-360
```

---

## 2. Create a Virtual Environment

### Windows PowerShell

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

---

## 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

# ▶️ Run the Dashboard

Run:

```powershell
python -m streamlit run app/app.py
```

The Streamlit application will start locally.

---

# 🔄 Refresh Government WQ6 Data

To fetch the current WQ6 data:

```powershell
python scripts/fetch_wqmis.py
```

The script automatically determines the current financial year.

The downloaded files are saved under:

```text
data/raw/
```

---

# 🧪 Testing

JalRakshak 360 includes automated unit tests for the core modules.

Run all tests with:

```powershell
python -m unittest discover -s tests -v
```

### Current test status

```text
Risk Engine              ✅
AI Anomaly Model         ✅
Risk Fusion              ✅
Scenario Simulator       ✅
WQ6 Mapper               ✅

Total: 9/9 tests passed
```

Testing covers:

* Low and critical risk classification
* Anomaly output generation
* Anomaly score range
* Risk fusion
* Rainfall scenario behaviour
* WQ6 data mapping and validation

---

# 📍 Dashboard Workflow

The user workflow is:

```text
Open Dashboard
      ↓
Select Risk Filters
      ↓
View Risk Map
      ↓
Check Intervention Priority Queue
      ↓
Inspect Location Risk Factors
      ↓
View Recommended Actions
      ↓
Run Rainfall What-If Scenario
      ↓
Review Verified Government WQ6 Intelligence
```

---

# 📌 Current Project Status

| Component                  | Status       |
| -------------------------- | ------------ |
| Project Architecture       | ✅ Complete   |
| Initial Prototype          | ✅ Complete   |
| Explainable Risk Engine    | ✅ Complete   |
| AI Anomaly Detection       | ✅ Complete   |
| Risk Fusion                | ✅ Complete   |
| Intervention Engine        | ✅ Complete   |
| What-If Rainfall Simulator | ✅ Complete   |
| Streamlit Dashboard        | ✅ Complete   |
| Official WQ6 Integration   | ✅ Complete   |
| Automatic WQ6 Refresh      | ✅ Complete   |
| WQ6 Mapping Layer          | ✅ Complete   |
| Automated Tests            | ✅ 9/9 Passed |
| GitHub Version Control     | ✅ Complete   |

---

# ⚠️ Current Limitations

The current implementation has the following limitations:

1. The full risk pipeline was initially developed and tested using a synthetic prototype dataset.
2. The current WQ6 government-data layer provides aggregated contaminant-wise indicators rather than complete location-level laboratory concentration measurements.
3. Verified WQ6 data is currently presented separately from the complete AI risk-fusion pipeline.
4. Rainfall, groundwater and population/exposure datasets still need to be integrated from additional verified sources.
5. Further calibration and validation are required before operational real-world deployment.
6. The current prototype should be considered a decision-support system rather than a replacement for official water-quality assessment or field verification.

---

# 🔭 Future Scope

Planned improvements include:

## Multi-Source Data Integration

Integrate additional verified datasets for:

* Rainfall
* Groundwater stress
* Population exposure
* Historical water-quality observations

## Improved Spatial Intelligence

* Village-level mapping
* Better geographic filtering
* Location-specific risk aggregation
* Advanced GIS visualisation

## Model Calibration

* Larger real-world datasets
* Feature calibration
* Threshold validation
* Model performance evaluation

## Advanced AI

Potential future work includes:

* Temporal anomaly detection
* Multi-source predictive modelling
* Risk trend forecasting
* Spatial risk clustering

## Deployment

* Cloud deployment
* Role-based access
* Automated scheduled data refresh
* Scalable APIs
* Monitoring and logging

---

# 🌱 Expected Impact

JalRakshak 360 aims to support:

* Earlier identification of potential water-risk hotspots
* Better prioritisation of field inspections and testing
* Data-driven intervention planning
* More transparent risk assessment
* Easier interpretation of fragmented environmental information
* Improved decision support for vulnerable communities

The platform is designed to help decision-makers move from:

```text
Data
 ↓
Information
 ↓
Risk Identification
 ↓
Prioritisation
 ↓
Action
```

---

# 🎯 Relevant Sustainable Development Goals

The project is aligned with:

### SDG 6 — Clean Water and Sanitation

Supports improved monitoring and decision support related to drinking-water quality.

### SDG 3 — Good Health and Well-being

Improved water-risk identification can contribute to preventive public-health interventions.

### SDG 11 — Sustainable Cities and Communities

Supports more resilient and data-informed local communities.

### SDG 13 — Climate Action

Rainfall scenario analysis can support consideration of environmental stress and climate-related risk.

---

# 🤝 Intended Users

Potential users include:

* Rural development authorities
* Local administrative bodies
* Water-quality monitoring teams
* Field inspection teams
* Environmental researchers
* NGOs and community organisations
* Disaster and risk-management stakeholders

---

# 🔐 Data & Responsible Use

JalRakshak 360 is intended as a decision-support prototype.

Risk scores and AI anomaly signals should be interpreted together with:

* Official testing
* Field verification
* Local conditions
* Expert assessment
* Updated government datasets

The system should not be treated as a substitute for official laboratory testing or government decision-making processes.

---

# 📚 Data Source

### JJM / WQMIS

The project uses the official JJM/WQMIS WQ6 contaminant-wise reporting system for government water-quality intelligence.

The implementation retrieves data programmatically and preserves the raw response before processing.

---

# 👨‍💻 Open Source

Repository:

```text
https://github.com/piyushmaurya5228/jalrakshak-360
```

The repository contains:

* Source code
* Application code
* Sample data
* Automated tests
* WQ6 integration scripts
* Data-processing modules
* Requirements
* Technical documentation

---

# 📄 License

This project is released under the **MIT License**.

See the `LICENSE` file for the complete license text.

---

# 🏁 Conclusion

JalRakshak 360 demonstrates a practical approach to drinking-water risk monitoring by combining explainable risk assessment, machine-learning-based anomaly detection, intervention prioritisation, scenario simulation and verified government water-quality intelligence.

The current prototype establishes the core architecture and working dashboard, while the next development phase focuses on multi-source real-data integration, model calibration, improved spatial intelligence and deployment.

**JalRakshak 360 — From Water Data to Actionable Risk Intelligence.**

