"""Unit tests for the PV model (offline, no PVGIS)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.engine.pv_model import PVSystemParams, run_pv_model

DT_HOURS = 0.25


def _weather_day(peak_ghi: float = 1000.0) -> pd.DataFrame:
    index = pd.date_range("2020-07-15", periods=96, freq="15min", tz="Europe/Rome")
    # triangular GHI peaking at noon
    hours = index.to_series().dt.hour + index.to_series().dt.minute / 60
    shape = np.clip(1 - np.abs(hours - 13) / 6, 0, 1)
    ghi = shape * peak_ghi
    return pd.DataFrame(
        {
            "ghi": ghi,
            "dni": ghi * 1.1,
            "dhi": ghi * 0.2,
            "temp_air": np.full(96, 25.0),
        },
        index=index,
    )


def test_run_pv_model_output_shape_and_limits() -> None:
    params = PVSystemParams(
        lat=41.9,
        lon=12.5,
        tz="Europe/Rome",
        power_kw=6.0,
        tilt=30.0,
        azimuth=180.0,
        inverter_power_kw=6.0,
        system_losses_pct=14.0,
    )
    ac = run_pv_model(_weather_day(), params)

    assert isinstance(ac, pd.Series)
    assert len(ac) == 96
    assert (ac >= 0).all()
    # inverter clipping caps AC at inverter power
    assert float(ac.max()) <= params.inverter_power_kw + 1e-6
    # system losses further reduce the clipped value
    assert float(ac.max()) <= params.inverter_power_kw * (1 - 0.14) + 1e-6


def test_run_pv_model_respects_index() -> None:
    params = PVSystemParams(
        lat=41.9,
        lon=12.5,
        tz="Europe/Rome",
        power_kw=3.0,
        tilt=30.0,
        azimuth=180.0,
        inverter_power_kw=3.0,
    )
    ac = run_pv_model(_weather_day(), params)
    assert ac.index.equals(_weather_day().index)
