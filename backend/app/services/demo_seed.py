"""Make the public reference sample available in read-only demo mode."""

from pathlib import Path
from shutil import copyfile

import pandas as pd
from sqlalchemy.orm import Session

from app.models import Dataset
from app.services.dataset_storage import UPLOAD_DIRECTORY


DEMO_DATASET_PATH = "uploads/demo-online-retail-sample.csv"
DEMO_SOURCE = Path(__file__).resolve().parents[3] / "datasets" / "online_retail_sample.csv"


def seed_demo_dataset(db: Session) -> Dataset:
    """Refresh the public sample and keep one matching metadata record."""
    UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
    destination = UPLOAD_DIRECTORY / Path(DEMO_DATASET_PATH).name
    copyfile(DEMO_SOURCE, destination)
    dataframe = pd.read_csv(destination)

    dataset = db.query(Dataset).filter(Dataset.file_path == DEMO_DATASET_PATH).first()
    if dataset is None:
        dataset = Dataset(file_path=DEMO_DATASET_PATH)
        db.add(dataset)
    dataset.file_name = DEMO_SOURCE.name
    dataset.rows_count = len(dataframe)
    dataset.columns_count = len(dataframe.columns)
    db.commit()
    db.refresh(dataset)
    return dataset
