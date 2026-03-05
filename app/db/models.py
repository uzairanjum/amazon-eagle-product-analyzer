"""
Database Models
===============

This module defines the data models for the application.
These Pydantic models represent the database schema and provide
validation for API requests/responses.

Note: These are Python representations of the Supabase tables.
The actual database schema should be created in Supabase.

IMPROVEMENT OPPORTUNITIES:
1. Add field-level validation rules
2. Implement custom validators for business logic
3. Add documentation to each field
4. Consider using SQLAlchemy for more complex queries
5. Add database-level constraints
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field


# =============================================================================
# ASIN Models (Product Metadata)
# =============================================================================


class ASINBase(BaseModel):
    """Base ASIN model with common fields."""

    asin: str = Field(..., description="Amazon Standard Identification Number")
    title: Optional[str] = Field(None, description="Product title")
    category: Optional[str] = Field(None, description="Product category")
    current_price: Optional[float] = Field(None, description="Current price")
    current_bsr: Optional[int] = Field(None, description="Current Best Seller Rank")
    current_reviews: Optional[int] = Field(None, description="Current review count")
    current_rating: Optional[float] = Field(None, description="Current average rating")
    current_sellers: Optional[int] = Field(
        None, description="Current number of sellers"
    )


class ASINCreate(ASINBase):
    """Model for creating a new ASIN."""

    pass


class ASINUpdate(BaseModel):
    """Model for updating an existing ASIN."""

    title: Optional[str] = None
    category: Optional[str] = None
    current_price: Optional[float] = None
    current_bsr: Optional[int] = None
    current_reviews: Optional[int] = None
    current_rating: Optional[float] = None
    current_sellers: Optional[int] = None


class ASINResponse(ASINBase):
    """Model for ASIN responses."""

    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Daily Snapshot Models (Time-Series Data)
# =============================================================================


class DailySnapshotBase(BaseModel):
    """Base model for daily snapshot."""

    asin: str = Field(..., description="Amazon product ID")
    date: date = Field(..., description="Snapshot date")
    price: Optional[float] = Field(None, description="Product price on this date")
    bsr: Optional[int] = Field(None, description="Best Seller Rank")
    reviews: Optional[int] = Field(None, description="Number of reviews")
    rating: Optional[float] = Field(None, description="Average rating")
    sellers: Optional[int] = Field(None, description="Number of sellers")


class DailySnapshotCreate(DailySnapshotBase):
    """Model for creating daily snapshot."""

    pass


class DailySnapshotResponse(DailySnapshotBase):
    """Model for daily snapshot responses."""

    id: int

    class Config:
        from_attributes = True


# =============================================================================
# Opportunity Candidate Models (Scored Products)
# =============================================================================


class OpportunityCandidateBase(BaseModel):
    """Base model for opportunity candidate."""

    asin: str = Field(..., description="Amazon product ID")
    score: float = Field(..., description="Overall opportunity score (0-100)")
    demand_consistency: float = Field(..., description="Demand stability score (0-100)")
    bsr_variability: float = Field(
        ..., description="BSR variability (coefficient of variation)"
    )
    review_gap: int = Field(..., description="Review gap vs competitors")
    seller_fragmentation: float = Field(..., description="Seller fragmentation score")
    margin_viable: bool = Field(..., description="Passes margin requirement (>10%)")


class OpportunityCandidateCreate(OpportunityCandidateBase):
    """Model for creating opportunity candidate."""

    pass


class OpportunityCandidateResponse(OpportunityCandidateBase):
    """Model for candidate responses."""

    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Forecast Plan Models (3-Phase Forecasting)
# =============================================================================


class ForecastPhase(str):
    """Forecast phase enumeration."""

    LAUNCH = "launch"
    GROWTH = "growth"
    MATURE = "mature"


class ForecastPlanBase(BaseModel):
    """Base model for forecast plan."""

    candidate_id: int = Field(..., description="Reference to opportunity candidate")
    phase: str = Field(..., description="Forecast phase (launch/growth/mature)")
    estimated_units: float = Field(..., description="Estimated units per day")
    price: float = Field(..., description="Projected price")
    acos: float = Field(..., description="Advertising Cost of Sales (0-1)")
    net_margin_percent: float = Field(..., description="Net margin percentage (0-1)")


class ForecastPlanCreate(ForecastPlanBase):
    """Model for creating forecast plan."""

    pass


class ForecastPlanResponse(ForecastPlanBase):
    """Model for forecast plan responses."""

    id: int

    class Config:
        from_attributes = True


# =============================================================================
# Composite Models (For API Responses)
# =============================================================================


class ForecastWithCandidate(BaseModel):
    """Combined forecast with candidate details."""

    candidate: OpportunityCandidateResponse
    forecasts: List[ForecastPlanResponse]


class TopCandidateResponse(BaseModel):
    """Structured output for Top N candidates."""

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

    # Forecast data
    launch: Optional[dict] = None
    growth: Optional[dict] = None
    mature: Optional[dict] = None

    # Economics
    economics: Optional[dict] = None

    # Capital requirements
    capital_requirement: Optional[dict] = None

    # Inventory plan
    inventory_plan: Optional[dict] = None
