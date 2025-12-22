"""
Komission FACTORY v5.2 Configuration
Environment-based settings with Pydantic
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "Komission FACTORY v5.2"
    VERSION: str = "5.2.0"
    ENVIRONMENT: str = "development"  # development | staging | production

    # PostgreSQL Database
    POSTGRES_USER: str = "kmeme_user"
    POSTGRES_PASSWORD: str = "kmeme_password"
    POSTGRES_DB: str = "kmeme_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis Cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Neo4j Graph Database
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "kmeme_password"

    # AI Models
    GEMINI_API_KEY: str = ""
    CLAUDE_API_KEY: str = ""

    # Monitoring
    SENTRY_DSN: str = ""

    # AWS S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-northeast-2"
    S3_BUCKET_NAME: str = "kmeme-factory-assets"

    # Firebase Auth (legacy)
    FIREBASE_CREDENTIALS_PATH: str = "firebase-adminsdk.json"

    # JWT Settings (SECURE - use strong secret in production!)
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production-256-bits-minimum"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Google OAuth 2.0
    GOOGLE_CLIENT_ID: str = ""  # From Google Cloud Console
    GOOGLE_CLIENT_SECRET: str = ""  # Not needed for ID token verification

    # CORS Settings
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """Parse CORS_ORIGINS into list"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

