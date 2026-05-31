"""Authentication, session management, and RBAC for DataPrism.

When Supabase is configured (URL + KEY present), users must sign in before
accessing the app. When Supabase is NOT configured (local dev mode), the app
works without login by returning a mock admin user.

All functions follow the (ok, payload) pattern used elsewhere in the codebase.
Activity logging is best-effort and never blocks the user.
"""

import os
from datetime import datetime, timezone

import streamlit as st

from utils.supabase_client import get_client, is_configured

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ROLE_HIERARCHY = {"admin": 3, "analyst": 2, "viewer": 1}
T_USERS = "dp_users"
T_ACTIVITY = "dp_activity_log"

MOCK_USER = {
    "user_id": "local-dev-user",
    "email": "admin@local",
    "display_name": "Local Admin",
    "role": "admin",
    "is_mock": True,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_admin_email():
    """Return the configured ADMIN_EMAIL or None."""
    try:
        val = st.secrets.get("ADMIN_EMAIL")
        if val and str(val).strip():
            return str(val).strip().lower()
    except Exception:
        pass
    val = os.environ.get("ADMIN_EMAIL")
    if val and str(val).strip():
        return str(val).strip().lower()
    return None


def check_auth_configured():
    """Return True if Supabase is configured (implying auth tables exist)."""
    return is_configured()


# ---------------------------------------------------------------------------
# Sign up / Sign in / Sign out
# ---------------------------------------------------------------------------

def sign_up(email, password, display_name):
    """Create a new user via Supabase Auth, then insert into dp_users.

    Returns (ok, message).
    """
    client, err = get_client()
    if client is None:
        return False, err

    try:
        # Create auth user
        auth_res = client.auth.sign_up({
            "email": email,
            "password": password,
        })

        if not auth_res or not auth_res.user:
            return False, "Sign-up failed. The email may already be registered."

        auth_id = auth_res.user.id

        # Determine role
        admin_email = _get_admin_email()
        role = "admin" if (admin_email and email.strip().lower() == admin_email) else "viewer"

        # Insert dp_users row
        client.table(T_USERS).insert({
            "auth_id": auth_id,
            "email": email.strip().lower(),
            "display_name": display_name.strip(),
            "role": role,
            "is_active": True,
        }).execute()

        return True, f"Account created successfully! Role: {role}. You can now sign in."

    except Exception as e:
        err_str = str(e)
        if "already registered" in err_str.lower() or "duplicate" in err_str.lower():
            return False, "This email is already registered. Please sign in instead."
        return False, f"Sign-up error: {err_str}"


def sign_in(email, password):
    """Authenticate via Supabase Auth, fetch role from dp_users, set session state.

    Returns (ok, message).
    """
    client, err = get_client()
    if client is None:
        return False, err

    try:
        auth_res = client.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })

        if not auth_res or not auth_res.user:
            return False, "Invalid email or password."

        auth_id = auth_res.user.id

        # Fetch user profile from dp_users
        user_res = (
            client.table(T_USERS)
            .select("id,email,display_name,role,is_active")
            .eq("auth_id", auth_id)
            .execute()
        )

        if not user_res.data:
            # Auto-create dp_users row if missing (e.g. user created outside app)
            admin_email = _get_admin_email()
            role = "admin" if (admin_email and email.strip().lower() == admin_email) else "viewer"
            client.table(T_USERS).insert({
                "auth_id": auth_id,
                "email": email.strip().lower(),
                "display_name": email.split("@")[0],
                "role": role,
                "is_active": True,
            }).execute()
            user_row = {
                "id": auth_id,
                "email": email.strip().lower(),
                "display_name": email.split("@")[0],
                "role": role,
            }
        else:
            user_row = user_res.data[0]
            if not user_row.get("is_active", True):
                return False, "Your account has been deactivated. Contact an admin."

        # Update last_login
        try:
            client.table(T_USERS).update(
                {"last_login": datetime.now(timezone.utc).isoformat()}
            ).eq("auth_id", auth_id).execute()
        except Exception:
            pass

        # Store in session state
        st.session_state["dp_authenticated"] = True
        st.session_state["dp_user_email"] = user_row.get("email", email)
        st.session_state["dp_user_id"] = user_row.get("id", auth_id)
        st.session_state["dp_user_role"] = user_row.get("role", "viewer")
        st.session_state["dp_user_name"] = user_row.get("display_name", "")
        st.session_state["dp_login_time"] = datetime.now(timezone.utc).isoformat()

        return True, "Signed in successfully."

    except Exception as e:
        err_str = str(e)
        if "invalid" in err_str.lower() or "credentials" in err_str.lower():
            return False, "Invalid email or password."
        return False, f"Sign-in error: {err_str}"


def sign_out():
    """Clear authentication session state."""
    keys_to_clear = [
        "dp_authenticated", "dp_user_email", "dp_user_id",
        "dp_user_role", "dp_user_name", "dp_login_time",
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    # Try to sign out from Supabase Auth too
    try:
        client, _ = get_client()
        if client:
            client.auth.sign_out()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Session / User helpers
# ---------------------------------------------------------------------------

def get_current_user():
    """Return a dict with user info from session state, or None if not authenticated."""
    if not st.session_state.get("dp_authenticated"):
        return None
    return {
        "user_id": st.session_state.get("dp_user_id"),
        "email": st.session_state.get("dp_user_email"),
        "display_name": st.session_state.get("dp_user_name", ""),
        "role": st.session_state.get("dp_user_role", "viewer"),
        "login_time": st.session_state.get("dp_login_time"),
    }


def is_admin():
    """Return True if the current user has the admin role."""
    return st.session_state.get("dp_user_role") == "admin"


def require_auth():
    """Gate function: ensures user is authenticated before proceeding.

    - If Supabase is NOT configured (local dev mode), returns a mock admin user
      without blocking.
    - If Supabase IS configured and user is NOT authenticated, renders the login
      page and calls st.stop().
    - Returns the current user dict when authenticated.
    """
    if not check_auth_configured():
        # Warn if partially configured (one credential set but not the other)
        from utils.supabase_client import get_credentials
        url, key = get_credentials()
        if bool(url) != bool(key):
            missing = "SUPABASE_KEY" if url else "SUPABASE_URL"
            st.warning(
                f"Partial Supabase configuration detected: `{missing}` is missing. "
                f"Authentication is disabled (local dev mode). Add both SUPABASE_URL "
                f"and SUPABASE_KEY to enable auth."
            )

        # Local dev mode - return mock admin, no login required
        st.session_state["dp_authenticated"] = True
        st.session_state["dp_user_id"] = MOCK_USER["user_id"]
        st.session_state["dp_user_email"] = MOCK_USER["email"]
        st.session_state["dp_user_role"] = MOCK_USER["role"]
        st.session_state["dp_user_name"] = MOCK_USER["display_name"]
        return MOCK_USER

    # Supabase is configured - require real auth
    user = get_current_user()
    if user:
        return user

    # Not authenticated - show login page and stop
    render_login_page()
    st.stop()


def require_role(min_role):
    """Check that the current user has at least the specified role level.

    Role hierarchy: admin > analyst > viewer.
    If insufficient, shows error and calls st.stop().
    Returns the current user dict if authorized.
    """
    user = get_current_user()
    if not user:
        st.error("You must be signed in to access this page.")
        st.stop()

    user_level = ROLE_HIERARCHY.get(user.get("role", "viewer"), 0)
    required_level = ROLE_HIERARCHY.get(min_role, 0)

    if user_level < required_level:
        st.error(
            f"Access denied. This page requires **{min_role}** role or higher. "
            f"Your role: **{user.get('role', 'viewer')}**."
        )
        st.stop()

    return user


# ---------------------------------------------------------------------------
# Activity logging (best-effort, never blocks)
# ---------------------------------------------------------------------------

def log_user_activity(action, details="", page=""):
    """Log a user action to dp_activity_log. Best-effort, never raises."""
    try:
        client, err = get_client()
        if client is None:
            return

        user_id = st.session_state.get("dp_user_id")
        if not user_id or user_id == "local-dev-user":
            return

        client.table(T_ACTIVITY).insert({
            "user_id": user_id,
            "action": action,
            "details": details,
            "page": page or "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Login / Signup UI
# ---------------------------------------------------------------------------

def render_login_page():
    """Render the login/signup UI with tabs for Sign In and Sign Up."""

    # Centered container
    st.markdown(
        """
        <div style="display:flex; justify-content:center; align-items:center;
                    min-height:60vh;">
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_center, col_right = st.columns([1, 2, 1])

    with col_center:
        st.markdown(
            "<h1 style='text-align:center; margin-bottom:0;'>"
            "\U0001f4a0 DataPrism</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center; color:#94A3B8; margin-bottom:2rem;'>"
            "Enterprise Data Intelligence Platform</p>",
            unsafe_allow_html=True,
        )

        tab_signin, tab_signup = st.tabs(["\U0001F511 Sign In", "\U0001F4DD Sign Up"])

        with tab_signin:
            with st.form("signin_form", clear_on_submit=False):
                email = st.text_input("Email", key="signin_email")
                password = st.text_input("Password", type="password", key="signin_password")
                submitted = st.form_submit_button(
                    "Sign In", use_container_width=True, type="primary"
                )
                if submitted:
                    if not email or not password:
                        st.error("Please enter both email and password.")
                    else:
                        ok, msg = sign_in(email.strip(), password)
                        if ok:
                            st.success(msg)
                            log_user_activity("login", page="auth")
                            st.rerun()
                        else:
                            st.error(msg)

        with tab_signup:
            with st.form("signup_form", clear_on_submit=False):
                new_name = st.text_input("Display Name", key="signup_name")
                new_email = st.text_input("Email", key="signup_email")
                new_password = st.text_input(
                    "Password", type="password", key="signup_password",
                    help="Minimum 6 characters"
                )
                confirm_password = st.text_input(
                    "Confirm Password", type="password", key="signup_confirm"
                )
                submitted = st.form_submit_button(
                    "Create Account", use_container_width=True, type="primary"
                )
                if submitted:
                    if not new_email or not new_password or not new_name:
                        st.error("Please fill in all fields.")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        ok, msg = sign_up(new_email.strip(), new_password, new_name.strip())
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)

        st.markdown("---")
        st.caption(
            "DataPrism | Enterprise Data Intelligence | "
            "Contact your admin if you need access."
        )
