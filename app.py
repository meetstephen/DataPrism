"""
DataPrism - Enterprise Data Intelligence Platform.

A comprehensive Streamlit web application for analyzing, cleaning, and exploring data
with interactive dashboards, AI-powered insights, and advanced analytics tools.
"""

import streamlit as st
import pandas as pd
import os

from utils.data_generator import generate_dataset, save_dataset
from utils.styles import inject_global_css
from utils.data_engine import init_cleaning_state

# Page configuration
st.set_page_config(
    page_title="DataPrism",
    page_icon="\U0001f4a0",
    layout="wide",
    initial_sidebar_state="expanded"
)
inject_global_css()

# Load dataset into session state
if "df" not in st.session_state:
    data_path = "data/community_college_data.csv"
    if os.path.exists(data_path):
        st.session_state.df = pd.read_csv(data_path)
    else:
        st.session_state.df = save_dataset(data_path)

# Initialize session state
if "online_df" not in st.session_state:
    st.session_state.online_df = None
if "uploaded_df" not in st.session_state:
    st.session_state.uploaded_df = None
if "generated_report" not in st.session_state:
    st.session_state.generated_report = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "doc_chat_history" not in st.session_state:
    st.session_state.doc_chat_history = []
if "doc_content" not in st.session_state:
    st.session_state.doc_content = None
if "doc_name" not in st.session_state:
    st.session_state.doc_name = None
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = None

# Initialize cleaning state
init_cleaning_state()

# Sidebar
with st.sidebar:
    st.title("\U0001f4a0 DataPrism")
    st.markdown("---")
    st.markdown(
        """
        **Enterprise Data Intelligence Platform**

        Navigate using the pages in the sidebar:

        - \U0001F680 **Getting Started** - Quick start guide
        - \U0001F4CA **Dashboard** - Pre-built visualizations
        - \U0001F4C1 **Upload & Analyze** - Your own datasets
        - \U0001F916 **AI Insights** - Automated analysis
        - \U0001F527 **Advanced Analytics** - Custom tools
        - \U0001F310 **Online Explorer** - Web data fetching
        - \U0001F4CB **Report Generator** - Export reports
        - \U0001F393 **Expert Analyst** - Deep file analysis
        - \U0001f9f9 **Data Cleaning** - Transform & prepare
        - \U0001F4AC **Chat With Data** - Natural language queries
        - \U0001F4C4 **Document Chat** - Chat with any document
        """
    )
    st.markdown("---")
    st.caption("DataPrism | Enterprise Data Intelligence")

# Main content - Welcome page
st.title("\U0001f4a0 DataPrism")
st.markdown("### Raw Data. Refined Intelligence.")
st.markdown(
    """
    DataPrism is an enterprise-grade data intelligence platform that transforms raw data
    into actionable insights. Explore interactive dashboards, clean and transform datasets,
    generate AI-powered analysis, and have natural conversations with your data.
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

# Expert Analyst feature card
col5, col6 = st.columns(2)
with col5:
    st.markdown(
        """
        #### \U0001F393 Expert Data Analyst
        Get professional-grade analysis of any dataset:
        - Upload CSV, Excel, or Power BI exports
        - Automatic data domain detection
        - AI-powered narrative insights
        - Ask questions about your data
        - Anomaly detection and recommendations
        """
    )

with col6:
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

# Chat feature card
col7, col8 = st.columns(2)
with col7:
    st.markdown(
        """
        #### \U0001f4ac Chat With Your Data
        Natural language data analysis:
        - Ask questions in plain English
        - Get AI-powered answers with data citations
        - Auto-generated Plotly visualizations
        - Contextual follow-up questions
        - Powered by Gemini 2.5 Flash
        """
    )

with col8:
    st.markdown(
        """
        #### \U0001F4C4 Document Chat
        Chat with any uploaded document:
        - Upload PDF, Word, Excel, CSV, JSON, or text files
        - Get AI-powered summaries and key insights
        - Ask questions in natural language
        - Extract data and patterns from documents
        - Export conversation history
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
st.caption("DataPrism | Enterprise Data Intelligence")
