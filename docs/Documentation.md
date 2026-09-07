# Project Documentation

## Overview

The Intelligent Data Quality Assessment & Anomaly Detection Framework is an enterprise-style platform for assessing structured datasets. It will ingest CSV files, profile their contents, measure data quality, identify anomalies, explain findings, and present results through a dashboard and report.

The project uses real transactional data rather than fabricated examples. Its primary reference dataset is the UCI Online Retail dataset.

## Current Status

**Completed through Phase 3 — Dataset Ingestion**

The backend currently supports:

- A FastAPI REST API with automatic OpenAPI documentation.
- PostgreSQL storage through SQLAlchemy.
- Dataset metadata records, including file name, storage path, row count, column count, and upload timestamp.
- CSV upload through `POST /datasets/upload`.
- Validation for missing names, unsupported file types, unreadable CSV content, and parsing failures.
- UUID-based local upload storage to avoid name collisions.
- Automatic metadata extraction with Pandas.

Current ingestion flow:

    CSV upload
          ↓
    Validation
          ↓
    Local file storage
          ↓
    Pandas metadata extraction
          ↓
    PostgreSQL dataset record

## Dataset Research Highlights

The UCI Online Retail dataset contains 541,909 transaction-line records and provides real examples of the problems this framework is designed to assess:

- 24.93% missing `CustomerID` values
- 5,268 duplicate rows
- Extreme and negative quantities
- Zero and negative prices
- Product-code/description consistency issues

One core design principle came from this research:

> An anomaly is not automatically a data-quality error.

For example, negative quantities can represent legitimate cancellation transactions. The framework will flag unusual values and provide context instead of automatically deleting or changing data.

## Current Architecture

    Client
      ↓
    FastAPI API
      ↓
    Dataset Ingestion Service
      ├── Local upload storage
      └── PostgreSQL metadata storage

Database credentials are supplied through a local environment file and are not committed to the repository. User-uploaded files are also excluded from Git.

## Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Environment & backend foundation | Complete |
| 2 | Dataset research | Complete |
| 3 | Dataset ingestion | Complete |
| 4 | Data profiling engine | Next |
| 5 | Data quality engine | Planned |
| 6 | Anomaly detection | Planned |
| 7 | Explainability | Planned |
| 8–10 | Dashboard, visualizations, reports | Planned |
| 11 | Deployment | Planned |
| 12 | Final documentation | Planned |

## Next Step

Phase 4 will add automatic profiling for each uploaded dataset: data types, missing values, duplicates, unique values, descriptive statistics, and column-level summaries.
