"""Saved Analysis Templates - save/load/list/delete analysis configurations.

Supports Supabase cloud persistence (dp_templates table) when configured,
otherwise falls back to local JSON files in .dataprism/templates/.

Each function returns an (ok, payload) tuple following the database.py pattern.
"""

import json
import os
from datetime import datetime, timezone

from utils.supabase_client import get_client, is_configured


TEMPLATES_DIR = ".dataprism/templates"
T_TEMPLATES = "dp_templates"


def _ensure_local_dir():
    """Create the local templates directory if it does not exist."""
    os.makedirs(TEMPLATES_DIR, exist_ok=True)


def save_template(name, config_dict):
    """Save an analysis template.

    Args:
        name: Template name.
        config_dict: Dict with keys like name, description, columns,
                     chart_type, filters, aggregations, created_at.

    Returns:
        (ok, message) tuple.
    """
    config_dict = dict(config_dict)
    config_dict.setdefault("name", name)
    config_dict.setdefault("created_at", datetime.now(timezone.utc).isoformat())

    if is_configured():
        client, err = get_client()
        if client is None:
            return False, err
        try:
            payload = {
                "name": name,
                "description": config_dict.get("description", ""),
                "config": config_dict,
            }
            client.table(T_TEMPLATES).insert(payload).execute()
            return True, f"Template '{name}' saved to cloud."
        except Exception as e:
            return False, f"Could not save template: {e}"
    else:
        try:
            _ensure_local_dir()
            safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in name)
            path = os.path.join(TEMPLATES_DIR, f"{safe_name}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2, default=str)
            return True, f"Template '{name}' saved locally."
        except Exception as e:
            return False, f"Could not save template: {e}"


def load_template(template_id_or_name):
    """Load a template by ID (cloud) or name (local).

    Args:
        template_id_or_name: UUID string for cloud, or name for local.

    Returns:
        (ok, config_dict | error_string) tuple.
    """
    if is_configured():
        client, err = get_client()
        if client is None:
            return False, err
        try:
            resp = client.table(T_TEMPLATES).select("*").eq("id", template_id_or_name).execute()
            if resp.data:
                return True, resp.data[0].get("config", {})
            # Fallback: search by name
            resp = client.table(T_TEMPLATES).select("*").eq("name", template_id_or_name).execute()
            if resp.data:
                return True, resp.data[0].get("config", {})
            return False, "Template not found."
        except Exception as e:
            return False, f"Could not load template: {e}"
    else:
        try:
            _ensure_local_dir()
            safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in template_id_or_name)
            path = os.path.join(TEMPLATES_DIR, f"{safe_name}.json")
            if not os.path.exists(path):
                # Try exact filename match
                for fname in os.listdir(TEMPLATES_DIR):
                    if fname.endswith(".json"):
                        fpath = os.path.join(TEMPLATES_DIR, fname)
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        if data.get("name") == template_id_or_name:
                            return True, data
                return False, "Template not found."
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return True, data
        except Exception as e:
            return False, f"Could not load template: {e}"


def list_templates():
    """List all available templates.

    Returns:
        (ok, list_of_template_dicts) tuple.
    """
    if is_configured():
        client, err = get_client()
        if client is None:
            return False, err
        try:
            resp = (
                client.table(T_TEMPLATES)
                .select("id, name, description, created_at")
                .order("created_at", desc=True)
                .execute()
            )
            return True, resp.data or []
        except Exception as e:
            return False, f"Could not list templates: {e}"
    else:
        try:
            _ensure_local_dir()
            templates = []
            for fname in sorted(os.listdir(TEMPLATES_DIR)):
                if fname.endswith(".json"):
                    fpath = os.path.join(TEMPLATES_DIR, fname)
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    templates.append({
                        "id": fname.replace(".json", ""),
                        "name": data.get("name", fname),
                        "description": data.get("description", ""),
                        "created_at": data.get("created_at", ""),
                    })
            return True, templates
        except Exception as e:
            return False, f"Could not list templates: {e}"


def delete_template(template_id_or_name):
    """Delete a template by ID (cloud) or name (local).

    Args:
        template_id_or_name: UUID for cloud, or name for local.

    Returns:
        (ok, message) tuple.
    """
    if is_configured():
        client, err = get_client()
        if client is None:
            return False, err
        try:
            resp = client.table(T_TEMPLATES).delete().eq("id", template_id_or_name).execute()
            # Verify that the delete actually matched a row
            if not resp.data or len(resp.data) == 0:
                return False, "Template not found or already deleted."
            return True, "Template deleted."
        except Exception as e:
            return False, f"Could not delete template: {e}"
    else:
        try:
            _ensure_local_dir()
            safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in template_id_or_name)
            path = os.path.join(TEMPLATES_DIR, f"{safe_name}.json")
            if os.path.exists(path):
                os.remove(path)
                return True, "Template deleted."
            return False, "Template not found."
        except Exception as e:
            return False, f"Could not delete template: {e}"
