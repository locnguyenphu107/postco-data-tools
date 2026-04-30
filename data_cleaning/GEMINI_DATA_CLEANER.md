# AI-Powered Data Cleaning with Google Gemini

Use large language models (LLMs) to intelligently clean merchant names and extract person names from email addresses.

## What It Does

### Mode 1: GEN (Generate Clean Merchant Names)
```
Input:  "saigonsneakers.com - affordable shoes online"
Output: "Saigon Sneakers"

Input:  "shop_electronics_LLC"
Output: "Shop Electronics"
```

### Mode 2: PIC (Person & Company Identification)
Cleans both merchant names AND extracts person names with confidence scoring:
```
Input:
  Name: "John Smith"
  Email: "j.smith@example.com"
  merchant_name: "shop.coolbrand.com - online retailer"

Output:
  Name: "Smith"
  merchant_name: "Cool Brand"
  confidence: "Good"
  reason: "First initial + Last name pattern"
```

## How It Works

### Merchant Cleaning (Uses Gemini API)
Smart removal of:
- Website formats (.com, www, http://, https://)
- Legal suffixes (LLC, Ltd, Inc, Co, TM)
- Slogans/descriptions (text after -, |, :)
- Auto-capitalizes to Title Case

### Person Name Extraction (Rule-Based)
Tries 7 rules in order of priority:
1. ✅ First name found in email → HIGH confidence
2. ✅ Last name found in email → HIGH confidence
3. ✅ Pattern: first_initial + last_name (jsmith) → GOOD confidence
4. ✅ Pattern: first_name + last_initial (johns) → GOOD confidence
5. ⚠️  Only last name matches → UNCLEAR confidence
6. ⚠️  Fallback to first name → UNCLEAR confidence
7. 🤔 Parse email local part as guess → GUESS confidence

**No API calls needed for name extraction** (rule-based only)

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get Gemini API Key
- Go to: https://aistudio.google.com/apikey
- Create free API key
- Create `.env` file in your working directory:
  ```
  GEMINI_API_KEY=your_api_key_here
  ```

### 3. Prepare Data
CSV or Excel file with these columns:
- `merchant_name` - Company/brand names (can be empty)
- `Name` - Person names (can be empty)
- `Email` - Email addresses (can be empty)

Example input:
```
Name,Email,merchant_name
John Smith,john.smith@example.com,saigonsneakers.com - shoes
Jane Doe,jane@company.com,
```

## Usage

### Command Line
```bash
python gemini_data_cleaner.py
# Then answer the prompts:
# - Input file path: /path/to/your/data.csv
# - Mode: PIC (or GEN for merchant names only)
# - Output directory: (press Enter to use input directory)
```

### Python Script
```python
from gemini_data_cleaner import process_file

# Full cleaning (merchant + person names)
output_file = process_file(
    input_path="data.csv",
    mode="PIC"
)

# Merchant names only
output_file = process_file(
    input_path="data.csv",
    mode="GEN"
)
```

## Output Files

1. **`{filename}_cleaned_{timestamp}.xlsx`** (Final result)
   - All rows processed
   - New columns added:
     - `old_Name`, `old_merchant_name` (original values)
     - `confidence` (High/Good/Unclear/Guess/Skip)
     - `reason` (explanation for each decision)

2. **`{filename}_partial.xlsx`** (Auto-saved every 20 rows)
   - Useful if processing interrupted
   - Can be used to verify progress

## Real Example

### Input Data
```csv
Name,Email,merchant_name
John Smith,j.smith@company.com,shop.coolbrand.com - awesome products
Sarah Johnson,sarah.johnson@mail.com,electronics-store-LLC
,contact@unknown.com,fashionwear.co.uk - premium clothing
```

### Processing (PIC mode)
```
[0] John Smith | j.smith@company.com → Smith (Good: First initial + Last name pattern)
    [merchant] shop.coolbrand.com - awesome products → Cool Brand
[1] Sarah Johnson | sarah.johnson@mail.com → Sarah (High: First name in email)
    [merchant] electronics-store-LLC → Electronics Store
[2]  | contact@unknown.com → (Skip: no name data)
    [merchant] fashionwear.co.uk - premium clothing → Fashion Wear

✅ Final file saved: data_cleaned_20250101_120000.xlsx
```

### Output Data
```csv
Name,Email,merchant_name,old_Name,old_merchant_name,confidence,reason
Smith,j.smith@company.com,Cool Brand,John Smith,shop.coolbrand.com...,Good,First initial + Last name...
Sarah,sarah.johnson@mail.com,Electronics Store,Sarah Johnson,electronics-store-LLC,High,First name in email
,,Fashion Wear,,fashionwear.co.uk...,Skip,no name data
```

## Confidence Levels Explained

| Level | Meaning | Example |
|-------|---------|---------|
| **High** | Very confident in extraction | john.doe@example.com → John/Doe |
| **Good** | Pattern-matched successfully | j.doe@example.com, johns@... |
| **Unclear** | Matched but ambiguous | Only last name found |
| **Guess** | Extracted from email creatively | jerry123@ex.com → Jerry |
| **Skip** | Not enough data to extract | Empty name + missing email |

## API Cost

- **Gemini API**: Free tier available (up to 60 requests/minute, 1,500/day)
- This tool makes **1 API call per merchant name** in your dataset
- Example: 1000 rows with merchant names = ~1000 API calls

## Tips & Tricks

### Performance
```python
# Process only rows with merchant names (faster)
df = df[df['merchant_name'].notna()]
output = process_file(...)
```

### Debugging
```python
# Check confidence distribution
df = pd.read_excel('data_cleaned_20250101_120000.xlsx')
print(df['confidence'].value_counts())
# Shows: High: 450, Good: 320, Unclear: 150, Guess: 75, Skip: 5
```

### Custom Workflows
```python
from gemini_data_cleaner import (
    clean_merchant_name_with_ai,
    extract_name_from_email_with_confidence,
    GeminiConfig
)

# Initialize Gemini once
model = GeminiConfig.init()

# Use individual functions
merchant = clean_merchant_name_with_ai("shop.brand.com - online", model)
name, conf, reason = extract_name_from_email_with_confidence("John Smith", "john.smith@example.com")
```

## Limitations

- **Email-only extraction**: Person name extraction requires at least an email
- **API dependency**: Merchant cleaning needs internet connection (Gemini API)
- **Rate limiting**: Free tier limited to 60 requests/minute
- **Name extraction**: Works best with standard email formats (john.smith, j.smith, johns patterns)

## Troubleshooting

### "GEMINI_API_KEY not set"
→ Create `.env` file with your API key

### "Timeout" errors
→ Increase timeout or reduce batch size

### "No Google generativeai module"
→ Run: `pip install google-generativeai`

## Next Steps

- Combine with `domain_title_cleaner.py` for multi-stage pipeline
- Add custom rules for your merchant naming patterns
- Use confidence scores to flag rows for manual review
