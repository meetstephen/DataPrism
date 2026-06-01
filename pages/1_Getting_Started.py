"""Getting Started - Quick start guide for DataPrism."""
import streamlit as st
st.set_page_config(page_title="Getting Started", page_icon="\U0001f4a0", layout="wide")
from utils.styles import inject_global_css, render_sidebar_nav
inject_global_css()
render_sidebar_nav()

st.title("🚀 Getting Started")
st.markdown("""
Welcome to **DataPrism**! Here's how to get the most out of the platform in 3 easy steps.
""")

st.markdown("---")

st.info(
    "🧭 **New here? Try Guided Analysis Mode.** "
    "It walks you through the full workflow step by step — load data, clean it, explore "
    "insights, and generate a report — without needing to know which page to open first. "
    "Look for **🧭 Guided Analysis** at the top of the sidebar. Highly recommended for beginners."
)

st.markdown("---")

st.markdown("### Step 1: Load Your Data")
st.markdown("""
You have three ways to get data into DataPrism:

| Method | Page | Description |
|--------|------|-------------|
| **Upload a file** | Upload & Analyze | CSV or Excel files (including Power BI exports) up to 200MB |
| **Fetch from web** | Online Data Explorer | Load from any URL or browse public datasets |
| **Chat with a document** | Chat With Data | Upload a PDF, Word, Excel, CSV, or Power BI export and converse with it |

A built-in sample dataset is also pre-loaded automatically so you can explore every page right away.
""")

st.markdown("### Step 2: Explore & Clean")
st.markdown("""
Once your data is loaded, it's automatically available across all pages:

- **Upload & Analyze** → Instant automated analysis, distributions, correlations, and data quality reports (accepts Power BI exports)
- **Data Cleaning** → Fix missing values, remove duplicates, handle outliers (with full undo support)
- **Advanced Analytics** → Pivot tables, custom charts, statistical summaries
""")

st.markdown("### Step 3: Generate Insights & Reports")
st.markdown("""
- **AI Insights Engine** → Get Gemini-powered findings, risks, and recommendations
- **Chat With Data** → Ask questions in natural language about **structured data** (get charts back) or about **documents** you upload (PDF, Word, Excel, Power BI exports, and more)
- **Report Generator** → Export professional HTML reports with AI executive summaries
""")

st.markdown("---")

st.markdown("### 🔑 AI Features (Optional)")
st.markdown("""
DataPrism works without an API key using rule-based analysis. For AI-powered features:

1. Get a **free** Gemini API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Enter it in the sidebar on any AI-powered page
3. Or add it to Streamlit secrets for automatic loading

**AI-powered pages:** AI Insights Engine, Chat With Data (structured data **and** documents), Report Generator
""")

st.markdown("---")

st.markdown("### 📊 Data Flow")
st.markdown("""
Data loaded on any page is shared across the entire app via session state:

- `Built-in Data` → Available on AI Insights, Advanced Analytics, Report Generator
- `Uploaded Data` → Available on all analysis pages + Cleaning + Chat
- `Online Data` → Available on all analysis pages + Cleaning + Chat + Report Generator
- `Cleaned Data` → Available on all analysis pages (after cleaning operations)

**Tip:** The Data Cleaning page operates on whichever dataset you load into it — upload, online, or built-in.
""")

st.markdown("---")
st.info("💡 **Pro Tip:** New to the platform? Start with **🧭 Guided Analysis Mode**, then branch out to Upload & Analyze with your own data!")
