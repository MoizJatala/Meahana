from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # Attendee API Configuration
    attendee_api_key: str = Field(..., description="Attendee API key for bot management")
    attendee_api_base_url: str = Field(default="https://app.attendee.dev", description="Attendee API base URL")
    
    # OpenAI API Configuration
    openai_api_key: str = Field(..., description="OpenAI API key for analysis")
    
    # Database
    database_url: str = Field(..., description="Database connection URL")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    
    # Webhook Configuration
    webhook_secret: Optional[str] = Field(default=None, description="Webhook HMAC secret")
    webhook_base_url: Optional[str] = Field(default=None, description="Production webhook base URL (e.g., https://api.yourdomain.com)")
    
    # Environment
    environment: str = Field(default="development", description="Environment: development, staging, production")
    
    # Ngrok Configuration (Development only)
    ngrok_auth_token: Optional[str] = Field(default=None, description="Ngrok authentication token")
    auto_start_ngrok: bool = Field(default=True, description="Auto-start ngrok tunnel on startup")
    ngrok_subdomain: Optional[str] = Field(default=None, description="Ngrok subdomain (requires auth token)")
    ngrok_port: int = Field(default=8000, description="Port for ngrok tunnel")
    
    # App settings
    app_name: str = Field(default="Meeting Bot Service", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Legacy/Optional fields (for backward compatibility)
    api_key_header: Optional[str] = Field(default=None, description="Legacy API key header (unused)")
    recall_api_key: Optional[str] = Field(default=None, description="Legacy recall API key (unused)")
    recall_api_base_url: Optional[str] = Field(default=None, description="Legacy recall API base URL (unused)")
    recall_region: Optional[str] = Field(default=None, description="Legacy recall region (unused)")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() in ["production", "staging"]
    
    @property
    def should_use_ngrok(self) -> bool:
        """Determine if ngrok should be used based on environment"""
        return self.environment.lower() == "development" and self.auto_start_ngrok
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings() 