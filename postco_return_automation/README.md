# PostCo Return App Identifier

Streamlit web app for identifying return management software installed on e-commerce stores — built for competitive intelligence and sales targeting at PostCo.

## Project

### Return App Identifier — `return_app_identifier.py`

A Streamlit dashboard that:
1. Accepts an uploaded CSV/Excel file with store data (installed apps, technologies, sales rank)
2. Matches each store against a reference list of 30+ known return management platforms
3. Deduplicates by domain — keeps the highest-ranked store when duplicates exist
4. Reports which stores use return apps and which use multiple
5. Exports a multi-sheet Excel report with summary metrics

## Usage

```bash
streamlit run return_app_identifier.py
```

Then upload your data file in the browser UI.

**Required input columns:**

| Column | Description |
|--------|-------------|
| `domain` | Store domain |
| `installed_apps_names` | Colon-separated list of installed apps |
| `technologies` | Colon-separated list of technologies |
| `platform_rank` | Store rank on platform (higher = more prominent) |
| `estimated_yearly_sales` | Estimated annual revenue |

**Optional:** Upload a custom return app reference list (CSV/Excel with `Competitor` and `RC` columns). If not provided, the built-in default list of 32 apps is used.

## Output

Excel file with three sheets:
- **Brands With Return App** — all stores using at least one return app
- **Brands With >1 Return App** — stores using multiple return apps
- **Summary** — totals and detection rate

## Setup

```bash
pip install -r requirements.txt
```
