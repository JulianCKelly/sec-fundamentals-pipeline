# Source Notes

## SEC API Exploration

Using:
https://sec-api.io/sandbox

---

## Observations

- Data is semi-structured and varies by filing
- Same financial concept appears under multiple tags
- Quarterly and annual data are mixed
- Duplicate facts exist across filings and amendments

---

## Key Questions

1. What is the raw grain of the dataset?
2. How should duplicate facts be resolved?
3. How do we distinguish quarterly vs annual reporting?
4. Which tags map to standardized financial metrics?

---

## Early Decisions

- Limit scope to a small set of companies
- Use explicit tag mapping rather than dynamic inference
- Prefer latest filing when duplicates exist
- Separate annual and quarterly logic

---

## Known Ambiguities

- Tag inconsistency across companies
- Missing values for certain metrics
- Restatements and amended filings
- Units and scaling differences

These will be addressed in transformation layers.