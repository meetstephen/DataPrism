"""Time series forecasting utilities using Holt-Winters exponential smoothing."""
import pandas as pd
import numpy as np


def run_time_series_forecast(df, date_col, value_col, periods=12, freq='MS'):
    """Run Holt-Winters forecasting on a time series.
    Returns dict with actuals_df, forecast_df (yhat, yhat_lower, yhat_upper),
    and combined_df for plotting.
    Falls back to simple exponential smoothing if seasonal model fails.
    """
    from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing

    work_df = df[[date_col, value_col]].dropna().copy()
    work_df[date_col] = pd.to_datetime(work_df[date_col], errors='coerce')
    work_df = work_df.dropna(subset=[date_col])
    work_df = work_df.sort_values(date_col)

    # Aggregate by frequency
    work_df = work_df.set_index(date_col)
    ts = work_df[value_col].resample(freq).mean().dropna()

    if len(ts) < 4:
        return {
            "actuals_df": pd.DataFrame({"date": ts.index, "value": ts.values}),
            "forecast_df": pd.DataFrame(),
            "combined_df": pd.DataFrame({"date": ts.index, "value": ts.values}),
        }

    # Attempt Holt-Winters with seasonality
    model = None
    fitted = None
    try:
        seasonal_periods = min(12, len(ts) // 2)
        if seasonal_periods >= 2 and len(ts) >= 2 * seasonal_periods:
            model = ExponentialSmoothing(
                ts, trend='add', seasonal='add',
                seasonal_periods=seasonal_periods
            ).fit(optimized=True)
            fitted = model
    except Exception:
        fitted = None

    # Fallback to simple exponential smoothing
    if fitted is None:
        try:
            model = SimpleExpSmoothing(ts).fit(optimized=True)
            fitted = model
        except Exception:
            return {
                "actuals_df": pd.DataFrame({"date": ts.index, "value": ts.values}),
                "forecast_df": pd.DataFrame(),
                "combined_df": pd.DataFrame({"date": ts.index, "value": ts.values}),
            }

    # Generate forecast
    forecast = fitted.forecast(periods)
    forecast_index = pd.date_range(start=ts.index[-1], periods=periods + 1, freq=freq)[1:]

    # Confidence band (approximate using residual std)
    residuals = ts - fitted.fittedvalues
    std_resid = residuals.std()
    yhat_lower = forecast - 1.96 * std_resid
    yhat_upper = forecast + 1.96 * std_resid

    actuals_df = pd.DataFrame({"date": ts.index, "value": ts.values})
    forecast_df = pd.DataFrame({
        "date": forecast_index,
        "yhat": forecast.values,
        "yhat_lower": yhat_lower.values,
        "yhat_upper": yhat_upper.values,
    })

    combined_df = pd.concat([
        actuals_df.rename(columns={"value": "yhat"}),
        forecast_df[["date", "yhat"]]
    ], ignore_index=True)

    return {
        "actuals_df": actuals_df,
        "forecast_df": forecast_df,
        "combined_df": combined_df,
    }


def build_forecast_chart(result_dict):
    """Build a Plotly figure showing actuals, forecast, and confidence band.
    Returns a Plotly Figure.
    """
    import plotly.graph_objects as go

    fig = go.Figure()

    actuals_df = result_dict.get("actuals_df", pd.DataFrame())
    forecast_df = result_dict.get("forecast_df", pd.DataFrame())

    # Actuals (solid line)
    if not actuals_df.empty:
        fig.add_trace(go.Scatter(
            x=actuals_df["date"],
            y=actuals_df["value"],
            mode="lines",
            name="Actuals",
            line=dict(color="#2563EB", width=2),
        ))

    # Forecast (dashed line)
    if not forecast_df.empty:
        fig.add_trace(go.Scatter(
            x=forecast_df["date"],
            y=forecast_df["yhat"],
            mode="lines",
            name="Forecast",
            line=dict(color="#DC2626", width=2, dash="dash"),
        ))

        # Confidence band (filled area)
        fig.add_trace(go.Scatter(
            x=pd.concat([forecast_df["date"], forecast_df["date"][::-1]]),
            y=pd.concat([forecast_df["yhat_upper"], forecast_df["yhat_lower"][::-1]]),
            fill="toself",
            fillcolor="rgba(220, 38, 38, 0.1)",
            line=dict(color="rgba(220, 38, 38, 0)"),
            name="95% Confidence",
            showlegend=True,
        ))

    fig.update_layout(
        title="Time Series Forecast",
        xaxis_title="Date",
        yaxis_title="Value",
        template="plotly_white",
        hovermode="x unified",
    )

    return fig
