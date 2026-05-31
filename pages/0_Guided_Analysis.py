"""
DataPrism - Guided Analysis Mode.

A 7-stage linear wizard that walks users through the full data analysis
lifecycle: define a question, upload data, profile, clean, explore,
generate insights, and produce a report.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from utils.styles import inject_global_css
from utils.data_loader import init_all_session_state
from utils.ai_client import get_api_key, generate_content
from utils.data_engine import (
    init_cleaning_state, apply_cleaning_step,
    fill_missing, drop_missing_rows, remove_duplicates, remove_outliers_iqr,
)
from utils.ai_insights import (
    generate_data_quality_report, generate_summary_stats,
    format_summary_as_markdown, generate_insights_fallback,
    generate_recommendations, detect_anomalies,
)
from utils.visualizations import (
    create_histogram, create_bar_chart, create_heatmap,
    create_scatter_plot, create_box_plot,
)
from utils.online_data import get_dataset_catalog, fetch_data_from_url
from utils.report_generator import generate_html_report

# ---------------------------------------------------------------------------
# Page config (MUST be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Guided Analysis - DataPrism",
    page_icon="\U0001f4a0",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_global_css()
init_all_session_state()
init_cleaning_state()

# ---------------------------------------------------------------------------
# Session state defaults for the wizard
# ---------------------------------------------------------------------------
if "guide_stage" not in st.session_state:
    st.session_state.guide_stage = 1
if "guide_data" not in st.session_state:
    st.session_state.guide_data = {}

STAGE_LABELS = [
    "Define Question",
    "Upload Data",
    "Profile",
    "Clean",
    "Explore",
    "Insights",
    "Report",
]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _render_progress_bar():
    """Always-visible progress indicator showing the 7 stages."""
    stage = st.session_state.guide_stage
    cols = st.columns(7)
    for i, (col, label) in enumerate(zip(cols, STAGE_LABELS), start=1):
        if i < stage:
            col.markdown(
                f"<div style='text-align:center;'>"
                f"<span style='color:#10B981; font-weight:700;'>&#10003;</span><br>"
                f"<span style='font-size:0.7rem; color:#10B981;'>{label}</span></div>",
                unsafe_allow_html=True,
            )
        elif i == stage:
            col.markdown(
                f"<div style='text-align:center;'>"
                f"<span style='color:#00D4FF; font-size:1.1rem; font-weight:700;'>{i}</span><br>"
                f"<span style='font-size:0.7rem; color:#00D4FF; font-weight:600;'>{label}</span></div>",
                unsafe_allow_html=True,
            )
        else:
            col.markdown(
                f"<div style='text-align:center;'>"
                f"<span style='color:#475569;'>{i}</span><br>"
                f"<span style='font-size:0.7rem; color:#475569;'>{label}</span></div>",
                unsafe_allow_html=True,
            )
    st.markdown("---")


def _nav_buttons(can_next=True):
    """Render Back / Next navigation buttons. Returns True if Next was clicked."""
    stage = st.session_state.guide_stage
    left, _, right = st.columns([1, 5, 1])
    with left:
        if stage > 1:
            if st.button("\u2190 Back", key=f"back_{stage}"):
                st.session_state.guide_stage -= 1
                st.rerun()
    with right:
        if can_next:
            if st.button("Next \u2192", key=f"next_{stage}", type="primary"):
                st.session_state.guide_stage += 1
                st.rerun()
    return False


def _ai_coach(prompt_text, key_suffix):
    """Show an AI coaching tip. Graceful fallback on failure."""
    api_key = get_api_key()
    if not api_key:
        return
    system = (
        "You are a friendly data-literacy coach inside an analytics platform. "
        "Keep tips concise (2-4 sentences), encouraging, and actionable."
    )
    with st.spinner("Getting AI coaching tip..."):
        text, err = generate_content(prompt_text, api_key=api_key, system_instruction=system)
    if text:
        st.info(f"**Coach:** {text}")


# ---------------------------------------------------------------------------
# Stage 1 - Define Your Question
# ---------------------------------------------------------------------------

def render_stage_1():
    st.markdown("## Stage 1: Define Your Research Question")
    st.markdown(
        "A clear question focuses your analysis. What do you want to learn from the data?"
    )

    goal = st.text_area(
        "What is your analysis goal?",
        value=st.session_state.guide_data.get("goal", ""),
        placeholder="e.g. Understand which factors most influence student retention rates...",
        height=120,
        key="guide_goal_input",
    )
    st.session_state.guide_data["goal"] = goal

    analysis_type = st.selectbox(
        "What type of analysis best fits?",
        ["Exploratory (discover patterns)", "Descriptive (summarize data)",
         "Comparative (compare groups)", "Predictive (forecast trends)"],
        index=0,
        key="guide_analysis_type",
    )
    st.session_state.guide_data["analysis_type"] = analysis_type

    audience = st.selectbox(
        "Who is the audience for your findings?",
        ["Executive / Leadership", "Technical Team", "Academic / Research",
         "General / Non-technical"],
        index=0,
        key="guide_audience",
    )
    st.session_state.guide_data["audience"] = audience

    ready = len(goal.strip()) >= 20
    if not ready:
        st.caption("Please write at least 20 characters describing your goal to proceed.")

    _nav_buttons(can_next=ready)

    if ready:
        _ai_coach(
            f"The user wants to: {goal}. They chose {analysis_type} for {audience}. "
            "Give a quick tip on how to sharpen this question.",
            "s1",
        )


# ---------------------------------------------------------------------------
# Stage 2 - Upload Your Data
# ---------------------------------------------------------------------------

def render_stage_2():
    st.markdown("## Stage 2: Upload Your Data")
    st.markdown("Provide a dataset to analyze. Upload your own file or pick a sample dataset.")

    tab_upload, tab_sample = st.tabs(["\U0001F4C1 Upload File", "\U0001F4E6 Sample Dataset"])

    df = None

    with tab_upload:
        uploaded = st.file_uploader(
            "Upload CSV, Excel, or JSON",
            type=["csv", "xlsx", "xls", "json"],
            key="guide_file_upload",
        )
        if uploaded:
            try:
                if uploaded.name.endswith(".csv"):
                    df = pd.read_csv(uploaded)
                elif uploaded.name.endswith((".xlsx", ".xls")):
                    df = pd.read_excel(uploaded)
                elif uploaded.name.endswith(".json"):
                    df = pd.read_json(uploaded)
            except Exception as e:
                st.error(f"Could not read file: {e}")

    with tab_sample:
        catalog = get_dataset_catalog()
        category = st.selectbox("Category", list(catalog.keys()), key="guide_cat")
        datasets = catalog[category]
        names = [d["name"] for d in datasets]
        choice = st.selectbox("Dataset", names, key="guide_ds")
        selected = next(d for d in datasets if d["name"] == choice)
        st.caption(selected["description"])
        if st.button("Load Sample Dataset", key="guide_load_sample"):
            with st.spinner("Fetching dataset..."):
                fetched, err = fetch_data_from_url(selected["url"])
            if fetched is not None:
                df = fetched
                st.success(f"Loaded {choice} ({len(df):,} rows)")
            else:
                st.error(f"Failed to load: {err}")

    # If we got a df from either source, store it
    if df is not None:
        st.session_state.guide_data["df"] = df
        st.session_state.working_df = df.copy()
        st.session_state.raw_df = df.copy()

    # Show preview of loaded data
    stored_df = st.session_state.guide_data.get("df")
    if stored_df is not None:
        st.markdown("#### Data Preview")
        st.dataframe(stored_df.head(10), use_container_width=True)
        st.caption(f"{len(stored_df):,} rows x {len(stored_df.columns)} columns")

    # Authorization checkbox
    authorized = st.checkbox(
        "I confirm I am authorized to analyze this data",
        value=st.session_state.guide_data.get("authorized", False),
        key="guide_auth_check",
    )
    st.session_state.guide_data["authorized"] = authorized

    can_proceed = stored_df is not None and authorized
    _nav_buttons(can_next=can_proceed)


# ---------------------------------------------------------------------------
# Stage 3 - Understand (Profile)
# ---------------------------------------------------------------------------

def render_stage_3():
    st.markdown("## Stage 3: Understand Your Data")
    st.markdown("Auto-profiling your dataset to identify structure, quality, and patterns.")

    df = st.session_state.working_df
    if df is None:
        st.warning("No data loaded. Please go back to Stage 2.")
        _nav_buttons(can_next=False)
        return

    # Quality report
    quality = generate_data_quality_report(df)
    score = quality.get("completeness_score", 100)
    dup_pct = quality.get("duplicate_percentage", 0)
    overall_score = max(0, score - dup_pct * 0.5)

    # Gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=overall_score,
        title={"text": "Data Quality Score"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#00D4FF"},
            "steps": [
                {"range": [0, 50], "color": "rgba(239,68,68,0.2)"},
                {"range": [50, 80], "color": "rgba(245,158,11,0.2)"},
                {"range": [80, 100], "color": "rgba(16,185,129,0.2)"},
            ],
        },
    ))
    fig.update_layout(
        height=250,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#F0F4F8",
    )
    st.plotly_chart(fig, use_container_width=True)

    if overall_score < 50:
        st.warning(
            "Quality score is below 50. The cleaning stage will help address issues."
        )

    # Per-column stats
    st.markdown("#### Column Statistics")
    col_data = []
    for col, info in quality["columns"].items():
        col_data.append({
            "Column": col,
            "Type": info["dtype"],
            "Non-Null": info["non_null_count"],
            "Null %": info["null_percentage"],
            "Unique": info["unique_count"],
        })
    st.dataframe(pd.DataFrame(col_data), use_container_width=True, hide_index=True)

    # Metrics row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{quality['total_rows']:,}")
    c2.metric("Columns", quality["total_columns"])
    c3.metric("Duplicates", f"{quality['duplicate_rows']:,}")
    c4.metric("Completeness", f"{score:.1f}%")

    st.session_state.guide_data["quality_score"] = overall_score
    st.session_state.guide_data["quality_report"] = quality

    # AI coaching
    _ai_coach(
        f"Dataset has {quality['total_rows']} rows, {quality['total_columns']} cols, "
        f"quality score {overall_score:.0f}%, {quality['duplicate_rows']} duplicates. "
        "Give a brief coaching tip about what to look for before cleaning.",
        "s3",
    )

    _nav_buttons(can_next=True)


# ---------------------------------------------------------------------------
# Stage 4 - Clean
# ---------------------------------------------------------------------------

def render_stage_4():
    st.markdown("## Stage 4: Clean Your Data")
    st.markdown("Address data quality issues one at a time. Each fix is tracked and reversible.")

    df = st.session_state.working_df
    if df is None:
        st.warning("No data loaded. Please go back to Stage 2.")
        _nav_buttons(can_next=False)
        return

    # Build issue queue
    issues = []
    # Duplicates
    dup_count = int(df.duplicated().sum())
    if dup_count > 0:
        issues.append({"type": "duplicates", "label": f"Duplicate rows ({dup_count})", "count": dup_count})

    # Null columns sorted by severity
    for col in df.columns:
        null_pct = df[col].isnull().sum() / len(df) * 100
        if null_pct > 0:
            issues.append({
                "type": "nulls",
                "column": col,
                "label": f"Missing values in '{col}' ({null_pct:.1f}%)",
                "pct": null_pct,
            })
    issues_nulls = [i for i in issues if i["type"] == "nulls"]
    issues_nulls.sort(key=lambda x: x["pct"], reverse=True)

    # Outlier columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    outlier_issues = []
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        if IQR > 0:
            mask = (df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)
            out_count = int(mask.sum())
            if out_count > 0:
                outlier_issues.append({
                    "type": "outliers",
                    "column": col,
                    "label": f"Outliers in '{col}' ({out_count} rows)",
                    "count": out_count,
                })

    all_issues = [i for i in issues if i["type"] == "duplicates"] + issues_nulls + outlier_issues

    # Track which issue we are on
    if "guide_issue_idx" not in st.session_state:
        st.session_state.guide_issue_idx = 0

    idx = st.session_state.guide_issue_idx

    # Before/after metrics
    raw_rows = len(st.session_state.raw_df) if st.session_state.raw_df is not None else len(df)
    m1, m2, m3 = st.columns(3)
    m1.metric("Original Rows", f"{raw_rows:,}")
    m2.metric("Current Rows", f"{len(df):,}")
    m3.metric("Issues Remaining", max(0, len(all_issues) - idx))

    if idx >= len(all_issues) or len(all_issues) == 0:
        st.success("All detected issues have been addressed (or none existed).")
        if st.button("Reset Issue Queue", key="guide_reset_issues"):
            st.session_state.guide_issue_idx = 0
            st.rerun()
        _nav_buttons(can_next=True)
        return

    issue = all_issues[idx]
    st.markdown(f"#### Issue {idx + 1} of {len(all_issues)}: {issue['label']}")

    action = st.radio(
        "How would you like to handle this?",
        ["Fix it (recommended)", "Skip for now"],
        key=f"guide_action_{idx}",
    )

    if st.button("Apply", key=f"guide_apply_{idx}", type="primary"):
        if action == "Fix it (recommended)":
            if issue["type"] == "duplicates":
                apply_cleaning_step("Remove duplicates", remove_duplicates)
            elif issue["type"] == "nulls":
                col = issue["column"]
                if df[col].dtype in ["int64", "float64"]:
                    apply_cleaning_step(f"Fill missing ({col}, median)", fill_missing, col, "median")
                else:
                    apply_cleaning_step(f"Fill missing ({col}, mode)", fill_missing, col, "mode")
            elif issue["type"] == "outliers":
                col = issue["column"]
                apply_cleaning_step(f"Remove outliers ({col})", remove_outliers_iqr, col)
            # Refresh df reference
            st.session_state.guide_data["df"] = st.session_state.working_df
        st.session_state.guide_issue_idx += 1
        st.rerun()

    st.markdown("---")
    if st.button("I'm Done Cleaning - Skip Remaining Issues", key="guide_done_clean"):
        st.session_state.guide_issue_idx = len(all_issues)
        st.rerun()

    _nav_buttons(can_next=False)


# ---------------------------------------------------------------------------
# Stage 5 - Explore & Analyse
# ---------------------------------------------------------------------------

def render_stage_5():
    st.markdown("## Stage 5: Explore & Analyse")
    st.markdown("Auto-selected analyses based on your data types. Review each visualization.")

    df = st.session_state.working_df
    if df is None:
        st.warning("No data loaded. Please go back to Stage 2.")
        _nav_buttons(can_next=False)
        return

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    analyses_done = []

    # 1. Distribution of first numeric column
    if numeric_cols:
        col = numeric_cols[0]
        st.markdown(f"#### Distribution of `{col}`")
        st.markdown(f"This histogram shows how values of **{col}** are distributed across the dataset.")
        fig = create_histogram(df, col, f"Distribution of {col}")
        st.plotly_chart(fig, use_container_width=True)
        analyses_done.append(f"Distribution of {col}")

    # 2. Correlation heatmap
    if len(numeric_cols) >= 2:
        st.markdown("#### Correlation Heatmap")
        st.markdown("Shows relationships between numeric variables. Values near +1 or -1 indicate strong correlation.")
        corr = df[numeric_cols].corr()
        fig = create_heatmap(corr, "Correlation Matrix")
        st.plotly_chart(fig, use_container_width=True)
        analyses_done.append("Correlation heatmap")

    # 3. Scatter plot of top-2 correlated columns
    if len(numeric_cols) >= 2:
        corr_matrix = df[numeric_cols].corr().abs()
        np.fill_diagonal(corr_matrix.values, 0)
        max_pair = corr_matrix.stack().idxmax()
        x_col, y_col = max_pair
        st.markdown(f"#### Scatter: `{x_col}` vs `{y_col}`")
        st.markdown(f"These two variables have the strongest correlation in your data.")
        fig = create_scatter_plot(df, x_col, y_col, f"{x_col} vs {y_col}")
        st.plotly_chart(fig, use_container_width=True)
        analyses_done.append(f"Scatter: {x_col} vs {y_col}")

    # 4. Bar chart of first categorical column value counts
    if categorical_cols:
        col = categorical_cols[0]
        counts = df[col].value_counts().head(15).reset_index()
        counts.columns = [col, "Count"]
        st.markdown(f"#### Top Values in `{col}`")
        st.markdown(f"Bar chart showing the most common values in the **{col}** column.")
        fig = create_bar_chart(counts, col, "Count", f"Top Values: {col}")
        st.plotly_chart(fig, use_container_width=True)
        analyses_done.append(f"Bar chart of {col}")

    if not analyses_done:
        st.info("No suitable columns found for automatic analysis.")

    # Build summary text
    st.session_state.guide_data["analysis_summary"] = "; ".join(analyses_done)

    # Reviewed checkbox
    reviewed = st.checkbox(
        "I have reviewed all visualizations above",
        value=st.session_state.guide_data.get("explored_reviewed", False),
        key="guide_explored_check",
    )
    st.session_state.guide_data["explored_reviewed"] = reviewed

    _nav_buttons(can_next=reviewed)


# ---------------------------------------------------------------------------
# Stage 6 - Generate Insights
# ---------------------------------------------------------------------------

def render_stage_6():
    st.markdown("## Stage 6: Generate Insights")
    st.markdown("AI-powered analysis and rule-based findings for your cleaned dataset.")

    df = st.session_state.working_df
    if df is None:
        st.warning("No data loaded. Please go back to Stage 2.")
        _nav_buttons(can_next=False)
        return

    api_key = get_api_key()

    # Try AI insights
    ai_insights = None
    if api_key:
        stats = generate_summary_stats(df)
        summary_md = format_summary_as_markdown(df, stats)
        goal = st.session_state.guide_data.get("goal", "General exploration")
        prompt = (
            f"Analyze this dataset for the user whose goal is: {goal}\n\n"
            f"{summary_md}\n\nFirst 5 rows:\n{df.head(5).to_string()}"
        )
        system = (
            "You are a senior data analyst. Provide structured insights: "
            "Key Findings (bullet points with numbers), Patterns, Concerns, "
            "and Actionable Recommendations. Be specific and cite figures."
        )
        with st.spinner("Generating AI insights..."):
            text, err = generate_content(prompt, api_key=api_key, system_instruction=system)
        if text:
            ai_insights = text

    if ai_insights:
        st.markdown("### AI-Generated Insights")
        st.markdown(ai_insights)
    else:
        st.markdown("### Rule-Based Insights")
        fallback = generate_insights_fallback(df)
        for category, items in fallback.items():
            if items:
                st.markdown(f"**{category.replace('_', ' ').title()}**")
                for item in items:
                    st.markdown(f"- {item}")

    # Recommendations
    st.markdown("### Recommendations")
    recs = generate_recommendations(df)
    for rec in recs:
        st.markdown(f"- {rec}")

    # User observations
    st.markdown("### Your Observations")
    user_notes = st.text_area(
        "Add any notes or observations of your own:",
        value=st.session_state.guide_data.get("user_notes", ""),
        key="guide_user_notes",
        height=100,
    )
    st.session_state.guide_data["user_notes"] = user_notes

    reviewed = st.checkbox(
        "I have reviewed the insights above",
        value=st.session_state.guide_data.get("insights_reviewed", False),
        key="guide_insights_check",
    )
    st.session_state.guide_data["insights_reviewed"] = reviewed

    _nav_buttons(can_next=reviewed)


# ---------------------------------------------------------------------------
# Stage 7 - Report & Share
# ---------------------------------------------------------------------------

def render_stage_7():
    st.markdown("## Stage 7: Report & Share")
    st.markdown("Generate a professional HTML report summarizing your entire analysis.")

    df = st.session_state.working_df
    if df is None:
        st.warning("No data loaded.")
        _nav_buttons(can_next=False)
        return

    # Recap
    st.markdown("### Analysis Recap")
    goal = st.session_state.guide_data.get("goal", "N/A")
    analysis_type = st.session_state.guide_data.get("analysis_type", "N/A")
    audience = st.session_state.guide_data.get("audience", "N/A")
    quality_score = st.session_state.guide_data.get("quality_score", "N/A")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Goal:** {goal}")
        st.markdown(f"**Analysis Type:** {analysis_type}")
    with c2:
        st.markdown(f"**Audience:** {audience}")
        st.markdown(f"**Quality Score:** {quality_score}")

    st.markdown("---")

    # Generate report
    api_key = get_api_key()
    title = f"DataPrism Analysis: {goal[:60]}"

    if st.button("Generate Report", type="primary", key="guide_gen_report"):
        with st.spinner("Building your report..."):
            report_html = generate_html_report(
                df,
                title=title,
                include_ai_summary=bool(api_key),
                api_key=api_key,
            )
            st.session_state.guide_data["report_html"] = report_html
        st.success("Report generated successfully!")

    report_html = st.session_state.guide_data.get("report_html")
    if report_html:
        st.download_button(
            label="\U0001F4E5 Download HTML Report",
            data=report_html,
            file_name="dataprism_guided_report.html",
            mime="text/html",
            type="primary",
            key="guide_download_report",
        )

    st.markdown("---")

    # Congratulations
    st.markdown(
        """
        ### Congratulations!

        You have completed the full guided analysis workflow:

        1. Defined a clear research question
        2. Loaded and authorized your data
        3. Profiled data quality
        4. Cleaned and transformed the dataset
        5. Explored key patterns visually
        6. Generated AI-powered insights
        7. Produced a shareable report

        **Learning moment:** Repeating this cycle with different questions or datasets
        builds your analytical intuition over time. Each pass helps you spot patterns
        faster and ask better questions.
        """
    )

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Start Over", key="guide_restart"):
            st.session_state.guide_stage = 1
            st.session_state.guide_data = {}
            st.session_state.guide_issue_idx = 0
            st.rerun()
    with c2:
        st.page_link("pages/2_Upload_and_Analyze.py", label="Continue in Upload & Analyze", icon="\U0001F4C1")


# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------

_render_progress_bar()

stage = st.session_state.guide_stage
if stage == 1:
    render_stage_1()
elif stage == 2:
    render_stage_2()
elif stage == 3:
    render_stage_3()
elif stage == 4:
    render_stage_4()
elif stage == 5:
    render_stage_5()
elif stage == 6:
    render_stage_6()
elif stage == 7:
    render_stage_7()
else:
    st.session_state.guide_stage = 1
    st.rerun()
