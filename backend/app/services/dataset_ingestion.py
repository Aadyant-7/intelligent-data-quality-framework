"""Dataset validation, normalization, storage, and metadata extraction."""

from pathlib import Path
from shutil import copyfileobj
from uuid import uuid4

import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models import Dataset


UPLOAD_DIRECTORY = Path(__file__).resolve().parents[2] / "uploads"
SUPPORTED_FILE_EXTENSIONS = {".csv", ".xlsx"}


def ingest_dataset(file: UploadFile, db: Session) -> Dataset:
    """Store a supported dataset, normalize it to CSV, and save its metadata."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="A file name is required.")

    original_filename = Path(file.filename).name
    file_extension = Path(original_filename).suffix.lower()
    if file_extension not in SUPPORTED_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only CSV and Excel (.xlsx) files are supported.",
        )

    UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
    upload_id = uuid4().hex
    source_file_path = UPLOAD_DIRECTORY / f"{upload_id}_{original_filename}"
    normalized_file_path: Path | None = None

    try:
        with source_file_path.open("wb") as destination:
            copyfileobj(file.file, destination)

        if file_extension == ".csv":
            dataframe = pd.read_csv(source_file_path)
            normalized_file_path = source_file_path
        else:
            dataframe = pd.read_excel(source_file_path)
            normalized_file_path = UPLOAD_DIRECTORY / f"{upload_id}_{Path(original_filename).stem}.csv"
            dataframe.to_csv(normalized_file_path, index=False)
            source_file_path.unlink(missing_ok=True)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError, ValueError) as error:
        source_file_path.unlink(missing_ok=True)
        if normalized_file_path:
            normalized_file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"The uploaded file could not be read: {error}") from error

    if normalized_file_path is None:
        raise HTTPException(status_code=500, detail="Dataset normalization did not complete.")

    dataset = Dataset(
        file_name=original_filename,
        file_path=(Path("uploads") / normalized_file_path.name).as_posix(),
        rows_count=len(dataframe.index),
        columns_count=len(dataframe.columns),
    )

    try:
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
    except Exception:
        db.rollback()
        source_file_path.unlink(missing_ok=True)
        normalized_file_path.unlink(missing_ok=True)
        raise

    return dataset
