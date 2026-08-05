"""Unit tests for the battery capacity optimizer."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.engine.battery_model import BatteryParams
from src.engine.economic_model import EconomicParams
from src.engine.load_model import generate_synthetic_curve
from src.engine.optimizer import sweep_capacities

DT_HOURS = 0.25


@pytest.fixture()
def inputs() -> tuple[pd.Series, pd.Series]:
    index = pd.date_range("2020-01-01", periods=96 * 365, freq="15min", tz="Europe/Rome")
    # strong daytime production
    hours = np.arange(96 * 365) % 96
    pv = pd.Series(np.maximum(np.sin(hours / 96 * np.pi * 0.8) * 6, 0), index=index)
    load = generate_synthetic_curve(index, 4000)
    return pv, load


def test_sweep_returns_sorted_scenarios(inputs: tuple[pd.Series, pd.Series]) -> None:
    pv, load = inputs
    economic = EconomicParams(
        horizon_years=25,
        investment_cost_eur=9000,
        purchase_eur_kwh=0.30,
        sell_eur_kwh=0.12,
    )
    battery = BatteryParams(capacity_kwh=0, c_rate=0.5)
    scenarios = sweep_capacities(pv, load, economic, battery, [0, 5, 10], 600, 400)

    assert len(scenarios) == 3
    # sorted by NPV descending
    npvs = [s.npv_eur for s in scenarios]
    assert npvs == sorted(npvs, reverse=True)
    # best scenario carries the full economic result for persistence
    assert len(scenarios[0].economic.annual) == 25


def test_sweep_with_no_battery_and_positive_investment(
    inputs: tuple[pd.Series, pd.Series],
) -> None:
    """A battery with high cost should never beat the no-battery baseline here."""
    pv, load = inputs
    economic = EconomicParams(
        horizon_years=10,
        investment_cost_eur=9000,
        purchase_eur_kwh=0.30,
        sell_eur_kwh=0.12,
    )
    battery = BatteryParams(capacity_kwh=0, c_rate=0.5)
    scenarios = sweep_capacities(pv, load, economic, battery, [0, 10], 600, 400)
    by_capacity = {s.capacity_kwh: s for s in scenarios}
    assert by_capacity[0].npv_eur >= by_capacity[10].npv_eur
