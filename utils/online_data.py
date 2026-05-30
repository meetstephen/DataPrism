"""
Online Data Explorer utility functions.

Provides web-connected data fetching capabilities: fetch CSV/JSON/Excel from URLs,
scrape HTML tables, and a built-in catalog of popular public datasets.
"""

import streamlit as st
import pandas as pd
import requests
from io import StringIO, BytesIO


def detect_file_type(url):
    """
    Infer file type (csv/json/excel) from URL extension.
    Returns 'csv', 'json', 'excel', or 'unknown'.
    """
    url_lower = url.lower().split("?")[0].split("#")[0]

    if url_lower.endswith(".csv"):
        return "csv"
    elif url_lower.endswith(".json"):
        return "json"
    elif url_lower.endswith((".xlsx", ".xls")):
        return "excel"
    else:
        return "unknown"


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_data_from_url(url, file_type="auto", timeout=30):
    """
    Download and parse CSV/JSON/Excel from a URL.
    Returns (DataFrame, None) on success or (None, error_message) on failure.
    """
    try:
        if file_type == "auto":
            file_type = detect_file_type(url)
            if file_type == "unknown":
                # Try to detect from content-type header
                head_resp = requests.head(url, timeout=10, allow_redirects=True)
                content_type = head_resp.headers.get("Content-Type", "").lower()
                if "csv" in content_type or "text/plain" in content_type:
                    file_type = "csv"
                elif "json" in content_type:
                    file_type = "json"
                elif "excel" in content_type or "spreadsheet" in content_type:
                    file_type = "excel"
                else:
                    file_type = "csv"  # Default fallback

        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        if not response.content:
            return None, "The URL returned an empty response."

        if file_type == "csv":
            df = pd.read_csv(StringIO(response.text))
        elif file_type == "json":
            df = pd.read_json(StringIO(response.text))
        elif file_type == "excel":
            df = pd.read_excel(BytesIO(response.content))
        else:
            return None, f"Unsupported file type: {file_type}"

        return df, None

    except requests.exceptions.Timeout:
        return None, "Request timed out. The server took too long to respond."
    except requests.exceptions.ConnectionError:
        return None, "Connection error. Please check the URL and your internet connection."
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP error: {e.response.status_code} - {e.response.reason}"
    except requests.exceptions.MissingSchema:
        return None, "Invalid URL. Please include http:// or https:// prefix."
    except requests.exceptions.InvalidURL:
        return None, "Invalid URL format. Please check the URL and try again."
    except pd.errors.EmptyDataError:
        return None, "The file appears to be empty or has no parseable data."
    except pd.errors.ParserError as e:
        return None, f"Failed to parse the file: {str(e)}"
    except ValueError as e:
        return None, f"Data parsing error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"


def scrape_tables_from_url(url, timeout=30):
    """
    Extract HTML tables from a web page using pandas.read_html.
    Returns (list_of_dataframes, None) on success or (None, error_message) on failure.
    """
    try:
        response = requests.get(url, timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (compatible; DataExplorer/1.0)"
        })
        response.raise_for_status()

        if not response.text:
            return None, "The URL returned an empty response."

        tables = pd.read_html(StringIO(response.text))

        if not tables:
            return None, "No tables found on this web page."

        return tables, None

    except requests.exceptions.Timeout:
        return None, "Request timed out. The server took too long to respond."
    except requests.exceptions.ConnectionError:
        return None, "Connection error. Please check the URL and your internet connection."
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP error: {e.response.status_code} - {e.response.reason}"
    except requests.exceptions.MissingSchema:
        return None, "Invalid URL. Please include http:// or https:// prefix."
    except requests.exceptions.InvalidURL:
        return None, "Invalid URL format. Please check the URL and try again."
    except ValueError:
        return None, "No tables found on this web page."
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"


def get_dataset_catalog():
    """
    Return a dict of categorized public datasets.
    Format: { "Category Name": [ {"name": "...", "description": "...", "url": "...", "format": "csv|json"}, ... ] }
    """
    catalog = {
        "Government": [
            {
                "name": "US Population by State",
                "description": "US Census population estimates by state",
                "url": "https://raw.githubusercontent.com/datasets/population-us/main/data/population.csv",
                "format": "csv"
            },
            {
                "name": "World Country Codes",
                "description": "ISO 3166-1 country codes and names",
                "url": "https://raw.githubusercontent.com/datasets/country-codes/master/data/country-codes.csv",
                "format": "csv"
            },
            {
                "name": "US Federal Budget",
                "description": "Historical US federal budget data",
                "url": "https://raw.githubusercontent.com/datasets/usa-budget-us-budget/main/data/budget.csv",
                "format": "csv"
            },
        ],
        "Economics": [
            {
                "name": "World GDP",
                "description": "GDP by country from World Bank",
                "url": "https://raw.githubusercontent.com/datasets/gdp/main/data/gdp.csv",
                "format": "csv"
            },
            {
                "name": "Consumer Price Index (US)",
                "description": "US Consumer Price Index historical data",
                "url": "https://raw.githubusercontent.com/datasets/cpi-us/main/data/cpiai.csv",
                "format": "csv"
            },
            {
                "name": "S&P 500 Companies",
                "description": "List of S&P 500 companies with sectors",
                "url": "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv",
                "format": "csv"
            },
        ],
        "Education": [
            {
                "name": "World University Rankings",
                "description": "Times Higher Education World University Rankings data",
                "url": "https://raw.githubusercontent.com/datasets/world-university-rankings/main/data/times.csv",
                "format": "csv"
            },
            {
                "name": "Iris Dataset",
                "description": "Classic iris flower measurements dataset",
                "url": "https://raw.githubusercontent.com/datasets/iris/master/data/iris.csv",
                "format": "csv"
            },
            {
                "name": "Glacier Mass Balance",
                "description": "Glacier mass balance measurements for climate studies",
                "url": "https://raw.githubusercontent.com/datasets/glacier-mass-balance/main/data/glaciers.csv",
                "format": "csv"
            },
        ],
        "Health": [
            {
                "name": "COVID-19 Global Data",
                "description": "Our World in Data COVID-19 dataset (latest)",
                "url": "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/latest/owid-covid-latest.csv",
                "format": "csv"
            },
            {
                "name": "Global Life Expectancy",
                "description": "Life expectancy by country from World Bank",
                "url": "https://raw.githubusercontent.com/datasets/life-expectancy/main/data/life-expectancy.csv",
                "format": "csv"
            },
            {
                "name": "WHO Suicide Statistics",
                "description": "WHO global suicide statistics by country and year",
                "url": "https://raw.githubusercontent.com/datasets/suicides/main/data/suicides.csv",
                "format": "csv"
            },
        ],
        "Environment": [
            {
                "name": "Global Temperature Anomalies",
                "description": "NASA GISS global temperature anomaly data",
                "url": "https://raw.githubusercontent.com/datasets/global-temp/master/data/monthly.csv",
                "format": "csv"
            },
            {
                "name": "CO2 Emissions by Country",
                "description": "Carbon dioxide emissions per country from OWID",
                "url": "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv",
                "format": "csv"
            },
            {
                "name": "Sea Level Rise",
                "description": "Global mean sea level data from CSIRO",
                "url": "https://raw.githubusercontent.com/datasets/sea-level-rise/master/data/csiro_recons_gmsl_yr_2015.csv",
                "format": "csv"
            },
        ],
        "Technology": [
            {
                "name": "GitHub Programming Languages",
                "description": "Popular programming languages on GitHub",
                "url": "https://raw.githubusercontent.com/datasets/github-programming-languages/main/data/languages.csv",
                "format": "csv"
            },
            {
                "name": "World Population",
                "description": "Global population by country over time",
                "url": "https://raw.githubusercontent.com/datasets/population/main/data/population.csv",
                "format": "csv"
            },
            {
                "name": "Airport Codes",
                "description": "World airport codes and locations",
                "url": "https://raw.githubusercontent.com/datasets/airport-codes/master/data/airport-codes.csv",
                "format": "csv"
            },
        ],
    }
    return catalog


def validate_dataframe(df):
    """
    Validate a loaded DataFrame. Returns dict with 'is_valid' (bool) and 'issues' (list of strings).
    Checks: not empty, not all-null columns, reasonable size (<1M rows), has at least 1 column.
    """
    issues = []

    if df is None:
        return {"is_valid": False, "issues": ["DataFrame is None."]}

    if df.empty:
        issues.append("The dataset is empty (no rows).")

    if len(df.columns) == 0:
        issues.append("The dataset has no columns.")

    if len(df) > 1_000_000:
        issues.append(f"The dataset is very large ({len(df):,} rows). Performance may be affected.")

    # Check for all-null columns
    all_null_cols = [col for col in df.columns if df[col].isna().all()]
    if all_null_cols:
        issues.append(f"The following columns are entirely empty: {', '.join(str(c) for c in all_null_cols)}")

    is_valid = len(issues) == 0 or (
        len(issues) == 1 and "very large" in issues[0]
    )

    return {"is_valid": is_valid, "issues": issues}
