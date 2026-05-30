"""
Community College Data Analyzer - Main Application Entry Point.

A comprehensive Streamlit web application for analyzing community college data
with interactive dashboards, AI-powered insights, and advanced analytics tools.
"""

import streamlit as st
import pandas as pd
import os

from utils.data_generator import generate_dataset, save_dataset

# Page configuration
st.set_page_config(
    page_title="Community College Data Analyzer",
    page_icon="\U0001F393",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load dataset into session state
if "df" not in st.session_state:
    data_path = "data/community_college_data.csv"
    if os.path.exists(data_path):
        st.session_state.df = pd.read_csv(data_path)
    else:
        st.session_state.df = save_dataset(data_path)

# Sidebar
with st.sidebar:
    st.title("\U0001F393 Data Analyzer")
    st.markdown("---")
    st.markdown(
        """
        **Community College Data Analysis Platform**

        Navigate using the pages in the sidebar to explore:

        - **Dashboard** - Pre-built visualizations
        - **Upload & Analyze** - Your own datasets
        - **AI Insights** - Automated analysis
        - **Advanced Analytics** - Custom tools
        """
    )
    st.markdown("---")
    st.caption("Built with Streamlit & Plotly")

# Main content - Welcome page
st.title("\U0001F393 Community College Data Analyzer")
st.markdown("### Welcome to the Data Analysis Platform")
st.markdown(
    """
    This application provides comprehensive data analysis tools for community college data.
    Explore pre-built dashboards, upload your own datasets, generate AI-powered insights,
    and perform advanced analytics with interactive tools.
    """
)

st.markdown("---")

# Feature cards
col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        #### \U0001F4CA Community College Dashboard
        Explore pre-built interactive visualizations of community college data including:
        - Student enrollment by major and year
        - Professor and course evaluations
        - Cost analysis across departments
        - KPI metrics and filters
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
        #### \U0001F4C1 Upload & Analyze
        Upload and analyze any dataset:
        - Support for CSV and Excel files
        - Automatic column type detection
        - Summary statistics and distributions
        - Correlation analysis and data quality reports
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

st.markdown("---")

# Dataset overview
st.markdown("### Dataset Overview")
st.markdown(
    f"The built-in community college dataset contains **{len(st.session_state.df)}** "
    f"records with **{len(st.session_state.df.columns)}** columns."
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Records", len(st.session_state.df))
with col2:
    st.metric("Columns", len(st.session_state.df.columns))
with col3:
    st.metric("Majors", st.session_state.df["Major"].nunique())
with col4:
    st.metric("Years Covered", st.session_state.df["Year"].nunique())

st.markdown("---")
st.markdown("*Select a page from the sidebar to get started.*")
