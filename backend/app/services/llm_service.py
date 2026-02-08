from openai import AsyncOpenAI
from app.config import settings
from typing import Dict, Any, List, Optional
import json

class LLMService:
    def __init__(self):
        self.client = None
        self.model = settings.openai_model
        self.base_url = settings.openai_base_url
        self.api_key = settings.openai_api_key
        self._init_client()
    
    def _init_client(self):
        """Initialize OpenAI client from .env configuration"""
        if self.api_key and self.api_key != "your-api-key-here":
            try:
                self.client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
                print(f"✅ LLM Client initialized - Model: {self.model}, Base URL: {self.base_url}")
            except Exception as e:
                print(f"❌ Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            print(f"⚠️ LLM not configured. Please set OPENAI_API_KEY in .env file")
            self.client = None
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get current LLM configuration info"""
        return {
            "is_configured": self.client is not None,
            "model": self.model,
            "base_url": self.base_url,
            "api_key_preview": f"{self.api_key[:8]}..." if self.api_key and len(self.api_key) > 8 else "Not set"
        }
    
    async def parse_job_posting(self, raw_content: str, source_type: str = "手动") -> Dict[str, Any]:
        """
        Parse raw job posting text using LLM with structured output
        """
        if not self.client:
            raise ValueError("LLM client not configured. Please set API key.")
        
        # Define the function schema for structured output
        function_schema = {
            "name": "parse_job_posting",
            "description": "Extract structured information from a job posting",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Job title/position name"
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Company name"
                    },
                    "suggested_industry": {
                        "type": "string",
                        "description": "Industry category (e.g., '互联网/科技', '金融', '教育')"
                    },
                    "suggested_industry_code": {
                        "type": "string",
                        "description": "Industry code in English lowercase (e.g., 'internet', 'finance', 'education')"
                    },
                    "suggested_tags": {
                        "type": "array",
                        "description": "Suggested tags for the job",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "category": {
                                    "type": "string",
                                    "enum": ["skill", "job_type", "company", "position"]
                                },
                                "color": {"type": "string"}
                            },
                            "required": ["name", "category"]
                        }
                    },
                    "apply_email": {
                        "type": "string",
                        "description": "Email address for application"
                    },
                    "email_subject_template": {
                        "type": "string",
                        "description": "Suggested email subject template with placeholders like {{name}}, {{position}}"
                    },
                    "email_body_template": {
                        "type": "string",
                        "description": "Suggested email body template with placeholders"
                    },
                    "requirements": {
                        "type": "object",
                        "properties": {
                            "education": {"type": "string"},
                            "experience": {"type": "string"},
                            "location": {"type": "string"},
                            "skills": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "salary": {"type": "string"}
                        }
                    },
                    "published_at": {
                        "type": "string",
                        "description": "Publication date in ISO format if mentioned"
                    }
                },
                "required": ["title", "company_name"]
            }
        }
        
        # Craft the prompt
        system_prompt = """你是一个专业的招聘信息解析助手。你的任务是从原始文本中提取结构化的招聘信息。

**重要规则：**
1. **核心必填项**：必须准确提取 **职位名称（title）** 和 **公司名称（company_name）**。这是最关键的信息。
2. **邮箱提取（重要）**：仔细查找文中的 **投递邮箱（apply_email）**。这通常是必填项，请务必提取。如果文中出现多个邮箱，优先提取HR或招聘专用的邮箱。
3. **行业分类**：推断行业分类（suggested_industry）并生成英文小写代码（suggested_industry_code）。
4. **智能标签**：生成相关标签（suggested_tags），包括技能、职位类型、公司特征等。
5. **颜色分配**：为技能标签分配合适的颜色（Python用#3776ab，Java用#007396等）。
6. **邮件模板**：如果有投递邮箱，必须生成邮件主题和正文模板，方便用户直接投递。
7. **职位要求**：提取结构化的职位要求（学历、经验、地点、技能、薪资）。

**标签颜色参考：**
- Python: #3776ab
- JavaScript: #f7df1e
- Java: #007396
- AI/机器学习: #ff6f61
- 数据分析: #36a2eb
- 设计: #ff6b9d
- 实习: #52c41a
- 远程: #1890ff
"""
        
        user_prompt = f"""请解析以下招聘信息：

来源类型：{source_type}

原始内容：
{raw_content}
"""
        
        try:
            # First try with Function Calling (Tools)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                functions=[function_schema],
                function_call={"name": "parse_job_posting"},
                temperature=0.1 # Lower temperature for more deterministic output
            )
            
            # Extract the function call result
            message = response.choices[0].message
            if message.function_call:
                result = json.loads(message.function_call.arguments)
                return result
            else:
                # Fallback to JSON Mode if function calling fails (common with some models like DeepSeek)
                print("⚠️ Function calling failed, falling back to JSON Mode...")
                return await self._parse_with_json_mode(system_prompt, user_prompt, function_schema)
                
        except Exception as e:
            print(f"❌ Primary parsing failed: {e}, attempting fallback...")
            try:
                # Immediate fallback attempt
                return await self._parse_with_json_mode(system_prompt, user_prompt, function_schema)
            except Exception as fallback_error:
                raise Exception(f"LLM parsing failed: {str(e)} | Fallback error: {str(fallback_error)}")

    async def _parse_with_json_mode(self, system_prompt: str, user_prompt: str, schema: Dict) -> Dict[str, Any]:
        """
        Fallback parsing using JSON mode with explicit schema instruction
        """
        # Enhance prompt with schema structure for JSON mode
        json_structure_prompt = f"""
请必须以严格的 JSON 格式输出，不要包含任何 markdown 格式化或其他文本。
输出应符合以下 JSON 结构：
{json.dumps(schema['parameters']['properties'], indent=2, ensure_ascii=False)}

必要字段：title, company_name
如果找不到字段，请留空或为null。
"""
        
        full_system_prompt = system_prompt + "\n" + json_structure_prompt

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": full_system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from LLM in JSON mode")
            
        return json.loads(content)

    async def test_connection(self) -> Dict[str, Any]:
        """Test LLM API connection"""
        if not self.client:
            return {
                "success": False,
                "message": "API key not configured"
            }
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return {
                "success": True,
                "message": "Connection successful",
                "model_info": {
                    "model": response.model,
                    "id": response.id
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}"
            }

# Global instance
llm_service = LLMService()
