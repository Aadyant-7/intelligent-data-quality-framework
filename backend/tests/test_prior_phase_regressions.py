"""Focused checks for earlier phases while building explainability."""

import json
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from fastapi import HTTPException, UploadFile

from app.models import Dataset
from app.services import dataset_ingestion, dataset_storage
from app.services.data_profiler import profile_dataset
from app.services.dataset_ingestion import ingest_dataset
from app.services.quality_engine import assess_dataset_quality


class PriorPhaseRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        self.upload_directory = Path(self.temp_directory.name) / "uploads"
        self.upload_directory.mkdir()
        for module in (dataset_storage, dataset_ingestion):
            storage_patch = patch.object(module, "UPLOAD_DIRECTORY", self.upload_directory)
            storage_patch.start()
            self.addCleanup(storage_patch.stop)
        self.csv_path = self.upload_directory / "test.csv"
        self.dataset = Dataset(id=1, file_name="test.csv", file_path="uploads/test.csv")

    def test_profile_does_not_treat_snowfall_as_identifier(self):
        pd.DataFrame({"Snowfall": [1, 2, 3], "CustomerID": [1, 2, 3]}).to_csv(
            self.csv_path, index=False
        )

        columns = profile_dataset(self.dataset)["columns"]

        self.assertEqual(columns[0]["logical_type"], "numeric")
        self.assertEqual(columns[1]["logical_type"], "identifier")

    def test_profile_with_infinite_number_is_json_safe(self):
        pd.DataFrame({"Amount": [1.0, 2.0, float("inf")]}).to_csv(
            self.csv_path, index=False
        )

        profile = profile_dataset(self.dataset)

        json.dumps(profile, allow_nan=False)
        amount = profile["columns"][0]
        self.assertEqual(amount["sample_values"], [1.0, 2.0, None])
        self.assertIsNone(amount["statistics"]["max"])
        self.assertEqual(amount["statistics"]["min"], 1.0)

    def test_quality_reports_malformed_retail_numbers(self):
        pd.DataFrame({
            "InvoiceNo": ["1", "2"],
            "Quantity": ["bad", "1"],
            "UnitPrice": ["x", "2"],
        }).to_csv(self.csv_path, index=False)

        result = assess_dataset_quality(self.dataset)

        self.assertEqual(result["dimensions"]["validity"]["invalid_rows"], 1)
        self.assertEqual(result["dimensions"]["validity"]["score"], 50.0)
        self.assertEqual(
            {issue["column"] for issue in result["issues"] if "column" in issue},
            {"Quantity", "UnitPrice"},
        )

    def test_quality_reports_infinite_retail_number(self):
        pd.DataFrame({
            "InvoiceNo": ["1", "2"],
            "Quantity": [float("inf"), 1],
            "UnitPrice": [2, 2],
        }).to_csv(self.csv_path, index=False)

        result = assess_dataset_quality(self.dataset)

        self.assertEqual(result["dimensions"]["validity"]["invalid_rows"], 1)
        self.assertEqual(result["dimensions"]["validity"]["score"], 50.0)

    def test_quality_does_not_award_consistency_without_comparable_rows(self):
        pd.DataFrame({"StockCode": [None], "Description": [None]}).to_csv(
            self.csv_path, index=False
        )

        result = assess_dataset_quality(self.dataset)

        self.assertEqual(result["dimensions"]["consistency"]["status"], "not_evaluated")
        self.assertIsNone(result["dimensions"]["consistency"]["score"])

    def test_generic_quality_excludes_unevaluated_retail_weights(self):
        pd.DataFrame({"Value": [1, None, 3]}).to_csv(self.csv_path, index=False)

        result = assess_dataset_quality(self.dataset)

        self.assertEqual(result["dimensions"]["validity"]["status"], "not_evaluated")
        self.assertEqual(result["dimensions"]["consistency"]["status"], "not_evaluated")
        self.assertIn("Retail validity requires", result["dimensions"]["validity"]["reason"])
        self.assertIn("Retail consistency requires", result["dimensions"]["consistency"]["reason"])
        self.assertEqual(result["overall_quality_score"], 81.82)

    def test_empty_dataset_is_not_scored(self):
        pd.DataFrame(columns=["Quantity", "UnitPrice"]).to_csv(self.csv_path, index=False)

        result = assess_dataset_quality(self.dataset)

        self.assertIsNone(result["overall_quality_score"])
        self.assertTrue(all(
            dimension["status"] == "not_evaluated"
            for dimension in result["dimensions"].values()
        ))

    def test_header_only_csv_and_xlsx_uploads_are_rejected_without_leftovers(self):
        csv_file = UploadFile(filename="empty.csv", file=BytesIO(b"Column\n"))
        with self.assertRaises(HTTPException) as csv_error:
            ingest_dataset(csv_file, None)
        self.assertEqual(csv_error.exception.status_code, 400)

        excel_buffer = BytesIO()
        pd.DataFrame(columns=["Column"]).to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        excel_file = UploadFile(filename="empty.xlsx", file=excel_buffer)
        with self.assertRaises(HTTPException) as excel_error:
            ingest_dataset(excel_file, None)
        self.assertEqual(excel_error.exception.status_code, 400)
        self.assertEqual(list(self.upload_directory.iterdir()), [])

    def test_corrupt_xlsx_upload_is_rejected_without_leftovers(self):
        corrupt_file = UploadFile(filename="broken.xlsx", file=BytesIO(b"PK\x03\x04garbage"))

        with self.assertRaises(HTTPException) as error:
            ingest_dataset(corrupt_file, None)

        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(list(self.upload_directory.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
