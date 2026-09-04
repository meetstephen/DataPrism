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


def _read_local_feedback():
    """Read legacy local feedback without exposing decode failures to the UI."""
    try:
        with open(LOCAL_FILE, "rb") as handle:
            raw = handle.read()
        encodings = ["utf-8-sig", "cp1252"]
        if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            encodings.insert(0, "utf-16")
        for encoding in encodings:
            try:
                return json.loads(raw.decode(encoding))
            except UnicodeDecodeError:
                continue
            except (ValueError, TypeError):
                return []
    except OSError:
        pass
    return []


def _write_local_feedback(entries):
    payload = json.dumps(entries, indent=2, ensure_ascii=False)
    temp_path = f"{LOCAL_FILE}.tmp-{os.getpid()}"
    with open(temp_path, "w", encoding="utf-8", newline="") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp_path, LOCAL_FILE)


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
        existing = _read_local_feedback() if os.path.exists(LOCAL_FILE) else []
        existing.append(entry)
        _write_local_feedback(existing)
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
            return True, _read_local_feedback()
        return True, []
    except Exception as e:
        return False, f"Could not read feedback: {e}"

