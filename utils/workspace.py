"""Workspace features: projects, audit log, dataset versioning.

All functions return (ok, payload) tuples. Graceful fallback when DB not configured.
Tables: dp_projects, dp_audit_log, dp_dataset_versions (see SUPABASE_SETUP.md).
"""

from utils.supabase_client import get_client
import pandas as pd
import io
from datetime import datetime


def save_project(name, description=""):
    """Insert a new project. Returns (ok, message)."""
    client, err = get_client()
    if err:
        return False, err
    try:
        result = client.table("dp_projects").insert({
            "name": name,
            "description": description,
        }).execute()
        if result.data:
            return True, "Project created successfully."
        return False, "No data returned from insert."
    except Exception as e:
        return False, f"Failed to save project: {str(e)}"


def list_projects():
    """List all projects. Returns (ok, list_of_dicts)."""
    client, err = get_client()
    if err:
        return False, err
    try:
        result = client.table("dp_projects").select("*").order("created_at", desc=True).execute()
        return True, result.data or []
    except Exception as e:
        return False, f"Failed to list projects: {str(e)}"


def get_project(project_id):
    """Get single project. Returns (ok, dict)."""
    client, err = get_client()
    if err:
        return False, err
    try:
        result = client.table("dp_projects").select("*").eq("id", project_id).execute()
        if result.data:
            return True, result.data[0]
        return False, "Project not found."
    except Exception as e:
        return False, f"Failed to get project: {str(e)}"


def delete_project(project_id):
    """Delete a project. Returns (ok, message)."""
    client, err = get_client()
    if err:
        return False, err
    try:
        client.table("dp_projects").delete().eq("id", project_id).execute()
        return True, "Project deleted."
    except Exception as e:
        return False, f"Failed to delete project: {str(e)}"


def log_action(project_id, action_type, description, details=None):
    """Log an action to dp_audit_log. details is optional dict/jsonb."""
    client, err = get_client()
    if err:
        return False, err
    try:
        entry = {
            "project_id": project_id,
            "action_type": action_type,
            "description": description,
            "details": details or {},
        }
        client.table("dp_audit_log").insert(entry).execute()
        return True, "Action logged."
    except Exception as e:
        return False, f"Failed to log action: {str(e)}"


def list_audit_log(project_id=None, limit=100):
    """List audit log entries, optionally filtered by project_id."""
    client, err = get_client()
    if err:
        return False, err
    try:
        query = client.table("dp_audit_log").select("*").order("created_at", desc=True).limit(limit)
        if project_id:
            query = query.eq("project_id", project_id)
        result = query.execute()
        return True, result.data or []
    except Exception as e:
        return False, f"Failed to list audit log: {str(e)}"


def save_dataset_version(project_id, dataset_name, df, version_note=""):
    """Save a dataset version (CSV text + metadata)."""
    client, err = get_client()
    if err:
        return False, err
    try:
        # Get next version number
        existing = client.table("dp_dataset_versions").select("version_number").eq(
            "project_id", project_id
        ).eq("dataset_name", dataset_name).order("version_number", desc=True).limit(1).execute()

        next_version = 1
        if existing.data:
            next_version = existing.data[0]["version_number"] + 1

        # Convert DataFrame to CSV text
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_text = csv_buffer.getvalue()

        entry = {
            "project_id": project_id,
            "dataset_name": dataset_name,
            "version_number": next_version,
            "data_csv": csv_text,
            "version_note": version_note,
        }
        client.table("dp_dataset_versions").insert(entry).execute()
        return True, f"Saved version {next_version} of '{dataset_name}'."
    except Exception as e:
        return False, f"Failed to save dataset version: {str(e)}"


def list_dataset_versions(project_id=None, limit=50):
    """List dataset versions."""
    client, err = get_client()
    if err:
        return False, err
    try:
        query = client.table("dp_dataset_versions").select(
            "id, project_id, dataset_name, version_number, version_note, created_at"
        ).order("created_at", desc=True).limit(limit)
        if project_id:
            query = query.eq("project_id", project_id)
        result = query.execute()
        return True, result.data or []
    except Exception as e:
        return False, f"Failed to list dataset versions: {str(e)}"


def restore_dataset_version(version_id):
    """Load a specific version. Returns (ok, DataFrame)."""
    client, err = get_client()
    if err:
        return False, err
    try:
        result = client.table("dp_dataset_versions").select("data_csv").eq("id", version_id).execute()
        if not result.data:
            return False, "Version not found."
        csv_text = result.data[0]["data_csv"]
        if not csv_text:
            return False, "Version has no data."
        df = pd.read_csv(io.StringIO(csv_text))
        return True, df
    except Exception as e:
        return False, f"Failed to restore version: {str(e)}"
