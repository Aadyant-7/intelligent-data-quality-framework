"""Verify the hosted sample is reproducible after an ephemeral restart."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, Dataset
from app.services import dataset_storage, demo_seed
from app.services.data_profiler import profile_dataset


class DemoSeedTests(unittest.TestCase):
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
