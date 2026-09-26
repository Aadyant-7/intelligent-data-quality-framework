from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import CORS_ORIGINS, DEMO_MODE
from app.database import SessionLocal, engine, get_db
from app.models import Base, Dataset
from app.services.anomaly_engine import (
    DEFAULT_EXAMPLES,
    MAX_EXAMPLES,
    detect_dataset_anomalies,
    explain_dataset_row,
)
from app.services.data_profiler import profile_dataset
from app.services.dataset_ingestion import ingest_dataset
from app.services.demo_seed import DEMO_DATASET_PATH, seed_demo_dataset
from app.services.dataset_storage import resolve_dataset_path
from app.services.quality_engine import assess_dataset_quality
from app.services.report_generator import generate_dataset_report
from app.services.visualization_engine import visualize_dataset_column


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if DEMO_MODE:
        with SessionLocal() as db:
            seed_demo_dataset(db)
    yield


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def demo_write_guard(request: Request, call_next):
    if DEMO_MODE and request.method == "POST" and request.url.path in {"/datasets", "/datasets/upload"}:
        return JSONResponse(status_code=403, content={"detail": "Uploads are disabled in the public demo."})
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def _get_dataset(db: Session, dataset_id: int) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None or (DEMO_MODE and dataset.file_path != DEMO_DATASET_PATH):
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return dataset


def _require_writable_workspace() -> None:
    if DEMO_MODE:
        raise HTTPException(status_code=403, detail="Uploads are disabled in the public demo.")


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


@app.get("/health")
def health():
    if DEMO_MODE and not resolve_dataset_path(DEMO_DATASET_PATH).is_file():
        raise HTTPException(status_code=503, detail="Demo dataset is unavailable.")
    return {"status": "ok"}


@app.get("/ready")
def ready():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    health()
    return {"status": "ready"}


@app.post("/datasets")
def create_dataset(dataset: DatasetCreate, db: Session = Depends(get_db)):
    _require_writable_workspace()
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
    _require_writable_workspace()
    return ingest_dataset(file, db)


@app.get("/datasets/{dataset_id}/profile")
def get_dataset_profile(dataset_id: int, db: Session = Depends(get_db)):
    dataset = _get_dataset(db, dataset_id)

    return profile_dataset(dataset)


@app.get("/datasets/{dataset_id}/quality")
def get_dataset_quality(dataset_id: int, db: Session = Depends(get_db)):
    dataset = _get_dataset(db, dataset_id)

    return assess_dataset_quality(dataset)


@app.get("/datasets/{dataset_id}/report")
def get_dataset_report(dataset_id: int, db: Session = Depends(get_db)):
    dataset = _get_dataset(db, dataset_id)

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
    dataset = _get_dataset(db, dataset_id)

    return visualize_dataset_column(dataset, column)


@app.get("/datasets/{dataset_id}/anomalies")
def get_dataset_anomalies(
    dataset_id: int,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=DEFAULT_EXAMPLES, ge=1, le=MAX_EXAMPLES),
    db: Session = Depends(get_db),
):
    dataset = _get_dataset(db, dataset_id)

    return detect_dataset_anomalies(dataset, offset=offset, limit=limit)


@app.get("/datasets/{dataset_id}/anomalies/{row_number}/explanation")
def get_anomaly_explanation(
    dataset_id: int, row_number: int, db: Session = Depends(get_db)
):
    dataset = _get_dataset(db, dataset_id)

    return explain_dataset_row(dataset, row_number)


@app.get("/datasets")
def get_datasets(db: Session = Depends(get_db)):
    query = db.query(Dataset)
    if DEMO_MODE:
        query = query.filter(Dataset.file_path == DEMO_DATASET_PATH)
    datasets = query.all()

    return datasets
