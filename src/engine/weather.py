"""Weather data retrieval (PVGIS-SARAH3 TMY) and 15-minute interpolation."""

from __future__ import annotations

from functools import lru_cache
from typing import cast

import pandas as pd
import pvlib.iotools


@lru_cache(maxsize=32)
def _fetch_pvgis_tmy(lat: float, lon: float) -> tuple[pd.DataFrame, dict]:
    """Fetch raw PVGIS TMY data, cached by site coordinates."""
    return cast(tuple[pd.DataFrame, dict], pvlib.iotools.get_pvgis_tmy(lat, lon))


def get_weather(lat: float, lon: float, tz: str, year: int = 2020) -> pd.DataFrame:
    """Return a local 15-minute weather series for a reference year.

    Fetches the PVGIS-SARAH3 typical meteorological year and interpolates the
    hourly values to 15-minute resolution. The returned index is a timezone
    aware ``DatetimeIndex`` spanning the given reference ``year``.
    """
    data, _ = _fetch_pvgis_tmy(lat, lon)
    data.index = pd.date_range(start=f"{year}-01-01", periods=len(data), freq="1h", tz=tz)
    return data.resample("15min").interpolate()
