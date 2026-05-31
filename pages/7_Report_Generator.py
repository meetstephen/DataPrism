import streamlit as st
st.set_page_config(page_title="Report Generator", page_icon="\U0001f4a0", layout="wide")
from utils.styles import inject_global_css
inject_global_css()

import pandas as pd
from utils.data_loader import ensure_builtin_data
from utils.ai_client import get_api_key, generate_content, GEMINI_MODEL
from utils.report_generator import generate_html_report, generate_executive_summary, generate_pdf_report, generate_docx_report
from utils.exporters import render_export_buttons
from utils.supabase_client import is_configured
from utils import database as db

st.title("\U0001F4CB Report Generator")
st.markdown("Generate comprehensive, downloadable HTML analysis reports.")

# Data Source Selection
st.markdown("### Select Data Source")

# Quick upload option
with st.expander("📁 Upload a new file for report", expanded=False):
    report_upload = st.file_uploader(
        "Upload CSV or Excel",
        type=["csv", "xlsx", "xls"],
        key="report_file_uploader",
        help="Upload a fresh dataset to generate a report from."
    )
    if report_upload is not None:
        try:
            if report_upload.name.endswith(".csv"):
                new_df = pd.read_csv(report_upload)
            else:
                new_df = pd.read_excel(report_upload)
            if not new_df.empty and len(new_df.columns) >= 1:
                st.session_state.uploaded_df = new_df
                st.success(f"✅ Loaded **{report_upload.name}** ({len(new_df):,} rows x {len(new_df.columns)} columns)")
            else:
                st.error("The uploaded file is empty or has no columns.")
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

sources = ["Built-in Community College Data"]
if st.session_state.get("uploaded_df") is not None:
    sources.append("Uploaded Data")
if st.session_state.get("online_df") is not None:
    sources.append("Online Data")
if st.session_state.get("working_df") is not None:
    sources.append("Cleaned Data")

data_source = st.radio("Choose data:", sources, horizontal=True)

# Load the selected data into df variable
df = None
if data_source == "Built-in Community College Data":
    df = ensure_builtin_data()
elif data_source == "Uploaded Data":
    df = st.session_state.get("uploaded_df")
    if df is None:
        st.error("No uploaded data found. Please upload data first.")
        st.page_link("pages/2_Upload_and_Analyze.py", label="\U0001F4C1 Go to Upload & Analyze", icon="\U0001F4C1")
        st.stop()
elif data_source == "Online Data":
    df = st.session_state.get("online_df")
    if df is None:
        st.error("No online data found. Please fetch data from the Online Data Explorer first.")
        st.page_link("pages/6_Online_Data_Explorer.py", label="\U0001F310 Go to Online Data Explorer", icon="\U0001F310")
        st.stop()
elif data_source == "Cleaned Data":
    df = st.session_state.get("working_df")
    if df is None:
        st.error("No cleaned data found. Please clean a dataset in the Data Cleaning page first.")
        st.page_link("pages/3_Data_Cleaning.py", label="\U0001f9f9 Go to Data Cleaning", icon="\U0001f9f9")
        st.stop()

st.markdown(f"**Selected dataset:** {len(df):,} rows x {len(df.columns)} columns")

# Report Configuration
st.markdown("---")
st.markdown("### Report Configuration")

col1, col2, col3 = st.columns(3)
with col1:
    report_title = st.text_input("Report Title", value="Data Analysis Report")
with col2:
    include_ai = st.checkbox("Include AI Executive Summary", value=False,
                             help="Requires Gemini API key")
with col3:
    report_format = st.selectbox("Output Format:", ["HTML", "PDF", "DOCX"], key="report_format_sel")

# Branding options
with st.expander("\U0001F3A8 Branding & Customization"):
    brand_col1, brand_col2 = st.columns(2)
    with brand_col1:
        brand_name = st.text_input("Organization Name:", value="DataPrism", key="brand_name")
    with brand_col2:
        brand_color = st.color_picker("Accent Color:", value="#00D4FF", key="brand_color")

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
    api_key = get_api_key()
    if not api_key:
        key_input = st.sidebar.text_input("Gemini API Key", type="password")
        if key_input and key_input.strip():
            st.session_state.gemini_api_key = key_input.strip()
            api_key = get_api_key()
    if api_key:
        st.sidebar.success("API key loaded")
    else:
        st.warning("Enter a Gemini API key in the sidebar for AI summary.")

# Generate button with progress
if st.button("Generate Report", type="primary", use_container_width=True):
    with st.spinner("Generating report..."):
        if report_format == "HTML":
            html_report = generate_html_report(
                df,
                title=report_title,
                include_ai_summary=include_ai,
                api_key=api_key
            )
            st.session_state.generated_report = html_report
            st.success("HTML report generated successfully!")
        elif report_format == "PDF":
            pdf_bytes = generate_pdf_report(
                df,
                title=report_title,
                include_ai_summary=include_ai,
                api_key=api_key
            )
            if pdf_bytes:
                st.session_state["_generated_pdf"] = pdf_bytes
                st.success("PDF report generated successfully!")
            else:
                st.error("PDF generation failed. Ensure fpdf2 is installed.")
        elif report_format == "DOCX":
            docx_bytes = generate_docx_report(
                df,
                title=report_title,
                include_ai_summary=include_ai,
                api_key=api_key
            )
            if docx_bytes:
                st.session_state["_generated_docx"] = docx_bytes
                st.success("DOCX report generated successfully!")
            else:
                st.error("DOCX generation failed. Ensure python-docx is installed.")

# Display report preview and download
if st.session_state.get("generated_report"):
    st.markdown("---")
    st.markdown("### Report Preview")
    import streamlit.components.v1 as components
    components.html(st.session_state.generated_report, height=600, scrolling=True)

    st.download_button(
        "Download HTML Report", st.session_state.generated_report,
        file_name="analysis_report.html", mime="text/html",
        use_container_width=True,
    )

if st.session_state.get("_generated_pdf"):
    st.download_button(
        "Download PDF Report", st.session_state["_generated_pdf"],
        file_name="analysis_report.pdf", mime="application/pdf",
        use_container_width=True,
    )

if st.session_state.get("_generated_docx"):
    st.download_button(
        "Download DOCX Report", st.session_state["_generated_docx"],
        file_name="analysis_report.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
    )

    # Multi-format export of the underlying data
    st.markdown("**Export underlying data:**")
    render_export_buttons(df, base_filename="report_data", key_prefix="report_export")

    # Optional: save report to cloud (Supabase)
    if is_configured():
        st.markdown("**Save to cloud:**")
        if st.button("\u2601\uFE0F Save report to cloud", key="report_cloud_save"):
            ok, msg = db.save_report(report_title, st.session_state.generated_report, str(data_source))
            st.success(msg) if ok else st.error(msg)
    else:
        st.caption(
            "\u2601\uFE0F Tip: connect a database (see SUPABASE_SETUP.md) to save reports to the cloud."
        )
