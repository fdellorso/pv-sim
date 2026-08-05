"""Load profile archive routes."""

from __future__ import annotations

import uuid
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.web.config import get_settings
from src.web.database import get_session
from src.web.models import LoadProfile

router = APIRouter(prefix="/api/load-profiles", tags=["load-profiles"])

DT_HOURS = 0.25


@router.post("/upload", status_code=201)
async def upload_load_profile(
    file: UploadFile,
    profile_type: str = "residential",
    description: str = "",
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Save an uploaded CSV load curve and register its metadata."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    content = await file.read()
    if not content.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    profile_dir = Path(get_settings().load_profiles_dir)
    profile_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}.csv"
    file_path = profile_dir / stored_name
    file_path.write_bytes(content)

    try:
        df = pd.read_csv(file_path)
        annual_consumption_kwh = float(df["power_kw"].to_numpy().sum()) * DT_HOURS
    except (KeyError, ValueError, pd.errors.ParserError) as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {exc}") from exc

    profile = LoadProfile(
        name=Path(file.filename).stem,
        source_type="upload",
        profile_type=profile_type,
        description=description,
        annual_consumption_kwh=annual_consumption_kwh,
        file_path=str(file_path),
    )
    session.add(profile)
    await session.commit()
    await session.refresh(profile)

    return {
        "id": profile.id,
        "name": profile.name,
        "annual_consumption_kwh": annual_consumption_kwh,
    }
