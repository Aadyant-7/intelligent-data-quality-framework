"""CSV validation, storage, and dataset metadata extraction."""

from pathlib import Path
from shutil import copyfileobj
from uuid import uuid4

import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models import Dataset


UPLOAD_DIRECTORY = Path(__file__).resolve().parents[2] / "uploads"
ALLOWED_FILE_EXTENSION = ".csv"


def ingest_csv(file: UploadFile, db: Session) -> Dataset:
    """Store a CSV, extract its dimensions, and save its metadata."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="A file name is required.")

    original_filename = Path(file.filename).name
    if Path(original_filename).suffix.lower() != ALLOWED_FILE_EXTENSION:
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid4().hex}_{original_filename}"
    stored_file_path = UPLOAD_DIRECTORY / stored_filename

    try:
        with stored_file_path.open("wb") as destination:
            copyfileobj(file.file, destination)

        dataframe = pd.read_csv(stored_file_path)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as error:
        stored_file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"The CSV could not be read: {error}") from error

    dataset = Dataset(
        file_name=original_filename,
        file_path=(Path("uploads") / stored_filename).as_posix(),
        rows_count=len(dataframe.index),
        columns_count=len(dataframe.columns),
    )

    try:
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
    except Exception:
        db.rollback()
        stored_file_path.unlink(missing_ok=True)
        raise

    return dataset
