"""
Configuration Management
========================

This module handles all application configuration using environment variables.
It provides type-safe access to settings throughout the application.

IMPROVEMENT OPPORTUNITIES:
1. Add validation for required fields on startup
2. Support for different environment profiles (dev/staging/prod)
3. Add secret rotation support for production
4. Implement configuration caching for performance
5. Add environment-specific rate limiting configs
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    TODO: Replace default values with actual credentials when provided.
    """

    # Supabase Configuration
    # =========================================================================
    supabase_url: str = "https://your-project.supabase.co"
    supabase_key: str = "your-supabase-api-key"

    # Keepa API Configuration
    # =========================================================================
    # Keepa API key - get from https://keepa.com/
    keepa_api_key: str = "your-keepa-api-key"

    # Keepa domain: 1=Amazon.com, 2=Amazon.co.uk, 3=Amazon.de, etc.
    # See: https://keepa.com/#!api
    keepa_domain: int = 1

    # Application Settings
    # =========================================================================
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Rate Limiting
    # =========================================================================
    # Delay between Keepa API requests (seconds)
    # Keepa free tier: 1 request/second
    keepa_request_delay: float = 1.0

    # Feature Flags
    # =========================================================================
    # Enable mock data for testing without Keepa API
    enable_mock_data: bool = False

    model_config = SettingsConfigDict(
        env_file=Path(".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Allow extra fields in .env
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    This uses lru_cache to ensure settings are only loaded once,
    improving performance across multiple imports.

    IMPROVEMENT: In production, consider using a proper dependency
    injection framework for better testability.
    """
    return Settings()
