"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from arq.connections import RedisSettings, create_pool
from fastapi import FastAPI

from src.web.config import get_settings
from src.web.routes.load_profiles import router as load_profiles_router
from src.web.routes.simulations import api_router as simulations_api_router
from src.web.routes.simulations import page_router as simulations_page_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    app.state.arq = pool
    try:
        yield
    finally:
        await pool.aclose()


app = FastAPI(title="PV-Sim", version="0.1.0", lifespan=lifespan)
app.include_router(load_profiles_router)
app.include_router(simulations_api_router)
app.include_router(simulations_page_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
