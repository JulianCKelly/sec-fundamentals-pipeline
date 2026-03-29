# SEC Fundamentals Pipeline

A financial data pipeline that ingests raw SEC filing data, standardizes XBRL facts, and produces a clean, analytics-ready fundamentals dataset.

This project is structured as a real-world data engineering case study:
- messy, semi-structured source data (SEC filings + XBRL)
- inconsistent tagging across companies
- overlapping and duplicate facts across filings
- the need to produce a single, trustworthy dataset for analysis

## Why This Matters

Financial data pipelines fail silently when:
- multiple tags represent the same metric (revenue vs sales)
- filings overlap or restate prior periods
- instant and duration metrics are mixed

This pipeline enforces:
- one canonical metric per concept
- one fact per company-metric-period
- explicit separation of point-in-time vs flow data

The result is a dataset that can be safely used for analysis without hidden duplication or semantic ambiguity.

---

## Problem

Raw SEC XBRL data is not directly usable.

Challenges include:
- inconsistent metric tagging (multiple tags for the same concept)
- duplicate facts across filings and amendments
- mixed reporting periods (instant vs duration)
- segmented vs non-segmented facts
- no standard schema for downstream use

The goal of this pipeline is to:

#### transform raw SEC filing data into a clean, standardized, deduplicated financial dataset.

---

## Scope (v1)

Companies:
- AAPL, MSFT, NVDA, JPM, AMZN

Core metrics:
- revenue
- net_income
- operating_income
- total_assets
- total_liabilities
- cash_and_cash_equivalents
- shareholders_equity

---

## Pipeline Stages

| Stage | Output | Purpose | Rows |
|---|---|---|---:|
| Filing ingestion | `data/raw/*_filings.json` | discover recent filings | |
| Filing parse | `data/interim/filings.parquet` | normalize filing metadata | |
| XBRL ingest | `data/raw/xbrl_json/*` | retrieve structured statements | |
| Flatten | `data/interim/xbrl_facts_raw.parquet` | convert nested JSON → rows | 69,171 |
| Standardize | `data/interim/xbrl_facts_standardized.parquet` | map tags → canonical metrics | 1,959 |
| Dedupe | `data/interim/xbrl_facts_deduped.parquet` | enforce one fact per company-metric-period | 145 |
| Mart | `data/marts/fundamentals.parquet` | analytics-ready dataset | 63 |

---

## Key Design Decisions

### 1. Canonical Metric Mapping

SEC tags are mapped to standardized metrics using a seed file:

dbt_project/seeds/tag_mapping.csv

Each mapping includes:
- source statement
- raw XBRL tag
- canonical metric
- priority ranking

Tradeoff:
- Manual mapping requires maintenance
- But ensures deterministic and explainable metric selection

---

### 2. Explicit Grain Definition

Final grain:

ticker, canonical_period_end, and canonical_period_type

Where:
- `duration` = income statement metrics
- `instant` = balance sheet metrics

This avoids mixing incompatible financial concepts.

---

### 3. Precedence Rules (Deduplication)

When multiple facts exist for the same company, metric, and period:

1. Lower mapping priority wins (more canonical tag)
2. Non-segmented facts preferred over segmented
3. Preferred filing form (10-K vs 10-Q depending on context)
4. Most recent filing as final tie-breaker

Tradeoff:
- Ranking logic may discard valid alternate representations
- But guarantees a single source of truth per metric

Result:
Remaining duplicate company-metric-period rows: 0
---

### 4. Correctness Over Convenience

The pipeline does not assume:
- tags are consistent
- filings are clean
- one fact exists per metric

Instead, it explicitly:
- standardizes
- filters
- ranks
- deduplicates

before producing outputs.

---

## Example Output

| ticker | canonical_period_end | canonical_period_type | revenue | net_income | total_assets |
|---|---|---|---:|---:|---:|
| AAPL | 2024-09-28 | duration | ... | ... | ... |
| AAPL | 2024-09-28 | instant | ... | ... | 364980000000 |

- `duration` rows represent flow metrics (income statement)
- `instant` rows represent point-in-time metrics (balance sheet)

---

## Repo Structure

```bash
data/
  raw/        # raw API responses
  interim/    # cleaned / normalized data
  marts/      # final outputs

src/
  ingest_xbrl_json.py
  flatten_xbrl_json.py
  standardize_metric_tags.py
  dedupe_company_period_facts.py
  build_fundamentals_mart.py

dbt_project/
  seeds/
    tag_mapping.csv

docs/
  source_notes.md
```
---

## How to Run

```bash
pip install -r requirements.txt
python src/ingest_xbrl_json.py
python src/flatten_xbrl_json.py
python src/standardize_metric_tags.py
python src/dedupe_company_period_facts.py
python src/build_fundamentals_mart.py
```

---
### Edge Cases Handled
- multiple tags mapping to the same metric
- duplicate facts across filings
- segmented vs consolidated facts
- missing or partial periods
- inconsistent statement naming across companies
- instant vs duration metric conflicts

## Next Steps

### Data Modeling
- split final outputs into:
  - income statement (duration metrics)
  - balance sheet (instant metrics)
- enforce stricter schema constraints (types, null handling)

### Data Quality
- add validation checks:
  - uniqueness of company-period-metric
  - missing critical fields
  - sanity checks on financial values
- surface row counts and validation summaries

### Pipeline Evolution
- migrate transformations into dbt models
- expand coverage beyond initial company set
- introduce incremental ingestion for new filings

### Consumption Layer
- add lightweight analysis notebook or dashboard
- expose dataset for downstream analytics use cases
---

### Design Principles
- correctness over convenience
- explicit grain definition
- reproducible local pipeline
- documented tradeoffs
- business-aligned modeling

