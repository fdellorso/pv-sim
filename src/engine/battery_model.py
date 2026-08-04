"""Battery model: C-rate limited charge/discharge, efficiency, degradation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

DT_HOURS = 0.25


@dataclass(frozen=True)
class BatteryParams:
    capacity_kwh: float
    c_rate: float = 0.5
    efficiency: float = 0.95
    soc_min_pct: float = 10.0
    soc_max_pct: float = 90.0
    degradation_pct_year: float = 2.0


@dataclass
class BatteryResult:
    autoconsumo_kwh: float
    autoconsumo_pct: float
    autosufficienza_pct: float
    grid_export_kwh: float
    grid_import_kwh: float
    battery_charge_kwh: float
    battery_discharge_kwh: float


def effective_capacity(params: BatteryParams, year: int) -> float:
    """Return usable battery capacity for a given year after degradation."""
    factor = (1 - params.degradation_pct_year / 100) ** (year - 1)
    return params.capacity_kwh * factor


def run_battery(
    pv: pd.Series,
    load: pd.Series,
    params: BatteryParams,
    dt_hours: float = DT_HOURS,
) -> BatteryResult:
    """Simulate battery operation at 15-minute steps and aggregate annual metrics.

    Charge from PV surplus after direct self-consumption, discharge to cover the
    load deficit before grid import. Power is capped by the C-rate and by SOC
    headroom/availability. Charge stores ``p*dt*eta``, discharge draws
    ``p*dt/eta``.
    """
    surplus = np.maximum(pv.to_numpy() - load.to_numpy(), 0.0)
    deficit = np.maximum(load.to_numpy() - pv.to_numpy(), 0.0)

    p_max = params.c_rate * params.capacity_kwh
    soc_min_kwh = params.capacity_kwh * params.soc_min_pct / 100
    soc_max_kwh = params.capacity_kwh * params.soc_max_pct / 100

    soc = soc_min_kwh
    charge_energy = 0.0
    discharge_energy = 0.0

    for s, d in zip(surplus, deficit, strict=True):
        headroom = max(soc_max_kwh - soc, 0.0)
        charge_power = min(s, p_max, headroom / dt_hours)
        charge_energy += charge_power * dt_hours
        soc += charge_power * dt_hours * params.efficiency

        available = max(soc - soc_min_kwh, 0.0)
        discharge_power = min(d, p_max, available / dt_hours)
        discharge_energy += discharge_power * dt_hours
        soc -= discharge_power * dt_hours / params.efficiency

    grid_export_kwh = float(surplus.sum() * dt_hours - charge_energy)
    grid_import_kwh = float(deficit.sum() * dt_hours - discharge_energy)

    pv_kwh = float(pv.sum() * dt_hours)
    load_kwh = float(load.sum() * dt_hours)
    autoconsumo_kwh = pv_kwh - grid_export_kwh

    autoconsumo_pct = (autoconsumo_kwh / pv_kwh * 100) if pv_kwh > 0 else 0.0
    autosufficienza_pct = ((1 - grid_import_kwh / load_kwh) * 100) if load_kwh > 0 else 0.0

    return BatteryResult(
        autoconsumo_kwh=autoconsumo_kwh,
        autoconsumo_pct=autoconsumo_pct,
        autosufficienza_pct=autosufficienza_pct,
        grid_export_kwh=grid_export_kwh,
        grid_import_kwh=grid_import_kwh,
        battery_charge_kwh=charge_energy,
        battery_discharge_kwh=discharge_energy,
    )
