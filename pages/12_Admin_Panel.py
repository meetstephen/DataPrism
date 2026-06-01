"""DataPrism Admin Panel - User management, activity log, feedback, and system status."""

import streamlit as st

from utils.styles import inject_global_css, render_sidebar_nav
from utils.supabase_client import get_client, is_configured, status_message
from utils.auth import require_role, get_current_user, log_user_activity

st.set_page_config(
    page_title="Admin Panel | DataPrism",
    page_icon="\U0001F6E1\uFE0F",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_global_css()
render_sidebar_nav()

# --- Admin-only access check ---
user = require_role("admin")

st.markdown(
    "<h1 class='dp-gradient-title'>\U0001F6E1\uFE0F Admin Panel</h1>",
    unsafe_allow_html=True,
)
st.caption(f"Signed in as: {user.get('display_name', user.get('email', 'Admin'))}")

# Log access
try:
    log_user_activity("admin_panel_access", page="admin")
except Exception:
    pass

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_users, tab_activity, tab_feedback, tab_system = st.tabs(
    ["\U0001F465 Users", "\U0001F4CB Activity Log", "\U0001F4AC Feedback", "\u2699\uFE0F System"]
)

# ---------------------------------------------------------------------------
# Users Tab
# ---------------------------------------------------------------------------
with tab_users:
    st.subheader("User Management")

    client, err = get_client()
    if client is None:
        st.info(err or "Supabase not configured. User management unavailable in local mode.")
    else:
        # List users
        try:
            res = (
                client.table("dp_users")
                .select("id,email,display_name,role,created_at,last_login,is_active")
                .order("created_at", desc=True)
                .execute()
            )
            users = res.data or []
        except Exception as e:
            users = []
            st.error(f"Could not load users: {e}")

        if users:
            st.markdown(f"**{len(users)} registered user(s)**")

            for u in users:
                with st.container():
                    cols = st.columns([3, 2, 1, 2, 1])
                    cols[0].markdown(
                        f"**{u.get('display_name', 'N/A')}**  \n"
                        f"`{u.get('email', '')}`"
                    )
                    cols[1].markdown(f"Role: **{u.get('role', 'viewer')}**")
                    cols[2].markdown(
                        "\U0001F7E2 Active" if u.get("is_active", True) else "\U0001F534 Inactive"
                    )
                    created = u.get("created_at", "")[:10] if u.get("created_at") else "N/A"
                    last_login = u.get("last_login", "")[:10] if u.get("last_login") else "Never"
                    cols[3].caption(f"Created: {created}\nLast login: {last_login}")

                    # Role change
                    current_role = u.get("role", "viewer")
                    role_col, save_col = cols[4].columns([2, 1])
                    new_role = role_col.selectbox(
                        "Role",
                        ["admin", "analyst", "viewer"],
                        index=["admin", "analyst", "viewer"].index(current_role),
                        key=f"role_{u['id']}",
                        label_visibility="collapsed",
                    )
                    if save_col.button("\U0001F4BE", key=f"save_role_{u['id']}", help="Save role change"):
                        if new_role != current_role:
                            try:
                                client.table("dp_users").update(
                                    {"role": new_role}
                                ).eq("id", u["id"]).execute()
                                st.success(f"Updated {u.get('email')} to {new_role}.")
                                log_user_activity(
                                    "change_user_role",
                                    details=f"{u.get('email')} -> {new_role}",
                                    page="admin",
                                )
                                st.rerun()
                            except Exception as e:
                                st.error(f"Could not update role: {e}")
                        else:
                            st.info("Role unchanged.")

            st.markdown("---")
        else:
            st.info("No users found.")

        # Add user form
        st.markdown("#### Add User")
        st.caption(
            "Note: This creates a dp_users record. The user must also exist in "
            "Supabase Auth (they should sign up through the login page)."
        )
        with st.form("add_user_form"):
            new_email = st.text_input("Email")
            new_name = st.text_input("Display Name")
            new_role = st.selectbox("Role", ["viewer", "analyst", "admin"])
            add_submitted = st.form_submit_button("Add User", type="primary")
            if add_submitted:
                if not new_email:
                    st.error("Email is required.")
                else:
                    try:
                        client.table("dp_users").insert({
                            "email": new_email.strip().lower(),
                            "display_name": new_name.strip() or new_email.split("@")[0],
                            "role": new_role,
                            "is_active": True,
                            "auth_id": None,
                        }).execute()
                        st.success(f"Added user: {new_email}")
                        log_user_activity(
                            "add_user",
                            details=f"{new_email} ({new_role})",
                            page="admin",
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not add user: {e}")


# ---------------------------------------------------------------------------
# Activity Log Tab
# ---------------------------------------------------------------------------
with tab_activity:
    st.subheader("Activity Log")

    client, err = get_client()
    if client is None:
        st.info(err or "Supabase not configured. Activity logging unavailable in local mode.")
    else:
        # Filters
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            filter_user = st.text_input(
                "Filter by email (partial match)", key="activity_filter_user"
            )
        with filter_col2:
            filter_action = st.text_input(
                "Filter by action", key="activity_filter_action"
            )

        try:
            query = (
                client.table("dp_activity_log")
                .select("id,user_id,action,details,page,created_at")
                .order("created_at", desc=True)
                .limit(200)
            )
            res = query.execute()
            activities = res.data or []
        except Exception as e:
            activities = []
            st.error(f"Could not load activity log: {e}")

        # Resolve user emails for display
        user_map = {}
        try:
            user_res = client.table("dp_users").select("id,email").execute()
            for u in (user_res.data or []):
                user_map[u["id"]] = u["email"]
        except Exception:
            pass

        # Apply filters
        if filter_user:
            activities = [
                a for a in activities
                if filter_user.lower() in user_map.get(a.get("user_id"), "").lower()
            ]
        if filter_action:
            activities = [
                a for a in activities
                if filter_action.lower() in (a.get("action") or "").lower()
            ]

        if activities:
            st.markdown(f"**Showing {len(activities)} entries** (latest 200)")
            for a in activities:
                email = user_map.get(a.get("user_id"), a.get("user_id", "unknown"))
                ts = a.get("created_at", "")[:19].replace("T", " ")
                action = a.get("action", "")
                details = a.get("details", "")
                page = a.get("page", "")
                st.markdown(
                    f"`{ts}` | **{email}** | `{action}` | {page} | {details}"
                )
        else:
            st.info("No activity log entries found.")


# ---------------------------------------------------------------------------
# Feedback Tab
# ---------------------------------------------------------------------------
with tab_feedback:
    st.subheader("User Feedback")

    from utils.feedback import list_feedback

    ok, feedback_data = list_feedback()
    if not ok:
        st.error(feedback_data)
    elif not feedback_data:
        st.info("No feedback submitted yet.")
    else:
        st.markdown(f"**{len(feedback_data)} feedback entries**")
        for fb in feedback_data:
            fb_type = fb.get("type", "Unknown")
            fb_page = fb.get("page", "N/A")
            fb_text = fb.get("text", "")
            fb_time = (fb.get("timestamp") or "")[:19].replace("T", " ")
            with st.expander(f"{fb_type} - {fb_page} ({fb_time})"):
                st.write(fb_text)


# ---------------------------------------------------------------------------
# System Tab
# ---------------------------------------------------------------------------
with tab_system:
    st.subheader("System Status")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Connection")
        st.markdown(f"**Supabase:** {status_message()}")
        st.markdown(f"**Auth configured:** {'Yes' if is_configured() else 'No'}")

    with col2:
        st.markdown("#### App Info")
        st.markdown("**Version:** 2.0.0 (Enterprise)")
        st.markdown("**Platform:** Streamlit")

    st.markdown("---")
    st.markdown("#### Quick Stats")

    client, err = get_client()
    if client is None:
        st.info("Stats unavailable without Supabase connection.")
    else:
        stat_cols = st.columns(4)
        # Total users
        try:
            res = client.table("dp_users").select("id", count="exact").execute()
            stat_cols[0].metric("Total Users", res.count if res.count else 0)
        except Exception:
            stat_cols[0].metric("Total Users", "N/A")

        # Total datasets
        try:
            res = client.table("dp_datasets").select("id", count="exact").execute()
            stat_cols[1].metric("Datasets", res.count if res.count else 0)
        except Exception:
            stat_cols[1].metric("Datasets", "N/A")

        # Total reports
        try:
            res = client.table("dp_reports").select("id", count="exact").execute()
            stat_cols[2].metric("Reports", res.count if res.count else 0)
        except Exception:
            stat_cols[2].metric("Reports", "N/A")

        # Total feedback
        try:
            res = client.table("dp_feedback").select("id", count="exact").execute()
            stat_cols[3].metric("Feedback Items", res.count if res.count else 0)
        except Exception:
            stat_cols[3].metric("Feedback Items", "N/A")
