# === SCRIPT COMPLETO CORRETTO: PRODUZIONE FV + CONSUMO + BATTERIA + GRAFICI (15 MIN) ===

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pvlib
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.modelchain import ModelChain

# === PARAMETRI ===
LAT, LON = 46.0, 8.9
TZ = "Europe/Zurich"
PV_POWER_KW = 5  # impianto 5 kW
BATTERY_KWH = 10
EFFICIENCY = 0.95
DT = 0.25  # 15 minuti
consumo_annuo_kwh = 4000  # consumo annuo in kWh

# === 1. DATI METEO REALI (PVGIS) ===
data, meta = pvlib.iotools.get_pvgis_tmy(LAT, LON)
data.index = pd.date_range(start="2020-01-01", periods=len(data), freq="1h", tz=TZ)
meteo = data.resample("15min").interpolate()

# === 2. PRODUZIONE FV ===
location = Location(LAT, LON, tz=TZ)
system = PVSystem(
    surface_tilt=30,
    surface_azimuth=180,
    module_parameters={"pdc0": PV_POWER_KW * 1000, "gamma_pdc": -0.004},
    inverter_parameters={"pdc0": PV_POWER_KW * 1000},
    racking_model="open_rack",
    module_type="glass_polymer",
)

mc = ModelChain(
    system,
    location,
    aoi_model="no_loss",
    spectral_model="no_loss",
    temperature_model="sapm",
)
mc.run_model(meteo)
pv_power = mc.results.ac.fillna(0) / 1000  # kW


# === 3. PROFILO CONSUMO SINTETICO ===
def generate_load(index, consumo_annuo_kwh):
    steps_per_day = 96  # 15 min
    day_profile = np.zeros(steps_per_day)
    day_profile[28:36] = 1.0  # picco mattina
    day_profile[72:88] = 1.2  # picco sera
    day_profile += 0.2  # base minima

    # Aggiungi un po' di casualità (es: +/-10% dei valori)
    rng = np.random.default_rng(seed=42)  # seed fisso per riproducibilità
    noise = rng.normal(0, 0.1, size=steps_per_day)
    day_profile += noise
    day_profile = np.clip(day_profile, 0, None)  # non meno di 0

    n_days = len(index) // steps_per_day
    full_profile = np.tile(day_profile, n_days)
    full_profile = full_profile[: len(index)]

    # scala per rispettare consumo annuo
    total_energy_profile = np.sum(full_profile) * 0.25
    scale_factor = consumo_annuo_kwh / total_energy_profile
    full_profile *= scale_factor
    return full_profile


load = generate_load(pv_power.index, consumo_annuo_kwh)

# === ALLINEAMENTO LUNGHEZZA PV E LOAD ===
pv = pv_power.values
min_len = min(len(pv), len(load))
pv = pv[:min_len]
load = load[:min_len]

# === 4. SIMULAZIONE BATTERIA VETTORIZZATA ===
surplus = pv - load
soc = np.zeros_like(surplus)
current_soc = 0

for i, s in enumerate(surplus):
    if s > 0:
        current_soc += s * DT * EFFICIENCY
    else:
        current_soc += s * DT / EFFICIENCY
    current_soc = np.clip(current_soc, 0, BATTERY_KWH)
    soc[i] = current_soc

# === 5. CALCOLI ENERGIA ===
self_consumption = np.minimum(pv, load)
grid_export = np.maximum(pv - load, 0)
grid_import = np.maximum(load - pv, 0)

energy_pv = np.sum(pv) * DT
energy_load = np.sum(load) * DT
energy_self = np.sum(self_consumption) * DT

print("Produzione FV (kWh):", round(energy_pv, 1))
print("Consumo (kWh):", round(energy_load, 1))
print("Autoconsumo (kWh):", round(energy_self, 1))
print("Autoconsumo %:", round(energy_self / energy_pv * 100, 1))
print("Autosufficienza %:", round(energy_self / energy_load * 100, 1))

# === 6. GRAFICO GIORNO TIPO ANNUALE ACCOPPIATO PV/LOAD (2 CURVE) ===
df = pd.DataFrame({"pv": pv, "load": load}, index=pv_power.index[:min_len])


def typical_day(month):
    df_m = df[df.index.month == month]
    grouped = df_m.groupby([df_m.index.hour, df_m.index.minute]).mean()
    return grouped.reset_index(drop=True)


plt.figure(figsize=(14, 6))
pv_continuous = []
load_continuous = []
x_cursor = 0
x_ticks = []

for m in range(1, 13):
    td = typical_day(m)
    pv_continuous.extend(td["pv"].values)
    load_continuous.extend(td["load"].values)
    x_ticks.append(x_cursor + len(td) // 2)
    x_cursor += len(td)

x = np.arange(len(pv_continuous))
plt.plot(x, pv_continuous, color="green", label="Produzione")
plt.plot(x, load_continuous, color="red", label="Consumo")
plt.title("Produzione e Consumo - Giorno tipo per mese (continuo)")
plt.xlabel("Mese")
plt.ylabel("kW")
plt.xticks(
    x_ticks,
    [
        "Gen",
        "Feb",
        "Mar",
        "Apr",
        "Mag",
        "Giu",
        "Lug",
        "Ago",
        "Set",
        "Ott",
        "Nov",
        "Dic",
    ],
)
plt.legend()
plt.tight_layout()
plt.show()
# === FINE ===
