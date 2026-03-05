"""
Business Constants
==================

This module contains all business logic constants used across the application.
These values define the rules for scoring, forecasting, and margin enforcement.

IMPROVEMENT OPPORTUNITIES:
1. Move to database configuration for easy tuning without code changes
2. Add category-specific constants
3. Implement A/B testing support for different constant values
4. Add validation to ensure constants are within valid ranges
5. Implement versioning for constants to track changes over time
"""

from enum import Enum


class ForecastPhase(str, Enum):
    """
    Three-phase growth model for product forecasting.

    - LAUNCH: Initial ramp-up period (typically 0-30 days)
    - GROWTH: Scaling phase (typically 31-180 days)
    - MATURE: Stable phase (typically 181+ days)
    """

    LAUNCH = "launch"
    GROWTH = "growth"
    MATURE = "mature"


# =============================================================================
# SCORING ENGINE CONSTANTS
# =============================================================================


class ScoringWeights:
    """
    Weights for opportunity scoring components.
    Total score = sum(component_score * weight)

    IMPROVEMENT: These weights could be:
    - Made configurable per category
    - Adjusted based on market conditions
    - Tuned via machine learning on historical data
    """

    # Weight for demand consistency (stability of sales over time)
    # Higher weight = more important for long-term viability
    DEMAND_CONSISTENCY = 0.40

    # Weight for BSR variability (lower variability = more predictable)
    BSR_VARIABILITY = 0.30

    # Weight for review gap (opportunity to outrank competitors)
    REVIEW_GAP = 0.20

    # Weight for seller fragmentation (less competition = better)
    SELLER_FRAGMENTATION = 0.10

    # Total should equal 1.0
    assert (
        DEMAND_CONSISTENCY + BSR_VARIABILITY + REVIEW_GAP + SELLER_FRAGMENTATION == 1.0
    )


# Scoring thresholds
class ScoringThresholds:
    """Thresholds for scoring categorization."""

    # Minimum demand consistency score (0-100)
    MIN_DEMAND_CONSISTENCY = 30.0

    # Maximum BSR variability coefficient of variation
    MAX_BSR_VARIABILITY = 2.0

    # Minimum review gap (reviews you need to catch up)
    MIN_REVIEW_GAP = -500  # Negative means you have more reviews

    # Minimum seller count for fragmentation
    MIN_SELLERS = 3


# =============================================================================
# FORECASTING ENGINE CONSTANTS
# =============================================================================


class ForecastingConstants:
    """
    Constants for 3-phase forecasting model.

    IMPROVEMENT OPPORTUNITIES:
    1. Make phase durations configurable
    2. Add seasonal adjustment factors
    3. Implement category-specific growth rates
    4. Add competitor-based adjustments
    """

    # Phase durations (days)
    LAUNCH_DAYS = 30
    GROWTH_DAYS = 150  # 31-180
    MATURE_DAYS = 730  # 181-911 (approx 2 years)

    # Growth rates per phase (multiplier of current BSR-based estimate)
    # These are simplified estimates - real forecasting would use ML
    LAUNCH_UNITS_MULTIPLIER = 0.1  # 10% of mature phase units
    GROWTH_UNITS_MULTIPLIER = 0.5  # 50% of mature phase units
    MATURE_UNITS_MULTIPLIER = 1.0  # 100% of mature phase units

    # Default assumptions
    DEFAULT_ACOS_LAUNCH = 0.50  # 50% ACOS during launch (high advertising)
    DEFAULT_ACOS_GROWTH = 0.35  # 35% ACOS during growth
    DEFAULT_ACOS_MATURE = 0.25  # 25% ACOS once mature

    # Price adjustment during phases
    PRICE_ADJUSTMENT_LAUNCH = 0.95  # Slightly lower to gain traction
    PRICE_ADJUSTMENT_GROWTH = 1.0  # Standard pricing
    PRICE_ADJUSTMENT_MATURE = 1.05  # Slight premium once established


# =============================================================================
# ECONOMICS CONSTANTS
# =============================================================================


class EconomicsConstants:
    """
    Constants for economics and margin calculations.

    IMPROVEMENT OPPORTUNITIES:
    1. Add Amazon fee calculator (varies by category)
    2. Support for FBA vs FBM calculations
    3. Add shipping cost estimation by size
    4. Include storage fees in calculations
    5. Support for multi-currency calculations
    """

    # Minimum margin requirement (10% as per business rule)
    # This is the HARD GATE - products below this threshold are rejected
    MIN_MARGIN_REQUIRED = 0.10

    # Amazon fee estimates (percentages)
    # These are approximations - actual fees vary by category
    REFERRAL_FEE_PERCENT = 0.15  # 15% average referral fee
    FBA_FEE_PERCENT = 0.15  # 15% average FBA fulfillment fee

    # Total Amazon fees (approximate)
    TOTAL_AMAZON_FEES = REFERRAL_FEE_PERCENT + FBA_FEE_PERCENT  # ~30%

    # PPC cost thresholds
    MAX_ACOS_ACCEPTABLE = 0.50  # Reject if ACOS > 50%

    # Inventory planning
    # Months of inventory to plan for initially
    INITIAL_INVENTORY_MONTHS = 3
    ONGOING_INVENTORY_MONTHS = 2

    # Safety stock percentage
    SAFETY_STOCK_PERCENT = 0.20  # 20% buffer


# =============================================================================
# KEEPA API CONSTANTS
# =============================================================================


class KeepaConstants:
    """
    Constants for Keepa API integration.

    IMPROVEMENT OPPORTUNITIES:
    1. Add support for multiple Amazon domains
    2. Implement smart caching based on product category
    3. Add data freshness indicators
    4. Support for historical data range selection
    """

    # Keepa domain mapping (top Amazon marketplaces)
    DOMAINS = {
        1: "amazon.com",
        2: "amazon.co.uk",
        3: "amazon.de",
        4: "amazon.fr",
        5: "amazon.es",
        6: "amazon.it",
        7: "amazon.co.jp",
        8: "amazon.ca",
    }

    # Data points available from Keepa
    # See: https://keepa.com/#!api
    DATA_POINTS = [
        "price",
        "bsr",  # Buy Box Price
        "salesRank",  # Best Seller Rank
        "reviews",  # Review count
        "rating",  # Average rating
        "offer",  # Number of offers/sellers
        "prime",  # Prime availability
        "warehouse",  # Warehouse deals
    ]

    # Default history to fetch (days)
    DEFAULT_HISTORY_DAYS = 730  # 2 years

    # Maximum history Keepa supports (days)
    MAX_HISTORY_DAYS = 911  # ~2.5 years


# =============================================================================
# API RESPONSE CONSTANTS
# =============================================================================


class APIConstants:
    """Constants for API responses."""

    # Maximum ASINs to process in single request
    MAX_ASINS_PER_REQUEST = 50

    # Default number of candidates to return
    DEFAULT_CANDIDATES_LIMIT = 10

    # Top N candidates in structured output
    TOP_N_CANDIDATES = 5

    # Job timeout (seconds)
    JOB_TIMEOUT = 300  # 5 minutes
