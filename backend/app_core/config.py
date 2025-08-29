from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    # Pydantic v2 settings config
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",  # 忽略 .env 中未在模型中声明的额外键
    )
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
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8005", "http://localhost:11010"]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                # Handle JSON array format
                import json
                origins = json.loads(v)
            else:
                # Handle comma-separated string
                origins = [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            origins = v
        else:
            origins = ["http://localhost:3000", "http://localhost:8005"]

        # 自动补全 localhost/127.0.0.1 变体，避免本地调试时 CORS 不匹配
        try:
            completed: List[str] = []
            seen = set()
            for origin in origins:
                if not isinstance(origin, str):
                    continue
                o = origin.strip()
                if not o:
                    continue
                if o in seen:
                    continue
                completed.append(o)
                seen.add(o)
                # 仅处理 http(s)://localhost:PORT 和 http(s)://127.0.0.1:PORT
                for host_a, host_b in [("localhost", "127.0.0.1"), ("127.0.0.1", "localhost")]:
                    prefix = f"http://{host_a}:"
                    sprefix = f"https://{host_a}:"
                    if o.startswith(prefix) or o.startswith(sprefix):
                        swapped = o.replace(f"{host_a}", host_b, 1)
                        if swapped not in seen:
                            completed.append(swapped)
                            seen.add(swapped)
            return completed
        except Exception:
            return origins if isinstance(origins, list) else ["http://localhost:3000", "http://localhost:8005"]
    
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
    
    # 旧版 Config 保留注释说明：已由 model_config 取代
    # class Config:
    #     env_file = ".env"


settings = Settings()