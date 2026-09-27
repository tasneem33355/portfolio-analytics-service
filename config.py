import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "CrediX Portfolio Analytics Service"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1/analytics"
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Allow Vercel frontend and local development
    CORS_ORIGINS: list[str] = [
        "https://credi-x.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ]

    class Config:
        case_sensitive = True


settings = Settings()
