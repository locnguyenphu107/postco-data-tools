# Data Extraction Projects

Two web scraping tools covering browser automation and HTTP-based extraction approaches.

## Projects

### 1. Ethical Brand Directory Scraper — `ethical_brand_scraper.py`
Scrapes brand directories using Playwright (headless browser automation) for dynamically-loaded content.

- Targets CSS selectors for brand name, website, location, and description
- Per-item error recovery — logs failures and continues to next brand
- Exports to Excel or CSV with timestamps
- Key Skills: Playwright, headless browser, CSS selectors, structured data extraction

### 2. Web Title Scraper — `web_title_scraper.py`
Batch-fetches `<title>` tags from a list of domain URLs using HTTP requests.

- Auto-adds `https://` protocol if missing
- Configurable retry logic with delay between attempts
- Handles redirects, timeouts, and HTTP errors gracefully
- DataFrame integration — drop into any CSV pipeline
- Key Skills: requests, BeautifulSoup, retry logic, pandas

## Usage

```python
# Scrape a brand directory (Playwright)
from ethical_brand_scraper import scrape_brand_directory, save_results

results = scrape_brand_directory("https://example.com/brand-directory/")
save_results(results, output_format="excel")

# Or get a DataFrame directly
from ethical_brand_scraper import scrape_directory_to_dataframe
df = scrape_directory_to_dataframe("https://example.com/brand-directory/")
```

```python
# Scrape page titles (requests)
from web_title_scraper import scrape_titles, save_results

results = scrape_titles(['example.com', 'google.com', 'github.com'])
save_results(results)  # saves timestamped CSV

# Or from a DataFrame
from web_title_scraper import scrape_dataframe
import pandas as pd

df = pd.read_csv('domains.csv')
df_with_titles = scrape_dataframe(df, domain_column='Domain')
```

## Setup

```bash
pip install -r requirements.txt
playwright install chromium  # for ethical_brand_scraper.py
```

> Note: Always check a website's `robots.txt` and terms of service before scraping.
