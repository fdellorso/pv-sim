"""Load model: CSV curves and synthetic profiles scaled to annual consumption."""

from __future__ import annotations

import numpy as np
import pandas as pd

DT_HOURS = 0.25
STEPS_PER_DAY = int(pd.Timedelta(days=1).total_seconds() / (DT_HOURS * 3600))


def load_curve_from_csv(file_path: str, tz: str) -> pd.Series:
    """Load a load curve CSV and return a 15-minute kW series.

    Expected columns: ``timestamp`` (local ISO ``YYYY-MM-DD HH:MM:SS``) and
    ``power_kw``. The timestamps are localized to ``tz`` and the series is
    resampled to 15-minute resolution.
    """
    df = pd.read_csv(file_path)
    timestamp = pd.to_datetime(df["timestamp"])
    if timestamp.dt.tz is None:
        timestamp = timestamp.dt.tz_localize(tz, ambiguous="infer", nonexistent="shift_forward")
    curve = pd.Series(df["power_kw"].to_numpy(), index=timestamp, name="power_kw")
    mask = ~curve.index.duplicated(keep="first")
    deduplicated = curve.loc[mask].sort_index()
    resampled: pd.Series = deduplicated.resample("15min").interpolate()
    return resampled


def scale_curve_to_annual(curve: pd.Series, target_kwh: float, dt_hours: float = DT_HOURS) -> pd.Series:
    """Scale a curve so that ``sum(curve) * dt_hours`` equals ``target_kwh``."""
    if target_kwh <= 0:
        raise ValueError("target_kwh must be positive")
    current_total = float(curve.sum()) * dt_hours
    if current_total <= 0:
        raise ValueError("curve has zero or negative total energy")
    return curve * (target_kwh / current_total)


def generate_synthetic_curve(
    index: pd.Index,
    annual_consumption_kwh: float,
    seed: int = 42,
    dt_hours: float = DT_HOURS,
) -> pd.Series:
    """Generate a synthetic residential load curve scaled to annual consumption.

    Builds a 96-step daily profile (morning peak 07:00-09:00, evening peak
    18:00-22:00, base load) with fixed-seed Gaussian noise, tiles it to cover
    the whole ``index``, and scales it to ``annual_consumption_kwh``.
    """
    rng = np.random.default_rng(seed)
    day_profile = np.zeros(STEPS_PER_DAY)
    day_profile[28:36] = 1.0
    day_profile[72:88] = 1.2
    day_profile += 0.2
    day_profile += rng.normal(0, 0.1, size=STEPS_PER_DAY)
    day_profile = np.clip(day_profile, 0, None)

    n_full = len(index) // STEPS_PER_DAY
    remainder = len(index) % STEPS_PER_DAY
    values = np.tile(day_profile, n_full)
    if remainder:
        values = np.concatenate([values, day_profile[:remainder]])

    curve = pd.Series(values, index=index, name="power_kw")
    return scale_curve_to_annual(curve, annual_consumption_kwh, dt_hours)
