from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import Job, Industry, Tag
from app.schemas import (
    JobCreate, JobUpdate, Job as JobSchema,
    LLMParseRequest, LLMParseResponse
)
from app.services.llm_service import llm_service
from typing import List

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

@router.post("/parse", response_model=LLMParseResponse)
async def parse_job_posting(
    parse_request: LLMParseRequest
):
    """
    Parse raw job posting text using LLM
    Returns structured data preview without saving to database
    """
    try:
        result = await llm_service.parse_job_posting(
            raw_content=parse_request.raw_content,
            source_type=parse_request.source_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", response_model=JobSchema)
async def create_job(
    job: JobCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new job posting
    Supports auto-creating industries and tags if they don't exist
    """
    # Handle industry
    if job.industry_name and not job.industry_id:
        # Try to find existing industry by name
        result = await db.execute(
            select(Industry).where(Industry.name == job.industry_name)
        )
        existing_industry = result.scalar_one_or_none()
        
        if existing_industry:
            job.industry_id = existing_industry.id
    
    # Create job instance
    job_data = job.model_dump(exclude={'tag_ids'})
    db_job = Job(**job_data)
    
    # Handle tags
    if job.tag_ids:
        result = await db.execute(
            select(Tag).where(Tag.id.in_(job.tag_ids))
        )
        tags = result.scalars().all()
        db_job.tags = list(tags)
    
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job, ['tags'])
    return db_job

@router.get("", response_model=List[JobSchema])
async def get_jobs(
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    industry_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    """Get jobs with filtering and pagination"""
    query = select(Job).options(selectinload(Job.tags))
    
    if status:
        query = query.where(Job.status == status)
    if industry_id:
        query = query.where(Job.industry_id == industry_id)
    
    result = await db.execute(
        query.order_by(Job.created_at.desc()).offset(skip).limit(limit)
    )
    jobs = result.scalars().all()
    return jobs

@router.get("/{job_id}", response_model=JobSchema)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get job by ID"""
    result = await db.execute(
        select(Job)
        .options(selectinload(Job.tags))
        .where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.put("/{job_id}", response_model=JobSchema)
async def update_job(
    job_id: int,
    job_update: JobUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update job"""
    result = await db.execute(
        select(Job)
        .options(selectinload(Job.tags))
        .where(Job.id == job_id)
    )
    db_job = result.scalar_one_or_none()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    update_data = job_update.model_dump(exclude_unset=True, exclude={'tag_ids'})
    for key, value in update_data.items():
        setattr(db_job, key, value)
    
    # Update tags if provided
    if job_update.tag_ids is not None:
        result = await db.execute(
            select(Tag).where(Tag.id.in_(job_update.tag_ids))
        )
        tags = result.scalars().all()
        db_job.tags = list(tags)
    
    await db.commit()
    await db.refresh(db_job, ['tags'])
    return db_job

@router.delete("/{job_id}")
async def delete_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete job"""
    result = await db.execute(select(Job).where(Job.id == job_id))
    db_job = result.scalar_one_or_none()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    await db.delete(db_job)
    await db.commit()
    return {"message": "Job deleted successfully"}
