"""Cloud Workspace - Projects, audit log, dataset versioning, and cloud persistence."""
import streamlit as st
st.set_page_config(page_title="Cloud Workspace", page_icon="\U0001f4a0", layout="wide")
from utils.styles import inject_global_css, render_empty_state
inject_global_css()

import pandas as pd
from utils.data_loader import init_all_session_state, ensure_builtin_data
from utils.supabase_client import is_configured
from utils.workspace import (
    save_project, list_projects, get_project, delete_project,
    log_action, list_audit_log,
    save_dataset_version, list_dataset_versions, restore_dataset_version,
)

init_all_session_state()
ensure_builtin_data()

st.title("\u2601\uFE0F Cloud Workspace")
st.markdown("Manage projects, track actions, and version your datasets in the cloud.")

# --- Onboarding Checklist ---
if "onboarding_complete" not in st.session_state:
    st.session_state.onboarding_complete = {
        "upload": False, "profile": False, "clean": False,
        "insights": False, "report": False,
    }

onboarding = st.session_state.onboarding_complete

# Auto-detect completion based on session state
if st.session_state.get("uploaded_df") is not None or st.session_state.get("raw_df") is not None:
    onboarding["upload"] = True
if st.session_state.get("working_df") is not None:
    onboarding["clean"] = True
if st.session_state.get("generated_report"):
    onboarding["report"] = True

all_complete = all(onboarding.values())

if not all_complete:
    st.markdown("### \U0001F3C1 Getting Started Checklist")
    st.markdown("Complete these steps to get the most out of DataPrism:")

    checklist_items = [
        ("upload", "\U0001F4C1 Upload a dataset"),
        ("profile", "\U0001F4CA Run data profiling"),
        ("clean", "\U0001f9f9 Clean your data"),
        ("insights", "\U0001F4A1 Generate insights"),
        ("report", "\U0001F4CB Create a report"),
    ]

    cols = st.columns(5)
    for i, (key, label) in enumerate(checklist_items):
        with cols[i]:
            status = "\u2705" if onboarding[key] else "\u2B1C"
            st.markdown(f"{status} {label}")

    completed_count = sum(1 for v in onboarding.values() if v)
    st.progress(completed_count / 5)
    st.markdown("---")
else:
    st.success("\U0001F389 All onboarding steps completed! You are a DataPrism power user.")
    st.markdown("---")

# --- Cloud Status ---
cloud_configured = is_configured()
if not cloud_configured:
    st.info(
        "\u2601\uFE0F Cloud features require Supabase configuration. "
        "Set SUPABASE_URL and SUPABASE_KEY in your secrets to enable "
        "projects, audit logging, and dataset versioning. "
        "See SUPABASE_SETUP.md for details."
    )

# --- Tabs ---
tab_projects, tab_audit, tab_versions = st.tabs([
    "\U0001F4C2 Projects", "\U0001F4DD Audit Log", "\U0001F4BE Dataset Versions"
])

# --- Projects Tab ---
with tab_projects:
    st.markdown("### \U0001F4C2 Projects")
    st.markdown("Organize your work into projects for better tracking.")

    with st.expander("\u2795 Create New Project", expanded=False):
        with st.form("create_project_form"):
            proj_name = st.text_input("Project Name", placeholder="My Analysis Project")
            proj_desc = st.text_area("Description", placeholder="Describe the project goals...")
            submitted = st.form_submit_button("Create Project", type="primary")
            if submitted:
                if proj_name.strip():
                    ok, msg = save_project(proj_name.strip(), proj_desc.strip())
                    if ok:
                        st.success(f"\u2705 {msg}")
                    else:
                        st.error(f"Failed: {msg}")
                else:
                    st.warning("Please enter a project name.")

    # List existing projects
    st.markdown("#### Your Projects")
    ok, projects = list_projects()
    if ok and projects:
        for proj in projects:
            with st.container():
                col1, col2, col3 = st.columns([4, 2, 2])
                with col1:
                    st.markdown(f"**{proj['name']}**")
                    st.caption(proj.get("description", "") or "No description")
                    st.caption(f"Created: {proj['created_at'][:10]}")
                with col2:
                    active_id = st.session_state.get("active_project_id")
                    if active_id == proj["id"]:
                        st.success("Active")
                    else:
                        if st.button("Set Active", key=f"activate_{proj['id']}"):
                            st.session_state.active_project_id = proj["id"]
                            st.rerun()
                with col3:
                    if st.button("\U0001F5D1\uFE0F Delete", key=f"delete_{proj['id']}"):
                        del_ok, del_msg = delete_project(proj["id"])
                        if del_ok:
                            if st.session_state.get("active_project_id") == proj["id"]:
                                st.session_state.active_project_id = None
                            st.success(del_msg)
                            st.rerun()
                        else:
                            st.error(del_msg)
                st.markdown("---")
    elif ok:
        st.info("No projects yet. Create one above to get started.")
    else:
        st.info(f"Could not load projects: {projects}")

# --- Audit Log Tab ---
with tab_audit:
    st.markdown("### \U0001F4DD Audit Log")
    st.markdown("Track all actions performed across your projects.")

    active_project = st.session_state.get("active_project_id")
    filter_project = st.checkbox(
        "Filter by active project", value=bool(active_project),
        key="audit_filter_project"
    )

    project_filter = active_project if filter_project and active_project else None
    ok, log_entries = list_audit_log(project_id=project_filter)

    if ok and log_entries:
        log_df = pd.DataFrame(log_entries)
        display_cols = ["created_at", "action_type", "description"]
        available_cols = [c for c in display_cols if c in log_df.columns]
        if available_cols:
            log_df_display = log_df[available_cols].copy()
            log_df_display.columns = ["Timestamp", "Action", "Description"][:len(available_cols)]
            st.dataframe(log_df_display, use_container_width=True, hide_index=True)
        else:
            st.dataframe(log_df, use_container_width=True, hide_index=True)
    elif ok:
        st.info("No audit log entries yet. Actions will be recorded as you use the platform.")
    else:
        st.info(f"Could not load audit log: {log_entries}")

# --- Dataset Versions Tab ---
with tab_versions:
    st.markdown("### \U0001F4BE Dataset Versions")
    st.markdown("Save and restore previous versions of your datasets.")

    active_project = st.session_state.get("active_project_id")

    # Save current dataset as version
    with st.expander("\U0001F4BE Save Current Dataset Version", expanded=False):
        working_df = st.session_state.get("working_df")
        if working_df is not None:
            if active_project:
                version_name = st.text_input("Dataset Name", value="working_dataset", key="ver_name")
                version_note = st.text_input("Version Note", placeholder="e.g. After cleaning outliers", key="ver_note")
                if st.button("Save Version", type="primary", key="save_ver_btn"):
                    ok, msg = save_dataset_version(active_project, version_name, working_df, version_note)
                    if ok:
                        st.success(f"\u2705 {msg}")
                    else:
                        st.error(msg)
            else:
                st.info("Set an active project first to save dataset versions.")
        else:
            st.info("No working dataset available. Upload and clean data first.")

    # List versions
    st.markdown("#### Saved Versions")
    ok, versions = list_dataset_versions(project_id=active_project)
    if ok and versions:
        for ver in versions:
            col1, col2 = st.columns([5, 2])
            with col1:
                st.markdown(
                    f"**{ver.get('dataset_name', 'Unknown')}** v{ver.get('version_number', '?')}"
                )
                st.caption(f"{ver.get('version_note', '')} | {ver.get('created_at', '')[:19]}")
            with col2:
                if st.button("Restore", key=f"restore_{ver['id']}"):
                    r_ok, result = restore_dataset_version(ver["id"])
                    if r_ok:
                        st.session_state.working_df = result
                        st.success(f"Restored {ver['dataset_name']} v{ver['version_number']}")
                        st.rerun()
                    else:
                        st.error(f"Restore failed: {result}")
            st.markdown("---")
    elif ok:
        st.info("No dataset versions saved yet.")
    else:
        st.info(f"Could not load versions: {versions}")
