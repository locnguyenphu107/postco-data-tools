# Data Cleaning Projects

Two production-ready data cleaning scripts for e-commerce data pipelines.

## Projects

### 1. Domain & Title Cleaning Pipeline — `domain_title_cleaner.py`
Extracts clean brand names from messy domain URLs and product names from titles using rule-based matching.

- Handles prefixes: `shop.`, `store.`, `www.`, all ISO country codes
- Matches product names from titles against extracted brand names
- Pure Python, no API calls — ~1000 rows/second
- Key Skills: Regex, pandas, Unicode normalization

### 2. AI-Powered Data Cleaning with Gemini — `gemini_data_cleaner.py`
Uses Google Gemini to clean merchant names and extract person names from emails with confidence scoring.

- Removes legal suffixes (LLC, Ltd), website formats, slogans
- Email-based name extraction: High / Good / Unclear / Guess confidence levels
- Two modes: `GEN` (merchant names only) / `PIC` (merchant + person name)
- Auto-saves every 20 rows in case of interruption
- Key Skills: LLM API integration, prompt engineering, error handling

## Usage

```python
# Domain/Title cleaning — no setup needed
from domain_title_cleaner import clean_dataframe
import pandas as pd

df = pd.read_csv('data.csv')
df_clean = clean_dataframe(df)  # adds 'brand' and 'product_name' columns
```

```python
# AI cleaning — requires GEMINI_API_KEY in .env
from gemini_data_cleaner import process_file

process_file("data.csv", mode="PIC")  # outputs timestamped Excel file
```

## Setup

```bash
pip install -r requirements.txt
# Create data_cleaning/.env with: GEMINI_API_KEY=your_key_here
```

## Docs

- [DOMAIN_TITLE_CLEANER.md](DOMAIN_TITLE_CLEANER.md) — detailed usage, parameters, examples
- [GEMINI_DATA_CLEANER.md](GEMINI_DATA_CLEANER.md) — AI cleaner usage and modes
