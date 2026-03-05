"""
Simple Runner Script
====================

Run the FastAPI application without Docker.

Usage:
    python run.py

IMPROVEMENT OPPORTUNITIES:
1. Add argument parsing for different modes
2. Add auto-reload support
3. Add logging configuration
4. Add environment-specific configurations
"""

import uvicorn
from app.config import get_settings


def main():
    """Run the application."""
    settings = get_settings()

    print("=" * 50)
    print("AMZ Eagle Product Analyzer")
    print("=" * 50)
    print(f"Environment: {settings.app_env}")
    print(f"Host: {settings.app_host}:{settings.app_port}")
    print(f"Supabase: {settings.supabase_url}")
    print(f"Keepa Domain: {settings.keepa_domain}")
    print(f"Mock Mode: {settings.enable_mock_data}")
    print("=" * 50)
    print()
    print("Starting server...")
    print(f"API Docs: http://{settings.app_host}:{settings.app_port}/docs")
    print()

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
    )


if __name__ == "__main__":
    main()
