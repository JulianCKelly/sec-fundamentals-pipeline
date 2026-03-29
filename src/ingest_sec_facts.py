import os
import json
import requests

API_KEY = os.getenv("SEC_API_KEY")
BASE_URL = "https://api.sec-api.io"

COMPANIES = {
    "AAPL": "320193",
    "MSFT": "789019",
    "NVDA": "1045810",
    "JPM": "19617",
    "AMZN": "1018724",
}


def fetch_filings(cik: str):
    query = {
        "query": f'cik:{cik} AND (formType:"10-K" OR formType:"10-Q")',
        "from": "0",
        "size": "10",
        "sort": [{"filedAt": {"order": "desc"}}],
    }

    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json",
    }

    response = requests.post(BASE_URL, json=query, headers=headers, timeout=30)

    if response.status_code != 200:
        raise Exception(f"API error {response.status_code}: {response.text}")

    return response.json()


def save_raw_data(ticker: str, data: dict):
    os.makedirs("data/raw", exist_ok=True)
    filepath = f"data/raw/{ticker}_filings.json"

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved: {filepath}")


def main():
    if not API_KEY:
        raise ValueError("Set SEC_API_KEY in your environment")

    for ticker, cik in COMPANIES.items():
        print(f"Fetching {ticker}...")
        data = fetch_filings(cik)
        save_raw_data(ticker, data)


if __name__ == "__main__":
    main()