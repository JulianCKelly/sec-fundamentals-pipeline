import os
import json
from pathlib import Path

import pandas as pd
import requests

API_KEY = os.getenv("SEC_API_KEY")
XBRL_URL = "https://api.sec-api.io/xbrl-to-json"


def load_latest_filings() -> pd.DataFrame:
    df = pd.read_parquet("data/interim/filings.parquet")
    df["filed_at"] = pd.to_datetime(df["filed_at"], utc=True)

    # keep most recent filing per ticker/form_type if you want both 10-K and 10-Q
    df = df.sort_values(["ticker", "form_type", "filed_at"], ascending=[True, True, False])
    latest = df.groupby(["ticker", "form_type"], as_index=False).first()

    return latest


def fetch_xbrl_json(accession_no: str) -> dict:
    headers = {"Authorization": API_KEY}
    params = {"accession-no": accession_no}

    response = requests.get(XBRL_URL, headers=headers, params=params, timeout=60)

    if response.status_code != 200:
        raise Exception(f"XBRL API error {response.status_code}: {response.text}")

    return response.json()


def save_xbrl_json(ticker: str, form_type: str, data: dict) -> None:
    output_dir = Path("data/raw/xbrl_json")
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_form = form_type.replace("/", "_")
    outpath = output_dir / f"{ticker}_{safe_form}_xbrl.json"

    with open(outpath, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved: {outpath}")


def main():
    if not API_KEY:
        raise ValueError("Set SEC_API_KEY in your environment")

    latest = load_latest_filings()

    for _, row in latest.iterrows():
        ticker = row["ticker"]
        form_type = row["form_type"]
        accession_no = row["accession_no"]

        print(f"Fetching XBRL JSON for {ticker} {form_type} ({accession_no})...")
        data = fetch_xbrl_json(accession_no)
        save_xbrl_json(ticker, form_type, data)


if __name__ == "__main__":
    main()