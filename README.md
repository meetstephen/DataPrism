# DataPrism

> **Raw Data. Refined Intelligence.**

DataPrism is an enterprise-grade data intelligence platform built with Streamlit. Transform raw datasets into actionable insights with AI-powered analysis, interactive visualizations, data cleaning tools, and natural language conversations with your data.

---

## What's New

This release adds a set of analyst-grade capabilities across the platform:

- **"Start Here" home screen** — A clear 3-path decision tree on the home page routes you to the right starting point: *upload your own data*, *take the guided walkthrough* with sample data, or *find data online*.
- **Calculated Columns / Feature Engineering** — A new tab in the Data Cleaning Engine lets you derive new columns from existing ones, either with a guided arithmetic builder (column ± column/value) or a custom expression. Evaluation is sandboxed via `DataFrame.eval` (arithmetic & comparisons only — no arbitrary code).
- **Multi-format Export** — Cleaned data (Data Cleaning), uploaded data (Upload & Analyze), and report datasets (Report Generator) can be downloaded as **CSV, Excel (.xlsx), JSON, or Parquet** from a single export bar.
- **Time Intelligence** — A new Advanced Analytics tab computes period-over-period change (MoM/QoQ/etc.), **year-over-year (YoY)**, and **rolling averages** from any date/value pair, with charts and metrics.
- **Data Validation Rules** — Declare expectations (no missing values, uniqueness, numeric range, allowed values, regex match) and run them for a pass/fail report with drill-down into violating rows.
- **AI Confidence Badges** — AI Insights now disclose whether output is *AI-generated* or *rule-based*, with a transparency confidence level (High/Medium/Low) derived from sample size and completeness, plus the factors behind the score.
- **"View as Table" toggle** — Charts across Advanced Analytics (Custom Chart Builder, Time Intelligence, Pivot Table, and Group By) include an accessible expander to inspect the underlying data as a table.

---

## Recent Fixes & Improvements

The platform has been hardened for reliable, enterprise-grade operation:

- **Stable AI model** — All AI features now use the stable `gemini-2.5-flash` model. The deprecated preview model that returned `404` errors has been fully removed, so AI generation works reliably with a valid API key.
- **Centralized AI client** — A single helper (`utils/ai_client.py`) standardizes model selection and API-key resolution (Streamlit secrets → session state → sidebar), so a key entered anywhere works across every AI page.
- **Robust data loading** — A shared loader (`utils/data_loader.py`) guarantees the built-in dataset is available on any page, eliminating the "Built-in dataset not loaded" error when opening a page directly.
- **Verified online dataset catalog** — The Online Data Explorer catalog was replaced with curated, verified-working dataset URLs, and requests now send a browser-style User-Agent to avoid 404/rejection errors.
- **Consistent branding** — Every page now shares the same DataPrism diamond favicon for a unified browser-tab identity.
- **Direct upload on all pages** — Analysis pages accept direct file uploads, and data loaded anywhere persists across the app via session state.
- **Premium enterprise theme** — Refined styling with fade-in transitions, gradient hero titles, hover-lift metrics, rounded dataframes/expanders, and polished chat and navigation components.

---

## Features

| # | Page | Description |
|---|------|-------------|
| — | **Guided Analysis** | Step-by-step guided workflow for beginners — load, clean, explore, and report without guesswork *(wired up separately)* |
| 1 | **Getting Started** | Quick start guide with 3-step onboarding, data flow diagram, and AI feature overview |
| 2 | **Upload & Analyze** | Upload CSV/Excel (incl. Power BI exports) for instant automated analysis with distributions, correlations, and data quality reports |
| 3 | **Data Cleaning Engine** | Comprehensive data cleaning with undo/redo, missing value handling, outlier removal, **calculated columns / feature engineering**, **data validation rules**, audit logging, and **multi-format export (CSV/Excel/JSON/Parquet)** |
| 4 | **AI Insights Engine** | Natural language insights via Google Gemini 2.5 Flash with structured executive reports, rule-based fallback, and **AI confidence-disclosure badges** |
| 5 | **Advanced Analytics** | Pivot table builder, custom chart creator (with **view-as-table** toggle), group-by analysis, statistical summaries, and **time intelligence (MoM, YoY, rolling averages)** |
| 6 | **Online Data Explorer** | Fetch datasets from any URL (CSV, JSON, Excel), browse curated public catalogs, scrape web tables |
| 7 | **Report Generator** | Generate comprehensive HTML analysis reports with embedded charts and AI summaries |
| 8 | **Chat With Your Data** | One assistant for **both** structured data **and** documents — ask questions about CSV/Excel (with auto-generated charts) or upload a PDF, Word, Excel, CSV, or **Power BI export** and chat with it |

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
| **File Support** | openpyxl (Excel), PyMuPDF (PDF), python-docx (Word), CSV, JSON, Power BI exports |
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
│   ├── 1_Getting_Started.py                  # Quick start guide & onboarding
│   ├── 2_Upload_and_Analyze.py               # Universal file analyzer (incl. Power BI exports)
│   ├── 3_Data_Cleaning.py                    # Data cleaning engine with undo/redo
│   ├── 4_AI_Insights_Engine.py               # AI-powered insights (Gemini + fallback)
│   ├── 5_Advanced_Analytics.py               # Pivot tables, charts, statistics
│   ├── 6_Online_Data_Explorer.py             # Web data fetching & scraping
│   ├── 7_Report_Generator.py                 # Professional report generation
│   └── 8_Chat_With_Data.py                   # Chat with structured data AND documents
│       #                                       (Guided Analysis page is wired up separately)
├── utils/
│   ├── __init__.py                           # Module init
│   ├── styles.py                             # Global CSS, premium theme & confidence badges
│   ├── ai_client.py                          # Centralized Gemini client & API-key helper
│   ├── data_loader.py                        # Shared data loading & session-state init
│   ├── data_engine.py                        # Data cleaning engine, audit log & calculated columns
│   ├── validation.py                         # Data validation rules engine
│   ├── time_intelligence.py                  # MoM / YoY / rolling-average time analysis
│   ├── exporters.py                          # Multi-format export (CSV/Excel/JSON/Parquet)
│   ├── persistence.py                        # Session persistence (save/restore to disk)
│   ├── data_generator.py                     # Synthetic data generation
│   ├── visualizations.py                     # Reusable Plotly charts & view-as-table helper
│   ├── ai_insights.py                        # AI and rule-based analysis engine
│   ├── online_data.py                        # Web data fetching utilities
│   └── report_generator.py                   # Report generation utilities
└── data/
    └── community_college_data.csv            # Built-in synthetic dataset
```

---

## Page Flow & Data Routing

DataPrism pages are interconnected. Data loaded on one page is automatically available across the platform:

```
                      ┌─────────────────────────────────────┐
                      │         app.py (Home Page)           │
                      │   Loads built-in dataset into state  │
                      └──────────────┬──────────────────────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          │                          │                           │
          v                          v                           v
  ┌───────────────┐      ┌────────────────────┐      ┌──────────────────┐
  │ Upload &      │      │ Online Data        │      │ Chat With Data   │
  │ Analyze       │      │ Explorer           │      │ (docs / Power BI │
  │ (uploaded_df) │      │ (online_df)        │      │  exports)        │
  └───────┬───────┘      └────────┬───────────┘      └────────┬─────────┘
          │                       │                            │
          └───────────────────────┼────────────────────────────┘
                                  │
                                  v
                      ┌───────────────────────┐
                      │   Data Cleaning       │
                      │   (working_df)        │
                      └───────────┬───────────┘
                                  │
          ┌───────────────────────┼───────────────────────────┐
          │                       │                            │
          v                       v                            v
  ┌───────────────┐    ┌──────────────────┐      ┌────────────────────┐
  │ AI Insights   │    │ Chat With Data   │      │ Report Generator   │
  │ Engine        │    │ (structured)     │      │                    │
  └───────────────┘    └──────────────────┘      └────────────────────┘
```

**Cross-module navigation** buttons on the Upload & Analyze and Data Cleaning pages let you send data directly to the next step in your workflow.

---

## Screenshots

> Screenshots coming soon. The platform features a premium dark theme with cyan accent colors and enterprise-grade UI components.

---

## Enterprise Features

- **Session Persistence** - Your work survives page refreshes and app reboots. Data, chat history, and cleaning logs are automatically saved.
- **Premium Enterprise Theme** - Refined dark UI with gradient hero titles, depth-layered background, glowing gradient buttons, pill-style selectors, hover-lift metrics, rounded dataframes/expanders, an on-brand scrollbar, and polished chat & navigation components.
- **Guided Analysis Mode** - A beginner-friendly, step-by-step workflow that walks you from raw data to a finished report *(wired up separately)*.
- **Data Cleaning with Undo/Redo** - Non-destructive data transformations with full audit trail, plus calculated columns and declarative validation rules
- **Multi-Format Export** - Download cleaned data as CSV, Excel, JSON, or Parquet
- **Time Intelligence** - Month-over-month, year-over-year, and rolling-average analysis on any date/value pair
- **AI Confidence Disclosure** - Insight output is badged as AI-generated or rule-based with a transparency confidence level
- **Accessible Visualizations** - "View as table" toggle exposes the data behind charts
- **Unified Chat With Data** - One assistant for both structured data (ask questions, get auto-generated charts) and documents (PDF, Word, Excel, CSV, **Power BI exports**) for AI-powered insights and summaries
- **Power BI Integration** - Upload Power BI Desktop exports for instant analysis on Upload & Analyze and Chat With Data
- **AI-Powered Insights** - Structured executive reports from Google Gemini 2.5 Flash
- **Multiple Data Sources** - Built-in data, file upload, URL fetch, web scraping
- **Professional Reports** - Downloadable HTML reports with embedded interactive charts
- **Session Persistence** - Data and state maintained across all pages
- **200MB Upload Support** - Handle large enterprise datasets
- **Responsive Design** - Wide layout optimized for desktop workflows

---

## Power BI Integration

DataPrism supports Power BI data on the **Upload & Analyze** and **Chat With Data** pages:

1. In Power BI Desktop, select your visual or table
2. Click **Export data** (or More options > Export data)
3. Save as CSV or Excel format
4. Upload the exported file to **Upload & Analyze** for instant automated analysis, distributions, correlations, and a data-quality report — or to **Chat With Data** (document mode) to ask questions and get AI-powered insights about it

---

## License

This project is for educational and demonstration purposes.
