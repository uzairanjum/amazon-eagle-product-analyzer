"""
Database Module
===============

This module handles database operations with Supabase.
It provides client initialization and table operations.

IMPROVEMENT OPPORTUNITIES:
1. Add connection pooling for better performance
2. Implement retry logic with exponential backoff
3. Add query result caching
4. Implement proper async operations
5. Add database migration support
"""

from supabase import create_client, Client
from typing import Optional

from app.config import get_settings


class SupabaseClient:
    """
    Supabase database client wrapper.

    This provides a simplified interface for database operations.

    IMPROVEMENT: Consider using async client (supabase-py async)
    for better performance in high-concurrency scenarios.
    """

    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        """
        Get or create Supabase client instance.

        Uses singleton pattern to avoid creating multiple connections.

        IMPROVEMENT: Add connection health check and auto-reconnect
        for production environments.
        """
        if cls._instance is None:
            settings = get_settings()
            cls._instance = create_client(settings.supabase_url, settings.supabase_key)
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset client instance (useful for testing)."""
        cls._instance = None


# =============================================================================
# TABLE OPERATIONS
# =============================================================================
# The following functions provide CRUD operations for each table.
# They use the Supabase client directly.
#
# IMPROVEMENT: Consider using a repository pattern for better
# organization and testability.
# =============================================================================


def get_all_asins() -> list:
    """
    Fetch all ASINs from database.

    IMPROVEMENT: Add pagination support for large datasets.
    """
    client = SupabaseClient.get_client()
    response = client.table("asin").select("*").execute()
    return response.data


def get_asin_by_asin(asin: str) -> Optional[dict]:
    """
    Fetch single ASIN by ASIN value.

    Args:
        asin: Amazon Standard Identification Number

    Returns:
        ASIN record or None if not found
    """
    client = SupabaseClient.get_client()
    response = client.table("asin").select("*").eq("asin", asin).execute()
    return response.data[0] if response.data else None


def create_asin(data: dict) -> dict:
    """
    Create new ASIN record.

    Args:
        data: ASIN data including asin, title, category, etc.

    Returns:
        Created ASIN record
    """
    client = SupabaseClient.get_client()
    response = client.table("asin").insert(data).execute()
    return response.data[0]


def upsert_asin(data: dict) -> dict:
    """
    Insert or update ASIN record.

    This uses UPSERT to handle duplicates gracefully.

    Args:
        data: ASIN data

    Returns:
        Upserted ASIN record
    """
    client = SupabaseClient.get_client()
    response = client.table("asin").upsert(data).execute()
    return response.data[0]


# -----------------------------------------------------------------------------
# Daily Snapshots
# -----------------------------------------------------------------------------


def get_snapshots_by_asin(asin: str, limit: int = 730) -> list:
    """
    Fetch daily snapshots for an ASIN.

    Args:
        asin: Amazon product ID
        limit: Maximum number of days to fetch (default 2 years)

    Returns:
        List of daily snapshot records
    """
    client = SupabaseClient.get_client()
    response = (
        client.table("asin_snapshot_daily")
        .select("*")
        .eq("asin", asin)
        .order("date", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data


def create_snapshot(data: dict) -> dict:
    """Create daily snapshot record."""
    client = SupabaseClient.get_client()
    response = client.table("asin_snapshot_daily").insert(data).execute()
    return response.data[0]


def upsert_snapshots(data: list) -> list:
    """
    Bulk upsert daily snapshots.

    This is more efficient than inserting one at a time.

    Args:
        data: List of snapshot records

    Returns:
        List of upserted records
    """
    client = SupabaseClient.get_client()
    response = client.table("asin_snapshot_daily").upsert(data).execute()
    return response.data


# -----------------------------------------------------------------------------
# Opportunity Candidates
# -----------------------------------------------------------------------------


def get_candidates(limit: int = 10, margin_only: bool = False) -> list:
    """
    Fetch scored opportunity candidates.

    Args:
        limit: Maximum number to return
        margin_only: If True, only return candidates that passed margin check

    Returns:
        List of candidate records
    """
    client = SupabaseClient.get_client()
    query = client.table("opportunity_candidate").select("*")

    if margin_only:
        query = query.eq("margin_viable", True)

    response = query.order("score", desc=True).limit(limit).execute()
    return response.data


def get_candidate_by_asin(asin: str) -> Optional[dict]:
    """Fetch candidate by ASIN."""
    client = SupabaseClient.get_client()
    response = (
        client.table("opportunity_candidate").select("*").eq("asin", asin).execute()
    )
    return response.data[0] if response.data else None


def create_candidate(data: dict) -> dict:
    """Create opportunity candidate record."""
    client = SupabaseClient.get_client()
    response = client.table("opportunity_candidate").insert(data).execute()
    return response.data[0]


def upsert_candidate(data: dict) -> dict:
    """Upsert opportunity candidate."""
    client = SupabaseClient.get_client()
    response = client.table("opportunity_candidate").upsert(data).execute()
    return response.data[0]


# -----------------------------------------------------------------------------
# Forecast Plans
# -----------------------------------------------------------------------------


def get_forecasts_by_candidate(candidate_id: int) -> list:
    """Fetch all forecasts for a candidate."""
    client = SupabaseClient.get_client()
    response = (
        client.table("forecast_plan")
        .select("*")
        .eq("candidate_id", candidate_id)
        .order("phase")
        .execute()
    )
    return response.data


def create_forecast(data: dict) -> dict:
    """Create forecast plan record."""
    client = SupabaseClient.get_client()
    response = client.table("forecast_plan").insert(data).execute()
    return response.data[0]


def create_forecasts(data: list) -> list:
    """Bulk create forecast plan records."""
    client = SupabaseClient.get_client()
    response = client.table("forecast_plan").insert(data).execute()
    return response.data
