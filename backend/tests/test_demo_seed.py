"""Verify the hosted sample is reproducible after an ephemeral restart."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, Dataset
from app.services import dataset_storage, demo_seed, quality_engine
from app.services.data_profiler import profile_dataset


class DemoSeedTests(unittest.TestCase):
    def test_edited_supermarket_fixture_exercises_quality_rules(self):
        fixture = demo_seed.DATASET_DIRECTORY / "supermarket_sales_demo.csv"
        with patch.object(quality_engine, "resolve_dataset_path", return_value=fixture):
            result = quality_engine.assess_dataset_quality(
                Dataset(id=3, file_name="Supermarket QA example (edited).csv",
                        file_path="uploads/demo-supermarket-sales.csv")
            )
        self.assertEqual(result["overall_quality_score"], 90.99)
        self.assertEqual(result["dimensions"]["uniqueness"]["duplicate_rows"], 30)
        self.assertEqual(result["dimensions"]["validity"]["invalid_rows"], 40)
        line_total = result["dimensions"]["consistency"]["checks"][0]
        self.assertEqual((line_total["checked"], line_total["affected"]), (1000, 120))

    def test_seed_recovers_all_samples_and_reuses_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "sample.csv"
            source.write_text("Amount,Group\n1,A\n2,B\n", encoding="utf-8")
            uploads = root / "uploads"
            engine = create_engine("sqlite://")
            self.addCleanup(engine.dispose)
            Base.metadata.create_all(engine)

            sources = {f"uploads/demo-example-{index}.csv": source for index in range(3)}
            with patch.object(demo_seed, "DEMO_SOURCES", sources), \
                 patch.object(demo_seed, "UPLOAD_DIRECTORY", uploads), \
                 patch.object(dataset_storage, "UPLOAD_DIRECTORY", uploads), \
                 Session(engine) as db:
                first = demo_seed.seed_demo_datasets(db)
                first_ids = [dataset.id for dataset in first]
                self.assertEqual([profile_dataset(dataset)["rows_count"] for dataset in first], [2] * 3)

                (uploads / "demo-example-1.csv").unlink()
                second = demo_seed.seed_demo_datasets(db)
                self.assertEqual([dataset.id for dataset in second], first_ids)
                self.assertEqual(db.query(Dataset).count(), 3)
                self.assertEqual([profile_dataset(dataset)["rows_count"] for dataset in second], [2] * 3)


if __name__ == "__main__":
    unittest.main()
