# Summary

Data engineering and automation projects from real-world work.

## Projects

| Folder | Script | Description |
|--------|--------|-------------|
| [data_cleaning/](data_cleaning/) | `domain_title_cleaner.py` | Extract brand names from domains and product names from titles |
| [data_cleaning/](data_cleaning/) | `gemini_data_cleaner.py` | AI-powered merchant and person name cleaning via Gemini |
| [data_extraction/](data_extraction/) | `ethical_brand_scraper.py` | Playwright-based brand directory scraper |
| [data_extraction/](data_extraction/) | `web_title_scraper.py` | Batch web title fetcher with retry logic |
| [postco_return_automation/](postco_return_automation/) | `return_app_identifier.py` | Streamlit app to identify return management software on stores |

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

For the Gemini cleaner, create `data_cleaning/.env`:
```
GEMINI_API_KEY=your_key_here
```
