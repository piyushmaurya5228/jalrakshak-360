import unittest

import pandas as pd

from src.cgwb_dashboard import (
    build_cgwb_parameter_table,
    build_cgwb_export_table,
    prepare_cgwb_location_history,
    summarize_cgwb_screening,
)


def sample_history():
    return pd.DataFrame([{
        "location_id": 1,
        "village": "Village_A",
        "sample_district": "Dehradun",
        "station": "Kanwali",
        "station_district": "Dehradun",
        "distance_km": 2.4,
        "first_observation": "2001-05-25",
        "latest_observation": "2022-05-30",
        "historical_record_count": 13,
        "match_status": "SAME_DISTRICT_WITHIN_15KM",
        "data_usage": "HISTORICAL_CONTEXT_ONLY",
        "risk_fusion_eligible": False,
        "ph_latest_value": 7.2,
        "ph_sample_date": "2022-04-18",
        "tds_latest_value": 650.0,
        "tds_sample_date": "2021-05-12",
        "chloride_latest_value": 250.0,
        "chloride_sample_date": "2022-04-18",
        "sulphate_latest_value": 0.0,
        "sulphate_sample_date": "2022-04-18",
        "hardness_latest_value": None,
        "hardness_sample_date": None,
    }])


class TestCGWBDashboard(unittest.TestCase):

    def test_latest_values_receive_reference_statuses(self):
        result = prepare_cgwb_location_history(sample_history()).iloc[0]
        self.assertEqual(result["ph_screening_status"], "WITHIN_REFERENCE_RANGE")
        self.assertEqual(result["tds_screening_status"],
                         "ABOVE_ACCEPTABLE_WITHIN_PERMISSIBLE")
        self.assertEqual(result["chloride_screening_status"],
                         "WITHIN_ACCEPTABLE")
        self.assertEqual(result["sulphate_screening_status"], "ZERO_REVIEW")
        self.assertEqual(result["hardness_screening_status"], "MISSING")

    def test_screening_summary_separates_all_outcome_categories(self):
        result = prepare_cgwb_location_history(sample_history()).iloc[0]
        summary = summarize_cgwb_screening(result)

        self.assertEqual(summary["within_acceptable_or_ph_range"], 2)
        self.assertEqual(
            summary["above_acceptable_within_permissible"], 1
        )
        self.assertEqual(summary["above_permissible"], 0)
        self.assertEqual(summary["ph_outside_reference_range"], 0)
        self.assertEqual(summary["review_required"], 1)
        self.assertEqual(summary["not_reported"], 1)

    def test_ph_outside_reference_range_is_separate_from_permissible_limits(self):
        data = sample_history()
        data.loc[0, "ph_latest_value"] = 8.8
        result = prepare_cgwb_location_history(data).iloc[0]
        summary = summarize_cgwb_screening(result)

        self.assertEqual(summary["above_permissible"], 0)
        self.assertEqual(summary["ph_outside_reference_range"], 1)

    def test_parameter_table_keeps_individual_sampling_dates(self):
        result = prepare_cgwb_location_history(sample_history())
        table = build_cgwb_parameter_table(result.iloc[0])
        self.assertEqual(len(table), 5)
        self.assertEqual(
            table.loc[table["Parameter"] == "Total Dissolved Solids",
                      "Sampling Date"].iloc[0],
            "2021-05-12",
        )

    def test_export_includes_parameter_data_and_station_context(self):
        result = prepare_cgwb_location_history(sample_history()).iloc[0]
        export_table = build_cgwb_export_table(result)

        self.assertEqual(len(export_table), 5)
        self.assertEqual(export_table.loc[0, "Location"], "Village_A")
        self.assertEqual(
            export_table.loc[0, "Matched CGWB Station"], "Kanwali"
        )
        self.assertEqual(
            export_table.loc[0, "Geographic Match Status"],
            "SAME_DISTRICT_WITHIN_15KM",
        )
        self.assertEqual(
            export_table.loc[0, "Station First Observation"], "2001-05-25"
        )
        self.assertEqual(
            export_table.loc[0, "Station Latest Observation"], "2022-05-30"
        )
        self.assertEqual(export_table.loc[0, "Station Historical Records"], 13)
        self.assertFalse(export_table.loc[0, "Risk Fusion Eligible"])
        tds_row = export_table[
            export_table["Parameter"] == "Total Dissolved Solids"
        ].iloc[0]
        self.assertEqual(tds_row["Latest Value"], 650.0)
        self.assertEqual(tds_row["Sampling Date"], "2021-05-12")
        self.assertEqual(
            tds_row["BIS Reference Screening"],
            "Above acceptable; within permissible",
        )

    def test_cross_district_values_must_remain_blank(self):
        data = sample_history()
        data.loc[0, "match_status"] = "CROSS_DISTRICT_REVIEW"

        for parameter in ["ph", "tds", "chloride", "sulphate", "hardness"]:
            data.loc[0, f"{parameter}_latest_value"] = None
            data.loc[0, f"{parameter}_sample_date"] = None

        result = prepare_cgwb_location_history(data)
        for parameter in ["ph", "tds", "chloride", "sulphate", "hardness"]:
            self.assertEqual(
                result.loc[0, f"{parameter}_screening_status"],
                "MISSING",
            )

    def test_cross_district_values_are_rejected_if_populated(self):
        data = sample_history()
        data.loc[0, "match_status"] = "CROSS_DISTRICT_REVIEW"
        with self.assertRaises(ValueError):
            prepare_cgwb_location_history(data)

    def test_risk_fusion_eligible_records_are_rejected(self):
        data = sample_history()
        data.loc[0, "risk_fusion_eligible"] = True
        with self.assertRaises(ValueError):
            prepare_cgwb_location_history(data)

    def test_non_historical_records_are_rejected(self):
        data = sample_history()
        data.loc[0, "data_usage"] = "CURRENT_RISK_INPUT"
        with self.assertRaises(ValueError):
            prepare_cgwb_location_history(data)


if __name__ == "__main__":
    unittest.main()
