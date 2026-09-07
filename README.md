# Intelligent Data Quality Assessment & Anomaly Detection Framework

An enterprise-style data analytics platform designed to automatically profile structured datasets, assess data quality, detect statistical and machine-learning-based anomalies, and present explainable insights through an interactive dashboard.

The project is being developed around real-world transactional data rather than a fabricated demonstration dataset.

---

## Project Overview

Modern data pipelines frequently contain missing values, duplicates, inconsistent records, invalid values, and statistical anomalies.

This project aims to build an automated framework that can:

- Ingest structured datasets
- Profile their structure and characteristics
- Measure multiple dimensions of data quality
- Detect unusual observations
- Distinguish potential errors from legitimate business events
- Explain detected issues
- Present results through an interactive dashboard
- Generate a data-quality report

### Planned Workflow

    Dataset Upload
          ↓
    Data Ingestion
          ↓
    Data Profiling
          ↓
    Data Quality Assessment
          ↓
    Anomaly Detection
          ↓
    Explainable Insights
          ↓
    Interactive Dashboard
          ↓
    Quality Report

---

## Tech Stack

### Backend

- Python
- FastAPI
- Uvicorn

### Data Processing

- Pandas
- NumPy

### Database

- PostgreSQL
- SQLAlchemy

### Machine Learning / Statistics

- Scikit-learn
- Z-score
- IQR
- Isolation Forest

### Frontend

- React

### Visualization

- Plotly

### Version Control

- Git
- GitHub

### Deployment

- Vercel
- Render
- Neon PostgreSQL
- Free-tier infrastructure where practical

---

## Current Status

### Phase 1 — Environment & Backend Foundation ✅

Implemented:

- FastAPI backend
- PostgreSQL database
- SQLAlchemy ORM
- `Dataset` database model
- Database session management
- Pydantic request validation
- Dataset metadata APIs
- Environment-variable based configuration
- Git/GitHub version control

### Phase 2 — Dataset Research ✅

Primary dataset:

**UCI Online Retail Dataset**

Key findings from dataset research:

- 541,909 transaction-line records
- 8 columns
- 25,900 unique invoices
- 4,070 unique products
- 4,372 identified customers
- 38 countries
- 24.93% missing `CustomerID` values
- 5,268 duplicate rows
- 10,624 negative-quantity records
- 2,515 zero-price records
- 650 `StockCode` values associated with multiple descriptions

The research also established an important design principle:

> An anomaly is not automatically a data-quality error.

For example, negative quantities can represent legitimate cancellation or return transactions.

### Phase 3 — Dataset Ingestion ✅

Implemented:

- `POST /datasets/upload` for CSV uploads
- CSV extension and readability validation
- Unique local storage for uploaded files
- Automatic row and column extraction with Pandas
- Automatic PostgreSQL metadata records for uploaded datasets
- Clean separation of upload logic into a reusable ingestion service

---

## Data Quality Dimensions

The framework will initially evaluate:

### Completeness

Missing values and incomplete records.

### Uniqueness

Duplicate records and unexpected duplication.

### Validity

Values that violate defined structural or business rules.

### Consistency

Relationships between related fields.

### Anomaly Detection

Statistically and algorithmically unusual observations.

### Context-Aware Rules

Business context used to distinguish legitimate unusual values from potential errors.

---

## Roadmap

- [x] Phase 1 — Environment & Backend Foundation
- [x] Phase 2 — Dataset Research
- [x] Phase 3 — Dataset Ingestion
- [ ] Phase 4 — Data Profiling Engine
- [ ] Phase 5 — Data Quality Engine
- [ ] Phase 6 — Anomaly Detection Engine
- [ ] Phase 7 — Explainability
- [ ] Phase 8 — React Dashboard
- [ ] Phase 9 — Interactive Visualizations
- [ ] Phase 10 — Report Generation
- [ ] Phase 11 — Deployment
- [ ] Phase 12 — Documentation & Interview Preparation

---

## Local Development

### 1. Navigate to the backend

    cd backend

### 2. Activate the virtual environment

    .\venv\Scripts\Activate.ps1

### 3. Start the FastAPI development server

    uvicorn app.main:app --reload

The backend runs at:

    http://127.0.0.1:8000

Interactive API documentation:

    http://127.0.0.1:8000/docs

Alternative API documentation:

    http://127.0.0.1:8000/redoc

The local `backend/.env` file must contain the PostgreSQL connection configuration. It is intentionally excluded from Git.

---

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Backend health/welcome response |
| POST | `/datasets` | Store dataset metadata |
| POST | `/datasets/upload` | Upload a CSV and automatically create its metadata record |
| GET | `/datasets` | Retrieve dataset metadata |

---

## Project Structure

    intelligent-data-quality-framework/
    │
    ├── backend/
    │   ├── app/
    │   │   ├── __init__.py
    │   │   ├── main.py
    │   │   ├── database.py
    │   │   ├── models.py
    │   │   └── services/
    │   │       └── dataset_ingestion.py
    │   ├── venv/
    │   ├── .env
    │   ├── uploads/
    │   └── requirements.txt
    │
├── datasets/
│   ├── Online Retail.xlsx
│   └── online_retail_sample.csv
    │
    ├── docs/
    │   └── Documentation.md
    │
    ├── frontend/
    │
    ├── .gitignore
    └── README.md

---

## Documentation

Detailed project development, technical concepts, decisions, problems encountered, solutions, and interview preparation are maintained in:

    docs/Documentation.md

The documentation is expanded as each development phase is completed.

---

## Project Goal

The final objective is to build a deployable, enterprise-style data-quality platform that demonstrates practical skills in:

- Backend development
- REST APIs
- Database design
- Data engineering
- Data analysis
- Statistical analysis
- Machine learning
- Explainable analytics
- Frontend development
- Data visualization
- Deployment
