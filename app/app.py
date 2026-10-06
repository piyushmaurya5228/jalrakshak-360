import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pipeline import load_and_process_data
from src.intervention import recommend_actions
from src.scenario import simulate_rainfall


st.set_page_config(
    page_title="JalRakshak 360",
    page_icon="💧",
    layout="wide",
)

st.title("JalRakshak 360")
st.caption("AI-powered drinking-water risk monitoring and intervention prioritisation")


@st.cache_data
def load_data():
    path = ROOT / "data" / "sample" / "water_risk_sample.csv"
    df, _ = load_and_process_data(path)
    return df


df = load_data()


@st.cache_data
def load_wqmis_data():
    path = ROOT / "data" / "processed" / "wqmis_up_2025_2026_risk.csv"
    return pd.read_csv(path)


wqmis_df = load_wqmis_data()

st.sidebar.header("Filters")

districts = ["All"] + sorted(df["district"].unique().tolist())
selected_district = st.sidebar.selectbox("District", districts)

risk_levels = ["All", "CRITICAL", "HIGH", "WATCH", "LOW"]
selected_risk = st.sidebar.selectbox("Risk Level", risk_levels)

filtered = df.copy()

if selected_district != "All":
    filtered = filtered[filtered["district"] == selected_district]

if selected_risk != "All":
    filtered = filtered[filtered["final_risk_level"] == selected_risk]


critical_count = len(filtered[filtered["final_risk_level"] == "CRITICAL"])
high_count = len(filtered[filtered["final_risk_level"] == "HIGH"])
p1_count = len(filtered[filtered["final_priority"] == "P1"])
exposed_population = int(filtered["population"].sum())


c1, c2, c3, c4 = st.columns(4)

c1.metric("Locations Monitored", len(filtered))
c2.metric("Critical", critical_count)
c3.metric("High", high_count)
c4.metric("P1 Interventions", p1_count)

st.metric("Population Covered", f"{exposed_population:,}")

st.divider()

left, right = st.columns([1.6, 1])

with left:
    st.subheader("Water Risk Map")

    if len(filtered) > 0:
        center_lat = filtered["latitude"].mean()
        center_lon = filtered["longitude"].mean()
    else:
        center_lat = 30.3165
        center_lon = 78.0322

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=7,
        tiles="OpenStreetMap",
    )

    colors = {
        "CRITICAL": "red",
        "HIGH": "orange",
        "WATCH": "blue",
        "LOW": "green",
    }

    for _, row in filtered.iterrows():
        popup = f"""
        <b>{row['village']}</b><br>
        District: {row['district']}<br>
        Final Risk: {row['final_risk_score']}<br>
        Level: {row['final_risk_level']}<br>
        Priority: {row['final_priority']}<br>
        AI Anomaly: {row['anomaly_score']}
        """

        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=popup,
            tooltip=f"{row['village']} - {row['final_risk_level']}",
            icon=folium.Icon(
                color=colors.get(row["final_risk_level"], "blue"),
                icon="info-sign",
            ),
        ).add_to(m)

    st_folium(m, width="100%", height=500)


with right:
    st.subheader("Intervention Priority Queue")

    priority_df = (
        filtered[
            [
                "village",
                "district",
                "final_risk_score",
                "final_risk_level",
                "final_priority",
                "anomaly_score",
            ]
        ]
        .sort_values("final_risk_score", ascending=False)
        .reset_index(drop=True)
    )

    priority_df.columns = [
        "Village",
        "District",
        "Risk Score",
        "Risk Level",
        "Priority",
        "AI Anomaly",
    ]

    st.dataframe(
        priority_df,
        use_container_width=True,
        hide_index=True,
    )


st.divider()

st.subheader("What-If Rainfall Simulator")

scenario_village = st.selectbox(
    "Select a location for simulation",
    df["village"].tolist(),
    key="scenario_village",
)

scenario_row = df[df["village"] == scenario_village].iloc[0]

rainfall_change = st.slider(
    "Simulated rainfall change (%)",
    min_value=-50,
    max_value=100,
    value=0,
    step=10,
)

scenario = simulate_rainfall(
    scenario_row,
    rainfall_change,
)

original_rule_score = float(scenario_row["risk_score"])
risk_change = round(
    scenario["risk_score"] - original_rule_score,
    2,
)

s1, s2, s3, s4 = st.columns(4)

s1.metric(
    "Original Rainfall",
    f"{scenario['original_rainfall']} mm",
)

s2.metric(
    "Simulated Rainfall",
    f"{scenario['simulated_rainfall']} mm",
)

s3.metric(
    "Scenario Risk",
    f"{scenario['risk_score']}/100",
    delta=f"{risk_change:+.2f}",
)

s4.metric(
    "Scenario Level",
    scenario["risk_level"],
)

st.caption(
    "Scenario risk is calculated using the explainable rule-based engine. "
    "AI anomaly scoring is not retrained for the simulated scenario."
)

st.divider()

st.subheader("Location Intelligence")

if len(filtered) > 0:

    selected_village = st.selectbox(
        "Select a location",
        filtered["village"].tolist(),
    )

    row = filtered[filtered["village"] == selected_village].iloc[0]

    st.write(
        f"### {row['village']} — {row['district']}"
    )

    a, b, c, d = st.columns(4)

    a.metric("Final Risk", f"{row['final_risk_score']}/100")
    b.metric("Risk Level", row["final_risk_level"])
    c.metric("Priority", row["final_priority"])
    d.metric("AI Anomaly", f"{row['anomaly_score']}/100")

    st.write("### Risk Factors")

    factors = {
        "Water contamination": row["water_risk"],
        "Rainfall anomaly": row["rainfall_risk"],
        "Groundwater stress": row["groundwater_risk"],
        "Historical contamination": row["historical_risk"],
        "Population exposure": row["exposure_risk"],
    }

    factor_df = (
        pd.DataFrame(
            list(factors.items()),
            columns=["Factor", "Risk Score"],
        )
        .sort_values("Risk Score", ascending=False)
    )

    st.bar_chart(
        factor_df.set_index("Factor"),
        y="Risk Score",
    )

    st.write("### Why was this location flagged?")

    top_factors = factor_df.head(3)

    for _, factor in top_factors.iterrows():
        st.write(
            f"- **{factor['Factor']}**: "
            f"{factor['Risk Score']:.1f}/100"
        )

    intervention_result = {
        "risk_level": row["final_risk_level"],
        "rainfall_risk": row["rainfall_risk"],
        "groundwater_risk": row["groundwater_risk"],
        "historical_risk": row["historical_risk"],
    }

    st.write("### Recommended Actions")

    actions = recommend_actions(intervention_result)

    for priority, action in actions:
        st.write(f"**{priority}** — {action}")

else:
    st.warning("No locations match the selected filters.")


st.divider()

st.subheader("Verified Government Water-Quality Intelligence")

st.caption(
    "Source: JJM / WQMIS WQ6 | Financial Year: 2025-2026 | "
    "PWS | Sample Location: All"
)

st.info(
    "WQ6 values below represent reported contamination indicators/counts. "
    "They are not raw concentration measurements and are not yet fused into "
    "the final AI risk score."
)

w1, w2, w3, w4 = st.columns(4)

contaminated_districts = int(
    (wqmis_df["contamination_burden"] > 0).sum()
)

total_indicators = int(
    wqmis_df["contamination_burden"].sum()
)

top_district = (
    wqmis_df.sort_values(
        "contamination_burden",
        ascending=False,
    ).iloc[0]
)

w1.metric("Districts Reported", len(wqmis_df))
w2.metric("Districts with Contamination", contaminated_districts)
w3.metric("Total Contamination Indicators", total_indicators)
w4.metric(
    "Highest Burden",
    f"{top_district['State']} ({int(top_district['contamination_burden'])})",
)

st.write("### Highest Contamination Burden")

top10 = (
    wqmis_df[
        ["State", "contamination_burden"]
    ]
    .sort_values("contamination_burden", ascending=False)
    .head(10)
    .reset_index(drop=True)
)

top10.columns = [
    "District",
    "Contamination Indicators",
]

st.dataframe(
    top10,
    use_container_width=True,
    hide_index=True,
)

st.write("### District-wise WQ6 Detail")

wqmis_district = st.selectbox(
    "Select a district",
    sorted(wqmis_df["State"].unique().tolist()),
    key="wqmis_district",
)

wqmis_row = wqmis_df[
    wqmis_df["State"] == wqmis_district
].iloc[0]

parameter_map = {
    "pH": "PH",
    "TDS": "TDS",
    "Turbidity": "Turbidity",
    "Chloride": "Chloride",
    "Alkalinity": "Total_Alkalinity",
    "Hardness": "Total_Hardness",
    "Sulphate": "Sulphate",
    "Iron": "Iron",
    "Arsenic": "Total_Arsenic",
    "Fluoride": "Fluoride",
    "Nitrate": "Nitrate",
    "Residual Chlorine": "Residual_Chlorine",
    "Bacteriological": "Bacteriologial_Contamination",
    "Total Coliform": "TotalColiform",
    "E. coli": "TotalEcoil",
}

detail_rows = []

for label, column in parameter_map.items():
    detail_rows.append(
        {
            "Parameter": label,
            "Reported Indicators": int(wqmis_row[column]),
        }
    )

detail_df = pd.DataFrame(detail_rows)
detail_df = detail_df[
    detail_df["Reported Indicators"] > 0
].sort_values(
    "Reported Indicators",
    ascending=False,
)

if len(detail_df) > 0:
    st.bar_chart(
        detail_df.set_index("Parameter"),
        y="Reported Indicators",
    )
else:
    st.success(
        f"No non-zero WQ6 contamination indicators reported for {wqmis_district}."
    )
