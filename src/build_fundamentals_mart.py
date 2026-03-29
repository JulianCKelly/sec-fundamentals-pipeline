from pathlib import Path
import pandas as pd


INPUT_PATH = Path("data/interim/xbrl_facts_deduped.parquet")
OUTPUT_PATH = Path("data/marts/fundamentals.parquet")


def main():
    df = pd.read_parquet(INPUT_PATH)

    # Keep only clean rows
    df = df[df["value"].notna()].copy()

    # Define grain explicitly (this is important)
    grain_cols = [
        "ticker",
        "canonical_period_end",
        "canonical_period_type",
    ]

    # Pivot metrics into columns
    mart = df.pivot_table(
        index=grain_cols,
        columns="standard_metric",
        values="value",
        aggfunc="first",
    ).reset_index()

    # Flatten column names
    mart.columns.name = None

    # Sort cleanly
    mart = mart.sort_values(
        by=["ticker", "canonical_period_end"],
        ascending=[True, True],
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    mart.to_parquet(OUTPUT_PATH, index=False)

    print(mart.head())
    print(f"\nSaved: {OUTPUT_PATH}")
    print(f"Rows: {len(mart):,}")

    print("\nColumns:")
    print(mart.columns.tolist())


if __name__ == "__main__":
    main()