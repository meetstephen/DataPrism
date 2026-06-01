"""
AI Insights Engine - Generate automated insights with Google Gemini or rule-based fallback.
"""

import streamlit as st
st.set_page_config(page_title="AI Insights Engine", page_icon="\U0001f4a0", layout="wide")
from utils.styles import inject_global_css, compute_confidence, render_confidence_badge, render_sidebar_nav
inject_global_css()
render_sidebar_nav()

import pandas as pd
from utils.data_loader import ensure_builtin_data
from utils.ai_client import get_api_key, generate_content, GEMINI_MODEL
from utils.supabase_client import is_configured
from utils import database as db
from utils.ai_insights import (
    generate_insights_gemini,
    generate_insights_fallback,
    generate_summary_stats,
    format_summary_as_markdown,
    detect_anomalies,
    detect_trends,
    generate_recommendations,
    generate_data_quality_report
)


def _insights_to_markdown(insights):
    """Convert a rule-based insights dict into a single markdown string."""
    parts = []
    sections = [
        ("Key Findings", insights.get("key_findings")),
        ("Patterns Detected", insights.get("patterns")),
        ("Concerns", insights.get("concerns")),
        ("Recommendations", insights.get("recommendations")),
    ]
    for heading, items in sections:
        if items:
            parts.append(f"#### {heading}")
            parts.extend(f"- {item}" for item in items)
    return "\n".join(parts)

st.title("\U0001F916 AI Insights Engine")
st.markdown("Generate automated insights from your data using **Google Gemini 2.5 Flash** or rule-based analysis.")

# Sidebar - API Key and data source
with st.sidebar:
    st.header("Configuration")

    api_key = get_api_key()
    if api_key:
        st.success("API key loaded")
    else:
        key_input = st.text_input(
            "Google Gemini API Key (optional)",
            type="password",
            help="Enter your Google Gemini API key for AI-powered insights. "
                 "Get one free at https://aistudio.google.com/apikey. "
                 "Leave empty to use rule-based analysis."
        )
        if key_input and key_input.strip():
            st.session_state.gemini_api_key = key_input.strip()
            api_key = get_api_key()

    st.markdown("---")
    st.markdown(
        "**Note:** Without an API key, the engine uses rule-based analysis "
        "to generate insights. With a Gemini API key, you get powerful "
        "AI-generated natural language insights from Google's latest model."
    )

# Data source selector
st.markdown("### Select Data Source")

# Quick upload option
with st.expander("📁 Upload a new file for analysis", expanded=False):
    ai_upload = st.file_uploader(
        "Upload CSV or Excel",
        type=["csv", "xlsx", "xls"],
        key="ai_insights_file_uploader",
        help="Upload a fresh dataset directly here for AI analysis."
    )
    if ai_upload is not None:
        try:
            if ai_upload.name.endswith(".csv"):
                new_df = pd.read_csv(ai_upload)
            else:
                new_df = pd.read_excel(ai_upload)
            if not new_df.empty and len(new_df.columns) >= 1:
                st.session_state.uploaded_df = new_df
                st.success(f"✅ Loaded **{ai_upload.name}** ({len(new_df):,} rows x {len(new_df.columns)} columns)")
            else:
                st.error("The uploaded file is empty or has no columns.")
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

data_source_options = ["Built-in Community College Data"]
if st.session_state.get("uploaded_df") is not None:
    data_source_options.append("Uploaded Data")
if "online_df" in st.session_state and st.session_state.online_df is not None:
    data_source_options.append("Online Data")
if st.session_state.get("working_df") is not None:
    data_source_options.append("Cleaned Data")
data_source = st.radio(
    "Choose data to analyze:",
    data_source_options,
    horizontal=True
)

# Load appropriate dataset
df = None
if data_source == "Built-in Community College Data":
    df = ensure_builtin_data().copy()
    st.info(f"Using built-in dataset: {len(df)} rows, {len(df.columns)} columns")
elif data_source == "Online Data":
    if "online_df" in st.session_state and st.session_state.online_df is not None:
        df = st.session_state.online_df.copy()
        st.info(f"Using online dataset: {len(df)} rows, {len(df.columns)} columns")
    else:
        st.warning("No online data available. Go to 'Online Data Explorer' to fetch data.")
        st.page_link("pages/6_Online_Data_Explorer.py", label="\U0001F310 Go to Online Data Explorer", icon="\U0001F310")
        st.stop()
elif data_source == "Cleaned Data":
    if st.session_state.get("working_df") is not None:
        df = st.session_state.working_df.copy()
        st.info(f"Using cleaned dataset: {len(df)} rows, {len(df.columns)} columns")
    else:
        st.warning("No cleaned data available. Go to 'Data Cleaning' to clean a dataset.")
        st.page_link("pages/3_Data_Cleaning.py", label="\U0001f9f9 Go to Data Cleaning", icon="\U0001f9f9")
        st.stop()
else:
    if st.session_state.get("uploaded_df") is not None:
        df = st.session_state.uploaded_df.copy()
        st.info(f"Using uploaded dataset: {len(df)} rows, {len(df.columns)} columns")
    else:
        st.warning("No data has been uploaded yet. Upload a file above or go to 'Upload & Analyze'.")
        st.page_link("pages/2_Upload_and_Analyze.py", label="\U0001F4C1 Go to Upload & Analyze", icon="\U0001F4C1")
        st.stop()

if df is not None:
    # Generate Insights button
    st.markdown("---")

    if st.button("Generate Insights", type="primary", use_container_width=True):
        with st.spinner("Analyzing data..."):
            # Generate insights
            if api_key and api_key.strip():
                st.markdown("### \u2728 AI-Powered Insights (Gemini 2.5 Flash)")
                st.caption("Using Google Gemini for analysis")

                # Prepare summary for AI
                summary_stats = generate_summary_stats(df)
                summary_text = format_summary_as_markdown(df, summary_stats)
                ai_result = generate_insights_gemini(summary_text, api_key)

                if ai_result is not None:
                    level, score, reasons = compute_confidence(df, source="ai")
                    render_confidence_badge(level, score, source_label="AI-generated", reasons=reasons)
                    st.markdown(ai_result)
                    st.session_state["last_insight"] = {
                        "content": ai_result, "source": "ai",
                        "level": level, "score": score, "dataset_name": str(data_source),
                    }
                else:
                    st.warning(
                        "AI analysis is temporarily unavailable. "
                        "Please check your Gemini API key. "
                        "Falling back to rule-based analysis."
                    )
                    level, score, reasons = compute_confidence(df, source="rule_based")
                    render_confidence_badge(level, score, source_label="Rule-based", reasons=reasons)
                    insights = generate_insights_fallback(df)
                    st.session_state["last_insight"] = {
                        "content": _insights_to_markdown(insights), "source": "rule_based",
                        "level": level, "score": score, "dataset_name": str(data_source),
                    }

                    st.markdown("#### Key Findings")
                    for finding in insights.get("key_findings", []):
                        st.markdown(f"- {finding}")

                    if insights.get("patterns"):
                        st.markdown("#### Patterns Detected")
                        for pattern in insights["patterns"]:
                            st.markdown(f"- {pattern}")

                    if insights.get("concerns"):
                        st.markdown("#### Concerns")
                        for concern in insights["concerns"]:
                            st.markdown(f"- \u26A0\uFE0F {concern}")

                    if insights.get("recommendations"):
                        st.markdown("#### Recommendations")
                        for rec in insights["recommendations"]:
                            st.markdown(f"- {rec}")
            else:
                st.markdown("### Rule-Based Insights")
                st.caption("Using automated rule-based analysis (no API key provided)")

                level, score, reasons = compute_confidence(df, source="rule_based")
                render_confidence_badge(level, score, source_label="Rule-based", reasons=reasons)

                insights = generate_insights_fallback(df)
                st.session_state["last_insight"] = {
                    "content": _insights_to_markdown(insights), "source": "rule_based",
                    "level": level, "score": score, "dataset_name": str(data_source),
                }

                # Key Findings
                st.markdown("#### Key Findings")
                for finding in insights.get("key_findings", []):
                    st.markdown(f"- {finding}")

                # Patterns
                if insights.get("patterns"):
                    st.markdown("#### Patterns Detected")
                    for pattern in insights["patterns"]:
                        st.markdown(f"- {pattern}")

                # Concerns
                if insights.get("concerns"):
                    st.markdown("#### Concerns")
                    for concern in insights["concerns"]:
                        st.markdown(f"- \u26A0\uFE0F {concern}")

                # Recommendations from fallback
                if insights.get("recommendations"):
                    st.markdown("#### Recommendations")
                    for rec in insights["recommendations"]:
                        st.markdown(f"- {rec}")

            st.markdown("---")

            # Trend Analysis
            st.markdown("### Trend Analysis")
            with st.expander("View Trend Details", expanded=True):
                trends = detect_trends(df, date_col="Year", value_col="Course_Cost")
                if trends:
                    if "overall_trend" in trends:
                        st.markdown(f"**Overall Trend:** {trends['overall_trend'].capitalize()}")
                        st.markdown(f"**Total Change:** {trends.get('total_change_pct', 'N/A')}%")
                    if "yearly_averages" in trends:
                        st.markdown("**Yearly Averages:**")
                        avg_df = pd.DataFrame(
                            list(trends["yearly_averages"].items()),
                            columns=["Year", "Average"]
                        )
                        st.dataframe(avg_df, use_container_width=True)
                    # Show other auto-detected trends
                    for key, value in trends.items():
                        if key not in ["overall_trend", "total_change_pct", "yearly_averages", "year_over_year_change"]:
                            st.markdown(f"**{key}:**")
                            if isinstance(value, dict):
                                st.json(value)
                            else:
                                st.write(value)
                else:
                    st.info("No clear trends detected in the data.")

            # Anomaly Detection
            st.markdown("### Anomaly Detection")
            with st.expander("View Anomaly Details", expanded=True):
                anomalies = detect_anomalies(df)
                if anomalies:
                    for col_name, info in anomalies.items():
                        st.markdown(
                            f"**{col_name}:** {info['count']} outliers detected "
                            f"(bounds: [{info['lower_bound']}, {info['upper_bound']}])"
                        )
                        if not info["outlier_rows"].empty:
                            st.dataframe(info["outlier_rows"].head(5), use_container_width=True)
                else:
                    st.success("No significant anomalies detected.")

            # Recommendations
            st.markdown("### Recommendations")
            with st.expander("View Recommendations", expanded=True):
                recommendations = generate_recommendations(df)
                for idx, rec in enumerate(recommendations, 1):
                    st.markdown(f"{idx}. {rec}")

    else:
        st.markdown("---")
        st.markdown("Click **Generate Insights** to analyze the selected data.")
        st.markdown(
            """
            The engine will provide:
            - **Key Findings** - Important observations about your data
            - **Trend Analysis** - Year-over-year or sequential patterns
            - **Anomaly Detection** - Outliers identified using statistical methods
            - **Recommendations** - Actionable suggestions based on data patterns
            """
        )

    # Save the most recent insight to the cloud (optional)
    last = st.session_state.get("last_insight")
    if last:
        st.markdown("---")
        if is_configured():
            if st.button("\u2601\uFE0F Save this insight to cloud", key="ai_cloud_save"):
                ok, msg = db.save_insight(
                    last["content"], last.get("dataset_name", ""), last.get("source", "ai"),
                    last.get("level", ""), last.get("score", 0),
                )
                st.success(msg) if ok else st.error(msg)
                if ok:
                    try:
                        from utils.auth import log_user_activity
                        log_user_activity("insight_saved", page="ai_insights")
                    except Exception:
                        pass
        else:
            st.caption(
                "\u2601\uFE0F Tip: connect a database (see SUPABASE_SETUP.md) to save insights to the cloud."
            )

    # --- Enterprise: Auto-Insight Cards ---
    st.markdown("---")
    st.markdown("### \U0001F4A1 Auto-Insight Cards")
    st.markdown("AI-powered insight cards highlighting key findings, risks, and opportunities.")

    from utils.ai_intelligence import generate_insight_cards, explain_this_number, generate_executive_summary_brief
    from utils.styles import render_insight_card

    if st.button("Generate Insight Cards", key="gen_insight_cards"):
        with st.spinner("Generating insight cards..."):
            cards = generate_insight_cards(df, api_key=api_key)
            if cards:
                for card in cards:
                    render_insight_card(card.get("type", "finding"), card.get("content", ""))
                st.session_state["_insight_cards"] = cards
            else:
                st.info("No notable insights detected for this dataset.")

    stored_cards = st.session_state.get("_insight_cards")
    if stored_cards and not st.session_state.get("_cards_just_generated"):
        for card in stored_cards:
            render_insight_card(card.get("type", "finding"), card.get("content", ""))

    # --- Enterprise: Explain This Number ---
    st.markdown("---")
    st.markdown("### \U0001F50D Explain This Number")
    st.markdown("Select a value from a numeric column to get a plain-language explanation of its context.")

    numeric_cols_explain = df.select_dtypes(include=["number"]).columns.tolist()
    if numeric_cols_explain:
        exp_col1, exp_col2 = st.columns(2)
        with exp_col1:
            explain_col = st.selectbox("Column:", numeric_cols_explain, key="explain_col_sel")
        with exp_col2:
            if explain_col:
                col_min = float(df[explain_col].min())
                col_max = float(df[explain_col].max())
                explain_val = st.number_input(
                    "Value to explain:",
                    min_value=col_min,
                    max_value=col_max,
                    value=float(df[explain_col].median()),
                    key="explain_val_input",
                )
        if st.button("Explain", type="primary", key="explain_btn"):
            explanation = explain_this_number(df, explain_col, explain_val, api_key=api_key)
            st.info(explanation)
    else:
        st.info("No numeric columns available for explanation.")

    # --- Enterprise: Executive Summary Brief ---
    st.markdown("---")
    st.markdown("### \U0001F4DD Executive Summary")
    st.markdown("Generate a concise executive summary for stakeholders.")

    goal_text = st.text_input(
        "Analysis goal (optional):", placeholder="e.g. Understand enrollment trends",
        key="exec_summary_goal",
    )
    if st.button("Generate Executive Summary", type="primary", key="gen_exec_summary"):
        with st.spinner("Generating executive summary..."):
            summary = generate_executive_summary_brief(
                df, goal=goal_text or "General analysis", api_key=api_key
            )
            st.markdown(summary)
