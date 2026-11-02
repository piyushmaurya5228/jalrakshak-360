import json
import os
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from scripts.fetch_wqmis import save_data


class TestWQMISFetch(unittest.TestCase):

    def test_fetch_metadata_is_saved_with_ist_timestamp(self):
        payload = {
            "Contaminantwise": [
                {"District": "Agra", "TotalColiform": 0},
                {"District": "Dehradun", "TotalColiform": 2},
            ]
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = Path.cwd()

            try:
                os.chdir(temp_dir)

                json_path, csv_path, count = save_data(
                    payload, "2026-2027"
                )

                metadata_path = (
                    Path("data/raw")
                    / "wqmis_up_2026_2027_metadata.json"
                )

                self.assertTrue(json_path.exists())
                self.assertTrue(csv_path.exists())
                self.assertTrue(metadata_path.exists())
                self.assertEqual(count, 2)

                metadata = json.loads(
                    metadata_path.read_text(encoding="utf-8")
                )

                timestamp = __import__(
                    "datetime"
                ).datetime.fromisoformat(
                    metadata["fetched_at_ist"]
                )

                self.assertEqual(
                    timestamp.utcoffset(),
                    timedelta(hours=5, minutes=30),
                )
                self.assertEqual(metadata["source"], "JJM/WQMIS WQ6")
                self.assertEqual(metadata["financial_year"], "2026-2027")
                self.assertEqual(metadata["row_count"], 2)

            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
