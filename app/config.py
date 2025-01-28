from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    API_TITLE: str = "FastAPI Service"
    API_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    LOG_LEVEL: str = "INFO"
    
    # OpenAI/vLLM Configuration
    OPENAI_API_BASE_URL: str = "http://localhost:8000/v1"
    OPENAI_API_KEY: str = "token-abc123"
    OPENAI_MODEL_NAME: str = "t-tech/T-lite-it-1.0"
    
    # Spacy Configuration
    SPACY_MODEL: str = "ru_core_news_lg"
    
    # Resource Files
    ROLE_MAPPING_FILE: str = "res/role-mapping.json"
    FORM_MAPPING_FILE: str = "res/form-mapping.json"
    EXAMPLES_FILE: str = "res/groupped_examples.json"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

settings = Settings() 