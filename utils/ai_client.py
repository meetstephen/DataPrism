"""Centralized Gemini AI client helpers for DataPrism."""
import streamlit as st

# Stable Gemini model — do NOT use preview suffixes (they return 404)
GEMINI_MODEL = "gemini-2.5-flash"


def get_api_key():
    """Get the Gemini API key from Streamlit secrets, session state, or sidebar.
    Returns the key string or None. Checks in priority order:
    1. st.secrets["GEMINI_API_KEY"]
    2. st.session_state.gemini_api_key
    """
    # Try secrets first
    try:
        key = st.secrets["GEMINI_API_KEY"]
        if key and str(key).strip():
            return str(key).strip()
    except Exception:
        pass
    # Try session state
    key = st.session_state.get("gemini_api_key")
    if key and str(key).strip():
        return str(key).strip()
    return None


def generate_content(prompt, api_key=None, system_instruction=None):
    """Generate content using Gemini. Returns (text, error_message).
    On success returns (text, None). On failure returns (None, error_string).
    """
    if api_key is None:
        api_key = get_api_key()
    if not api_key:
        return None, "No API key provided. Add GEMINI_API_KEY to secrets or enter it in the sidebar."
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        if system_instruction:
            model = genai.GenerativeModel(GEMINI_MODEL, system_instruction=system_instruction)
        else:
            model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        if response and getattr(response, "text", None):
            return response.text, None
        return None, "The model returned an empty response. Try rephrasing your request."
    except Exception as e:
        import logging
        logging.warning(f"Gemini generation failed: {str(e)}")
        return None, f"AI request failed: {str(e)}"
