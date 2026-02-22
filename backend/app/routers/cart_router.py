from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import CartItem, Job
from app.schemas import Job as JobSchema
from typing import List
from datetime import datetime

router = APIRouter(prefix="/api/cart", tags=["Cart"])


@router.get("/items", response_model=List[JobSchema])
async def get_cart_items(
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """获取购物车中的职位列表"""
    result = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.job).selectinload(Job.tags))
        .where(
            and_(
                CartItem.user_id == user_id,
                CartItem.status == 'active'
            )
        )
        .order_by(CartItem.created_at.desc())
    )
    cart_items = result.scalars().all()
    
    # 返回关联的职位
    jobs = [item.job for item in cart_items if item.job]
    return jobs


@router.post("/items/{job_id}")
async def add_to_cart(
    job_id: int,
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """添加职位到购物车"""
    # 检查职位是否存在
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # 检查是否已在购物车
    result = await db.execute(
        select(CartItem).where(
            and_(
                CartItem.job_id == job_id,
                CartItem.user_id == user_id,
                CartItem.status == 'active'
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        return {"message": "Job already in cart", "cart_item_id": existing.id}
    
    # 创建购物车项目
    cart_item = CartItem(
        job_id=job_id,
        user_id=user_id,
        status='active'
    )
    db.add(cart_item)
    await db.commit()
    await db.refresh(cart_item)
    
    return {"message": "Added to cart successfully", "cart_item_id": cart_item.id}


@router.delete("/items/{job_id}")
async def remove_from_cart(
    job_id: int,
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """从购物车移除职位"""
    result = await db.execute(
        select(CartItem).where(
            and_(
                CartItem.job_id == job_id,
                CartItem.user_id == user_id,
                CartItem.status == 'active'
            )
        )
    )
    cart_item = result.scalar_one_or_none()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Item not found in cart")
    
    cart_item.status = 'removed'
    cart_item.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Removed from cart successfully"}


@router.get("/count")
async def get_cart_count(
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """获取购物车数量"""
    result = await db.execute(
        select(CartItem).where(
            and_(
                CartItem.user_id == user_id,
                CartItem.status == 'active'
            )
        )
    )
    count = len(result.scalars().all())
    return {"count": count}


@router.delete("/clear")
async def clear_cart(
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """清空购物车"""
    result = await db.execute(
        select(CartItem).where(
            and_(
                CartItem.user_id == user_id,
                CartItem.status == 'active'
            )
        )
    )
    cart_items = result.scalars().all()
    
    for item in cart_items:
        item.status = 'removed'
        item.updated_at = datetime.utcnow()
    
    await db.commit()
    return {"message": "Cart cleared successfully"}
