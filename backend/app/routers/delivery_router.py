from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import Delivery, Job, CartItem
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix="/api/deliveries", tags=["Deliveries"])


class DeliveryCreate(BaseModel):
    job_id: int
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    cover_letter_style: str = "concise"


class DeliveryUpdate(BaseModel):
    status: Optional[str] = None
    interview_stage: Optional[str] = None
    interview_notes: Optional[str] = None


class DeliveryStats(BaseModel):
    total_count: int
    sent_count: int
    viewed_count: int
    interview_count: int
    rejected_count: int
    hired_count: int


@router.get("", response_model=List[dict])
async def get_deliveries(
    user_id: str = "default_user",
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """获取投递记录列表"""
    query = select(Delivery).options(
        selectinload(Delivery.job).selectinload(Job.tags)
    ).where(Delivery.user_id == user_id)
    
    if status:
        query = query.where(Delivery.status == status)
    
    result = await db.execute(
        query.order_by(Delivery.created_at.desc()).offset(skip).limit(limit)
    )
    deliveries = result.scalars().all()
    
    # 转换为可序列化的格式
    return [
        {
            "id": d.id,
            "job_id": d.job_id,
            "job": {
                "id": d.job.id,
                "title": d.job.title,
                "company_name": d.job.company_name,
                "apply_email": d.job.apply_email,
                "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in d.job.tags]
            } if d.job else None,
            "status": d.status,
            "email_subject": d.email_subject,
            "sent_at": d.sent_at.isoformat() if d.sent_at else None,
            "delivered_at": d.delivered_at.isoformat() if d.delivered_at else None,
            "viewed_at": d.viewed_at.isoformat() if d.viewed_at else None,
            "replied_at": d.replied_at.isoformat() if d.replied_at else None,
            "interview_stage": d.interview_stage,
            "interview_notes": d.interview_notes,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in deliveries
    ]


@router.post("/batch")
async def batch_create_deliveries(
    job_ids: List[int],
    cover_letter_style: str = "concise",
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """批量创建投递记录（从购物车投递）"""
    created_deliveries = []
    
    for job_id in job_ids:
        # 检查职位是否存在
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            continue
        
        # 创建投递记录
        delivery = Delivery(
            job_id=job_id,
            user_id=user_id,
            status='pending',
            cover_letter_style=cover_letter_style,
            email_subject=job.email_subject_template or f"求职申请 - {job.title}",
        )
        db.add(delivery)
        created_deliveries.append(delivery)
        
        # 从购物车移除
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
        if cart_item:
            cart_item.status = 'removed'
            cart_item.updated_at = datetime.utcnow()
    
    await db.commit()
    
    # 刷新所有投递记录
    for delivery in created_deliveries:
        await db.refresh(delivery)
    
    return {
        "message": f"Created {len(created_deliveries)} deliveries",
        "delivery_ids": [d.id for d in created_deliveries]
    }


@router.post("/{delivery_id}/send")
async def send_delivery(
    delivery_id: int,
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """发送投递（模拟邮件发送）"""
    result = await db.execute(
        select(Delivery).where(
            and_(Delivery.id == delivery_id, Delivery.user_id == user_id)
        )
    )
    delivery = result.scalar_one_or_none()
    
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    # 模拟发送
    delivery.status = 'sent'
    delivery.sent_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Delivery sent successfully", "delivery_id": delivery_id}


@router.patch("/{delivery_id}")
async def update_delivery(
    delivery_id: int,
    update_data: DeliveryUpdate,
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """更新投递记录"""
    result = await db.execute(
        select(Delivery).where(
            and_(Delivery.id == delivery_id, Delivery.user_id == user_id)
        )
    )
    delivery = result.scalar_one_or_none()
    
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    if update_data.status:
        delivery.status = update_data.status
        # 更新时间戳
        if update_data.status == 'viewed' and not delivery.viewed_at:
            delivery.viewed_at = datetime.utcnow()
        elif update_data.status == 'replied' and not delivery.replied_at:
            delivery.replied_at = datetime.utcnow()
    
    if update_data.interview_stage:
        delivery.interview_stage = update_data.interview_stage
    
    if update_data.interview_notes is not None:
        delivery.interview_notes = update_data.interview_notes
    
    delivery.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Delivery updated successfully"}


@router.get("/stats/summary")
async def get_delivery_stats(
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """获取投递统计"""
    # 总投递数
    result = await db.execute(
        select(func.count(Delivery.id)).where(Delivery.user_id == user_id)
    )
    total_count = result.scalar() or 0
    
    # 各状态统计
    stats = {}
    for status in ['sent', 'viewed', 'interview', 'rejected', 'hired']:
        result = await db.execute(
            select(func.count(Delivery.id)).where(
                and_(Delivery.user_id == user_id, Delivery.status == status)
            )
        )
        stats[status] = result.scalar() or 0
    
    return {
        "total_count": total_count,
        "sent_count": stats.get('sent', 0),
        "viewed_count": stats.get('viewed', 0),
        "interview_count": stats.get('interview', 0),
        "rejected_count": stats.get('rejected', 0),
        "hired_count": stats.get('hired', 0),
        "view_rate": round(stats.get('viewed', 0) / total_count * 100, 1) if total_count > 0 else 0,
        "interview_rate": round(stats.get('interview', 0) / total_count * 100, 1) if total_count > 0 else 0,
    }


@router.get("/trends/daily")
async def get_daily_trends(
    days: int = 30,
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """获取每日投递趋势"""
    from datetime import timedelta
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 这里简化处理，实际应该按日期分组统计
    result = await db.execute(
        select(Delivery).where(
            and_(
                Delivery.user_id == user_id,
                Delivery.created_at >= start_date
            )
        )
    )
    deliveries = result.scalars().all()
    
    # 按日期分组
    daily_data = {}
    for d in deliveries:
        date_key = d.created_at.strftime('%Y-%m-%d')
        daily_data[date_key] = daily_data.get(date_key, 0) + 1
    
    # 填充缺失日期
    trends = []
    for i in range(days):
        date = (end_date - timedelta(days=i)).strftime('%Y-%m-%d')
        trends.append({
            "date": date,
            "count": daily_data.get(date, 0)
        })
    
    return list(reversed(trends))
