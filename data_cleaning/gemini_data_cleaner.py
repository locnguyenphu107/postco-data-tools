"""
AI-Powered Data Cleaning with Google Gemini
Cleans merchant names and personal names using large language models.

This module provides:
1. Merchant name cleaning: Remove suffixes (LLC, Ltd), website formats, slogans
2. Personal name normalization: Extract names from email addresses using rule-based logic
3. Two processing modes:
   - GEN: Clean merchant names only
   - PIC: Clean both merchant names AND person names with confidence scoring

Requirements:
    - google-generativeai
    - python-dotenv
    - pandas
    - openpyxl (for Excel export)
"""

import os
import re
import pandas as pd
from typing import Tuple, Optional
from datetime import datetime
from dotenv import load_dotenv

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

class GeminiConfig:
    """Configuration for Gemini API"""
    MODEL = "gemini-2.0-flash"
    TIMEOUT = 30

    @staticmethod
    def init():
        """Initialize Gemini API from .env credentials"""
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai not installed. "
                "Install with: pip install google-generativeai"
            )

        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "❌ GEMINI_API_KEY not found in .env file\n"
                "Please create a .env file with: GEMINI_API_KEY=your_key_here"
            )

        genai.configure(api_key=api_key)
        return genai.GenerativeModel(GeminiConfig.MODEL)


# ──────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────

def clean_merchant_name_with_ai(raw_name: str, model) -> str:
    """
    Use Gemini API to intelligently clean merchant names.

    Removes:
    - Website formats (.com, www, http, https)
    - Legal suffixes (LLC, Ltd, Co, TM, Inc)
    - Slogans or descriptions (after -, |, :)
    - Proper capitalization (title case)

    Args:
        raw_name: Uncleaned merchant name
        model: Initialized Gemini model instance

    Returns:
        Cleaned merchant name (or original if error)

    Example:
        clean_merchant_name_with_ai("saigonsneakers.com - affordable shoes", model)
        → "Saigon Sneakers"
    """
    if not isinstance(raw_name, str) or not raw_name.strip():
        return ""

    prompt = f"""You are cleaning brand names for a sales pipeline.

STRICT RULES:
- Remove website formats (.com, .org, www, http, https).
- Remove legal suffixes (LLC, Ltd, Co, TM, Inc, Corporation).
- Remove slogans/descriptions after -, |, :.
- Proper capitalization (Title Case).
- Output ONLY the cleaned brand name. No explanation, no sentences.

Example:
Input: "saigonsneakers.com - affordable shoes"
Output: Saigon Sneakers

Input: "{raw_name}"
Output:"""

    try:
        response = model.generate_content(prompt, request_options={"timeout": GeminiConfig.TIMEOUT})
        cleaned = response.text.strip().split("\n")[0].strip()
        return cleaned if cleaned else raw_name
    except Exception as e:
        print(f"⚠️ Gemini error for '{raw_name}': {e}")
        return raw_name


def normalize_name(text: str) -> str:
    """
    Simple text normalization: strip whitespace, title case.

    Args:
        text: Input text

    Returns:
        Normalized text
    """
    if not isinstance(text, str) or not text.strip():
        return ""
    return text.strip().title()


def extract_email_local_part(email: str) -> str:
    """
    Extract the part before @ in email address.

    Args:
        email: Email address

    Returns:
        Local part (lowercase)

    Example:
        extract_email_local_part("john.doe@example.com") → "john.doe"
    """
    if not isinstance(email, str) or "@" not in email:
        return ""
    return email.split("@")[0].lower()


def extract_name_from_email_with_confidence(
    name: str,
    email: str
) -> Tuple[str, str, str]:
    """
    Extract person's name from email address using pattern matching.

    Rules (in order of priority):
    1. First name appears in email local part → HIGH confidence
    2. Last name appears in email local part → HIGH confidence
    3. First initial + Last name pattern (jsmith) → GOOD confidence
    4. First name + Last initial pattern (johns) → GOOD confidence
    5. Only last name match → UNCLEAR confidence
    6. Fallback to first name if available → UNCLEAR confidence
    7. Parse email local part → GUESS confidence

    Args:
        name: Person's name (e.g., "John Smith")
        email: Email address (e.g., "john.smith@example.com")

    Returns:
        Tuple[extracted_name, confidence_level, reason]

    Example:
        extract_name_from_email_with_confidence("John Smith", "john.smith@example.com")
        → ("John", "High", "First name in email")
    """
    if not name and not email:
        return "", "Skip", "Both name and email missing"

    # Parse the name
    parts = name.split()
    first = parts[0].lower() if len(parts) >= 1 else ""
    last = parts[-1].lower() if len(parts) >= 2 else ""

    email_local = extract_email_local_part(email)

    # Rule 1: First name in email
    if first and first in email_local:
        return normalize_name(first), "High", "First name in email"

    # Rule 2: Last name in email
    if last and last in email_local:
        return normalize_name(last), "High", "Last name in email"

    # Rule 3: First initial + Last name (jsmith)
    if first and last and email_local.startswith(first[0] + last):
        return normalize_name(first), "Good", "First initial + Last name pattern"

    # Rule 4: First name + Last initial (johns)
    if first and last and email_local.startswith(first + last[0]):
        return normalize_name(first), "Good", "First name + Last initial pattern"

    # Rule 5: Last name match
    if last and last in email_local:
        return normalize_name(last), "Unclear", "Only last name matched"

    # Rule 6: Fallback to first name
    if first:
        return normalize_name(first), "Unclear", "No email pattern matched, using first name"

    # Rule 7: Extract from email if name unavailable
    if email_local:
        guess = re.split(r"[._-]", email_local)[0]
        return normalize_name(guess), "Guess", "Extracted from email local part"

    return "", "Skip", "Could not extract any data"


# ──────────────────────────────────────────────
# Main Processing
# ──────────────────────────────────────────────

def process_file(
    input_path: str,
    mode: str = "PIC",
    output_dir: Optional[str] = None,
    model = None
) -> str:
    """
    Process CSV/Excel file: clean names and/or merchant data.

    Modes:
    - "GEN": Generate clean merchant_name from raw data
    - "PIC": Clean BOTH merchant_name AND person Name with confidence tracking

    Output files:
    - {filename}_cleaned_{timestamp}.xlsx: Final cleaned data
    - {filename}_partial.xlsx: Auto-saved every 20 rows (in case of interruption)

    Args:
        input_path: Path to CSV/Excel file
        mode: "GEN" or "PIC"
        output_dir: Where to save output (if None, uses input directory)
        model: Gemini model instance (if None, initializes one)

    Returns:
        Path to output file
    """
    # Initialize Gemini if not provided
    if model is None:
        model = GeminiConfig.init()

    # Validate mode
    if mode.upper() not in ["GEN", "PIC"]:
        raise ValueError("mode must be 'GEN' or 'PIC'")

    mode = mode.upper()

    # Load file
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")

    ext = os.path.splitext(input_path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(input_path)
    elif ext in [".xlsx", ".xls"]:
        df = pd.read_excel(input_path)
    else:
        raise ValueError("❌ File must be CSV or Excel (.xlsx, .xls)")

    # Ensure required columns exist
    for col in ["merchant_name", "Name", "Email"]:
        if col not in df.columns:
            df[col] = ""

    # Add tracking columns
    df["old_Name"] = df["Name"]
    df["old_merchant_name"] = df["merchant_name"]
    df["confidence"] = ""
    df["reason"] = ""

    # Setup output paths
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = output_dir or os.path.dirname(input_path)
    base_name = os.path.splitext(os.path.basename(input_path))[0]

    final_path = os.path.join(output_dir, f"{base_name}_cleaned_{timestamp}.xlsx")
    partial_path = os.path.join(output_dir, f"{base_name}_partial.xlsx")

    print(f"\n📋 Processing {len(df)} rows in {mode} mode...")
    print(f"Output: {final_path}\n")

    try:
        for idx, row in df.iterrows():
            name = str(row["Name"]) if pd.notna(row["Name"]) else ""
            email = str(row["Email"]) if pd.notna(row["Email"]) else ""
            merchant = str(row["merchant_name"]) if pd.notna(row["merchant_name"]) else ""

            if mode == "GEN":
                # Generate clean merchant name only
                if not merchant and not email:
                    continue

                cleaned_merchant = clean_merchant_name_with_ai(merchant, model)
                df.at[idx, "merchant_name"] = cleaned_merchant
                print(f"[{idx}] {merchant} → {cleaned_merchant}")

            elif mode == "PIC":
                # Clean both merchant and person name
                if not name and not email and not merchant:
                    continue

                # Clean merchant name
                cleaned_merchant = clean_merchant_name_with_ai(merchant, model)
                df.at[idx, "merchant_name"] = cleaned_merchant

                # Extract person name with confidence
                extracted_name, confidence, reason = extract_name_from_email_with_confidence(name, email)
                df.at[idx, "Name"] = extracted_name
                df.at[idx, "confidence"] = confidence
                df.at[idx, "reason"] = reason

                print(f"[{idx}] {name} | {email} → {extracted_name} ({confidence}: {reason})")

            # Auto-save every 20 rows
            if idx % 20 == 0 and idx > 0:
                df.to_excel(partial_path, index=False)
                print(f"  💾 Partial save at row {idx}\n")

    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user. Saving partial results...")
        df.to_excel(partial_path, index=False)
        print(f"Partial file saved: {partial_path}")
        return partial_path

    except Exception as e:
        print(f"\n⚠️  Error: {e}")
        df.to_excel(partial_path, index=False)
        print(f"Partial file saved: {partial_path}")
        return partial_path

    finally:
        # Always save the final file
        df.to_excel(final_path, index=False)
        print(f"\n✅ Final file saved: {final_path}")

    return final_path


# ──────────────────────────────────────────────
# CLI Interface
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("=== AI-Powered Data Cleaning with Gemini ===\n")

    input_path = input("Input file path (CSV or Excel): ").strip()
    mode = input("Mode (GEN for merchant names only, PIC for full cleaning) [default: PIC]: ").strip().upper()
    output_dir = input("Output directory (press Enter to use input directory): ").strip()

    if not mode or mode not in ["GEN", "PIC"]:
        mode = "PIC"

    try:
        output_file = process_file(
            input_path,
            mode=mode,
            output_dir=output_dir if output_dir else None
        )
        print(f"\n🎉 Success! Output: {output_file}")
    except Exception as e:
        print(f"\n❌ Failed: {e}")
