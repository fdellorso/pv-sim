"""Server-side Plotly chart builders for the result dashboard."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pandas as pd
import plotly.graph_objects as go

from src.web.config import get_settings
from src.web.models import SimulationResult

_WINTER_DAY = "2020-01-15"
_SUMMER_DAY = "2020-07-15"


def read_curves(simulation_id: int) -> tuple[pd.Series, pd.Series] | None:
    """Load the persisted year-1 PV and load series, or ``None`` if absent."""
    data_dir = Path(get_settings().simulation_data_dir) / str(simulation_id)
    pv_file = data_dir / "pv_year1.json"
    load_file = data_dir / "load_year1.json"
    if not pv_file.exists() or not load_file.exists():
        return None

    def load(path: Path) -> pd.Series:
        data = json.loads(path.read_text())
        index = pd.date_range(
            start=data["start"],
            periods=len(data["values"]),
            freq=data.get("freq", "15min"),
            tz=data.get("tz"),
        )
        return pd.Series(data["values"], index=index)

    return load(pv_file), load(load_file)


def daily_curves_figure(pv: pd.Series, load: pd.Series) -> go.Figure:
    """Overlay PV and load on a winter and a summer day (hour of day on x)."""
    fig = go.Figure()

    def day_traces(day: str, label: str) -> None:
        for series, color, name in (
            (pv, "#f59e0b", f"FV {label}"),
            (load, "#3b82f6", f"Carico {label}"),
        ):
            day_values = cast(pd.Series, series.loc[day])
            hour_series = cast(pd.DatetimeIndex, day_values.index).to_series()
            hours = (hour_series.dt.hour + hour_series.dt.minute / 60).to_numpy()
            fig.add_trace(
                go.Scatter(
                    x=hours.tolist(),
                    y=day_values.to_numpy(),
                    mode="lines",
                    name=name,
                    line={"color": color, "dash": "solid" if "FV" in name else "dot"},
                )
            )

    day_traces(_WINTER_DAY, "inverno")
    day_traces(_SUMMER_DAY, "estate")

    fig.update_layout(
        title="Produzione e carico — giorni tipo (inverno vs estate)",
        xaxis={"title": "Ora del giorno"},
        yaxis={"title": "kW"},
        legend={"orientation": "h", "y": -0.25},
        height=420,
    )
    return fig


def cashflow_figure(results: list[SimulationResult]) -> go.Figure:
    """Bar of yearly net cashflow plus cumulative line on a secondary axis."""
    years = [r.year for r in results]
    net = [r.net_cashflow_eur for r in results]
    cumulative = [r.cumulative_cashflow_eur for r in results]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(x=years, y=net, name="Netto annuo", marker_color="#10b981")
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=cumulative,
            name="Cumulativo",
            yaxis="y2",
            mode="lines+markers",
            line={"color": "#6366f1"},
        )
    )
    fig.update_layout(
        title="Cashflow annuale",
        xaxis={"title": "Anno"},
        yaxis={"title": "Netto (EUR)"},
        yaxis2={"overlaying": "y", "side": "right", "title": "Cumulativo (EUR)"},
        legend={"orientation": "h", "y": -0.25},
        height=420,
    )
    return fig
