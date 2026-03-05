"""Database module for Supabase operations."""

from app.db.client import (
    SupabaseClient,
    get_all_asins,
    get_asin_by_asin,
    create_asin,
    upsert_asin,
    get_snapshots_by_asin,
    create_snapshot,
    upsert_snapshots,
    get_candidates,
    get_candidate_by_asin,
    create_candidate,
    upsert_candidate,
    get_forecasts_by_candidate,
    create_forecast,
    create_forecasts,
)

__all__ = [
    "SupabaseClient",
    "get_all_asins",
    "get_asin_by_asin",
    "create_asin",
    "upsert_asin",
    "get_snapshots_by_asin",
    "create_snapshot",
    "upsert_snapshots",
    "get_candidates",
    "get_candidate_by_asin",
    "create_candidate",
    "upsert_candidate",
    "get_forecasts_by_candidate",
    "create_forecast",
    "create_forecasts",
]
