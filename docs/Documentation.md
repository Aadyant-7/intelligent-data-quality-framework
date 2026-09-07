# Project Documentation

## 1. Purpose

The Intelligent Data Quality Assessment & Anomaly Detection Framework is an enterprise-style platform for examining structured datasets before they are trusted for reporting, analytics, or machine-learning work.

The finished platform will allow a user to upload a dataset, automatically profile it, measure data quality, detect unusual observations, explain the findings, and present the results in a dashboard and report.

The project is built around real public data rather than fabricated examples. Its primary reference dataset is the UCI Online Retail dataset.

## 2. Current Status

**Completed through Phase 5 — Data Quality Engine**

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

The next phase is **Anomaly Detection**, where the system will identify unusual numeric observations without treating every unusual value as an error.

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
    Profiling and quality endpoints inspect the normalized CSV

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

The current implementation is deliberately a local development version. It reads the first worksheet of an Excel workbook, supports `.xlsx` rather than legacy `.xls`, processes files in memory, and stores normalized datasets on the local filesystem. File-size limits, multi-sheet selection, cloud object storage, and asynchronous processing are planned improvements rather than current requirements.

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

## 9. Technology Roles

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
| Git and GitHub | Version control and public project history |

---

## 10. Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Environment and backend foundation | Complete |
| 2 | Dataset research | Complete |
| 3 | Dataset ingestion | Complete |
| 4 | Data profiling engine | Complete |
| 5 | Data quality engine | Complete |
| 6 | Anomaly detection | Planned |
| 7 | Explainability | Planned |
| 8–10 | Dashboard, visualizations, and reports | Planned |
| 11 | Deployment | Planned |
| 12 | Final documentation | Planned |

## 11. Next Step

Phase 6 will add statistical and machine-learning-assisted anomaly detection, starting with numeric transaction fields while retaining the business context established in Phase 5.
