from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Industry
from app.schemas import IndustryCreate, IndustryUpdate, Industry as IndustrySchema
from typing import List

router = APIRouter(prefix="/api/industries", tags=["Industries"])

@router.get("", response_model=List[IndustrySchema])
async def get_industries(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all industries"""
    result = await db.execute(
        select(Industry)
        .where(Industry.is_active == True)
        .order_by(Industry.sort_order)
        .offset(skip)
        .limit(limit)
    )
    industries = result.scalars().all()
    return industries

@router.post("", response_model=IndustrySchema)
async def create_industry(
    industry: IndustryCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new industry"""
    # Check if code already exists
    result = await db.execute(select(Industry).where(Industry.code == industry.code))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Industry code already exists")
    
    db_industry = Industry(**industry.model_dump())
    db.add(db_industry)
    await db.commit()
    await db.refresh(db_industry)
    return db_industry

@router.get("/{industry_id}", response_model=IndustrySchema)
async def get_industry(
    industry_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get industry by ID"""
    result = await db.execute(select(Industry).where(Industry.id == industry_id))
    industry = result.scalar_one_or_none()
    if not industry:
        raise HTTPException(status_code=404, detail="Industry not found")
    return industry

@router.put("/{industry_id}", response_model=IndustrySchema)
async def update_industry(
    industry_id: int,
    industry_update: IndustryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update industry"""
    result = await db.execute(select(Industry).where(Industry.id == industry_id))
    db_industry = result.scalar_one_or_none()
    if not db_industry:
        raise HTTPException(status_code=404, detail="Industry not found")
    
    update_data = industry_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_industry, key, value)
    
    await db.commit()
    await db.refresh(db_industry)
    return db_industry

@router.delete("/{industry_id}")
async def delete_industry(
    industry_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete industry (soft delete by setting is_active=False)"""
    result = await db.execute(select(Industry).where(Industry.id == industry_id))
    db_industry = result.scalar_one_or_none()
    if not db_industry:
        raise HTTPException(status_code=404, detail="Industry not found")
    
    db_industry.is_active = False
    await db.commit()
    return {"message": "Industry deleted successfully"}
