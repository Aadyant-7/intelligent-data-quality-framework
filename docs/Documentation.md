# Project Documentation

## 1. Purpose

The Intelligent Data Quality Assessment & Anomaly Detection Framework is an enterprise-style platform for examining structured datasets before they are trusted for reporting, analytics, or machine-learning work.

The finished platform will allow a user to upload a dataset, automatically profile it, measure data quality, detect unusual observations, explain the findings, and present the results in a dashboard and report.

The project is built around real public data rather than fabricated examples. Its primary reference dataset is the UCI Online Retail dataset.

## 2. Current Status

**Completed through Phase 3 — Dataset Ingestion**

The system can currently:

- Run a FastAPI backend locally.
- Store dataset metadata in PostgreSQL.
- Accept CSV and Excel (`.xlsx`) uploads.
- Validate the uploaded file and reject unsupported or unreadable input.
- Convert Excel uploads into CSV for a consistent downstream format.
- Store normalized files locally with collision-resistant names.
- Extract row and column counts with Pandas.
- Create a linked PostgreSQL dataset record.

The next phase is **Data Profiling**, where the system will inspect the contents of an uploaded dataset instead of only recording its dimensions.

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

## 7. Technology Roles

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

## 8. Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Environment and backend foundation | Complete |
| 2 | Dataset research | Complete |
| 3 | Dataset ingestion | Complete |
| 4 | Data profiling engine | Next |
| 5 | Data quality engine | Planned |
| 6 | Anomaly detection | Planned |
| 7 | Explainability | Planned |
| 8–10 | Dashboard, visualizations, and reports | Planned |
| 11 | Deployment | Planned |
| 12 | Final documentation | Planned |

## 9. Next Step

Phase 4 will add automatic profiling for every normalized dataset: data types, missing values, duplicate rows, unique values, descriptive statistics, and column-level summaries.
