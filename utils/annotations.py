"""Chart annotation utilities for adding text annotations to Plotly figures.

Annotations are stored in Streamlit session state under the key 'dp_annotations'
as a dict mapping chart_id -> list of {x, y, text} dicts.
"""

import streamlit as st


def _ensure_state():
    """Initialize the dp_annotations session state key if absent."""
    if "dp_annotations" not in st.session_state:
        st.session_state.dp_annotations = {}


def add_annotation(chart_id, x, y, text):
    """Add an annotation to a chart.

    Args:
        chart_id: Unique identifier for the chart.
        x: X-coordinate (value on x-axis).
        y: Y-coordinate (value on y-axis).
        text: Annotation text to display.
    """
    _ensure_state()
    if chart_id not in st.session_state.dp_annotations:
        st.session_state.dp_annotations[chart_id] = []
    st.session_state.dp_annotations[chart_id].append({
        "x": x,
        "y": y,
        "text": text,
    })


def get_annotations(chart_id):
    """Get all annotations for a chart.

    Args:
        chart_id: Unique identifier for the chart.

    Returns:
        List of annotation dicts [{x, y, text}, ...].
    """
    _ensure_state()
    return st.session_state.dp_annotations.get(chart_id, [])


def remove_annotation(chart_id, index):
    """Remove a single annotation by index.

    Args:
        chart_id: Unique identifier for the chart.
        index: Zero-based index of the annotation to remove.
    """
    _ensure_state()
    annotations = st.session_state.dp_annotations.get(chart_id, [])
    if 0 <= index < len(annotations):
        annotations.pop(index)
        st.session_state.dp_annotations[chart_id] = annotations


def apply_annotations_to_figure(fig, annotations):
    """Apply a list of annotations to a Plotly figure.

    Args:
        fig: A Plotly figure object.
        annotations: List of annotation dicts with keys x, y, text.

    Returns:
        The modified figure with annotations added.
    """
    for ann in annotations:
        fig.add_annotation(
            x=ann.get("x"),
            y=ann.get("y"),
            text=ann.get("text", ""),
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=1,
            ax=0,
            ay=-30,
            font=dict(size=11, color="white"),
            bgcolor="rgba(50, 50, 50, 0.8)",
            bordercolor="rgba(255, 255, 255, 0.3)",
            borderwidth=1,
            borderpad=4,
        )
    return fig
