"""Keep the local dataset library usable without changing saved data on reads."""

from hashlib import file_digest
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Dataset
from app.services.dataset_storage import resolve_dataset_path


def _existing_path(dataset: Dataset) -> Path | None:
    try:
        path = resolve_dataset_path(dataset.file_path)
    except HTTPException:
        return None
    return path if path.is_file() else None


def _fingerprint(path: Path) -> tuple[int, bytes]:
    with path.open("rb") as source:
        return path.stat().st_size, file_digest(source, "sha256").digest()


def list_available_datasets(records: list[Dataset]) -> list[Dataset]:
    """Show the newest saved copy of each distinct, readable dataset."""
    seen: set[tuple[int, bytes]] = set()
    available = []
    for dataset in sorted(records, key=lambda item: item.id, reverse=True):
        path = _existing_path(dataset)
        if path is None:
            continue
        try:
            fingerprint = _fingerprint(path)
        except OSError:
            continue
        if fingerprint not in seen:
            seen.add(fingerprint)
            available.append(dataset)
    return available


def find_duplicate_dataset(db: Session, new_path: Path, rows: int, columns: int) -> Dataset | None:
    """Reuse an existing record when its normalized CSV is byte-for-byte identical."""
    fingerprint = _fingerprint(new_path)
    matches = (
        db.query(Dataset)
        .filter(Dataset.rows_count == rows, Dataset.columns_count == columns)
        .order_by(Dataset.id.desc())
    )
    for dataset in matches:
        path = _existing_path(dataset)
        if path is not None:
            try:
                if _fingerprint(path) == fingerprint:
                    return dataset
            except OSError:
                continue
    return None


def clear_dataset_history(db: Session) -> dict[str, int]:
    """Remove local metadata and its safely resolved upload files on request."""
    records = db.query(Dataset).all()
    paths = {path for record in records if (path := _existing_path(record)) is not None}
    db.query(Dataset).delete(synchronize_session=False)
    db.commit()

    removed_files = 0
    file_errors = 0
    for path in paths:
        try:
            path.unlink(missing_ok=True)
            removed_files += 1
        except OSError:
            file_errors += 1
    return {"deleted_records": len(records), "deleted_files": removed_files, "file_errors": file_errors}


def remove_dataset_group(db: Session, dataset_id: int) -> dict[str, int]:
    """Remove one visible dataset and identical older copies so it stays gone."""
    selected = db.get(Dataset, dataset_id)
    if selected is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    selected_path = _existing_path(selected)
    fingerprint = _fingerprint(selected_path) if selected_path is not None else None
    records = [selected]
    paths = {selected_path} if selected_path is not None else set()
    if fingerprint is not None:
        for candidate in db.query(Dataset).filter(Dataset.id != dataset_id):
            path = _existing_path(candidate)
            if path is None:
                continue
            try:
                if _fingerprint(path) == fingerprint:
                    records.append(candidate)
                    paths.add(path)
            except OSError:
                continue

    db.query(Dataset).filter(Dataset.id.in_([record.id for record in records])).delete(
        synchronize_session=False
    )
    db.commit()

    removed_files = 0
    file_errors = 0
    for path in paths:
        try:
            path.unlink(missing_ok=True)
            removed_files += 1
        except OSError:
            file_errors += 1
    return {"deleted_records": len(records), "deleted_files": removed_files, "file_errors": file_errors}
