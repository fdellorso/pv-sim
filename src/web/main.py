"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from pathlib import Path

from arq.connections import RedisSettings, create_pool
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.web.auth import SESSION_COOKIE, verify_session_token
from src.web.config import get_settings
from src.web.routes.auth import router as auth_router
from src.web.routes.load_profiles import router as load_profiles_router
from src.web.routes.optimizations import api_router as optimizations_api_router
from src.web.routes.optimizations import page_router as optimizations_page_router
from src.web.routes.pages import router as pages_router
from src.web.routes.simulations import api_router as simulations_api_router
from src.web.routes.simulations import page_router as simulations_page_router

_PUBLIC_PATHS = {"/login", "/health"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    app.state.arq = pool
    try:
        yield
    finally:
        await pool.aclose()


app = FastAPI(title="PV-Sim", version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def session_auth(request: Request, call_next):
    path = request.url.path
    if path in _PUBLIC_PATHS or path.startswith("/static/"):
        return await call_next(request)

    token = request.cookies.get(SESSION_COOKIE)
    if not verify_session_token(get_settings().app_secret_key, token):
        if path.startswith("/api/"):
            return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
        if request.headers.get("HX-Request"):
            return HTMLResponse(
                status_code=401,
                content='<div id="sim-status"><script>window.location.href="/login"</script></div>',
            )
        return RedirectResponse(url=f"/login?next={path}", status_code=303)
    return await call_next(request)


app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).resolve().parent / "static")),
    name="static",
)

app.include_router(auth_router)
app.include_router(pages_router)
app.include_router(load_profiles_router)
app.include_router(simulations_api_router)
app.include_router(simulations_page_router)
app.include_router(optimizations_api_router)
app.include_router(optimizations_page_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
