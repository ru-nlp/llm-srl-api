from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

# Get the root directory of the project
ROOT_DIR = Path(__file__).parent.parent

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
    
    # OpenAI/T-Lite Configuration
    OPENAI_API_BASE_URL: str = "http://localhost:8000/v1"
    OPENAI_API_KEY: str = "token-abc123"
    OPENAI_MODEL_NAME: str = "t-tech/T-lite-it-1.0"
    
    # Spacy Configuration
    SPACY_MODEL: str = "ru_core_news_lg"
    
    # Role Mappings Files - using relative paths from project root
    ROLE_MAPPING_FILE: str = "role-mapping.json"
    FORM_MAPPING_FILE: str = "form-mapping.json"
    EXAMPLES_FILE: str = "groupped_examples.json"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

    def get_role_mapping_path(self) -> Path:
        return ROOT_DIR / self.ROLE_MAPPING_FILE
        
    def get_form_mapping_path(self) -> Path:
        return ROOT_DIR / self.FORM_MAPPING_FILE
        
    def get_examples_path(self) -> Path:
        return ROOT_DIR / self.EXAMPLES_FILE


settings = Settings() 