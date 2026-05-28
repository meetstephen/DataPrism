# Community College Data Analyzer

A comprehensive Streamlit web application for analyzing community college data with interactive dashboards, AI-powered insights, and advanced analytics tools.

## Features

- **Interactive Dashboard** - Pre-built visualizations for community college data with KPI metrics, filterable charts, and enrollment analysis
- **Upload & Analyze** - Upload any CSV or Excel file for instant automated analysis including distributions, correlations, and data quality reports
- **AI Insights Engine** - Generate natural language insights using Google Gemini 2.5 Flash with automatic fallback to rule-based analysis
- **Advanced Analytics** - Pivot table builder, custom chart creator, group-by analysis, and statistical summaries

## Tech Stack

- **Framework:** Streamlit
- **Data Processing:** Pandas, NumPy, SciPy
- **Visualizations:** Plotly
- **Machine Learning:** scikit-learn
- **AI Integration:** Google Gemini 2.5 Flash API (optional, free tier available)
- **File Support:** openpyxl (Excel files)

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- pip package manager

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/community-college-data-analysis.git
   cd community-college-data-analysis
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   streamlit run app.py
   ```

The app will open in your default browser at `http://localhost:8501`.

## Deployment on Streamlit Community Cloud

1. Push this repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app" and connect your GitHub repository
4. Set the main file path to `app.py`
5. Click "Deploy"

For AI-powered insights, add your Google Gemini API key in the app sidebar when running. Get a free API key at https://aistudio.google.com/apikey

## Project Structure

```
community-college-data-analysis/
├── app.py                          # Main application entry point
├── requirements.txt                # Python dependencies
├── .streamlit/
│   └── config.toml                 # Streamlit theme configuration
├── pages/
│   ├── 1_Community_College_Dashboard.py  # Pre-built dashboard
│   ├── 2_Upload_and_Analyze.py           # Universal file analyzer
│   ├── 3_AI_Insights_Engine.py           # AI-powered insights
│   └── 4_Advanced_Analytics.py           # Advanced tools
├── utils/
│   ├── __init__.py                 # Module init
│   ├── data_generator.py          # Synthetic data generation
│   ├── visualizations.py          # Reusable Plotly charts
│   └── ai_insights.py             # AI and rule-based analysis
└── data/
    └── community_college_data.csv  # Generated synthetic dataset
```

## Usage Guide

### Community College Dashboard

The dashboard provides an overview of the synthetic community college dataset:
- Use sidebar filters to narrow data by year, major, professor, or course
- View KPIs including total students, average evaluations, and course costs
- Explore 6 interactive charts covering enrollment, evaluations, and costs

### Upload & Analyze

Upload your own dataset (CSV or Excel) for automated analysis:
- Instant data preview with shape and column types
- Summary statistics for numeric and categorical columns
- Auto-generated histograms and bar charts
- Correlation heatmap for numeric columns
- Missing data analysis with visualizations
- Data quality report

### AI Insights Engine

Generate automated insights from your data:
- Optionally enter an OpenAI API key for AI-powered analysis
- Without an API key, the system uses rule-based analysis
- View key findings, trend analysis, anomaly detection, and recommendations
- Supports both built-in and uploaded datasets

### Advanced Analytics

Power tools for deeper exploration:
- **Pivot Table Builder** - Create custom aggregation tables with flexible row/column/value selection
- **Custom Chart Builder** - Design your own visualizations by selecting axes, colors, and chart types
- **Statistical Summary** - Extended descriptive statistics including skewness, kurtosis, and percentiles
- **Group By Analysis** - Aggregate and compare metrics across categories

## Data Description

The built-in synthetic dataset contains approximately 800 records with the following fields:

| Column | Description |
|--------|-------------|
| Student_ID | Unique identifier (STU-0001 format) |
| Student_Name | Student full name |
| Major | Academic major (8 options) |
| Year | Academic year (2020-2023) |
| Student_Type | Full-time or Part-time |
| Professor | Instructor name |
| Course | Course name |
| Course_Cost | Course cost in USD ($500-$5000) |
| Evaluation_Score | Course evaluation (1.0-5.0) |

## License

This project is for educational and demonstration purposes.
