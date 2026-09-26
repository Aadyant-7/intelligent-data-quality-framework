"""Local library shows distinct usable files and clears only on request."""

import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException, UploadFile
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, Dataset
from app.services import dataset_ingestion, dataset_storage
from app.services.dataset_catalog import clear_dataset_history, list_available_datasets, remove_dataset_group
from app.services.dataset_ingestion import ingest_dataset


class DatasetCatalogTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.uploads = self.root / "uploads"
        self.uploads.mkdir()
        for module in (dataset_storage, dataset_ingestion):
            directory_patch = patch.object(module, "UPLOAD_DIRECTORY", self.uploads)
            directory_patch.start()
            self.addCleanup(directory_patch.stop)
        engine = create_engine("sqlite://")
        self.addCleanup(engine.dispose)
        Base.metadata.create_all(engine)
        self.db = Session(engine)
        self.addCleanup(self.db.close)

    def upload(self, name: str, content: bytes) -> Dataset:
        return ingest_dataset(UploadFile(filename=name, file=BytesIO(content)), self.db)

    def test_repeat_upload_reuses_record_and_stored_file(self):
        first = self.upload("sales.csv", b"Amount,Type\n1,A\n2,B\n")
        second = self.upload("same-data.csv", b"Amount,Type\n1,A\n2,B\n")

        self.assertEqual(second.id, first.id)
        self.assertEqual(self.db.query(Dataset).count(), 1)
        self.assertEqual(len(list(self.uploads.iterdir())), 1)

    def test_same_name_with_different_data_stays_separate(self):
        first = self.upload("sales.csv", b"Amount\n1\n")
        second = self.upload("sales.csv", b"Amount\n2\n")

        self.assertNotEqual(first.id, second.id)
        self.assertEqual(len(list_available_datasets(self.db.query(Dataset).all())), 2)

    def test_library_hides_old_copies_and_broken_paths_without_deleting_them(self):
        first = self.upload("sales.csv", b"Amount\n1\n2\n")
        copy = self.uploads / "old-copy.csv"
        copy.write_bytes((self.uploads / Path(first.file_path).name).read_bytes())
        self.db.add_all([
            Dataset(file_name="old-copy.csv", file_path="uploads/old-copy.csv", rows_count=2, columns_count=1),
            Dataset(file_name="missing.csv", file_path="uploads/missing.csv", rows_count=2, columns_count=1),
            Dataset(file_name="outside.csv", file_path="../outside.csv", rows_count=2, columns_count=1),
        ])
        self.db.commit()

        visible = list_available_datasets(self.db.query(Dataset).all())

        self.assertEqual(len(visible), 1)
        self.assertEqual(visible[0].file_name, "old-copy.csv")
        self.assertEqual(self.db.query(Dataset).count(), 4)
        self.assertTrue(copy.exists())

    def test_clear_history_removes_saved_uploads_and_metadata_only(self):
        self.upload("sales.csv", b"Amount\n1\n")
        unrelated = self.root / "outside.csv"
        unrelated.write_text("keep this", encoding="utf-8")
        self.db.add(Dataset(file_name="outside.csv", file_path="../outside.csv"))
        self.db.commit()

        result = clear_dataset_history(self.db)

        self.assertEqual(result, {"deleted_records": 2, "deleted_files": 1, "file_errors": 0})
        self.assertEqual(self.db.query(Dataset).count(), 0)
        self.assertEqual(list(self.uploads.iterdir()), [])
        self.assertTrue(unrelated.exists())

    def test_remove_one_dataset_also_removes_hidden_identical_copy(self):
        first = self.upload("one.csv", b"Amount\n1\n")
        original_path = self.uploads / Path(first.file_path).name
        copy = self.uploads / "copy.csv"
        copy.write_bytes(original_path.read_bytes())
        duplicate = Dataset(file_name="copy.csv", file_path="uploads/copy.csv", rows_count=1, columns_count=1)
        self.db.add(duplicate)
        self.db.commit()
        other = self.upload("other.csv", b"Amount\n2\n")
        other_path = self.uploads / Path(other.file_path).name

        result = remove_dataset_group(self.db, duplicate.id)

        self.assertEqual(result, {"deleted_records": 2, "deleted_files": 2, "file_errors": 0})
        self.assertEqual([item.id for item in list_available_datasets(self.db.query(Dataset).all())], [other.id])
        self.assertFalse(original_path.exists())
        self.assertFalse(copy.exists())
        self.assertTrue(other_path.exists())

    def test_remove_unknown_dataset_is_404(self):
        with self.assertRaises(HTTPException) as error:
            remove_dataset_group(self.db, 999999)
        self.assertEqual(error.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
