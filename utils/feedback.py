"""Feedback collection for DataPrism.

Stores tester/user feedback. If Supabase is configured, feedback goes to the
``dp_feedback`` table. Otherwise, it is stored locally in ``.dataprism/feedback.json``
so it can be collected later.

All functions return ``(ok, message)`` and never raise.
"""

import json
import os
from datetime import datetime, timezone

from utils.supabase_client import get_client

T_FEEDBACK = "dp_feedback"
LOCAL_FILE = ".dataprism/feedback.json"


def save_feedback(feedback_type, page, text):
    """Save a feedback entry. Returns (True, msg) on success, (False, msg) on failure."""
    entry = {
        "type": feedback_type,
        "page": page,
        "text": text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Try Supabase first
    client, err = get_client()
    if client is not None:
        try:
            client.table(T_FEEDBACK).insert(entry).execute()
            return True, "Feedback saved to cloud."
        except Exception as e:
            # Fall through to local storage on any DB error
            pass

    # Local fallback
    try:
        os.makedirs(os.path.dirname(LOCAL_FILE), exist_ok=True)
        existing = []
        if os.path.exists(LOCAL_FILE):
            with open(LOCAL_FILE, "r") as f:
                existing = json.load(f)
        existing.append(entry)
        with open(LOCAL_FILE, "w") as f:
            json.dump(existing, f, indent=2)
        return True, "Feedback saved locally."
    except Exception as e:
        return False, f"Could not save feedback: {e}"


def list_feedback():
    """List all feedback entries. Returns (ok, list_or_error)."""
    # Try Supabase
    client, err = get_client()
    if client is not None:
        try:
            res = (
                client.table(T_FEEDBACK)
                .select("*")
                .order("timestamp", desc=True)
                .execute()
            )
            return True, res.data or []
        except Exception:
            pass

    # Local fallback
    try:
        if os.path.exists(LOCAL_FILE):
            with open(LOCAL_FILE, "r") as f:
                data = json.load(f)
            return True, data
        return True, []
    except Exception as e:
        return False, f"Could not read feedback: {e}"
