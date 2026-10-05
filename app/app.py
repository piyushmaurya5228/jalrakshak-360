import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.risk_engine import calculate_location_risk
from src.intervention import recommend_actions


st.set_page_config(
    page_title="JalRakshak 360",
    page_icon="??",
    layout="wide",
)


@st.cache_data
def load_data():
    path = ROOT / "data" / "sample" / "water_risk_sample.csv"
    df = pd.read_csv(path)

    results = df.apply(calculate_location_risk, axis=1, result_type="expand")
    df = pd.concat([df, results], axis=1)

    return df


df = load_data()

st.title("?? JalRakshak 360")
st.caption("AI-powered drinking-water risk monitoring and intervention prioritisation")

st.sidebar.header("Filters")

districts = ["All"] + sorted(df["district"].unique().tolist())
selected_district = st.sidebar.selectbox("District", districts)

risk_levels = ["All", "CRITICAL", "HIGH", "WATCH", "LOW"]
selected_risk = st.sidebar.selectbox("Risk Level", risk_levels)

filtered = df.copy()

if selected_district != "All":
    filtered = filtered[filtered["district"] == selected_district]

if selected_risk != "All":
    filtered = filtered[filtered["risk_level"] == selected_risk]


critical_count = len(filtered[filtered["risk_level"] == "CRITICAL"])
high_count = len(filtered[filtered["risk_level"] == "HIGH"])
watch_count = len(filtered[filtered["risk_level"] == "WATCH"])
exposed_population = int(filtered["population"].sum())


c1, c2, c3, c4 = st.columns(4)

c1.metric("Locations Monitored", len(filtered))
c2.metric("Critical", critical_count)
c3.metric("High Risk", high_count)
c4.metric("Population Covered", f"{exposed_population:,}")


st.divider()

left, right = st.columns([1.6, 1])

with left:
    st.subheader("??? Water Risk Map")

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
        Risk Score: {row['risk_score']}<br>
        Risk Level: {row['risk_level']}<br>
        Priority: {row['priority']}
        """

        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=popup,
            tooltip=f"{row['village']} - {row['risk_level']}",
            icon=folium.Icon(
                color=colors.get(row["risk_level"], "blue"),
                icon="tint",
                prefix="fa",
            ),
        ).add_to(m)

    st_folium(m, width="100%", height=500)


with right:
    st.subheader("?? Intervention Priority Queue")

    priority_df = (
        filtered[
            [
                "village",
                "district",
                "risk_score",
                "risk_level",
                "priority",
            ]
        ]
        .sort_values("risk_score", ascending=False)
        .reset_index(drop=True)
    )

    priority_df.index = priority_df.index + 1

    st.dataframe(
        priority_df,
        use_container_width=True,
    )


st.divider()

st.subheader("?? Location Intelligence")

if len(filtered) > 0:
    selected_village = st.selectbox(
        "Select a location",
        filtered["village"].tolist(),
    )

    row = filtered[filtered["village"] == selected_village].iloc[0]

    result = {
        "risk_score": row["risk_score"],
        "risk_level": row["risk_level"],
        "priority": row["priority"],
        "water_risk": row["water_risk"],
        "rainfall_risk": row["rainfall_risk"],
        "groundwater_risk": row["groundwater_risk"],
        "historical_risk": row["historical_risk"],
        "exposure_risk": row["exposure_risk"],
    }

    a, b, c = st.columns(3)

    a.metric("Risk Score", f"{row['risk_score']}/100")
    b.metric("Risk Level", row["risk_level"])
    c.metric("Intervention Priority", row["priority"])

    st.write("### Why is this location at risk?")

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

    st.write("### Recommended actions")

    actions = recommend_actions(result)

    for priority, action in actions:
        st.write(f"**{priority}** — {action}")
else:
    st.warning("No locations match the selected filters.")
