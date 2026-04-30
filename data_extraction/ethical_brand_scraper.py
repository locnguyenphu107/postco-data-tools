"""
Ethical Fashion Brand Scraper
Scrapes brand information from structured directory websites using Playwright.

This module demonstrates:
1. Browser automation with Playwright (headless mode)
2. Dynamic HTML parsing and CSS selectors
3. Structured data extraction from directory sites
4. Robust error handling with per-item try-catch
5. Excel export with formatting

Use Case: Extract brand databases, competitive intelligence, directory aggregation
Real Example: ethicalfashion.net.au brand directory
"""

import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from datetime import datetime
import logging
from typing import List, Dict, Optional
import re
import os

# ──────────────────────────────────────────────
# Configuration & Logging
# ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScraperConfig:
    """Configuration for Playwright scraper"""
    HEADLESS = True  # Run browser in background
    TIMEOUT = 60000  # 60 seconds
    WAIT_TIMEOUT = 10000  # 10 seconds for selectors
    BROWSER_TYPE = "chromium"  # chromium, firefox, or webkit


# ──────────────────────────────────────────────
# Extraction Helpers
# ──────────────────────────────────────────────

def extract_clean_name(raw_text: str) -> str:
    """
    Clean brand name by removing parenthetical text.

    Example:
        extract_clean_name("Nike (Apparel)") → "Nike"
    """
    if not raw_text:
        return ""
    # Remove text in parentheses
    return re.sub(r"\s*\(.*?\)", "", raw_text).strip()


def parse_pipe_separated_fields(text: str) -> Dict[str, str]:
    """
    Parse pipe-separated text into structured fields.

    Expected format: "Brand Location | Description | Category1 | Category2"

    Returns:
        Dict with 'location' and 'description' keys

    Example:
        parse_pipe_separated_fields("Australia | Sustainable Fashion | Apparel")
        → {'location': 'Australia', 'description': 'Sustainable Fashion | Apparel'}
    """
    if not text:
        return {"location": "", "description": ""}

    parts = [part.strip() for part in text.split("|") if part.strip()]

    return {
        "location": parts[0] if len(parts) > 0 else "",
        "description": " | ".join(parts[1:]) if len(parts) > 1 else ""
    }


# ──────────────────────────────────────────────
# Main Scraper
# ──────────────────────────────────────────────

def scrape_brand_directory(
    url: str,
    container_selector: str = ".so-widget-sow-editor.so-widget-sow-editor-base",
    name_selector: str = ".widget-title",
    content_selector: str = ".siteorigin-widget-tinymce.textwidget",
    link_selector: str = "a"
) -> List[Dict]:
    """
    Scrape brand information from a directory website.

    This function:
    1. Launches a browser and navigates to the URL
    2. Waits for brand containers to load
    3. Extracts name, website, location, and description for each brand
    4. Handles errors gracefully (continues on individual item failures)
    5. Returns structured data as list of dictionaries

    Args:
        url: Website URL to scrape
        container_selector: CSS selector for brand containers
        name_selector: CSS selector for brand name within container
        content_selector: CSS selector for content (location + description)
        link_selector: CSS selector for website link within content

    Returns:
        List of dictionaries with keys:
        - name: Brand name
        - website: Website URL
        - location: Brand location
        - description: Brand description/categories
        - error: Error message if extraction failed

    Example:
        results = scrape_brand_directory(
            "https://www.ethicalfashion.net.au/brand-directory/"
        )
        df = pd.DataFrame(results)
        print(f"Scraped {len(results)} brands")
    """
    results = []
    successful = 0
    failed = 0

    logger.info(f"Starting scraper for: {url}")
    logger.info(f"Launching Playwright browser...")

    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=ScraperConfig.HEADLESS)
            context = browser.new_context()
            page = context.new_page()

            # Navigate to URL
            logger.info(f"Loading page...")
            page.goto(url, timeout=ScraperConfig.TIMEOUT)

            # Wait for content to load
            logger.info(f"Waiting for brand containers to load...")
            page.wait_for_selector(
                container_selector,
                timeout=ScraperConfig.WAIT_TIMEOUT
            )

            # Get all brand containers
            containers = page.query_selector_all(container_selector)
            total_containers = len(containers)
            logger.info(f"Found {total_containers} brand containers")

            if total_containers == 0:
                logger.warning("⚠️  No brand containers found. Check selectors.")
                return results

            # Extract data from each container
            for idx, container in enumerate(containers, start=1):
                try:
                    # Extract brand name
                    name_elem = container.query_selector(name_selector)
                    raw_name = name_elem.inner_text().strip() if name_elem else ""
                    brand_name = extract_clean_name(raw_name)

                    # Extract content (location + description)
                    content_elem = container.query_selector(content_selector)
                    full_text = content_elem.inner_text().strip() if content_elem else ""

                    # Extract website link
                    link_elem = content_elem.query_selector(link_selector) if content_elem else None
                    website = link_elem.get_attribute("href") if link_elem else ""

                    # Parse pipe-separated content
                    parsed = parse_pipe_separated_fields(full_text)

                    # Store result
                    result = {
                        "name": brand_name,
                        "website": website,
                        "location": parsed["location"],
                        "description": parsed["description"],
                        "error": None
                    }
                    results.append(result)

                    logger.info(f"[{idx}/{total_containers}] ✓ {brand_name}")
                    successful += 1

                except Exception as e:
                    # Log error but continue with next item
                    error_msg = str(e)[:100]
                    logger.warning(f"[{idx}/{total_containers}] ✗ Error: {error_msg}")

                    results.append({
                        "name": "",
                        "website": "",
                        "location": "",
                        "description": "",
                        "error": error_msg
                    })
                    failed += 1

            # Close browser
            context.close()
            browser.close()
            logger.info(f"Browser closed.")

    except PlaywrightTimeoutError as e:
        logger.error(f"Page load timeout: {e}")
        return results
    except Exception as e:
        logger.error(f"Scraper error: {e}")
        return results

    # Summary
    logger.info(f"\n{'='*50}")
    logger.info(f"Scraping complete!")
    logger.info(f"  Successful: {successful}")
    logger.info(f"  Failed: {failed}")
    logger.info(f"  Total: {successful + failed}")
    logger.info(f"{'='*50}\n")

    return results


# ──────────────────────────────────────────────
# Export Utilities
# ──────────────────────────────────────────────

def save_results(
    results: List[Dict],
    output_format: str = "excel",
    output_path: Optional[str] = None
) -> str:
    """
    Save scraping results to file.

    Args:
        results: List of result dictionaries from scrape_brand_directory()
        output_format: "excel" or "csv"
        output_path: Path to save (if None, auto-generates name)

    Returns:
        Path to saved file
    """
    df = pd.DataFrame(results)

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = "xlsx" if output_format == "excel" else "csv"
        output_path = f"brands_scraped_{timestamp}.{ext}"

    if output_format == "excel":
        df.to_excel(output_path, index=False)
        logger.info(f"✅ Excel file saved: {output_path}")
    else:
        df.to_csv(output_path, index=False)
        logger.info(f"✅ CSV file saved: {output_path}")

    return output_path


# ──────────────────────────────────────────────
# Pandas Integration
# ──────────────────────────────────────────────

def scrape_directory_to_dataframe(
    url: str,
    **kwargs
) -> pd.DataFrame:
    """
    Scrape directory website and return results as DataFrame.

    Args:
        url: Website URL to scrape
        **kwargs: Additional arguments for scrape_brand_directory()

    Returns:
        pandas DataFrame with scraped data
    """
    results = scrape_brand_directory(url, **kwargs)
    return pd.DataFrame(results)


# ──────────────────────────────────────────────
# CLI & Example Usage
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Brand Directory Scraper ===\n")

    # Example: Ethical Fashion Australia
    # NOTE: This is a real website example, but check robots.txt and terms of service first!
    example_url = "https://www.ethicalfashion.net.au/brand-directory/ethical-fashion-brand-directory-all-brands/"

    # NOTE: Uncomment below to run the scraper
    # print(f"Scraping: {example_url}\n")
    # results = scrape_brand_directory(example_url)
    #
    # df = pd.DataFrame(results)
    # print(f"\nResults Preview:")
    # print(df[['name', 'website', 'location']].head(10))
    #
    # save_path = save_results(results, output_format="excel")
    # print(f"\n✅ Saved to: {save_path}")

    print("To use this scraper:")
    print("  1. Import: from ethical_fashion_scraper import scrape_brand_directory")
    print("  2. Run: results = scrape_brand_directory(url)")
    print("  3. Save: save_results(results)")
    print("\nNote: Always check website's robots.txt and terms before scraping!")
