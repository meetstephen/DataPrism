import streamlit as st
st.set_page_config(page_title="Report Generator", page_icon="\U0001F4CB", layout="wide")
from utils.styles import inject_global_css
inject_global_css()

import pandas as pd
from utils.report_generator import generate_html_report, generate_executive_summary

st.title("\U0001F4CB Report Generator")
st.markdown("Generate comprehensive, downloadable HTML analysis reports.")

# Data Source Selection
st.markdown("### Select Data Source")
sources = ["Built-in Community College Data"]
if st.session_state.get("uploaded_df") is not None:
    sources.append("Uploaded Data")
if st.session_state.get("online_df") is not None:
    sources.append("Online Data")

data_source = st.radio("Choose data:", sources, horizontal=True)

# Load the selected data into df variable
df = None
if data_source == "Built-in Community College Data":
    if "df" in st.session_state:
        df = st.session_state.df
    else:
        st.error("Built-in dataset not loaded. Please visit the home page first.")
        st.stop()
elif data_source == "Uploaded Data":
    df = st.session_state.get("uploaded_df")
    if df is None:
        st.error("No uploaded data found. Please upload data first.")
        st.stop()
elif data_source == "Online Data":
    df = st.session_state.get("online_df")
    if df is None:
        st.error("No online data found. Please fetch data from the Online Data Explorer first.")
        st.stop()

st.markdown(f"**Selected dataset:** {len(df):,} rows x {len(df.columns)} columns")

# Report Configuration
st.markdown("---")
st.markdown("### Report Configuration")

col1, col2 = st.columns(2)
with col1:
    report_title = st.text_input("Report Title", value="Data Analysis Report")
with col2:
    include_ai = st.checkbox("Include AI Executive Summary", value=False,
                             help="Requires Gemini API key")

# Sections to include (all checked by default)
st.markdown("**Sections to include:**")
sec_col1, sec_col2, sec_col3 = st.columns(3)
with sec_col1:
    inc_overview = st.checkbox("Dataset Overview", value=True)
    inc_stats = st.checkbox("Summary Statistics", value=True)
with sec_col2:
    inc_charts = st.checkbox("Distribution Charts", value=True)
    inc_correlation = st.checkbox("Correlation Analysis", value=True)
with sec_col3:
    inc_quality = st.checkbox("Data Quality", value=True)
    inc_recommendations = st.checkbox("Recommendations", value=True)

# API key handling
api_key = None
if include_ai:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        api_key = st.sidebar.text_input("Gemini API Key", type="password")
    if not api_key:
        st.warning("Enter a Gemini API key in the sidebar for AI summary.")

# Generate button with progress
if st.button("Generate Report", type="primary", use_container_width=True):
    with st.spinner("Generating report..."):
        html_report = generate_html_report(
            df,
            title=report_title,
            include_ai_summary=include_ai,
            api_key=api_key
        )

        # Store in session state
        st.session_state.generated_report = html_report
        st.success("Report generated successfully!")

# Display report preview and download
if "generated_report" in st.session_state:
    st.markdown("---")
    st.markdown("### Report Preview")
    import streamlit.components.v1 as components
    components.html(st.session_state.generated_report, height=600, scrolling=True)

    # Download buttons
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Download HTML Report", st.session_state.generated_report,
                           file_name="analysis_report.html", mime="text/html")
    with col2:
        csv_data = df.to_csv(index=False)
        st.download_button("Download Data as CSV", csv_data,
                           file_name="data_export.csv", mime="text/csv")
