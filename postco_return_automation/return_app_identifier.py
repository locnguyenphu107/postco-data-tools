"""
Return App Identifier - Streamlit Application
Identifies return management applications installed on e-commerce stores.

This Streamlit application:
1. Accepts uploaded data with installed apps and technologies
2. Compares against a return app reference list
3. Identifies which stores use return management solutions
4. Generates reports with metrics and downloads

Features:
- File upload (CSV/Excel)
- Custom or default return app reference list
- Duplicate handling (keeps highest-ranked store per domain)
- Multiple return app detection
- Excel export with multiple sheets

Use Case: Competitive intelligence, market research, sales targeting
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
from typing import Tuple, Optional
from datetime import datetime
import logging

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default list of return management applications
DEFAULT_RETURN_APPS = {
    'Competitor': [
        'AfterShip Returns & Exchanges', 'Return Prime:Return & Exchange', 'ReturnGO Returns & Exchanges',
        'Happy Returns, a UPS Company', 'Sorted Returns Center', 'Swap Shipping & Returns',
        'ZigZag Returns & Exchanges', 'Narvar Return and Exchange', 'Refundid: Returns Portal',
        'Return Rabbit', 'Parcel Panel Returns &Exchange', 'Order Returns | easyReturns',
        'Baback - Exchanges & Returns', 'EcoReturns- AI Powered Returns', 'Yanet: Returns and Exchanges',
        'Rich Returns & Exchanges', 'ReturnZap Returns & Exchanges', 'Bold Returns',
        'Easy Returns Management System', 'Atomic Returns', 'Frate Returns & Recommerce',
        'Zon Customer Accounts & Return', 'Quick Returns and Exchanges', 'Keepoala: Returns & rewards',
        'COS Order Returns Manager', 'Optoro Returns & Exchanges', 'Navidium Returns & Exchanges',
        'BOXO Return', 'WeSupply Returns & Exchanges', 'IF Returns (not on storeleads)',
        'ReturnLogic', 'Ready Returns'
    ],
    'RC': [
        'AfterShip', 'Return Prime', 'ReturnGO', 'Happy Returns', 'Sorted', 'Swap',
        'ZigZag', 'Narvar', 'Refundid', 'Return Rabbit', 'Parcel Panel', 'easyReturns',
        'Baback', 'EcoReturns', 'Yanet', 'Rich', 'ReturnZap', 'Bold Returns',
        'Easy Returns', 'Atomic Returns', 'Frate', 'Zon', 'QuickReturns', 'Keepoala',
        'COS Order Returns Manager', 'Optoro', 'Navidium', 'BOXO Return',
        'WeSupply', 'IF Returns', 'ReturnLogic', 'Ready Returns'
    ]
}

# Required columns in input data
REQUIRED_MAIN_COLUMNS = ['domain', 'installed_apps_names', 'technologies', 'platform_rank', 'estimated_yearly_sales']
REQUIRED_APP_COLUMNS = ['Competitor', 'RC']


# ──────────────────────────────────────────────
# Core Processing Functions
# ──────────────────────────────────────────────

def preprocess_main_data(df: pd.DataFrame) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Preprocess main dataset: remove duplicates, merge app columns, handle NaN.

    Args:
        df: Input DataFrame with store data

    Returns:
        Tuple[processed_df, error_message]
        - processed_df is None if error
        - error_message is None if success
    """
    try:
        df = df.copy()

        # Sort by platform rank and sales (highest first)
        df = df.sort_values(
            by=['platform_rank', 'estimated_yearly_sales'],
            ascending=[False, False]
        )

        # Remove duplicates (keep first = highest ranked)
        df = df.drop_duplicates(subset=['domain'], keep='first')

        # Fill NaN values
        df['installed_apps_names'] = df['installed_apps_names'].fillna('')
        df['technologies'] = df['technologies'].fillna('')

        # Merge app columns into single column for matching
        df['all_apps'] = df['installed_apps_names'] + ':' + df['technologies']

        logger.info(f"Preprocessed {len(df)} unique domains")
        return df, None

    except KeyError as e:
        error_msg = f"Missing required column: {e}. Expected columns: {REQUIRED_MAIN_COLUMNS}"
        logger.error(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = f"Preprocessing error: {str(e)}"
        logger.error(error_msg)
        return None, error_msg


def preprocess_app_reference(df: pd.DataFrame) -> Tuple[Optional[dict], Optional[str]]:
    """
    Preprocess return app reference data: create mapping dictionary.

    Args:
        df: DataFrame with Competitor and RC columns

    Returns:
        Tuple[app_mapping, error_message]
        - app_mapping: Dict[full_name] → short_code
        - error_message: None if success
    """
    try:
        # Normalize competitor names (lowercase, stripped)
        df = df.copy()
        df['Competitor'] = df['Competitor'].str.lower().str.strip()

        # Create mapping from full name to short code
        app_mapping = dict(zip(df['Competitor'], df['RC']))

        logger.info(f"Loaded {len(app_mapping)} return apps in reference list")
        return app_mapping, None

    except KeyError as e:
        error_msg = f"Missing required column: {e}. Expected: {REQUIRED_APP_COLUMNS}"
        logger.error(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = f"App reference error: {str(e)}"
        logger.error(error_msg)
        return None, error_msg


def find_return_apps(app_string: str, app_mapping: dict) -> Tuple[int, str]:
    """
    Find which return apps are present in a store's app string.

    Args:
        app_string: String like "app1:app2:app3" (colon-separated)
        app_mapping: Dict mapping app names to short codes

    Returns:
        Tuple[count, names]
        - count: Number of return apps found
        - names: Comma-separated short codes
    """
    if not isinstance(app_string, str) or not app_string.strip():
        return 0, ''

    # Split by colon and normalize
    apps_list = [
        app.strip().lower()
        for app in app_string.split(':')
        if app.strip()
    ]

    # Find matches in our reference list
    found_apps = [
        app_mapping[app]
        for app in apps_list
        if app in app_mapping
    ]

    return len(found_apps), ', '.join(found_apps)


def process_return_apps(
    df_main: pd.DataFrame,
    df_app: pd.DataFrame
) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[str]]:
    """
    Main processing pipeline: identify return apps in dataset.

    Args:
        df_main: Main dataset with store data
        df_app: Reference dataset with return apps

    Returns:
        Tuple[df_with_returns, df_multiple_returns, error_message]
    """
    # Preprocess main data
    df, error = preprocess_main_data(df_main)
    if error:
        return None, None, error

    # Preprocess app reference
    app_mapping, error = preprocess_app_reference(df_app)
    if error:
        return None, None, error

    # Find return apps for each domain
    logger.info("Identifying return apps...")
    df[['return_app_count', 'return_app_names']] = df['all_apps'].apply(
        lambda x: pd.Series(find_return_apps(x, app_mapping))
    )

    # Create output dataframes
    df_with_returns = df[df['return_app_count'] > 0].copy()
    df_multiple_returns = df[df['return_app_count'] > 1].copy()

    logger.info(f"Found {len(df_with_returns)} brands with return apps")
    logger.info(f"Found {len(df_multiple_returns)} brands with multiple return apps")

    return df_with_returns, df_multiple_returns, None


# ──────────────────────────────────────────────
# Export Utilities
# ──────────────────────────────────────────────

def create_excel_download(
    df_with_returns: pd.DataFrame,
    df_multiple_returns: pd.DataFrame,
    total_brands: int = 0
) -> io.BytesIO:
    """
    Create downloadable Excel file with multiple sheets.

    Args:
        df_with_returns: Brands with at least one return app
        df_multiple_returns: Brands with multiple return apps

    Returns:
        BytesIO object for Streamlit download
    """
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: All brands with return apps
        df_with_returns.to_excel(
            writer,
            sheet_name='Brands With Return App',
            index=False
        )

        # Sheet 2: Brands with multiple return apps
        df_multiple_returns.to_excel(
            writer,
            sheet_name='Brands With >1 Return App',
            index=False
        )

        # Sheet 3: Summary stats
        total = total_brands or len(df_with_returns)
        summary_df = pd.DataFrame({
            'Metric': [
                'Total Brands Analyzed',
                'Brands with Return Apps',
                'Brands with Multiple Apps',
                'Return App Detection Rate'
            ],
            'Value': [
                total,
                len(df_with_returns),
                len(df_multiple_returns),
                f"{len(df_with_returns)/total*100:.1f}%" if total > 0 else "0%"
            ]
        })
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

    output.seek(0)
    return output


# ──────────────────────────────────────────────
# Streamlit UI
# ──────────────────────────────────────────────

def main():
    """Main Streamlit application"""

    # Page configuration
    st.set_page_config(
        page_title="Return App Identifier",
        layout="wide",
        page_icon="🛍️",
        initial_sidebar_state="expanded"
    )

    # Title and description
    st.title("🛍️ Return App Identifier")
    st.markdown("""
    Upload your e-commerce dataset and identify which stores use return management solutions.

    **What it does:**
    - Analyzes installed apps and technologies
    - Matches against 30+ known return management platforms
    - Identifies single and multiple return app usage
    - Exports detailed analysis reports
    """)

    st.divider()

    # ──────────────────────────────────────────
    # Section 1: Reference Data Display
    # ──────────────────────────────────────────

    st.subheader("📋 Return App Reference List")
    st.markdown("These apps are used for identification. Upload your own list to customize.")

    default_df = pd.DataFrame(DEFAULT_RETURN_APPS)
    st.dataframe(default_df, height=300, use_container_width=True)

    st.divider()

    # ──────────────────────────────────────────
    # Section 2: File Uploads
    # ──────────────────────────────────────────

    st.subheader("📁 Upload Your Data")

    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.info("**Required columns:** domain, installed_apps_names, technologies, platform_rank, estimated_yearly_sales")
        main_file = st.file_uploader(
            "Step 1: Upload your main data file",
            type=["csv", "xlsx"],
            key="main_file"
        )

    with col2:
        st.info("**Optional:** Leave blank to use default list")
        app_file = st.file_uploader(
            "Step 2: Upload custom app reference (optional)",
            type=["csv", "xlsx"],
            key="app_file"
        )

    st.divider()

    # ──────────────────────────────────────────
    # Section 3: Processing
    # ──────────────────────────────────────────

    if main_file:
        # Load main data
        if main_file.name.endswith('.csv'):
            df_main = pd.read_csv(main_file)
        else:
            df_main = pd.read_excel(main_file)

        st.info(f"✅ Loaded {len(df_main)} rows from main file")

        # Load app reference data
        if app_file:
            if app_file.name.endswith('.csv'):
                df_app = pd.read_csv(app_file)
            else:
                df_app = pd.read_excel(app_file)
            st.info(f"✅ Loaded custom app reference ({len(df_app)} apps)")
        else:
            df_app = pd.DataFrame(DEFAULT_RETURN_APPS)
            st.info(f"ℹ️  Using default app reference ({len(df_app)} apps)")

        # Run analysis
        if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
            with st.spinner("Processing your data... Please wait."):
                try:
                    df_with_returns, df_multiple_returns, error = process_return_apps(df_main, df_app)

                    if error:
                        st.error(f"❌ Error: {error}")
                    else:
                        st.success("✅ Analysis Complete!")

                        # Display metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(
                                "Brands Analyzed",
                                len(df_main.drop_duplicates(subset=['domain']))
                            )
                        with col2:
                            st.metric(
                                "With Return Apps",
                                len(df_with_returns),
                            )
                        with col3:
                            st.metric(
                                "Multiple Return Apps",
                                len(df_multiple_returns)
                            )

                        st.divider()

                        # Download button
                        total_brands = len(df_main.drop_duplicates(subset=['domain']))
                        excel_output = create_excel_download(df_with_returns, df_multiple_returns, total_brands=total_brands)
                        st.download_button(
                            label="📥 Download Excel Report",
                            data=excel_output,
                            file_name=f"return_app_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )

                        st.divider()

                        # Display results
                        st.subheader("Brands with Return Apps")
                        st.dataframe(
                            df_with_returns[[
                                'domain',
                                'return_app_count',
                                'return_app_names',
                                'platform_rank',
                                'estimated_yearly_sales'
                            ]],
                            use_container_width=True,
                            height=400
                        )

                        st.subheader("Brands with Multiple Return Apps")
                        st.dataframe(
                            df_multiple_returns[[
                                'domain',
                                'return_app_count',
                                'return_app_names',
                                'platform_rank',
                                'estimated_yearly_sales'
                            ]],
                            use_container_width=True,
                            height=300
                        )

                except Exception as e:
                    st.error(f"❌ Processing error: {str(e)}")
                    logger.exception("Processing error")

    else:
        st.warning("👆 Please upload a main data file to begin")


if __name__ == "__main__":
    main()
