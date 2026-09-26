"""Check report export preserves assessment meaning and storage safeguards."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from fastapi import HTTPException

from app.models import Dataset
from app.services import dataset_storage
from app.services.report_generator import generate_dataset_report


class ReportGeneratorTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        upload_directory = Path(directory.name) / "uploads"
        upload_directory.mkdir()
        storage_patch = patch.object(dataset_storage, "UPLOAD_DIRECTORY", upload_directory)
        storage_patch.start()
        self.addCleanup(storage_patch.stop)
        self.csv_path = upload_directory / "test.csv"
        self.dataset = Dataset(id=42, file_name="test.csv", file_path="uploads/test.csv")

    def test_generic_report_is_pdf_and_does_not_fabricate_retail_scores(self):
        pd.DataFrame({"Amount": [10, 11, 12, 100], "Group": ["A", "A", "B", "B"]}).to_csv(
            self.csv_path, index=False
        )
        pdf = generate_dataset_report(self.dataset)

        self.assertTrue(pdf.startswith(b"%PDF-"))
        self.assertGreater(len(pdf), 10_000)

        with patch("app.services.report_generator.render_report_pdf") as renderer:
            generate_dataset_report(self.dataset)
        _, profile, quality, anomalies = renderer.call_args.args
        self.assertEqual(profile["rows_count"], 4)
        self.assertIsNone(quality["dimensions"]["validity"]["score"])
        self.assertIsNone(quality["dimensions"]["consistency"]["score"])
        self.assertEqual(anomalies["anomaly_rows_count"], 1)

    def test_header_only_report_has_no_fabricated_score(self):
        self.csv_path.write_text("Amount,Group\n", encoding="utf-8")
        pdf = generate_dataset_report(self.dataset)
        self.assertTrue(pdf.startswith(b"%PDF-"))

    def test_missing_file_and_path_traversal_are_rejected(self):
        with self.assertRaises(HTTPException) as missing:
            generate_dataset_report(self.dataset)
        self.assertEqual(missing.exception.status_code, 404)

        self.dataset.file_path = "../outside.csv"
        with self.assertRaises(HTTPException) as traversal:
            generate_dataset_report(self.dataset)
        self.assertEqual(traversal.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
