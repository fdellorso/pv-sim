"""Economic model: yearly cashflow, loan, NPV, IRR, payback."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.engine.battery_model import BatteryParams, effective_capacity, run_battery

DT_HOURS = 0.25


@dataclass(frozen=True)
class EconomicParams:
    horizon_years: int
    investment_cost_eur: float
    purchase_eur_kwh: float
    sell_eur_kwh: float
    maintenance_annual_eur: float = 0.0
    inverter_replacement_cost_eur: float | None = None
    inverter_replace_at_year: int | None = None
    battery_replacement_cost_eur: float | None = None
    battery_replace_at_year: int | None = None
    grid_activation_eur: float | None = None
    grid_annual_eur: float | None = None
    loan_interest_pct: float | None = None
    loan_years: int | None = None
    pv_degradation_pct_year: float = 0.5
    discount_rate_pct: float = 4.5


@dataclass
class AnnualCashflow:
    year: int
    pv_production_kwh: float
    load_consumption_kwh: float
    self_consumption_kwh: float
    self_consumption_pct: float
    autosufficienza_pct: float
    grid_export_kwh: float
    grid_import_kwh: float
    battery_capacity_kwh: float
    battery_charge_kwh: float
    battery_discharge_kwh: float
    savings_eur: float
    revenue_eur: float
    maintenance_cost_eur: float
    replacement_cost_eur: float
    grid_cost_eur: float
    loan_payment_eur: float
    net_cashflow_eur: float
    cumulative_cashflow_eur: float


@dataclass
class EconomicResult:
    npv_eur: float
    irr_pct: float | None
    payback_years: float | None
    annual: list[AnnualCashflow]


def compute_annuity(principal: float, interest_pct: float, years: int) -> float:
    """Return the yearly annuity payment (French amortization)."""
    if years <= 0 or principal <= 0:
        return 0.0
    if interest_pct == 0:
        return principal / years
    r = interest_pct / 100
    return principal * r * (1 + r) ** years / ((1 + r) ** years - 1)


def compute_irr(cashflows: list[float]) -> float | None:
    """Find the discount rate that zeroes the NPV of ``cashflows`` (bisection).

    Returns the IRR as a percentage, or ``None`` if no root exists in range.
    """
    if all(cf <= 0 for cf in cashflows):
        return None

    def npv(rate: float) -> float:
        return sum(cf / (1 + rate) ** i for i, cf in enumerate(cashflows))

    def sign(x: float) -> int:
        return 1 if x > 0 else (-1 if x < 0 else 0)

    lo, hi = -0.999, 1.0
    v_lo = npv(lo)
    v_hi = npv(hi)
    if sign(v_lo) == sign(v_hi):
        return None

    for _ in range(200):
        mid = (lo + hi) / 2
        value = npv(mid)
        if abs(value) < 1e-7:
            return mid * 100
        if sign(v_lo) == sign(value):
            lo, v_lo = mid, value
        else:
            hi = mid
    return None


def run_economics(
    pv_year1: pd.Series,
    load: pd.Series,
    economic: EconomicParams,
    battery: BatteryParams,
    dt_hours: float = DT_HOURS,
) -> EconomicResult:
    """Run the multi-year cashflow analysis for a single scenario.

    Year-1 PV and load series are reused every year; production is scaled by
    the annual PV degradation and battery capacity by ``effective_capacity``.
    Investment and grid activation are paid at year 0.
    """
    loan_payment = compute_annuity(
        economic.investment_cost_eur,
        economic.loan_interest_pct or 0.0,
        economic.loan_years or 0,
    )
    has_loan = economic.loan_years is not None and economic.loan_years > 0
    load_kwh = float(load.sum() * dt_hours)
    cashflows: list[float] = []
    annual: list[AnnualCashflow] = []

    cumulative = 0.0
    for year in range(1, economic.horizon_years + 1):
        pv_deg = (1 - economic.pv_degradation_pct_year / 100) ** (year - 1)
        pv_year = pv_year1 * pv_deg
        battery_year = BatteryParams(
            capacity_kwh=effective_capacity(battery, year),
            c_rate=battery.c_rate,
            efficiency=battery.efficiency,
            soc_min_pct=battery.soc_min_pct,
            soc_max_pct=battery.soc_max_pct,
        )
        res = run_battery(pv_year, load, battery_year, dt_hours)

        replacement = 0.0
        if economic.inverter_replace_at_year == year and economic.inverter_replacement_cost_eur:
            replacement += economic.inverter_replacement_cost_eur
        if economic.battery_replace_at_year == year and economic.battery_replacement_cost_eur:
            replacement += economic.battery_replacement_cost_eur

        savings = res.autoconsumo_kwh * economic.purchase_eur_kwh
        revenue = res.grid_export_kwh * economic.sell_eur_kwh
        maintenance = economic.maintenance_annual_eur
        grid_cost = economic.grid_annual_eur or 0.0
        loan_years = economic.loan_years or 0
        loan_pay = loan_payment if has_loan and year <= loan_years else 0.0

        net_cf = savings + revenue - maintenance - replacement - grid_cost - loan_pay
        cumulative += net_cf
        cashflows.append(net_cf)

        annual.append(
            AnnualCashflow(
                year=year,
                pv_production_kwh=float(pv_year.sum() * dt_hours),
                load_consumption_kwh=load_kwh,
                self_consumption_kwh=res.autoconsumo_kwh,
                self_consumption_pct=res.autoconsumo_pct,
                autosufficienza_pct=res.autosufficienza_pct,
                grid_export_kwh=res.grid_export_kwh,
                grid_import_kwh=res.grid_import_kwh,
                battery_capacity_kwh=battery_year.capacity_kwh,
                battery_charge_kwh=res.battery_charge_kwh,
                battery_discharge_kwh=res.battery_discharge_kwh,
                savings_eur=savings,
                revenue_eur=revenue,
                maintenance_cost_eur=maintenance,
                replacement_cost_eur=replacement,
                grid_cost_eur=grid_cost,
                loan_payment_eur=loan_pay,
                net_cashflow_eur=net_cf,
                cumulative_cashflow_eur=cumulative,
            )
        )

    investment = economic.investment_cost_eur + (economic.grid_activation_eur or 0.0)
    if has_loan:
        investment = economic.grid_activation_eur or 0.0
    full_cashflows = [-investment, *cashflows]

    def discounted_npv(rate_pct: float) -> float:
        r = rate_pct / 100
        return sum(cf / (1 + r) ** i for i, cf in enumerate(full_cashflows))

    npv = discounted_npv(economic.discount_rate_pct)
    irr = compute_irr(full_cashflows)

    payback = None
    cumulative_invested = -investment
    for entry in annual:
        cumulative_invested += entry.net_cashflow_eur
        if cumulative_invested >= 0:
            payback = float(entry.year)
            break
    return EconomicResult(
        npv_eur=npv,
        irr_pct=irr,
        payback_years=payback,
        annual=annual,
    )
