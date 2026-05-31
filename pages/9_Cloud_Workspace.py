"""Cloud Workspace - browse and manage data persisted to Supabase.

Works only when Supabase is configured (see SUPABASE_SETUP.md). When it is not
configured, the page shows setup guidance instead of failing.
"""

import streamlit as st
st.set_page_config(page_title="Cloud Workspace", page_icon="\U0001f4a0", layout="wide")
from utils.styles import inject_global_css
inject_global_css()

import pandas as pd
from utils.supabase_client import is_configured, get_client, status_message
from utils import database as db
from utils.persistence import save_session_state

st.title("\u2601\uFE0F Cloud Workspace")
st.markdown(
    "Save and reload datasets, reports, validation rule sets, and AI insights "
    "from your own Supabase database."
)

# --- Connection status ---
configured = is_configured()
if not configured:
    st.warning("Supabase is not connected yet.")
    st.markdown(
        """
        This page lets you persist your work to a cloud database so it survives
        across sessions and devices. To enable it:

        1. Create a free Supabase project.
        2. Run the SQL schema from **`SUPABASE_SETUP.md`** in the Supabase SQL Editor.
        3. Add **`SUPABASE_URL`** and **`SUPABASE_KEY`** to your secrets
           (`.streamlit/secrets.toml` locally, or the Secrets panel on Streamlit Cloud).

        See **`SUPABASE_SETUP.md`** in the repository root for the complete,
        copy-paste guide including the full SQL.
        """
    )
    st.info(f"Status: {status_message()}")
    st.stop()

# Verify the client actually initializes (catches missing package / bad creds)
client, client_err = get_client()
if client is None:
    st.error(client_err)
    st.info("See SUPABASE_SETUP.md for troubleshooting.")
    st.stop()

st.success("Connected to Supabase.")

tab_datasets, tab_reports, tab_rules, tab_insights, tab_projects, tab_audit, tab_versions = st.tabs(
    ["\U0001F4E6 Datasets", "\U0001F4CB Reports", "\u2705 Rule Sets", "\U0001F916 Insights",
     "\U0001F4C1 Projects", "\U0001F4DC Audit Log", "\U0001F504 Dataset Versions"]
)


# ---------------- Datasets ----------------
with tab_datasets:
    st.markdown("### Save a dataset")
    # Build a list of in-session datasets that can be saved
    candidates = {}
    if st.session_state.get("uploaded_df") is not None:
        candidates["Uploaded Data"] = st.session_state.uploaded_df
    if st.session_state.get("working_df") is not None:
        candidates["Cleaned Data"] = st.session_state.working_df
    if st.session_state.get("online_df") is not None:
        candidates["Online Data"] = st.session_state.online_df
    if st.session_state.get("df") is not None:
        candidates["Built-in Data"] = st.session_state.df

    if candidates:
        sc1, sc2 = st.columns([2, 2])
        with sc1:
            src = st.selectbox("Dataset in session", list(candidates.keys()), key="cw_save_src")
        with sc2:
            ds_name = st.text_input("Save as name", key="cw_save_name", placeholder="e.g. Q2 enrollment")
        ds_desc = st.text_input("Description (optional)", key="cw_save_desc")
        if st.button("Save dataset to cloud", type="primary", key="cw_save_btn"):
            if not ds_name.strip():
                st.error("Please enter a name.")
            else:
                ok, msg = db.save_dataset(ds_name.strip(), candidates[src], ds_desc.strip())
                st.success(msg) if ok else st.error(msg)
                st.rerun()
    else:
        st.info("No datasets in the current session yet. Upload or load data first.")

    st.markdown("---")
    st.markdown("### Saved datasets")
    ok, datasets = db.list_datasets()
    if not ok:
        st.error(datasets)
    elif not datasets:
        st.info("No datasets saved yet.")
    else:
        for d in datasets:
            with st.container(border=True):
                c1, c2, c3 = st.columns([5, 2, 2])
                with c1:
                    st.markdown(f"**{d['name']}**")
                    if d.get("description"):
                        st.caption(d["description"])
                    st.caption(
                        f"{d.get('row_count', 0):,} rows x {d.get('column_count', 0)} cols "
                        f"\u00b7 {str(d.get('created_at', ''))[:19].replace('T', ' ')}"
                    )
                with c2:
                    if st.button("Load", key=f"cw_load_ds_{d['id']}", use_container_width=True):
                        ok2, result = db.get_dataset(d["id"])
                        if ok2:
                            st.session_state.uploaded_df = result
                            save_session_state()
                            st.success(f"Loaded '{d['name']}' into Uploaded Data.")
                        else:
                            st.error(result)
                with c3:
                    if st.button("Delete", key=f"cw_del_ds_{d['id']}", use_container_width=True):
                        ok2, msg = db.delete_dataset(d["id"])
                        st.success(msg) if ok2 else st.error(msg)
                        st.rerun()


# ---------------- Reports ----------------
with tab_reports:
    st.markdown("### Saved reports")
    ok, reports = db.list_reports()
    if not ok:
        st.error(reports)
    elif not reports:
        st.info("No reports saved yet. Generate one in the Report Generator and click 'Save to cloud'.")
    else:
        for r in reports:
            with st.container(border=True):
                c1, c2, c3 = st.columns([5, 2, 2])
                with c1:
                    st.markdown(f"**{r['title']}**")
                    st.caption(
                        f"{r.get('dataset_name', '') or 'dataset'} "
                        f"\u00b7 {str(r.get('created_at', ''))[:19].replace('T', ' ')}"
                    )
                with c2:
                    if st.button("View", key=f"cw_view_rep_{r['id']}", use_container_width=True):
                        ok2, result = db.get_report(r["id"])
                        if ok2:
                            st.session_state["_cw_open_report"] = result
                        else:
                            st.error(result)
                with c3:
                    if st.button("Delete", key=f"cw_del_rep_{r['id']}", use_container_width=True):
                        ok2, msg = db.delete_report(r["id"])
                        st.success(msg) if ok2 else st.error(msg)
                        st.rerun()

        opened = st.session_state.get("_cw_open_report")
        if opened:
            st.markdown("---")
            st.markdown(f"#### Preview: {opened.get('title', 'Report')}")
            import streamlit.components.v1 as components
            components.html(opened.get("html", ""), height=600, scrolling=True)
            st.download_button(
                "Download HTML", opened.get("html", ""),
                file_name="report.html", mime="text/html",
            )


# ---------------- Rule sets ----------------
with tab_rules:
    st.markdown("### Save current validation rules")
    current_rules = st.session_state.get("validation_rules", [])
    st.caption(f"{len(current_rules)} rule(s) currently defined (from the Data Cleaning page).")
    rs_name = st.text_input("Rule set name", key="cw_rs_name", placeholder="e.g. Enrollment expectations")
    if st.button("Save rule set to cloud", key="cw_rs_save", disabled=not current_rules):
        if not rs_name.strip():
            st.error("Please enter a name.")
        else:
            ok, msg = db.save_rule_set(rs_name.strip(), current_rules)
            st.success(msg) if ok else st.error(msg)
            st.rerun()

    st.markdown("---")
    st.markdown("### Saved rule sets")
    ok, rule_sets = db.list_rule_sets()
    if not ok:
        st.error(rule_sets)
    elif not rule_sets:
        st.info("No rule sets saved yet.")
    else:
        for rs in rule_sets:
            with st.container(border=True):
                c1, c2, c3 = st.columns([5, 2, 2])
                rules = rs.get("rules", []) or []
                with c1:
                    st.markdown(f"**{rs['name']}**")
                    st.caption(
                        f"{len(rules)} rules "
                        f"\u00b7 {str(rs.get('created_at', ''))[:19].replace('T', ' ')}"
                    )
                with c2:
                    if st.button("Load", key=f"cw_load_rs_{rs['id']}", use_container_width=True):
                        st.session_state.validation_rules = rules
                        st.success(f"Loaded {len(rules)} rules into the session. Open Data Cleaning to use them.")
                with c3:
                    if st.button("Delete", key=f"cw_del_rs_{rs['id']}", use_container_width=True):
                        ok2, msg = db.delete_rule_set(rs["id"])
                        st.success(msg) if ok2 else st.error(msg)
                        st.rerun()


# ---------------- Insights ----------------
with tab_insights:
    st.markdown("### Saved insights")
    ok, insights = db.list_insights()
    if not ok:
        st.error(insights)
    elif not insights:
        st.info("No insights saved yet. Generate insights in the AI Insights Engine and click 'Save to cloud'.")
    else:
        for ins in insights:
            with st.container(border=True):
                head = (
                    f"**{ins.get('dataset_name', '') or 'dataset'}** \u00b7 "
                    f"{ins.get('source', 'ai')} \u00b7 "
                    f"{ins.get('confidence_level', '')} "
                    f"({ins.get('confidence_score', 0)}%)"
                )
                st.markdown(head)
                st.caption(str(ins.get("created_at", ""))[:19].replace("T", " "))
                with st.expander("View insight"):
                    st.markdown(ins.get("content", ""))
                if st.button("Delete", key=f"cw_del_ins_{ins['id']}"):
                    ok2, msg = db.delete_insight(ins["id"])
                    st.success(msg) if ok2 else st.error(msg)
                    st.rerun()


# ---------------- Projects ----------------
with tab_projects:
    st.markdown("### Projects")
    st.markdown("Organize your work into named projects.")

    from utils.workspace import save_project, list_projects, delete_project

    with st.expander("Create New Project", expanded=False):
        proj_name = st.text_input("Project name:", key="cw_proj_name", placeholder="e.g. Q2 Enrollment Analysis")
        proj_desc = st.text_input("Description (optional):", key="cw_proj_desc")
        if st.button("Create Project", type="primary", key="cw_proj_create"):
            if not proj_name.strip():
                st.error("Please enter a project name.")
            else:
                ok, msg = save_project(proj_name.strip(), proj_desc.strip())
                st.success(msg) if ok else st.error(msg)
                st.rerun()

    st.markdown("---")
    st.markdown("### Saved Projects")
    ok, projects = list_projects()
    if not ok:
        st.error(projects)
    elif not projects:
        st.info("No projects created yet.")
    else:
        for proj in projects:
            with st.container(border=True):
                c1, c2 = st.columns([6, 2])
                with c1:
                    st.markdown(f"**{proj['name']}**")
                    if proj.get("description"):
                        st.caption(proj["description"])
                    st.caption(str(proj.get("created_at", ""))[:19].replace("T", " "))
                with c2:
                    if st.button("Delete", key=f"cw_del_proj_{proj['id']}", use_container_width=True):
                        ok2, msg = delete_project(proj["id"])
                        st.success(msg) if ok2 else st.error(msg)
                        st.rerun()


# ---------------- Audit Log ----------------
with tab_audit:
    st.markdown("### Audit Log")
    st.markdown("Track all actions performed in the workspace.")

    from utils.workspace import log_action, list_audit_log

    if st.button("Refresh Audit Log", key="cw_refresh_audit"):
        st.rerun()

    ok, entries = list_audit_log(limit=50)
    if not ok:
        st.error(entries)
    elif not entries:
        st.info("No audit log entries yet. Actions are logged automatically as you use the platform.")
    else:
        log_df = pd.DataFrame(entries)
        display_cols = [c for c in ["action", "details", "created_at"] if c in log_df.columns]
        if display_cols:
            st.dataframe(log_df[display_cols], use_container_width=True, hide_index=True)


# ---------------- Dataset Versions ----------------
with tab_versions:
    st.markdown("### Dataset Versions")
    st.markdown("Save and restore versioned snapshots of your datasets.")

    from utils.workspace import save_dataset_version, list_dataset_versions, restore_dataset_version

    # Save a version
    with st.expander("Save Current Dataset Version", expanded=False):
        ver_candidates = {}
        if st.session_state.get("uploaded_df") is not None:
            ver_candidates["Uploaded Data"] = st.session_state.uploaded_df
        if st.session_state.get("working_df") is not None:
            ver_candidates["Cleaned Data"] = st.session_state.working_df

        if ver_candidates:
            ver_src = st.selectbox("Dataset:", list(ver_candidates.keys()), key="cw_ver_src")
            ver_name = st.text_input("Version name:", key="cw_ver_name", placeholder="e.g. after_cleaning_v1")
            ver_note = st.text_input("Note (optional):", key="cw_ver_note")
            if st.button("Save Version", type="primary", key="cw_ver_save"):
                if not ver_name.strip():
                    st.error("Please enter a version name.")
                else:
                    ok, msg = save_dataset_version(ver_name.strip(), ver_candidates[ver_src], ver_note.strip())
                    st.success(msg) if ok else st.error(msg)
                    st.rerun()
        else:
            st.info("No datasets in session to version. Load or upload data first.")

    st.markdown("---")
    st.markdown("### Saved Versions")
    ok, versions = list_dataset_versions()
    if not ok:
        st.error(versions)
    elif not versions:
        st.info("No dataset versions saved yet.")
    else:
        for ver in versions:
            with st.container(border=True):
                c1, c2 = st.columns([6, 2])
                with c1:
                    st.markdown(f"**{ver.get('dataset_name', 'Unknown')}**")
                    st.caption(
                        f"{ver.get('row_count', 0):,} rows x {ver.get('column_count', 0)} cols"
                        f" | {ver.get('version_note', '')}"
                        f" | {str(ver.get('created_at', ''))[:19].replace('T', ' ')}"
                    )
                with c2:
                    if st.button("Restore", key=f"cw_restore_ver_{ver['id']}", use_container_width=True):
                        ok2, result = restore_dataset_version(ver["id"])
                        if ok2:
                            st.session_state.uploaded_df = result
                            st.session_state.working_df = result.copy()
                            save_session_state()
                            st.success(f"Restored version '{ver.get('dataset_name', '')}'.")
                        else:
                            st.error(result)


# --- Onboarding Checklist ---
st.markdown("---")
st.markdown("### \U0001F3AF Onboarding Checklist")
checklist_items = {
    "Upload a dataset": st.session_state.get("uploaded_df") is not None,
    "Run AI Insights": st.session_state.get("last_insight") is not None,
    "Clean data": len(st.session_state.get("cleaning_log", [])) > 0,
    "Generate a report": st.session_state.get("generated_report") is not None,
    "Save to cloud": True,  # They are on this page with Supabase connected
}
for label, done in checklist_items.items():
    icon = "\u2705" if done else "\u2B1C"
    st.markdown(f"{icon} {label}")
completed = sum(1 for v in checklist_items.values() if v)
st.progress(completed / len(checklist_items))
