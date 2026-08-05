"""Application configuration using pydantic-settings"""

from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # =============================================================================
    # Application Settings
    # =============================================================================
    app_name: str = Field(default="SmartReco", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    app_env: str = Field(default="development", description="Environment")
    debug: bool = Field(default=False, description="Debug mode")
    
    # =============================================================================
    # Database Configuration
    # =============================================================================
    database_url: str = Field(
        ..., 
        description="PostgreSQL connection string"
    )
    db_pool_size: int = Field(default=10, description="Database connection pool size")
    db_max_overflow: int = Field(default=20, description="Max overflow connections")
    db_pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    db_echo: bool = Field(default=False, description="Echo SQL queries")
    
    # =============================================================================
    # Redis Configuration
    # =============================================================================
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string"
    )
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_max_connections: int = Field(default=50, description="Max Redis connections")
    
    # =============================================================================
    # ChromaDB Configuration
    # =============================================================================
    chroma_host: str = Field(default="localhost", description="ChromaDB host")
    chroma_port: int = Field(default=8000, description="ChromaDB port")
    chroma_collection_name: str = Field(
        default="smartreco_embeddings",
        description="ChromaDB collection name"
    )
    
    # =============================================================================
    # Embedding Model Configuration
    # =============================================================================
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence Transformers model"
    )
    embedding_dimension: int = Field(default=384, description="Embedding vector dimension")
    
    # =============================================================================
    # Mesh API Configuration (OpenAI-compatible LLM Gateway)
    # =============================================================================
    mesh_api_key: str = Field(..., description="Mesh API key")
    mesh_api_base_url: str = Field(
        default="https://api.mesh.com/v1",
        description="Mesh API base URL"
    )
    mesh_model: str = Field(
        default="tencent/hy3",
        description="LLM model to use"
    )
    mesh_max_tokens: int = Field(default=4096, description="Max tokens per request")
    mesh_temperature: float = Field(default=0.7, description="LLM temperature")
    
    @field_validator("mesh_api_key")
    @classmethod
    def validate_mesh_api_key(cls, v: str) -> str:
        """Validate MESH_API_KEY is not empty"""
        if not v or v.strip() == "":
            raise ValueError("MESH_API_KEY cannot be empty - required for LLM operations")
        return v
    
    # =============================================================================
    # LangSmith Configuration
    # =============================================================================
    langsmith_api_key: Optional[str] = Field(default=None, description="LangSmith API key")
    langsmith_project: str = Field(
        default="smartreco-prod",
        description="LangSmith project name"
    )
    langsmith_endpoint: str = Field(
        default="https://api.smith.langchain.com",
        description="LangSmith endpoint"
    )
    langsmith_tracing_enabled: bool = Field(
        default=False,
        description="Enable LangSmith tracing"
    )
    
    # =============================================================================
    # Authentication & Security
    # =============================================================================
    secret_key: str = Field(..., description="Secret key for JWT tokens")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration in days"
    )
    bcrypt_rounds: int = Field(default=12, description="Bcrypt hashing rounds")
    
    # =============================================================================
    # SMTP Configuration
    # =============================================================================
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP host")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_user: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    smtp_from_email: str = Field(
        default="noreply@smartreco.com",
        description="From email address"
    )
    smtp_from_name: str = Field(
        default="SmartReco Platform",
        description="From name"
    )
    smtp_tls: bool = Field(default=True, description="Use TLS")
    smtp_ssl: bool = Field(default=False, description="Use SSL")
    app_url: str = Field(
        default="http://localhost:3000",
        description="Frontend application URL for email links"
    )
    
    # =============================================================================
    # Recommendation System Settings
    # =============================================================================
    default_recommendation_count: int = Field(
        default=10,
        description="Default number of recommendations"
    )
    max_recommendation_count: int = Field(
        default=50,
        description="Maximum recommendations allowed"
    )
    min_similarity_threshold: float = Field(
        default=0.6,
        description="Minimum similarity threshold"
    )
    diversity_factor: float = Field(
        default=0.3,
        description="Diversity factor for recommendations"
    )
    recommendation_cache_ttl: int = Field(
        default=3600,
        description="Recommendation cache TTL in seconds"
    )
    persona_cache_ttl: int = Field(
        default=1800,
        description="Persona cache TTL in seconds"
    )
    
    # =============================================================================
    # Scheduler Configuration
    # =============================================================================
    scheduler_enabled: bool = Field(default=True, description="Enable scheduler")
    scheduler_timezone: str = Field(default="UTC", description="Scheduler timezone")
    persona_update_interval: int = Field(
        default=60,
        description="Persona update interval in minutes"
    )
    embedding_refresh_interval: int = Field(
        default=1440,
        description="Embedding refresh interval in minutes"
    )
    analytics_job_interval: int = Field(
        default=30,
        description="Analytics job interval in minutes"
    )
    
    # =============================================================================
    # Logging Configuration
    # =============================================================================
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")
    log_file_path: str = Field(
        default="logs/smartreco.log",
        description="Log file path"
    )
    log_file_max_bytes: int = Field(
        default=10485760,
        description="Max log file size in bytes"
    )
    log_file_backup_count: int = Field(
        default=5,
        description="Number of log file backups"
    )
    
    # =============================================================================
    # CORS Settings
    # =============================================================================
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="CORS allowed origins"
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow credentials")
    cors_allow_methods: List[str] = Field(default=["*"], description="Allowed methods")
    cors_allow_headers: List[str] = Field(default=["*"], description="Allowed headers")
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # =============================================================================
    # Rate Limiting
    # =============================================================================
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_per_minute: int = Field(
        default=60,
        description="Rate limit per minute"
    )
    rate_limit_per_hour: int = Field(
        default=1000,
        description="Rate limit per hour"
    )
    
    # =============================================================================
    # Celery Configuration
    # =============================================================================
    celery_broker_url: Optional[str] = Field(
        default=None,
        description="Celery broker URL"
    )
    celery_result_backend: Optional[str] = Field(
        default=None,
        description="Celery result backend"
    )
    celery_task_serializer: str = Field(default="json", description="Task serializer")
    celery_result_serializer: str = Field(default="json", description="Result serializer")
    celery_accept_content: List[str] = Field(
        default=["json"],
        description="Accepted content types"
    )
    celery_timezone: str = Field(default="UTC", description="Celery timezone")
    
    @field_validator("celery_accept_content", mode="before")
    @classmethod
    def parse_celery_accept_content(cls, v: object) -> List[str]:
        """Parse celery accept content from comma-separated string"""
        if isinstance(v, str):
            return [content.strip() for content in v.split(",")]
        return v
    
    # =============================================================================
    # Feature Flags
    # =============================================================================
    enable_behavioral_analysis: bool = Field(
        default=True,
        description="Enable behavioral analysis"
    )
    enable_persona_generation: bool = Field(
        default=True,
        description="Enable persona generation"
    )
    enable_narrative_generation: bool = Field(
        default=True,
        description="Enable narrative generation"
    )
    enable_diversity_boost: bool = Field(
        default=True,
        description="Enable diversity boost"
    )
    enable_cold_start_handling: bool = Field(
        default=True,
        description="Enable cold start handling"
    )
    
    # =============================================================================
    # Monitoring & Metrics
    # =============================================================================
    enable_metrics: bool = Field(default=True, description="Enable metrics")
    metrics_port: int = Field(default=9090, description="Metrics port")
    health_check_endpoint: str = Field(
        default="/health",
        description="Health check endpoint"
    )
    
    # =============================================================================
    # Computed Properties
    # =============================================================================
    
    @property
    def chroma_url(self) -> str:
        """Construct ChromaDB URL"""
        return f"http://{self.chroma_host}:{self.chroma_port}"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.app_env.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.app_env.lower() == "development"


# Global settings instance
settings = Settings()


# Export for easy import
__all__ = ["settings", "Settings"]
