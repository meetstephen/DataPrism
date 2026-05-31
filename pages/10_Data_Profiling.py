"""Data Profiling - Deep dataset quality analysis and column profiling."""
import streamlit as st
st.set_page_config(page_title="Data Profiling", page_icon="\U0001f4a0", layout="wide")
from utils.styles import inject_global_css, render_empty_state
inject_global_css()

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.data_loader import ensure_builtin_data, init_all_session_state
from utils.profiling import compute_quality_score, generate_column_profiles, generate_correlation_heatmap_data, ai_profiler_commentary
from utils.visualizations import create_heatmap
from utils.ai_client import get_api_key

init_all_session_state()
ensure_builtin_data()

st.title("\U0001F4A0 Data Profiling")
st.markdown("Deep quality analysis, column profiling, and correlation insights for your dataset.")

st.markdown("---")

# --- Data Source Selection ---
st.markdown("### Select Data Source")
data_source = st.radio(
    "Choose data to profile:",
    ["Built-in Community College Data", "Uploaded Data", "Online Data", "Cleaned Data"],
    horizontal=True,
    key="profiling_data_source"
)

df = None
if data_source == "Built-in Community College Data":
    df = st.session_state.get("df")
elif data_source == "Uploaded Data":
    df = st.session_state.get("uploaded_df")
elif data_source == "Online Data":
    df = st.session_state.get("online_df")
elif data_source == "Cleaned Data":
    df = st.session_state.get("working_df")

if df is None or (hasattr(df, "empty") and df.empty):
    render_empty_state(
        "\U0001F4CA",
        "No Data Available",
        "Load a dataset to begin profiling. Upload data on the Upload & Analyze page, or select the built-in dataset."
    )
    st.page_link("pages/2_Upload_and_Analyze.py", label="\U0001F4C1 Go to Upload & Analyze", icon="\U0001F4C1")
    st.stop()

st.success(f"Profiling dataset: **{len(df):,} rows** x **{len(df.columns)} columns**")

st.markdown("---")

# --- Data Quality Score ---
st.markdown("### \U0001F3AF Data Quality Score")

quality_score = compute_quality_score(df)

fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=quality_score,
    domain={"x": [0, 1], "y": [0, 1]},
    title={"text": "Overall Quality Score", "font": {"size": 18}},
    gauge={
        "axis": {"range": [0, 100], "tickwidth": 1},
        "bar": {"color": "#00D4FF"},
        "steps": [
            {"range": [0, 40], "color": "rgba(255, 75, 75, 0.2)"},
            {"range": [40, 70], "color": "rgba(255, 193, 7, 0.2)"},
            {"range": [70, 100], "color": "rgba(40, 167, 69, 0.2)"},
        ],
        "threshold": {
            "line": {"color": "#00D4FF", "width": 4},
            "thickness": 0.75,
            "value": quality_score,
        },
    },
))
fig_gauge.update_layout(
    height=300,
    margin=dict(l=30, r=30, t=50, b=30),
    template="plotly_dark",
    font=dict(family="Arial, sans-serif"),
)
st.plotly_chart(fig_gauge, use_container_width=True)

# Quality interpretation
if quality_score >= 80:
    st.success(f"Excellent data quality ({quality_score}/100). The dataset is well-structured with minimal issues.")
elif quality_score >= 60:
    st.warning(f"Moderate data quality ({quality_score}/100). Some cleaning may improve analysis results.")
else:
    st.error(f"Low data quality ({quality_score}/100). Significant cleaning is recommended before analysis.")

st.markdown("---")

# --- AI Profiler Commentary ---
st.markdown("### \U0001F916 AI Profiler Commentary")

api_key = get_api_key()
if not api_key:
    st.info("Enter a Gemini API key in the sidebar or secrets to enable AI commentary.")
else:
    if st.button("Generate AI Commentary", type="primary", key="ai_profiler_btn"):
        with st.spinner("Generating AI profiling commentary..."):
            try:
                commentary, err = ai_profiler_commentary(df, api_key)
                if err:
                    st.error(f"AI commentary error: {err}")
                elif commentary:
                    st.markdown(commentary)
            except Exception as e:
                st.error(f"Failed to generate AI commentary: {str(e)}")

st.markdown("---")

# --- Column Profile Cards ---
st.markdown("### \U0001F4DD Column Profile Cards")

profiles = generate_column_profiles(df)

for profile in profiles:
    col_name = profile["column"]
    with st.expander(f"\U0001F4CC {col_name} ({profile['dtype']})", expanded=False):
        info_col1, info_col2, info_col3 = st.columns(3)
        with info_col1:
            st.metric("Data Type", profile["dtype"])
        with info_col2:
            st.metric("Null %", f"{profile['null_pct']}%")
        with info_col3:
            st.metric("Unique Values", f"{profile['unique_count']:,}")

        # Top 5 values table
        if profile["top_values"]:
            st.markdown("**Top Values:**")
            top_df = pd.DataFrame(profile["top_values"])
            top_df.columns = ["Value", "Count"]
            st.dataframe(top_df, use_container_width=True, hide_index=True)

        # Mini chart
        dist = profile["distribution"]
        if dist.get("type") == "histogram" and dist.get("counts"):
            bin_edges = dist["bin_edges"]
            counts = dist["counts"]
            # Create bin centers for display
            bin_centers = [(bin_edges[i] + bin_edges[i + 1]) / 2 for i in range(len(counts))]
            fig_mini = go.Figure(go.Bar(
                x=bin_centers,
                y=counts,
                marker_color="#00D4FF",
                opacity=0.7,
            ))
            fig_mini.update_layout(
                height=200,
                margin=dict(l=30, r=30, t=20, b=30),
                template="plotly_dark",
                xaxis_title=col_name,
                yaxis_title="Count",
                font=dict(size=10),
            )
            st.plotly_chart(fig_mini, use_container_width=True)
        elif dist.get("type") == "categorical" and dist.get("labels"):
            labels = dist["labels"][:10]
            counts = dist["counts"][:10]
            fig_mini = go.Figure(go.Bar(
                x=counts,
                y=labels,
                orientation="h",
                marker_color="#7B61FF",
                opacity=0.7,
            ))
            fig_mini.update_layout(
                height=max(150, len(labels) * 25 + 50),
                margin=dict(l=30, r=30, t=20, b=30),
                template="plotly_dark",
                xaxis_title="Count",
                yaxis_title="",
                font=dict(size=10),
            )
            st.plotly_chart(fig_mini, use_container_width=True)

st.markdown("---")

# --- Correlation Heatmap ---
st.markdown("### \U0001F525 Correlation Heatmap")

numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

if len(numeric_cols) >= 2:
    corr_data = generate_correlation_heatmap_data(df)
    corr_matrix = corr_data["matrix"]
    high_pairs = corr_data["high_correlation_pairs"]

    if not corr_matrix.empty:
        fig_heatmap = create_heatmap(corr_matrix, "Feature Correlation Matrix")
        st.plotly_chart(fig_heatmap, use_container_width=True)

        # Flagged high-correlation pairs
        if high_pairs:
            st.markdown("#### \u26A0\uFE0F High Correlation Pairs (|r| > 0.85)")
            for pair in high_pairs:
                st.warning(
                    f"**{pair['col_a']}** and **{pair['col_b']}**: "
                    f"r = {pair['correlation']:.4f} - These columns may be redundant."
                )
        else:
            st.info("No highly correlated pairs found (|r| > 0.85). All features appear independent.")
    else:
        st.info("Could not compute correlations for the available numeric columns.")
else:
    st.info("Correlation analysis requires at least 2 numeric columns. Current dataset has fewer.")

# Cross-module navigation
st.markdown("---")
st.markdown("### \U0001F517 Next Steps")
nav_col1, nav_col2, nav_col3 = st.columns(3)
with nav_col1:
    st.page_link("pages/3_Data_Cleaning.py", label="\U0001f9f9 Clean Data", icon="\U0001f9f9")
with nav_col2:
    st.page_link("pages/4_AI_Insights_Engine.py", label="\U0001F916 AI Insights", icon="\U0001F916")
with nav_col3:
    st.page_link("pages/2_Upload_and_Analyze.py", label="\U0001F4C1 Upload & Analyze", icon="\U0001F4C1")
