"""CLI smoke test for the simulation engine.

Run with::

    uv run python -m src.engine.cli
"""

from __future__ import annotations

import argparse

import pandas as pd

from src.engine.battery_model import BatteryParams, run_battery
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
    load_group.add_argument("--load-synthetic", action="store_true", help="generate a synthetic load curve")
    parser.add_argument("--annual-consumption", type=float, default=4000.0, help="kWh for synthetic load")
    battery_group = parser.add_argument_group("battery")
    battery_group.add_argument("--battery-capacity", type=float, default=10.0, help="battery capacity in kWh")
    battery_group.add_argument("--battery-crate", type=float, default=0.5, help="battery C-rate")
    battery_group.add_argument("--no-battery", action="store_true", help="disable the battery")
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
    result = run_battery(pv_power, load, battery_params)

    print(f"Autoconsumo (kWh): {round(result.autoconsumo_kwh, 1)}")
    print(f"Autoconsumo %: {round(result.autoconsumo_pct, 1)}")
    print(f"Autosufficienza %: {round(result.autosufficienza_pct, 1)}")
    if not args.no_battery:
        print(f"Ricaricato batteria (kWh): {round(result.battery_charge_kwh, 1)}")
        print(f"Scaricato batteria (kWh): {round(result.battery_discharge_kwh, 1)}")


if __name__ == "__main__":
    main()
