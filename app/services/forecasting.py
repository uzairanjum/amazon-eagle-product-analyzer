"""
Forecasting Engine
==================

This module generates 3-phase forecasts for Amazon products:
- Phase A (Launch): Days 0-30 - Initial ramp-up
- Phase B (Growth): Days 31-180 - Scaling phase
- Phase C (Mature): Days 181+ - Stable phase

For each phase, we forecast:
- Estimated units per day
- Recommended price
- Expected ACOS (Advertising Cost of Sales)
- Net margin after PPC

IMPROVEMENT OPPORTUNITIES:
1. Add machine learning models for more accurate forecasting
2. Implement seasonal adjustment factors
3. Add category-specific growth patterns
4. Support competitor-based adjustments
5. Add confidence intervals
6. Implement scenario analysis (best/worst case)
7. Add historical validation of forecasts
"""

from typing import Dict, Any, List
import numpy as np

from app.constants import ForecastingConstants, ForecastPhase
from app.core.exceptions import ForecastingError


class ForecastingEngine:
    """
    Engine for generating product forecasts.

    This is a simplified V1 forecasting engine using historical data
    patterns. More sophisticated approaches would use ML models.
    """

    def __init__(self):
        """Initialize forecasting engine."""
        self.constants = ForecastingConstants()

    def generate_forecast(
        self, metrics: Dict[str, Any], score: float, current_price: float = None
    ) -> Dict[str, Any]:
        """
        Generate 3-phase forecast for a product.

        Args:
            metrics: Historical metrics from decoder
            score: Opportunity score (0-100)
            current_price: Current product price

        Returns:
            Dictionary with 3-phase forecast
        """
        try:
            # Estimate base units from BSR
            base_units = self._estimate_base_units(metrics)

            # Determine growth multiplier based on score
            growth_multiplier = self._get_growth_multiplier(score)

            # Generate forecasts for each phase
            forecast = {
                ForecastPhase.LAUNCH: self._forecast_launch(
                    base_units, growth_multiplier, current_price
                ),
                ForecastPhase.GROWTH: self._forecast_growth(
                    base_units, growth_multiplier, current_price
                ),
                ForecastPhase.MATURE: self._forecast_mature(
                    base_units, growth_multiplier, current_price
                ),
            }

            return forecast

        except Exception as e:
            raise ForecastingError(f"Failed to generate forecast: {str(e)}")

    def _estimate_base_units(self, metrics: Dict[str, Any]) -> float:
        """
        Estimate base daily units from BSR.

        This is a simplified estimation based on typical Amazon patterns.

        IMPROVEMENT: Use more sophisticated BSR-to-units conversion
        with category-specific multipliers.
        """
        bsr_current = metrics.get("bsr_current")

        if not bsr_current or bsr_current == 0:
            # No BSR data - use default
            return 1.0

        # Simplified conversion (very rough estimate)
        # Lower BSR = more units
        # This is a very rough approximation
        if bsr_current < 1000:
            units = 50.0  # Top products
        elif bsr_current < 5000:
            units = 20.0  # Good products
        elif bsr_current < 20000:
            units = 5.0  # Average products
        elif bsr_current < 50000:
            units = 2.0  # Below average
        else:
            units = 0.5  # Low sellers

        return units

    def _get_growth_multiplier(self, score: float) -> float:
        """
        Get growth multiplier based on opportunity score.

        Higher scores indicate better products = faster growth.

        IMPROVEMENT: Make this category-specific.
        """
        if score >= 80:
            return 1.5  # Excellent product - strong growth
        elif score >= 60:
            return 1.2  # Good product - moderate growth
        elif score >= 40:
            return 1.0  # Average product - normal growth
        else:
            return 0.8  # Poor product - slow growth

    def _forecast_launch(
        self, base_units: float, growth_multiplier: float, current_price: float
    ) -> Dict[str, Any]:
        """Generate launch phase forecast."""
        days = self.constants.LAUNCH_DAYS

        # Launch: lower units due to new product
        units = base_units * self.constants.LAUNCH_UNITS_MULTIPLIER * growth_multiplier

        # Launch: slightly lower price to gain traction
        price = (
            current_price * self.constants.PRICE_ADJUSTMENT_LAUNCH
            if current_price
            else 25.99
        )

        # Launch: higher ACOS due to advertising investment
        acos = self.constants.DEFAULT_ACOS_LAUNCH

        return {
            "phase": ForecastPhase.LAUNCH,
            "days": days,
            "estimated_units": round(units, 2),
            "price": round(price, 2),
            "acos": acos,
        }

    def _forecast_growth(
        self, base_units: float, growth_multiplier: float, current_price: float
    ) -> Dict[str, Any]:
        """Generate growth phase forecast."""
        days = self.constants.GROWTH_DAYS

        # Growth: increasing units
        units = base_units * self.constants.GROWTH_UNITS_MULTIPLIER * growth_multiplier

        # Growth: standard pricing
        price = (
            current_price * self.constants.PRICE_ADJUSTMENT_GROWTH
            if current_price
            else 25.99
        )

        # Growth: moderate ACOS
        acos = self.constants.DEFAULT_ACOS_GROWTH

        return {
            "phase": ForecastPhase.GROWTH,
            "days": days,
            "estimated_units": round(units, 2),
            "price": round(price, 2),
            "acos": acos,
        }

    def _forecast_mature(
        self, base_units: float, growth_multiplier: float, current_price: float
    ) -> Dict[str, Any]:
        """Generate mature phase forecast."""
        days = self.constants.MATURE_DAYS

        # Mature: full potential units
        units = base_units * self.constants.MATURE_UNITS_MULTIPLIER * growth_multiplier

        # Mature: slight premium pricing
        price = (
            current_price * self.constants.PRICE_ADJUSTMENT_MATURE
            if current_price
            else 25.99
        )

        # Mature: lower ACOS (established product)
        acos = self.constants.DEFAULT_ACOS_MATURE

        return {
            "phase": ForecastPhase.MATURE,
            "days": days,
            "estimated_units": round(units, 2),
            "price": round(price, 2),
            "acos": acos,
        }

    def calculate_revenue(self, units: float, price: float) -> float:
        """Calculate daily revenue."""
        return units * price

    def calculate_profit(
        self, revenue: float, landed_cost: float, amazon_fees: float, ppc_cost: float
    ) -> float:
        """Calculate net profit."""
        return revenue - landed_cost - amazon_fees - ppc_cost


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def get_forecasting_engine() -> ForecastingEngine:
    """Get forecasting engine instance."""
    return ForecastingEngine()
