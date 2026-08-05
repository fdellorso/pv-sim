"""Unit tests for the load model."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pandas as pd
import pytest

from src.engine.load_model import (
    generate_synthetic_curve,
    load_curve_from_csv,
    scale_curve_to_annual,
)

DT_HOURS = 0.25


def test_scale_curve_to_annual() -> None:
    index = pd.date_range("2020-01-01", periods=4, freq="15min", tz="Europe/Rome")
    curve = pd.Series([1.0, 1.0, 1.0, 1.0], index=index)
    scaled = scale_curve_to_annual(curve, 4000)
    assert float(scaled.sum() * DT_HOURS) == pytest.approx(4000.0)


def test_scale_curve_zero_target_raises() -> None:
    index = pd.date_range("2020-01-01", periods=4, freq="15min", tz="Europe/Rome")
    curve = pd.Series([1.0, 1.0, 1.0, 1.0], index=index)
    with pytest.raises(ValueError):
        scale_curve_to_annual(curve, 0)


def test_generate_synthetic_curve_deterministic_and_scaled() -> None:
    index = pd.date_range("2020-01-01", periods=96 * 365, freq="15min", tz="Europe/Rome")
    a = generate_synthetic_curve(index, 4000, seed=42)
    b = generate_synthetic_curve(index, 4000, seed=42)
    assert a.equals(b)
    assert float(a.sum() * DT_HOURS) == pytest.approx(4000.0)
    assert (a >= 0).all()


def test_load_curve_from_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "load.csv"
    csv_path.write_text(
        "timestamp,power_kw\n"
        "2020-01-01 00:00:00,1.0\n"
        "2020-01-01 00:15:00,2.0\n"
        "2020-01-01 00:30:00,3.0\n"
    )
    curve = load_curve_from_csv(str(csv_path), "Europe/Rome")
    assert cast(pd.DatetimeIndex, curve.index).tz is not None
    assert curve.sum() == pytest.approx(6.0)
