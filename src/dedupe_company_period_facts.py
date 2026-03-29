from pathlib import Path
import pandas as pd


STANDARDIZED_PATH = Path("data/interim/xbrl_facts_standardized.parquet")
OUT_PATH = Path("data/interim/xbrl_facts_deduped.parquet")


def classify_preferred_form(row):
    """
    Lower score = better
    """
    form_type = row.get("form_type")
    period_type = row.get("canonical_period_type")

    if period_type == "instant":
        # for balance sheet style rows, filing recency matters more than form preference
        return 2

    if form_type == "10-K":
        return 1
    if form_type == "10-Q":
        return 2

    return 9


def main():
    df = pd.read_parquet(STANDARDIZED_PATH)

    # Basic cleanup
    df = df[df["value"].notna()].copy()
    df = df[df["canonical_period_end"].notna()].copy()

    # Segment preference: no segment is simpler / more canonical
    df["has_segment"] = df["segment"].notna() & (df["segment"] != "null")
    df["segment_rank"] = df["has_segment"].astype(int)

    # Form preference
    df["form_rank"] = df.apply(classify_preferred_form, axis=1)

    # Priority cleanup
    df["priority"] = pd.to_numeric(df["priority"], errors="coerce").fillna(99).astype(int)

    # Sort so best row per company-metric-period is first
    df = df.sort_values(
        by=[
            "ticker",
            "standard_metric",
            "canonical_period_end",
            "canonical_period_type",
            "priority",
            "segment_rank",
            "form_rank",
            "filed_at",
        ],
        ascending=[True, True, True, True, True, True, True, False],
    )

    deduped = df.drop_duplicates(
        subset=[
            "ticker",
            "standard_metric",
            "canonical_period_end",
            "canonical_period_type",
        ],
        keep="first",
    ).copy()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    deduped.to_parquet(OUT_PATH, index=False)

    print(deduped.head())
    print(f"Saved: {OUT_PATH}")
    print(f"Rows: {len(deduped):,}")

    print("\nRows by metric:")
    print(deduped["standard_metric"].value_counts())

    print("\nRows by ticker:")
    print(deduped["ticker"].value_counts())

    dupes_remaining = deduped.duplicated(
        subset=[
            "ticker",
            "standard_metric",
            "canonical_period_end",
            "canonical_period_type",
        ]
    ).sum()
    print(f"\nRemaining duplicate company-metric-period rows: {dupes_remaining}")


if __name__ == "__main__":
    main()