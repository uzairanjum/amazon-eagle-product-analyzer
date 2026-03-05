"""
Opportunity Scoring Engine
==========================

This module calculates opportunity scores for Amazon products based on
multiple factors that indicate potential for success.

Scoring Components:
1. Demand Consistency: How stable is the product's sales over time?
2. BSR Variability: How much does the Best Seller Rank fluctuate?
3. Review Gap: How many reviews does the product have vs competitors?
4. Seller Fragmentation: How many sellers are competing?

IMPROVEMENT OPPORTUNITIES:
1. Add more sophisticated scoring algorithms
2. Implement machine learning for weight optimization
3. Add category-specific scoring rules
4. Implement real-time scoring updates
5. Add scoring confidence intervals
6. Implement A/B testing for scoring models
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd

from app.constants import ScoringWeights, ScoringThresholds
from app.core.exceptions import ScoringError


class ScoringEngine:
    """
    Engine for calculating product opportunity scores.

    The score is a weighted combination of multiple factors,
    each normalized to a 0-100 scale.
    """

    def __init__(self):
        """Initialize scoring engine with weights."""
        self.weights = ScoringWeights()
        self.thresholds = ScoringThresholds()

    def calculate_score(
        self, metrics: Dict[str, Any], current_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Calculate overall opportunity score.

        Args:
            metrics: Calculated metrics from decoder
            current_data: Current product data

        Returns:
            Dictionary with score breakdown
        """
        try:
            # Calculate individual component scores
            demand_score = self._calc_demand_score(metrics)
            bsr_score = self._calc_bsr_score(metrics)
            review_score = self._calc_review_score(metrics, current_data)
            seller_score = self._calc_seller_score(metrics, current_data)

            # Calculate weighted total
            total_score = (
                demand_score * self.weights.DEMAND_CONSISTENCY
                + bsr_score * self.weights.BSR_VARIABILITY
                + review_score * self.weights.REVIEW_GAP
                + seller_score * self.weights.SELLER_FRAGMENTATION
            )

            return {
                "score": round(total_score, 2),
                "demand_consistency": round(demand_score, 2),
                "bsr_variability": round(bsr_score, 2),
                "review_gap": review_score,
                "seller_fragmentation": round(seller_score, 2),
                "weights_used": {
                    "demand_consistency": self.weights.DEMAND_CONSISTENCY,
                    "bsr_variability": self.weights.BSR_VARIABILITY,
                    "review_gap": self.weights.REVIEW_GAP,
                    "seller_fragmentation": self.weights.SELLER_FRAGMENTATION,
                },
            }

        except Exception as e:
            raise ScoringError(f"Failed to calculate score: {str(e)}")

    def _calc_demand_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate demand consistency score.

        Higher demand consistency = more predictable sales = better opportunity

        Score is based on:
        - Coefficient of variation of BSR (lower = more stable)
        - Trend analysis (is demand growing or declining?)

        IMPROVEMENT: Add trend analysis to detect growing/declining products.
        """
        demand_consistency = metrics.get("demand_consistency", 0)

        # Normalize to 0-100
        # demand_consistency is already calculated as 100 - (cv * 100)
        score = min(100, max(0, demand_consistency))

        return score

    def _calc_bsr_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate BSR variability score.

        Lower BSR = better sales = higher score

        Score is inverse of coefficient of variation.
        """
        bsr_cv = metrics.get("bsr_cv", float("inf"))

        if bsr_cv == 0:
            return 100.0

        if bsr_cv == float("inf") or bsr_cv is None:
            return 0.0

        # Convert CV to score (lower CV = higher score)
        # CV of 0 = 100, CV of 2.0 = 0
        score = max(0, 100 - (bsr_cv * 50))

        return score

    def _calc_review_score(
        self, metrics: Dict[str, Any], current_data: Dict[str, Any] = None
    ) -> float:
        """
        Calculate review gap score.

        The "review gap" represents the opportunity to outrank competitors.

        If product has fewer reviews than average, there's opportunity to catch up.
        If product has more reviews, it's already established.

        IMPROVEMENT: Calculate actual competitor average from category data.
        """
        reviews_current = metrics.get("reviews_current", 0)

        # For V1, use simplified scoring:
        # More reviews = more established = higher base score
        # But also opportunity for products with moderate reviews

        if current_data and "reviews" in current_data:
            competitor_avg = current_data.get("competitor_avg_reviews", 1000)
            review_gap = reviews_current - competitor_avg
        else:
            # Simplified: use absolute review count
            review_gap = reviews_current

        # Score based on review count
        # Higher review count = more established
        # But products with ~100-500 reviews have growth potential
        if reviews_current < 50:
            score = 40  # New product, lots of opportunity
        elif reviews_current < 200:
            score = 60  # Growing product
        elif reviews_current < 1000:
            score = 80  # Established
        else:
            score = 100  # Very established

        return float(score)

    def _calc_seller_score(
        self, metrics: Dict[str, Any], current_data: Dict[str, Any] = None
    ) -> float:
        """
        Calculate seller fragmentation score.

        More sellers = more competition = lower score

        IMPROVEMENT: Add analysis of seller quality (FBA vs FBM, etc.)
        """
        sellers_current = metrics.get("sellers_current", 0)

        if sellers_current == 0:
            return 50  # Unknown

        # Fewer sellers = less competition = higher score
        if sellers_current <= 3:
            score = 90  # Low competition
        elif sellers_current <= 5:
            score = 70  # Moderate competition
        elif sellers_current <= 10:
            score = 50  # High competition
        else:
            score = 30  # Very high competition

        return float(score)

    def rank_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank candidates by opportunity score.

        Args:
            candidates: List of candidate dictionaries with scores

        Returns:
            Sorted list (highest score first)
        """
        return sorted(candidates, key=lambda x: x.get("score", 0), reverse=True)


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def get_scoring_engine() -> ScoringEngine:
    """Get scoring engine instance."""
    return ScoringEngine()
