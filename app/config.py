from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Supabase Configuration (Primary Database)
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    
    # Application Configuration
    secret_key: str = "your-secret-key-here"
    environment: str = "development"
    debug: bool = True
    
    # API Configuration
    api_title: str = "Smart Tourist Safety & Incident Response System"
    api_description: str = "Backend API for monitoring tourist safety and managing incident responses"
    api_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()