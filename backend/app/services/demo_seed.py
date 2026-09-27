"""Restore the public retail examples on ephemeral demo hosts."""

from pathlib import Path
from shutil import copyfile

import pandas as pd
from sqlalchemy.orm import Session

from app.models import Dataset
from app.services.dataset_storage import UPLOAD_DIRECTORY


DATASET_DIRECTORY = Path(__file__).resolve().parents[3] / "datasets"
DEMO_SOURCES = {
    "uploads/demo-online-retail-sample.csv": DATASET_DIRECTORY / "online_retail_sample.csv",
    "uploads/demo-retail-store-sales.csv": DATASET_DIRECTORY / "retail_store_sales_demo.csv",
    "uploads/demo-supermarket-sales.csv": DATASET_DIRECTORY / "supermarket_sales_demo.csv",
}
DEMO_DATASET_PATHS = frozenset(DEMO_SOURCES)


def seed_demo_datasets(db: Session) -> list[Dataset]:
    """Refresh public samples and reuse matching metadata records."""
    UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
    datasets = []
    for storage_path, source in DEMO_SOURCES.items():
        destination = UPLOAD_DIRECTORY / Path(storage_path).name
        copyfile(source, destination)
        dataframe = pd.read_csv(destination)
        dataset = db.query(Dataset).filter(Dataset.file_path == storage_path).first()
        if dataset is None:
            dataset = Dataset(file_path=storage_path)
            db.add(dataset)
        dataset.file_name = source.name
        dataset.rows_count = len(dataframe)
        dataset.columns_count = len(dataframe.columns)
        datasets.append(dataset)
    db.commit()
    for dataset in datasets:
        db.refresh(dataset)
    return datasets
