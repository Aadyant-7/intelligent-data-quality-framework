from fastapi import Depends, FastAPI, File, HTTPException, Query, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Dataset
from app.services.anomaly_engine import (
    DEFAULT_EXAMPLES,
    MAX_EXAMPLES,
    detect_dataset_anomalies,
    explain_dataset_row,
)
from app.services.data_profiler import profile_dataset
from app.services.dataset_ingestion import ingest_dataset
from app.services.quality_engine import assess_dataset_quality
from app.services.report_generator import generate_dataset_report
from app.services.visualization_engine import visualize_dataset_column

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


@app.get("/datasets/{dataset_id}/report")
def get_dataset_report(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    return Response(
        content=generate_dataset_report(dataset),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="dataset-{dataset_id}-quality-report.pdf"'},
    )


@app.get("/datasets/{dataset_id}/visualizations")
def get_dataset_visualization(
    dataset_id: int,
    column: str = Query(min_length=1),
    db: Session = Depends(get_db),
):
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    return visualize_dataset_column(dataset, column)


@app.get("/datasets/{dataset_id}/anomalies")
def get_dataset_anomalies(
    dataset_id: int,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=DEFAULT_EXAMPLES, ge=1, le=MAX_EXAMPLES),
    db: Session = Depends(get_db),
):
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    return detect_dataset_anomalies(dataset, offset=offset, limit=limit)


@app.get("/datasets/{dataset_id}/anomalies/{row_number}/explanation")
def get_anomaly_explanation(
    dataset_id: int, row_number: int, db: Session = Depends(get_db)
):
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    return explain_dataset_row(dataset, row_number)


@app.get("/datasets")
def get_datasets(db: Session = Depends(get_db)):
    datasets = db.query(Dataset).all()

    return datasets
