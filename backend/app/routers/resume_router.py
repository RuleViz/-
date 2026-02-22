from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.config import settings
from app.models import Resume, ResumeParse, MatchResult, DeliveryLog
from app.schemas import ResumeUploadResponse, ResumeParsed
from app.services.llm_service import llm_service
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import json

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])


def _ensure_storage_dir() -> Path:
    storage = Path(settings.resume_storage_path)
    storage.mkdir(parents=True, exist_ok=True)
    return storage


def _validate_file(file: UploadFile):
    allowed = {ext.strip().lower() for ext in settings.resume_allowed_extensions.split(",") if ext.strip()}
    suffix = Path(file.filename or "").suffix.lower().replace(".", "")
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{suffix}")


def _extract_resume_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        return file_path.read_text(encoding="utf-8", errors="ignore")

    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(file_path))
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception:
            return ""

    if suffix == ".docx":
        try:
            import docx
            doc = docx.Document(str(file_path))
            return "\n".join([p.text for p in doc.paragraphs])
        except Exception:
            return ""

    return ""


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    user_id: str = Query("default_user"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    _validate_file(file)
    storage_dir = _ensure_storage_dir()

    now = datetime.utcnow()
    safe_name = f"{int(now.timestamp())}_{(file.filename or 'resume').replace(' ', '_')}"
    target_path = storage_dir / safe_name

    content = await file.read()
    if len(content) > settings.resume_max_file_size_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")

    target_path.write_bytes(content)

    resume = Resume(
        user_id=user_id,
        filename=file.filename or safe_name,
        storage_path=str(target_path),
        status="uploaded"
    )
    db.add(resume)
    await db.flush()

    try:
        text_content = _extract_resume_text(target_path)
        parse_result = await llm_service.parse_resume(text_content)

        latest_parse = ResumeParse(
            resume_id=resume.id,
            parsed_json=parse_result,
            extracted_fields=parse_result.get("parsed_fields", {}),
            version=1,
        )
        db.add(latest_parse)
        resume.status = "parsed"
        resume.updated_at = datetime.utcnow()
    except Exception as exc:
        resume.status = "failed"
        resume.error_message = str(exc)

    await db.commit()
    return ResumeUploadResponse(resume_id=resume.id, status=resume.status)


@router.post("/{resume_id}/parse", response_model=ResumeParsed)
async def parse_resume(
    resume_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    text_content = _extract_resume_text(Path(resume.storage_path))
    parse_result = await llm_service.parse_resume(text_content)

    parse_result_db = await db.execute(
        select(ResumeParse).where(ResumeParse.resume_id == resume_id).order_by(desc(ResumeParse.version))
    )
    latest = parse_result_db.scalar_one_or_none()
    next_version = (latest.version + 1) if latest else 1

    record = ResumeParse(
        resume_id=resume_id,
        parsed_json=parse_result,
        extracted_fields=parse_result.get("parsed_fields", {}),
        version=next_version,
    )
    db.add(record)
    resume.status = "parsed"
    resume.updated_at = datetime.utcnow()
    await db.commit()

    return ResumeParsed(
        resume_id=resume_id,
        status=resume.status,
        parsed_fields=parse_result.get("parsed_fields", {}),
        parsed_json=parse_result,
        version=next_version,
    )


@router.get("/{resume_id}")
async def get_resume_detail(resume_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    parse_result = await db.execute(
        select(ResumeParse).where(ResumeParse.resume_id == resume_id).order_by(desc(ResumeParse.version))
    )
    latest_parse = parse_result.scalar_one_or_none()

    matches_result = await db.execute(
        select(MatchResult).where(MatchResult.resume_id == resume_id).order_by(desc(MatchResult.created_at)).limit(50)
    )
    matches = matches_result.scalars().all()

    logs_result = await db.execute(
        select(DeliveryLog).where(DeliveryLog.resume_id == resume_id).order_by(desc(DeliveryLog.timestamp)).limit(100)
    )
    logs = logs_result.scalars().all()

    return {
        "resume": {
            "id": resume.id,
            "user_id": resume.user_id,
            "filename": resume.filename,
            "status": resume.status,
            "uploaded_at": resume.uploaded_at,
            "updated_at": resume.updated_at,
        },
        "parsed": {
            "version": latest_parse.version,
            "parsed_json": latest_parse.parsed_json,
            "extracted_fields": latest_parse.extracted_fields,
            "parsed_at": latest_parse.parsed_at,
        } if latest_parse else None,
        "matches": [
            {
                "job_id": item.job_id,
                "score": item.score,
                "reason_snippet": item.reason_snippet,
                "highlights": item.highlights,
                "created_at": item.created_at,
            } for item in matches
        ],
        "delivery_history": [
            {
                "id": log.id,
                "job_id": log.job_id,
                "simulated_status": log.simulated_status,
                "note": log.note,
                "timestamp": log.timestamp,
            } for log in logs
        ],
    }


@router.get("/search")
async def search_resumes(
    q: Optional[str] = None,
    skill: Optional[str] = None,
    user_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    query = select(Resume).order_by(desc(Resume.uploaded_at))
    if user_id:
        query = query.where(Resume.user_id == user_id)

    result = await db.execute(query)
    resumes = result.scalars().all()

    if q or skill:
        parse_result = await db.execute(select(ResumeParse).order_by(desc(ResumeParse.version)))
        parses = parse_result.scalars().all()
        parse_map = {}
        for p in parses:
            parse_map.setdefault(p.resume_id, p)

        filtered = []
        for resume in resumes:
            p = parse_map.get(resume.id)
            text_blob = json.dumps((p.parsed_json if p else {}), ensure_ascii=False).lower()
            if q and q.lower() not in text_blob and q.lower() not in resume.filename.lower():
                continue
            if skill and skill.lower() not in text_blob:
                continue
            filtered.append(resume)
        resumes = filtered

    total = len(resumes)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = resumes[start:end]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "filename": r.filename,
                "status": r.status,
                "uploaded_at": r.uploaded_at,
                "updated_at": r.updated_at,
            }
            for r in page_items
        ],
    }


@router.get("/{resume_id}/download")
async def download_resume(resume_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    file_path = Path(resume.storage_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Resume file not found")

    return FileResponse(path=str(file_path), filename=resume.filename)
