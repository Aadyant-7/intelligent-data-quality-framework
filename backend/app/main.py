from contextlib import asynccontextmanager
import re
from urllib.parse import quote

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
from app.services.dataset_catalog import clear_dataset_history, list_available_datasets, remove_dataset_group
from app.services.dataset_ingestion import ingest_dataset
from app.services.demo_seed import DEMO_DATASET_PATHS, seed_demo_datasets
from app.services.dataset_storage import resolve_dataset_path
from app.services.quality_engine import assess_dataset_quality
from app.services.report_generator import generate_dataset_report
from app.services.visualization_engine import visualize_dataset_column


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if DEMO_MODE:
        with SessionLocal() as db:
            seed_demo_datasets(db)
    yield


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def demo_write_guard(request: Request, call_next):
    if DEMO_MODE and (
        (request.method == "POST" and request.url.path in {"/datasets", "/datasets/upload"})
        or (request.method == "DELETE" and (request.url.path == "/datasets" or request.url.path.startswith("/datasets/")))
    ):
        detail = (
            "Dataset deletion is disabled in the public demo."
            if request.method == "DELETE" else "Uploads are disabled in the public demo."
        )
        return JSONResponse(status_code=403, content={"detail": detail})
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)


def _get_dataset(db: Session, dataset_id: int) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None or (DEMO_MODE and dataset.file_path not in DEMO_DATASET_PATHS):
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return dataset


def _report_download_name(file_name: str) -> str:
    """Build a safe, readable PDF name from the uploaded dataset name."""
    source_name = file_name.replace("\\", "/").rsplit("/", 1)[-1]
    stem = re.sub(r"\.(csv|xlsx)$", "", source_name, flags=re.IGNORECASE)
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", stem).strip(" .")[:100]
    return f"Data Quality Report - {stem or 'Dataset'}.pdf"


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
    if DEMO_MODE and not all(resolve_dataset_path(path).is_file() for path in DEMO_DATASET_PATHS):
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
    download_name = _report_download_name(dataset.file_name)

    return Response(
        content=generate_dataset_report(dataset),
        media_type="application/pdf",
        headers={"Content-Disposition": (
            f'attachment; filename="{download_name if download_name.isascii() else "Data Quality Report.pdf"}"; '
            f"filename*=UTF-8''{quote(download_name)}"
        )},
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
        query = query.filter(Dataset.file_path.in_(DEMO_DATASET_PATHS))
    return list_available_datasets(query.all())


@app.delete("/datasets")
def clear_datasets(db: Session = Depends(get_db)):
    _require_writable_workspace()
    return clear_dataset_history(db)


@app.delete("/datasets/{dataset_id}")
def remove_dataset(dataset_id: int, db: Session = Depends(get_db)):
    _require_writable_workspace()
    return remove_dataset_group(db, dataset_id)
