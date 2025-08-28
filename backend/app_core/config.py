from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-change-this"
    
    # LLM Provider Settings
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_APP_NAME: str = "SolutionAgent"
    
    # Server Settings
    PORT: int = 8001
    HOST: str = "0.0.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8005"]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                # Handle JSON array format
                import json
                return json.loads(v)
            else:
                # Handle comma-separated string
                return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        else:
            return ["http://localhost:3000", "http://localhost:8005"]
    
    # Content directories
    WIKI_DIR: str = "wiki"
    UPLOAD_DIR: str = "uploads"
    TENDER_DEFAULT_PATH: str = "uploads/招标文件.md"
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    VERBOSE_LOGGING: bool = False
    
    # Security Settings
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-this"
    SESSION_TIMEOUT: int = 3600  # 1 hour
    
    # Database Settings (optional)
    DATABASE_URL: str = "sqlite:///./sessions.db"
    
    class Config:
        env_file = ".env"


settings = Settings()