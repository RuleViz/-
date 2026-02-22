from openai import AsyncOpenAI
from app.config import settings
from typing import Dict, Any, List, Optional
import json
import re

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
            print(f"❌ Function calling failed: {e}, attempting JSON mode...")
            try:
                # Second attempt: JSON mode
                return await self._parse_with_json_mode(system_prompt, user_prompt, function_schema)
            except Exception as json_error:
                print(f"❌ JSON mode failed: {json_error}, attempting plain text mode...")
                try:
                    # Third attempt: Plain text mode
                    return await self._parse_with_plain_text(system_prompt, user_prompt, function_schema)
                except Exception as plain_error:
                    raise Exception(f"All parsing methods failed: Function={str(e)} | JSON={str(json_error)} | Plain={str(plain_error)}")

    async def _parse_with_json_mode(self, system_prompt: str, user_prompt: str, schema: Dict) -> Dict[str, Any]:
        """
        Second attempt: Using JSON mode (for models that support response_format)
        """
        json_structure_prompt = f"""
请必须以严格的 JSON 格式输出，不要包含任何 markdown 格式化或其他文本。
输出应符合以下 JSON 结构：
{json.dumps(schema['parameters']['properties'], indent=2, ensure_ascii=False)}

必要字段：title, company_name
如果找不到字段，请留空或为null。
"""
        
        full_system_prompt = system_prompt + "\n" + json_structure_prompt

        try:
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
        except Exception as e:
            # If JSON mode is not supported, raise to trigger plain text fallback
            if "json mode" in str(e).lower() or "not supported" in str(e).lower():
                raise Exception(f"JSON mode not supported: {e}")
            raise

    async def _parse_with_plain_text(self, system_prompt: str, user_prompt: str, schema: Dict) -> Dict[str, Any]:
        """
        Third attempt: Using plain text mode (universal fallback)
        """
        json_structure_prompt = f"""
请必须以严格的 JSON 格式输出，不要包含任何 markdown 格式化或其他文本。
输出应符合以下 JSON 结构：
{json.dumps(schema['parameters']['properties'], indent=2, ensure_ascii=False)}

必要字段：title, company_name
如果找不到字段，请留空或为null。

**重要**：直接返回JSON字符串，不要添加```json标记或其他格式。
"""
        
        full_system_prompt = system_prompt + "\n" + json_structure_prompt

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": full_system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from LLM")
        
        # Clean up the content - remove markdown code blocks if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
            
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

    async def parse_resume(self, text_content: str) -> Dict[str, Any]:
        """
        Parse resume text into structured fields.
        Falls back to deterministic regex extraction when LLM is unavailable.
        """
        extracted = self._extract_resume_fields_local(text_content)

        if not self.client:
            return {
                "parsed_fields": extracted,
                "raw_text": text_content
            }

        prompt = f"""你是简历解析助手。请从下面简历文本中提取结构化字段，并返回JSON：
字段：name,email,phone,skills(数组),education(数组),experiences(数组),keywords(数组)
简历文本：\n{text_content[:12000]}
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是专业简历解析助手，只输出JSON对象"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            content = response.choices[0].message.content or "{}"
            parsed = json.loads(content)
            normalized = {
                "name": parsed.get("name") or extracted.get("name"),
                "email": parsed.get("email") or extracted.get("email"),
                "phone": parsed.get("phone") or extracted.get("phone"),
                "skills": parsed.get("skills") or extracted.get("skills", []),
                "education": parsed.get("education") or extracted.get("education", []),
                "experiences": parsed.get("experiences") or extracted.get("experiences", []),
                "keywords": parsed.get("keywords") or extracted.get("keywords", []),
            }
            return {
                "parsed_fields": normalized,
                "raw_text": text_content
            }
        except Exception:
            return {
                "parsed_fields": extracted,
                "raw_text": text_content
            }

    def match_resume_to_jobs(self, resume_fields: Dict[str, Any], jobs: List[Dict[str, Any]], top_n: int = 3) -> List[Dict[str, Any]]:
        """
        Keyword-based matching with score 0-100.
        """
        resume_skills = set(s.lower() for s in (resume_fields.get("skills") or []))
        resume_keywords = set(k.lower() for k in (resume_fields.get("keywords") or []))
        merged_tokens = resume_skills | resume_keywords

        results: List[Dict[str, Any]] = []
        for job in jobs:
            requirements = job.get("requirements") or {}
            job_skills = set(s.lower() for s in (requirements.get("skills") or []))
            title_tokens = set(re.findall(r"[\w\u4e00-\u9fff]+", (job.get("title") or "").lower()))
            location = (requirements.get("location") or "").lower()

            skill_hits = merged_tokens & job_skills
            title_hits = merged_tokens & title_tokens

            base = 30
            skill_score = min(50, len(skill_hits) * 15)
            title_score = min(15, len(title_hits) * 5)
            loc_score = 5 if location and location in merged_tokens else 0
            score = min(100, base + skill_score + title_score + loc_score)

            highlights = []
            if skill_hits:
                highlights.append(f"技能匹配: {', '.join(list(skill_hits)[:5])}")
            if title_hits:
                highlights.append(f"职位关键词匹配: {', '.join(list(title_hits)[:3])}")
            if not highlights:
                highlights.append("基础关键词相关")

            results.append({
                "job_id": job.get("id"),
                "score": float(score),
                "highlights": highlights,
                "template_recommendation": "template_1" if score >= 85 else "template_2"
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_n]

    def _extract_resume_fields_local(self, text_content: str) -> Dict[str, Any]:
        email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text_content)
        phone_match = re.search(r"(?:\+?86[- ]?)?1[3-9]\d{9}", text_content)
        name_match = re.search(r"姓名[:：\s]*([\u4e00-\u9fff]{2,4})", text_content)

        known_skills = [
            "python", "java", "javascript", "typescript", "react", "vue", "sql", "fastapi", "django", "flask",
            "机器学习", "深度学习", "nlp", "数据分析", "pytorch", "tensorflow", "docker", "kubernetes"
        ]
        lowered = text_content.lower()
        skills = [s for s in known_skills if s in lowered]

        education = []
        for marker in ["博士", "硕士", "本科", "大专", "高中"]:
            if marker in text_content:
                education.append(marker)

        keywords = list(set(skills + education))
        return {
            "name": name_match.group(1) if name_match else None,
            "email": email_match.group(0) if email_match else None,
            "phone": phone_match.group(0) if phone_match else None,
            "skills": skills,
            "education": education,
            "experiences": [],
            "keywords": keywords,
        }

# Global instance
llm_service = LLMService()
