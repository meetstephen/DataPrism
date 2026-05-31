"""
DataPrism - Enterprise Data Intelligence Platform.

A comprehensive Streamlit web application for analyzing, cleaning, and exploring data
with interactive dashboards, AI-powered insights, and advanced analytics tools.
"""

import streamlit as st

from utils.styles import inject_global_css
from utils.data_engine import init_cleaning_state
from utils.data_loader import ensure_builtin_data, init_all_session_state
from utils.persistence import restore_session_state, save_session_state, get_last_saved_time, clear_persisted_session

# Page configuration
st.set_page_config(
    page_title="DataPrism",
    page_icon="\U0001f4a0",
    layout="wide",
    initial_sidebar_state="expanded"
)
inject_global_css()

# Initialize all common session state keys and ensure built-in data is loaded
init_all_session_state()
ensure_builtin_data()

# Initialize cleaning state
init_cleaning_state()

# --- Authentication Gate ---
from utils.auth import require_auth, get_current_user, sign_out, log_user_activity

user = require_auth()
# If require_auth() returned, the user is authenticated (or local dev mode)

# Restore persisted session on first load
if "session_restored" not in st.session_state:
    restored = restore_session_state()
    st.session_state.session_restored = True
    if restored:
        st.toast("\u2705 Previous session restored!", icon="\U0001F4BE")

# Sidebar
with st.sidebar:
    st.title("\U0001f4a0 DataPrism")
    st.markdown("---")

    # --- User Info ---
    current_user = get_current_user()
    if current_user and not current_user.get("is_mock"):
        st.markdown(
            f"**\U0001F464 {current_user.get('display_name', 'User')}**"
        )
        st.caption(
            f"{current_user.get('email', '')} | "
            f"Role: {current_user.get('role', 'viewer').title()}"
        )
        if st.button("\U0001F6AA Sign Out", key="sidebar_signout", use_container_width=True):
            sign_out()
            st.rerun()
        st.markdown("---")

    # Theme Switcher
    from utils.styles import render_theme_switcher
    render_theme_switcher()

    st.markdown("---")
    st.markdown(
        """
        **Enterprise Data Intelligence Platform**

        Navigate using the pages in the sidebar:

        - \U0001F9ED **Guided Analysis** - Step-by-step workflow
        - \U0001F680 **Getting Started** - Quick start guide
        - \U0001F4C1 **Upload & Analyze** - Your own datasets
        - \U0001f9f9 **Data Cleaning** - Transform & prepare
        - \U0001F916 **AI Insights** - Automated analysis
        - \U0001F527 **Advanced Analytics** - Custom tools
        - \U0001F310 **Online Explorer** - Web data fetching
        - \U0001F4CB **Report Generator** - Export reports
        - \U0001F4AC **Chat With Data** - Structured data & documents
        - \u2601\uFE0F **Cloud Workspace** - Save & restore
        - \U0001F50D **Data Profiling** - Quality assessment
        - \U0001F4CA **Dashboard Builder** - KPI & charts
        - \U0001F517 **Data Join** - Merge & combine datasets
        - \U0001F4DD **SQL Query** - Query with SQL
        - \U0001F4D6 **Data Dictionary** - Column documentation
        """
    )
    st.markdown("---")
    st.caption("DataPrism | Enterprise Data Intelligence")
    st.markdown("---")
    st.markdown("##### \U0001F4BE Session")
    last_saved = get_last_saved_time()
    if last_saved:
        st.caption(f"Last saved: {last_saved[:19]}")
    save_col, clear_col = st.columns(2)
    with save_col:
        if st.button("\U0001F4BE Save", use_container_width=True, help="Save current work"):
            save_session_state()
            st.toast("\u2705 Session saved!", icon="\U0001F4BE")
    with clear_col:
        if st.button("\U0001F5D1\uFE0F Clear", use_container_width=True, help="Clear saved session"):
            clear_persisted_session()
            st.toast("\U0001F5D1\uFE0F Session cleared!", icon="\U0001F5D1\uFE0F")

    # --- Feedback Widget ---
    st.markdown("---")
    st.markdown("##### \U0001F4AC Feedback")
    st.caption("Help us improve DataPrism. Report bugs, suggestions, or observations.")
    with st.expander("\u270F\uFE0F Submit Feedback", expanded=False):
        fb_type = st.selectbox(
            "Type",
            ["\U0001F41B Bug Report", "\U0001F4A1 Suggestion", "\u2753 Confusion / UX Issue", "\U0001F44D Positive Feedback"],
            key="sidebar_fb_type",
        )
        fb_page = st.selectbox(
            "Which page?",
            ["Home", "Guided Analysis", "Getting Started", "Upload & Analyze",
             "Data Cleaning", "AI Insights", "Advanced Analytics",
             "Online Explorer", "Report Generator", "Chat With Data",
             "Cloud Workspace", "Data Profiling", "Dashboard",
             "Data Join", "SQL Query", "Data Dictionary", "Other"],
            key="sidebar_fb_page",
        )
        fb_text = st.text_area(
            "Describe your feedback",
            key="sidebar_fb_text",
            placeholder="What happened? What did you expect? How can we improve?",
            height=100,
        )
        if st.button("Submit Feedback", key="sidebar_fb_submit", use_container_width=True):
            if not fb_text.strip():
                st.warning("Please describe your feedback.")
            else:
                from utils.feedback import save_feedback
                ok, msg = save_feedback(fb_type, fb_page, fb_text.strip())
                if ok:
                    st.success("\u2705 Thank you! Feedback submitted.")
                else:
                    st.error(msg)

# Main content - Welcome page
st.markdown(
    "<h1 class='dp-gradient-title' style='font-size:3rem; margin-bottom:0;'>"
    "\U0001f4a0 DataPrism</h1>",
    unsafe_allow_html=True,
)
st.markdown("### Raw Data. Refined Intelligence.")
st.markdown(
    """
    DataPrism is an enterprise-grade data intelligence platform that transforms raw data
    into actionable insights. Explore interactive dashboards, clean and transform datasets,
    generate AI-powered analysis, and have natural conversations with your data.
    """
)

st.markdown("---")

# --- Start Here: 3-button decision tree ---
st.markdown(
    "<h2 style='margin-bottom:0.2rem;'>\U0001F9ED Start Here</h2>",
    unsafe_allow_html=True,
)
st.markdown("Pick the path that matches what you want to do right now.")


def _start_card(emoji, title, description):
    st.markdown(
        f"""
        <div style="border:1px solid rgba(0,212,255,0.22); border-radius:14px;
                    padding:1.2rem 1.3rem; min-height:160px; margin-bottom:0.6rem;
                    background:linear-gradient(135deg, rgba(0,212,255,0.07), rgba(123,97,255,0.05));
                    display:flex; flex-direction:column; justify-content:flex-start;">
            <div style="font-size:1.9rem; line-height:1; margin-bottom:0.4rem;">{emoji}</div>
            <h4 style="margin:0 0 0.35rem 0; color:#E2E8F0; font-size:1.05rem;">{title}</h4>
            <p style="margin:0; color:#94A3B8; font-size:0.85rem; line-height:1.4;">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


start_col1, start_col2, start_col3 = st.columns(3)
with start_col1:
    _start_card(
        "\U0001F4C1",
        "I have my own data",
        "Upload a CSV or Excel file (including Power BI exports) for instant "
        "automated analysis, distributions, and data-quality checks.",
    )
    st.page_link(
        "pages/2_Upload_and_Analyze.py",
        label="Upload & Analyze",
        icon="\U0001F4C1",
        use_container_width=True,
    )
with start_col2:
    _start_card(
        "\U0001F9ED",
        "Show me how it works",
        "New to DataPrism? Take the guided, step-by-step workflow using the "
        "built-in sample dataset \u2014 load, clean, explore, and report.",
    )
    st.page_link(
        "pages/0_Guided_Analysis.py",
        label="Launch Guided Analysis",
        icon="\U0001F9ED",
        use_container_width=True,
    )
with start_col3:
    _start_card(
        "\U0001F310",
        "Find data online",
        "No data yet? Fetch a dataset from any URL or browse the curated "
        "catalog of verified public datasets to get started fast.",
    )
    st.page_link(
        "pages/6_Online_Data_Explorer.py",
        label="Online Data Explorer",
        icon="\U0001F310",
        use_container_width=True,
    )

st.markdown("---")

# Guided Analysis callout (the dedicated page is wired up separately)
st.markdown(
    """
    <div style="border:1px solid rgba(0,212,255,0.35); border-radius:14px;
                padding:1.25rem 1.5rem; margin-bottom:0.5rem;
                background:linear-gradient(135deg, rgba(0,212,255,0.10), rgba(123,97,255,0.08));">
        <span style="font-size:0.75rem; font-weight:700; color:#00D4FF;
                     text-transform:uppercase; letter-spacing:0.08em;">
            \U0001F9ED New &middot; Recommended for beginners
        </span>
        <h3 style="margin:0.35rem 0 0.4rem 0; color:#E2E8F0;">Guided Analysis Mode</h3>
        <p style="margin:0; color:#94A3B8; max-width:760px;">
            Not sure where to start? Guided Analysis Mode walks you through the full
            workflow step by step - load data, clean it, explore insights, and generate a
            report - without needing to know which page to open first.
            <strong>Look for &ldquo;\U0001F9ED Guided Analysis&rdquo; at the top of the sidebar.</strong>
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.page_link("pages/0_Guided_Analysis.py", label="\U0001F9ED Launch Guided Analysis", icon="\U0001F9ED")

st.markdown("---")

# Feature cards
col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        #### \U0001F4C1 Upload & Analyze
        Upload and analyze any dataset:
        - Support for CSV and Excel files (incl. **Power BI exports**)
        - Automatic column type detection
        - Summary statistics and distributions
        - Correlation analysis, data quality reports, and automated insights
        """
    )
    st.markdown(
        """
        #### \U0001F916 AI Insights Engine
        Get automated insights powered by AI:
        - Natural language data analysis
        - Pattern and trend detection
        - Anomaly identification
        - Actionable recommendations
        """
    )

with col2:
    st.markdown(
        """
        #### \U0001f9f9 Data Cleaning Engine
        Transform and prepare your data for analysis:
        - Handle missing values with multiple strategies
        - Remove duplicates and outliers (IQR method)
        - Drop or rename columns interactively
        - Full undo support and audit logging
        - Export cleaned data as CSV
        """
    )
    st.markdown(
        """
        #### \U0001F527 Advanced Analytics
        Powerful analytical tools:
        - Pivot table builder
        - Custom chart creator
        - Group-by analysis
        - Statistical summaries
        """
    )

# Additional feature cards
col3, col4 = st.columns(2)
with col3:
    st.markdown(
        """
        #### \U0001F310 Online Data Explorer
        Fetch datasets from anywhere on the web:
        - Load CSV, JSON, or Excel from any URL
        - Browse curated public dataset catalog
        - Scrape tables from web pages
        - Preview and use remote data instantly
        """
    )

with col4:
    st.markdown(
        """
        #### \U0001F4CB Report Generator
        Create professional analysis reports:
        - Comprehensive HTML reports with charts
        - AI-generated executive summaries
        - Embedded interactive visualizations
        - One-click download for sharing
        """
    )

# Unified Chat With Data card (structured data AND documents)
col5, _col6 = st.columns(2)
with col5:
    st.markdown(
        """
        #### \U0001f4ac Chat With Your Data
        One assistant for **both structured data and documents**:
        - Chat with CSV/Excel data - answers with data citations and auto-generated Plotly charts
        - Chat with documents - PDF, Word, Excel, CSV, JSON, text, **and Power BI exports**
        - Upload a file, get expert insights, summaries, and recommendations
        - Contextual follow-up questions, powered by Gemini 2.5 Flash
        """
    )

st.markdown("---")

# Dataset overview
st.markdown("### Dataset Overview")
df = st.session_state.df
st.markdown(
    f"The built-in dataset currently loaded contains **{len(df):,}** "
    f"records with **{len(df.columns)}** columns."
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Records", f"{len(df):,}")
with col2:
    st.metric("Columns", len(df.columns))
with col3:
    if "Major" in df.columns:
        st.metric("Majors", df["Major"].nunique())
    else:
        # Generic fallback when the built-in schema is not present
        numeric_cols = df.select_dtypes(include="number").shape[1]
        st.metric("Numeric Columns", numeric_cols)
with col4:
    if "Year" in df.columns:
        st.metric("Years Covered", df["Year"].nunique())
    else:
        text_cols = df.select_dtypes(include=["object", "category"]).shape[1]
        st.metric("Text Columns", text_cols)

st.markdown("---")
st.markdown("*Select a page from the sidebar to get started.*")
st.caption("DataPrism | Enterprise Data Intelligence")
