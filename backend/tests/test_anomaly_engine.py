"""Behavior checks for the Phase 6 anomaly service."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from fastapi import HTTPException

from app.models import Dataset
from app.services import dataset_storage
from app.services.anomaly_engine import detect_dataset_anomalies


class AnomalyEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        upload_directory = Path(self.temp_directory.name) / "uploads"
        upload_directory.mkdir()
        storage_patch = patch.object(dataset_storage, "UPLOAD_DIRECTORY", upload_directory)
        storage_patch.start()
        self.addCleanup(storage_patch.stop)
        self.csv_path = upload_directory / "test.csv"
        self.dataset = Dataset(id=1, file_name="test.csv", file_path="uploads/test.csv")

    def test_numeric_anomaly_retains_cancellation_context(self):
        rows = 30
        dataframe = pd.DataFrame({
            "InvoiceNo": [f"I{index}" for index in range(rows - 1)] + ["C999"],
            "CustomerID": list(range(1000, 1000 + rows)),
            "Quantity": list(range(1, rows)) + [-1000],
            "UnitPrice": list(range(10, 10 + rows - 1)) + [1000],
        })
        dataframe.to_csv(self.csv_path, index=False)

        result = detect_dataset_anomalies(self.dataset)

        self.assertEqual(result["status"], "evaluated")
        self.assertEqual(result["numeric_fields"], ["Quantity", "UnitPrice"])
        self.assertGreater(result["anomaly_rows_count"], 0)
        self.assertEqual(result["methods"]["isolation_forest"]["status"], "evaluated")
        self.assertGreaterEqual(
            result["retail_context"]["flagged_negative_quantity_with_cancellation"], 1
        )
        cancellation = next(item for item in result["examples"] if item["row_number"] == 30)
        self.assertIn("legitimate return", cancellation["business_context"])
        self.assertTrue(cancellation["signals"])

    def test_non_numeric_dataset_is_not_evaluated(self):
        pd.DataFrame({"Category": ["A", "B", "C"]}).to_csv(self.csv_path, index=False)

        result = detect_dataset_anomalies(self.dataset)

        self.assertEqual(result["status"], "not_evaluated")
        self.assertIsNone(result["anomaly_rows_count"])
        self.assertEqual(result["examples"], [])

    def test_one_generic_numeric_field_skips_multivariate_method(self):
        pd.DataFrame({"Snowfall": list(range(1, 30)) + [1000]}).to_csv(
            self.csv_path, index=False
        )

        result = detect_dataset_anomalies(self.dataset)

        self.assertEqual(result["numeric_fields"], ["Snowfall"])
        self.assertEqual(result["status"], "evaluated")
        self.assertEqual(result["methods"]["isolation_forest"]["status"], "not_evaluated")
        self.assertGreater(result["anomaly_rows_count"], 0)

    def test_missing_file_and_path_traversal_are_rejected(self):
        with self.assertRaises(HTTPException) as missing:
            detect_dataset_anomalies(self.dataset)
        self.assertEqual(missing.exception.status_code, 404)

        self.dataset.file_path = "../outside.csv"
        with self.assertRaises(HTTPException) as traversal:
            detect_dataset_anomalies(self.dataset)
        self.assertEqual(traversal.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
