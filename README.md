# Intelligent Data Quality Assessment & Anomaly Detection Framework

An enterprise-style data analytics platform that will profile uploaded CSV datasets, assess data quality, detect anomalies, and present explainable insights through an interactive dashboard.

## Current status

**Phase 1 complete — Environment & Backend Foundation**

The backend can store and retrieve dataset metadata through a FastAPI API connected to PostgreSQL.

## Tech stack

- Python, FastAPI, Uvicorn
- PostgreSQL, SQLAlchemy
- Pandas, NumPy
- Planned: Scikit-learn, React, Plotly

## Completed in Phase 1

- FastAPI backend and automatic API documentation
- PostgreSQL database connection through SQLAlchemy
- `Dataset` ORM model and `datasets` table
- `POST /datasets` to create dataset metadata records
- `GET /datasets` to retrieve stored dataset records
- FastAPI-managed database sessions
- Environment-variable based database configuration

## Run locally

From the `backend` directory:

```powershell
uvicorn app.main:app --reload
```

Open the API documentation at `http://127.0.0.1:8000/docs`.

> Create `backend/.env` locally before running the app. It must contain your own PostgreSQL connection URL and is intentionally not committed to Git.

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/` | Backend health/welcome message |
| POST | `/datasets` | Store dataset metadata |
| GET | `/datasets` | Retrieve all dataset metadata |

## Roadmap

- [x] Phase 1 — Environment & Backend Foundation
- [ ] Phase 2 — Dataset Research
- [ ] Phase 3 — Dataset Ingestion
- [ ] Phase 4 — Data Profiling Engine
- [ ] Phase 5 — Data Quality Engine
- [ ] Phase 6 — Anomaly Detection Engine
- [ ] Phase 7 — Explainability
- [ ] Phase 8–10 — Dashboard, Visualizations, Reports
- [ ] Phase 11 — Deployment
- [ ] Phase 12 — Documentation & Interview Preparation
