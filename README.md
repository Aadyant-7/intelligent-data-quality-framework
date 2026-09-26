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

### Frontend

- React
- Vite

### Visualization

- Plotly.js (basic bundle, loaded when charts are opened)

### Reporting

- ReportLab for downloadable PDF assessments

### Version Control

- Git
- GitHub

### Deployment preparation

- Vercel configuration for the React frontend
- Render Blueprint for a sample-only FastAPI service
- Neon PostgreSQL as the intended hosted metadata database
- GitHub Actions build and test checks

The public demo is prepared but has no live URL yet. Provider accounts and hosted configuration are still required.

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

The endpoint flags observations for investigation; it does not change the uploaded file or call every anomaly a data-quality error. It returns 20 example rows by default. The count covers all flagged rows, with rows flagged by multiple methods counted once.

### Phase 7 — Explainability ✅

Implemented:

- Plain-language evidence for every displayed anomaly: observed value and boundary for IQR/Z-score, or model score for Isolation Forest
- A cautious interpretation based on available retail rules, with a suggested next check
- `GET /datasets/{dataset_id}/anomalies/{row_number}/explanation` to inspect any data row, including one outside the default examples
- `offset` and `limit` on the anomaly list to page through all flagged rows (up to 100 per response)

The model explains that a combination is unusual, but it does not claim to identify the field that caused an Isolation Forest flag. Retail interpretations distinguish a possible return from a possible quality issue without making a final business judgment.

### Phase 8 — React Dashboard ✅

Implemented:

- A local React dashboard for uploading and switching between datasets
- An overview of dataset size, available quality scores, and leading findings
- A column-by-column profile, explainable quality findings, and a paginated anomaly review queue
- Row-number lookup with method evidence and a suggested next check
- Loading, empty, and API-error states, with retry controls where useful
- A responsive layout for desktop and smaller screens

The dashboard calls the FastAPI endpoints. It keeps anomaly flags separate from quality errors and shows `Not evaluated` when a rule cannot assess the dataset.

### Phase 9 — Interactive Visualizations ✅

Implemented:

- Interactive Plotly charts for evaluated quality dimensions, missing values, and anomaly signals
- A field explorer for numeric distributions, leading categories, and date activity
- Numeric full-range and typical-range views, with the excluded tail count stated clearly
- Hover, zoom, and reset controls, plus a count table alongside each chart
- `GET /datasets/{dataset_id}/visualizations?column=...` to calculate compact chart data from one stored CSV column

Chart counts are drawn from the current dataset. Method and field anomaly counts can overlap; the separate distinct-row total counts each flagged row once. Identifiers and free text are not plotted as measurements.

### Phase 10 — Report Generation ✅

Implemented:

- `GET /datasets/{dataset_id}/report` to download an A4 PDF assessment
- A working **Download PDF report** button on the dataset overview
- Overall and dimension scores, evaluation status, counted quality findings, and a column profile
- Distinct anomaly-row counts, method evidence, five review examples, and retail cancellation context when available
- Clear limits for large reports: up to 40 columns, 50 findings, and 30 method/field rows, with truncation stated in the PDF

The report recalculates results from the stored normalized CSV when requested. It does not save analysis in PostgreSQL or treat unusual records as proven errors. PDF generation runs during the request, so large datasets can take several seconds.

### Phase 11 — Deployment preparation (in progress)

The repository now has a free-hosting setup for a **read-only public sample**. In hosted demo mode, startup restores the tracked 5,000-row retail sample, the API lists only that sample, and both upload and manual metadata creation are rejected. The website labels this mode and hides its upload form. Local development keeps the full CSV and `.xlsx` upload workflow.

`render.yaml` describes the free backend service, and `frontend/vercel.json` supports the Vite single-page frontend. Hosted secrets and the allowed frontend origin are configured in provider settings, not in Git. `/health` is a lightweight hosting check; `/ready` also checks the database on demand. A GitHub Actions workflow checks backend tests and a demo frontend build.

**Deployment status:** configuration and local checks are complete; a live Render, Vercel, and Neon deployment is pending provider accounts. No live service has been verified. The free backend filesystem is temporary, which is why the hosted demo does not accept user uploads.

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
- [x] Phase 7 — Explainability
- [x] Phase 8 — React Dashboard
- [x] Phase 9 — Interactive Visualizations
- [x] Phase 10 — Report Generation
- [ ] Phase 11 — Deployment (configuration ready; live launch pending)
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

### 4. Start the dashboard

In a second terminal, from the repository root:

    cd frontend
    npm ci
    npm run dev

Open `http://127.0.0.1:5173`. Keep the backend running at `http://127.0.0.1:8000`; Vite forwards dashboard `/api` requests to it during local development. `npm run build` checks and builds the frontend. The dashboard accepts the backend's current `.csv` and `.xlsx` upload formats.

---

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Backend health/welcome response |
| GET | `/health` | Lightweight hosting health check |
| GET | `/ready` | Check the database and sample availability on demand |
| POST | `/datasets` | Store dataset metadata |
| POST | `/datasets/upload` | Upload a CSV or Excel file and automatically create normalized dataset metadata |
| GET | `/datasets` | Retrieve dataset metadata |
| GET | `/datasets/{dataset_id}/profile` | Generate a detailed profile for an uploaded dataset |
| GET | `/datasets/{dataset_id}/quality` | Calculate explainable data-quality scores and issues |
| GET | `/datasets/{dataset_id}/report` | Download the current quality and anomaly assessment as a PDF |
| GET | `/datasets/{dataset_id}/visualizations?column=...` | Return bounded histogram, category, or date counts for one stored column |
| GET | `/datasets/{dataset_id}/anomalies` | Find unusual numeric observations with method evidence and retail context |
| GET | `/datasets/{dataset_id}/anomalies/{row_number}/explanation` | Explain a specific one-based data row, flagged or not |

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
