"""Multi-format export helpers for DataPrism.

Provides serialization of a DataFrame to CSV, Excel, JSON, and Parquet, plus a
reusable Streamlit widget (`render_export_buttons`) that renders one download
button per available format in a single row.

The serialization helpers are pure (no Streamlit dependency) so they can be unit
tested in isolation.
"""

import io

import pandas as pd


# --- Pure serialization helpers ---------------------------------------------

def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Serialize a DataFrame to UTF-8 encoded CSV bytes."""
    return df.to_csv(index=False).encode("utf-8")


def to_json_bytes(df: pd.DataFrame) -> bytes:
    """Serialize a DataFrame to pretty-printed, record-oriented JSON bytes."""
    return df.to_json(orient="records", indent=2, date_format="iso").encode("utf-8")


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Serialize a DataFrame to an .xlsx workbook (single 'Data' sheet)."""
    buffer = io.BytesIO()
    # Excel cannot store timezone-aware datetimes; drop tz to stay safe.
    safe_df = df.copy()
    for col in safe_df.columns:
        if isinstance(safe_df[col].dtype, pd.DatetimeTZDtype):
            safe_df[col] = safe_df[col].dt.tz_localize(None)
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        safe_df.to_excel(writer, index=False, sheet_name="Data")
    return buffer.getvalue()


def to_parquet_bytes(df: pd.DataFrame) -> bytes:
    """Serialize a DataFrame to Parquet bytes (requires pyarrow)."""
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False)
    return buffer.getvalue()


# Registry: format key -> (label, file extension, mime type, serializer)
_FORMATS = {
    "csv": ("\U0001F4C4 CSV", "csv", "text/csv", to_csv_bytes),
    "excel": (
        "\U0001F4D7 Excel",
        "xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        to_excel_bytes,
    ),
    "json": ("\U0001F4E6 JSON", "json", "application/json", to_json_bytes),
    "parquet": ("\U0001F5C3\uFE0F Parquet", "parquet", "application/octet-stream", to_parquet_bytes),
}


# --- Streamlit widget --------------------------------------------------------

def render_export_buttons(
    df: pd.DataFrame,
    base_filename: str = "dataprism_export",
    key_prefix: str = "export",
    formats=("csv", "excel", "json", "parquet"),
):
    """Render a row of download buttons for the given DataFrame.

    Args:
        df: The DataFrame to export.
        base_filename: File name stem (without extension) for downloads.
        key_prefix: Unique key prefix to avoid Streamlit widget collisions.
        formats: Iterable of format keys to offer (any of csv/excel/json/parquet).

    Each format is serialized eagerly; if a format fails (e.g. an exotic dtype
    that Parquet rejects), a disabled placeholder button explains why instead of
    crashing the page.
    """
    import streamlit as st

    formats = [f for f in formats if f in _FORMATS]
    if not formats:
        return

    cols = st.columns(len(formats))
    for col, fmt in zip(cols, formats):
        label, ext, mime, serializer = _FORMATS[fmt]
        with col:
            try:
                data = serializer(df)
                st.download_button(
                    label,
                    data=data,
                    file_name=f"{base_filename}.{ext}",
                    mime=mime,
                    use_container_width=True,
                    key=f"{key_prefix}_{fmt}",
                )
            except Exception as exc:  # pragma: no cover - defensive UI guard
                st.button(
                    f"{label} (unavailable)",
                    disabled=True,
                    use_container_width=True,
                    key=f"{key_prefix}_{fmt}_disabled",
                    help=f"Could not generate {fmt.upper()}: {exc}",
                )
