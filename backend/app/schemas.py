from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

# ============= Industry Schemas =============

class IndustryBase(BaseModel):
    code: str
    name: str
    parent_id: Optional[int] = None
    sort_order: int = 0
    is_active: bool = True

class IndustryCreate(IndustryBase):
    pass

class IndustryUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class Industry(IndustryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# ============= Tag Schemas =============

class TagBase(BaseModel):
    code: str
    name: str
    category: str  # position/job_type/company/skill
    color: str = "#1890ff"
    is_active: bool = True

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None

class Tag(TagBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# ============= Job Schemas =============

class JobRequirements(BaseModel):
    education: Optional[str] = None
    experience: Optional[str] = None
    location: Optional[str] = None
    skills: Optional[List[str]] = None
    salary: Optional[str] = None

class JobBase(BaseModel):
    title: str
    company_name: str
    industry_id: Optional[int] = None
    industry_name: Optional[str] = None
    apply_email: Optional[str] = None
    email_subject_template: Optional[str] = None
    email_body_template: Optional[str] = None
    requirements: Optional[Dict[str, Any]] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    raw_content: Optional[str] = None
    published_at: Optional[datetime] = None
    status: str = "active"

class JobCreate(JobBase):
    tag_ids: Optional[List[int]] = []

class JobUpdate(BaseModel):
    title: Optional[str] = None
    company_name: Optional[str] = None
    industry_id: Optional[int] = None
    industry_name: Optional[str] = None
    apply_email: Optional[str] = None
    email_subject_template: Optional[str] = None
    email_body_template: Optional[str] = None
    requirements: Optional[Dict[str, Any]] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    raw_content: Optional[str] = None
    published_at: Optional[datetime] = None
    status: Optional[str] = None
    tag_ids: Optional[List[int]] = None

class Job(JobBase):
    id: int
    created_at: datetime
    updated_at: datetime
    tags: List[Tag] = []
    
    model_config = ConfigDict(from_attributes=True)

# ============= LLM Parsing Schemas =============

class LLMParseRequest(BaseModel):
    raw_content: str
    source_type: Optional[str] = "手动"

class LLMParseResponse(BaseModel):
    title: str
    company_name: str
    suggested_industry: Optional[str] = None
    suggested_industry_code: Optional[str] = None
    suggested_tags: List[Dict[str, str]] = []  # [{"name": "Python", "category": "skill", "color": "#3776ab"}]
    apply_email: Optional[str] = None
    email_subject_template: Optional[str] = None
    email_body_template: Optional[str] = None
    requirements: Optional[Dict[str, Any]] = None
    published_at: Optional[str] = None

# ============= LLM Config Schemas =============

class LLMConfigRequest(BaseModel):
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"

class LLMConfigResponse(BaseModel):
    api_key_preview: str  # Only show first 8 characters
    base_url: str
    model: str
    is_configured: bool

class LLMTestResponse(BaseModel):
    success: bool
    message: str
    model_info: Optional[Dict[str, Any]] = None
