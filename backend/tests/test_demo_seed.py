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
    def test_seed_recovers_sample_and_reuses_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "sample.csv"
            source.write_text("Amount,Group\n1,A\n2,B\n", encoding="utf-8")
            uploads = root / "uploads"
            engine = create_engine("sqlite://")
            self.addCleanup(engine.dispose)
            Base.metadata.create_all(engine)

            with patch.object(demo_seed, "DEMO_SOURCE", source), \
                 patch.object(demo_seed, "UPLOAD_DIRECTORY", uploads), \
                 patch.object(dataset_storage, "UPLOAD_DIRECTORY", uploads), \
                 Session(engine) as db:
                first = demo_seed.seed_demo_dataset(db)
                first_id = first.id
                self.assertEqual(profile_dataset(first)["rows_count"], 2)

                (uploads / "demo-online-retail-sample.csv").unlink()
                second = demo_seed.seed_demo_dataset(db)
                self.assertEqual(second.id, first_id)
                self.assertEqual(db.query(Dataset).count(), 1)
                self.assertEqual(profile_dataset(second)["rows_count"], 2)


if __name__ == "__main__":
    unittest.main()
