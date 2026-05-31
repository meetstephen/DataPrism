"""Time series forecasting utilities using Holt-Winters (statsmodels)."""
import pandas as pd
import numpy as np


def run_time_series_forecast(df, date_col, value_col, periods=12, seasonal_periods=None):
    """Run Holt-Winters exponential smoothing forecast.

    Args:
        df: DataFrame with date and value columns.
        date_col: Name of the date/time column.
        value_col: Name of the numeric value column.
        periods: Number of periods to forecast ahead.
        seasonal_periods: Seasonal period length (auto-detected if None).

    Returns a dict with keys: historical (DataFrame), forecast (DataFrame),
    model_summary (str), or error (str) on failure.
    """
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
    except ImportError:
        return {"error": "statsmodels is required for forecasting."}

    try:
        # Prepare time series
        ts_df = df[[date_col, value_col]].copy()
        ts_df[date_col] = pd.to_datetime(ts_df[date_col], errors="coerce")
        ts_df = ts_df.dropna()

        if len(ts_df) < 6:
            return {"error": "Need at least 6 data points for forecasting."}

        ts_df = ts_df.sort_values(date_col).reset_index(drop=True)

        # Aggregate by period if duplicates
        ts_df = ts_df.groupby(date_col)[value_col].mean().reset_index()
        ts_df = ts_df.set_index(date_col)

        # Infer frequency
        if ts_df.index.freq is None:
            inferred_freq = pd.infer_freq(ts_df.index)
            if inferred_freq:
                ts_df = ts_df.asfreq(inferred_freq)
            else:
                # Default to monthly
                ts_df = ts_df.asfreq("MS")

        # Fill any gaps
        ts_df[value_col] = ts_df[value_col].interpolate(method="linear")

        series = ts_df[value_col]

        # Determine seasonal periods
        if seasonal_periods is None:
            freq_str = str(ts_df.index.freq) if ts_df.index.freq else "M"
            if "Y" in freq_str or "A" in freq_str:
                seasonal_periods = None  # no seasonality for yearly
            elif "Q" in freq_str:
                seasonal_periods = 4
            elif "M" in freq_str:
                seasonal_periods = 12
            elif "W" in freq_str:
                seasonal_periods = 52
            elif "D" in freq_str:
                seasonal_periods = 7
            else:
                seasonal_periods = None

        # Fit model
        if seasonal_periods and len(series) >= seasonal_periods * 2:
            model = ExponentialSmoothing(
                series,
                trend="add",
                seasonal="add",
                seasonal_periods=seasonal_periods,
            ).fit(optimized=True)
        else:
            model = ExponentialSmoothing(
                series,
                trend="add",
                seasonal=None,
            ).fit(optimized=True)

        # Forecast
        forecast_values = model.forecast(periods)

        # Build result DataFrames
        historical = pd.DataFrame({
            "date": series.index,
            "value": series.values,
            "type": "historical",
        }).reset_index(drop=True)

        forecast_df = pd.DataFrame({
            "date": forecast_values.index,
            "value": forecast_values.values,
            "type": "forecast",
        }).reset_index(drop=True)

        return {
            "historical": historical,
            "forecast": forecast_df,
            "model_summary": f"Holt-Winters (trend=add, seasonal={'add' if seasonal_periods else 'none'})",
            "aic": round(float(model.aic), 2) if hasattr(model, "aic") else None,
        }

    except Exception as e:
        return {"error": f"Forecasting failed: {str(e)}"}


def build_forecast_chart(forecast_result):
    """Build a Plotly figure showing historical data and forecast.

    Args:
        forecast_result: Dict returned by run_time_series_forecast.

    Returns a Plotly figure or None on failure.
    """
    import plotly.graph_objects as go

    if "error" in forecast_result:
        return None

    historical = forecast_result.get("historical")
    forecast_df = forecast_result.get("forecast")

    if historical is None or forecast_df is None:
        return None

    fig = go.Figure()

    # Historical line
    fig.add_trace(go.Scatter(
        x=historical["date"],
        y=historical["value"],
        mode="lines+markers",
        name="Historical",
        line=dict(color="#00D4FF", width=2),
        marker=dict(size=4),
    ))

    # Forecast line
    fig.add_trace(go.Scatter(
        x=forecast_df["date"],
        y=forecast_df["value"],
        mode="lines+markers",
        name="Forecast",
        line=dict(color="#F59E0B", width=2, dash="dash"),
        marker=dict(size=4),
    ))

    fig.update_layout(
        title="Time Series Forecast (Holt-Winters)",
        xaxis_title="Date",
        yaxis_title="Value",
        template="plotly_dark",
        font=dict(family="Arial, sans-serif", size=12),
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
    )

    return fig
