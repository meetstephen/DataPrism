"""DataPrism premium enterprise styling system with switchable themes."""
import streamlit as st

# ---------------------------------------------------------------------------
# Theme system - 3 premium enterprise themes with distinct sidebar/main colors
# ---------------------------------------------------------------------------
THEMES = {
    "Enterprise Dark": {
        "sidebar_bg": "#0A1628",
        "main_bg": "#0B1524",
        "accent": "#00D4FF",
        "accent_secondary": "#0066FF",
        "accent_tertiary": "#7B61FF",
        "card_bg": "#1A2740",
        "text_primary": "#FAFAFA",
        "text_secondary": "#94A3B8",
        "border": "rgba(255,255,255,0.07)",
        "sidebar_border": "rgba(0,212,255,0.12)",
    },
    "Midnight Purple": {
        "sidebar_bg": "#120B2E",
        "main_bg": "#1A0F3C",
        "accent": "#A855F7",
        "accent_secondary": "#7C3AED",
        "accent_tertiary": "#EC4899",
        "card_bg": "#2D1B69",
        "text_primary": "#F8FAFC",
        "text_secondary": "#A5B4FC",
        "border": "rgba(168,85,247,0.12)",
        "sidebar_border": "rgba(168,85,247,0.2)",
    },
    "Ocean Blue": {
        "sidebar_bg": "#041C2C",
        "main_bg": "#0C2D48",
        "accent": "#06B6D4",
        "accent_secondary": "#0891B2",
        "accent_tertiary": "#22D3EE",
        "card_bg": "#164E63",
        "text_primary": "#F0FDFA",
        "text_secondary": "#99F6E4",
        "border": "rgba(6,182,212,0.12)",
        "sidebar_border": "rgba(6,182,212,0.2)",
    },
}


def _get_active_theme():
    """Get the currently active theme dict. Defaults to Enterprise Dark."""
    theme_name = st.session_state.get("dp_active_theme", "Enterprise Dark")
    return THEMES.get(theme_name, THEMES["Enterprise Dark"])


def render_theme_switcher():
    """Render a theme switcher widget in the sidebar."""
    current = st.session_state.get("dp_active_theme", "Enterprise Dark")
    theme_names = list(THEMES.keys())
    selected = st.selectbox(
        "\U0001F3A8 Theme",
        theme_names,
        index=theme_names.index(current) if current in theme_names else 0,
        key="dp_theme_selector",
    )
    if selected != current:
        st.session_state.dp_active_theme = selected
        st.rerun()


def _build_css(theme):
    """Build the full CSS string for a given theme dict."""
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');
#MainMenu, footer, .stDeployButton {{ visibility: hidden; display: none; }}
html, body, [class*="css"] {{ font-family: 'DM Sans', 'Segoe UI', sans-serif; }}
h1, h2, h3 {{ letter-spacing: -0.02em; }}

/* Sidebar - distinctly darker than main */
[data-testid="stSidebar"] {{
    background: {theme['sidebar_bg']} !important;
    border-right: 1px solid {theme['sidebar_border']};
}}

/* Main content area */
[data-testid="stAppViewContainer"] {{
    background:
        radial-gradient(1100px 600px at 12% -8%, {theme['accent']}12, transparent 60%),
        radial-gradient(900px 500px at 100% 0%, {theme['accent_tertiary']}0F, transparent 55%),
        {theme['main_bg']};
}}

.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {theme['accent']}, {theme['accent_secondary']});
    color: {theme['sidebar_bg']};
    font-weight: 700;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.5rem;
    transition: opacity 0.2s;
    box-shadow: 0 4px 16px {theme['accent_secondary']}48;
}}
.stButton > button[kind="primary"]:hover {{
    opacity: 0.85;
    transform: translateY(-1px);
    box-shadow: 0 8px 24px {theme['accent']}58;
}}
.stButton > button[kind="secondary"] {{
    border: 1px solid {theme['accent']}38;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.02);
    transition: border-color 0.18s ease, background 0.18s ease, transform 0.18s ease;
}}
.stButton > button[kind="secondary"]:hover {{
    border-color: {theme['accent']}80;
    background: {theme['accent']}0F;
    transform: translateY(-1px);
}}
[data-testid="stMetric"] {{
    background: {theme['card_bg']};
    border-radius: 10px;
    padding: 1rem;
    border: 1px solid {theme['border']};
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}}
[data-testid="stMetric"]:hover {{
    transform: translateY(-2px);
    border-color: {theme['accent']}58;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.28);
}}
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid {theme['border']}; }}
.stTabs [aria-selected="true"] {{ background: {theme['accent']}1A !important; color: {theme['accent']} !important; }}
.stTabs [data-baseweb="tab"] {{
    transition: color 0.18s ease, background 0.18s ease;
    border-radius: 8px 8px 0 0;
}}
[data-testid="stFileUploadDropzone"] {{
    border: 2px dashed {theme['accent']}66 !important;
    border-radius: 12px !important;
    background: {theme['accent']}08 !important;
}}

/* Smooth fade-in for the main content area */
@keyframes dpFadeIn {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
[data-testid="stAppViewContainer"] .main .block-container {{
    animation: dpFadeIn 0.5s ease-out;
    padding-top: 3rem;
}}

/* Gradient text option for hero titles */
.dp-gradient-title {{
    background: linear-gradient(135deg, {theme['accent']} 0%, {theme['accent_secondary']} 60%, {theme['accent_tertiary']} 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    color: transparent;
    font-weight: 700;
    letter-spacing: -0.03em;
}}

/* Styled expanders */
[data-testid="stExpander"] {{
    border: 1px solid {theme['accent']}28;
    border-radius: 12px;
    background: {theme['card_bg']}73;
    overflow: hidden;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}}
[data-testid="stExpander"]:hover {{
    border-color: {theme['accent']}66;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.25);
}}
[data-testid="stExpander"] summary {{ font-weight: 600; }}

/* Better dataframe styling */
[data-testid="stDataFrame"], [data-testid="stTable"] {{
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid {theme['border']};
}}

/* Page links */
[data-testid="stPageLink"] a {{
    border: 1px solid {theme['accent']}2E;
    border-radius: 10px;
    padding: 0.55rem 0.9rem !important;
    background: {theme['accent']}08;
    transition: background 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}}
[data-testid="stPageLink"] a:hover {{
    background: {theme['accent']}1F;
    border-color: {theme['accent']}73;
    transform: translateY(-1px);
}}

/* Chat messages */
[data-testid="stChatMessage"] {{
    background: {theme['card_bg']}8C;
    border: 1px solid {theme['border']};
    border-radius: 14px;
    padding: 0.4rem 0.6rem;
    margin: 0.35rem 0;
    transition: border-color 0.2s ease;
}}
[data-testid="stChatMessage"]:hover {{
    border-color: {theme['accent']}38;
}}

/* Download buttons */
.stDownloadButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {theme['accent']}, {theme['accent_secondary']});
    color: {theme['sidebar_bg']};
    font-weight: 700;
    border: none;
    border-radius: 8px;
    box-shadow: 0 4px 16px {theme['accent_secondary']}48;
}}

/* Radio groups */
div[role="radiogroup"] {{ gap: 0.5rem; }}
div[role="radiogroup"] > label {{
    background: {theme['card_bg']}8C;
    border: 1px solid {theme['border']};
    border-radius: 999px;
    padding: 0.4rem 1rem;
    transition: border-color 0.18s ease, background 0.18s ease;
}}
div[role="radiogroup"] > label:hover {{
    border-color: {theme['accent']}73;
    background: {theme['accent']}14;
}}

/* Focus rings */
.stTextInput input:focus,
.stNumberInput input:focus,
.stTextArea textarea:focus {{
    border-color: {theme['accent']} !important;
    box-shadow: 0 0 0 2px {theme['accent']}40 !important;
}}

/* Scrollbar */
::-webkit-scrollbar {{ width: 10px; height: 10px; }}
::-webkit-scrollbar-track {{ background: {theme['main_bg']}; }}
::-webkit-scrollbar-thumb {{
    background: linear-gradient(180deg, {theme['accent']}73, {theme['accent_secondary']}73);
    border-radius: 8px;
    border: 2px solid {theme['main_bg']};
}}
::-webkit-scrollbar-thumb:hover {{
    background: linear-gradient(180deg, {theme['accent']}B3, {theme['accent_secondary']}B3);
}}

h1 {{ font-weight: 700; }}
</style>
"""


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

/* ===== Enterprise / premium polish ===== */

/* App background: subtle radial depth so the platform feels premium, not flat */
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(1100px 600px at 12% -8%, rgba(0,212,255,0.07), transparent 60%),
        radial-gradient(900px 500px at 100% 0%, rgba(123,97,255,0.06), transparent 55%),
        #0B1524;
}

/* Glow + lift on the primary gradient buttons */
.stButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"] {
    box-shadow: 0 4px 16px rgba(0, 102, 255, 0.28);
    transition: transform 0.18s ease, box-shadow 0.18s ease, opacity 0.18s ease;
}
.stButton > button[kind="primary"]:hover,
.stDownloadButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 24px rgba(0, 212, 255, 0.35);
}

/* Secondary buttons: crisp enterprise outline that responds to hover */
.stButton > button[kind="secondary"] {
    border: 1px solid rgba(0, 212, 255, 0.22);
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.02);
    transition: border-color 0.18s ease, background 0.18s ease, transform 0.18s ease;
}
.stButton > button[kind="secondary"]:hover {
    border-color: rgba(0, 212, 255, 0.5);
    background: rgba(0, 212, 255, 0.06);
    transform: translateY(-1px);
}

/* Premium pill styling for radio groups (e.g. the chat mode selector) */
div[role="radiogroup"] {
    gap: 0.5rem;
}
div[role="radiogroup"] > label {
    background: rgba(26, 39, 64, 0.55);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 999px;
    padding: 0.4rem 1rem;
    transition: border-color 0.18s ease, background 0.18s ease;
}
div[role="radiogroup"] > label:hover {
    border-color: rgba(0, 212, 255, 0.45);
    background: rgba(0, 212, 255, 0.08);
}

/* Focus ring for text inputs / selects to feel polished and accessible */
.stTextInput input:focus,
.stNumberInput input:focus,
.stTextArea textarea:focus {
    border-color: #00D4FF !important;
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.25) !important;
}

/* Refined gradient hero headings across the platform */
h1 {
    font-weight: 700;
}

/* Slim, on-brand scrollbar */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: #0B1524; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, rgba(0,212,255,0.45), rgba(0,102,255,0.45));
    border-radius: 8px;
    border: 2px solid #0B1524;
}
::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(180deg, rgba(0,212,255,0.7), rgba(0,102,255,0.7));
}

/* Tabs: smooth hover transition for a polished feel */
.stTabs [data-baseweb="tab"] {
    transition: color 0.18s ease, background 0.18s ease;
    border-radius: 8px 8px 0 0;
}
</style>
"""


def inject_global_css():
    """Call at top of every page after set_page_config. Uses the active theme."""
    import streamlit as st
    theme = _get_active_theme()
    themed_css = _build_css(theme)
    st.markdown(themed_css, unsafe_allow_html=True)


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



def compute_confidence(df, source="ai"):
    """Heuristically score how much to trust generated insights for a dataset.

    The score blends sample size, data completeness and the analysis source.
    Returns ``(level, score_pct, reasons)`` where level is "High"/"Medium"/"Low",
    score_pct is an int 0-100, and reasons is a list of short explanation strings.

    This is a transparency aid, not a statistical guarantee.
    """
    reasons = []
    score = 0.5

    n_rows = len(df) if df is not None else 0
    if n_rows >= 500:
        score += 0.2
        reasons.append(f"Large sample ({n_rows:,} rows)")
    elif n_rows >= 100:
        score += 0.1
        reasons.append(f"Adequate sample ({n_rows:,} rows)")
    elif n_rows < 30:
        score -= 0.2
        reasons.append(f"Small sample ({n_rows:,} rows) \u2014 interpret with caution")

    # Completeness
    try:
        total_cells = (len(df) * len(df.columns)) if df is not None and len(df.columns) else 0
        missing = int(df.isnull().sum().sum()) if total_cells else 0
        completeness = ((total_cells - missing) / total_cells * 100) if total_cells else 100
    except Exception:
        completeness = 100
    if completeness >= 99:
        score += 0.15
        reasons.append(f"High completeness ({completeness:.0f}%)")
    elif completeness >= 95:
        score += 0.1
        reasons.append(f"Good completeness ({completeness:.0f}%)")
    elif completeness < 80:
        score -= 0.15
        reasons.append(f"Notable missing data (completeness {completeness:.0f}%)")

    # Source: rule-based output is deterministic and reproducible.
    if source == "rule_based":
        score += 0.1
        reasons.append("Deterministic rule-based analysis")
    else:
        reasons.append("AI-generated \u2014 verify key numbers before acting")

    score = max(0.05, min(0.95, score))
    score_pct = int(round(score * 100))
    if score_pct >= 75:
        level = "High"
    elif score_pct >= 50:
        level = "Medium"
    else:
        level = "Low"
    return level, score_pct, reasons


def render_confidence_badge(level, score=None, source_label="AI-generated", reasons=None):
    """Render a confidence/disclosure badge above generated insights.

    Args:
        level: "High" / "Medium" / "Low".
        score: Optional 0-100 confidence score to display.
        source_label: e.g. "AI-generated" or "Rule-based".
        reasons: Optional list of short factor strings shown as a caption.
    """
    import streamlit as st

    colors = {"High": "#10B981", "Medium": "#F59E0B", "Low": "#EF4444"}
    color = colors.get(level, "#00D4FF")
    score_txt = f" &middot; {score}% confidence" if score is not None else ""
    tooltip = " | ".join(reasons) if reasons else ""

    st.markdown(
        f"""
    <div title="{tooltip}" style="display:inline-flex; align-items:center; gap:0.5rem;
                border:1px solid {color}55; background:{color}1A; color:{color};
                border-radius:999px; padding:0.3rem 0.85rem; font-size:0.78rem;
                font-weight:700; letter-spacing:0.03em; margin:0.25rem 0 0.5rem 0;">
        <span style="width:8px; height:8px; border-radius:50%; background:{color};
                     display:inline-block;"></span>
        {source_label} &middot; {level} confidence{score_txt}
    </div>
    """,
        unsafe_allow_html=True,
    )
    if reasons:
        st.caption("Confidence factors: " + " &nbsp;|&nbsp; ".join(reasons))
