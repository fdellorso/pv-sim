"""Unit tests for the battery model."""

from __future__ import annotations

import pandas as pd
import pytest

from src.engine.battery_model import BatteryParams, effective_capacity, run_battery

DT_HOURS = 0.25


def _series(values: list[float]) -> pd.Series:
    index = pd.date_range("2020-01-01", periods=len(values), freq="15min", tz="Europe/Rome")
    return pd.Series(values, index=index)


def test_effective_capacity_degradation() -> None:
    battery = BatteryParams(capacity_kwh=10.0, degradation_pct_year=2.0)
    assert effective_capacity(battery, 1) == pytest.approx(10.0)
    assert effective_capacity(battery, 2) == pytest.approx(9.8)


def test_no_battery_passthrough() -> None:
    """With zero capacity, grid flows equal raw surplus/deficit."""
    pv = _series([1.0, 0.0, 0.5, 0.0])
    load = _series([0.0, 1.0, 0.0, 0.5])
    res = run_battery(pv, load, BatteryParams(capacity_kwh=0.0), dt_hours=DT_HOURS)
    assert res.grid_export_kwh == pytest.approx((1.0 + 0.5) * DT_HOURS)
    assert res.grid_import_kwh == pytest.approx((1.0 + 0.5) * DT_HOURS)
    assert res.autoconsumo_kwh == pytest.approx(0.0)


def test_battery_shifts_energy() -> None:
    """Surplus charges, deficit discharges: grid import drops to zero."""
    # 8 kW surplus for 1h, then 8 kW deficit for 1h; 10 kWh battery
    # c_rate=1.0 (p_max=10 kW) and ideal efficiency so the shift is lossless
    pv = _series([8.0, 0.0, 0.0, 0.0])
    load = _series([0.0, 8.0, 0.0, 0.0])
    battery = BatteryParams(capacity_kwh=10.0, c_rate=1.0, efficiency=1.0)
    res = run_battery(pv, load, battery, dt_hours=DT_HOURS)

    assert res.battery_charge_kwh == pytest.approx(2.0, abs=1e-9)  # 8 kW * 0.25h
    assert res.grid_import_kwh == pytest.approx(0.0, abs=1e-9)
    assert res.grid_export_kwh == pytest.approx(0.0, abs=1e-9)


def test_c_rate_limits_power() -> None:
    """0.5C on 10 kWh = 5 kW max; a 20 kW step is capped."""
    pv = _series([20.0, 0.0, 0.0, 0.0])
    load = _series([0.0, 0.0, 0.0, 0.0])
    battery = BatteryParams(capacity_kwh=10.0, c_rate=0.5, efficiency=0.95)
    res = run_battery(pv, load, battery, dt_hours=DT_HOURS)
    # capped at 5 kW * 0.25h = 1.25 kWh, rest exported
    assert res.battery_charge_kwh == pytest.approx(1.25, abs=1e-9)
    assert res.grid_export_kwh == pytest.approx((20.0 - 5.0) * DT_HOURS, abs=1e-9)


def test_autosufficienza_computation() -> None:
    pv = _series([2.0, 0.0, 0.0, 0.0])
    load = _series([1.0, 1.0, 0.0, 0.0])
    res = run_battery(pv, load, BatteryParams(capacity_kwh=0.0), dt_hours=DT_HOURS)
    # 1 kWh consumed directly, 1 kWh from grid
    assert res.autosufficienza_pct == pytest.approx(50.0)
