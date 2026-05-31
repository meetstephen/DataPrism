"""
AI Insights Engine - Generate automated insights with Google Gemini or rule-based fallback.
"""

import streamlit as st
st.set_page_config(page_title="AI Insights Engine", page_icon="\U0001f4a0", layout="wide")
from utils.styles import inject_global_css, render_insight_card
inject_global_css()

import pandas as pd
from utils.data_loader import ensure_builtin_data
from utils.ai_client import get_api_key, generate_content, GEMINI_MODEL
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
from utils.ai_intelligence import (
    generate_insight_cards,
    explain_this_number,
    generate_executive_summary_brief,
)

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
        st.stop()
elif data_source == "Cleaned Data":
    if st.session_state.get("working_df") is not None:
        df = st.session_state.working_df.copy()
        st.info(f"Using cleaned dataset: {len(df)} rows, {len(df.columns)} columns")
    else:
        st.warning("No cleaned data available. Go to 'Data Cleaning' to clean a dataset.")
        st.stop()
else:
    if st.session_state.get("uploaded_df") is not None:
        df = st.session_state.uploaded_df.copy()
        st.info(f"Using uploaded dataset: {len(df)} rows, {len(df.columns)} columns")
    else:
        st.warning("No data has been uploaded yet. Upload a file above or go to 'Upload & Analyze'.")
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
                    st.markdown(ai_result)
                else:
                    st.warning(
                        "AI analysis is temporarily unavailable. "
                        "Please check your Gemini API key. "
                        "Falling back to rule-based analysis."
                    )
                    insights = generate_insights_fallback(df)

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

                insights = generate_insights_fallback(df)

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

            # Auto-Insight Cards (AI-powered)
            st.markdown("### Auto-Insight Cards")
            if api_key and api_key.strip():
                with st.spinner("Generating insight cards..."):
                    summary_stats_cards = generate_summary_stats(df)
                    summary_text_cards = format_summary_as_markdown(df, summary_stats_cards)
                    cards, cards_err = generate_insight_cards(summary_text_cards, api_key)
                    if cards_err:
                        st.warning(f"Insight cards partially unavailable: {cards_err}")
                    rendered_any = False
                    for finding in cards.get("findings", []):
                        render_insight_card("finding", finding)
                        rendered_any = True
                    for risk in cards.get("risks", []):
                        render_insight_card("risk", risk)
                        rendered_any = True
                    for opp in cards.get("opportunities", []):
                        render_insight_card("opportunity", opp)
                        rendered_any = True
                    for rec_item in cards.get("recommendations", []):
                        render_insight_card("recommendation", rec_item)
                        rendered_any = True
                    if not rendered_any:
                        st.info("No insight cards generated.")
            else:
                st.info("Add a Gemini API key to generate AI-powered insight cards.")

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

    # --- Explain This Number ---
    st.markdown("---")
    st.markdown("### Explain This Number")
    st.caption("Enter a value from your data and get an AI-powered explanation of what it means in context.")

    etn_col1, etn_col2 = st.columns(2)
    with etn_col1:
        etn_value = st.text_input("Value to explain", key="etn_value", placeholder="e.g. 42000")
    with etn_col2:
        etn_column = st.selectbox("Column context", df.columns.tolist(), key="etn_col")

    if st.button("Explain", key="btn_explain_number"):
        if not etn_value:
            st.warning("Please enter a value to explain.")
        elif not api_key:
            st.warning("A Gemini API key is required for this feature. Add one in the sidebar.")
        else:
            try:
                with st.spinner("Generating explanation..."):
                    explanation, err = explain_this_number(etn_value, etn_column, df, api_key)
                    if explanation:
                        st.markdown(explanation)
                    elif err:
                        st.error(f"Explanation failed: {err}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # --- Executive Summary Generator ---
    st.markdown("---")
    st.markdown("### Executive Summary Generator")
    st.caption("Generate a formal 400-word executive brief covering situation, metrics, findings, risks, and recommendations.")

    if st.button("Generate Executive Summary", key="btn_exec_summary"):
        if not api_key:
            st.warning("A Gemini API key is required for executive summary generation. Add one in the sidebar.")
        else:
            try:
                with st.spinner("Generating executive summary..."):
                    summary, err = generate_executive_summary_brief(df, api_key)
                    if summary:
                        with st.expander("Executive Summary Brief", expanded=True):
                            st.markdown(summary)
                    elif err:
                        st.error(f"Summary generation failed: {err}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
