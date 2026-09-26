"""Check chart summaries preserve counts and honest evaluation status."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from fastapi import HTTPException

from app.models import Dataset
from app.services import dataset_storage
from app.services.visualization_engine import visualize_dataset_column


class VisualizationEngineTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        upload_directory = Path(directory.name) / "uploads"
        upload_directory.mkdir()
        storage_patch = patch.object(dataset_storage, "UPLOAD_DIRECTORY", upload_directory)
        storage_patch.start()
        self.addCleanup(storage_patch.stop)
        self.csv_path = upload_directory / "test.csv"
        self.dataset = Dataset(id=1, file_name="test.csv", file_path="uploads/test.csv")

    def test_numeric_bins_account_for_finite_rows_and_tails(self):
        values = list(range(1, 101)) + [1000, float("inf"), None]
        pd.DataFrame({"Amount": values}).to_csv(self.csv_path, index=False)

        result = visualize_dataset_column(self.dataset, "Amount")

        self.assertEqual(result["logical_type"], "numeric")
        self.assertEqual(result["rows_count"], 103)
        self.assertEqual(result["missing_count"], 1)
        self.assertEqual(result["excluded_nonfinite_count"], 1)
        self.assertEqual(result["usable_count"], 101)
        self.assertEqual(sum(result["full_range"]["counts"]), 101)
        self.assertEqual(
            sum(result["central_range"]["counts"]) + result["outside_central_count"],
            101,
        )

    def test_categorical_top_values_include_an_other_count(self):
        values = [f"group-{index}" for index in range(14) for _ in range(10)]
        pd.DataFrame({"Group": values}).to_csv(self.csv_path, index=False)

        result = visualize_dataset_column(self.dataset, "Group")

        self.assertEqual(result["logical_type"], "categorical")
        self.assertEqual(len(result["categories"]), 12)
        self.assertEqual(sum(item["count"] for item in result["categories"]), 120)
        self.assertEqual(result["other_count"], 20)

    def test_extreme_finite_numbers_still_produce_finite_bins(self):
        pd.DataFrame({"Amount": [-1e308, -1e307, 1e307, 1e308]}).to_csv(
            self.csv_path, index=False
        )

        result = visualize_dataset_column(self.dataset, "Amount")

        self.assertEqual(result["status"], "evaluated")
        self.assertEqual(sum(result["full_range"]["counts"]), 4)
        self.assertTrue(all(abs(edge) <= 1e308 for edge in result["full_range"]["edges"]))

    def test_dates_are_counted_by_month(self):
        pd.DataFrame({"RecordedAt": ["2025-01-01", "2025-01-20", "2025-02-01"]}).to_csv(
            self.csv_path, index=False
        )

        result = visualize_dataset_column(self.dataset, "RecordedAt")

        self.assertEqual(result["logical_type"], "datetime")
        self.assertEqual(result["time_unit"], "month")
        self.assertEqual(result["time_buckets"], [
            {"period": "2025-01", "count": 2},
            {"period": "2025-02", "count": 1},
        ])

    def test_identifier_is_not_plotted_as_measure(self):
        pd.DataFrame({"CustomerID": [1, 2, 3, 4]}).to_csv(self.csv_path, index=False)

        result = visualize_dataset_column(self.dataset, "CustomerID")

        self.assertEqual(result["status"], "not_evaluated")
        self.assertEqual(result["logical_type"], "identifier")

    def test_missing_column_and_missing_file_return_404(self):
        pd.DataFrame({"Amount": [1, 2]}).to_csv(self.csv_path, index=False)
        with self.assertRaises(HTTPException) as unknown:
            visualize_dataset_column(self.dataset, "Other")
        self.assertEqual(unknown.exception.status_code, 404)

        self.csv_path.unlink()
        with self.assertRaises(HTTPException) as missing:
            visualize_dataset_column(self.dataset, "Amount")
        self.assertEqual(missing.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
