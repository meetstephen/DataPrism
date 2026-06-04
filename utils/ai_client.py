"""Centralized Gemini AI client helpers for DataPrism.

Uses the current google-genai>=1.0.0 SDK (not the deprecated google-generativeai).
"""
import streamlit as st

# Stable Gemini model — do NOT use preview suffixes (they return 404)
GEMINI_MODEL = "gemini-2.5-flash"


def get_api_key():
    """Get the Gemini API key from Streamlit secrets or session state.
    Returns the key string or None. Checks in priority order:
    1. st.secrets["GEMINI_API_KEY"]
    2. st.session_state.gemini_api_key
    """
    try:
        key = st.secrets["GEMINI_API_KEY"]
        if key and str(key).strip():
            return str(key).strip()
    except Exception:
        pass
    key = st.session_state.get("gemini_api_key")
    if key and str(key).strip():
        return str(key).strip()
    return None


def generate_content(prompt, api_key=None, system_instruction=None):
    """Generate content using Gemini (google-genai SDK).

    Returns (text, error_message).
    On success: (text, None). On failure: (None, error_string).
    """
    if api_key is None:
        api_key = get_api_key()
    if not api_key:
        return None, "No API key provided. Add GEMINI_API_KEY to secrets or enter it in the sidebar."
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        config = None
        if system_instruction:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction
            )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=config,
        )

        if response and getattr(response, "text", None):
            return response.text, None
        return None, "The model returned an empty response. Try rephrasing your request."

    except Exception as e:
        import logging
        logging.warning(f"Gemini generation failed: {str(e)}")
        return None, f"AI request failed: {str(e)}"
