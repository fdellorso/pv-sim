"""App shell page routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.web.database import get_session
from src.web.models import LoadProfile
from src.web.templating import templates

router = APIRouter(tags=["pages"])


@router.get("/")
async def index() -> RedirectResponse:
    return RedirectResponse(url="/new", status_code=303)


@router.get("/new")
async def new_simulation_page(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    profiles = (await session.execute(select(LoadProfile).order_by(LoadProfile.name))).scalars().all()
    return templates.TemplateResponse(
        request,
        "new_simulation.html",
        {"profiles": profiles},
    )
