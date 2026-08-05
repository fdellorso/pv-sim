"""PDF report generation with WeasyPrint and matplotlib charts."""

from __future__ import annotations

import base64
import io
from datetime import datetime
from typing import cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure
from weasyprint import HTML

from src.web.models import Simulation, SimulationMetrics, SimulationResult
from src.web.templating import templates

_WINTER_DAY = "2020-01-15"
_SUMMER_DAY = "2020-07-15"


def _figure_png(fig: Figure) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def _daily_curves_png(pv: pd.Series, load: pd.Series) -> str:
    fig, ax = plt.subplots(figsize=(7, 3.4))
    for label, day in (("inverno", _WINTER_DAY), ("estate", _SUMMER_DAY)):
        pv_day = pv.loc[day]
        load_day = load.loc[day]
        hours = pv_day.index.hour + pv_day.index.minute / 60
        ax.plot(hours, pv_day.to_numpy(), label=f"FV {label}", linewidth=1.4)
        ax.plot(hours, load_day.to_numpy(), label=f"Carico {label}", linewidth=1.4, linestyle="--")
    ax.set_xlabel("Ora del giorno")
    ax.set_ylabel("kW")
    ax.set_title("Produzione e carico — giorni tipo (inverno vs estate)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    return _figure_png(fig)


def _cashflow_png(results: list[SimulationResult]) -> str:
    years = [r.year for r in results]
    net = [r.net_cashflow_eur for r in results]
    cumulative = [r.cumulative_cashflow_eur for r in results]

    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.bar(years, net, color="#10b981", alpha=0.9, label="Netto annuo")
    ax2 = ax.twinx()
    ax2.plot(
        years,
        cumulative,
        color="#6366f1",
        marker="o",
        markersize=3,
        linewidth=1.4,
        label="Cumulativo",
    )
    ax.set_xlabel("Anno")
    ax.set_ylabel("Netto (EUR)")
    ax2.set_ylabel("Cumulativo (EUR)")
    ax.legend(loc="upper left", fontsize=8)
    ax2.legend(loc="lower right", fontsize=8)
    ax.grid(alpha=0.3, axis="y")
    return _figure_png(fig)


def build_report_pdf(
    sim: Simulation,
    metrics: SimulationMetrics,
    results: list[SimulationResult],
    curves: tuple[pd.Series, pd.Series] | None,
) -> bytes:
    """Render the simulation report HTML and return PDF bytes."""
    context = {
        "name": sim.name,
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "sim": sim,
        "metrics": metrics,
        "results": results,
        "daily_png": _daily_curves_png(curves[0], curves[1]) if curves else None,
        "cashflow_png": _cashflow_png(results) if results else None,
    }
    html = templates.get_template("report.html").render(**context)
    return cast(bytes, HTML(string=html).write_pdf())
