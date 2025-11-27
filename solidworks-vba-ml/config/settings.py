"""
Application settings and configuration
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""

    # API Settings
    API_VERSION: str = "v1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Model Settings
    DEFAULT_MODEL: str = "microsoft/codebert-base"
    MODEL_CACHE_DIR: str = "models/cache"
    MAX_MODEL_CACHE_SIZE_GB: int = 10

    # Training Settings
    DEFAULT_BATCH_SIZE: int = 8
    DEFAULT_LEARNING_RATE: float = 2e-5
    DEFAULT_NUM_EPOCHS: int = 3
    MAX_SEQUENCE_LENGTH: int = 512
    USE_LORA: bool = True
    LORA_R: int = 8
    LORA_ALPHA: int = 16
    LORA_DROPOUT: float = 0.05

    # Dataset Settings
    DATASET_BASE_PATH: str = "datasets"
    VBA_MACROS_PATH: str = "datasets/vba_macros"
    API_REFERENCES_PATH: str = "datasets/api_references"
    GEOMETRY_JSON_PATH: str = "datasets/geometry_json"
    PROMPTS_PATH: str = "datasets/prompts"
    TRAINING_SAMPLES_PATH: str = "datasets/training_samples"

    # Validation Settings
    ENABLE_STRICT_VALIDATION: bool = True
    VALIDATE_API_CALLS: bool = True
    CODE_TEST_TIMEOUT: int = 30

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/api.log"
    LOG_ROTATION: str = "100 MB"
    LOG_RETENTION: str = "30 days"

    # Redis (for caching)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Database
    DATABASE_URL: str = "sqlite:///./solidworks_vba_ml.db"

    # Generation Settings
    DEFAULT_MAX_LENGTH: int = 512
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_TOP_P: float = 0.9

    class Config:
        env_file = ".env"
        case_sensitive = True


# Initialize settings
settings = Settings()
