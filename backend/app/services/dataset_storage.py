"""Shared local storage helpers for normalized datasets."""

from pathlib import Path

from fastapi import HTTPException


UPLOAD_DIRECTORY = Path(__file__).resolve().parents[2] / "uploads"


def resolve_dataset_path(stored_path: str) -> Path:
    """Resolve a stored dataset path while preventing path traversal."""
    storage_root = UPLOAD_DIRECTORY.resolve()
    candidate_path = (UPLOAD_DIRECTORY.parent / stored_path).resolve()

    if storage_root not in candidate_path.parents:
        raise HTTPException(status_code=400, detail="Dataset storage path is invalid.")

    return candidate_path
