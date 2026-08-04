"""FastAPI application entrypoint."""

from fastapi import FastAPI

from src.web.routes.load_profiles import router as load_profiles_router

app = FastAPI(title="PV-Sim", version="0.1.0")
app.include_router(load_profiles_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
