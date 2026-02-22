from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models import Resume, ResumeParse
from app.schemas import ResumeFixRequest
from datetime import datetime

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def _ensure_admin(x_role: str | None):
    if x_role not in {"admin", "owner"}:
        raise HTTPException(status_code=403, detail="Admin role required")


@router.post("/resume/{resume_id}/fix")
async def fix_resume_parse(
    resume_id: int,
    payload: ResumeFixRequest,
    x_role: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db)
):
    _ensure_admin(x_role)

    resume_result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = resume_result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    parse_result = await db.execute(
        select(ResumeParse).where(ResumeParse.resume_id == resume_id).order_by(desc(ResumeParse.version))
    )
    latest = parse_result.scalar_one_or_none()
    next_version = (latest.version + 1) if latest else 1

    base_json = latest.parsed_json if latest else {}
    base_json["parsed_fields"] = payload.parsed_fields
    if payload.note:
        base_json["admin_note"] = payload.note

    record = ResumeParse(
        resume_id=resume_id,
        parsed_json=base_json,
        extracted_fields=payload.parsed_fields,
        version=next_version,
    )
    db.add(record)
    resume.status = "parsed"
    resume.updated_at = datetime.utcnow()

    await db.commit()

    return {
        "resume_id": resume_id,
        "version": next_version,
        "status": "saved",
    }
