"""Data Profiling - Quality gauge, column profiles, AI commentary, correlation heatmap."""
import streamlit as st
st.set_page_config(page_title="Data Profiling", page_icon="\U0001f4a0", layout="wide")
from utils.styles import inject_global_css, render_sidebar_nav
inject_global_css()
render_sidebar_nav()

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.data_loader import ensure_builtin_data, init_all_session_state
from utils.ai_client import get_api_key
from utils.profiling import (
    compute_quality_score,
    generate_column_profiles,
    generate_correlation_heatmap_data,
    ai_profiler_commentary,
)

init_all_session_state()

st.title("\U0001F50D Data Profiling")
st.markdown("Comprehensive data quality assessment, column statistics, and AI-powered commentary.")

with st.expander("❓ How to use this page", expanded=False):
    st.markdown("""
    1. **Select or upload** a dataset using the options above
    2. The **Quality Score** gauge shows an overall 0-100 health rating
    3. **Column profiles** show type, null %, unique values, and distributions
    4. **AI Commentary** (requires Gemini API key) provides plain-English assessment
    5. **Correlation Heatmap** flags highly correlated column pairs (>0.85)
    6. Use the **Next Steps** links at the bottom to continue your workflow
    """)

# Data source selection
st.markdown("### Select Data Source")
sources = ["Built-in Community College Data"]
if st.session_state.get("uploaded_df") is not None:
    sources.append("Uploaded Data")
if st.session_state.get("working_df") is not None:
    sources.append("Cleaned Data")
if st.session_state.get("online_df") is not None:
    sources.append("Online Data")

data_source = st.radio("Choose data:", sources, horizontal=True, key="profiling_source")

df = None
if data_source == "Built-in Community College Data":
    df = ensure_builtin_data()
elif data_source == "Uploaded Data":
    df = st.session_state.get("uploaded_df")
elif data_source == "Cleaned Data":
    df = st.session_state.get("working_df")
elif data_source == "Online Data":
    df = st.session_state.get("online_df")

# Direct upload option — so users can bring their own data without visiting another page
with st.expander("\U0001F4C1 Upload your own file directly", expanded=(df is None)):
    upload_col1, upload_col2 = st.columns([3, 2])
    with upload_col1:
        prof_file = st.file_uploader(
            "Upload CSV, Excel, JSON, TSV, or Parquet",
            type=["csv", "xlsx", "xls", "json", "tsv", "parquet"],
            key="profiling_file_upload",
            help="File will also be saved to your session for use on other pages.",
        )
    with upload_col2:
        st.markdown("")
        st.markdown("")
        st.caption("Or paste CSV/TSV text below:")
        prof_paste = st.text_area(
            "Paste data",
            height=100,
            key="profiling_paste",
            placeholder="col1,col2,col3\n1,a,100\n2,b,200",
            label_visibility="collapsed",
        )

    if prof_file is not None:
        from utils.data_loader import load_file_flexible
        loaded, err = load_file_flexible(prof_file)
        if err:
            st.error(err)
        elif loaded is not None:
            df = loaded
            st.session_state.uploaded_df = df.copy()
            st.success(f"Loaded: {prof_file.name} ({len(df):,} rows)")
    elif prof_paste and prof_paste.strip():
        from utils.data_loader import parse_pasted_csv
        loaded, err = parse_pasted_csv(prof_paste)
        if err:
            st.error(err)
        elif loaded is not None:
            df = loaded
            st.session_state.uploaded_df = df.copy()
            st.success(f"Loaded pasted data ({len(df):,} rows)")

if df is None or df.empty:
    st.warning("No data available. Upload a file above, or load data from another page.")
    try:
        st.page_link("pages/2_Upload_and_Analyze.py", label="\U0001F4C1 Go to Upload & Analyze", icon="\U0001F4C1")
    except Exception:
        pass
    st.stop()

st.info(f"Profiling: {len(df):,} rows x {len(df.columns)} columns")
st.markdown("---")

# Quality Score Gauge
st.markdown("### Data Quality Score")
score = compute_quality_score(df)

fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=score,
    title={"text": "Quality Score (0-100)"},
    number={"suffix": "/100"},
    gauge={
        "axis": {"range": [0, 100]},
        "bar": {"color": "#00D4FF"},
        "steps": [
            {"range": [0, 40], "color": "rgba(239,68,68,0.2)"},
            {"range": [40, 70], "color": "rgba(245,158,11,0.2)"},
            {"range": [70, 100], "color": "rgba(16,185,129,0.2)"},
        ],
        "threshold": {
            "line": {"color": "#00D4FF", "width": 4},
            "thickness": 0.75,
            "value": score,
        },
    },
))
fig.update_layout(
    height=280,
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#F0F4F8",
)
st.plotly_chart(fig, use_container_width=True)

if score >= 80:
    st.success("Excellent data quality - dataset is ready for analysis.")
elif score >= 50:
    st.warning("Moderate quality - some cleaning recommended before analysis.")
else:
    st.error("Low quality - significant data cleaning is needed.")

st.markdown("---")

# AI Commentary
st.markdown("### AI Profiling Commentary")
api_key = get_api_key()
with st.spinner("Generating profiling commentary..."):
    commentary = ai_profiler_commentary(df, api_key=api_key)
st.markdown(f"> {commentary}")

st.markdown("---")

# Column Profiles
st.markdown("### Column Profiles")
profiles = generate_column_profiles(df)

if profiles:
    profile_df = pd.DataFrame(profiles)
    display_cols = ["column", "dtype", "non_null", "null_pct", "unique", "mean", "std", "min", "max", "mode"]
    available_cols = [c for c in display_cols if c in profile_df.columns]
    st.dataframe(
        profile_df[available_cols],
        use_container_width=True,
        hide_index=True,
    )

    # Expandable per-column details
    with st.expander("Detailed Column Profiles"):
        for profile in profiles:
            col_name = profile["column"]
            st.markdown(f"**{col_name}** ({profile['dtype']})")
            detail_cols = st.columns(4)
            with detail_cols[0]:
                st.metric("Non-Null", profile["non_null"])
            with detail_cols[1]:
                st.metric("Null %", f"{profile['null_pct']}%")
            with detail_cols[2]:
                st.metric("Unique", profile["unique"])
            with detail_cols[3]:
                if profile["mean"] is not None:
                    st.metric("Mean", f"{profile['mean']:.4f}")
                elif profile["mode"]:
                    st.metric("Mode", profile["mode"])
            st.markdown("---")

st.markdown("---")

# Correlation Heatmap
st.markdown("### Correlation Heatmap")
heatmap_data = generate_correlation_heatmap_data(df)

if heatmap_data:
    columns = heatmap_data["columns"]
    matrix = heatmap_data["matrix"]

    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=columns,
        y=columns,
        colorscale="RdBu_r",
        zmin=-1,
        zmax=1,
        text=[[f"{v:.2f}" for v in row] for row in matrix],
        texttemplate="%{text}",
        hovertemplate="(%{x}, %{y}): %{z:.3f}<extra></extra>",
    ))
    fig.update_layout(
        title="Correlation Matrix",
        template="plotly_dark",
        font=dict(family="Arial, sans-serif", size=11),
        height=500,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Need at least 2 numeric columns for correlation analysis.")

# Navigation
st.markdown("---")
st.markdown("### Next Steps")
nav_col1, nav_col2, nav_col3 = st.columns(3)
try:
    with nav_col1:
        st.page_link("pages/3_Data_Cleaning.py", label="\U0001f9f9 Clean Data", icon="\U0001f9f9")
    with nav_col2:
        st.page_link("pages/4_AI_Insights_Engine.py", label="\U0001F916 AI Insights", icon="\U0001F916")
    with nav_col3:
        st.page_link("pages/11_Dashboard.py", label="\U0001F4CA Dashboard", icon="\U0001F4CA")
except Exception:
    pass  # page_link requires multipage app context; graceful in standalone
