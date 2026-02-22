from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    job_router,
    industry_router,
    tag_router,
    config_router,
    cart_router,
    delivery_router,
    resume_router,
    ai_router,
    delivery_job_router,
    analytics_router,
    admin_router,
)
from app.database import engine, Base
from app.services.llm_service import llm_service
from contextlib import asynccontextmanager
from app.config import settings
from pathlib import Path

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    Path(settings.resume_storage_path).mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title="Job Management API",
    description="API for managing job postings with AI-powered auto-categorization",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - 允许所有来源用于开发
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # 当allow_origins=["*"]时，必须为False
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Include routers
app.include_router(job_router.router)
app.include_router(industry_router.router)
app.include_router(tag_router.router)
app.include_router(config_router.router)
app.include_router(cart_router.router)
app.include_router(delivery_router.router)
app.include_router(resume_router.router)
app.include_router(ai_router.router)
app.include_router(delivery_job_router.router)
app.include_router(analytics_router.router)
app.include_router(admin_router.router)

@app.get("/")
async def root():
    config_info = llm_service.get_config_info()
    return {
        "message": "Job Management API",
        "docs": "/docs",
        "version": "1.0.0",
        "llm_configured": config_info["is_configured"],
        "llm_model": config_info["model"],
        "llm_base_url": config_info["base_url"]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
