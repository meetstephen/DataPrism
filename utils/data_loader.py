"""Shared data loading helpers to ensure datasets are always available."""
import os
import streamlit as st
import pandas as pd


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
        "dp_active_theme": "Enterprise Dark",
        "dp_onboarding_done": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# --- Sample Datasets ---

SAMPLE_DATASETS = {
    "Iris (Classification)": {
        "description": "Classic iris flower measurements - 150 rows, 5 columns",
        "generator": "_gen_iris",
    },
    "Sales Data": {
        "description": "Simulated retail sales data - 500 rows, 7 columns",
        "generator": "_gen_sales",
    },
    "Employee Survey": {
        "description": "Employee satisfaction survey - 200 rows, 6 columns",
        "generator": "_gen_employee",
    },
    "Weather Stations": {
        "description": "Weather station readings - 365 rows, 6 columns",
        "generator": "_gen_weather",
    },
    "Student Performance": {
        "description": "Student grades and demographics - 300 rows, 8 columns",
        "generator": "_gen_students",
    },
}


def _gen_iris():
    """Generate Iris-like dataset."""
    import numpy as np
    np.random.seed(42)
    n = 150
    species = np.repeat(["setosa", "versicolor", "virginica"], 50)
    sepal_length = np.concatenate([
        np.random.normal(5.0, 0.35, 50),
        np.random.normal(5.9, 0.5, 50),
        np.random.normal(6.6, 0.6, 50),
    ])
    sepal_width = np.concatenate([
        np.random.normal(3.4, 0.38, 50),
        np.random.normal(2.8, 0.3, 50),
        np.random.normal(3.0, 0.3, 50),
    ])
    petal_length = np.concatenate([
        np.random.normal(1.5, 0.17, 50),
        np.random.normal(4.3, 0.5, 50),
        np.random.normal(5.6, 0.5, 50),
    ])
    petal_width = np.concatenate([
        np.random.normal(0.2, 0.1, 50),
        np.random.normal(1.3, 0.2, 50),
        np.random.normal(2.0, 0.3, 50),
    ])
    return pd.DataFrame({
        "sepal_length": sepal_length.round(1),
        "sepal_width": sepal_width.round(1),
        "petal_length": petal_length.round(1),
        "petal_width": petal_width.round(1),
        "species": species,
    })


def _gen_sales():
    """Generate sales dataset."""
    import numpy as np
    np.random.seed(123)
    n = 500
    regions = np.random.choice(["North", "South", "East", "West"], n)
    products = np.random.choice(["Widget A", "Widget B", "Gadget X", "Gadget Y", "Premium Z"], n)
    dates = pd.date_range("2023-01-01", periods=n, freq="D")[:n]
    revenue = np.random.lognormal(6, 0.8, n).round(2)
    quantity = np.random.randint(1, 50, n)
    return pd.DataFrame({
        "date": dates[:n],
        "region": regions,
        "product": products,
        "revenue": revenue,
        "quantity": quantity,
        "unit_price": (revenue / quantity).round(2),
        "discount_pct": np.random.choice([0, 5, 10, 15, 20], n),
    })


def _gen_employee():
    """Generate employee survey dataset."""
    import numpy as np
    np.random.seed(456)
    n = 200
    departments = np.random.choice(["Engineering", "Sales", "Marketing", "HR", "Finance"], n)
    return pd.DataFrame({
        "department": departments,
        "satisfaction": np.random.randint(1, 11, n),
        "years_tenure": np.random.randint(0, 20, n),
        "salary_band": np.random.choice(["Junior", "Mid", "Senior", "Lead"], n),
        "remote_days": np.random.randint(0, 6, n),
        "engagement_score": np.random.normal(7.0, 1.5, n).clip(1, 10).round(1),
    })


def _gen_weather():
    """Generate weather dataset."""
    import numpy as np
    np.random.seed(789)
    n = 365
    dates = pd.date_range("2023-01-01", periods=n)
    # Simulate temperature with seasonal pattern
    day_of_year = np.arange(n)
    temp = 15 + 12 * np.sin(2 * np.pi * (day_of_year - 80) / 365) + np.random.normal(0, 3, n)
    return pd.DataFrame({
        "date": dates,
        "temperature_c": temp.round(1),
        "humidity_pct": np.random.normal(65, 15, n).clip(20, 100).round(0),
        "wind_speed_kmh": np.random.exponential(12, n).round(1),
        "precipitation_mm": np.random.exponential(2, n).round(1),
        "station": np.random.choice(["Station_A", "Station_B", "Station_C"], n),
    })


def _gen_students():
    """Generate student performance dataset."""
    import numpy as np
    np.random.seed(321)
    n = 300
    genders = np.random.choice(["Male", "Female"], n)
    majors = np.random.choice(["STEM", "Arts", "Business", "Health Sciences"], n)
    gpa = np.random.normal(3.0, 0.5, n).clip(1.0, 4.0).round(2)
    return pd.DataFrame({
        "student_id": range(1, n + 1),
        "gender": genders,
        "major": majors,
        "gpa": gpa,
        "credits_completed": np.random.randint(15, 130, n),
        "study_hours_week": np.random.normal(20, 8, n).clip(2, 50).round(1),
        "extracurricular": np.random.choice(["Yes", "No"], n, p=[0.4, 0.6]),
        "graduation_year": np.random.choice([2023, 2024, 2025, 2026], n),
    })


def load_sample_dataset(name):
    """Load a sample dataset by name. Returns a DataFrame or None."""
    if name not in SAMPLE_DATASETS:
        return None

    generator_name = SAMPLE_DATASETS[name]["generator"]
    generators = {
        "_gen_iris": _gen_iris,
        "_gen_sales": _gen_sales,
        "_gen_employee": _gen_employee,
        "_gen_weather": _gen_weather,
        "_gen_students": _gen_students,
    }
    gen_fn = generators.get(generator_name)
    if gen_fn:
        return gen_fn()
    return None


def parse_pasted_csv(text):
    """Parse pasted CSV/TSV text into a DataFrame.

    Returns (df, error_message) tuple. On success, error_message is None.
    """
    import io

    if not text or not text.strip():
        return None, "No data pasted."

    try:
        # Try tab-separated first
        if "\t" in text:
            df = pd.read_csv(io.StringIO(text), sep="\t")
        else:
            df = pd.read_csv(io.StringIO(text))

        if df.empty:
            return None, "Parsed data is empty."
        return df, None
    except Exception as e:
        return None, f"Could not parse pasted data: {str(e)}"


def load_file_flexible(uploaded_file):
    """Load a file supporting CSV, Excel, JSON, TSV, and Parquet.

    Returns (df, error_message) tuple.
    """
    if uploaded_file is None:
        return None, "No file provided."

    name = uploaded_file.name.lower()
    try:
        if name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file)
        elif name.endswith(".json"):
            df = pd.read_json(uploaded_file)
        elif name.endswith(".tsv"):
            df = pd.read_csv(uploaded_file, sep="\t")
        elif name.endswith(".parquet"):
            df = pd.read_parquet(uploaded_file)
        else:
            # Try CSV as fallback
            df = pd.read_csv(uploaded_file)

        if df is None or df.empty:
            return None, "File loaded but contains no data."
        return df, None
    except Exception as e:
        return None, f"Error reading file: {str(e)}"
