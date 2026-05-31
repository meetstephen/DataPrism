import streamlit as st
st.set_page_config(page_title="Report Generator", page_icon="\U0001f4a0", layout="wide")
from utils.styles import inject_global_css
inject_global_css()

import pandas as pd
from utils.data_loader import ensure_builtin_data
from utils.ai_client import get_api_key, generate_content, GEMINI_MODEL
from utils.report_generator import generate_html_report, generate_executive_summary, generate_pdf_report, generate_docx_report

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
        st.stop()
elif data_source == "Online Data":
    df = st.session_state.get("online_df")
    if df is None:
        st.error("No online data found. Please fetch data from the Online Data Explorer first.")
        st.stop()
elif data_source == "Cleaned Data":
    df = st.session_state.get("working_df")
    if df is None:
        st.error("No cleaned data found. Please clean a dataset in the Data Cleaning page first.")
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

# Report Branding
with st.expander("\U0001F3A8 Report Branding", expanded=False):
    brand_col1, brand_col2 = st.columns(2)
    with brand_col1:
        branding_logo = st.file_uploader(
            "Company Logo (PNG/JPG)", type=["png", "jpg", "jpeg"],
            key="branding_logo_upload"
        )
        branding_company = st.text_input("Company Name", key="branding_company_name")
    with brand_col2:
        branding_primary = st.color_picker("Primary Color", value="#00D4FF", key="branding_primary")
        branding_secondary = st.color_picker("Secondary Color", value="#0066FF", key="branding_secondary")

    # Store branding in session state
    logo_bytes = None
    if branding_logo is not None:
        logo_bytes = branding_logo.getvalue()

    st.session_state.report_branding = {
        "logo_bytes": logo_bytes,
        "company_name": branding_company,
        "primary_color": branding_primary,
        "secondary_color": branding_secondary,
    }

# Report Format Selection
st.markdown("**Output Format:**")
report_format = st.selectbox(
    "Choose report format",
    ["HTML", "PDF", "DOCX"],
    key="report_format_select",
    label_visibility="collapsed",
)

# Generate button with progress
if st.button("Generate Report", type="primary", use_container_width=True):
    with st.spinner("Generating report..."):
        branding_data = st.session_state.get("report_branding")

        # Generate AI summary if requested
        ai_summary_text = None
        if include_ai and api_key:
            try:
                ai_summary_text = generate_executive_summary(df, api_key=api_key)
            except Exception:
                ai_summary_text = None

        if report_format == "HTML":
            html_report = generate_html_report(
                df,
                title=report_title,
                include_ai_summary=include_ai,
                api_key=api_key
            )
            st.session_state.generated_report = html_report
            st.session_state.generated_report_format = "HTML"
        elif report_format == "PDF":
            try:
                pdf_bytes = generate_pdf_report(
                    df, title=report_title,
                    branding=branding_data, ai_summary=ai_summary_text
                )
                st.session_state.generated_report_pdf = pdf_bytes
                st.session_state.generated_report_format = "PDF"
            except Exception as e:
                st.error(f"PDF generation error: {str(e)}")
        elif report_format == "DOCX":
            try:
                docx_bytes = generate_docx_report(
                    df, title=report_title,
                    branding=branding_data, ai_summary=ai_summary_text
                )
                st.session_state.generated_report_docx = docx_bytes
                st.session_state.generated_report_format = "DOCX"
            except Exception as e:
                st.error(f"DOCX generation error: {str(e)}")

        st.success("Report generated successfully!")

# Display report preview and download
report_fmt = st.session_state.get("generated_report_format", "HTML")

if report_fmt == "HTML" and "generated_report" in st.session_state:
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

elif report_fmt == "PDF" and "generated_report_pdf" in st.session_state:
    st.markdown("---")
    st.markdown("### PDF Report Ready")
    st.info("PDF report has been generated. Click below to download.")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "\U0001F4E5 Download PDF Report",
            st.session_state.generated_report_pdf,
            file_name="analysis_report.pdf",
            mime="application/pdf",
            type="primary",
        )
    with col2:
        csv_data = df.to_csv(index=False)
        st.download_button("Download Data as CSV", csv_data,
                           file_name="data_export.csv", mime="text/csv")

elif report_fmt == "DOCX" and "generated_report_docx" in st.session_state:
    st.markdown("---")
    st.markdown("### Word Document Ready")
    st.info("DOCX report has been generated. Click below to download.")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "\U0001F4E5 Download DOCX Report",
            st.session_state.generated_report_docx,
            file_name="analysis_report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
        )
    with col2:
        csv_data = df.to_csv(index=False)
        st.download_button("Download Data as CSV", csv_data,
                           file_name="data_export.csv", mime="text/csv")
