"""Supabase client wrapper for DataPrism cloud persistence.

Provides a graceful wrapper that returns (client, error) so callers
never crash when Supabase is not configured.

Configuration: set SUPABASE_URL and SUPABASE_KEY in .streamlit/secrets.toml
or as environment variables.
"""

import streamlit as st


def get_client():
    """Get a Supabase client instance.

    Returns:
        tuple: (client, error_string)
            - client is the supabase Client or None
            - error_string is None on success, or a description of the issue
    """
    try:
        url = None
        key = None

        # Try secrets first
        try:
            url = st.secrets.get("SUPABASE_URL")
            key = st.secrets.get("SUPABASE_KEY")
        except Exception:
            pass

        # Fallback to environment variables
        if not url or not key:
            import os
            url = url or os.environ.get("SUPABASE_URL")
            key = key or os.environ.get("SUPABASE_KEY")

        if not url or not key:
            return None, "Supabase not configured. Set SUPABASE_URL and SUPABASE_KEY in secrets."

        from supabase import create_client
        client = create_client(url, key)
        return client, None

    except ImportError:
        return None, "supabase package not installed. Run: pip install supabase"
    except Exception as e:
        return None, f"Failed to connect to Supabase: {str(e)}"


def is_configured():
    """Check if Supabase credentials are configured (without connecting).

    Returns:
        bool: True if both URL and KEY are set
    """
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
        if url and key:
            return True
    except Exception:
        pass

    import os
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    return bool(url and key)
