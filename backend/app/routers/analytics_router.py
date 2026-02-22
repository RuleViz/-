from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import DeliveryLog
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/deliveries")
async def get_delivery_analytics(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    group_by: str = Query("day", pattern="^(day|template|status)$"),
    db: AsyncSession = Depends(get_db)
):
    query = select(DeliveryLog)
    if start:
        query = query.where(DeliveryLog.timestamp >= start)
    if end:
        query = query.where(DeliveryLog.timestamp <= end)

    result = await db.execute(query)
    logs = result.scalars().all()

    bucket = {}
    for item in logs:
        if group_by == "day":
            key = item.timestamp.strftime("%Y-%m-%d")
        elif group_by == "template":
            key = item.template_name or "unknown"
        else:
            key = item.simulated_status
        bucket[key] = bucket.get(key, 0) + 1

    rows = [{"key": k, "count": v} for k, v in sorted(bucket.items(), key=lambda x: x[0])]
    total = sum(v for v in bucket.values())
    success = sum(v for k, v in bucket.items() if "delivered" in k or "sent" in k)

    return {
        "group_by": group_by,
        "total": total,
        "success_rate": round((success / total) * 100, 2) if total else 0,
        "items": rows,
    }


@router.get("/delivery-logs")
async def get_delivery_logs(
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db)
):
    query = select(DeliveryLog).order_by(DeliveryLog.timestamp.desc())
    result = await db.execute(query)
    logs = result.scalars().all()

    total = len(logs)
    start = (page - 1) * page_size
    end = start + page_size
    items = logs[start:end]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": item.id,
                "delivery_job_id": item.delivery_job_id,
                "job_id": item.job_id,
                "resume_id": item.resume_id,
                "simulated_status": item.simulated_status,
                "note": item.note,
                "timestamp": item.timestamp,
                "template_name": item.template_name,
                "attachment_names": item.attachment_names,
            }
            for item in items
        ],
    }
