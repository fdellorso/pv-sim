"""Unit tests for the economic model."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.engine.battery_model import BatteryParams
from src.engine.economic_model import (
    EconomicParams,
    compute_annuity,
    compute_irr,
    run_economics,
)

DT_HOURS = 0.25


def _make_series(n: int = 96) -> pd.Series:
    index = pd.date_range("2020-01-01", periods=n, freq="15min", tz="Europe/Rome")
    return pd.Series(np.ones(n), index=index)


def test_compute_annuity_known_value() -> None:
    assert compute_annuity(12000, 4.5, 10) == pytest.approx(1516.55, abs=0.01)


def test_compute_annuity_zero_interest() -> None:
    assert compute_annuity(12000, 0.0, 10) == pytest.approx(1200.0)


def test_compute_annuity_zero_principal() -> None:
    assert compute_annuity(0, 4.5, 10) == 0.0


def test_compute_irr_known() -> None:
    assert compute_irr([-100.0, 110.0]) == pytest.approx(10.0, abs=1e-4)


def test_compute_irr_no_root_returns_none() -> None:
    assert compute_irr([-100.0, -50.0]) is None


def test_run_economics_basic() -> None:
    pv = _make_series()  # 1 kW for 24h -> 24 kWh
    load = _make_series() * 2  # 2 kW -> 48 kWh
    economic = EconomicParams(
        horizon_years=10,
        investment_cost_eur=10000,
        purchase_eur_kwh=0.30,
        sell_eur_kwh=0.12,
    )
    result = run_economics(pv, load, economic, BatteryParams(capacity_kwh=0))

    assert len(result.annual) == 10
    first = result.annual[0]
    assert first.pv_production_kwh == pytest.approx(24.0)
    assert first.load_consumption_kwh == pytest.approx(48.0)
    # all production self-consumed (load > pv), none exported
    assert first.self_consumption_kwh == pytest.approx(24.0)
    assert first.grid_export_kwh == pytest.approx(0.0)
    assert first.grid_import_kwh == pytest.approx(24.0)
    # production degrades each year
    assert result.annual[1].pv_production_kwh < result.annual[0].pv_production_kwh
    # with a 10 kEUR investment and ~7 EUR/yr savings, NPV is negative
    assert result.npv_eur < 0
    assert result.payback_years is None


def test_run_economics_with_loan_no_double_count() -> None:
    """With loan, year-0 outlay is only grid activation (annuity replaces it)."""
    pv = _make_series()
    load = _make_series() * 2
    economic = EconomicParams(
        horizon_years=10,
        investment_cost_eur=10000,
        purchase_eur_kwh=0.30,
        sell_eur_kwh=0.12,
        loan_interest_pct=4.5,
        loan_years=10,
        grid_activation_eur=100.0,
    )
    result = run_economics(pv, load, economic, BatteryParams(capacity_kwh=0))
    assert result.annual[0].loan_payment_eur > 0
    assert result.npv_eur != pytest.approx(0.0)
