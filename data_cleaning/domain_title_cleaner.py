"""
Domain-Based Title Cleaning Pipeline
Extracts and normalizes brand names from domains and product titles.

This module provides tools to:
1. Extract brand names from domain URLs (removes common prefixes like 'shop', 'store', country codes)
2. Extract product/service names from titles using brand matching
3. Normalize extracted names and handle special characters

Use Case: E-commerce data cleaning, removing domain boilerplate to get clean brand/product names
"""

import re
import pandas as pd
from datetime import datetime
import unicodedata
from typing import List, Tuple


# ──────────────────────────────────────────────
# Configuration: Common Prefixes to Skip
# ──────────────────────────────────────────────
COMMON_PREFIXES = [
    # Country Codes
    "AF", "AL", "DZ", "AD", "AO", "AG", "AR", "AM", "AU", "AT", "AZ", "BS", "BH",
    "BD", "BB", "BY", "BE", "BZ", "BJ", "BT", "BO", "BA", "BW", "BR", "BN", "BG",
    "BF", "BI", "CV", "KH", "CM", "CA", "CF", "TD", "CL", "CN", "CO", "KM", "CG",
    "CR", "HR", "CU", "CY", "CZ", "DK", "DJ", "DM", "DO", "EC", "EG", "SV", "GQ",
    "ER", "EE", "SZ", "ET", "FJ", "FI", "FR", "GA", "GM", "GE", "DE", "GH", "GR",
    "GD", "GT", "GN", "GW", "GY", "HT", "HN", "HU", "IS", "IN", "ID", "IR", "IQ",
    "IE", "IL", "IT", "CI", "JM", "JP", "JO", "KZ", "KE", "KI", "KP", "KR", "KW",
    "KG", "LA", "LV", "LB", "LS", "LR", "LY", "LI", "LT", "LU", "MG", "MW", "MY",
    "MV", "ML", "MT", "MH", "MR", "MU", "MX", "FM", "MD", "MC", "MN", "ME", "MA",
    "MZ", "MM", "NA", "NR", "NP", "NL", "NZ", "NI", "NE", "NG", "MK", "NO", "OM",
    "PK", "PW", "PA", "PG", "PY", "PE", "PH", "PL", "PT", "QA", "RO", "RU", "RW",
    "KN", "LC", "VC", "WS", "SM", "ST", "SA", "SN", "RS", "SC", "SL", "SG", "SK",
    "SI", "SB", "SO", "ZA", "SS", "ES", "LK", "SD", "SR", "SE", "CH", "SY", "TW",
    "TJ", "TZ", "TH", "TL", "TG", "TO", "TT", "TN", "TR", "TM", "TV", "UG", "UA",
    "AE", "GB", "US", "UY", "UZ", "VU", "VA", "VE", "VN", "YE", "ZM", "ZW",

    # Business/Commerce
    "shop", "store", "outlet", "market", "mart", "boutique", "bazaar", "emporium",
    "trade", "warehouse", "supplier", "merchant", "retail",

    # Online/Service
    "checkout", "online", "order", "ecommerce", "portal", "cart", "buy", "sell",

    # Industry Categories
    "fashion", "beauty", "sports", "electronics", "furniture", "home", "tools",
    "appliances", "toys", "grocery", "health", "fitness", "books", "games", "gear",
    "clothing", "jewelry",

    # Community/Interest
    "club", "group", "hub", "community", "society", "team", "circle",

    # Promotions/Discounts
    "deal", "discount", "bargain", "promo", "offer", "sale", "special",

    # Location-Based
    "global", "international", "world", "local", "city", "region", "zone",

    # Generic Keywords
    "pro", "plus", "prime", "max", "best", "new", "next", "elite", "lux",
    "value", "classic", "direct", "express",

    # Web
    "www", "uk", "eu", "asia", "shopify"
]

# Normalize to lowercase for comparison
PREFIXES_LOWER = [p.lower() for p in COMMON_PREFIXES]


# ──────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────

def remove_accents(text: str) -> str:
    """
    Remove accent marks from text.

    Example:
        remove_accents("Café") → "Cafe"
    """
    if not isinstance(text, str):
        return ""

    return ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if unicodedata.category(c) != 'Mn'
    )


def extract_brand_from_domain(domains: List[str], separator: str = ".") -> List[str]:
    """
    Extract brand names from domain URLs.

    Strategy:
    - Remove protocol (http://, https://)
    - Split by separator (usually '.')
    - If first part is common prefix (shop, store, www, country code), use second part
    - Otherwise use first part

    Args:
        domains: List of domain URLs
        separator: Character to split by (default: '.')

    Returns:
        List of extracted brand names

    Example:
        extract_brand_from_domain(['shop.nike.com', 'adidas.com'])
        → ['Nike', 'Adidas']
    """
    brand_names = []

    for domain in domains:
        # Clean protocol
        domain = domain.replace("https://", "").replace("http://", "")

        # Split by separator
        parts = domain.split(separator)

        if len(parts) < 2:
            # Single part domain (rare), use as-is
            brand_names.append(parts[0].lower())
        else:
            first_part = parts[0].lower()
            second_part = parts[1].lower()

            # If first part is a known prefix, use second part
            if first_part in PREFIXES_LOWER:
                brand_names.append(second_part)
            else:
                brand_names.append(first_part)

    return brand_names


def extract_name_from_title(
    title_column: List[str],
    brand_names: List[str]
) -> List[str]:
    """
    Extract product/service names from titles by matching against brand names.

    Process:
    1. Clean title (remove #numbers, fix quote characters)
    2. Split title into words
    3. Find words that match the brand name parts
    4. Return the word with highest match count (tie-breaker: shortest length)

    Args:
        title_column: List of titles
        brand_names: List of brand names to match against

    Returns:
        List of extracted names (empty string if no match found)

    Example:
        extract_name_from_title(
            ["Nike Air Max Running Shoe", "Adidas Ultraboost"],
            ["nike", "adidas"]
        ) → ["Nike Air Max", "Adidas Ultraboost"]
    """
    extracted_names = []

    for title, brand_name in zip(title_column, brand_names):
        matched_name = None

        # Ensure title is string
        title = str(title) if title else ""
        if not title:
            extracted_names.append("")
            continue

        # Clean title
        title = title.replace("'", "'")  # Fix curly quotes
        title = re.sub(r"#\d+", "", title)  # Remove patterns like "#1"

        # Split by special characters (keep alphanumeric, dots, apostrophes, ampersands)
        words = re.split(r"[^\w.'&+\s]", title)

        # Normalize brand name
        brand_normalized = remove_accents(brand_name).lower()

        word_scores = []

        # Score each word based on matches with brand
        for word in words:
            original_word = word.strip()
            if not original_word:
                continue

            normalized_word = remove_accents(original_word).lower()

            # Special case: if word contains a dot and matches brand, use full domain
            if '.' in original_word and brand_normalized in normalized_word:
                matched_name = original_word
                break

            # Count how many parts of brand appear in this word
            match_count = 0

            # Split word by special chars and check each part
            sub_words = re.split(r"[^\w]", normalized_word)
            sub_words = [w for w in sub_words if w]  # Remove empty strings

            for sub_word in sub_words:
                if sub_word in brand_normalized:
                    match_count += 1

            if match_count > 0:
                word_scores.append((original_word, match_count))

        # Select best match (highest count, then shortest length)
        if not matched_name and word_scores:
            best_match = max(
                word_scores,
                key=lambda x: (x[1], -len(x[0]))  # Sort by count DESC, length ASC
            )
            matched_name = best_match[0]

        extracted_names.append(matched_name if matched_name else "")

    return extracted_names


# ──────────────────────────────────────────────
# Main Processor
# ──────────────────────────────────────────────

def clean_dataframe(
    df: pd.DataFrame,
    domain_column: str = "Domain",
    title_column: str = "Title",
    output_columns: Tuple[str, str] = ("brand", "product_name")
) -> pd.DataFrame:
    """
    Process entire DataFrame: extract brand from domain, then name from title.

    Args:
        df: Input DataFrame
        domain_column: Name of column containing domains
        title_column: Name of column containing titles
        output_columns: Names for output columns (brand, product_name)

    Returns:
        DataFrame with new columns added

    Example:
        df = pd.read_csv('data.csv')
        df_clean = clean_dataframe(df)
        print(df_clean[['brand', 'product_name']])
    """
    df = df.copy()

    # Validate input columns exist
    if domain_column not in df.columns or title_column not in df.columns:
        raise ValueError(f"Missing required columns: {domain_column}, {title_column}")

    # Extract brand names
    df[output_columns[0]] = extract_brand_from_domain(df[domain_column].tolist())

    # Extract product names
    df[output_columns[1]] = extract_name_from_title(
        df[title_column].tolist(),
        df[output_columns[0]].tolist()
    )

    return df


if __name__ == "__main__":
    # Example usage
    sample_data = {
        "Domain": ["shop.nike.com", "adidas.com", "store.puma.de"],
        "Title": ["Nike Air Max Running Shoe Professional", "Adidas Ultraboost Pro Edition", "Puma RS-X Sneaker"]
    }

    df = pd.DataFrame(sample_data)
    print("Input:")
    print(df)
    print("\n" + "="*50 + "\n")

    result = clean_dataframe(df)
    print("Output:")
    print(result[["Domain", "Title", "brand", "product_name"]])
