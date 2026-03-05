"""
Pydantic Schemas
================

Request and response models for the API.

IMPROVEMENT OPPORTUNITIES:
1. Add more validation rules
2. Implement nested schemas for complex responses
3. Add documentation to each field
4. Implement response serialization customization
"""

from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================


class AnalyzeRequest(BaseModel):
    """Request schema for product analysis."""

    asins: List[str] = Field(
        ..., description="List of Amazon ASINs to analyze", min_length=1, max_length=50
    )
    category: Optional[str] = Field(None, description="Product category (optional)")
    limit: int = Field(5, description="Number of top candidates to return", ge=1, le=20)


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================


class ForecastPhaseResponse(BaseModel):
    """Forecast phase data in response."""

    phase: str
    days: int
    estimated_units: float
    price: float
    acos: float


class EconomicsPhaseResponse(BaseModel):
    """Economics data for a phase."""

    revenue: float
    product_cost: float
    amazon_fees: float
    ppc_cost: float
    total_costs: float
    net_profit: float
    net_margin_percent: float
    net_margin_display: str


class CandidateResponse(BaseModel):
    """Single candidate in results."""

    rank: int
    asin: str
    title: Optional[str] = None
    category: Optional[str] = None
    score: float
    demand_consistency: float
    bsr_variability: float
    review_gap: int
    seller_fragmentation: float
    margin_viable: bool

    # Forecast phases
    launch: Optional[ForecastPhaseResponse] = None
    growth: Optional[ForecastPhaseResponse] = None
    mature: Optional[ForecastPhaseResponse] = None

    # Economics
    economics_launch: Optional[EconomicsPhaseResponse] = None
    economics_growth: Optional[EconomicsPhaseResponse] = None
    economics_mature: Optional[EconomicsPhaseResponse] = None

    # Capital requirements
    capital_requirement: Optional[dict] = None

    # Inventory plan
    inventory_plan: Optional[dict] = None


class AnalyzeResponse(BaseModel):
    """Response schema for analyze endpoint."""

    total_analyzed: int
    passed_margin_check: int
    candidates: List[CandidateResponse]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ASINResponse(BaseModel):
    """Response for single ASIN."""

    asin: str
    title: Optional[str] = None
    category: Optional[str] = None
    current_price: Optional[float] = None
    current_bsr: Optional[int] = None
    current_reviews: Optional[int] = None
    created_at: Optional[datetime] = None


class CandidatesListResponse(BaseModel):
    """Response for listing candidates."""

    candidates: List[dict]
    total: int


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# ERROR SCHEMAS
# =============================================================================


class ErrorDetail(BaseModel):
    """Error detail."""

    code: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
