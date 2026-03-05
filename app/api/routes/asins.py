"""
ASIN Routes
===========

Endpoints for ASIN-related operations.

IMPROVEMENT OPPORTUNITIES:
1. Add pagination
2. Add filtering
3. Add caching
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.schemas.request import ASINResponse
from app.db import get_asin_by_asin, get_all_asins

router = APIRouter(prefix="/asins", tags=["asins"])


@router.get("/{asin}", response_model=ASINResponse)
async def get_asin(asin: str):
    """
    Get ASIN details.

    Args:
        asin: Amazon product ID

    Returns:
        ASIN metadata
    """
    asin_data = get_asin_by_asin(asin)

    if not asin_data:
        raise HTTPException(status_code=404, detail="ASIN not found")

    return ASINResponse(**asin_data)


@router.get("")
async def list_asins(
    limit: int = Query(10, ge=1, le=100), offset: int = Query(0, ge=0)
):
    """
    List ASINs.

    Args:
        limit: Maximum number to return
        offset: Number to skip

    Returns:
        List of ASINs
    """
    asins = get_all_asins()

    return {
        "asins": asins[offset : offset + limit],
        "total": len(asins),
        "limit": limit,
        "offset": offset,
    }
