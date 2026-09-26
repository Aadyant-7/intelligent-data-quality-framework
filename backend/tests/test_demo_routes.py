"""Ensure public demo requests cannot reach write routes or private metadata."""

import asyncio
import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException, Request
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

os.environ.setdefault("DATABASE_URL", "sqlite://")

from app import main  # noqa: E402 - set an isolated test URL before importing the app
from app.models import Base, Dataset


class DemoRouteTests(unittest.TestCase):
    def test_write_guard_blocks_before_upload_body_is_parsed(self):
        request = Request({
            "type": "http", "method": "POST", "path": "/datasets/upload",
            "headers": [(b"content-type", b"multipart/form-data")],
            "scheme": "http", "server": ("testserver", 80),
        })

        async def should_not_continue(_request):
            self.fail("The upload route must not parse a public demo request.")

        with patch.object(main, "DEMO_MODE", True):
            response = asyncio.run(main.demo_write_guard(request, should_not_continue))
        self.assertEqual(response.status_code, 403)

    def test_other_dataset_metadata_is_hidden(self):
        engine = create_engine("sqlite://")
        self.addCleanup(engine.dispose)
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            other = Dataset(file_name="private.csv", file_path="uploads/private.csv")
            db.add(other)
            db.commit()
            with patch.object(main, "DEMO_MODE", True), self.assertRaises(HTTPException) as hidden:
                main._get_dataset(db, other.id)
        self.assertEqual(hidden.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
