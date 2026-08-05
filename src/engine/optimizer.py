"""Battery capacity optimizer: sweep scenarios and pick the optimum."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.engine.battery_model import BatteryParams
from src.engine.economic_model import EconomicParams, EconomicResult, run_economics

DT_HOURS = 0.25


@dataclass(frozen=True)
class ScenarioResult:
    """Metrics for one swept battery capacity, with the full economic result."""

    capacity_kwh: float
    npv_eur: float
    irr_pct: float | None
    payback_years: float | None
    autoconsumo_pct: float
    autosufficienza_pct: float
    economic: EconomicResult


def sweep_capacities(
    pv_year1: pd.Series,
    load: pd.Series,
    economic: EconomicParams,
    battery: BatteryParams,
    capacities: list[float],
    battery_cost_eur_per_kwh: float,
    battery_replace_eur_per_kwh: float,
    dt_hours: float = DT_HOURS,
) -> list[ScenarioResult]:
    """Run one scenario per battery capacity, sorted by NPV descending.

    The PV-only investment is recovered from ``economic.investment_cost_eur``
    assuming the base battery cost ``battery.capacity_kwh * cost_per_kwh``;
    each scenario then invests ``pv_only + capacity * cost_per_kwh`` and
    replaces the battery for ``capacity * replace_per_kwh``.
    """
    pv_investment = economic.investment_cost_eur - battery.capacity_kwh * battery_cost_eur_per_kwh
    scenarios: list[ScenarioResult] = []

    for capacity in capacities:
        scenario_battery = BatteryParams(
            capacity_kwh=capacity,
            c_rate=battery.c_rate,
            efficiency=battery.efficiency,
            soc_min_pct=battery.soc_min_pct,
            soc_max_pct=battery.soc_max_pct,
            degradation_pct_year=battery.degradation_pct_year,
        )
        scenario_economic = EconomicParams(
            horizon_years=economic.horizon_years,
            investment_cost_eur=pv_investment + capacity * battery_cost_eur_per_kwh,
            purchase_eur_kwh=economic.purchase_eur_kwh,
            sell_eur_kwh=economic.sell_eur_kwh,
            maintenance_annual_eur=economic.maintenance_annual_eur,
            inverter_replacement_cost_eur=economic.inverter_replacement_cost_eur,
            inverter_replace_at_year=economic.inverter_replace_at_year,
            battery_replacement_cost_eur=capacity * battery_replace_eur_per_kwh,
            battery_replace_at_year=economic.battery_replace_at_year,
            grid_activation_eur=economic.grid_activation_eur,
            grid_annual_eur=economic.grid_annual_eur,
            loan_interest_pct=economic.loan_interest_pct,
            loan_years=economic.loan_years,
            pv_degradation_pct_year=economic.pv_degradation_pct_year,
            discount_rate_pct=economic.discount_rate_pct,
        )
        result = run_economics(pv_year1, load, scenario_economic, scenario_battery, dt_hours)
        scenarios.append(
            ScenarioResult(
                capacity_kwh=capacity,
                npv_eur=result.npv_eur,
                irr_pct=result.irr_pct,
                payback_years=result.payback_years,
                autoconsumo_pct=result.annual[0].self_consumption_pct,
                autosufficienza_pct=result.annual[0].autosufficienza_pct,
                economic=result,
            )
        )

    scenarios.sort(key=lambda s: s.npv_eur, reverse=True)
    return scenarios
