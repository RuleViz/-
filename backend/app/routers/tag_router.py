from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Tag
from app.schemas import TagCreate, TagUpdate, Tag as TagSchema
from typing import List

router = APIRouter(prefix="/api/tags", tags=["Tags"])

@router.get("", response_model=List[TagSchema])
async def get_tags(
    category: str = None,
    skip: int = 0,
    limit: int = 200,
    db: AsyncSession = Depends(get_db)
):
    """Get all tags, optionally filtered by category"""
    query = select(Tag).where(Tag.is_active == True)
    
    if category:
        query = query.where(Tag.category == category)
    
    result = await db.execute(
        query.offset(skip).limit(limit)
    )
    tags = result.scalars().all()
    return tags

@router.post("", response_model=TagSchema)
async def create_tag(
    tag: TagCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new tag"""
    # Check if code already exists
    result = await db.execute(select(Tag).where(Tag.code == tag.code))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Tag code already exists")
    
    db_tag = Tag(**tag.model_dump())
    db.add(db_tag)
    await db.commit()
    await db.refresh(db_tag)
    return db_tag

@router.get("/{tag_id}", response_model=TagSchema)
async def get_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get tag by ID"""
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

@router.put("/{tag_id}", response_model=TagSchema)
async def update_tag(
    tag_id: int,
    tag_update: TagUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update tag"""
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    db_tag = result.scalar_one_or_none()
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    update_data = tag_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_tag, key, value)
    
    await db.commit()
    await db.refresh(db_tag)
    return db_tag

@router.delete("/{tag_id}")
async def delete_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete tag (soft delete by setting is_active=False)"""
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    db_tag = result.scalar_one_or_none()
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    db_tag.is_active = False
    await db.commit()
    return {"message": "Tag deleted successfully"}
