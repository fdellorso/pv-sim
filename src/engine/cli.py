"""CLI smoke test for the simulation engine.

Run with::

    uv run python -m src.engine.cli
"""

from __future__ import annotations

import argparse

import pandas as pd

from src.engine.battery_model import BatteryParams
from src.engine.economic_model import EconomicParams, run_economics
from src.engine.load_model import generate_synthetic_curve, load_curve_from_csv
from src.engine.pv_model import PVSystemParams, run_pv_model
from src.engine.weather import get_weather

DT_HOURS = 0.25


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PV-Sim engine smoke test")
    parser.add_argument("--lat", type=float, default=46.0)
    parser.add_argument("--lon", type=float, default=8.9)
    parser.add_argument("--tz", default="Europe/Zurich")
    parser.add_argument("--power-kw", type=float, default=5.0)
    parser.add_argument("--tilt", type=float, default=30.0)
    parser.add_argument("--azimuth", type=float, default=180.0)
    parser.add_argument("--inverter-kw", type=float, default=5.0)
    parser.add_argument("--system-losses-pct", type=float, default=0.0)
    load_group = parser.add_mutually_exclusive_group()
    load_group.add_argument("--load-csv", metavar="FILE", help="use a real CSV load curve")
    load_group.add_argument(
        "--load-synthetic", action="store_true", help="generate a synthetic load curve"
    )
    parser.add_argument(
        "--annual-consumption", type=float, default=4000.0, help="kWh for synthetic load"
    )
    battery_group = parser.add_argument_group("battery")
    battery_group.add_argument(
        "--battery-capacity", type=float, default=10.0, help="battery capacity in kWh"
    )
    battery_group.add_argument("--battery-crate", type=float, default=0.5, help="battery C-rate")
    battery_group.add_argument("--no-battery", action="store_true", help="disable the battery")
    economic_group = parser.add_argument_group("economics")
    economic_group.add_argument("--horizon", type=int, default=25, help="analysis horizon in years")
    economic_group.add_argument("--investment-cost-eur", type=float, default=12000.0)
    economic_group.add_argument("--purchase-eur-kwh", type=float, default=0.30)
    economic_group.add_argument("--sell-eur-kwh", type=float, default=0.12)
    economic_group.add_argument("--maintenance-annual-eur", type=float, default=0.0)
    economic_group.add_argument("--inverter-replacement-cost", type=float, default=1500.0)
    economic_group.add_argument("--inverter-replace-at-year", type=int, default=10)
    economic_group.add_argument("--battery-replacement-cost", type=float, default=2500.0)
    economic_group.add_argument("--battery-replace-at-year", type=int, default=12)
    economic_group.add_argument("--grid-annual-eur", type=float, default=30.0)
    economic_group.add_argument("--grid-activation-eur", type=float, default=100.0)
    economic_group.add_argument("--loan-interest-pct", type=float, default=0.0)
    economic_group.add_argument("--loan-years", type=int, default=0)
    economic_group.add_argument(
        "--pv-degradation", type=float, default=0.5, help="PV degradation %/year"
    )
    economic_group.add_argument("--discount-rate", type=float, default=4.5, help="discount rate %")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    params = PVSystemParams(
        lat=args.lat,
        lon=args.lon,
        tz=args.tz,
        power_kw=args.power_kw,
        tilt=args.tilt,
        azimuth=args.azimuth,
        inverter_power_kw=args.inverter_kw,
        system_losses_pct=args.system_losses_pct,
    )

    weather: pd.DataFrame = get_weather(params.lat, params.lon, params.tz)
    pv_power = run_pv_model(weather, params)
    production_kwh = float(pv_power.sum()) * DT_HOURS

    print(f"Produzione FV (kWh): {round(production_kwh, 1)}")

    if args.load_csv:
        load = load_curve_from_csv(args.load_csv, params.tz)
    elif args.load_synthetic:
        load = generate_synthetic_curve(pv_power.index, args.annual_consumption)
    else:
        return

    consumption_kwh = float(load.sum()) * DT_HOURS
    print(f"Consumo (kWh): {round(consumption_kwh, 1)}")

    battery_params = BatteryParams(
        capacity_kwh=0.0 if args.no_battery else args.battery_capacity,
        c_rate=args.battery_crate,
    )

    economic_params = EconomicParams(
        horizon_years=args.horizon,
        investment_cost_eur=args.investment_cost_eur,
        purchase_eur_kwh=args.purchase_eur_kwh,
        sell_eur_kwh=args.sell_eur_kwh,
        maintenance_annual_eur=args.maintenance_annual_eur,
        inverter_replacement_cost_eur=args.inverter_replacement_cost,
        inverter_replace_at_year=args.inverter_replace_at_year,
        battery_replacement_cost_eur=args.battery_replacement_cost,
        battery_replace_at_year=args.battery_replace_at_year,
        grid_activation_eur=args.grid_activation_eur,
        grid_annual_eur=args.grid_annual_eur,
        loan_interest_pct=args.loan_interest_pct or None,
        loan_years=args.loan_years or None,
        pv_degradation_pct_year=args.pv_degradation,
        discount_rate_pct=args.discount_rate,
    )

    economic = run_economics(pv_power, load, economic_params, battery_params)
    first = economic.annual[0]

    print(f"Autoconsumo anno 1 (kWh): {round(first.self_consumption_kwh, 1)}")
    print(f"Autoconsumo anno 1 %: {round(first.self_consumption_pct, 1)}")
    print(f"Autosufficienza anno 1 %: {round(first.autosufficienza_pct, 1)}")
    if not args.no_battery:
        print(f"Ricaricato batteria (kWh): {round(first.battery_charge_kwh, 1)}")
        print(f"Scaricato batteria (kWh): {round(first.battery_discharge_kwh, 1)}")

    print("\nAnno | Autoconsumo% | Autosufficienza% | Net CF (EUR) | Cumulativo (EUR)")
    for entry in economic.annual:
        print(
            f"{entry.year:4d} | {entry.self_consumption_pct:12.1f} | "
            f"{entry.autosufficienza_pct:16.1f} | {entry.net_cashflow_eur:12.1f} | "
            f"{entry.cumulative_cashflow_eur:16.1f}"
        )

    print(f"\nNPV: {round(economic.npv_eur, 1)} EUR")
    print(f"IRR: {round(economic.irr_pct, 2) if economic.irr_pct is not None else 'n/a'} %")
    print(f"Payback: anno {economic.payback_years}")


if __name__ == "__main__":
    main()
