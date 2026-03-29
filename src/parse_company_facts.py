import json
import pandas as pd
import os


def load_raw_files():
    records = []

    for file in os.listdir("data/raw"):
        if file.endswith(".json"):
            with open(f"data/raw/{file}", "r") as f:
                data = json.load(f)

                filings = data.get("filings", [])

                for filing in filings:
                    records.append({
                        "ticker": file.split("_")[0],
                        "cik": filing.get("cik"),
                        "form_type": filing.get("formType"),
                        "filed_at": filing.get("filedAt"),
                        "accession_no": filing.get("accessionNo"),
                    })

    return pd.DataFrame(records)


def save_parsed(df: pd.DataFrame):
    os.makedirs("data/interim", exist_ok=True)
    filepath = "data/interim/filings.parquet"
    df.to_parquet(filepath, index=False)
    print(f"Saved: {filepath}")


def main():
    df = load_raw_files()
    print(df.head())
    save_parsed(df)


if __name__ == "__main__":
    main()