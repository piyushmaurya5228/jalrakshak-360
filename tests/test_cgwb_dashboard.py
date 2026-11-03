import unittest

import pandas as pd

from src.cgwb_dashboard import (
    build_cgwb_parameter_table,
    prepare_cgwb_location_history,
)


def sample_history():
    return pd.DataFrame([{
        "location_id": 1,
        "village": "Village_A",
        "sample_district": "Dehradun",
        "station": "Kanwali",
        "station_district": "Dehradun",
        "distance_km": 2.4,
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

    def test_parameter_table_keeps_individual_sampling_dates(self):
        result = prepare_cgwb_location_history(sample_history())
        table = build_cgwb_parameter_table(result.iloc[0])
        self.assertEqual(len(table), 5)
        self.assertEqual(
            table.loc[table["Parameter"] == "Total Dissolved Solids",
                      "Sampling Date"].iloc[0],
            "2021-05-12",
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
