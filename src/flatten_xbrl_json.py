import json
from pathlib import Path
from typing import Any

import pandas as pd


RAW_DIR = Path("data/raw/xbrl_json")
OUT_PATH = Path("data/interim/xbrl_facts_raw.parquet")


def safe_get(d: dict, key: str, default=None):
    return d.get(key, default) if isinstance(d, dict) else default


def extract_fact_rows(
    ticker: str,
    form_type: str,
    statement_name: str,
    metric_key: str,
    metric_payload: Any,
) -> list[dict]:
    rows = []

    # Most useful case: metric maps to a list of fact dicts
    if isinstance(metric_payload, list):
        for fact in metric_payload:
            if not isinstance(fact, dict):
                continue

            rows.append(
                {
                    "ticker": ticker,
                    "form_type": form_type,
                    "statement_name": statement_name,
                    "metric_key": metric_key,
                    "label": safe_get(fact, "label"),
                    "value": safe_get(fact, "value"),
                    "unit": safe_get(fact, "unitRef") or safe_get(fact, "unit"),
                    "decimals": safe_get(fact, "decimals"),
                    "segment": json.dumps(safe_get(fact, "segment")) if safe_get(fact, "segment") is not None else None,
                    "period_start": safe_get(fact, "period", {}).get("startDate") if isinstance(safe_get(fact, "period"), dict) else safe_get(fact, "startDate"),
                    "period_end": safe_get(fact, "period", {}).get("endDate") if isinstance(safe_get(fact, "period"), dict) else safe_get(fact, "endDate"),
                    "instant": safe_get(fact, "period", {}).get("instant") if isinstance(safe_get(fact, "period"), dict) else safe_get(fact, "instant"),
                    "period_type": "instant" if (isinstance(safe_get(fact, "period"), dict) and safe_get(fact, "period", {}).get("instant")) or safe_get(fact, "instant") else "duration",
                    "fiscal_year": safe_get(fact, "fy"),
                    "fiscal_period": safe_get(fact, "fp"),
                    "frame": safe_get(fact, "frame"),
                    "filed_at": safe_get(fact, "filedAt"),
                    "form": safe_get(fact, "form"),
                    "accession_no": safe_get(fact, "accn") or safe_get(fact, "accessionNo"),
                }
            )

    # Sometimes metric payload is a dict with metadata + facts nested deeper
    elif isinstance(metric_payload, dict):
        # try common nested keys first
        nested_candidates = ["facts", "data", "items", "values"]
        found_nested = False

        for nested_key in nested_candidates:
            nested = metric_payload.get(nested_key)
            if isinstance(nested, list):
                found_nested = True
                rows.extend(
                    extract_fact_rows(
                        ticker=ticker,
                        form_type=form_type,
                        statement_name=statement_name,
                        metric_key=metric_key,
                        metric_payload=nested,
                    )
                )

        if not found_nested:
            # keep one metadata-only row if structure is unusual
            rows.append(
                {
                    "ticker": ticker,
                    "form_type": form_type,
                    "statement_name": statement_name,
                    "metric_key": metric_key,
                    "label": safe_get(metric_payload, "label"),
                    "value": safe_get(metric_payload, "value"),
                    "unit": safe_get(metric_payload, "unitRef") or safe_get(metric_payload, "unit"),
                    "decimals": safe_get(metric_payload, "decimals"),
                    "segment": json.dumps(safe_get(metric_payload, "segment")) if safe_get(metric_payload, "segment") is not None else None,
                    "period_start": safe_get(metric_payload, "period", {}).get("startDate") if isinstance(safe_get(metric_payload, "period"), dict) else safe_get(metric_payload, "startDate"),
                    "period_end": safe_get(metric_payload, "period", {}).get("endDate") if isinstance(safe_get(metric_payload, "period"), dict) else safe_get(metric_payload, "endDate"),
                    "instant": safe_get(metric_payload, "period", {}).get("instant") if isinstance(safe_get(metric_payload, "period"), dict) else safe_get(metric_payload, "instant"),
                    "period_type": "instant" if (isinstance(safe_get(metric_payload, "period"), dict) and safe_get(metric_payload, "period", {}).get("instant")) or safe_get(metric_payload, "instant") else "duration",
                    "fiscal_year": safe_get(metric_payload, "fy"),
                    "fiscal_period": safe_get(metric_payload, "fp"),
                    "frame": safe_get(metric_payload, "frame"),
                    "filed_at": safe_get(metric_payload, "filedAt"),
                    "form": safe_get(metric_payload, "form"),
                    "accession_no": safe_get(metric_payload, "accn") or safe_get(metric_payload, "accessionNo"),
                }
            )

    return rows


def parse_file(path: Path) -> list[dict]:
    with open(path, "r") as f:
        data = json.load(f)

    filename = path.stem  # e.g. AAPL_10-K_xbrl
    parts = filename.split("_")
    ticker = parts[0]
    form_type = parts[1] if len(parts) > 1 else None

    rows = []

    if not isinstance(data, dict):
        return rows

    for statement_name, statement_payload in data.items():
        if not isinstance(statement_payload, dict):
            continue

        for metric_key, metric_payload in statement_payload.items():
            rows.extend(
                extract_fact_rows(
                    ticker=ticker,
                    form_type=form_type,
                    statement_name=statement_name,
                    metric_key=metric_key,
                    metric_payload=metric_payload,
                )
            )

    return rows


def main():
    all_rows = []

    for path in RAW_DIR.glob("*_xbrl.json"):
        print(f"Parsing {path.name}...")
        all_rows.extend(parse_file(path))

    df = pd.DataFrame(all_rows)

    if df.empty:
        raise ValueError("No rows extracted from XBRL JSON files.")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PATH, index=False)

    print(df.head())
    print(f"Saved: {OUT_PATH}")
    print(f"Rows: {len(df):,}")


if __name__ == "__main__":
    main()