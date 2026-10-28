import unittest

import pandas as pd

from scripts.fetch_groundwater_telemetry import (
    find_nearest_same_district_station,
)


class TestGroundwaterMapping(unittest.TestCase):

    def setUp(self):
        self.candidates = pd.DataFrame([
            {"Station": "Nearby Other District", "District": "Dehradun",
             "distance_km": 2.0},
            {"Station": "Far Local Station", "District": "Nainital",
             "distance_km": 16.0},
            {"Station": "Near Local Station", "District": " NAINITAL ",
             "distance_km": 11.9},
        ])

    def test_selects_nearest_station_in_same_district(self):
        station = find_nearest_same_district_station(
            self.candidates, "Nainital"
        )

        self.assertEqual(station["Station"], "Near Local Station")
        self.assertAlmostEqual(station["distance_km"], 11.9)

    def test_district_matching_ignores_case_and_whitespace(self):
        station = find_nearest_same_district_station(
            self.candidates, "  nAiNiTaL  "
        )

        self.assertIsNotNone(station)
        self.assertEqual(station["Station"], "Near Local Station")

    def test_returns_none_when_no_same_district_station_exists(self):
        station = find_nearest_same_district_station(
            self.candidates, "Tehri Garhwal"
        )

        self.assertIsNone(station)


if __name__ == "__main__":
    unittest.main()
