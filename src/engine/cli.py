"""CLI smoke test for the simulation engine.

Run with::

    uv run python -m src.engine.cli
"""

from __future__ import annotations

import argparse

import pandas as pd

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


if __name__ == "__main__":
    main()
