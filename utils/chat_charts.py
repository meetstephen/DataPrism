"""Safe chart rendering for the AI chat features.

SECURITY NOTE
-------------
This module replaces an earlier implementation that asked the LLM to return
raw Python code and ran it with ``exec(code, {"__builtins__": {}}, ...)``.
That pattern is NOT a real sandbox: Python objects remain reachable via
attribute/introspection chains (e.g. ``().__class__.__bases__[0]
.__subclasses__()``) even with ``__builtins__`` emptied, which allows full
arbitrary code execution regardless of any string-based denylist. Any
LLM-authored code block — including one influenced by adversarial content in
an uploaded document or a crafted prompt — could have achieved remote code
execution against the server process (and access to secrets in
``st.secrets``).

Instead, the LLM is asked to return a small, strictly-typed JSON "chart
spec" describing *what* to plot. This module turns that spec into a Plotly
figure using an allow-listed set of chart types and columns that are
validated against the actual DataFrame. No user- or model-supplied code is
ever executed.
"""
from __future__ import annotations

import json
import re

import pandas as pd
import plotly.express as px

ALLOWED_CHART_TYPES = {"bar", "line", "scatter", "histogram", "box", "pie"}
ALLOWED_AGGS = {"sum", "mean", "median", "count", "min", "max", "none"}

CHART_SPEC_INSTRUCTIONS = (
    "If a visualization would materially help, do NOT include Python code. "
    "Instead, append a single fenced ```chartspec block containing ONLY a "
    "JSON object (no comments, no trailing text) with this shape:\n"
    '{"chart_type": "bar|line|scatter|histogram|box|pie", '
    '"x": "<existing column name>", '
    '"y": "<existing column name, omit for histogram/pie>", '
    '"color": "<existing column name, optional>", '
    '"agg": "sum|mean|median|count|min|max|none", '
    '"title": "<short chart title>"}\n'
    "Only reference column names that literally appear in the dataset schema "
    "given above. Omit the chartspec block entirely if no chart is useful."
)


def extract_chart_spec(response_text: str) -> dict | None:
    """Pull the first ```chartspec block out of an LLM response, if any.

    Returns a parsed dict, or None if absent / malformed. Never raises.
    """
    if not response_text or "```chartspec" not in response_text:
        return None
    try:
        block = response_text.split("```chartspec", 1)[1].split("```", 1)[0].strip()
        # Guard against pathological input before handing to json.loads
        if len(block) > 2000:
            return None
        spec = json.loads(block)
        if not isinstance(spec, dict):
            return None
        return spec
    except (json.JSONDecodeError, IndexError, ValueError):
        return None


def strip_chart_spec(response_text: str) -> str:
    """Remove the ```chartspec fenced block so it isn't shown to the user as text."""
    return re.sub(r"```chartspec.*?```", "", response_text, flags=re.DOTALL).strip()


def build_chart_from_spec(df: pd.DataFrame, spec: dict):
    """Build a Plotly figure from a validated chart spec. Returns a Figure or None.

    Every field is validated against the real DataFrame and an allow-list —
    nothing from ``spec`` is ever evaluated or executed as code.
    """
    if not isinstance(spec, dict) or df is None or df.empty:
        return None

    chart_type = str(spec.get("chart_type", "")).strip().lower()
    if chart_type not in ALLOWED_CHART_TYPES:
        return None

    columns = set(df.columns.astype(str))

    def _valid_col(name):
        return isinstance(name, str) and name in columns

    x = spec.get("x")
    y = spec.get("y")
    color = spec.get("color")
    agg = str(spec.get("agg", "none")).strip().lower()
    title = str(spec.get("title") or "")[:120]  # bounded, rendered as plain text by Plotly

    if agg not in ALLOWED_AGGS:
        agg = "none"
    if not _valid_col(x):
        return None
    if y is not None and not _valid_col(y):
        y = None
    if color is not None and not _valid_col(color):
        color = None

    plot_df = df
    try:
        if agg != "none" and y is not None:
            group_cols = [x] + ([color] if color else [])
            plot_df = df.groupby(group_cols, dropna=False, as_index=False)[y].agg(agg)

        common = dict(template="plotly_dark", title=title or None,
                       color_discrete_sequence=["#00D4FF"])

        if chart_type == "bar":
            fig = px.bar(plot_df, x=x, y=y, color=color, **common)
        elif chart_type == "line":
            fig = px.line(plot_df, x=x, y=y, color=color, **common)
        elif chart_type == "scatter":
            fig = px.scatter(plot_df, x=x, y=y, color=color, **common)
        elif chart_type == "histogram":
            fig = px.histogram(plot_df, x=x, color=color, **common)
        elif chart_type == "box":
            fig = px.box(plot_df, x=x, y=y, color=color, **common)
        elif chart_type == "pie":
            fig = px.pie(plot_df, names=x, values=y, **{k: v for k, v in common.items() if k != "color_discrete_sequence"})
        else:
            return None

        fig.update_layout(margin=dict(t=40, l=10, r=10, b=10))
        return fig
    except Exception:
        # Any data-shape mismatch degrades to "no chart", never an error to the user
        return None
