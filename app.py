"""DataPrism entrypoint: one persistent frame around every page."""
import streamlit as st

from utils.styles import inject_global_css, render_sidebar_controls
from utils.navigation import navigation_pages
from utils.data_loader import init_all_session_state, ensure_builtin_data
from utils.data_engine import init_cleaning_state
from utils.auth import require_auth
from utils.persistence import restore_session_state

st.set_page_config(page_title="DataPrism", page_icon="\U0001f4a0", layout="wide", initial_sidebar_state="expanded")
init_all_session_state()
inject_global_css()
user = require_auth()
ensure_builtin_data()
init_cleaning_state()
if "session_restored" not in st.session_state:
    restore_session_state()
    st.session_state.session_restored = True

# Both navigation and common widgets belong to this entrypoint, not individual
# pages. Their widget identity and DOM positions survive page switches.
page = st.navigation(navigation_pages(user), position="sidebar", expanded=True)
render_sidebar_controls()
page.run()
