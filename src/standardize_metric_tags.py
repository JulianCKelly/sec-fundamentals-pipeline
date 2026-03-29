from pathlib import Path
import pandas as pd


RAW_FACTS_PATH = Path("data/interim/xbrl_facts_raw.parquet")
TAG_MAPPING_PATH = Path("dbt_project/seeds/tag_mapping.csv")
OUT_PATH = Path("data/interim/xbrl_facts_standardized.parquet")


TARGET_STATEMENTS = {
    "StatementsOfIncome",
    "BalanceSheets",
    "StatementsOfCashFlows",
}


def main():
    df = pd.read_parquet(RAW_FACTS_PATH)
    tag_map = pd.read_csv(TAG_MAPPING_PATH)

    # Keep only the statement groups we care about for fundamentals
    df = df[df["statement_name"].isin(TARGET_STATEMENTS)].copy()

    # Normalize value type
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Normalize dates
    for col in ["period_start", "period_end", "instant", "filed_at"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

    # Join mapping table
    standardized = df.merge(
        tag_map,
        how="left",
        left_on=["statement_name", "metric_key"],
        right_on=["source_statement", "metric_key"],
    )

    # Keep mapped metrics only
    standardized = standardized[standardized["standard_metric"].notna()].copy()

    # Derive canonical period_end
    standardized["canonical_period_end"] = standardized["period_end"]
    standardized.loc[
        standardized["canonical_period_end"].isna(), "canonical_period_end"
    ] = standardized["instant"]

    # Derive canonical period_type
    standardized["canonical_period_type"] = standardized["period_type"].fillna("unknown")

    # Keep only useful columns
    keep_cols = [
        "ticker",
        "form_type",
        "statement_name",
        "metric_key",
        "standard_metric",
        "priority",
        "label",
        "value",
        "unit",
        "decimals",
        "segment",
        "period_start",
        "period_end",
        "instant",
        "canonical_period_end",
        "canonical_period_type",
        "fiscal_year",
        "fiscal_period",
        "frame",
        "filed_at",
        "form",
        "accession_no",
    ]

    standardized = standardized[keep_cols].copy()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    standardized.to_parquet(OUT_PATH, index=False)

    print(standardized.head())
    print(f"Saved: {OUT_PATH}")
    print(f"Rows: {len(standardized):,}")
    print("\nStandard metrics counts:")
    print(standardized["standard_metric"].value_counts(dropna=False))


if __name__ == "__main__":
    main()