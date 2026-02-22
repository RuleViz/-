from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import DeliveryJob, DeliveryLog, Job, Resume
from app.schemas import DeliveryPrepareRequest, DeliveryPrepareResponse, DeliveryJobDetail
from datetime import datetime

router = APIRouter(prefix="/api/delivery", tags=["Delivery Jobs"])


@router.post("/prepare", response_model=DeliveryPrepareResponse)
async def prepare_delivery(
    request: DeliveryPrepareRequest,
    db: AsyncSession = Depends(get_db)
):
    if not request.job_ids:
        raise HTTPException(status_code=400, detail="job_ids is required")

    resume_result = await db.execute(select(Resume).where(Resume.id == request.resume_id))
    resume = resume_result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    jobs_result = await db.execute(select(Job).where(Job.id.in_(request.job_ids)))
    jobs = jobs_result.scalars().all()
    if len(jobs) != len(set(request.job_ids)):
        raise HTTPException(status_code=400, detail="Some jobs are not found")

    delivery_job = DeliveryJob(
        user_id=request.user_id,
        resume_id=request.resume_id,
        job_ids=request.job_ids,
        config=request.config,
        status="queued"
    )
    db.add(delivery_job)
    await db.flush()

    logs = []
    for job_id in request.job_ids:
        logs.append(
            DeliveryLog(
                delivery_job_id=delivery_job.id,
                job_id=job_id,
                resume_id=request.resume_id,
                simulated_status="queued",
                note="投递任务已进入队列",
                template_name=(request.config or {}).get("template_name"),
                attachment_names=(request.config or {}).get("attachments", []),
            )
        )

    delivery_job.status = "sent_simulated"
    for log in logs:
        db.add(log)

    await db.flush()

    for log in logs:
        delivered = DeliveryLog(
            delivery_job_id=delivery_job.id,
            job_id=log.job_id,
            resume_id=request.resume_id,
            simulated_status="delivered_simulated",
            note="模拟投递成功",
            template_name=log.template_name,
            attachment_names=log.attachment_names,
        )
        db.add(delivered)

    delivery_job.status = "completed_simulated"
    delivery_job.updated_at = datetime.utcnow()

    await db.commit()
    return DeliveryPrepareResponse(delivery_job_id=delivery_job.id, status=delivery_job.status)


@router.get("/jobs/{delivery_job_id}", response_model=DeliveryJobDetail)
async def get_delivery_job(delivery_job_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DeliveryJob)
        .options(selectinload(DeliveryJob.logs))
        .where(DeliveryJob.id == delivery_job_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Delivery job not found")
    return item
