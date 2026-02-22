from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./jobs.db"
    
    # OpenAI Configuration
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Resume
    resume_storage_path: str = "./data/resumes"
    resume_max_file_size_mb: int = 10
    resume_allowed_extensions: str = "pdf,doc,docx,txt"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
print(f"DEBUG: Loaded settings - API Key: '{settings.openai_api_key}', Model: '{settings.openai_model}', Base URL: '{settings.openai_base_url}'")
