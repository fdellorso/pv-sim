"""PV production model: pvlib ModelChain, inverter clipping, system losses."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from pvlib.location import Location
from pvlib.modelchain import ModelChain
from pvlib.pvsystem import PVSystem


@dataclass(frozen=True)
class PVSystemParams:
    lat: float
    lon: float
    tz: str
    power_kw: float
    tilt: float
    azimuth: float
    inverter_power_kw: float
    system_losses_pct: float = 14.0


def run_pv_model(weather: pd.DataFrame, params: PVSystemParams) -> pd.Series:
    """Run the pvlib ModelChain and return AC power in kW (15-minute series).

    Applies inverter clipping (``ac = min(ac, inverter_power_kw)``) and global
    system losses (cabling, soiling, mismatch) as a percentage of AC output.
    """
    location = Location(params.lat, params.lon, tz=params.tz)
    system = PVSystem(
        surface_tilt=params.tilt,
        surface_azimuth=params.azimuth,
        module_parameters={"pdc0": params.power_kw * 1000, "gamma_pdc": -0.004},
        inverter_parameters={"pdc0": params.power_kw * 1000},
        racking_model="open_rack",
        module_type="glass_polymer",
    )
    model_chain = ModelChain(
        system,
        location,
        aoi_model="no_loss",
        spectral_model="no_loss",
        temperature_model="sapm",
    )
    model_chain.run_model(weather)

    ac = model_chain.results.ac.fillna(0) / 1000
    ac = np.minimum(ac, params.inverter_power_kw)
    ac = ac * (1 - params.system_losses_pct / 100)
    return ac
