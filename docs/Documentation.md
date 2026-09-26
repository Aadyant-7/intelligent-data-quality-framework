# Project Documentation

## 1. Purpose

The Intelligent Data Quality Assessment & Anomaly Detection Framework is an enterprise-style platform for examining structured datasets before they are trusted for reporting, analytics, or machine-learning work.

Locally, a user can upload a dataset, profile it, measure data quality, investigate unusual observations, and download a report. The public website offers a read-only sample of that workflow.

The project is built around real public data rather than fabricated examples. Its primary reference dataset is the UCI Online Retail dataset.

## 2. Current Status

**All 12 planned phases complete**

The system can currently:

- Run a FastAPI backend locally.
- Store dataset metadata in PostgreSQL.
- Accept CSV and Excel (`.xlsx`) uploads.
- Validate the uploaded file and reject unsupported or unreadable input.
- Convert Excel uploads into CSV for a consistent downstream format.
- Store normalized files locally with collision-resistant names.
- Extract row and column counts with Pandas.
- Create a linked PostgreSQL dataset record.
- Generate a detailed structural profile of an uploaded dataset.
- Calculate explainable data-quality scores and evidence.
- Flag unusual numeric observations with statistical and Isolation Forest methods.
- Explain why a row was flagged and describe relevant retail business context.
- Browse these results in a local React dashboard, upload datasets, and inspect individual rows.
- Explore quality, missingness, anomaly signals, and field distributions with interactive charts.
- Download a PDF assessment of the current stored dataset.

The public, read-only sample is live at [Data Quality Studio](https://intelligent-data-quality-framework.vercel.app). The full upload workflow remains available locally. The final interface review removed misleading and repeated controls and added recovery for failed quality requests.

---

## 3. System Flow

The current ingestion flow is:

    User selects CSV or Excel file
              ↓
    FastAPI upload endpoint
              ↓
    Validate name, extension, and readability
              ↓
    Normalize Excel to CSV when required
              ↓
    Store normalized CSV locally
              ↓
    Pandas extracts basic metadata
              ↓
    PostgreSQL stores dataset record
              ↓
    Profiling, quality, and anomaly endpoints inspect the normalized CSV

This design is intentional: every later component can work with CSV data, even when the original upload was an Excel workbook.

---

## 4. Phase 1 — Environment and Backend Foundation

### Goal

Phase 1 established the backend infrastructure required before any data analysis could begin.

### Backend API

The project uses **FastAPI**, a Python framework for building HTTP APIs. It defines routes such as:

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/` | Basic backend response |
| `POST` | `/datasets` | Create dataset metadata manually |
| `GET` | `/datasets` | Retrieve saved dataset metadata |
| `POST` | `/datasets/upload` | Upload and ingest a dataset |

**Uvicorn** runs the FastAPI application locally. During development, it is started with:

    uvicorn app.main:app --reload

The `--reload` option restarts the server when Python code changes. FastAPI also generates API documentation automatically at `/docs` and `/redoc` from the route definitions and type annotations.

### Database

The project uses **PostgreSQL** for persistent storage. Unlike a Python variable, a database record remains after the server restarts.

The `datasets` table stores metadata about every ingested dataset:

| Field | Meaning |
|---|---|
| `id` | Unique database identifier |
| `file_name` | Original uploaded file name |
| `file_path` | Local normalized CSV storage path |
| `rows_count` | Number of rows |
| `columns_count` | Number of columns |
| `uploaded_at` | Upload timestamp |

### SQLAlchemy and ORM

**SQLAlchemy** connects Python to PostgreSQL. The `Dataset` Python model represents the `datasets` database table. This pattern is called an **ORM** (Object Relational Mapper): a Python object represents one database row, and its attributes represent table columns.

For example, creating a `Dataset` object and committing it through SQLAlchemy creates a persistent row in PostgreSQL without writing raw SQL for every operation.

### Validation and Sessions

**Pydantic** validates API data before it reaches the database. For example, the manual metadata endpoint requires a file name, storage path, row count, and column count in the expected types.

Database sessions are managed through FastAPI's `Depends(get_db)` mechanism. Each request receives a temporary SQLAlchemy session, and the session is closed after the request completes. This keeps database access consistent and prevents connections from being left open.

### Configuration and Security

The database URL is read from a local `backend/.env` file using `python-dotenv`. The file is excluded from Git, so credentials are not stored in source code or pushed to GitHub.

---

## 5. Phase 2 — Dataset Research

### Goal

Before writing automated quality rules, the project needed a real dataset with genuine data-quality challenges. The selected primary dataset is the **UCI Online Retail dataset**, a UK online retail transaction dataset.

### Dataset Shape

The original workbook contains:

- 541,909 transaction-line rows
- 8 columns
- 25,900 unique invoices
- 4,070 unique products
- 4,372 identified customers
- 38 countries

A row represents a transaction line item, not necessarily a full transaction. One invoice can contain multiple product rows.

### Columns

| Column | Purpose |
|---|---|
| `InvoiceNo` | Transaction or invoice identifier |
| `StockCode` | Product identifier |
| `Description` | Product description |
| `Quantity` | Number of items |
| `InvoiceDate` | Transaction timestamp |
| `UnitPrice` | Price per item |
| `CustomerID` | Customer identifier |
| `Country` | Customer country |

### Findings That Shape the Framework

Research with Pandas found several real issues and patterns:

| Finding | Relevance |
|---|---|
| 24.93% missing `CustomerID` values | Completeness |
| 5,268 duplicate rows | Uniqueness |
| 10,624 negative-quantity records | Context-aware validity and anomaly analysis |
| 2,515 zero-price records | Validity investigation |
| 650 `StockCode` values with multiple descriptions | Consistency |

The important design conclusion is:

> An anomaly is not automatically a data-quality error.

For example, negative quantities can represent legitimate cancellations when their invoice context indicates a credit transaction. The framework should flag and explain unusual data rather than automatically delete it.

### Reference Data Used in Development

The repository keeps the original Excel workbook as reference data and a 5,000-row CSV sample derived from it. The sample is used for quick API testing; it is not a replacement for the full 541,909-row source dataset.

---

## 6. Phase 3 — Dataset Ingestion

### Goal

Phase 3 made the application capable of receiving a real user dataset rather than accepting manually typed metadata.

### Supported Input Formats

The current upload endpoint supports:

- `.csv`
- `.xlsx`

Older `.xls` workbooks are not yet supported. Support can be added later if needed.

### Why Normalize to CSV

CSV is the platform's current canonical processing format. It is simple, portable, and can be read efficiently by Pandas.

When a user uploads CSV, the file is stored directly as the normalized dataset. When a user uploads Excel, Pandas reads the workbook and writes a normalized CSV copy. The later profiling, quality, and anomaly engines can therefore process one predictable format instead of maintaining separate CSV and Excel logic.

The original upload name remains visible in the database record, while `file_path` refers to the normalized CSV used by the application.

### File Validation

The ingestion service checks:

| Check | Result on failure |
|---|---|
| Missing file name | HTTP 400 |
| Unsupported extension | HTTP 400 |
| Empty file | HTTP 400 |
| CSV/Excel parser or encoding error | HTTP 400 |

For example, an unsupported upload returns a message explaining that only CSV and Excel (`.xlsx`) files are accepted.

### Storage Strategy

Files are stored locally in the backend upload directory. The application prefixes each stored file with a UUID, a randomly generated identifier, to avoid collisions:

    online_retail_sample.csv
              ↓
    550e8400e29b41d4a716446655440000_online_retail_sample.csv

This prevents one upload from overwriting another when both files have the same visible name.

The upload directory is excluded from Git because uploaded datasets are runtime data, not source code. The folder itself is retained in the repository with a placeholder file so a fresh project clone still has the expected storage location.

### Metadata Extraction

After a file has been successfully read, Pandas extracts:

- Number of rows
- Number of columns

The ingestion service creates a PostgreSQL `Dataset` record containing the original file name, normalized storage path, dimensions, and timestamp.

If the database write fails after local storage, the service rolls back the database transaction and removes the newly created file. This avoids leaving orphaned upload files without a matching database record.

### Code Organization

The upload route is intentionally small. It receives the HTTP upload and calls the reusable ingestion service. The service contains validation, file handling, normalization, metadata extraction, and database persistence.

Keeping this logic outside the API route makes it easier to reuse during later profiling and analysis work.

### Verification

The original CSV-only flow was tested with the 5,000-row Online Retail sample:

- Valid CSV upload returned HTTP `200`.
- The file was stored with a unique name.
- A PostgreSQL metadata record was created with 5,000 rows and 8 columns.
- An Excel upload was previously rejected with HTTP `400` under the CSV-only policy.

The Excel-normalization flow was verified with the full 541,909-row, 8-column UCI Online Retail workbook:

- Excel upload returned HTTP `200`.
- The workbook was converted to a 48.6 MB normalized CSV.
- The raw temporary Excel upload was removed after conversion.
- PostgreSQL recorded the original file name and normalized CSV path.

### Current Scope Limitations

The full upload workflow runs locally; the hosted demo is read-only. In local mode the app reads the first worksheet of an Excel workbook, supports `.xlsx` rather than legacy `.xls`, processes files in memory, and stores normalized datasets on the local filesystem. File-size limits, multi-sheet selection, cloud object storage, and asynchronous processing are possible future improvements, not implemented features.

---

## 7. Phase 4 — Data Profiling Engine

### Goal

Phase 4 adds automated inspection of a stored normalized CSV. Instead of manually running Pandas commands to understand a dataset, a client can request a profile through:

    GET /datasets/{dataset_id}/profile

The endpoint loads the dataset linked to the PostgreSQL record and returns JSON that can later feed the dashboard, quality engine, and report generator.

### Profile Contents

The profiler returns dataset-level information:

- Row and column counts
- Duplicate-row count
- Total missing-value count
- Number of columns containing missing values

For every column, it returns:

- Raw Pandas data type
- Logical type
- Missing count and percentage
- Unique-value count
- Sample values
- Numeric summary statistics when applicable
- Date range for date columns
- Most common values for categorical columns

### Logical Type Inference

CSV files do not preserve all source semantics. For example, `InvoiceDate` becomes text after CSV storage, and `CustomerID` may appear as a numeric value despite functioning as an identifier.

The profiler uses lightweight, non-destructive rules to classify columns as:

- `identifier` for names containing markers such as `ID`, `Code`, or `No`
- `datetime` for date-like values
- `numeric` for measurable numeric columns
- `categorical` for low-cardinality values
- `text` for other string content

This prevents misleading metrics. `CustomerID`, for example, is labeled as an identifier and does not receive a meaningless average or standard deviation.

### Verification

Profiling the full Online Retail dataset produced:

- 541,909 rows and 8 columns
- 5,268 duplicate rows
- 136,534 total missing values across 2 columns
- `CustomerID` missing rate of 24.93%
- Transaction date range from December 2010 to December 2011
- United Kingdom as the most frequent country with 495,478 records

The endpoint also returns HTTP `404` with a clear message when the requested dataset record does not exist.

---

## 8. Phase 5 — Data Quality Engine

### Goal

Phase 5 turns the raw evidence from profiling into a concise, explainable assessment:

    GET /datasets/{dataset_id}/quality

The response provides an overall score, a grade, four dimension scores, and a list of the exact issues that influenced the result. It does not modify or delete uploaded data.

### Quality Dimensions and Weights

| Dimension | Weight | What is measured |
|---|---:|---|
| Completeness | 30% | The proportion of populated cells, plus missing-value evidence by column |
| Uniqueness | 25% | The proportion of rows that are not duplicates |
| Validity | 25% | Values that violate available business-aware rules |
| Consistency | 20% | Whether related fields agree with each other |

The weighted score maps to a simple grade: `Excellent` (95 or above), `Good` (85–94.99), `Fair` (70–84.99), or `Needs attention` (below 70).

### Context-Aware Retail Rules

Generic checks such as completeness and duplicate detection work for every uploaded CSV. Some checks only make sense when the required Online Retail columns are present; otherwise the response marks that dimension as `not_evaluated` rather than inventing a perfect score.

For the retail dataset, validity checks identify negative quantities without cancellation-style invoice numbers and negative unit prices. Zero-priced rows are reported for review but are not automatically treated as invalid, because a free item may be legitimate. Consistency checks identify `StockCode` values linked to more than one product description.

This preserves the project principle that unusual data is evidence to investigate, not a reason to delete a record automatically.

### Explainable Results

Each issue contains its quality dimension, severity, affected-record count, relevant column when available, and a plain-language message. This gives a later dashboard or report enough information to explain a score rather than display an unexplained number.

### Verification

The endpoint was tested against the normalized full Online Retail dataset (dataset ID 8):

| Result | Value |
|---|---:|
| Overall score | 95.47 / 100 (`Excellent`) |
| Completeness | 96.85 |
| Uniqueness | 99.03 |
| Validity | 99.75 |
| Consistency | 83.58 |
| Missing values | 136,534 |
| Duplicate rows | 5,268 |
| Invalid rows under the implemented rules | 1,338 |
| Inconsistent `StockCode` values | 650 |

An unknown dataset ID was also verified to return HTTP `404`.

### Service Organization

Application logic now lives under `backend/app/services/`: ingestion handles file input, profiling describes a dataset, the quality engine scores it, and the storage helper safely resolves persisted upload paths. This separation keeps the FastAPI route file focused on HTTP requests and makes each capability reusable.

---

## 9. Phase 6 — Anomaly Detection Engine

### Goal and API

Phase 6 adds `GET /datasets/{dataset_id}/anomalies`. It reads the dataset's stored CSV through the shared safe-path resolver and returns unusual numeric rows for review. It does not edit the uploaded data or turn anomaly findings into quality-score penalties. A missing dataset record or stored file returns HTTP 404.

### How Detection Works

The service considers numeric columns but excludes likely identifiers such as `CustomerID`. For each usable numeric field, it applies:

| Method | Rule | Why it is useful |
|---|---|---|
| IQR | Outside the first/third quartile by more than 1.5 times the interquartile range | Finds values far from the middle half of a column |
| Z-score | More than 3 population standard deviations from the mean | Finds values far from the average |
| Isolation Forest | A reproducible model trained on up to 10,000 complete rows, using 1% contamination | Finds unusual combinations across at least two numeric fields |

IQR and Z-score need at least four finite values and two distinct values. IQR skips a field with zero interquartile range; Z-score skips zero or non-finite standard deviation. Isolation Forest needs at least two varying numeric fields and 20 complete rows. A method that cannot run returns `not_evaluated` with a reason. Missing and infinite numeric values are not used as anomaly evidence.

The response includes each method's evaluation status, inspected fields, flagged counts, and statistical bounds where applicable. `anomaly_rows_count` is the number of distinct rows flagged by at least one method, so overlapping method counts must not be added together. The first 20 example rows are returned by default; Phase 7 added pagination for the rest. Examples with more signals appear first.

When `InvoiceNo` and `Quantity` exist, the response also counts flagged negative quantities with and without a cancellation-style invoice number. Example rows include a short business-context message for negative quantities. A cancellation-style negative quantity may be a legitimate return; neither this endpoint nor its model proves a data-quality error.

### Verification

The Phase 6 endpoint was exercised against a fresh 5,000-row sample upload (dataset ID 9 in this local database) and the existing full 541,909-row Online Retail upload (local ID 8). On the full upload it returned 97,801 distinct flagged rows, including 2,686 flagged negative-quantity rows with cancellation-style invoices. The IQR checks flagged 58,619 rows for `Quantity` and 39,627 for `UnitPrice`; the Z-score checks flagged 346 and 374 respectively; Isolation Forest flagged 5,520. These counts overlap and are method-specific. The large IQR count reflects the skewed retail data and should be read as a review queue, not an error rate.

An unknown dataset ID returned HTTP 404. Four automated service tests passed for cancellation context, an arbitrary single-numeric-field dataset, a nonnumeric dataset, missing files, and path traversal. Backend compilation passed.

### Current Limits

Detection currently covers numeric fields only. Identifier recognition uses column-name tokens; unusual naming may need user-configurable field roles later. Isolation Forest is fitted on a bounded sample but scores all complete rows, so analysis still reads the whole CSV into memory. Results are calculated on request and are not stored in PostgreSQL. The 1% model contamination and statistical thresholds are initial, documented defaults rather than universal definitions of "bad" data.

---

## 10. Phase 7 — Explainability and Regression Review

### Why This Phase Exists

An anomaly count alone cannot tell a user whether a row is wrong. Phase 7 adds evidence that can be inspected row by row and a cautious interpretation drawn from the retail rules already used in quality scoring. The data and quality score remain separate from the anomaly findings.

### API and Response

`GET /datasets/{dataset_id}/anomalies?offset=0&limit=20` returns a page of flagged rows in the existing priority order. `offset` starts at zero and `limit` can be 1–100. The response includes `next_offset` when another page exists. This makes every flagged row reachable, beyond the first 20 examples.

`GET /datasets/{dataset_id}/anomalies/{row_number}/explanation` explains one row by its **one-based data-row number** (the header is not counted). It works for flagged and unflagged rows. Unknown dataset IDs and out-of-range row numbers return HTTP 404.

Each returned row has:

- `signals`: which methods flagged it.
- `method_evidence`: the observed value, direction, and boundary for IQR or Z-score; for Isolation Forest, the model score and zero decision boundary. A negative model score means the model flagged the row. The model does not identify the field that caused the result.
- `interpretation`: a category, plain-language reason, and suggested next check.
- `status`: `flagged`, `not_flagged`, or `not_evaluated`. An unflagged row is not certified correct.

Retail interpretation uses explicit transaction rules rather than the model's anomaly label. Negative prices and negative quantities without a cancellation marker are possible quality issues; a cancellation-style negative quantity is a possible legitimate return; zero price needs business review. A flagged row without a matching business rule says `needs_review`. These are investigation hints, not final judgments.

### Earlier-Phase Corrections

The Phase 7 review found and fixed three gaps in previous phases:

- Header-only CSV and `.xlsx` files could pass ingestion despite containing no data rows. They now return HTTP 400, and temporary upload files are removed.
- The profiler's old substring check could mistake a numeric field such as `Snowfall` for an identifier because its name contains `no`. Profiling and anomaly detection now share token-based identifier recognition.
- Quality scoring could award 100 for consistency when there were no stock-code/description pairs to compare, and malformed retail numbers could raise an exception. Empty comparisons now return `not_evaluated`; nonnumeric and non-finite retail values produce counted validity evidence. An empty stored dataset is not scored.

### Verification and Limits

The real 5,000-row upload returned 877 distinct flagged rows. A two-row page returned `next_offset: 2`; a flagged sample row supplied three method explanations, while row 1 correctly returned `not_flagged`. The full dataset still profiled as 541,909 rows with 5,268 duplicates, and its quality score remained 95.47. Invalid dataset and row IDs returned 404. A header-only CSV upload returned 400. Fourteen automated tests and backend compilation passed.

Explanations are based on current thresholds and the available retail fields. They cannot prove cause or replace source-system checks. Row explanations recompute the dataset analysis on request; caching and stored results remain future improvements.

---

## 11. Phase 8 — React Dashboard

### What Was Added

The `frontend/` application uses React and Vite to present the existing API in one workspace. Users can upload a `.csv` or `.xlsx` file, search and select a stored dataset, and move between four views:

| View | What it shows |
|---|---|
| Overview | Dataset size, available quality scores, and leading findings |
| Profile | Missing values, duplicates, field types, examples, and column details |
| Quality | Overall and dimension scores, plus issue severity, counts, and explanations |
| Anomalies | Method status, paginated flagged rows, and evidence for any chosen data-row number |

The interface shows loading, empty, and error states. Failed profile, quality, and anomaly requests can be retried. A missing local upload file is surfaced as an error rather than displayed as a clean dataset. Smaller screens keep dataset selection available through a horizontally scrollable list.

### Architecture and Local Use

`frontend/src/App.jsx` owns selection, tab state, data loading, and the views. `frontend/src/api.js` contains the HTTP calls and error handling; `frontend/src/format.js` contains display formatting; `frontend/src/styles.css` contains layout and responsive rules. Profile and anomaly pages are fetched when opened and cached for the current session. A dataset switch cancels in-flight requests and starts a fresh quality request.

Run the backend on `127.0.0.1:8000`, then run `npm ci` and `npm run dev` from `frontend/`. Open `http://127.0.0.1:5173`. The Vite development proxy forwards `/api` to the backend, so no separate browser CORS configuration is needed for this local setup. `npm run build` creates the production frontend bundle. The separate hosted sample uses the Vercel and Render configuration described in Phase 11.

### Verification and Limits

The production build passed and npm's audit found no known vulnerabilities in the locked dependencies. The browser was checked with the real 5,000-row upload: overview, column details, quality findings, anomaly paging, a flagged row's evidence, an unflagged row, dataset search, and switching to the full 541,909-row upload. A missing stored file produced a visible error. A four-row CSV uploaded through the development proxy and appeared as dataset ID 10 in the local workspace; its profile, quality, and anomaly endpoints responded. An unknown dataset ID returned HTTP 404 through the proxy. At phone width, the dataset selector and main content stayed within the viewport. Stopping the backend showed a clear connection error; restarting it and using Retry restored the dashboard.

This phase also corrected a backend explanation label from `Z_SCORE` to `Z-score`; backend compilation and all 14 regression tests passed, and the live row explanation showed the corrected wording.

The dashboard is available locally with uploads and online as a read-only sample. Authentication and persistent hosted upload storage remain future work. Analysis remains calculated on request by the backend. Dataset IDs above refer only to the local development database.

---

## 12. Phase 9 — Interactive Visualizations

### Chart Data and Meaning

The new `GET /datasets/{dataset_id}/visualizations?column=...` endpoint reads one requested column from the normalized CSV through the shared storage-path resolver. It returns compact counts rather than individual rows:

| Field type | Chart data |
|---|---|
| Numeric | 24-bin histograms for the full finite range and a typical range between the 1st and 99th percentiles |
| Categorical | 12 leading values and a counted `Other categories` group |
| Datetime | Counts by month, or by year for spans longer than three years |
| Identifier or free text | `not_evaluated` with a reason |

Missing values and infinite numbers are counted separately from finite numeric values. The typical-range view states how many finite rows lie outside it; those rows remain in the full-range chart. Histogram bins sum to the stated included-row count. An unknown dataset or column, or a missing stored file, returns HTTP 404.

### Dashboard

The **Visualizations** tab uses Plotly.js to show evaluated quality scores, fields with missing values, leading anomaly signals, and a selectable field distribution. Users can hover for values, zoom and reset charts, switch numeric ranges, and open count tables beneath the charts. Plotly's basic bundle is loaded only when a chart is opened. The profile, quality, and anomaly summaries remain the source data for the first three charts; the new endpoint supplies the selected field's distribution.

Quality dimensions without a score are omitted from the score chart and described as unevaluated. Anomaly method/field counts can overlap, so the chart explicitly separates them from the distinct flagged-row total. The charts never label an unusual observation as a proven data-quality error.

### Verification and Limits

Backend compilation and all 20 automated tests passed, including checks for histogram count conservation, categories grouped into `Other`, date buckets, identifier exclusion, missing files, and extremely large finite numbers. On the real 5,000-row retail sample, the Quantity full histogram counted 5,000 rows; its typical-range chart counted 4,906 and reported 94 outside. On the full 541,909-row upload, month buckets and full Quantity bins each summed to 541,909; the typical range counted 531,914 and reported 9,995 outside. A generic four-row dataset also rendered. Unknown IDs and columns returned 404. Browser checks covered numeric, category, and date selection, range switching, chart layout, dataset switching, and phone width.

The endpoint reads one entire column into memory per request, then sends bounded chart data. It is not a streaming or asynchronous analysis service. Chart zoom changes the display; it does not recalculate quality or anomaly rules. The Plotly chart bundle is a separate download of about 381 kB compressed.

---

## 13. Phase 10 — Report Generation

### What the PDF Contains

`GET /datasets/{dataset_id}/report` returns an A4 PDF with an attachment filename. The dataset overview has a **Download PDF report** button, with a preparing state and an error message if generation fails. The backend uses ReportLab to format the current profile, quality assessment, and anomaly results in memory. It does not store the PDF or computed results in the database.

The report gives the overall score and grade, each dimension's weight and score or `Not evaluated` status, severity and affected counts for quality findings, column-level missing and unique counts, distinct flagged-row count, anomaly method counts, and five explained examples. Retail cancellation context appears only when the source columns support it. It states that method counts may overlap and that anomaly flags require investigation. If a dataset lacks retail fields, validity and consistency remain unevaluated and their weights are excluded from the overall score.

Reports show at most 40 columns, 50 findings, and 30 anomaly method/field rows; any omitted rows are counted in a visible note and remain available through the existing API. The report does not include every raw record. Reports are generated synchronously and recompute analyses from the stored CSV, so a large upload can take several seconds. The source file is never changed.

### Verification and Limits

Backend compilation and all 23 automated tests passed. Tests cover PDF generation, unevaluated retail checks for a generic CSV, a header-only legacy file, missing stored files, and traversal-path rejection. Live PDF responses were checked for a four-row generic CSV, a 5,000-row retail sample, and the 541,909-row retail upload. The full upload generated a PDF in about eight seconds. Unknown dataset IDs and missing stored files returned HTTP 404. Generated pages were rendered and visually inspected, and the browser button made a successful request to the report endpoint. The frontend production build passed; Vite still warns that the separate Plotly bundle is large.

The PDF is a point-in-time assessment of local data, not a certification. Generic validity or consistency rules beyond the current retail checks are future work. The report is not yet a scheduled export, persisted snapshot, or asynchronous job.

---

## 14. Phase 11 — Deployment

### Hosted Mode

The user chose a free public demo rather than paid persistent upload storage. [Vercel](https://intelligent-data-quality-framework.vercel.app) hosts the Vite frontend, [Render](https://intelligent-data-quality-api.onrender.com) runs FastAPI on a Free web service, and Neon Free PostgreSQL stores metadata. `render.yaml` defines the backend build, startup command, Python version, and lightweight `/health` check. The Vercel project uses `frontend/` as its root directory; `frontend/vercel.json` provides a single-page fallback. A GitHub Actions workflow compiles and tests the backend and builds the demo frontend. Its deployment-preparation run passed.

With `DEMO_MODE=true`, the backend copies the tracked public 5,000-row retail sample to its runtime upload folder at startup and creates or reuses one metadata record. This restores the sample after an ephemeral restart. The API lists only that record, hides other dataset IDs, and rejects upload and manual metadata creation. The frontend uses `VITE_DEMO_MODE=true` to label the public sample and hide its upload form. The full upload workflow remains available when running locally without demo mode. The hosted demo does not retain user uploads because Render Free storage is temporary.

`DATABASE_URL` stays in the backend provider's private environment. `CORS_ORIGINS` must contain the exact Vercel origin; a different origin is rejected. Vercel receives `VITE_API_BASE_URL` with the public Render API URL. Vite embeds that public URL at build time, so changing it requires a rebuild. No database credentials belong in a Vite variable, source file, or GitHub commit. `/health` checks the demo file without querying PostgreSQL; repeated Render health probes therefore do not keep an idle Neon database awake. `/ready` checks PostgreSQL on demand. Backend startup creates the existing table schema and fails if the database is unavailable. This remains a small project without managed migrations.

### Local Verification

Backend compilation and all 26 automated tests passed. An isolated SQLite-backed demo server started with the public sample and returned one 5,000-row dataset, quality score 98.61, 877 flagged rows, and a PDF response. Unknown IDs returned 404; upload and valid metadata creation returned 403. The demo write guard runs before multipart parsing, so blocked uploads do not consume file-processing resources. A configured browser origin passed CORS preflight, while an unlisted origin was rejected. The regular local mode still listed its existing datasets and returned the sample quality and report, with 404 for an unknown ID. A Vite demo build passed; the existing Plotly bundle-size warning remains.

### Live Verification

On 2026-09-26, the deployed API returned 200 from `/health` and `ready` from `/ready`. `/datasets` exposed only the public 5,000-row sample. The sample returned a 98.61 quality score, 877 distinct flagged rows, a Quantity visualization, a profile, and a 200 PDF response (`application/pdf`). The live dashboard loaded the sample, quality evidence, profile, charts, anomaly paging, and a row explanation without browser console errors. An unknown dataset ID returned 404; both write routes returned 403. CORS preflight accepted `https://intelligent-data-quality-framework.vercel.app` and rejected an unlisted origin.

The first Render startup failed because a copied connection string had a space inside its hostname. The private Render setting was corrected and the next deployment started successfully. No connection string was added to Git. Render was created from the public repository URL, so automatic redeploys from later Git pushes are unavailable until a Git provider connection is added; a manual Blueprint sync or deploy is needed for backend changes. Vercel is connected to the GitHub repository and deploys its `frontend/` root.

The free backend can sleep when idle and can take about a minute to wake. Its filesystem is temporary; the public sample is restored at startup, and uploads are disabled. This is a portfolio demo, not a persistent multi-user service. Provider limits can change; see [Render Free](https://render.com/docs/free), [Vercel Vite](https://vercel.com/docs/frameworks/frontend/vite), and [Neon](https://neon.com/docs).

---

## 15. Technology Roles

| Technology | Role in the project |
|---|---|
| Python | Backend and data-processing language |
| FastAPI | HTTP API framework |
| Uvicorn | Local ASGI server |
| PostgreSQL | Persistent metadata and future analysis storage |
| SQLAlchemy | Python-to-database ORM layer |
| Pydantic | API input validation |
| Pandas | Reading, converting, and profiling datasets |
| OpenPyXL | Excel `.xlsx` support for Pandas |
| NumPy and scikit-learn | Numeric anomaly calculations and Isolation Forest |
| React and Vite | Local dashboard and hosted frontend build |
| Plotly.js | Interactive charts in the dashboard |
| ReportLab | PDF assessment layout and export |
| Git and GitHub | Version control and public project history |

---

## 16. Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Environment and backend foundation | Complete |
| 2 | Dataset research | Complete |
| 3 | Dataset ingestion | Complete |
| 4 | Data profiling engine | Complete |
| 5 | Data quality engine | Complete |
| 6 | Anomaly detection | Complete |
| 7 | Explainability | Complete |
| 8 | React dashboard | Complete |
| 9 | Interactive visualizations | Complete |
| 10 | Report generation | Complete |
| 11 | Deployment | Complete: free, read-only sample live |
| 12 | Final documentation and polish | Complete |

## 17. Phase 12 — Final Documentation and Polish

### Interface Review

The previous sidebar showed a chevron beside the workspace name without offering a menu. That decoration was removed. Search now appears only when there is more than one dataset, which keeps the single-sample demo simpler. The overview no longer repeats the Profile and Anomalies tabs as large action cards, and the page header is shorter. Plotly's Share button had no configured destination; it and extra chart toolbar buttons were removed, leaving PNG download, zoom, and reset. A failed quality request can be retried from the overview or quality chart. Quality retries no longer clear loaded profile or anomaly results. An empty hosted dataset list now explains that the free API may be waking up instead of suggesting an upload that the demo does not allow. Keyboard focus is visible on chart field selectors. The dataset header stacks on narrow phone screens.

### Verification

Backend compilation passed and all 26 automated tests passed. The frontend production build passed. The build still warns about the separately loaded Plotly bundle, around 381 kB compressed. The live sample's tabs, row review, chart controls, report download, and responsive layout were checked in the browser after the frontend update. These checks verify the public sample and core interactions; they do not certify every possible CSV or Excel file.

### Remaining Limits

The free Render service sleeps after inactivity, so the first request may be slow. It has temporary storage, and public uploads remain disabled. The local upload path processes files synchronously and has no dedicated large-file limit or cloud object storage. Retail-specific validity and consistency checks only run when their columns exist; the generic checks do not cover every possible domain rule. The database stores metadata, while profiles, scores, charts, anomaly results, and PDFs are recomputed on request. Hosted backend changes require manual Render deployment until its Git provider integration is connected.

## 18. Status

The planned project is complete as a portfolio demonstration. Further work can focus on newly found bugs, broader dataset trials, accessibility checks, and features chosen after using the finished workflow.
