"""Time-intelligence helpers for DataPrism.

Builds period-aggregated time series and derives period-over-period change
(e.g. MoM/QoQ), year-over-year change (YoY) and rolling averages from a date
column and a numeric value column.

All functions are pure (no Streamlit dependency) so they can be unit tested.
"""

import pandas as pd

# Resample frequency -> (period-over-period label, periods that make up a year)
_FREQ_INFO = {
    "D": ("DoD", "Day", 365),
    "W": ("WoW", "Week", 52),
    "M": ("MoM", "Month", 12),
    "Q": ("QoQ", "Quarter", 4),
    "Y": ("YoY", "Year", 1),
}

# User-friendly frequency choices -> pandas resample alias.
FREQ_CHOICES = {
    "Daily": "D",
    "Weekly": "W",
    "Monthly": "MS",
    "Quarterly": "QS",
    "Yearly": "YS",
}


def _freq_root(freq: str) -> str:
    """Normalize a pandas alias like 'MS'/'QS'/'YS' to its root letter."""
    return freq[0].upper()


def coerce_datetime(series: pd.Series) -> pd.Series:
    """Best-effort conversion of a column to datetime.

    Datetime columns are returned as-is. Integer/float columns that look like
    4-digit years are interpreted as calendar years. Everything else is parsed
    with ``pd.to_datetime`` (unparseable entries become NaT).
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return series

    if pd.api.types.is_numeric_dtype(series):
        non_null = series.dropna()
        if not non_null.empty and non_null.between(1000, 9999).all():
            years = series.astype("Int64").astype("string")
            return pd.to_datetime(years, format="%Y", errors="coerce")
        # Fall through to generic parsing for non-year numerics.

    return pd.to_datetime(series, errors="coerce")


def detect_date_columns(df: pd.DataFrame):
    """Return columns that are datetime, year-like integers, or named date/year."""
    candidates = []
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_datetime64_any_dtype(series):
            candidates.append(col)
            continue
        lowered = str(col).lower()
        if any(token in lowered for token in ("date", "year", "month", "time", "period", "day")):
            candidates.append(col)
            continue
        if pd.api.types.is_numeric_dtype(series):
            non_null = series.dropna()
            if not non_null.empty and non_null.between(1000, 9999).all():
                candidates.append(col)
    return candidates


def build_time_series(df, date_col, value_col, freq="MS", agg="sum"):
    """Aggregate ``value_col`` into evenly spaced periods of ``freq``.

    Returns a DataFrame with columns ``["Period", value_col]`` sorted by period.
    Rows with unparseable dates or non-numeric values are dropped.
    """
    work = df[[date_col, value_col]].copy()
    work[date_col] = coerce_datetime(work[date_col])
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
    work = work.dropna(subset=[date_col, value_col])

    if work.empty:
        return pd.DataFrame(columns=["Period", value_col])

    grouped = (
        work.set_index(date_col)
        .resample(freq)[value_col]
        .agg(agg)
        .reset_index()
        .rename(columns={date_col: "Period"})
    )
    return grouped


def compute_time_intelligence(df, date_col, value_col, freq="MS", agg="sum", rolling_window=3):
    """Build a time series and attach PoP %, YoY % and rolling-average columns.

    Returns a dict with:
        ``series``: DataFrame with Period, value, PoP %, YoY %, Rolling Avg.
        ``pop_label``: e.g. "MoM" for monthly frequency.
        ``period_label``: e.g. "Month".
        ``rolling_label``: e.g. "3-Period Rolling Avg".
        ``periods_per_year``: int used for the YoY calculation.
    """
    root = _freq_root(freq)
    pop_label, period_label, periods_per_year = _FREQ_INFO.get(root, ("PoP", "Period", 12))

    ts = build_time_series(df, date_col, value_col, freq=freq, agg=agg)

    pop_col = f"{pop_label} %"
    rolling_label = f"{rolling_window}-Period Rolling Avg"

    if ts.empty:
        for col in (pop_col, "YoY %", rolling_label):
            ts[col] = pd.Series(dtype="float64")
        return {
            "series": ts,
            "pop_label": pop_label,
            "period_label": period_label,
            "rolling_label": rolling_label,
            "periods_per_year": periods_per_year,
        }

    ts[pop_col] = (ts[value_col].pct_change(1, fill_method=None) * 100).round(2)
    if periods_per_year > 1:
        ts["YoY %"] = (ts[value_col].pct_change(periods_per_year, fill_method=None) * 100).round(2)
    else:
        # Already yearly: period-over-period IS year-over-year.
        ts["YoY %"] = ts[pop_col]
    ts[rolling_label] = ts[value_col].rolling(window=rolling_window, min_periods=1).mean().round(2)

    return {
        "series": ts,
        "pop_label": pop_label,
        "period_label": period_label,
        "rolling_label": rolling_label,
        "periods_per_year": periods_per_year,
    }
