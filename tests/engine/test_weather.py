"""Unit tests for the weather module (PVGIS mocked)."""

from __future__ import annotations

from typing import cast

import numpy as np
import pandas as pd
import pytest

from src.engine import weather


@pytest.fixture()
def fake_pvgis(monkeypatch) -> pd.DataFrame:
    hourly = pd.DataFrame(
        {
            "temp_air": np.linspace(0, 20, 24),
            "ghi": np.concatenate([np.zeros(6), np.full(12, 500.0), np.zeros(6)]),
            "dni": np.concatenate([np.zeros(6), np.full(12, 600.0), np.zeros(6)]),
            "dhi": np.full(24, 50.0),
        },
        index=pd.date_range("2020-01-01", periods=24, freq="1h"),
    )

    def _fake_get(lat: float, lon: float) -> tuple[pd.DataFrame, dict]:
        return hourly.copy(), {"meta": {}}

    monkeypatch.setattr(weather, "_fetch_pvgis_tmy", _fake_get)
    return hourly


def test_get_weather_interpolates_to_15min(fake_pvgis: pd.DataFrame) -> None:
    df = weather.get_weather(46.0, 8.9, "Europe/Rome")
    index = cast(pd.DatetimeIndex, df.index)
    assert len(df) > 24  # interpolated beyond the hourly input
    assert index.freq == "15min"
    assert str(index.tz) == "Europe/Rome"
    assert "ghi" in df.columns
