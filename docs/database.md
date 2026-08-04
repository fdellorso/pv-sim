# Database

PostgreSQL schema for PV-Sim, managed by SQLAlchemy + Alembic.

## Tables

### simulations

A simulation run: input parameters + job status.

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| name | text | free label |
| status | text | `queued` / `running` / `completed` / `failed` |
| error_message | text | when failed |
| lat / lon | float | site coordinates |
| tz | text | e.g. `Europe/Rome` |
| pv_power_kw | float | peak power |
| tilt / azimuth | float | PV field orientation |
| inverter_power_kw | float | nominal, drives clipping |
| system_losses_pct | float | default 14 |
| pv_degradation_pct_year | float | default 0.5 |
| battery_capacity_kwh | float | |
| battery_c_rate | float | 0.1–1.0 |
| battery_efficiency_pct | float | round-trip, default 95 |
| battery_degradation_pct_year | float | default 2 |
| battery_soc_min_pct / battery_soc_max_pct | float | default 10 / 90 |
| battery_replace_at_year | int | default 12 |
| load_profile_id | int FK → load_profiles | nullable |
| annual_consumption_kwh | float | used when no real profile |
| purchase_eur_kwh / sell_eur_kwh | float | monoraria tariffs |
| horizon_years | int | 20 / 25 / 30 |
| investment_cost_eur | float | total initial investment |
| loan_interest_pct | float | annual |
| loan_years | int | amortization period |
| maintenance_annual_eur | float | ordinary |
| inverter_replace_at_year | int | default 10 |
| inverter_replacement_cost_eur | float | |
| battery_replacement_cost_eur | float | |
| grid_activation_eur | float | one-time RCPV/contatore |
| grid_annual_eur | float | per-year RCPV/contatore |
| created_at | timestamptz | default now |
| updated_at | timestamptz | |

### load_profiles

Metadata for archived load curves; raw data lives as CSV on disk.

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| name | text | display name |
| source_type | text | `upload` / `synthetic` |
| profile_type | text | e.g. `residential`, `commercial`, `agricultural` |
| description | text | free text |
| annual_consumption_kwh | float | measured annual total |
| file_path | text | path under `data/load_profiles/` |
| created_at | timestamptz | |

### simulation_results

One row per year of a completed simulation.

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| simulation_id | int FK → simulations | cascade delete |
| year | int | 1..horizon |
| pv_production_kwh | float | after degradation |
| load_consumption_kwh | float | |
| self_consumption_kwh | float | |
| self_consumption_pct | float | of PV production |
| autosufficienza_pct | float | of load |
| grid_export_kwh | float | |
| grid_import_kwh | float | |
| battery_energy_in_kwh / battery_energy_out_kwh | float | |
| battery_capacity_available_kwh | float | after degradation |
| revenue_sold_eur | float | grid export × sell tariff |
| savings_self_consumption_eur | float | self-consumption × purchase tariff |
| maintenance_cost_eur | float | ordinary |
| replacement_cost_eur | float | inverter/battery that year |
| grid_cost_eur | float | annual RCPV |
| loan_payment_eur | float | annuity (0 after loan ends) |
| net_cashflow_eur | float | |
| cumulative_cashflow_eur | float | |

### simulation_metrics

One row per completed simulation (summary). Could be columns on
`simulations`; kept separate for clarity.

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| simulation_id | int FK → simulations | unique |
| npv_eur | float | at horizon |
| irr_pct | float | |
| payback_years | float | cumulative ≥ 0 year |
| total_autoconsumo_pct | float | horizon average |
| total_autosufficienza_pct | float | horizon average |
| battery_cycles_total | float | |

## Relationships

- `simulations.load_profile_id → load_profiles.id` (nullable, SET NULL)
- `simulation_results.simulation_id → simulations.id` (CASCADE)
- `simulation_metrics.simulation_id → simulations.id` (CASCADE)

## Indexes

- `simulations(status)` — worker status queries
- `load_profiles(profile_type)` — synthetic profile selection
- `simulation_results(simulation_id, year)` — unique
- `simulation_metrics(simulation_id)` — unique

## Notes

- Timestamps: `timestamptz`, UTC storage.
- The schema is intentionally flat and explicit (no JSONB) for the MVP;
  JSONB may be considered later for tariff flexibility.
- Alembic autogenerate migrations from `src/web/models.py`.
