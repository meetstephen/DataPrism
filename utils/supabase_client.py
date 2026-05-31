"""Supabase client helpers for DataPrism (optional cloud persistence).

The whole module is designed to degrade gracefully: if no credentials are
configured, or the ``supabase`` package isn't installed, the app keeps working
and cloud features simply show a "connect a database" message.

Credentials are read (in priority order) from Streamlit secrets, then env vars:
    SUPABASE_URL
    SUPABASE_KEY        (preferred; usually the anon/public key)
    SUPABASE_ANON_KEY   (fallback name)
    SUPABASE_SERVICE_KEY (fallback name)

See SUPABASE_SETUP.md for the full setup guide and SQL schema.
"""

import os

import streamlit as st


def _get_secret(name):
    """Return a secret/env value by name, or None. Streamlit secrets win."""
    try:
        val = st.secrets.get(name)  # type: ignore[attr-defined]
        if val and str(val).strip():
            return str(val).strip()
    except Exception:
        pass
    val = os.environ.get(name)
    if val and str(val).strip():
        return str(val).strip()
    return None


def get_credentials():
    """Return (url, key) from secrets/env, each possibly None."""
    url = _get_secret("SUPABASE_URL")
    key = (
        _get_secret("SUPABASE_KEY")
        or _get_secret("SUPABASE_ANON_KEY")
        or _get_secret("SUPABASE_SERVICE_KEY")
    )
    return url, key


def is_configured():
    """True if both a URL and a key are present (does not test connectivity)."""
    url, key = get_credentials()
    return bool(url and key)


@st.cache_resource(show_spinner=False)
def _create_client(url, key):
    """Create and cache a Supabase client for the given credentials."""
    from supabase import create_client

    return create_client(url, key)


def get_client():
    """Return ``(client, error)``.

    ``client`` is None when not configured, the package is missing, or the
    connection could not be created; ``error`` then holds a user-facing string.
    """
    url, key = get_credentials()
    if not (url and key):
        return None, (
            "Supabase is not configured. Add SUPABASE_URL and SUPABASE_KEY to your "
            "secrets (see SUPABASE_SETUP.md)."
        )
    try:
        return _create_client(url, key), None
    except ModuleNotFoundError:
        return None, (
            "The 'supabase' package is not installed. Run `pip install supabase` "
            "(it is included in requirements.txt)."
        )
    except Exception as e:  # pragma: no cover - network/credential errors
        return None, f"Could not initialize Supabase client: {e}"


def status_message():
    """Return a short human-readable status string for the UI."""
    url, key = get_credentials()
    if not url and not key:
        return "Not connected \u2014 no SUPABASE_URL or SUPABASE_KEY configured."
    if not url:
        return "Incomplete \u2014 SUPABASE_URL is missing."
    if not key:
        return "Incomplete \u2014 SUPABASE_KEY is missing."
    return "Credentials detected."
