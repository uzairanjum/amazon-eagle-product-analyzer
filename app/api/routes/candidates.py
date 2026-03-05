"""
Candidates Routes
=================

Endpoints for opportunity candidates.

IMPROVEMENT OPPORTUNITIES:
1. Add detailed candidate response with full data
2. Add filtering by score, margin viability, etc.
3. Add pagination
"""

from fastapi import APIRouter, Query

from app.db import get_candidates

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("")
async def list_candidates(
    limit: int = Query(10, ge=1, le=100),
    margin_only: bool = Query(
        False, description="Only return candidates that pass margin check"
    ),
):
    """
    List opportunity candidates.

    Args:
        limit: Maximum number to return
        margin_only: Filter to only candidates passing margin check

    Returns:
        List of scored candidates
    """
    candidates = get_candidates(limit=limit, margin_only=margin_only)

    return {"candidates": candidates, "total": len(candidates), "limit": limit}
