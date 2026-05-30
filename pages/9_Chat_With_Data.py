"""Chat With Your Data - Natural language data analysis powered by Gemini."""
import streamlit as st
st.set_page_config(page_title="Chat With Data", page_icon="\U0001f4ac", layout="wide")
from utils.styles import inject_global_css
inject_global_css()

import pandas as pd
import numpy as np

st.title("\U0001f4ac Chat With Your Data")
st.markdown("Ask questions about your data in natural language and get AI-powered answers with optional visualizations.")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Data Source Selection ---
st.markdown("---")
source_options = []
if "uploaded_df" in st.session_state and st.session_state.uploaded_df is not None:
    source_options.append("Uploaded Data")
if "df" in st.session_state and st.session_state.df is not None:
    source_options.append("Built-in Dataset")
if "online_df" in st.session_state and st.session_state.online_df is not None:
    source_options.append("Online Data")

if not source_options:
    st.warning("No data available. Please upload a dataset or load data from the home page.")
    st.stop()

selected_source = st.selectbox("Select data source for chat:", source_options, key="chat_data_source")

# Load the selected dataframe
if selected_source == "Uploaded Data":
    chat_df = st.session_state.uploaded_df
elif selected_source == "Online Data":
    chat_df = st.session_state.online_df
else:
    chat_df = st.session_state.df

# Show data preview
with st.expander("Preview Data", expanded=False):
    st.dataframe(chat_df.head(10), use_container_width=True)
    st.caption(f"Shape: {chat_df.shape[0]:,} rows x {chat_df.shape[1]} columns")

# --- API Key ---
api_key = None
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

with st.sidebar:
    st.markdown("### Configuration")
    if not api_key:
        api_key = st.text_input(
            "Gemini API Key",
            type="password",
            help="Required for AI chat. Get one free at https://aistudio.google.com/apikey",
            key="chat_gemini_key"
        )
    else:
        st.success("API key loaded from secrets")

    st.markdown("---")
    if st.button("\U0001F5D1\uFE0F Clear Chat", use_container_width=True):
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

# --- Chat Interface ---
if not api_key:
    st.info(
        "\U0001F511 **API Key Required** - Enter your Gemini API key in the sidebar to start chatting with your data. "
        "Get a free key at [Google AI Studio](https://aistudio.google.com/apikey)."
    )
    st.stop()

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("figure"):
            st.plotly_chart(message["figure"], use_container_width=True)

# Chat input
user_input = st.chat_input("Ask a question about your data...")

if user_input:
    # Display user message
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

    system_instruction = (
        "You are a senior data analyst. Answer the user's question about their dataset "
        "in clear business English. If a visualization would help, include Python code "
        "for a Plotly chart in a ```python code block. The code should create a variable "
        "called 'fig' using plotly. Use the variable 'df' which is already defined as "
        "the user's dataframe. Always use the plotly_dark template and the color "
        "#00D4FF as the primary accent color."
    )

    prompt = (
        f"Dataset information:\n{dataset_context}\n\n"
        f"User question: {user_input}\n\n"
        f"Provide a clear, data-driven answer. Cite specific numbers where possible."
    )

    # Call Gemini
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    "gemini-2.5-flash-preview-04-17",
                    system_instruction=system_instruction
                )
                response = model.generate_content(prompt)

                if response and response.text:
                    response_text = response.text

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

                    # Display response
                    st.markdown(response_text)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)

                    # Save to history
                    history_entry = {"role": "assistant", "content": response_text}
                    if fig:
                        history_entry["figure"] = fig
                    st.session_state.chat_history.append(history_entry)
                else:
                    fallback_msg = "I was unable to generate a response. Please try rephrasing your question."
                    st.warning(fallback_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": fallback_msg})

            except Exception as e:
                import logging
                logging.warning(f"Gemini chat failed: {str(e)}")
                fallback_msg = (
                    "AI chat is temporarily unavailable. Please verify your API key is correct "
                    "and try again. If the issue persists, check your network connection."
                )
                st.warning(fallback_msg)
                st.session_state.chat_history.append({"role": "assistant", "content": fallback_msg})
