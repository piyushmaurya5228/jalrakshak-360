import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

import json
import tempfile
from pathlib import Path

import pandas as pd

from src.data_freshness import (
    assess_retrieval_timestamp,
    build_data_freshness_report,
)


class TestDataFreshness(unittest.TestCase):

    def setUp(self):
        self.now = datetime(
            2026, 11, 2, 20, 0,
            tzinfo=ZoneInfo("Asia/Kolkata"),
        )

    def test_recent_timestamp(self):
        result = assess_retrieval_timestamp(
            "2026-10-27T20:00:00+05:30",
            max_age_days=7,
            now=self.now,
        )
        self.assertEqual(result["status"], "RECENT")

    def test_stale_timestamp(self):
        result = assess_retrieval_timestamp(
            "2026-10-20T20:00:00+05:30",
            max_age_days=7,
            now=self.now,
        )
        self.assertEqual(result["status"], "STALE")

    def test_missing_timestamp_is_unknown(self):
        result = assess_retrieval_timestamp(
            None,
            max_age_days=7,
            now=self.now,
        )
        self.assertEqual(result["status"], "UNKNOWN")

    def test_future_timestamp_is_flagged(self):
        result = assess_retrieval_timestamp(
            "2026-11-03T10:00:00+05:30",
            max_age_days=7,
            now=self.now,
        )
        self.assertEqual(
            result["status"], "INVALID_FUTURE_TIMESTAMP"
        )


    def test_source_report_marks_missing_wqmis_timestamp_unknown(self):
        rainfall_df = pd.DataFrame({
            "retrieved_at_ist": ["2026-11-02T10:00:00+05:30"],
            "rainfall_window_end": ["2026-10-26"],
        })

        with tempfile.TemporaryDirectory() as temp_dir:
            metadata_path = Path(temp_dir) / "missing_metadata.json"

            report = build_data_freshness_report(
                rainfall_df,
                metadata_path,
                now=self.now,
            ).set_index("source")

        self.assertEqual(
            report.loc["Rainfall (ERA5)", "status"], "RECENT"
        )
        self.assertEqual(
            report.loc["JJM/WQMIS WQ6", "status"], "UNKNOWN"
        )
        self.assertEqual(
            report.loc["Rainfall (ERA5)", "latest_observation_date"],
            "2026-10-26",
        )

    def test_source_report_reads_wqmis_metadata(self):
        rainfall_df = pd.DataFrame({
            "retrieved_at_ist": ["2026-11-02T10:00:00+05:30"],
            "rainfall_window_end": ["2026-10-26"],
        })

        metadata = {
            "source": "JJM/WQMIS WQ6",
            "financial_year": "2026-2027",
            "fetched_at_ist": "2026-10-30T10:00:00+05:30",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            metadata_path = Path(temp_dir) / "metadata.json"
            metadata_path.write_text(
                json.dumps(metadata), encoding="utf-8"
            )

            report = build_data_freshness_report(
                rainfall_df,
                metadata_path,
                now=self.now,
            ).set_index("source")

        self.assertEqual(
            report.loc["JJM/WQMIS WQ6", "status"],
            "TIMESTAMP_RECORDED",
        )
        self.assertAlmostEqual(
            report.loc["JJM/WQMIS WQ6", "age_days"],
            3.42,
            places=1,
        )


    def test_rainfall_observation_near_limit(self):
        rainfall_df = pd.DataFrame({
            "retrieved_at_ist": ["2026-11-02T10:00:00+05:30"],
            "rainfall_window_end": ["2026-10-20"],
        })

        with tempfile.TemporaryDirectory() as temp_dir:
            report = build_data_freshness_report(
                rainfall_df,
                Path(temp_dir) / "missing.json",
                now=self.now,
            )

        rainfall = report.set_index("source").loc["Rainfall (ERA5)"]
        self.assertEqual(rainfall["observation_status"], "NEAR_LIMIT")

    def test_rainfall_observation_stale(self):
        rainfall_df = pd.DataFrame({
            "retrieved_at_ist": ["2026-11-02T10:00:00+05:30"],
            "rainfall_window_end": ["2026-10-18"],
        })

        with tempfile.TemporaryDirectory() as temp_dir:
            report = build_data_freshness_report(
                rainfall_df,
                Path(temp_dir) / "missing.json",
                now=self.now,
            )

        rainfall = report.set_index("source").loc["Rainfall (ERA5)"]
        self.assertEqual(rainfall["observation_status"], "STALE")


if __name__ == "__main__":
    unittest.main()
