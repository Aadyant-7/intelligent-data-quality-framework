# Intelligent Data Quality Assessment & Anomaly Detection Framework

An educational data-quality tool that profiles structured datasets, scores the checks it can evaluate, flags unusual records, and explains the evidence in a dashboard and PDF report.

The reference data is a real Online Retail dataset. An unusual transaction is a reason to investigate, not automatically an error.

**Try the read-only public demo:** [Data Quality Studio](https://intelligent-data-quality-framework.vercel.app). It opens a 5,000-row Online Retail sample. [API health](https://intelligent-data-quality-api.onrender.com/health) may respond slowly after inactivity because the free service sleeps.

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

### Workflow

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

### Deployment

- Vercel Hobby hosts the React frontend
- Render Free hosts the sample-only FastAPI service from `render.yaml`
- Neon Free stores the hosted sample's metadata in PostgreSQL
- GitHub Actions checks backend tests and the demo frontend build

The hosted workspace is read-only. Run the project locally to upload your own CSV or `.xlsx` file.

The local library shows one entry per distinct stored CSV and skips old records whose upload file is missing or has an invalid storage path. Uploading the same file again reuses its saved entry. The remove button beside an entry deletes that dataset and identical saved copies after confirmation. **Clear history** removes all local dataset records and their stored upload files after confirmation. To use a removed dataset again, re-upload the original file. Neither control is available in the public demo.

**Open either version:** [Public sample demo](https://intelligent-data-quality-framework.vercel.app/) · [Local dashboard with uploads](http://127.0.0.1:5173/) (requires the local backend and frontend to be running).

**Reading the results:** Overview previews the dataset and its leading quality findings; Profile describes columns, missing cells, and duplicate rows; Quality shows the weighted score and the evidence behind each finding; Anomalies lists unusual numeric rows for investigation; Visualizations charts the same underlying counts and one chosen field. The anomaly queue is ordered by review priority, not source row number. Use **Source row → Explain** to inspect any one-based data row; its result appears beside the lookup. Numeric anomaly flags are not proof of data errors, and missing fields are covered in Profile and Quality. The PDF collects the main findings for sharing.

**How to read the score:** Completeness weighs both overall filled-cell coverage and the least-complete column, with an extra deduction capped at 15 completeness points. The overall score then blends the weighted average of evaluated dimensions equally with the lowest evaluated dimension. This prevents strong checks from hiding a weak area. The full local retail file scores **87.56** and the 5,000-row local sample **89.57**; their weighted averages alone would be 91.55 and 94.81. Quality and the PDF show the calculation and affected columns. The score still cannot know which fields are essential to a particular task. Retail validity and consistency are **Not evaluated** for unrelated data such as Titanic and excluded from its score. Statistical anomaly flags do not lower quality scores by themselves; suggested next steps come from explicit rules, not a language model.

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

### Phase 11 — Deployment ✅

The repository now has a free-hosting setup for a **read-only public sample**. In hosted demo mode, startup restores the tracked 5,000-row retail sample, the API lists only that sample, and both upload and manual metadata creation are rejected. The website labels this mode and hides its upload form. Local development keeps the full CSV and `.xlsx` upload workflow.

`render.yaml` describes the free backend service, and `frontend/vercel.json` supports the Vite single-page frontend. Hosted secrets and the allowed frontend origin are configured in provider settings, not in Git. `/health` is a lightweight hosting check; `/ready` also checks the database on demand. A GitHub Actions workflow checks backend tests and a demo frontend build.

**Live deployment:** [React dashboard](https://intelligent-data-quality-framework.vercel.app) · [FastAPI service](https://intelligent-data-quality-api.onrender.com) · Neon Free metadata database. The free backend filesystem is temporary, so the hosted demo does not accept user uploads. Render can take around a minute to wake after inactivity; the tracked sample is restored when the service starts.

At its original Phase 11 verification, before the completeness formula changed, the live deployment showed its 5,000-row sample with a 98.61 quality score, 877 anomaly-flagged rows, working charts and row explanations, and a downloadable PDF. Unknown dataset IDs returned 404; demo write routes returned 403. Only the Vercel production origin passed the API's configured CORS preflight. The GitHub Actions check for the deployment setup passed. These results describe that historical verification, not the revised local score or every possible dataset.

### Phase 12 — Final Documentation & Polish ✅

The dashboard now removes a workspace chevron that implied a menu, hides search when there is only one dataset, and drops navigation cards that repeated the section tabs. Plotly's unused Share control and extra toolbar buttons were removed. Quality errors offer a retry from the overview and charts. A retry refreshes quality without clearing the already loaded profile and anomaly results. The empty public-demo state explains that the free API may be waking up. The dataset header also stacks cleanly on phones.

The final check covered the backend's 26 automated tests, Python compilation, and the production frontend build. The hosted sample and its controls were checked in a browser. See [project documentation](docs/Documentation.md) for the verification record and current limits.

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
- [x] Phase 11 — Deployment (free, read-only public demo)
- [x] Phase 12 — Final Documentation & Polish

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
| DELETE | `/datasets` | Clear local saved datasets and their upload files (disabled in demo mode) |
| DELETE | `/datasets/{dataset_id}` | Remove one local dataset and identical saved copies (disabled in demo mode) |
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

The documentation records the completed phases, verification evidence, and remaining limits.

### Stabilization review (September 2026)

A three-pass QA review checked upload, profiling, scoring, anomalies, explanations, charts, reports, the React dashboard, and the hosted sample. Two reproduced edge cases were fixed: a damaged `.xlsx` archive now returns HTTP 400 and removes its temporary file, and numeric profile values that JSON cannot represent (such as infinity) now appear as `null` instead of crashing the response. The final backend suite passed 28 tests, backend compilation and the frontend production build passed, and the local retail sample still returned a 98.61 quality score and 877 flagged rows. The public demo remains read-only; local uploads are available when both local servers are running. See the detailed QA record in `docs/Documentation.md`.

### Local library follow-up (September 2026)

The local list now hides missing-file records and repeated copies by comparing normalized CSV content. Re-uploading identical content does not add another record or file. A two-step **Clear history** control deletes all local dataset records and their stored uploads when confirmed; it also clears older entries hidden from the list. The dashboard scrollbars now use colors from its light and dark themes. The existing 11 local records produced 3 usable, distinct entries without deleting the other records. An isolated API check verified repeat-upload reuse and complete cleanup after an explicit delete; 33 backend tests and the frontend build passed.

### Anomaly review clarity (September 2026)

The tracked 5,000-row retail sample is the first 5,000 rows of the original workbook, not a selection of anomalies. Its 1,205 missing CustomerID values (24.1%) reflect that source slice; the full 541,909-row local copy has 135,080 missing CustomerID values (24.93%). The anomaly review now explains its priority order and distinguishes queue positions from source row numbers. Row explanations and errors appear next to the lookup and scroll into view after a request. The local library currently shows Titanic, the retail sample, and the full retail workbook after the user removed the temporary proxy test dataset.

### Final score interpretation review (September 2026)

High-severity findings now appear beside the rule score and first in the findings list. Retail-only dimensions say why they were excluded from a generic dataset, with no zero-score bar. The anomaly methods panel explains which checks are statistical, which uses a model fitted to the selected dataset, and which suggestions come from fixed rules. The PDF uses the same score caveat and high-severity callout. The later scoring revision below also reduces completeness when missing values are concentrated in one column.

### Concentration-aware completeness (September 2026)

The completeness dimension starts with the percentage of filled cells, then deducts 60% of the gap between the worst column's missing rate and the dataset-wide average missing rate, capped at 15 completeness points. This treats a large blank portion of one field as a dataset quality concern without letting one optional field dominate the whole score. At this intermediate revision, the local weighted-average results were 91.55 for full Online Retail, 94.81 for the sample, and 87.40 for Titanic. The later conservative overall scoring revision below uses these as inputs. The counts and column evidence are unchanged. Numeric anomaly flags remain separate investigation leads, not score penalties. See [Documentation](docs/Documentation.md) for the exact formula and verification.

### Conservative overall scoring (September 2026)

The overall score now gives equal influence to the weighted average of evaluated dimensions and the lowest evaluated dimension. This is a transparent, risk-conscious rule that works whether the weakest area is completeness, uniqueness, retail validity, or retail consistency. The local results are full Online Retail **87.56** (`Good`), 5,000-row sample **89.57** (`Good`), and Titanic **82.15** (`Fair`). Quality and the PDF show the weighted average and limiting dimension. Individual findings are not deducted again, and statistical anomaly counts are not treated as errors. These scores express this project's policy rather than universal fitness for every business use.

---

## Project Goal

The completed project demonstrates practical skills in:

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
