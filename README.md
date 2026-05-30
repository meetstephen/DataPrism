# DataPrism

> **Raw Data. Refined Intelligence.**

DataPrism is an enterprise-grade data intelligence platform built with Streamlit. Transform raw datasets into actionable insights with AI-powered analysis, interactive visualizations, data cleaning tools, and natural language conversations with your data.

---

## Features

| # | Page | Description |
|---|------|-------------|
| 1 | **Community College Dashboard** | Pre-built interactive visualizations with KPI metrics, multi-filter sidebar, and data export |
| 2 | **Upload & Analyze** | Upload CSV/Excel for instant automated analysis with distributions, correlations, and data quality reports |
| 3 | **AI Insights Engine** | Natural language insights via Google Gemini 2.5 Flash with structured executive reports and rule-based fallback |
| 4 | **Advanced Analytics** | Pivot table builder, custom chart creator, group-by analysis, and statistical summaries |
| 5 | **Online Data Explorer** | Fetch datasets from any URL (CSV, JSON, Excel), browse curated public catalogs, scrape web tables |
| 6 | **Report Generator** | Generate comprehensive HTML analysis reports with embedded charts and AI summaries |
| 7 | **Expert Data Analyst** | Upload any file (CSV, Excel, Power BI exports) for deep automated analysis with AI insights |
| 8 | **Data Cleaning Engine** | Comprehensive data cleaning with undo/redo, missing value handling, outlier removal, and audit logging |
| 9 | **Chat With Your Data** | Natural language AI chat interface - ask questions about your data and get answers with auto-generated charts |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Framework** | Streamlit (multi-page architecture) |
| **Data Processing** | Pandas, NumPy, SciPy, statsmodels |
| **Visualizations** | Plotly (enterprise dark theme) |
| **Machine Learning** | scikit-learn |
| **AI Integration** | Google Gemini 2.5 Flash API |
| **Web Scraping** | BeautifulSoup4, requests, lxml |
| **File Support** | openpyxl (Excel), CSV, JSON, Power BI exports |
| **Encoding Detection** | chardet |

---

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/meetstephen/community-college-data-analysis.git
cd community-college-data-analysis

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## Configuration

### AI Features (Optional)

DataPrism uses Google Gemini 2.5 Flash for AI-powered insights and natural language chat. Get a free API key:

1. Visit [Google AI Studio](https://aistudio.google.com/apikey)
2. Create a free API key
3. Configure it using one of these methods:

**Method 1: Streamlit Secrets (Recommended for deployment)**

Create `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your-api-key-here"
```

**Method 2: Sidebar Input**

Enter your API key in the sidebar of any AI-powered page during your session.

> **Note:** All AI features work without an API key using rule-based analysis as a fallback.

---

## Deployment on Streamlit Cloud

1. Push this repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** and connect your GitHub repository
4. Set the main file path to `app.py`
5. In **Advanced settings > Secrets**, add:
   ```toml
   GEMINI_API_KEY = "your-api-key-here"
   ```
6. Click **Deploy**

The app supports up to 200MB file uploads and runs in headless mode by default.

---

## Project Structure

```
community-college-data-analysis/
├── app.py                                    # Main entry point (DataPrism home)
├── requirements.txt                          # Python dependencies
├── .streamlit/
│   └── config.toml                           # Enterprise dark theme & server config
├── pages/
│   ├── 1_Community_College_Dashboard.py      # Interactive dashboard with filters
│   ├── 2_Upload_and_Analyze.py               # Universal file analyzer
│   ├── 3_AI_Insights_Engine.py               # AI-powered insights (Gemini + fallback)
│   ├── 4_Advanced_Analytics.py               # Pivot tables, charts, statistics
│   ├── 5_Online_Data_Explorer.py             # Web data fetching & scraping
│   ├── 6_Report_Generator.py                 # Professional report generation
│   ├── 7_Expert_Analyst.py                   # Expert analysis with Power BI support
│   ├── 8_Data_Cleaning.py                    # Data cleaning engine with undo/redo
│   └── 9_Chat_With_Data.py                   # Natural language data chat
├── utils/
│   ├── __init__.py                           # Module init
│   ├── styles.py                             # Global CSS & premium theme system
│   ├── data_engine.py                        # Data cleaning engine with audit log
│   ├── data_generator.py                     # Synthetic data generation
│   ├── visualizations.py                     # Reusable Plotly charts
│   ├── ai_insights.py                        # AI and rule-based analysis engine
│   ├── online_data.py                        # Web data fetching utilities
│   └── report_generator.py                   # Report generation utilities
└── data/
    └── community_college_data.csv            # Built-in synthetic dataset
```

---

## Screenshots

> Screenshots coming soon. The platform features a premium dark theme with cyan accent colors and enterprise-grade UI components.

---

## Enterprise Features

- **Premium Dark Theme** - Custom enterprise styling with gradient buttons, styled metrics, and polished UI
- **Data Cleaning with Undo/Redo** - Non-destructive data transformations with full audit trail
- **Natural Language Chat** - Ask questions about your data in plain English, get answers with charts
- **Power BI Integration** - Upload Power BI Desktop exports for instant analysis
- **AI-Powered Insights** - Structured executive reports from Google Gemini 2.5 Flash
- **Multiple Data Sources** - Built-in data, file upload, URL fetch, web scraping
- **Professional Reports** - Downloadable HTML reports with embedded interactive charts
- **Session Persistence** - Data and state maintained across all pages
- **200MB Upload Support** - Handle large enterprise datasets
- **Responsive Design** - Wide layout optimized for desktop workflows

---

## Power BI Integration

DataPrism supports Power BI data through the **Expert Data Analyst** page:

1. In Power BI Desktop, select your visual or table
2. Click **Export data** (or More options > Export data)
3. Save as CSV or Excel format
4. Upload the exported file to DataPrism's Expert Analyst page
5. Get instant automated analysis, AI insights, and recommendations

---

## License

This project is for educational and demonstration purposes.
