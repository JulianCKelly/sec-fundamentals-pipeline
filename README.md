# SEC Fundamentals Pipeline

A production-style data pipeline that ingests raw SEC filings and transforms them into standardized, analytics-ready financial datasets.
This project focuses on correctness, reproducibility, and handling real-world financial reporting inconsistencies across companies.

This project is designed as a case study in real-world data engineering:
- messy, semi-structured source data
- inconsistent reporting schemas across companies
- ambiguous mapping between raw fields and business metrics
- the need to produce trustworthy, decision-ready outputs

---

## Problem

Raw SEC filing data is not directly usable for analysis.

Challenges include:
- inconsistent tagging of financial metrics across companies
- duplicate or overlapping facts across filings
- mixed reporting periods (quarterly vs annual)
- lack of standardized schema for downstream consumption

The goal of this project is to:

> transform raw filing data into a clean, standardized financial dataset suitable for analytics and modeling

---

## Scope (v1)

- 5–10 companies (AAPL, MSFT, NVDA, JPM, AMZN)
- Core financial metrics:
  - revenue
  - net_income
  - total_assets
  - total_liabilities
  - operating_income
  - cash_and_cash_equivalents
  - shareholders_equity

---

## Architecture (planned)

Raw JSON (SEC API) 

Parsed / Flattened Facts (Python)

Staging (dbt)

Intermediate (standardization + deduplication)

Marts (analytics-ready tables)

---

## Repo Structure
data/
raw/        # raw API responses
interim/    # flattened / parsed data
marts/      # final outputs

src/
ingest_sec_facts.py
parse_company_facts.py

dbt_project/
seeds/
tag_mapping.csv

docs/
source_notes.md

---

## How to Run

```bash
pip install -r requirements.txt
export SEC_API_KEY=your_key_here

python src/ingest_sec_facts.py
python src/parse_company_facts.py
```

Outputs will be written to:
- data/raw/
- data/interim/

dbt layer coming next. 

Design Principles
- correctness over convenience
- explicit grain definition
- reproducible local pipeline 
- documented tradeoffs
- business-aligned modeling

## Edge Cases and Failure Modes

This project intentionally treats raw SEC data as a source that requires judgment, not blind trust.

Key edge cases this pipeline is designed to account for:

### 1. Duplicate or overlapping filings
A company may have multiple filings that appear to represent the same reporting period.  
Examples include amended forms, overlapping facts, or multiple records returned for similar filing windows.

**Current handling**
- retain filing metadata at raw level
- plan to deduplicate in transformation layers using company, form type, reporting period, and latest filing date

### 2. Quarterly vs annual reporting ambiguity
10-K and 10-Q filings represent different reporting scopes and should not be merged naively.

**Current handling**
- preserve form type in parsed outputs
- plan to model annual and quarterly reporting separately before any standardized downstream mart is built

### 3. Inconsistent metric tagging across companies
The same business concept may appear under different source tags depending on issuer or filing structure.

**Current handling**
- use an explicit tag mapping table rather than assuming one universal source field per metric
- prioritize transparency over aggressive inference

### 4. Amended filings and restatements
Amended filings may supersede prior filings or revise previously reported values.

**Current handling**
- preserve accession number and filing timestamp
- plan to define clear precedence rules so downstream outputs prefer the most relevant version of a fact

### 5. Incomplete comparability across companies
Even after normalization, financial metrics may not be perfectly comparable across issuers due to reporting practices, taxonomy differences, or missing values.

**Current handling**
- treat standardized outputs as analytics-ready, but not assumption-free
- document known gaps rather than hiding them

### 6. Metadata success does not equal financial fact success
Successfully retrieving filings does not guarantee that downstream financial concepts will be easy to parse or standardize.

**Current handling**
- separate ingestion, parsing, standardization, and mart-building into distinct layers
- treat each layer as independently testable