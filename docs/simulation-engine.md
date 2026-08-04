# Simulation Engine

Specification of the simulation core in `src/engine/`. Each module is pure
(no web/worker imports) and operates on `pandas` time series at 15-minute
resolution.

## Pipeline

```
weather → pv_model → load_model → battery_model → economic_model
```

An annual reference simulation runs at 15-minute resolution for year 1; later
years reuse the same time series scaled by degradation factors (production
shrinks, battery capacity shrinks). This keeps runtime low while retaining
per-year accuracy.

## 1. Weather (`weather.py`)

- `get_pvgis_tmy(lat, lon)` → `(data, meta)` via
  `pvlib.iotools.get_pvgis_tmy` (SARAH3).
- Reindex to a local 15-minute series for a reference year (e.g. 2020),
  interpolating hourly TMY values.
- Results cached by `(lat, lon)` to avoid repeated network calls.

## 2. PV model (`pv_model.py`)

`pvlib.ModelChain` configured with:

- `Location(lat, lon, tz)`
- `PVSystem(surface_tilt, surface_azimuth, module/inverter params)`
- `ModelChain(..., aoi_model, spectral_model, temperature_model)`

Post-processing:

- **Clipping**: `ac = min(ac, inverter_power_kw)` — models grid-connection
  limits and inverter saturation. Configurable.
- **System losses**: global percentage (default 14%) applied to AC output
  (cabling, soiling, mismatch).
- **Degradation**: annual linear factor
  `production(year) = production_yr1 × (1 - pv_degradation_pct_year)^(year-1)`.

## 3. Load model (`load_model.py`)

Two sources:

- **Real curve**: load a CSV from `data/load_profiles/` (see
  `docs/development.md` for format), resampled to 15-minute series.
- **Synthetic**: select an archived profile with a matching `profile_type`
  and scale so that `sum(curve) × dt = annual_consumption_kwh`.

## 4. Battery model (`battery_model.py`)

State-of-charge simulation at 15-minute steps.

- Power limits: `p_max_charge = p_max_discharge = c_rate × capacity_kwh`.
- Round-trip efficiency `η` (default 95%): energy into the battery is
  `p_charge × dt / sqrt(η)`; energy out is `p_discharge × dt × sqrt(η)`
  (per-trip split), or simpler: charge stores `p×dt×η`, discharge draws
  `p×dt/η`.
- SOC clamped to `[soc_min, soc_max] × capacity`.
- Charge priority: fill from PV surplus after direct self-consumption;
  discharge covers load deficit before grid import.
- Capacity degradation per year:
  `capacity(year) = capacity_yr1 × (1 - battery_degradation_pct_year)^(year-1)`.

Energy flows per year:

```
self_consumption = min(pv, load)  [direct, before battery]
surplus = max(pv - load, 0)       [available to battery]
deficit = max(load - pv, 0)       [load not covered directly]
battery_charge = min(surplus, p_max_charge, soc_headroom)
battery_discharge = min(deficit, p_max_discharge, soc_available)
grid_export = surplus - battery_charge
grid_import = deficit - battery_discharge
```

## 5. Economic model (`economic_model.py`)

Per year `y = 1..horizon_years`:

```
savings_self_consumption = self_consumption_kwh × purchase_eur_kwh
revenue_sold            = grid_export_kwh × sell_eur_kwh
maintenance_cost        = maintenance_annual_eur
replacement_cost        = inverter_replace_cost if y == inverter_replace_at_year
                          + battery_replace_cost if y == battery_replace_at_year
grid_cost               = grid_annual_eur
loan_payment            = annuity if y <= loan_years else 0
net_cashflow = savings + revenue - maintenance - replacement - grid_cost - loan_payment
cumulative_cashflow = sum(net_cashflow[1..y])
```

Annuity (French amortization):

```
A = P × r × (1+r)^n / ((1+r)^n - 1)
P = investment_cost_eur, r = loan_interest_pct/100, n = loan_years
```

Final metrics:

- **NPV**: `Σ net_cashflow_y / (1+d)^y - investment_cost_eur`, with discount
  rate `d` (configurable, default = loan interest or a set discount rate).
- **IRR**: discount rate that zeroes NPV, found numerically
  (`numpy.irr`-equivalent or bisection).
- **Payback**: first year where cumulative cashflow ≥ 0 (simple, non-discounted).

Investment cost is paid at year 0; replacement costs are treated as expenses
in their year.

## 6. Optimizer (`optimizer.py`)

- Sweep battery capacity across a range (e.g. `0 .. pv_power_kw × 4`, step
  configurable, plus the C-rate).
- For each scenario run the engine and record IRR / NPV.
- Return the capacity maximizing the chosen metric (default IRR), plus the
  full scenario table for comparison in the UI.

## Degradation summary

| Component | Default | Configurable |
|---|---|---|
| PV panels | 0.5 %/year linear | yes |
| Battery capacity | 2 %/year linear | yes |
| Inverter | replaced at year 10 | yes |
| Battery | replaced at year 12 | yes |

## Validation targets

- Year-1 production for a 5 kW / tilt 30° / Rome site should match the
  prototype output of `pvlib_autoconsumo_simulazione.py` within a few percent.
- Autoconsumo % and autosufficienza % definitions per `CONTEXT.md`.
- Payback sanity: a well-sized plant typically pays back in 8–15 years with
  Italian retail tariffs.
