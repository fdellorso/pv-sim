# API

Web routes and REST endpoints planned for PV-Sim. The web layer uses HTMX
for HTML fragments and JSON endpoints for job control and data fetching.

## Auth

Single password login (cookie-based session).

| Method | Path | Description |
|---|---|---|
| GET | `/login` | Login page |
| POST | `/login` | Validate password, set session |
| POST | `/logout` | Clear session |

## Pages (SPA shell)

| Method | Path | Description |
|---|---|---|
| GET | `/` | Dashboard: list of simulations |
| GET | `/projects/new` | Simulation parameter form |
| GET | `/projects/{id}` | Simulation detail / results dashboard |
| GET | `/load-profiles` | Load profile archive management |

## Simulations

| Method | Path | Description |
|---|---|---|
| GET | `/api/simulations` | List simulations (JSON) |
| POST | `/api/simulations` | Create simulation, enqueue job. Body: full parameter set. Returns `{id, status}` |
| GET | `/api/simulations/{id}` | Simulation parameters + status |
| GET | `/api/simulations/{id}/status` | Job status (HTMX polls this every 2s) |
| GET | `/api/simulations/{id}/results` | Full results (annual rows + metrics) |
| GET | `/api/simulations/{id}/report.pdf` | Download PDF report |
| DELETE | `/api/simulations/{id}` | Delete simulation + results |

## Load profiles

| Method | Path | Description |
|---|---|---|
| GET | `/api/load-profiles` | List archived profiles (metadata) |
| POST | `/api/load-profiles/upload` | Upload CSV, create metadata row |
| GET | `/api/load-profiles/{id}/preview` | First N rows of the curve |
| GET | `/api/load-profiles/{id}/download` | Download raw CSV |
| DELETE | `/api/load-profiles/{id}` | Delete metadata (optionally the file) |

## Simulation parameter payload (POST /api/simulations)

```jsonc
{
  "name": "Casa Roma 6kW + batteria",
  "location": { "lat": 41.9, "lon": 12.5, "tz": "Europe/Rome" },
  "pv_field": {
    "power_kw": 6.0,
    "tilt": 30,
    "azimuth": 180,
    "inverter_power_kw": 6.0,
    "system_losses_pct": 14.0,
    "degradation_pct_year": 0.5
  },
  "battery": {
    "capacity_kwh": 10.0,
    "c_rate": 0.5,
    "round_trip_efficiency_pct": 95.0,
    "degradation_pct_year": 2.0,
    "soc_min_pct": 10.0,
    "soc_max_pct": 90.0,
    "replace_at_year": 12
  },
  "load": {
    "load_profile_id": null,
    "annual_consumption_kwh": 4000.0
  },
  "tariffs": {
    "purchase_eur_kwh": 0.30,
    "sell_eur_kwh": 0.12
  },
  "economics": {
    "horizon_years": 25,
    "investment_cost_eur": 12000.0,
    "loan": { "interest_rate_pct": 4.5, "years": 10 },
    "maintenance_annual_eur": 150.0,
    "inverter_replacement_cost_eur": 1500.0,
    "inverter_replace_at_year": 10,
    "battery_replacement_cost_eur": 2500.0,
    "grid_activation_eur": 100.0,
    "grid_annual_eur": 30.0
  }
}
```

## Simulation result payload

```jsonc
{
  "id": 42,
  "status": "completed",
  "metrics": {
    "npv_eur": 3100.0,
    "irr_pct": 7.2,
    "payback_years": 12.4,
    "autoconsumo_pct": 48.0,
    "autosufficienza_pct": 62.0
  },
  "annual": [
    {
      "year": 1,
      "pv_production_kwh": 6900.0,
      "self_consumption_kwh": 3300.0,
      "grid_export_kwh": 3600.0,
      "grid_import_kwh": 700.0,
      "cashflow_eur": 620.0,
      "cumulative_cashflow_eur": 620.0
    }
  ],
  "charts": {
    "daily_curves_json": "...",     // Plotly figure JSON
    "cashflow_json": "..."          // Plotly figure JSON
  }
}
```

## Error responses

Errors use HTTP status codes plus a JSON body `{"detail": "..."}`.
Job failures are recorded on the simulation row with a `failed` status and an
error message, surfaced by the dashboard.
