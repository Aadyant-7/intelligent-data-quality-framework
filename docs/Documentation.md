# Intelligent Data Quality Assessment & Anomaly Detection Framework

## 1. Project Overview

The Intelligent Data Quality Assessment & Anomaly Detection Framework is an enterprise-style data analytics platform designed to automatically evaluate the quality of structured datasets, identify potential data-quality problems, detect statistical and machine-learning-based anomalies, and present the findings through an explainable interactive dashboard.

The system is designed around a real-world data workflow rather than a simple data visualization application.

The intended workflow is:

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

The framework will initially work with CSV datasets and will be tested using real-world public datasets.

---

## 2. Why This Project Is Being Built

Modern organizations rely heavily on data for reporting, analytics, machine learning, and business decisions.

However, raw datasets frequently contain problems such as:

- Missing values
- Duplicate records
- Invalid values
- Inconsistent representations
- Incorrect or unexpected data types
- Extreme values
- Statistical outliers
- Broken relationships between fields

These problems can negatively affect downstream analytics and machine learning systems.

Data quality is therefore not only a cleaning problem. A useful system should be able to:

1. Discover problems automatically.
2. Quantify their severity.
3. Distinguish genuine errors from unusual but potentially valid observations.
4. Explain why a record or field was flagged.
5. Present the results in a form that is understandable to analysts and decision-makers.

This project is being built to demonstrate that complete workflow.

---

## 3. Project Objectives

The major objectives are:

- Build a backend capable of accepting and managing datasets.
- Automatically profile uploaded datasets.
- Detect missing and duplicate data.
- Evaluate multiple dimensions of data quality.
- Calculate an overall data-quality score.
- Detect statistical anomalies.
- Apply machine-learning-based anomaly detection.
- Provide explainable reasons for detected issues.
- Present findings through an interactive dashboard.
- Generate a useful data-quality report.
- Deploy the completed application using free or low-cost infrastructure.
- Build the project using real-world datasets rather than fabricated examples.

---

## 4. Core Data Quality Dimensions

The initial framework will evaluate the following dimensions.

### 4.1 Completeness

Measures whether required data is present.

Examples:

- Missing `CustomerID`
- Missing `Description`

A completeness score can be derived from the proportion of populated values.

---

### 4.2 Uniqueness

Identifies duplicated records or values that are expected to be unique.

Example:

- Duplicate transaction rows

---

### 4.3 Validity

Checks whether values satisfy defined structural or business rules.

Examples:

- Invalid data types
- Invalid ranges
- Unexpected values
- Invalid prices

---

### 4.4 Consistency

Checks whether related fields agree with each other.

Example:

- A product code appearing with multiple descriptions

Consistency rules may depend on the dataset and its business context.

---

### 4.5 Anomaly Detection

Identifies observations that are unusually different from the rest of the dataset.

Planned techniques include:

- Z-score
- Interquartile Range (IQR)
- Isolation Forest

An anomaly will not automatically be considered an error.

---

### 4.6 Context-Aware / Business Rules

The framework will attempt to interpret unusual values in context.

For example, a negative quantity in a transaction dataset may represent a legitimate cancellation or return rather than invalid data.

Therefore:

    Unusual Value ≠ Automatically Invalid Value

The system should provide context when flagging such observations.

---

# 5. Overall System Architecture

The planned architecture is:

    User
      │
      ▼
    React Frontend
      │
      │ HTTP / REST API
      ▼
    FastAPI Backend
      │
      ├───────────────┐
      ▼               ▼
    Data Engine    PostgreSQL
      │
      ├── Data Profiling
      ├── Quality Engine
      ├── Anomaly Detection
      └── Explainability
      │
      ▼
    Analysis Results
      │
      ▼
    Dashboard / Report

The frontend will be responsible primarily for interaction and visualization.

The backend will handle application logic, dataset processing, analysis, and database communication.

---

# 6. Complete Project Roadmap

## Phase 0 — Planning

- Define the problem
- Define objectives
- Define system architecture
- Define major features
- Select the initial dataset strategy

Status: Complete

---

## Phase 1 — Environment & Backend Foundation

- Python environment
- Virtual environment
- FastAPI
- Uvicorn
- PostgreSQL
- SQLAlchemy
- Database connection
- ORM model
- Database sessions
- Pydantic request validation
- Dataset metadata APIs
- Environment variables
- Git/GitHub setup

Status: Complete

---

## Phase 2 — Dataset Research

- Select a real-world dataset
- Inspect dataset structure
- Understand columns and data types
- Measure missing values
- Measure duplicates
- Inspect cardinality
- Investigate unusual values
- Investigate business-specific patterns
- Identify consistency issues
- Define initial quality dimensions

Status: Complete

Primary dataset:

**UCI Online Retail Dataset**

---

## Phase 3 — Dataset Ingestion

Status: Complete

### 6.1 Objective

Phase 3 turns the backend from a metadata-only API into a real dataset-ingestion service. A user can now upload a CSV, and the application validates it, stores it safely, measures its dimensions, and creates a linked PostgreSQL record.

### 6.2 Ingestion Flow

    CSV upload
          ↓
    Validate file name and .csv extension
          ↓
    Store a uniquely named copy in backend/uploads/
          ↓
    Read the CSV with Pandas
          ↓
    Extract row and column counts
          ↓
    Save dataset metadata in PostgreSQL

### 6.3 API Endpoint

    POST /datasets/upload

The endpoint accepts a multipart file upload. The supported format is currently CSV only, which keeps the ingestion format consistent while the profiling engine is being built.

### 6.4 Validation and Storage

The service rejects missing file names, non-CSV extensions, unreadable CSV files, empty files, malformed CSV content, and invalid text encodings with a useful HTTP 400 response.

Uploaded files receive a UUID prefix before storage. This avoids accidental overwrites when different users upload files with the same original name.

The `backend/uploads/` folder is ignored by Git. The project retains the folder through `.gitkeep`, but never commits user-uploaded files.

### 6.5 Metadata Extraction

Pandas reads the validated CSV and automatically calculates:

- Row count
- Column count

The original file name, generated storage path, dimensions, and upload timestamp are saved through the existing `Dataset` SQLAlchemy model.

### 6.6 Reusable Service Design

File operations and database persistence were moved into:

    backend/app/services/dataset_ingestion.py

This keeps `main.py` focused on HTTP routes while allowing the ingestion logic to be reused later by profiling and analysis workflows.

### 6.7 Verification

The endpoint was tested with a 5,000-row, 8-column CSV sample derived from the UCI Online Retail dataset.

- Valid CSV upload: HTTP 200
- Metadata record created in PostgreSQL
- Invalid Excel upload: HTTP 400 with `Only CSV files are supported.`

### 6.8 Cleanup

The temporary `test_db.py` script was removed. It was only needed during the initial database connection experiment and has been replaced by the actual API-based ingestion workflow.

---

## Phase 4 — Data Profiling Engine

Planned capabilities:

- Row and column counts
- Data types
- Missing values
- Duplicate records
- Unique values
- Cardinality
- Descriptive statistics
- Basic distributions
- Column-level summaries

Status: Planned

---

## Phase 5 — Data Quality Engine

Planned capabilities:

- Completeness score
- Uniqueness score
- Validity score
- Consistency score
- Overall quality score
- Issue classification
- Severity levels
- Recommendations

Status: Planned

---

## Phase 6 — Anomaly Detection Engine

Planned methods:

- Z-score
- IQR
- Isolation Forest

The system will compare statistical and machine-learning approaches where appropriate.

Status: Planned

---

## Phase 7 — Explainability

The system will explain detected problems in human-readable language.

Example:

    CustomerID contains 24.93% missing values.

    This reduces the completeness of the CustomerID field.

Or:

    Quantity = 80,995 was detected as an extreme statistical outlier.

Status: Planned

---

## Phase 8 — React Dashboard

Planned dashboard sections:

- Dataset overview
- Quality score
- Data-quality issues
- Missing-value analysis
- Duplicate analysis
- Anomaly analysis
- Dataset statistics
- Recommendations

Status: Planned

---

## Phase 9 — Interactive Visualizations

Planned visualizations:

- Missing-value charts
- Distributions
- Outlier visualizations
- Quality-score breakdowns
- Country/category distributions
- Interactive dataset summaries

Plotly is currently planned for visualization.

Status: Planned

---

## Phase 10 — Report Generation

The application will eventually generate a downloadable data-quality report containing:

- Dataset summary
- Quality scores
- Detected issues
- Anomalies
- Explanations
- Recommendations

Status: Planned

---

## Phase 11 — Deployment

The final application will be deployed as a complete system.

Planned architecture:

    React Frontend
          ↓
    Hosted FastAPI Backend
          ↓
    Hosted PostgreSQL Database

Free-tier services will be preferred.

Potential services include:

- Vercel
- Render
- Neon PostgreSQL

The final deployment choice will depend on availability and suitability when deployment begins.

Status: Planned

---

## Phase 12 — Documentation & Interview Preparation

Final documentation will cover:

- Complete architecture
- Technologies used
- Algorithms
- Design decisions
- Problems encountered
- Solutions
- Testing
- Results
- Limitations
- Future improvements

Interview preparation will cover:

- Project explanation
- Technology-specific questions
- Architecture questions
- Algorithm questions
- Design decisions
- Challenges and solutions
- Resume explanation

Status: Planned

---

# 7. Technology Stack

## Backend

- Python
- FastAPI
- Uvicorn

## Data Processing

- Pandas
- NumPy

## Database

- PostgreSQL
- SQLAlchemy

## Machine Learning / Statistics

- Scikit-learn
- Z-score
- IQR
- Isolation Forest

## Frontend

- React

## Visualization

- Plotly

## Version Control

- Git
- GitHub

## Deployment

Free-tier hosting will be preferred.

Potential services:

- Vercel
- Render
- Neon PostgreSQL

---

# 8. Current Project Structure

    intelligent-data-quality-framework/
    │
    ├── backend/
    │   ├── app/
    │   │   ├── __init__.py
    │   │   ├── main.py
    │   │   ├── database.py
    │   │   ├── models.py
    │   │   └── test_db.py
    │   │
    │   ├── venv/
    │   ├── .env
    │   └── requirements.txt
    │
    ├── datasets/
    │   └── Online Retail.xlsx
    │
    ├── docs/
    │   └── Documentation.md
    │
    ├── frontend/
    │
    ├── .gitignore
    └── README.md

The `.env` file contains local database credentials and must never be committed to GitHub.

The `venv` directory is a local Python environment and is excluded from Git.

---

# 9. Local Development Setup

## Backend

Open a terminal in the `backend` directory.

Activate the virtual environment:

    .\venv\Scripts\Activate.ps1

Start FastAPI:

    uvicorn app.main:app --reload

The backend runs locally at:

    http://127.0.0.1:8000

Automatic API documentation:

    http://127.0.0.1:8000/docs

Alternative API documentation:

    http://127.0.0.1:8000/redoc

OpenAPI specification:

    http://127.0.0.1:8000/openapi.json

---

## Database

The project currently uses PostgreSQL with a database named:

    data_quality_db

The database connection is configured through:

    backend/.env

The `.env` file is intentionally excluded from Git.

---

# 10. Dependency Management

Python dependencies are maintained in:

    backend/requirements.txt

Whenever a new Python package is required:

    1. Install the package inside the project's virtual environment.
    2. Verify that it works.
    3. Update requirements.txt.
    4. Continue development.

This ensures the project can be recreated on another machine or deployment environment.

---

# 11. Version Control

Git is used to track project development.

Major milestones are committed and pushed to GitHub.

Commits should represent meaningful checkpoints rather than every small experiment.

---

# 12. Documentation Strategy

This document is the detailed development and learning documentation for the project.

Each completed phase will receive its own detailed section containing:

- What was built
- Why it was built
- How it works
- Important concepts
- Problems encountered
- Solutions
- Technical decisions
- Lessons learned
- Interview-ready explanations

The root `README.md` will remain concise and public-facing.

---

# 13. Current Status

Current phase:

**Phase 2 — Dataset Research**

Completed phases:

- Phase 0 — Planning
- Phase 1 — Environment & Backend Foundation
- Phase 2 — Dataset Research

Next phase:

**Phase 3 — Dataset Ingestion**

---

# 14. Phase 1 — Environment & Backend Foundation

## 14.1 Objective

The objective of Phase 1 was to establish the complete backend foundation required for the data-quality platform.

Before implementing dataset analysis, anomaly detection, or the frontend, the application needed a reliable way to:

- Run a Python backend
- Expose API endpoints
- Connect to a relational database
- Store dataset metadata
- Validate incoming API data
- Manage database sessions safely
- Keep credentials outside source code
- Track the project using Git and GitHub

The resulting architecture was:

    Client / API Request
            ↓
        FastAPI
            ↓
      Pydantic Validation
            ↓
       SQLAlchemy ORM
            ↓
        PostgreSQL
            ↓
       Stored Metadata


## 14.2 Python Virtual Environment

A Python virtual environment was created inside the backend:

    backend/
    └── venv/

A virtual environment isolates the project's Python packages from the global Python installation.

This is important because different projects may require different package versions.

For example:

    Project A → FastAPI version A
    Project B → FastAPI version B

Without isolation, package versions can conflict.

The virtual environment therefore acts as a project-specific Python environment.

The virtual environment is not committed to GitHub because it can be recreated from `requirements.txt`.

---

## 14.3 Dependency Management

The backend uses a `requirements.txt` file to record its Python dependencies.

Important packages used during Phase 1 include:

- FastAPI
- Uvicorn
- Pandas
- NumPy
- SQLAlchemy
- psycopg2-binary
- python-multipart
- python-dotenv
- openpyxl

When a new Python package is required, the development workflow is:

    Install package
          ↓
    Verify it works
          ↓
    Update requirements.txt
          ↓
    Continue development

This ensures that the project can be recreated on another machine or deployment environment.

---

## 14.4 FastAPI

FastAPI is the backend web framework used by the project.

Its responsibility is to receive HTTP requests, execute application logic, and return responses.

Conceptually:

    Client
      ↓
    HTTP Request
      ↓
    FastAPI
      ↓
    Python Function
      ↓
    HTTP Response

For example, a client can send a request to:

    POST /datasets

FastAPI receives the request and passes the submitted data to the corresponding Python function.

FastAPI also automatically generates API documentation using the OpenAPI specification.

The project exposes:

    /docs
    /redoc
    /openapi.json

The `/docs` interface provides an interactive Swagger UI that can be used to test endpoints directly from the browser.

---

## 14.5 Uvicorn

Uvicorn is the ASGI server used to run the FastAPI application.

FastAPI defines the application and its routes, while Uvicorn provides the server that actually runs the application and listens for HTTP requests.

The backend is started using:

    uvicorn app.main:app --reload

The `--reload` option automatically restarts the development server when source files are modified.

The local server runs at:

    http://127.0.0.1:8000

---

## 14.6 REST API Fundamentals

The project communicates through HTTP endpoints.

An API allows one software component to communicate with another through defined requests and responses.

The first API endpoints implemented were:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Backend health/welcome response |
| POST | `/datasets` | Create a dataset metadata record |
| GET | `/datasets` | Retrieve stored dataset metadata |

### GET

GET is generally used to retrieve information.

Example:

    GET /datasets

returns the dataset records stored in the database.

### POST

POST is used to submit data to the server.

Example:

    POST /datasets

submits metadata for a dataset that should be stored.

---

## 14.7 PostgreSQL

PostgreSQL is the relational database used by the project.

The database created for the project is:

    data_quality_db

The database provides persistent storage.

This means that data stored in PostgreSQL remains available even after the FastAPI server is stopped and restarted.

The application does not store important application data only in Python variables because those variables would disappear when the application process stops.

---

## 14.8 SQLAlchemy

SQLAlchemy is the Python database toolkit and ORM used to communicate with PostgreSQL.

Instead of manually writing SQL for every database operation, the project can represent database tables as Python classes and interact with them using Python objects.

Conceptually:

    Python Object
          ↓
      SQLAlchemy
          ↓
      SQL Query
          ↓
      PostgreSQL


## 14.9 ORM — Object Relational Mapping

ORM stands for Object Relational Mapping.

The project's `Dataset` Python class represents the `datasets` database table.

Conceptually:

    Python Class
        Dataset
           ↓
       SQLAlchemy
           ↓
    PostgreSQL Table
        datasets

The model contains fields such as:

- `id`
- `file_name`
- `file_path`
- `rows_count`
- `columns_count`
- `uploaded_at`

This allows application code to work with Python objects instead of manually constructing SQL statements for basic operations.

---

## 14.10 SQLAlchemy Database Model

The `Dataset` model is defined in:

    backend/app/models.py

The model inherits from SQLAlchemy's declarative base.

The primary key is:

    id

Other columns store metadata about a dataset.

The database table is created from the ORM model using SQLAlchemy metadata.

This creates the relationship:

    models.py
        ↓
    SQLAlchemy metadata
        ↓
    PostgreSQL datasets table

---

## 14.11 Database Engine

The database engine is configured in:

    backend/app/database.py

The engine represents the application's connection mechanism to PostgreSQL.

The database URL is obtained from the environment rather than being written directly into the Python source code.

The application also performs a basic connection test using:

    SELECT 1

This was used during development to verify that the application could communicate successfully with PostgreSQL.

---

## 14.12 Environment Variables and `.env`

Database credentials should not be written directly into source code.

The project therefore uses:

    backend/.env

The database connection URL is stored there and loaded using `python-dotenv`.

The `.env` file is excluded through `.gitignore`.

This prevents database credentials from being accidentally pushed to GitHub.

This is an important security practice for both development and deployment.

---

## 14.13 Database Sessions

SQLAlchemy sessions are used to communicate with the database during individual operations.

The project creates a session factory called:

    SessionLocal

A request obtains a database session through:

    get_db()

The simplified lifecycle is:

    HTTP Request
         ↓
    Create DB Session
         ↓
    Perform database operation
         ↓
    Return response
         ↓
    Close DB Session

Closing the session after the request prevents unnecessary database connections from remaining open.

---

## 14.14 FastAPI Dependency Injection

FastAPI's dependency injection system is used to provide database sessions to API endpoints.

The routes use:

    Depends(get_db)

This allows FastAPI to automatically obtain the database session required by the endpoint.

The endpoint therefore does not need to manually create and close a session every time.

The database session is also closed safely after the request.

This pattern becomes particularly useful as the application grows because many endpoints will need database access.

---

## 14.15 Pydantic Request Validation

The `DatasetCreate` model in `main.py` is a Pydantic model.

It defines the expected structure of data submitted to:

    POST /datasets

The request contains:

- `file_name`
- `file_path`
- `rows_count`
- `columns_count`

Pydantic validates incoming data before the endpoint processes it.

Conceptually:

    Client Request
         ↓
    Pydantic Validation
         ↓
    Valid Data
         ↓
    API Logic

If the incoming request does not match the expected structure or data types, FastAPI can reject it automatically.

---

## 14.16 POST /datasets

The `POST /datasets` endpoint creates a new `Dataset` object from the validated request data.

The process is:

    Client
      ↓
    POST /datasets
      ↓
    DatasetCreate validation
      ↓
    Dataset ORM object
      ↓
    SQLAlchemy session
      ↓
    PostgreSQL
      ↓
    Created record returned

This was the first proper API-based database write in the project.

---

## 14.17 GET /datasets

The `GET /datasets` endpoint retrieves dataset records from PostgreSQL.

The process is:

    Client
      ↓
    GET /datasets
      ↓
    SQLAlchemy query
      ↓
    PostgreSQL
      ↓
    Dataset records
      ↓
    API response

This confirmed that the application could both write to and read from the database through FastAPI.

---

## 14.18 Temporary Database Test

During the initial database setup, a temporary script was created:

    backend/app/test_db.py

Its purpose was to manually verify that Python and SQLAlchemy could insert a record into PostgreSQL.

A test record similar to the following was inserted:

    file_name: sales.csv
    file_path: datasets/sales.csv
    rows_count: 5000
    columns_count: 12

After the proper `/datasets` API endpoints were implemented, this script became a temporary development utility rather than part of the final application architecture.

It is being kept temporarily and will be removed during a later backend cleanup once it is no longer needed.

---

## 14.19 Problems Encountered During Phase 1

### PostgreSQL command not initially recognized

The `psql` command was initially unavailable from the terminal because PostgreSQL's executable directory was not available through PATH.

The PostgreSQL installation was verified and the required PATH configuration was corrected.

---

### PowerShell execution policy

Activating the virtual environment using:

    .\venv\Scripts\Activate.ps1

initially produced a PowerShell execution-policy error.

A command-based activation approach was used successfully.

This demonstrated that Windows PowerShell security policies can affect local Python development environments.

---

### Database connection URL issue

The PostgreSQL password contained the `@` character.

When special characters appear inside a database connection URL, they can be interpreted as URL syntax rather than part of the password.

The password character therefore had to be URL-encoded in the connection string.

---

### Missing SQLAlchemy package

At one point, Python was run outside the virtual environment, causing:

    ModuleNotFoundError: No module named 'sqlalchemy'

The issue was that the global Python interpreter was being used instead of the project's virtual environment.

The virtual environment was activated before continuing.

---

### Missing `openpyxl`

When the Online Retail Excel dataset was first inspected, Pandas reported that `openpyxl` was missing.

`openpyxl` was installed and subsequently added to `requirements.txt`.

This is required because Pandas uses an Excel-reading engine to load `.xlsx` files.

---

## 14.20 Git and GitHub

Git was configured for version control.

The project was pushed to a GitHub repository so that development progress could be backed up and tracked.

Meaningful milestones were committed rather than relying on a single final upload.

The project also uses `.gitignore` to prevent files such as:

- `venv/`
- `.env`
- `__pycache__/`
- `node_modules/`

from being committed.

A database credential was accidentally exposed during early development. The password was rotated and the Git history was cleaned before the project continued.

The important lesson was that secrets should never be committed to source control, even temporarily.

---

## 14.21 Phase 1 Result

At the end of Phase 1, the project had a functional backend foundation:

    FastAPI
       ↓
    Pydantic
       ↓
    SQLAlchemy
       ↓
    PostgreSQL

The backend could:

- Start successfully
- Connect to PostgreSQL
- Create the required database table
- Validate dataset metadata
- Store dataset metadata
- Retrieve dataset metadata
- Manage database sessions
- Generate automatic API documentation

This foundation is now ready for the actual data-processing functionality.

---

## 14.22 Phase 1 Interview Explanation

A concise interview explanation:

> I first established the backend foundation using FastAPI and PostgreSQL. I used SQLAlchemy as the ORM to map a Python Dataset model to a PostgreSQL table and Pydantic to validate incoming API requests. I implemented POST and GET endpoints for dataset metadata and used FastAPI dependency injection to manage database sessions safely. Database credentials were kept in environment variables and Git was used for version control.

### Key interview questions I should be able to answer

**Why FastAPI?**

FastAPI provides a lightweight Python framework for building APIs with automatic validation and OpenAPI documentation. It also works naturally with Python-based data-processing libraries.

**Why PostgreSQL?**

The project needs persistent structured storage for dataset metadata and analysis results. PostgreSQL is a mature relational database suitable for this requirement.

**Why SQLAlchemy?**

SQLAlchemy allows the application to interact with PostgreSQL through Python objects and ORM models while providing a structured database-access layer.

**What is an ORM?**

An ORM maps objects in application code to relational database tables, allowing developers to work with database records through programming-language objects.

**Why Pydantic?**

Pydantic validates incoming API data against defined schemas before the application processes it.

**Why use `Depends(get_db)`?**

It allows FastAPI to provide a database session to an endpoint and ensures the session lifecycle is handled consistently.

**Why not store the database password directly in Python?**

Credentials should be kept outside source code so they are not exposed through version control and can be changed independently between environments.

---

# 15. Phase 2 — Dataset Research

## 15.1 Objective

The objective of Phase 2 was to select a realistic dataset and understand its structure, characteristics, and existing data-quality problems before building the actual data-ingestion and quality-analysis engines.

Instead of creating artificial problems in a fabricated dataset, the project uses a real-world public dataset so that the framework can be designed around genuine data-quality challenges.

The selected primary dataset is the:

**UCI Online Retail Dataset**

The dataset contains transactional records from a UK-based online retail business.

---

## 15.2 Why the Online Retail Dataset Was Selected

The dataset was selected because it provides a useful combination of:

- Large dataset size
- Multiple data types
- Missing values
- Duplicate records
- Numerical variables suitable for anomaly detection
- Categorical variables
- Dates and timestamps
- Customer information
- Product information
- Transaction information
- Multiple countries
- Business-specific patterns

This makes it suitable for demonstrating the complete data-quality workflow.

The dataset is also large enough to make the project feel realistic while remaining manageable for local development.

---

## 15.3 Dataset Structure

The dataset contains:

- **541,909 rows**
- **8 columns**
- **25,900 unique invoices**
- **4,070 unique products**
- **4,372 identified customers**
- **38 countries**

The columns are:

| Column | Description |
|---|---|
| `InvoiceNo` | Invoice or transaction identifier |
| `StockCode` | Product/item identifier |
| `Description` | Product description |
| `Quantity` | Quantity of the product in the transaction |
| `InvoiceDate` | Transaction date and time |
| `UnitPrice` | Price per unit |
| `CustomerID` | Customer identifier |
| `Country` | Country associated with the transaction |

---

## 15.4 Important Data Concept: Rows vs Transactions

A row in this dataset represents a transaction line item rather than necessarily an entire transaction.

This is demonstrated by the difference between:

    541,909 rows

and:

    25,900 unique invoices

A single invoice can contain multiple products and therefore multiple rows.

For example:

    Invoice 536365
        ├── Product A
        ├── Product B
        ├── Product C
        └── Product D

Therefore:

    Row ≠ Transaction

This distinction will be important later when calculating dataset metrics and business-level statistics.

---

## 15.5 Data Types

The observed data types were:

| Column | Data Type |
|---|---|
| `InvoiceNo` | object |
| `StockCode` | object |
| `Description` | object |
| `Quantity` | int64 |
| `InvoiceDate` | datetime |
| `UnitPrice` | float64 |
| `CustomerID` | float64 |
| `Country` | string |

An important observation is that `CustomerID` is represented as a floating-point value even though it functions primarily as an identifier.

This is something the future profiling engine should be capable of identifying and reporting rather than assuming that every numeric column is a numerical measurement.

---

## 15.6 Missing Values

The dataset contains missing values in two columns.

| Column | Missing Values | Percentage |
|---|---:|---:|
| `CustomerID` | 135,080 | 24.93% |
| `Description` | 1,454 | 0.27% |
| All other columns | 0 | 0% |

The most significant issue is `CustomerID`, where almost one quarter of the records have no customer identifier.

This provides a strong real-world example for the **Completeness** dimension of data quality.

The framework should report the issue rather than automatically deleting the affected rows.

---

## 15.7 Duplicate Records

The dataset contains:

**5,268 duplicate rows**

Duplicate records are an important **Uniqueness** issue.

The future framework should identify duplicate records and report their quantity and proportion rather than silently removing them.

This preserves the distinction between:

    Detecting a data-quality problem

and:

    Automatically modifying the original data

The framework's primary responsibility is assessment and explanation.

---

## 15.8 Numerical Data Investigation

The main numerical columns investigated were:

- `Quantity`
- `UnitPrice`

The observed ranges were:

| Column | Minimum | Maximum |
|---|---:|---:|
| `Quantity` | -80,995 | 80,995 |
| `UnitPrice` | -11,062.06 | 38,970 |

These extreme values make the columns useful candidates for later anomaly detection.

However, extreme values cannot automatically be classified as errors.

---

## 15.9 Negative Quantities

There are:

**10,624 records with negative quantities.**

The dataset uses invoice numbers beginning with `C` for cancellation/credit-style transactions.

Of the negative-quantity records:

- **9,288** were associated with `C` invoices.
- **1,336** did not have a `C` invoice prefix.

This demonstrated an important principle:

> A negative value is not automatically a data-quality error.

Many negative quantities can represent legitimate business events such as cancellations or returns.

The framework therefore needs to consider context instead of using simplistic rules such as:

    Quantity < 0 → Invalid

---

## 15.10 Zero and Negative Unit Prices

The investigation found:

- **2 negative `UnitPrice` values**
- **2,515 zero `UnitPrice` values**

Negative unit prices are highly unusual and may be useful candidates for validity investigation.

Zero prices are more ambiguous because they may represent legitimate business cases such as free items, adjustments, or other special transactions.

Therefore, these values should be **flagged for investigation rather than automatically deleted or classified as errors**.

---

## 15.11 Missing and Unusual Values Can Occur Together

Some records with negative quantities and zero prices also contained missing descriptions and missing customer IDs.

For example, certain records contained a combination of:

- Negative `Quantity`
- `UnitPrice = 0`
- Missing `Description`
- Missing `CustomerID`

This demonstrates why examining individual columns independently is not always sufficient.

A high-quality framework should eventually be capable of identifying combinations of issues and providing context.

---

## 15.12 Cardinality and Unique Values

The number of unique values observed in each column was:

| Column | Unique Values |
|---|---:|
| `InvoiceNo` | 25,900 |
| `StockCode` | 4,070 |
| `Description` | 4,223 |
| `Quantity` | 722 |
| `InvoiceDate` | 23,260 |
| `UnitPrice` | 1,630 |
| `CustomerID` | 4,372 |
| `Country` | 38 |

Cardinality refers to the number of distinct values in a column.

Understanding cardinality is useful for determining the nature of a column.

For example:

- `Country` has relatively low cardinality.
- `InvoiceNo` has many unique values.
- `Quantity` has only 722 distinct values despite containing more than 500,000 records.

The future profiling engine should calculate and report these characteristics automatically.

---

## 15.13 Geographic Distribution

The dataset contains transactions from:

**38 countries**

The top countries by number of records were:

| Country | Records |
|---|---:|
| United Kingdom | 495,478 |
| Germany | 9,495 |
| France | 8,557 |
| EIRE | 8,196 |
| Spain | 2,533 |
| Netherlands | 2,371 |
| Belgium | 2,069 |
| Switzerland | 2,002 |
| Portugal | 1,519 |
| Australia | 1,259 |

The United Kingdom accounts for the large majority of records.

This will be useful later when designing visualizations because a simple country distribution chart may heavily emphasize the UK and hide smaller categories.

---

## 15.14 Time Range

The dataset covers:

**1 December 2010 → 9 December 2011**

This provides approximately one year of transaction history.

The presence of timestamps also creates opportunities for future temporal profiling and analysis.

---

## 15.15 Cancellation Pattern

The investigation found:

- **9,288 cancellation/credit-style rows**
- **532,621 normal rows**

These counts refer to rows rather than unique invoices.

The cancellation pattern was particularly useful for understanding why a purely numerical rule can be misleading.

For example:

    Negative Quantity

may be normal when associated with a cancellation, but may deserve further investigation when the same pattern occurs outside that context.

This supports the project's decision to include **context-aware/business rules** alongside statistical checks.

---

## 15.16 StockCode and Description Consistency

A consistency investigation grouped records by `StockCode` and counted the number of distinct descriptions associated with each product code.

The result was:

**650 StockCodes appeared with multiple descriptions.**

Some examples included product codes associated with:

- 2 descriptions
- 3 descriptions
- One observed code with as many as 8 descriptions

This provides a real example of a potential **Consistency** issue.

However, the framework should not automatically assume that every multiple-description case is an error.

Possible explanations may include changes or inconsistencies in the source data.

Therefore, the system should flag the relationship for investigation and provide the evidence behind the flag.

---

## 15.17 Data Quality Dimensions Derived From Research

The dataset research led to the definition of the initial quality dimensions for the framework.

### Completeness

Detect missing values.

Example:

    CustomerID → 24.93% missing

### Uniqueness

Detect duplicate records.

Example:

    5,268 duplicate rows

### Validity

Detect values that violate defined structural or business rules.

Examples:

    Negative UnitPrice
    Invalid ranges
    Unexpected values

### Consistency

Check relationships between related fields.

Example:

    StockCode ↔ Description

### Anomaly Detection

Identify statistically unusual observations.

Planned methods:

    Z-score
    IQR
    Isolation Forest

### Context-Aware Business Rules

Interpret unusual values using domain context.

Example:

    Negative Quantity
          +
    Cancellation Invoice
          ↓
    Potentially legitimate business event

---

## 15.18 Important Concept: Anomaly vs Error

One of the most important lessons from the dataset research was:

    Anomaly ≠ Automatically Error

An anomaly is an observation that is unusual compared with the rest of the data.

A data-quality error is a value that violates a defined expectation or rule.

For example:

    Quantity = 80,995

may be statistically extreme, but it could theoretically represent a legitimate bulk transaction.

Similarly:

    Quantity = -10

may initially look invalid but can represent a legitimate cancellation.

The framework should therefore identify unusual observations and provide context rather than blindly modifying or deleting them.

---

## 15.19 Tools Used During Dataset Research

Pandas was used to inspect the dataset.

Important operations included:

- `read_excel()` — loading the Excel dataset
- `shape` — determining rows and columns
- `columns` — inspecting column names
- `dtypes` — inspecting data types
- `isnull()` / `isna()` — identifying missing values
- `duplicated()` — identifying duplicate rows
- `nunique()` — counting unique values
- `value_counts()` — measuring category frequencies
- Boolean filtering — investigating specific conditions
- `groupby()` — investigating relationships between fields
- `describe()` — calculating numerical summary statistics

These exploratory commands were used to understand the dataset before implementing the automated profiling engine.

The eventual system will move this exploratory logic into reusable backend functions so users will not need to manually run analysis commands.

---

## 15.20 Phase 2 Result

Phase 2 established the real-world data foundation for the project.

The framework is no longer being designed around hypothetical data problems. Its initial requirements are based on observations from an actual large transactional dataset.

The research identified:

- Missing data
- Duplicate records
- Unusual numerical values
- Cancellation patterns
- Potential validity issues
- Potential consistency issues
- High-cardinality and low-cardinality fields
- Temporal information
- Geographic distribution
- Context-dependent business behavior

These findings directly informed the initial design of the Data Profiling Engine and Data Quality Engine.

---

## 15.21 Phase 2 Interview Explanation

A concise interview explanation:

> I selected the UCI Online Retail dataset because it contains over 541,000 real transaction-line records with missing values, duplicates, numerical anomalies, categorical data, timestamps, customer and product relationships, and business-specific cancellation patterns. I profiled the dataset using Pandas and found issues such as 24.93% missing CustomerIDs, 5,268 duplicate rows, and 650 product codes associated with multiple descriptions. I also found that negative quantities often represented cancellation transactions, which led me to design the framework so that anomalies are interpreted using context rather than automatically treated as errors.

### Key interview questions I should be able to answer

**Why did you choose this dataset?**

It provides a large, realistic transactional dataset containing several different types of data-quality problems, making it suitable for demonstrating profiling, quality assessment, and anomaly detection.

**Why didn't you simply clean the dataset first?**

The purpose of the framework is to assess data quality. Automatically cleaning everything would hide the problems we are trying to detect and explain.

**Why isn't every negative quantity considered invalid?**

Because the dataset contains cancellation/credit transactions where negative quantities can represent legitimate business events.

**What is the difference between an anomaly and an error?**

An anomaly is an unusual observation, while an error violates an expected rule or constraint. An unusual value can still be legitimate.

**What quality dimensions did your research identify?**

Completeness, uniqueness, validity, consistency, anomaly detection, and context-aware business rules.
