"""
Simple HTTP-Based Web Title Scraper
Fetches website titles from a list of domain URLs.

This module provides:
1. Batch fetching of website titles from domain URLs
2. Automatic protocol handling (adds https:// if missing)
3. Robust error handling with retry logic
4. Progress tracking and logging
5. CSV export of results

Use Case: Build datasets of website titles for competitive analysis, SEO research, or data enrichment
"""

import requests
import pandas as pd
from datetime import datetime
import logging
from typing import List, Dict
from urllib.parse import urlparse
import time

# ──────────────────────────────────────────────
# Configuration & Logging
# ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Scraping configuration
class ScraperConfig:
    """Configuration for web scraper"""
    REQUEST_TIMEOUT = 10  # seconds
    RETRY_ATTEMPTS = 2
    RETRY_DELAY = 1  # seconds
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


# ──────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────

def normalize_url(domain: str) -> str:
    """
    Ensure URL has protocol prefix (https://).

    Args:
        domain: URL or domain name

    Returns:
        URL with https:// prefix

    Example:
        normalize_url("example.com") → "https://example.com"
        normalize_url("https://example.com") → "https://example.com"
    """
    if not domain:
        return ""

    domain = domain.strip()

    # Already has protocol
    if domain.startswith(("http://", "https://")):
        return domain

    # Add https by default
    return f"https://{domain}"


def fetch_page_title(url: str) -> str:
    """
    Fetch and extract the <title> tag from a webpage.

    Args:
        url: Full URL with protocol

    Returns:
        Page title (cleaned), or error message if failed

    Example:
        fetch_page_title("https://example.com") → "Example - Welcome to our site"
    """
    try:
        # Send request with timeout
        response = requests.get(
            url,
            timeout=ScraperConfig.REQUEST_TIMEOUT,
            headers={"User-Agent": ScraperConfig.USER_AGENT},
            allow_redirects=True
        )

        # Check for HTTP errors
        response.raise_for_status()

        # Extract title from HTML
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            # Clean: strip whitespace and normalize spaces
            title = title_tag.string.strip()
            title = " ".join(title.split())  # Remove excess spaces
            return title
        else:
            return "no title found"

    except requests.exceptions.Timeout:
        return "timeout error"
    except requests.exceptions.HTTPError as e:
        return f"http error {response.status_code}"
    except requests.exceptions.ConnectionError:
        return "connection error"
    except Exception as e:
        return f"error: {str(e)[:50]}"  # Truncate long errors


# ──────────────────────────────────────────────
# Main Scraper
# ──────────────────────────────────────────────

def scrape_titles(
    domains: List[str],
    max_retries: int = ScraperConfig.RETRY_ATTEMPTS
) -> List[Dict]:
    """
    Scrape titles from a list of domains with retry logic.

    Args:
        domains: List of domain URLs or domain names
        max_retries: Number of retry attempts per domain

    Returns:
        List of dictionaries with:
        - domain: Original domain input
        - url: Normalized URL (with protocol)
        - title: Extracted page title
        - status: Success/error status

    Example:
        results = scrape_titles(['example.com', 'google.com'])
        print(results)
        # [
        #   {'domain': 'example.com', 'url': 'https://example.com', 'title': 'Example Domain', 'status': 'success'},
        #   {'domain': 'google.com', 'url': 'https://google.com', 'title': 'Google', 'status': 'success'}
        # ]
    """
    results = []
    total = len(domains)

    logger.info(f"Starting to scrape {total} domains...")

    for index, domain in enumerate(domains, start=1):
        # Normalize the URL
        url = normalize_url(domain)

        if not url:
            logger.warning(f"[{index}/{total}] Skipped (empty domain)")
            results.append({
                "domain": domain,
                "url": "",
                "title": "",
                "status": "skipped - empty domain"
            })
            continue

        logger.info(f"[{index}/{total}] Processing: {domain}")

        # Try fetching with retries
        title = None
        for attempt in range(max_retries + 1):
            title = fetch_page_title(url)

            # Check if successful (doesn't contain "error")
            if "error" not in title.lower() and title != "timeout error" and title != "connection error":
                break

            if attempt < max_retries:
                logger.warning(f"  Attempt {attempt + 1} failed: {title}. Retrying...")
                time.sleep(ScraperConfig.RETRY_DELAY)

        # Determine status
        status = "success" if not any(x in title.lower() for x in ["error", "timeout", "connection"]) else "failed"

        result = {
            "domain": domain,
            "url": url,
            "title": title,
            "status": status
        }
        results.append(result)

        # Show progress
        remaining = total - index
        if remaining > 0:
            logger.info(f"  → {title}")
            logger.info(f"  Remaining: {remaining}\n")

    logger.info(f"\n✅ Scraping complete! Processed {total} domains.")
    return results


# ──────────────────────────────────────────────
# Pandas Integration
# ──────────────────────────────────────────────

def scrape_dataframe(
    df: pd.DataFrame,
    domain_column: str = "domain"
) -> pd.DataFrame:
    """
    Scrape titles for domains in a DataFrame.

    Args:
        df: Input DataFrame with domains
        domain_column: Name of column containing domains

    Returns:
        DataFrame with new columns added:
        - url: Normalized URL
        - title: Extracted page title
        - status: Success/error status

    Example:
        df = pd.read_csv('domains.csv')
        df_scraped = scrape_dataframe(df, domain_column='Domain')
        df_scraped.to_csv('results.csv', index=False)
    """
    if domain_column not in df.columns:
        raise ValueError(f"Column '{domain_column}' not found in DataFrame")

    domains = df[domain_column].tolist()
    results = scrape_titles(domains)

    result_df = pd.DataFrame(results)
    result_df = result_df.rename(columns={"domain": domain_column})

    # Merge with original DataFrame
    output_df = pd.concat([df, result_df[[column for column in result_df.columns if column != domain_column]]], axis=1)

    return output_df


# ──────────────────────────────────────────────
# Export Utilities
# ──────────────────────────────────────────────

def save_results(
    results: List[Dict],
    output_path: str = None
) -> str:
    """
    Save scraping results to CSV file.

    Args:
        results: List of result dictionaries from scrape_titles()
        output_path: Path to save (if None, auto-generates name)

    Returns:
        Path to saved file
    """
    df = pd.DataFrame(results)

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"web_titles_scraped_{timestamp}.csv"

    df.to_csv(output_path, index=False)
    logger.info(f"Results saved to: {output_path}")

    return output_path


# ──────────────────────────────────────────────
# CLI Interface
# ──────────────────────────────────────────────

if __name__ == "__main__":
    # Example 1: Scrape from a list of domains
    print("=== Web Title Scraper ===\n")

    sample_domains = [
        "example.com",
        "google.com",
        "github.com"
    ]

    print("Example: Scraping sample domains...")
    results = scrape_titles(sample_domains)

    # Display results
    df = pd.DataFrame(results)
    print("\nResults:")
    print(df.to_string())

    # Save results
    output_file = save_results(results)
    print(f"\n✅ Saved to: {output_file}")

    # Example 2: Scrape from CSV file
    print("\n" + "="*50)
    print("\nTo scrape from your own CSV file:")
    print("  1. Prepare a CSV with a 'domain' column")
    print("  2. Run: df = pd.read_csv('your_file.csv')")
    print("  3. Run: results_df = scrape_dataframe(df)")
    print("  4. Run: results_df.to_csv('output.csv')")
