"""Retail rules should follow meaning while avoiding uncertain matches."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from app.models import Dataset
from app.services import dataset_storage
from app.services.quality_engine import assess_dataset_quality
from app.services.retail_schema import resolve_retail_schema


class RetailSchemaTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        upload_directory = Path(directory.name) / "uploads"
        upload_directory.mkdir()
        storage_patch = patch.object(dataset_storage, "UPLOAD_DIRECTORY", upload_directory)
        storage_patch.start()
        self.addCleanup(storage_patch.stop)
        self.path = upload_directory / "retail.csv"
        self.dataset = Dataset(id=1, file_name="retail.csv", file_path="uploads/retail.csv")

    def test_name_variants_and_ambiguous_price_are_explainable(self):
        schema = resolve_retail_schema(["Price Per Unit", "Unit Price", "Qty", "Total Spent"])
        self.assertEqual(schema["matches"]["quantity"], "Qty")
        self.assertNotIn("unit_price", schema["matches"])
        self.assertEqual(schema["ambiguous"]["unit_price"], ["Price Per Unit", "Unit Price"])

    def test_alternate_retail_headers_enable_validity_and_arithmetic_consistency(self):
        pd.DataFrame({"Transaction ID": ["TX1", "TX2", "TX3"],
                      "Price Per Unit": [10, -2, 3], "Quantity": [2, 1, -1],
                      "Total Spent": [20, -2, 4], "Discount Applied": [False, False, False]}).to_csv(self.path, index=False)
        result = assess_dataset_quality(self.dataset)
        self.assertEqual(result["retail_schema"]["matches"]["unit_price"], "Price Per Unit")
        self.assertEqual(result["dimensions"]["validity"]["invalid_rows"], 1)
        self.assertFalse(result["dimensions"]["validity"]["cancellation_rule_evaluated"])
        consistency = result["dimensions"]["consistency"]
        self.assertEqual(consistency["checks"][0]["checked"], 3)
        self.assertEqual(consistency["checks"][0]["affected"], 1)

    def test_tax_included_total_and_discount_exclusion(self):
        pd.DataFrame({"Invoice ID": ["1", "2"], "Unit price": [10, 10],
                      "Quantity": [2, 2], "Tax 5%": [1, 1], "Total": [21, 18],
                      "Discount Applied": [False, True]}).to_csv(self.path, index=False)
        result = assess_dataset_quality(self.dataset)
        check = result["dimensions"]["consistency"]["checks"][0]
        self.assertEqual(check["checked"], 1)
        self.assertEqual(check["affected"], 0)
        self.assertEqual(check["tax_amount_column"], "Tax 5%")


if __name__ == "__main__":
    unittest.main()
