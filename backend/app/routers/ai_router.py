from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models import ResumeParse, Job, MatchResult
from app.schemas import MatchRequest, MatchItem
from app.services.llm_service import llm_service
from typing import List

router = APIRouter(prefix="/api/ai", tags=["AI Matching"])


@router.post("/match", response_model=List[MatchItem])
async def match_resume(
    request: MatchRequest,
    db: AsyncSession = Depends(get_db)
):
    parse_result = await db.execute(
        select(ResumeParse)
        .where(ResumeParse.resume_id == request.resume_id)
        .order_by(desc(ResumeParse.version))
    )
    latest_parse = parse_result.scalar_one_or_none()
    if not latest_parse:
        raise HTTPException(status_code=404, detail="Resume parse not found")

    query = select(Job).where(Job.status == "active")
    if request.filters:
        location = request.filters.get("location")
        if location:
            query = query.where(Job.requirements["location"].as_string() == location)

    jobs_result = await db.execute(query)
    jobs = jobs_result.scalars().all()
    if not jobs:
        return []

    jobs_data = [
        {
            "id": job.id,
            "title": job.title,
            "requirements": job.requirements or {},
        }
        for job in jobs
    ]

    matched = llm_service.match_resume_to_jobs(
        resume_fields=latest_parse.extracted_fields or {},
        jobs=jobs_data,
        top_n=request.top_n
    )

    for item in matched:
        db.add(
            MatchResult(
                resume_id=request.resume_id,
                job_id=item["job_id"],
                score=item["score"],
                reason_snippet="；".join(item.get("highlights", [])),
                highlights=item.get("highlights", []),
                template_recommendation=item.get("template_recommendation")
            )
        )
    await db.commit()

    return matched
