"""
Reusable Plotly visualization functions with consistent professional styling.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


CHART_TEMPLATE = "plotly_dark"
CHART_FONT = dict(family="Arial, sans-serif", size=12)
CHART_MARGIN = dict(l=60, r=30, t=50, b=60)
COLOR_SEQUENCE = px.colors.qualitative.Set2


def _apply_layout(fig, title):
    """Apply consistent layout styling to a figure."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, family="Arial, sans-serif")),
        template=CHART_TEMPLATE,
        font=CHART_FONT,
        margin=CHART_MARGIN,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        height=400
    )
    return fig


def create_bar_chart(df, x, y, title, color=None):
    """
    Create a vertical bar chart.

    Args:
        df: DataFrame with data.
        x: Column name for x-axis.
        y: Column name for y-axis.
        title: Chart title.
        color: Optional column for color grouping.

    Returns:
        plotly.graph_objects.Figure
    """
    fig = px.bar(
        df, x=x, y=y, title=title, color=color,
        color_discrete_sequence=COLOR_SEQUENCE
    )
    return _apply_layout(fig, title)


def create_grouped_bar_chart(df, x, y, color, title):
    """
    Create a grouped bar chart.

    Args:
        df: DataFrame with data.
        x: Column name for x-axis.
        y: Column name for y-axis.
        color: Column name for color grouping.
        title: Chart title.

    Returns:
        plotly.graph_objects.Figure
    """
    fig = px.bar(
        df, x=x, y=y, color=color, title=title,
        barmode="group",
        color_discrete_sequence=COLOR_SEQUENCE
    )
    return _apply_layout(fig, title)


def create_pie_chart(df, names, values, title):
    """
    Create a pie/donut chart.

    Args:
        df: DataFrame with data.
        names: Column name for slice labels.
        values: Column name for slice values.
        title: Chart title.

    Returns:
        plotly.graph_objects.Figure
    """
    fig = px.pie(
        df, names=names, values=values, title=title,
        hole=0.4,
        color_discrete_sequence=COLOR_SEQUENCE
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _apply_layout(fig, title)


def create_horizontal_bar_chart(df, x, y, title):
    """
    Create a horizontal bar chart.

    Args:
        df: DataFrame with data.
        x: Column name for x-axis (values).
        y: Column name for y-axis (categories).
        title: Chart title.

    Returns:
        plotly.graph_objects.Figure
    """
    fig = px.bar(
        df, x=x, y=y, title=title, orientation="h",
        color_discrete_sequence=COLOR_SEQUENCE
    )
    return _apply_layout(fig, title)


def create_scatter_plot(df, x, y, title, color=None):
    """
    Create a scatter plot.

    Args:
        df: DataFrame with data.
        x: Column name for x-axis.
        y: Column name for y-axis.
        title: Chart title.
        color: Optional column for color grouping.

    Returns:
        plotly.graph_objects.Figure
    """
    fig = px.scatter(
        df, x=x, y=y, title=title, color=color,
        color_discrete_sequence=COLOR_SEQUENCE
    )
    return _apply_layout(fig, title)


def create_histogram(df, x, title, nbins=30):
    """
    Create a histogram.

    Args:
        df: DataFrame with data.
        x: Column name for distribution.
        title: Chart title.
        nbins: Number of bins.

    Returns:
        plotly.graph_objects.Figure
    """
    fig = px.histogram(
        df, x=x, title=title, nbins=nbins,
        color_discrete_sequence=COLOR_SEQUENCE
    )
    return _apply_layout(fig, title)


def create_heatmap(correlation_matrix, title):
    """
    Create a correlation heatmap.

    Args:
        correlation_matrix: DataFrame or 2D array of correlations.
        title: Chart title.

    Returns:
        plotly.graph_objects.Figure
    """
    fig = go.Figure(data=go.Heatmap(
        z=correlation_matrix.values,
        x=correlation_matrix.columns.tolist(),
        y=correlation_matrix.index.tolist(),
        colorscale="RdBu_r",
        zmin=-1, zmax=1,
        text=correlation_matrix.round(2).values,
        texttemplate="%{text}",
        textfont={"size": 10}
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, family="Arial, sans-serif")),
        template=CHART_TEMPLATE,
        font=CHART_FONT,
        margin=CHART_MARGIN,
        height=450
    )
    return fig


def create_box_plot(df, x, y, title):
    """
    Create a box plot.

    Args:
        df: DataFrame with data.
        x: Column name for categories.
        y: Column name for values.
        title: Chart title.

    Returns:
        plotly.graph_objects.Figure
    """
    fig = px.box(
        df, x=x, y=y, title=title,
        color_discrete_sequence=COLOR_SEQUENCE
    )
    return _apply_layout(fig, title)


def create_line_chart(df, x, y, title, color=None):
    """
    Create a line chart.

    Args:
        df: DataFrame with data.
        x: Column name for x-axis.
        y: Column name for y-axis.
        title: Chart title.
        color: Optional column for color grouping.

    Returns:
        plotly.graph_objects.Figure
    """
    fig = px.line(
        df, x=x, y=y, title=title, color=color,
        color_discrete_sequence=COLOR_SEQUENCE
    )
    return _apply_layout(fig, title)



def render_chart_with_table(fig, data=None, key=None, table_label="View as table",
                            caption=None, use_container_width=True):
    """Render a Plotly chart with an accessible "View as table" toggle.

    Displays the chart, then an expander revealing the underlying data as a
    table. This improves accessibility (screen readers, low-vision users) and
    lets analysts inspect exact values behind a visualization.

    Args:
        fig: A Plotly figure to display.
        data: Optional DataFrame/Series with the data behind the chart.
        key: Optional unique key (reserved for future widget use).
        table_label: Label shown on the expander toggle.
        caption: Optional caption rendered above the table.
        use_container_width: Passed through to ``st.plotly_chart``.
    """
    import streamlit as st

    st.plotly_chart(fig, use_container_width=use_container_width)
    if data is not None:
        with st.expander(f"\U0001F4CB {table_label}"):
            if caption:
                st.caption(caption)
            st.dataframe(data, use_container_width=True)
