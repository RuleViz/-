from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import job_router, industry_router, tag_router, config_router
from app.database import engine, Base
from app.services.llm_service import llm_service
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(job_router.router)
app.include_router(industry_router.router)
app.include_router(tag_router.router)
app.include_router(config_router.router)

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
