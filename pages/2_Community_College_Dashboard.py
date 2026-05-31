"""
Community College Dashboard - Pre-built interactive visualizations.
"""

import streamlit as st
st.set_page_config(page_title="Community College Dashboard", page_icon="\U0001f4a0", layout="wide")
from utils.styles import inject_global_css
inject_global_css()
from utils.data_loader import ensure_builtin_data
ensure_builtin_data()

import pandas as pd
from utils.visualizations import (
    create_grouped_bar_chart,
    create_pie_chart,
    create_horizontal_bar_chart,
    create_bar_chart
)
from utils.data_generator import generate_dataset

st.title("\U0001F4CA Community College Dashboard")

# Load data
if "df" not in st.session_state:
    st.session_state.df = generate_dataset()

df = st.session_state.df.copy()

# Sidebar filters
with st.sidebar:
    st.header("Filters")

    years = sorted(df["Year"].unique().tolist())
    selected_years = st.multiselect("Year", years, default=years)

    majors = sorted(df["Major"].unique().tolist())
    selected_majors = st.multiselect("Major", majors, default=majors)

    professors = sorted(df["Professor"].unique().tolist())
    selected_professors = st.multiselect("Professor", professors, default=professors)

    courses = sorted(df["Course"].unique().tolist())
    selected_courses = st.multiselect("Course", courses, default=courses)

# Apply filters
filtered_df = df[
    (df["Year"].isin(selected_years)) &
    (df["Major"].isin(selected_majors)) &
    (df["Professor"].isin(selected_professors)) &
    (df["Course"].isin(selected_courses))
]

if filtered_df.empty:
    st.warning("No data matches the selected filters. Please adjust your selections.")
    st.stop()

# Data export
with st.sidebar:
    st.markdown("---")
    csv = filtered_df.to_csv(index=False)
    st.download_button("\U0001F4E5 Download Filtered Data", csv, "filtered_data.csv", "text/csv")

# KPI Row
st.markdown("### Key Performance Indicators")
kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

with kpi1:
    st.metric("Total Students", f"{len(filtered_df):,}")
with kpi2:
    st.metric("Avg Evaluation", f"{filtered_df['Evaluation_Score'].mean():.2f}")
with kpi3:
    st.metric("Avg Course Cost", f"${filtered_df['Course_Cost'].mean():,.0f}")
with kpi4:
    st.metric("Professors", filtered_df["Professor"].nunique())
with kpi5:
    st.metric("Courses", filtered_df["Course"].nunique())
with kpi6:
    type_counts = filtered_df["Student_Type"].value_counts()
    st.metric("Full-time", type_counts.get("Full-time", 0))

st.markdown("---")

# Visualizations - Row 1
col1, col2 = st.columns(2)

with col1:
    try:
        # Student Majors by Year (grouped bar)
        major_year = filtered_df.groupby(["Year", "Major"]).size().reset_index(name="Count")
        major_year["Year"] = major_year["Year"].astype(str)
        fig = create_grouped_bar_chart(major_year, "Year", "Count", "Major", "Student Majors by Year")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating Student Majors chart: {str(e)}")

with col2:
    try:
        # Proportion of Student Types (pie/donut)
        type_dist = filtered_df["Student_Type"].value_counts().reset_index()
        type_dist.columns = ["Student_Type", "Count"]
        fig = create_pie_chart(type_dist, "Student_Type", "Count", "Proportion of Student Types")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating Student Types chart: {str(e)}")

# Visualizations - Row 2
col3, col4 = st.columns(2)

with col3:
    try:
        # Top 10 Professors by Avg Evaluations
        prof_eval = (
            filtered_df.groupby("Professor")["Evaluation_Score"]
            .mean()
            .sort_values(ascending=True)
            .tail(10)
            .reset_index()
        )
        prof_eval.columns = ["Professor", "Avg_Evaluation"]
        prof_eval["Avg_Evaluation"] = prof_eval["Avg_Evaluation"].round(2)
        fig = create_horizontal_bar_chart(
            prof_eval, "Avg_Evaluation", "Professor",
            "Top 10 Professors by Avg Evaluation Score"
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating Professor Evaluations chart: {str(e)}")

with col4:
    try:
        # Top 10 Courses by Avg Evaluations
        course_eval = (
            filtered_df.groupby("Course")["Evaluation_Score"]
            .mean()
            .sort_values(ascending=True)
            .tail(10)
            .reset_index()
        )
        course_eval.columns = ["Course", "Avg_Evaluation"]
        course_eval["Avg_Evaluation"] = course_eval["Avg_Evaluation"].round(2)
        fig = create_horizontal_bar_chart(
            course_eval, "Avg_Evaluation", "Course",
            "Top 10 Courses by Avg Evaluation Score"
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating Course Evaluations chart: {str(e)}")

# Visualizations - Row 3
col5, col6 = st.columns(2)

with col5:
    try:
        # Professors by Avg Course Cost
        prof_cost = (
            filtered_df.groupby("Professor")["Course_Cost"]
            .mean()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        prof_cost.columns = ["Professor", "Avg_Cost"]
        prof_cost["Avg_Cost"] = prof_cost["Avg_Cost"].round(2)
        fig = create_bar_chart(prof_cost, "Professor", "Avg_Cost", "Top 10 Professors by Avg Course Cost")
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating Professor Costs chart: {str(e)}")

with col6:
    try:
        # Courses by Avg Course Cost
        course_cost = (
            filtered_df.groupby("Course")["Course_Cost"]
            .mean()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        course_cost.columns = ["Course", "Avg_Cost"]
        course_cost["Avg_Cost"] = course_cost["Avg_Cost"].round(2)
        fig = create_bar_chart(course_cost, "Course", "Avg_Cost", "Top 10 Courses by Avg Course Cost")
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating Course Costs chart: {str(e)}")
