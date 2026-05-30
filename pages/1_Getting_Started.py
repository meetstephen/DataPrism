"""Getting Started - Quick start guide for DataPrism."""
import streamlit as st
st.set_page_config(page_title="Getting Started", page_icon="🚀", layout="wide")
from utils.styles import inject_global_css
inject_global_css()

st.title("🚀 Getting Started")
st.markdown("""
Welcome to **DataPrism**! Here's how to get the most out of the platform in 3 easy steps.
""")

st.markdown("---")

st.markdown("### Step 1: Load Your Data")
st.markdown("""
You have three ways to get data into DataPrism:

| Method | Page | Description |
|--------|------|-------------|
| **Upload a file** | Upload & Analyze | CSV or Excel files up to 200MB |
| **Fetch from web** | Online Data Explorer | Load from any URL or browse public datasets |
| **Use built-in data** | Community College Dashboard | Pre-loaded sample dataset for exploration |
""")

st.markdown("### Step 2: Explore & Clean")
st.markdown("""
Once your data is loaded, it's automatically available across all pages:

- **Data Cleaning** → Fix missing values, remove duplicates, handle outliers (with full undo support)
- **Advanced Analytics** → Pivot tables, custom charts, statistical summaries
- **Expert Analyst** → Upload Power BI exports for deep automated analysis
""")

st.markdown("### Step 3: Generate Insights & Reports")
st.markdown("""
- **AI Insights Engine** → Get Gemini-powered findings, risks, and recommendations
- **Chat With Data** → Ask questions in natural language, get charts back
- **Report Generator** → Export professional HTML reports with AI executive summaries
""")

st.markdown("---")

st.markdown("### 🔑 AI Features (Optional)")
st.markdown("""
DataPrism works without an API key using rule-based analysis. For AI-powered features:

1. Get a **free** Gemini API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Enter it in the sidebar on any AI-powered page
3. Or add it to Streamlit secrets for automatic loading

**AI-powered pages:** AI Insights Engine, Chat With Data, Report Generator, Expert Analyst
""")

st.markdown("---")

st.markdown("### 📊 Data Flow")
st.markdown("""
Data loaded on any page is shared across the entire app via session state:

- `Built-in Data` → Available on Dashboard, AI Insights, Advanced Analytics, Report Generator
- `Uploaded Data` → Available on all analysis pages + Cleaning + Chat
- `Online Data` → Available on all analysis pages + Cleaning + Chat + Report Generator
- `Cleaned Data` → Available on all analysis pages (after cleaning operations)

**Tip:** The Data Cleaning page operates on whichever dataset you load into it - upload, online, or built-in.
""")

st.markdown("---")
st.info("💡 **Pro Tip:** Start with the Community College Dashboard to see what DataPrism can do, then upload your own data!")
