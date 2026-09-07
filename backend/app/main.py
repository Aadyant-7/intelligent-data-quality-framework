from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Dataset
from app.services.data_profiler import profile_dataset
from app.services.dataset_ingestion import ingest_dataset
from app.services.quality_engine import assess_dataset_quality

app = FastAPI()

class DatasetCreate(BaseModel):
    file_name: str
    file_path: str
    rows_count: int
    columns_count: int


@app.get("/")
def home():
    return {
        "message": "Intelligent Data Quality Assessment and Anomaly Detection Framework"
    }


@app.post("/datasets")
def create_dataset(dataset: DatasetCreate, db: Session = Depends(get_db)):
    new_dataset = Dataset(
        file_name=dataset.file_name,
        file_path=dataset.file_path,
        rows_count=dataset.rows_count,
        columns_count=dataset.columns_count
    )

    db.add(new_dataset)
    db.commit()
    db.refresh(new_dataset)

    return new_dataset


@app.post("/datasets/upload")
def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return ingest_dataset(file, db)


@app.get("/datasets/{dataset_id}/profile")
def get_dataset_profile(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    return profile_dataset(dataset)


@app.get("/datasets/{dataset_id}/quality")
def get_dataset_quality(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    return assess_dataset_quality(dataset)


@app.get("/datasets")
def get_datasets(db: Session = Depends(get_db)):
    datasets = db.query(Dataset).all()

    return datasets
