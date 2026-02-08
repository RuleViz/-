from fastapi import APIRouter
from app.schemas import LLMConfigResponse, LLMTestResponse
from app.services.llm_service import llm_service
from app.config import settings

router = APIRouter(prefix="/api/config", tags=["Configuration"])

@router.get("/llm", response_model=LLMConfigResponse)
async def get_llm_config():
    """Get current LLM configuration (API key masked)"""
    config_info = llm_service.get_config_info()
    return LLMConfigResponse(
        api_key_preview=config_info["api_key_preview"],
        base_url=config_info["base_url"],
        model=config_info["model"],
        is_configured=config_info["is_configured"]
    )

@router.post("/llm/test", response_model=LLMTestResponse)
async def test_llm_connection():
    """Test LLM API connection"""
    result = await llm_service.test_connection()
    return LLMTestResponse(**result)
