"""
AI Insights Engine - Generate automated insights with Google Gemini or rule-based fallback.
"""

import streamlit as st
import pandas as pd
from utils.data_generator import generate_dataset
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

st.title("\U0001F916 AI Insights Engine")
st.markdown("Generate automated insights from your data using **Google Gemini 2.5 Flash** or rule-based analysis.")

# Sidebar - API Key and data source
with st.sidebar:
    st.header("Configuration")

    api_key = st.text_input(
        "Google Gemini API Key (optional)",
        type="password",
        help="Enter your Google Gemini API key for AI-powered insights. "
             "Get one free at https://aistudio.google.com/apikey. "
             "Leave empty to use rule-based analysis."
    )

    st.markdown("---")
    st.markdown(
        "**Note:** Without an API key, the engine uses rule-based analysis "
        "to generate insights. With a Gemini API key, you get powerful "
        "AI-generated natural language insights from Google's latest model."
    )

# Data source selector
st.markdown("### Select Data Source")
data_source = st.radio(
    "Choose data to analyze:",
    ["Built-in Community College Data", "Uploaded Data"],
    horizontal=True
)

# Load appropriate dataset
df = None
if data_source == "Built-in Community College Data":
    if "df" not in st.session_state:
        st.session_state.df = generate_dataset()
    df = st.session_state.df.copy()
    st.info(f"Using built-in dataset: {len(df)} rows, {len(df.columns)} columns")
else:
    if "uploaded_df" in st.session_state:
        df = st.session_state.uploaded_df.copy()
        st.info(f"Using uploaded dataset: {len(df)} rows, {len(df.columns)} columns")
    else:
        st.warning("No data has been uploaded yet. Go to 'Upload & Analyze' to upload a file.")
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
