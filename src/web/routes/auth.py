"""Login/logout routes for single-password session auth."""

from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from src.web.auth import SESSION_COOKIE, create_session_token
from src.web.config import get_settings
from src.web.templating import templates

router = APIRouter(tags=["auth"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: bool = False) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": error, "next": request.query_params.get("next", "/")},
    )


@router.post("/login")
async def login(
    password: str = Form(...),
    next: str = Form("/"),
) -> RedirectResponse:
    if password != get_settings().app_password:
        return RedirectResponse(url="/login?error=1", status_code=303)
    response = RedirectResponse(url=next, status_code=303)
    response.set_cookie(
        SESSION_COOKIE,
        create_session_token(get_settings().app_secret_key),
        max_age=24 * 3600,
        httponly=True,
        samesite="lax",
    )
    return response


@router.post("/logout")
async def logout() -> RedirectResponse:
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE)
    return response
