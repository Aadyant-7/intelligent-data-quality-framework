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

### Anomaly Detection

- Scikit-learn
- Z-score
- IQR
- Isolation Forest

### Frontend (planned)

- React

### Visualization (planned)

- Plotly

### Version Control

- Git
- GitHub

### Deployment (planned)

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

- `POST /datasets/upload` for CSV and Excel (`.xlsx`) uploads
- File-type and readability validation
- Excel-to-CSV normalization for one consistent analysis format
- Unique local storage for uploaded files
- Automatic row and column extraction with Pandas
- Automatic PostgreSQL metadata records for uploaded datasets
- Clean separation of upload logic into a reusable ingestion service

### Phase 4 — Data Profiling Engine ✅

Implemented:

- `GET /datasets/{dataset_id}/profile` for automated dataset profiling
- Row, column, duplicate, and missing-value summaries
- Column data types, inferred logical types, unique values, and sample values
- Numeric descriptive statistics, date ranges, and top category values
- Clear handling for datasets that do not exist

### Phase 5 — Data Quality Engine ✅

Implemented:

- `GET /datasets/{dataset_id}/quality` for an explainable quality assessment
- Weighted scores for completeness, uniqueness, validity, and consistency
- An overall score and human-readable grade
- Issue evidence with severity, affected-record counts, and clear explanations
- Context-aware Online Retail checks: cancellation-style invoices, negative prices, zero-price review, and `StockCode`/description mismatches
- Shared storage-path validation used by profiling and quality services

### Phase 6 — Anomaly Detection Engine ✅

Implemented:

- `GET /datasets/{dataset_id}/anomalies` for numeric anomaly detection on the stored CSV
- IQR and Z-score checks for unusual values in individual numeric columns
- Isolation Forest for unusual combinations of numeric values, when enough data is available
- Counts and sample rows showing the methods that flagged each observation
- Retail context for flagged negative quantities, including cancellation-style invoices
- Clear `not_evaluated` results when a method lacks enough usable data

The endpoint flags observations for investigation; it does not change the uploaded file or call every anomaly a data-quality error. It returns up to 20 example rows. The count covers all flagged rows, with rows flagged by multiple methods counted once.

---

## Assessment Capabilities

Quality scoring uses the first four dimensions below. Anomaly detection is a separate analysis:

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
- [x] Phase 4 — Data Profiling Engine
- [x] Phase 5 — Data Quality Engine
- [x] Phase 6 — Anomaly Detection Engine
- [ ] Phase 7 — Explainability
- [ ] Phase 8 — React Dashboard
- [ ] Phase 9 — Interactive Visualizations
- [ ] Phase 10 — Report Generation
- [ ] Phase 11 — Deployment
- [ ] Phase 12 — Final Documentation & Polish

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
| POST | `/datasets/upload` | Upload a CSV or Excel file and automatically create normalized dataset metadata |
| GET | `/datasets` | Retrieve dataset metadata |
| GET | `/datasets/{dataset_id}/profile` | Generate a detailed profile for an uploaded dataset |
| GET | `/datasets/{dataset_id}/quality` | Calculate explainable data-quality scores and issues |
| GET | `/datasets/{dataset_id}/anomalies` | Find unusual numeric observations with method evidence and retail context |

---

## Documentation

Detailed project development, technical decisions, verification, and limitations are maintained in:

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
