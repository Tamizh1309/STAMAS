# STAMAS Architecture Overview

**STAMAS — Smart Tender Analysis & Management Assessment System**

## Core Principle

> **AI finds and understands the evidence. Rules verify it. Humans make the final decision.**

## System Topology

```text
               +----------------------------------+
               |          React Frontend          |
               | (Vite + TypeScript + Tailwind)   |
               +----------------+-----------------+
                                |
                                v
               +----------------+-----------------+
               |         FastAPI Backend          |
               | (Python 3.14 + Pydantic + PyMuPDF)|
               +--------+----------------+--------+
                        |                |
                        v                v
               +--------+-------+ +------+--------+
               |  SQLite / Postgres| | PDF Extractor |
               |     Database    | |   (PyMuPDF)   |
               +----------------+ +---------------+
```

## Data Models

1. **Tender**: Stores reference metadata (Tender ID, Title, Department, Issue/Closing dates, File path, Page count, Status).
2. **TenderPage**: Page-level extracted text and parsed tabular structures.
