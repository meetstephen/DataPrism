"""DataPrism premium enterprise styling system."""

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');
#MainMenu, footer, .stDeployButton { visibility: hidden; display: none; }
html, body, [class*="css"] { font-family: 'DM Sans', 'Segoe UI', sans-serif; }
h1, h2, h3 { letter-spacing: -0.02em; }
[data-testid="stSidebar"] {
    background: #0F1C2E !important;
    border-right: 1px solid rgba(255,255,255,0.07);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #00D4FF, #0066FF);
    color: #0F1C2E;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.5rem;
    transition: opacity 0.2s;
}
.stButton > button[kind="primary"]:hover { opacity: 0.85; }
[data-testid="stMetric"] {
    background: #1A2740;
    border-radius: 10px;
    padding: 1rem;
    border: 1px solid rgba(255,255,255,0.06);
}
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.stTabs [aria-selected="true"] { background: rgba(0, 212, 255, 0.1) !important; color: #00D4FF !important; }
[data-testid="stFileUploadDropzone"] {
    border: 2px dashed rgba(0, 212, 255, 0.4) !important;
    border-radius: 12px !important;
    background: rgba(0, 212, 255, 0.03) !important;
}

/* ===== Premium enterprise enhancements ===== */

/* Smooth fade-in for the main content area */
@keyframes dpFadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
[data-testid="stAppViewContainer"] .main .block-container {
    animation: dpFadeIn 0.5s ease-out;
    padding-top: 3rem;
}

/* Gradient text option for hero titles: add class "dp-gradient-title" */
.dp-gradient-title {
    background: linear-gradient(135deg, #00D4FF 0%, #0066FF 60%, #7B61FF 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    color: transparent;
    font-weight: 700;
    letter-spacing: -0.03em;
}

/* Styled expanders: rounded with subtle border */
[data-testid="stExpander"] {
    border: 1px solid rgba(0, 212, 255, 0.15);
    border-radius: 12px;
    background: rgba(26, 39, 64, 0.45);
    overflow: hidden;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
[data-testid="stExpander"]:hover {
    border-color: rgba(0, 212, 255, 0.4);
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.25);
}
[data-testid="stExpander"] summary {
    font-weight: 600;
}

/* Hover lift effect on metrics */
[data-testid="stMetric"] {
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    transition: transform 0.2s;
    border-color: rgba(0, 212, 255, 0.35);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.28);
}

/* Better dataframe styling: rounded corners */
[data-testid="stDataFrame"], [data-testid="stTable"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.06);
}

/* Subtle styling for st.page_link */
[data-testid="stPageLink"] a {
    border: 1px solid rgba(0, 212, 255, 0.18);
    border-radius: 10px;
    padding: 0.55rem 0.9rem !important;
    background: rgba(0, 212, 255, 0.04);
    transition: background 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}
[data-testid="stPageLink"] a:hover {
    background: rgba(0, 212, 255, 0.12);
    border-color: rgba(0, 212, 255, 0.45);
    transform: translateY(-1px);
}

/* Subtle styling for chat messages */
[data-testid="stChatMessage"] {
    background: rgba(26, 39, 64, 0.55);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 14px;
    padding: 0.4rem 0.6rem;
    margin: 0.35rem 0;
    transition: border-color 0.2s ease;
}
[data-testid="stChatMessage"]:hover {
    border-color: rgba(0, 212, 255, 0.22);
}

/* Primary download buttons share the gradient treatment */
.stDownloadButton > button[kind="primary"] {
    background: linear-gradient(135deg, #00D4FF, #0066FF);
    color: #0F1C2E;
    font-weight: 700;
    border: none;
    border-radius: 8px;
}
</style>
"""


def inject_global_css():
    """Call at top of every page after set_page_config."""
    import streamlit as st
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def render_insight_card(insight_type: str, content: str):
    """Render a styled AI insight card. Types: finding, risk, opportunity, recommendation."""
    import streamlit as st
    config = {
        "finding":        ("\U0001f535", "#00D4FF", "Key Finding"),
        "risk":           ("\U0001f534", "#EF4444", "Risk Flag"),
        "opportunity":    ("\U0001f7e2", "#10B981", "Opportunity"),
        "recommendation": ("\U0001f7e1", "#F59E0B", "Recommendation"),
    }
    icon, color, label = config.get(insight_type, ("\U0001f4ca", "#00D4FF", "Insight"))
    st.markdown(f"""
    <div style="border-left: 4px solid {color}; padding: 0.75rem 1rem;
                background: rgba(255,255,255,0.04); border-radius: 0 8px 8px 0;
                margin: 0.5rem 0;">
        <span style="font-size:0.75rem; font-weight:700; color:{color};
                     text-transform:uppercase; letter-spacing:0.05em;">
            {icon} {label}
        </span>
        <p style="margin:0.25rem 0 0 0; font-size:0.9rem; color:#E2E8F0;">{content}</p>
    </div>
    """, unsafe_allow_html=True)


def render_empty_state(icon: str, title: str, message: str):
    """Render a beautiful empty state when no data is loaded."""
    import streamlit as st
    st.markdown(f"""
    <div style="text-align:center; padding: 4rem 2rem; color: #94A3B8;">
        <div style="font-size:3rem; margin-bottom:1rem;">{icon}</div>
        <h3 style="color:#E2E8F0; margin-bottom:0.5rem;">{title}</h3>
        <p style="max-width:400px; margin:0 auto 1.5rem;">{message}</p>
    </div>
    """, unsafe_allow_html=True)
