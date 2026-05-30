# Community College Data Analyzer

> Enterprise-grade Streamlit platform for community college data analysis with AI-powered insights, interactive dashboards, and advanced analytics tools.

## Features

| Page | Description |
|------|-------------|
| **Interactive Dashboard** | Pre-built visualizations with KPI metrics, multi-filter sidebar, and data export |
| **Upload & Analyze** | Upload CSV/Excel for instant automated analysis with distributions, correlations, and data quality reports |
| **AI Insights Engine** | Natural language insights via Google Gemini 2.5 Flash with structured executive reports and rule-based fallback |
| **Advanced Analytics** | Pivot table builder, custom chart creator, group-by analysis, and statistical summaries |
| **Online Data Explorer** | Fetch datasets from any URL (CSV, JSON, Excel), browse curated public catalogs, scrape web tables |
| **Report Generator** | Generate comprehensive HTML analysis reports with embedded charts and AI summaries |
| **Expert Data Analyst** | Upload any file (CSV, Excel, Power BI exports) for deep automated analysis with AI insights |

## Tech Stack

- **Framework:** Streamlit (multi-page architecture)
- **Data Processing:** Pandas, NumPy, SciPy
- **Visualizations:** Plotly (dark theme, enterprise color palette)
- **Machine Learning:** scikit-learn
- **AI Integration:** Google Gemini 2.5 Flash API (optional, free tier available)
- **Web Scraping:** BeautifulSoup4, requests, lxml
- **File Support:** openpyxl (Excel), CSV, JSON

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

### Optional: Configure API Key via Secrets

For persistent AI-powered insights without entering the key each session, create `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "your-google-gemini-api-key"
```

Get a free API key at [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)

## Deployment on Streamlit Community Cloud

1. Push this repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app" and connect your GitHub repository
4. Set the main file path to `app.py`
5. (Optional) Add `GEMINI_API_KEY` in the app's Secrets management panel
6. Click "Deploy"

## Project Structure

```
community-college-data-analysis/
├── app.py                          # Main application entry point
├── requirements.txt                # Python dependencies
├── .streamlit/
│   └── config.toml                 # Enterprise dark theme configuration
├── pages/
│   ├── 1_Community_College_Dashboard.py  # Pre-built dashboard with filters & export
│   ├── 2_Upload_and_Analyze.py           # Universal file analyzer with spinners
│   ├── 3_AI_Insights_Engine.py           # AI-powered insights (Gemini + fallback)
│   ├── 4_Advanced_Analytics.py           # Pivot tables, charts, statistics
│   ├── 5_Online_Data_Explorer.py         # Web data fetching & scraping
│   ├── 6_Report_Generator.py            # Professional report generation
│   └── 7_Expert_Analyst.py              # Expert data analyst with Power BI support
├── utils/
│   ├── __init__.py                 # Module init
│   ├── data_generator.py          # Synthetic data generation
│   ├── visualizations.py          # Reusable Plotly charts (dark theme)
│   ├── ai_insights.py             # AI and rule-based analysis engine
│   ├── online_data.py             # Web data fetching utilities
│   └── report_generator.py        # Report generation utilities
└── data/
    └── community_college_data.csv  # Generated synthetic dataset
```

## Usage Guide

### Community College Dashboard

The dashboard provides an overview of the synthetic community college dataset:
- Use sidebar filters to narrow data by year, major, professor, or course
- View KPIs including total students, average evaluations, and course costs
- Explore 6 interactive charts covering enrollment, evaluations, and costs
- Download filtered data as CSV via the sidebar export button

### Upload & Analyze

Upload your own dataset (CSV or Excel) for automated analysis:
- Instant data preview with shape and column types
- Summary statistics for numeric and categorical columns
- Auto-generated histograms and bar charts with loading spinners
- Correlation heatmap for numeric columns (requires 2+ numeric columns)
- Missing data analysis with visualizations
- Data quality report with completeness scoring
- Download analyzed data as CSV
- Graceful handling of empty files and single-column datasets

### AI Insights Engine

Generate automated insights from your data:
- API key loaded from `st.secrets` automatically, with sidebar input as fallback
- Structured executive report format: Executive Summary, Key Findings, Patterns, Anomalies, Recommendations
- Supports built-in, uploaded, and online datasets
- Without an API key, the system uses comprehensive rule-based analysis
- Trend analysis, anomaly detection (IQR method), and actionable recommendations

### Advanced Analytics

Power tools for deeper exploration:
- **Pivot Table Builder** - Custom aggregation tables with CSV export
- **Custom Chart Builder** - Select axes, colors, and chart types with edge-case validation
- **Statistical Summary** - Extended descriptive statistics including skewness, kurtosis, and percentiles
- **Group By Analysis** - Aggregate and compare metrics across categories
- Supports built-in, uploaded, and online data sources

### Online Data Explorer

Fetch and analyze data from anywhere on the web:
- Load CSV, JSON, or Excel files directly from URLs
- Browse a curated catalog of public datasets
- Scrape HTML tables from web pages
- Preview fetched data and store it in session state for use across all pages

### Report Generator

Create professional analysis reports:
- Generate comprehensive HTML reports with embedded Plotly charts
- AI-generated executive summaries (when API key is available)
- One-click download for sharing with stakeholders
- Supports all data sources available in the platform

### Expert Data Analyst

Upload any data file for comprehensive expert-level analysis:
- Supports CSV, Excel, and Power BI exported data files
- **Power BI support:** Export your visuals/tables from Power BI Desktop as CSV or Excel, then upload here
- Automatic data domain detection (Financial, Time-Series, HR, Survey, Education)
- Complete data profiling with statistics for numeric and categorical columns
- AI-powered narrative insights via Gemini (with rule-based fallback)
- Ask questions about your data in natural language
- Auto-generated visualizations: distributions, correlations, scatter plots, box plots
- Anomaly detection using the IQR method with detailed outlier information
- Actionable recommendations based on data patterns
- Export analyzed data and insights reports

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

## Enterprise Features

- Premium dark theme with purple accent color palette
- Session state management across all pages
- Error handling with user-friendly messages on all chart operations
- Loading spinners for long-running operations
- Data export/download buttons on all analysis pages
- Edge-case handling for empty datasets and invalid selections
- Responsive wide layout across all pages
- `st.set_page_config()` properly configured on every page

## License

This project is for educational and demonstration purposes.
