"""Shared data loading helpers to ensure datasets are always available."""
import os
import csv
from io import StringIO
import streamlit as st
import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Sample Datasets
# ---------------------------------------------------------------------------

def _generate_sales_data():
    """Generate 200 rows of synthetic sales data."""
    np.random.seed(42)
    n = 200
    products = ["Widget A", "Widget B", "Gadget X", "Gadget Y", "Device Z"]
    regions = ["North", "South", "East", "West"]
    dates = pd.date_range("2023-01-01", periods=n, freq="D")
    return pd.DataFrame({
        "Date": dates[:n],
        "Product": np.random.choice(products, n),
        "Region": np.random.choice(regions, n),
        "Revenue": np.round(np.random.uniform(500, 15000, n), 2),
        "Units": np.random.randint(1, 200, n),
        "Cost": np.round(np.random.uniform(200, 8000, n), 2),
    })


def _generate_hr_data():
    """Generate 300 rows of synthetic HR analytics data."""
    np.random.seed(43)
    n = 300
    departments = ["Engineering", "Marketing", "Sales", "HR", "Finance", "Operations"]
    return pd.DataFrame({
        "Employee_ID": [f"EMP-{i:04d}" for i in range(1, n + 1)],
        "Department": np.random.choice(departments, n),
        "Salary": np.round(np.random.normal(75000, 20000, n).clip(30000, 200000), 2),
        "Years_Experience": np.random.randint(0, 30, n),
        "Performance_Score": np.round(np.random.uniform(1.0, 5.0, n), 1),
        "Attrition": np.random.choice(["Yes", "No"], n, p=[0.2, 0.8]),
    })


def _generate_finance_data():
    """Generate 400 rows of synthetic finance transaction data."""
    np.random.seed(44)
    n = 400
    accounts = ["Checking", "Savings", "Credit", "Investment"]
    categories = ["Food", "Transport", "Utilities", "Entertainment", "Salary", "Transfer"]
    txn_types = ["Debit", "Credit"]
    dates = pd.date_range("2023-01-01", periods=n, freq="6h")
    return pd.DataFrame({
        "Date": dates[:n],
        "Account": np.random.choice(accounts, n),
        "Category": np.random.choice(categories, n),
        "Amount": np.round(np.random.uniform(-5000, 10000, n), 2),
        "Balance": np.round(np.cumsum(np.random.uniform(-500, 800, n)) + 10000, 2),
        "Transaction_Type": np.random.choice(txn_types, n),
    })


def _generate_survey_data():
    """Generate 250 rows of synthetic customer survey data."""
    np.random.seed(45)
    n = 250
    genders = ["Male", "Female", "Non-binary", "Prefer not to say"]
    categories = ["Product Quality", "Customer Service", "Pricing", "Delivery", "Website UX"]
    return pd.DataFrame({
        "Respondent_ID": [f"R-{i:04d}" for i in range(1, n + 1)],
        "Age": np.random.randint(18, 75, n),
        "Gender": np.random.choice(genders, n),
        "Satisfaction_Score": np.random.randint(1, 11, n),
        "NPS": np.random.randint(-100, 101, n),
        "Category": np.random.choice(categories, n),
    })


def _generate_marketing_data():
    """Generate 200 rows of synthetic marketing campaign data."""
    np.random.seed(46)
    n = 200
    campaigns = [f"Campaign_{i}" for i in range(1, 21)]
    channels = ["Email", "Social Media", "Search", "Display", "Affiliate"]
    return pd.DataFrame({
        "Campaign_Name": np.random.choice(campaigns, n),
        "Channel": np.random.choice(channels, n),
        "Spend": np.round(np.random.uniform(100, 50000, n), 2),
        "Impressions": np.random.randint(1000, 500000, n),
        "Clicks": np.random.randint(10, 20000, n),
        "Conversions": np.random.randint(0, 1000, n),
    })


SAMPLE_DATASETS = {
    "Sales Data": {
        "name": "Sales Data",
        "description": "200 rows of synthetic sales transactions with Date, Product, Region, Revenue, Units, and Cost.",
        "generator": _generate_sales_data,
    },
    "HR Analytics": {
        "name": "HR Analytics",
        "description": "300 rows of synthetic HR data with Employee_ID, Department, Salary, Years_Experience, Performance_Score, and Attrition.",
        "generator": _generate_hr_data,
    },
    "Finance Transactions": {
        "name": "Finance Transactions",
        "description": "400 rows of synthetic finance transactions with Date, Account, Category, Amount, Balance, and Transaction_Type.",
        "generator": _generate_finance_data,
    },
    "Customer Survey": {
        "name": "Customer Survey",
        "description": "250 rows of synthetic survey responses with Respondent_ID, Age, Gender, Satisfaction_Score, NPS, and Category.",
        "generator": _generate_survey_data,
    },
    "Marketing Campaigns": {
        "name": "Marketing Campaigns",
        "description": "200 rows of synthetic marketing data with Campaign_Name, Channel, Spend, Impressions, Clicks, and Conversions.",
        "generator": _generate_marketing_data,
    },
}


def load_sample_dataset(name):
    """Load a sample dataset by name. Returns a DataFrame or None if not found."""
    entry = SAMPLE_DATASETS.get(name)
    if entry is None:
        return None
    return entry["generator"]()


def parse_pasted_csv(text, delimiter=None):
    """Parse pasted CSV/TSV text into a DataFrame.
    Auto-detects delimiter using csv.Sniffer if not provided.
    Returns (df, error_message). On success error_message is None.
    """
    if not text or not text.strip():
        return None, "No text provided."
    try:
        if delimiter is None:
            try:
                sample = text[:4096]
                dialect = csv.Sniffer().sniff(sample)
                delimiter = dialect.delimiter
            except csv.Error:
                delimiter = ","
        df = pd.read_csv(StringIO(text), sep=delimiter)
        if df.empty:
            return None, "Parsed data is empty."
        return df, None
    except Exception as e:
        return None, f"Error parsing pasted data: {str(e)}"


def load_file_flexible(file_obj):
    """Load a file object (CSV, Excel, JSON, TSV) into a DataFrame.
    Handles encoding detection (chardet) and delimiter sniffing.
    Returns (df, error_message). On success error_message is None.
    """
    try:
        name = getattr(file_obj, "name", "unknown")
        lower_name = name.lower()

        if lower_name.endswith(".json"):
            file_obj.seek(0)
            df = pd.read_json(file_obj)
            return df, None

        if lower_name.endswith((".xlsx", ".xls")):
            file_obj.seek(0)
            df = pd.read_excel(file_obj)
            return df, None

        # CSV or TSV - detect encoding and delimiter
        file_obj.seek(0)
        raw_bytes = file_obj.read()

        # Encoding detection
        encoding = "utf-8"
        try:
            import chardet
            detected = chardet.detect(raw_bytes[:10000])
            if detected and detected.get("encoding"):
                encoding = detected["encoding"]
        except ImportError:
            pass

        text = raw_bytes.decode(encoding, errors="replace")

        # Delimiter detection
        if lower_name.endswith(".tsv"):
            sep = "\t"
        else:
            try:
                sample = text[:4096]
                dialect = csv.Sniffer().sniff(sample)
                sep = dialect.delimiter
            except csv.Error:
                sep = ","

        df = pd.read_csv(StringIO(text), sep=sep)
        return df, None
    except Exception as e:
        return None, f"Error loading file: {str(e)}"


# ---------------------------------------------------------------------------
# Core Session & Data Management
# ---------------------------------------------------------------------------

def ensure_builtin_data():
    """Ensure the built-in community college dataset is loaded into session state.
    Safe to call from any page. Returns the DataFrame."""
    if st.session_state.get("df") is not None:
        return st.session_state.df
    data_path = "data/community_college_data.csv"
    try:
        if os.path.exists(data_path):
            st.session_state.df = pd.read_csv(data_path)
        else:
            from utils.data_generator import save_dataset
            st.session_state.df = save_dataset(data_path)
    except Exception:
        # Last resort: generate in-memory
        from utils.data_generator import generate_dataset
        st.session_state.df = generate_dataset()
    return st.session_state.df


def init_all_session_state():
    """Initialize all common session state keys. Safe to call from any page."""
    defaults = {
        "online_df": None,
        "uploaded_df": None,
        "working_df": None,
        "raw_df": None,
        "generated_report": None,
        "chat_history": [],
        "doc_chat_history": [],
        "doc_content": None,
        "doc_name": None,
        "gemini_api_key": None,
        "cleaning_log": [],
        "cleaning_history": [],
        # New keys for enhanced features
        "onboarding_complete": {},
        "active_project_id": None,
        "dataset_versions": [],
        "action_audit_log": [],
        "report_branding": None,
        "dashboard_filters": {},
        "dashboard_charts": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
