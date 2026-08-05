"""Unit tests for the worker job helpers (pure functions)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.engine.battery_model import BatteryParams
from src.engine.economic_model import (
    EconomicParams,
    EconomicResult,
    run_economics,
)
from src.worker.jobs import _to_metrics, _to_result_rows, _write_curves

DT_HOURS = 0.25


def _economic() -> EconomicResult:
    index = pd.date_range("2020-01-01", periods=96, freq="15min", tz="Europe/Rome")
    pv = pd.Series(np.full(96, 1.0), index=index)
    load = pd.Series(np.full(96, 2.0), index=index)
    economic = EconomicParams(
        horizon_years=5,
        investment_cost_eur=10000,
        purchase_eur_kwh=0.30,
        sell_eur_kwh=0.12,
    )
    return run_economics(pv, load, economic, BatteryParams(capacity_kwh=0), DT_HOURS)


def test_to_result_rows_one_per_year() -> None:
    rows = _to_result_rows(42, _economic())
    assert len(rows) == 5
    assert [r.year for r in rows] == [1, 2, 3, 4, 5]
    assert all(r.simulation_id == 42 for r in rows)
    assert rows[0].net_cashflow_eur > 0


def test_to_metrics_averages() -> None:
    metrics = _to_metrics(42, _economic())
    assert metrics.simulation_id == 42
    assert metrics.npv_eur == pytest.approx(_economic().npv_eur)
    # toy data (24 kWh/yr vs 10 kEUR investment) never pays back
    assert metrics.payback_years is None


def test_write_curves_roundtrip(tmp_path: Path, monkeypatch) -> None:
    from src.web.config import get_settings

    monkeypatch.setenv("SIMULATION_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()

    index = pd.date_range("2020-01-01", periods=8, freq="15min", tz="Europe/Rome")
    pv = pd.Series([1.0] * 8, index=index)
    load = pd.Series([2.0] * 8, index=index)
    _write_curves(7, pv, load)

    pv_data = json.loads((tmp_path / "7" / "pv_year1.json").read_text())
    load_data = json.loads((tmp_path / "7" / "load_year1.json").read_text())
    assert pv_data["tz"] == "Europe/Rome"
    assert len(pv_data["values"]) == 8
    assert load_data["values"][0] == 2.0

    get_settings.cache_clear()
