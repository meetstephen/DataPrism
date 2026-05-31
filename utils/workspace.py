"""Workspace utilities: projects, versioning, and audit logging backed by Supabase."""
import pandas as pd
from datetime import datetime
import json


def save_project(name, description="", metadata=None):
    """Save a project to Supabase.

    Returns (ok: bool, message: str) tuple.
    """
    try:
        from utils.supabase_client import get_client
        client, err = get_client()
        if client is None:
            return False, err or "Supabase not configured."

        data = {
            "name": name,
            "description": description,
            "metadata": json.dumps(metadata or {}),
        }
        result = client.table("dp_projects").insert(data).execute()
        if result.data:
            return True, f"Project '{name}' saved successfully."
        return False, "Failed to save project."
    except Exception as e:
        return False, f"Error saving project: {str(e)}"


def list_projects():
    """List all projects from Supabase.

    Returns (ok: bool, projects_or_error) tuple.
    """
    try:
        from utils.supabase_client import get_client
        client, err = get_client()
        if client is None:
            return False, err or "Supabase not configured."

        result = client.table("dp_projects").select("*").order("created_at", desc=True).execute()
        return True, result.data or []
    except Exception as e:
        return False, f"Error listing projects: {str(e)}"


def get_project(project_id):
    """Get a single project by ID.

    Returns (ok: bool, project_or_error) tuple.
    """
    try:
        from utils.supabase_client import get_client
        client, err = get_client()
        if client is None:
            return False, err or "Supabase not configured."

        result = client.table("dp_projects").select("*").eq("id", project_id).execute()
        if result.data:
            return True, result.data[0]
        return False, "Project not found."
    except Exception as e:
        return False, f"Error getting project: {str(e)}"


def delete_project(project_id):
    """Delete a project by ID.

    Returns (ok: bool, message: str) tuple.
    """
    try:
        from utils.supabase_client import get_client
        client, err = get_client()
        if client is None:
            return False, err or "Supabase not configured."

        client.table("dp_projects").delete().eq("id", project_id).execute()
        return True, "Project deleted."
    except Exception as e:
        return False, f"Error deleting project: {str(e)}"


def log_action(action, details=""):
    """Log an action to the audit log.

    Returns (ok: bool, message: str) tuple.
    """
    try:
        from utils.supabase_client import get_client
        client, err = get_client()
        if client is None:
            return False, err or "Supabase not configured."

        data = {
            "action": action,
            "details": details,
        }
        client.table("dp_audit_log").insert(data).execute()
        return True, "Action logged."
    except Exception as e:
        return False, f"Error logging action: {str(e)}"


def list_audit_log(limit=50):
    """List recent audit log entries.

    Returns (ok: bool, entries_or_error) tuple.
    """
    try:
        from utils.supabase_client import get_client
        client, err = get_client()
        if client is None:
            return False, err or "Supabase not configured."

        result = (
            client.table("dp_audit_log")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return True, result.data or []
    except Exception as e:
        return False, f"Error listing audit log: {str(e)}"


def save_dataset_version(dataset_name, df, version_note=""):
    """Save a versioned snapshot of a dataset.

    Returns (ok: bool, message: str) tuple.
    """
    try:
        from utils.supabase_client import get_client
        client, err = get_client()
        if client is None:
            return False, err or "Supabase not configured."

        data = {
            "dataset_name": dataset_name,
            "version_note": version_note,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "data_csv": df.to_csv(index=False),
        }
        result = client.table("dp_dataset_versions").insert(data).execute()
        if result.data:
            return True, f"Version saved for '{dataset_name}'."
        return False, "Failed to save version."
    except Exception as e:
        return False, f"Error saving version: {str(e)}"


def list_dataset_versions(dataset_name=None):
    """List dataset versions, optionally filtered by name.

    Returns (ok: bool, versions_or_error) tuple.
    """
    try:
        from utils.supabase_client import get_client
        client, err = get_client()
        if client is None:
            return False, err or "Supabase not configured."

        query = client.table("dp_dataset_versions").select("*").order("created_at", desc=True)
        if dataset_name:
            query = query.eq("dataset_name", dataset_name)
        result = query.limit(50).execute()
        return True, result.data or []
    except Exception as e:
        return False, f"Error listing versions: {str(e)}"


def restore_dataset_version(version_id):
    """Restore a dataset version by ID.

    Returns (ok: bool, df_or_error) tuple.
    """
    try:
        from utils.supabase_client import get_client
        import io

        client, err = get_client()
        if client is None:
            return False, err or "Supabase not configured."

        result = client.table("dp_dataset_versions").select("*").eq("id", version_id).execute()
        if not result.data:
            return False, "Version not found."

        row = result.data[0]
        csv_text = row.get("data_csv", "")
        if not csv_text:
            return False, "No data stored in this version."

        df = pd.read_csv(io.StringIO(csv_text))
        return True, df
    except Exception as e:
        return False, f"Error restoring version: {str(e)}"
