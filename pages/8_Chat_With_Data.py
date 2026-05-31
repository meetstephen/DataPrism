"""Chat With Your Data - Natural language chat for structured data AND documents.

Two modes:
  - Chat with structured data: select a CSV/Excel data source and ask questions,
    optionally getting auto-generated Plotly charts back.
  - Chat with a document: upload any document (PDF, Word, Excel, CSV, Power BI
    exports, JSON, text, markdown, RTF) and have an AI conversation about it.
"""
import streamlit as st
st.set_page_config(page_title="Chat With Data", page_icon="\U0001f4a0", layout="wide")
from utils.styles import inject_global_css, render_empty_state
inject_global_css()

import pandas as pd
import numpy as np
from io import StringIO, BytesIO
from utils.ai_client import get_api_key, generate_content, GEMINI_MODEL
from utils.persistence import save_session_state

st.title("\U0001f4ac Chat With Your Data")
st.markdown(
    "Have a natural-language conversation with your **structured data** or with any "
    "**document** you upload. Get AI-powered, executive-ready answers, insights, and charts."
)

# --- Mode selector (must come right after the title) ---
mode = st.radio(
    "Choose chat mode:",
    ["\U0001f4ac Chat with structured data", "\U0001f4c4 Chat with a document"],
    horizontal=True,
)

# Initialize chat state for both modes
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "doc_chat_history" not in st.session_state:
    st.session_state.doc_chat_history = []
if "doc_content" not in st.session_state:
    st.session_state.doc_content = None
if "doc_name" not in st.session_state:
    st.session_state.doc_name = None

# Premium, expert-grade system instructions (the app's internal AI prompts)
STRUCTURED_SYSTEM_INSTRUCTION = (
    "You are DataPrism's senior data analyst - an expert-level business intelligence "
    "consultant advising an executive stakeholder. Answer the user's question about "
    "their dataset in clear, executive-ready business English, grounded strictly in the "
    "actual data provided. Be specific and quantified: cite exact figures, percentages, "
    "and column names, and surface relevant trends, comparisons, anomalies, and caveats. "
    "If a visualization would materially help, include Python code in a ```python code "
    "block that builds a Plotly figure assigned to a variable named 'fig', using the "
    "dataframe variable 'df' (already defined). Always use the plotly_dark template and "
    "the accent color #00D4FF. Keep responses well-structured with concise headings and "
    "bullet points."
)

DOCUMENT_SYSTEM_INSTRUCTION = (
    "You are DataPrism's senior document and data analyst - an expert analyst that turns "
    "any uploaded file into actionable intelligence. You have been given the contents of a "
    "document, which may include Power BI exported CSV/Excel data. Answer the user's "
    "questions strictly based on the document content. Be specific and quantified: cite "
    "exact figures, reference the relevant sections, and provide executive-ready, "
    "actionable insights and recommendations. When the document contains data, perform "
    "quantitative analysis - identify trends, patterns, outliers, and risks with concrete "
    "numbers. Format every response in clean markdown with clear headings and bullet points."
)


# ============================================================================
# Shared sidebar: API key configuration
# ============================================================================
api_key = get_api_key()
with st.sidebar:
    st.markdown("### Configuration")
    if not api_key:
        key_input = st.text_input(
            "Gemini API Key",
            type="password",
            help="Required for AI chat. Get one free at https://aistudio.google.com/apikey",
            key="chat_gemini_key",
        )
        if key_input and key_input.strip():
            st.session_state.gemini_api_key = key_input.strip()
            api_key = get_api_key()
    else:
        st.success("API key loaded")


# ============================================================================
# Document text extraction (ported from Document Chat)
# ============================================================================
def extract_text_from_file(uploaded_file):
    """Extract text content from various file types (incl. Power BI CSV/Excel exports)."""
    file_type = uploaded_file.name.split(".")[-1].lower()
    content = ""

    try:
        if file_type in ("txt", "md", "rtf"):
            content = uploaded_file.read().decode("utf-8", errors="replace")

        elif file_type == "csv":
            df = pd.read_csv(uploaded_file)
            content = f"CSV File: {uploaded_file.name}\n"
            content += f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\n"
            content += f"Columns: {', '.join(df.columns.tolist())}\n\n"
            content += "Column Types:\n"
            for col in df.columns:
                content += f"  - {col}: {df[col].dtype}\n"
            content += f"\nSummary Statistics:\n{df.describe().to_string()}\n"
            content += f"\nFirst 20 rows:\n{df.head(20).to_string()}\n"
            if len(df) > 20:
                content += f"\n... ({len(df) - 20} more rows)\n"
            # Also store the dataframe for use across the app
            st.session_state.uploaded_df = df

        elif file_type in ["xlsx", "xls"]:
            df = pd.read_excel(uploaded_file)
            content = f"Excel File: {uploaded_file.name}\n"
            content += f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\n"
            content += f"Columns: {', '.join(df.columns.tolist())}\n\n"
            content += "Column Types:\n"
            for col in df.columns:
                content += f"  - {col}: {df[col].dtype}\n"
            content += f"\nSummary Statistics:\n{df.describe().to_string()}\n"
            content += f"\nFirst 20 rows:\n{df.head(20).to_string()}\n"
            if len(df) > 20:
                content += f"\n... ({len(df) - 20} more rows)\n"
            st.session_state.uploaded_df = df

        elif file_type == "json":
            import json
            raw = uploaded_file.read().decode("utf-8", errors="replace")
            try:
                data = json.loads(raw)
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                    df = pd.DataFrame(data)
                    content = f"JSON File (tabular): {uploaded_file.name}\n"
                    content += f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\n"
                    content += f"Columns: {', '.join(df.columns.tolist())}\n\n"
                    content += f"First 10 records:\n{df.head(10).to_string()}\n"
                    st.session_state.uploaded_df = df
                else:
                    content = f"JSON File: {uploaded_file.name}\n\n"
                    content += json.dumps(data, indent=2)[:10000]  # Limit to 10k chars
            except json.JSONDecodeError:
                content = raw[:10000]

        elif file_type == "pdf":
            try:
                import fitz  # PyMuPDF
                pdf_bytes = uploaded_file.read()
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                pages_text = []
                for page_num, page in enumerate(doc):
                    text = page.get_text()
                    if text.strip():
                        pages_text.append(f"--- Page {page_num + 1} ---\n{text}")
                content = f"PDF File: {uploaded_file.name}\n"
                content += f"Pages: {len(doc)}\n\n"
                content += "\n".join(pages_text)
                doc.close()
            except ImportError:
                content = "[PDF reading requires PyMuPDF. Please install it or convert to text first.]"
            except Exception as e:
                content = f"[Error reading PDF: {str(e)}]"

        elif file_type in ["docx", "doc"]:
            try:
                from docx import Document
                doc = Document(uploaded_file)
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                content = f"Word Document: {uploaded_file.name}\n"
                content += f"Paragraphs: {len(paragraphs)}\n\n"
                content += "\n\n".join(paragraphs)
            except ImportError:
                content = "[Word document reading requires python-docx. Please install it or convert to text first.]"
            except Exception as e:
                content = f"[Error reading document: {str(e)}]"

        else:
            content = uploaded_file.read().decode("utf-8", errors="replace")

    except Exception as e:
        content = f"[Error processing file: {str(e)}]"

    # Truncate very long content for context window
    if len(content) > 30000:
        content = content[:30000] + "\n\n[... Content truncated for analysis. First 30,000 characters shown.]"

    return content


# ============================================================================
# MODE 1: Chat with structured data
# ============================================================================
def render_structured_chat():
    st.markdown("---")
    st.markdown("### Load Data")

    source_tab1, source_tab2 = st.tabs(["\U0001F4C1 Upload New File", "\U0001F4C2 Use Existing Data"])

    with source_tab1:
        chat_upload = st.file_uploader(
            "Upload a CSV or Excel file to chat with",
            type=["csv", "xlsx", "xls"],
            key="chat_file_uploader",
            help="Upload a structured data file (CSV or Excel, including Power BI exports) and ask questions about it.",
        )
        if chat_upload is not None:
            try:
                if chat_upload.name.endswith(".csv"):
                    new_df = pd.read_csv(chat_upload)
                else:
                    new_df = pd.read_excel(chat_upload)
                if new_df.empty or len(new_df.columns) < 1:
                    st.error("The uploaded file is empty or has no columns.")
                else:
                    st.session_state.uploaded_df = new_df
                    st.session_state["_chat_df"] = new_df
                    save_session_state()
                    st.success(f"\u2705 Loaded **{chat_upload.name}** ({len(new_df):,} rows x {len(new_df.columns)} columns)")
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")

    with source_tab2:
        source_options = []
        if "uploaded_df" in st.session_state and st.session_state.uploaded_df is not None:
            source_options.append("Uploaded Data")
        if "df" in st.session_state and st.session_state.df is not None:
            source_options.append("Built-in Dataset")
        if "online_df" in st.session_state and st.session_state.online_df is not None:
            source_options.append("Online Data")
        if "working_df" in st.session_state and st.session_state.working_df is not None:
            source_options.append("Cleaned Data")

        if not source_options:
            st.info("No existing data loaded. Upload a file above, or load data from the Online Explorer or Home page.")
        else:
            selected_source = st.selectbox("Select data source for chat:", source_options, key="chat_data_source")

            if st.button("Use This Dataset", type="primary", key="load_existing_for_chat"):
                if selected_source == "Uploaded Data":
                    st.session_state["_chat_df"] = st.session_state.uploaded_df
                elif selected_source == "Online Data":
                    st.session_state["_chat_df"] = st.session_state.online_df
                elif selected_source == "Cleaned Data":
                    st.session_state["_chat_df"] = st.session_state.working_df
                else:
                    st.session_state["_chat_df"] = st.session_state.df
                st.success(f"\u2705 Using '{selected_source}' for chat.")
                st.rerun()

    # Determine active chat dataframe
    chat_df = st.session_state.get("_chat_df")
    if chat_df is None:
        # Fallback: try to find any available data
        if st.session_state.get("uploaded_df") is not None:
            chat_df = st.session_state.uploaded_df
        elif st.session_state.get("df") is not None:
            chat_df = st.session_state.df
        elif st.session_state.get("online_df") is not None:
            chat_df = st.session_state.online_df

    if chat_df is None:
        st.info("\U0001F446 Upload a file or select existing data above to start chatting.")
        return

    # Show data preview
    with st.expander("Preview Data", expanded=False):
        st.dataframe(chat_df.head(10), use_container_width=True)
        st.caption(f"Shape: {chat_df.shape[0]:,} rows x {chat_df.shape[1]} columns")

    # Mode-specific sidebar controls
    with st.sidebar:
        st.markdown("---")
        if st.button("\U0001F5D1\uFE0F Clear Chat", use_container_width=True, key="clear_structured_chat"):
            st.session_state.chat_history = []
            st.rerun()
        st.markdown("---")
        st.markdown(
            "**Tips:**\n"
            "- Ask about trends, patterns, or specific columns\n"
            "- Request charts: 'Show me a bar chart of...'\n"
            "- Ask for comparisons or summaries\n"
            "- Ask follow-up questions for deeper analysis"
        )

    if not api_key:
        st.info(
            "\U0001F511 **API Key Required** - Enter your Gemini API key in the sidebar to start chatting with your data. "
            "Get a free key at [Google AI Studio](https://aistudio.google.com/apikey)."
        )
        return

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("figure"):
                st.plotly_chart(message["figure"], use_container_width=True)

    # Chat input
    user_input = st.chat_input("Ask a question about your data...")

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        # Build context about the dataset
        schema_info = []
        for col in chat_df.columns:
            dtype = str(chat_df[col].dtype)
            null_count = int(chat_df[col].isnull().sum())
            schema_info.append(f"  - {col} ({dtype}, {null_count} nulls)")

        dataset_context = (
            f"Dataset shape: {chat_df.shape[0]} rows x {chat_df.shape[1]} columns\n"
            f"Columns:\n" + "\n".join(schema_info) + "\n\n"
            f"Sample data (first 10 rows):\n{chat_df.head(10).to_string()}"
        )

        prompt = (
            f"Dataset information:\n{dataset_context}\n\n"
            f"User question: {user_input}\n\n"
            f"Provide a clear, data-driven answer. Cite specific numbers where possible."
        )

        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                response_text, error = generate_content(
                    prompt, api_key=api_key, system_instruction=STRUCTURED_SYSTEM_INSTRUCTION
                )

                if response_text:
                    # Check for Python code blocks (chart generation)
                    fig = None
                    if "```python" in response_text:
                        code_blocks = response_text.split("```python")
                        for block in code_blocks[1:]:
                            code = block.split("```")[0].strip()
                            # Basic safety check - reject dangerous patterns
                            dangerous_patterns = ['import os', 'import subprocess', 'import sys', '__import__',
                                                  'eval(', 'exec(', 'open(', 'import shutil', 'import socket']
                            code_lower = code.lower()
                            if any(pattern in code_lower for pattern in dangerous_patterns):
                                continue  # Skip this code block
                            try:
                                local_vars = {"df": chat_df, "pd": pd, "np": np}
                                import plotly.express as px
                                import plotly.graph_objects as go
                                local_vars["px"] = px
                                local_vars["go"] = go
                                exec(code, {"__builtins__": {}}, local_vars)
                                if "fig" in local_vars:
                                    fig = local_vars["fig"]
                                    break
                            except Exception:
                                pass

                    st.markdown(response_text)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)

                    history_entry = {"role": "assistant", "content": response_text}
                    if fig:
                        history_entry["figure"] = fig
                    st.session_state.chat_history.append(history_entry)
                    save_session_state()
                else:
                    fallback_msg = (
                        "AI chat is temporarily unavailable. "
                        f"{error or 'Please verify your API key and try again.'}"
                    )
                    st.warning(fallback_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": fallback_msg})
                    save_session_state()


# ============================================================================
# MODE 2: Chat with a document
# ============================================================================
def render_document_chat():
    st.markdown("---")
    st.markdown(
        "Upload any document and have an AI-powered conversation about its contents. "
        "Get insights, summaries, and answers to your questions. "
        "**Power BI exported files (CSV/Excel) are fully supported**, alongside PDF, Word, "
        "text, JSON, markdown, and RTF."
    )

    uploaded_doc = st.file_uploader(
        "Upload a document to chat with",
        type=["pdf", "docx", "doc", "txt", "csv", "xlsx", "xls", "json", "md", "rtf"],
        help="Supported: PDF, Word (DOCX), Text, CSV, Excel, JSON, Markdown, RTF, and Power BI exports (CSV/Excel).",
        key="doc_chat_uploader",
    )

    # Process uploaded document
    if uploaded_doc:
        if uploaded_doc.name != st.session_state.doc_name:
            with st.spinner("Reading document..."):
                content = extract_text_from_file(uploaded_doc)
                st.session_state.doc_content = content
                st.session_state.doc_name = uploaded_doc.name
                st.session_state.doc_chat_history = []  # Reset chat for new doc
            st.success(f"Document loaded: **{uploaded_doc.name}** ({len(content):,} characters extracted)")

    # Mode-specific sidebar controls
    with st.sidebar:
        st.markdown("---")
        st.markdown("### Document Chat")
        if st.session_state.doc_name:
            st.success(f"Active: {st.session_state.doc_name}")
        if st.button("Clear Chat History", key="clear_doc_chat"):
            st.session_state.doc_chat_history = []
            st.rerun()
        if st.session_state.doc_chat_history:
            chat_export = f"Document Chat - {st.session_state.doc_name}\n{'='*50}\n\n"
            for msg in st.session_state.doc_chat_history:
                chat_export += f"{'USER' if msg['role'] == 'user' else 'AI'}: {msg['content']}\n\n"
            st.download_button("Export Chat", chat_export, file_name="document_chat.txt", mime="text/plain")

    if not st.session_state.doc_content:
        render_empty_state(
            "\U0001F4C4",
            "Upload a Document",
            "Upload any document (PDF, Word, Excel, CSV, Power BI export, Text, JSON) and start "
            "chatting with it. Ask questions, get summaries, extract insights, and more.",
        )
        st.markdown("---")
        st.markdown("### Supported File Types")
        type_col1, type_col2, type_col3 = st.columns(3)
        with type_col1:
            st.markdown(
                """
                **Data Files**
                - CSV (.csv)
                - Excel (.xlsx, .xls)
                - JSON (.json)
                - **Power BI exports (CSV/Excel)**
                """
            )
        with type_col2:
            st.markdown(
                """
                **Documents**
                - PDF (.pdf)
                - Word (.docx)
                - Text (.txt)
                """
            )
        with type_col3:
            st.markdown(
                """
                **Other**
                - Markdown (.md)
                - Rich Text (.rtf)
                """
            )
        return

    # Document preview
    with st.expander("Document Preview", expanded=False):
        st.text(st.session_state.doc_content[:3000])
        if len(st.session_state.doc_content) > 3000:
            st.caption(f"Showing first 3,000 of {len(st.session_state.doc_content):,} characters")

    st.markdown("---")

    # Quick action buttons
    st.markdown("### Quick Actions")
    action_col1, action_col2, action_col3, action_col4 = st.columns(4)
    with action_col1:
        if st.button("Summarize", use_container_width=True):
            st.session_state.doc_chat_history.append({
                "role": "user",
                "content": "Please provide a comprehensive summary of this document. Include the main topics, key findings, and important details.",
            })
            st.rerun()
    with action_col2:
        if st.button("Key Insights", use_container_width=True):
            st.session_state.doc_chat_history.append({
                "role": "user",
                "content": "What are the most important insights and key takeaways from this document? List them as bullet points.",
            })
            st.rerun()
    with action_col3:
        if st.button("Generate Questions", use_container_width=True):
            st.session_state.doc_chat_history.append({
                "role": "user",
                "content": "Generate 5 important questions that this document raises or answers. For each question, provide a brief answer based on the document content.",
            })
            st.rerun()
    with action_col4:
        if st.button("Data Analysis", use_container_width=True):
            st.session_state.doc_chat_history.append({
                "role": "user",
                "content": "If this document contains data or statistics, provide a detailed analysis. Identify trends, patterns, outliers, and any notable findings. If it's a text document, analyze the key themes and arguments.",
            })
            st.rerun()

    st.markdown("---")
    st.markdown("### Chat")

    # Display chat history
    for message in st.session_state.doc_chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Determine if there is a pending user message that needs an answer
    pending = (
        st.session_state.doc_chat_history
        and st.session_state.doc_chat_history[-1]["role"] == "user"
    )

    # Chat input
    typed = st.chat_input("Ask anything about your document...")
    if typed:
        st.session_state.doc_chat_history.append({"role": "user", "content": typed})
        with st.chat_message("user"):
            st.markdown(typed)
        pending = True

    if pending:
        prompt = st.session_state.doc_chat_history[-1]["content"]
        with st.chat_message("assistant"):
            with st.spinner("Analyzing document..."):
                if api_key:
                    # Include last few messages for context
                    history_context = ""
                    recent_history = st.session_state.doc_chat_history[-6:-1]  # Last 5 before current
                    if recent_history:
                        history_context = "\n\nRecent conversation:\n"
                        for msg in recent_history:
                            history_context += f"{msg['role'].upper()}: {msg['content']}\n"

                    full_prompt = (
                        f"DOCUMENT CONTENT:\n{st.session_state.doc_content}\n\n"
                        f"{history_context}\n"
                        f"USER QUESTION: {prompt}\n\n"
                        "Provide a detailed, helpful response:"
                    )

                    answer, error = generate_content(
                        full_prompt, api_key=api_key, system_instruction=DOCUMENT_SYSTEM_INSTRUCTION
                    )
                    if not answer:
                        answer = f"AI analysis unavailable. {error or 'Please check your Gemini API key in the sidebar.'}"
                else:
                    doc_content = st.session_state.doc_content
                    answer = (
                        "**AI features require a Gemini API key.**\n\n"
                        "Enter your key in the sidebar to enable intelligent document chat.\n\n"
                        "**Document info:**\n"
                        f"- File: {st.session_state.doc_name}\n"
                        f"- Content length: {len(doc_content):,} characters\n"
                        f"- Lines: {doc_content.count(chr(10)):,}\n\n"
                        "Get a free API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)"
                    )

                st.markdown(answer)
                st.session_state.doc_chat_history.append({"role": "assistant", "content": answer})
                save_session_state()


# ============================================================================
# Render the selected mode
# ============================================================================
if mode == "\U0001f4c4 Chat with a document":
    render_document_chat()
else:
    render_structured_chat()

# Cross-module navigation
st.markdown("---")
st.markdown("### Related Tools")
nav_col1, nav_col2, nav_col3 = st.columns(3)
with nav_col1:
    st.page_link("pages/2_Upload_and_Analyze.py", label="Upload & Analyze", icon="\U0001F4C1")
with nav_col2:
    st.page_link("pages/4_AI_Insights_Engine.py", label="AI Insights", icon="\U0001F916")
with nav_col3:
    st.page_link("pages/7_Report_Generator.py", label="Generate Report", icon="\U0001F4CB")
