import streamlit as st
st.set_page_config(page_title="Expert Data Analyst", page_icon="\U0001F393", layout="wide")
from utils.styles import inject_global_css
inject_global_css()

import pandas as pd
import numpy as np
import plotly.express as px
from utils.visualizations import create_histogram, create_bar_chart, create_heatmap, create_scatter_plot
from utils.ai_insights import (
    generate_insights_gemini, generate_insights_fallback,
    generate_summary_stats, format_summary_as_markdown,
    detect_anomalies, detect_trends, generate_recommendations
)


def detect_data_domain(df):
    """
    Detect the domain/type of a dataset based on column names and data patterns.

    Returns:
        tuple: (domain_name, icon, description)
    """
    col_names_lower = [c.lower() for c in df.columns]
    col_names_str = " ".join(col_names_lower)

    # Financial indicators
    financial_keywords = ["revenue", "cost", "profit", "price", "budget", "sales",
                          "income", "expense", "margin", "tax", "payment", "invoice"]
    financial_score = sum(1 for kw in financial_keywords if kw in col_names_str)

    # Time-series indicators
    time_keywords = ["date", "year", "month", "quarter", "week", "timestamp", "period"]
    time_score = sum(1 for kw in time_keywords if kw in col_names_str)
    # Also check for datetime columns
    datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
    time_score += len(datetime_cols)

    # HR/People indicators
    hr_keywords = ["employee", "department", "salary", "hire", "performance",
                   "manager", "position", "tenure", "staff", "headcount"]
    hr_score = sum(1 for kw in hr_keywords if kw in col_names_str)

    # Survey indicators
    survey_keywords = ["rating", "score", "satisfaction", "survey", "feedback",
                       "response", "likert", "agree", "disagree"]
    survey_score = sum(1 for kw in survey_keywords if kw in col_names_str)
    # Check for Likert-scale patterns (values 1-5 or 1-7)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    for col in numeric_cols:
        unique_vals = df[col].dropna().unique()
        if len(unique_vals) <= 7 and len(unique_vals) >= 3:
            if all(1 <= v <= 7 for v in unique_vals):
                survey_score += 1

    # Education indicators
    edu_keywords = ["student", "grade", "course", "enrollment", "gpa", "school",
                    "class", "professor", "major", "semester", "credit"]
    edu_score = sum(1 for kw in edu_keywords if kw in col_names_str)

    # Determine domain
    scores = {
        "Financial": financial_score,
        "Time-Series": time_score,
        "HR/People": hr_score,
        "Survey": survey_score,
        "Education": edu_score
    }

    max_domain = max(scores, key=scores.get)
    max_score = scores[max_domain]

    if max_score >= 2:
        domain_info = {
            "Financial": ("\U0001F4B0", "Financial/Business data detected. Analysis will focus on monetary trends, profitability, and cost optimization."),
            "Time-Series": ("\U0001F4C5", "Time-series data detected. Analysis will focus on temporal patterns, seasonality, and trends."),
            "HR/People": ("\U0001F465", "HR/People data detected. Analysis will focus on workforce metrics, compensation, and organizational patterns."),
            "Survey": ("\U0001F4CB", "Survey/Rating data detected. Analysis will focus on satisfaction scores, response distributions, and sentiment patterns."),
            "Education": ("\U0001F393", "Education data detected. Analysis will focus on academic performance, enrollment patterns, and institutional metrics.")
        }
        icon, desc = domain_info[max_domain]
        return max_domain, icon, desc
    else:
        return "Generic", "\U0001F4CA", "General dataset. Comprehensive statistical analysis will be performed across all variables."


st.title("\U0001F393 Expert Data Analyst")
st.markdown("""
Upload any data file and get comprehensive expert-level analysis.
Supports CSV, Excel, and Power BI exported data files (.csv, .xlsx, .xls).

**How to export from Power BI:**
1. In Power BI Desktop, go to your visual/table
2. Click "Export data" (or "More options" > "Export data")
3. Save as CSV or Excel format
4. Upload the exported file here
""")

st.markdown("---")

# File uploader (supports Power BI exports)
uploaded_file = st.file_uploader(
    "Upload your data file (CSV, Excel, Power BI export)",
    type=["csv", "xlsx", "xls"],
    help="Power BI: Export your visual as CSV or Excel, then upload here."
)

if uploaded_file:
    # Load with error handling
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        st.info("Ensure the file is a valid CSV or Excel file. For Power BI exports, use 'Export data' as CSV or Excel.")
        st.stop()

    if df.empty:
        st.warning("The uploaded file contains no data rows.")
        st.stop()

    if len(df.columns) < 1:
        st.warning("The uploaded file has no columns. Please check the file format.")
        st.stop()

    # Show data overview
    st.markdown("---")
    st.markdown("### \U0001F4CA Data Overview")

    memory_usage = df.memory_usage(deep=True).sum()
    if memory_usage > 1_000_000:
        memory_str = f"{memory_usage / 1_000_000:.1f} MB"
    else:
        memory_str = f"{memory_usage / 1_000:.1f} KB"

    total_cells = len(df) * len(df.columns)
    missing_cells = df.isnull().sum().sum()
    completeness = ((total_cells - missing_cells) / total_cells * 100) if total_cells > 0 else 100

    met_col1, met_col2, met_col3, met_col4 = st.columns(4)
    with met_col1:
        st.metric("Rows", f"{len(df):,}")
    with met_col2:
        st.metric("Columns", f"{len(df.columns)}")
    with met_col3:
        st.metric("Memory", memory_str)
    with met_col4:
        st.metric("Completeness", f"{completeness:.1f}%")

    with st.expander("Preview Data", expanded=False):
        st.dataframe(df.head(50), use_container_width=True)

    # Auto-detect data domain
    st.markdown("### \U0001F50D Data Domain Detection")
    domain_name, domain_icon, domain_desc = detect_data_domain(df)
    st.info(f"{domain_icon} **{domain_name} Data** - {domain_desc}")

    # Comprehensive profiling
    st.markdown("### \U0001F4CB Data Profiling")

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    prof_col1, prof_col2 = st.columns(2)
    with prof_col1:
        st.markdown(f"**Numeric columns:** {len(numeric_cols)}")
        if numeric_cols:
            st.dataframe(df[numeric_cols].describe().T.round(2), use_container_width=True)

    with prof_col2:
        st.markdown(f"**Categorical columns:** {len(categorical_cols)}")
        if categorical_cols:
            cat_stats = []
            for col in categorical_cols:
                cat_stats.append({
                    "Column": col,
                    "Unique": df[col].nunique(),
                    "Mode": str(df[col].mode().iloc[0]) if not df[col].mode().empty else "N/A",
                    "Null %": f"{df[col].isnull().sum() / len(df) * 100:.1f}%"
                })
            st.dataframe(pd.DataFrame(cat_stats), use_container_width=True)

    # Key insights (automatic)
    st.markdown("### \U0001F4A1 Key Insights")
    with st.spinner("Analyzing data patterns..."):
        fallback_insights = generate_insights_fallback(df)

    # Display insights by category
    if fallback_insights.get("key_findings"):
        st.markdown("**Key Findings:**")
        for finding in fallback_insights["key_findings"][:8]:
            st.markdown(f"- {finding}")

    if fallback_insights.get("patterns"):
        st.markdown("**Patterns Detected:**")
        for pattern in fallback_insights["patterns"][:5]:
            st.markdown(f"- {pattern}")

    if fallback_insights.get("concerns"):
        st.markdown("**Concerns:**")
        for concern in fallback_insights["concerns"][:5]:
            st.markdown(f"- \u26a0\ufe0f {concern}")

    # AI-powered analysis (optional)
    st.markdown("### \U0001F916 AI-Powered Analysis")
    api_key = None
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        api_key = st.sidebar.text_input("Gemini API Key (for AI features)", type="password",
                                        key="expert_analyst_api_key")

    if api_key:
        stats = generate_summary_stats(df)
        summary_text = format_summary_as_markdown(df, stats)

        if st.button("Generate AI Insights", type="primary"):
            with st.spinner("Generating AI-powered insights..."):
                ai_result = generate_insights_gemini(summary_text, api_key)
                if ai_result:
                    st.markdown(ai_result)
                else:
                    st.warning("AI analysis unavailable. Showing rule-based insights above.")
    else:
        st.info("Enter a Gemini API key in the sidebar to unlock AI-powered narrative insights.")

    # Ask a question about your data
    st.markdown("### \U0001F914 Ask About Your Data")
    question = st.text_input("Ask a question about your data:",
                             placeholder="e.g., What are the top performing categories?")
    if question:
        if st.button("Get Answer", key="ask_answer_btn"):
            if api_key:
                with st.spinner("Thinking..."):
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")

                        stats = generate_summary_stats(df)
                        summary_text = format_summary_as_markdown(df, stats)
                        sample_data = df.head(10).to_string()

                        prompt = (
                            f"Based on this dataset summary:\n\n{summary_text}\n\n"
                            f"Sample data:\n{sample_data}\n\n"
                            f"User question: {question}\n\n"
                            "Provide a clear, data-driven answer. Cite specific numbers where possible."
                        )
                        response = model.generate_content(prompt)
                        if response and response.text:
                            st.markdown(response.text)
                        else:
                            st.warning("Could not generate an answer. Try rephrasing your question.")
                    except Exception as e:
                        import logging
                        logging.warning(f"Gemini Q&A failed: {str(e)}")
                        st.warning("AI Q&A unavailable. Please check your API key.")
            else:
                # Rule-based answer attempt
                st.info("AI Q&A requires a Gemini API key. Showing basic data summary instead:")
                st.dataframe(df.describe(), use_container_width=True)

    # Visualizations (auto-generated)
    st.markdown("### \U0001F4C8 Auto-Generated Visualizations")

    if numeric_cols:
        viz_tabs = st.tabs(["Distributions", "Correlations", "Box Plots"])

        with viz_tabs[0]:
            viz_cols = st.columns(2)
            for i, col in enumerate(numeric_cols[:6]):
                with viz_cols[i % 2]:
                    try:
                        fig = create_histogram(df, col, f"Distribution of {col}")
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception:
                        pass

        with viz_tabs[1]:
            if len(numeric_cols) >= 2:
                try:
                    fig = create_heatmap(df[numeric_cols].corr(), "Correlation Matrix")
                    st.plotly_chart(fig, use_container_width=True)
                except Exception:
                    st.info("Could not generate correlation matrix.")

                # Scatter plot of top correlated pair
                if len(numeric_cols) >= 2:
                    try:
                        corr_matrix = df[numeric_cols].corr()
                        np.fill_diagonal(corr_matrix.values, 0)
                        max_idx = np.unravel_index(np.abs(corr_matrix.values).argmax(), corr_matrix.shape)
                        col_x = numeric_cols[max_idx[0]]
                        col_y = numeric_cols[max_idx[1]]
                        fig = create_scatter_plot(df, col_x, col_y, f"Top Correlation: {col_x} vs {col_y}")
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception:
                        pass

        with viz_tabs[2]:
            box_cols = st.columns(2)
            for i, col in enumerate(numeric_cols[:6]):
                with box_cols[i % 2]:
                    try:
                        fig = px.box(df, y=col, title=f"Box Plot: {col}",
                                     color_discrete_sequence=["#00D4FF"])
                        fig.update_layout(template="plotly_dark", height=350)
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception:
                        pass

    elif categorical_cols:
        for col in categorical_cols[:4]:
            try:
                fig = create_bar_chart(
                    df[col].value_counts().reset_index(),
                    x=col, y="count",
                    title=f"Distribution: {col}"
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                pass
    else:
        st.info("No suitable columns found for automatic visualization.")

    # Anomalies
    st.markdown("### \u26a0\ufe0f Anomaly Detection")
    anomalies = detect_anomalies(df)
    if anomalies:
        for col, info in anomalies.items():
            with st.expander(f"{col}: {info['count']} outliers detected"):
                st.markdown(f"- **Bounds:** [{info['lower_bound']}, {info['upper_bound']}]")
                st.markdown(f"- **Outlier count:** {info['count']}")
                st.dataframe(info["outlier_rows"].head(5), use_container_width=True)
    else:
        st.success("No significant anomalies detected using IQR method.")

    # Recommendations
    st.markdown("### \U0001F3AF Recommendations")
    recs = generate_recommendations(df)
    for rec in recs:
        st.markdown(f"- {rec}")

    # Trend detection
    trends = detect_trends(df)
    if trends:
        st.markdown("### \U0001F4C8 Trend Analysis")
        for key, value in trends.items():
            if isinstance(value, dict) and "trend" in value:
                st.markdown(f"**{key}:** {value['trend'].capitalize()} trend")
            elif isinstance(value, str):
                st.markdown(f"**Overall trend:** {value}")

    # Export section
    st.markdown("### \U0001F4E5 Export")
    exp_col1, exp_col2 = st.columns(2)
    with exp_col1:
        csv_export = df.to_csv(index=False)
        st.download_button(
            "Download Data as CSV",
            csv_export,
            file_name="analyzed_data.csv",
            mime="text/csv"
        )
    with exp_col2:
        # Generate insights text export
        insights_text = []
        insights_text.append(f"=== Expert Data Analysis Report ===\n")
        insights_text.append(f"Domain: {domain_name}")
        insights_text.append(f"Shape: {len(df)} rows x {len(df.columns)} columns")
        insights_text.append(f"Completeness: {completeness:.1f}%\n")
        insights_text.append("--- Key Findings ---")
        for f in fallback_insights.get("key_findings", []):
            insights_text.append(f"  - {f}")
        insights_text.append("\n--- Patterns ---")
        for p in fallback_insights.get("patterns", []):
            insights_text.append(f"  - {p}")
        insights_text.append("\n--- Concerns ---")
        for c in fallback_insights.get("concerns", []):
            insights_text.append(f"  - {c}")
        insights_text.append("\n--- Recommendations ---")
        for r in recs:
            insights_text.append(f"  - {r}")

        st.download_button(
            "Download Insights Report",
            "\n".join(insights_text),
            file_name="insights_report.txt",
            mime="text/plain"
        )
else:
    st.markdown("---")
    st.info("\U0001F4C2 Upload a file above to begin expert analysis.")
    st.markdown("""
    **Supported file types:**
    - **CSV** (.csv) - Comma-separated values
    - **Excel** (.xlsx, .xls) - Microsoft Excel workbooks
    - **Power BI exports** - Use "Export data" in Power BI, save as CSV or Excel

    **What you will get:**
    - Automatic data domain detection (Financial, HR, Education, Survey, etc.)
    - Comprehensive data profiling and quality assessment
    - AI-powered narrative insights (with Gemini API key)
    - Auto-generated visualizations matched to your data
    - Anomaly detection and actionable recommendations
    - Ask questions about your data in natural language
    """)
