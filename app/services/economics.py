"""
Economics Engine
================

This module handles all economics calculations and margin enforcement.

Key Calculations:
- Revenue = Units × Price
- Landed Cost = Product cost + Shipping + Customs
- Amazon Fees = Referral Fee + FBA Fee
- PPC Cost = Revenue × ACOS
- Net Profit = Revenue - Landed Cost - Amazon Fees - PPC Cost
- Net Margin = Net Profit / Revenue

Business Rule (HARD GATE):
- Net margin must be >= 10% in Growth and Mature phases
- If margin < 10%, product is REJECTED

IMPROVEMENT OPPORTUNITIES:
1. Add detailed Amazon fee calculator (varies by category)
2. Support FBA vs FBM comparison
3. Add shipping cost estimation by size/weight
4. Implement multi-currency support
5. Add storage fee calculations
6. Support long-term storage fee calculations
7. Add ROI and break-even analysis
8. Implement scenario comparisons
"""

from typing import Dict, Any, List
from app.constants import EconomicsConstants
from app.core.exceptions import EconomicsError


class EconomicsEngine:
    """
    Engine for economics calculations and margin enforcement.
    """

    def __init__(self):
        """Initialize economics engine."""
        self.constants = EconomicsConstants()

    def calculate_economics(
        self, forecast: Dict[str, Any], landed_cost: float = None
    ) -> Dict[str, Any]:
        """
        Calculate economics for all forecast phases.

        Args:
            forecast: 3-phase forecast from ForecastingEngine
            landed_cost: Product cost + shipping (default estimate if None)

        Returns:
            Dictionary with economics for each phase
        """
        # Default landed cost if not provided (estimate as 30% of price)
        default_landed_percent = 0.30

        results = {}

        for phase_name, phase_data in forecast.items():
            price = phase_data["price"]
            units = phase_data["estimated_units"]
            acos = phase_data["acos"]

            # Use provided landed cost or estimate
            if landed_cost:
                lc = landed_cost
            else:
                lc = price * default_landed_percent

            # Calculate economics
            economics = self._calc_phase_economics(
                units=units, price=price, acos=acos, landed_cost=lc
            )

            results[phase_name] = economics

        return results

    def _calc_phase_economics(
        self, units: float, price: float, acos: float, landed_cost: float
    ) -> Dict[str, Any]:
        """
        Calculate economics for a single phase.

        Args:
            units: Estimated units per day
            price: Product price
            acos: Advertising Cost of Sales (0-1)
            landed_cost: Cost of product + shipping

        Returns:
            Dictionary with economics breakdown
        """
        # Revenue
        revenue = units * price

        # Costs
        product_cost = units * landed_cost
        amazon_fees = revenue * self.constants.TOTAL_AMAZON_FEES
        ppc_cost = revenue * acos

        # Total costs
        total_costs = product_cost + amazon_fees + ppc_cost

        # Net profit
        net_profit = revenue - total_costs

        # Net margin (as percentage)
        net_margin = (net_profit / revenue) if revenue > 0 else 0

        return {
            "revenue": round(revenue, 2),
            "product_cost": round(product_cost, 2),
            "amazon_fees": round(amazon_fees, 2),
            "ppc_cost": round(ppc_cost, 2),
            "total_costs": round(total_costs, 2),
            "net_profit": round(net_profit, 2),
            "net_margin_percent": round(net_margin, 4),
            "net_margin_display": f"{net_margin * 100:.1f}%",
        }

    def check_margin_requirement(self, forecast: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if forecast meets margin requirements.

        Business Rule: Net margin must be >= 10% in Growth and Mature phases.

        Args:
            forecast: 3-phase forecast with economics

        Returns:
            Dictionary with margin check results
        """
        results = {"passes": True, "phases": {}, "failed_phases": []}

        # Check each phase
        for phase_name, phase_data in forecast.items():
            margin = phase_data.get("net_margin_percent", 0)

            # All phases should have positive margin
            # Growth and Mature must have >= 10%
            if phase_name in [ForecastPhase.GROWTH, ForecastPhase.MATURE]:
                meets_requirement = margin >= self.constants.MIN_MARGIN_REQUIRED
            else:
                # Launch phase can have lower margin
                meets_requirement = margin >= 0

            results["phases"][phase_name] = {
                "margin": margin,
                "meets_requirement": meets_requirement,
                "required": self.constants.MIN_MARGIN_REQUIRED
                if phase_name in [ForecastPhase.GROWTH, ForecastPhase.MATURE]
                else 0,
            }

            if not meets_requirement:
                results["passes"] = False
                results["failed_phases"].append(phase_name)

        return results

    def calculate_capital_requirement(
        self, forecast: Dict[str, Any], landed_cost: float = None
    ) -> Dict[str, Any]:
        """
        Calculate capital required to launch and sustain the product.

        This estimates:
        - Initial inventory investment
        - Monthly cash flow requirement
        - Break-even timeline

        Args:
            forecast: 3-phase forecast
            landed_cost: Product cost per unit

        Returns:
            Dictionary with capital requirements
        """
        # Default landed cost
        if not landed_cost:
            # Estimate from mature phase price
            mature_price = forecast.get(ForecastPhase.MATURE, {}).get("price", 25.99)
            landed_cost = mature_price * 0.30

        # Calculate initial inventory investment
        # IMPROVEMENT: Use actual days of inventory based on forecast
        mature_units = forecast.get(ForecastPhase.MATURE, {}).get("estimated_units", 0)

        initial_inventory_units = (
            mature_units * self.constants.INITIAL_INVENTORY_MONTHS * 30
        )
        initial_investment = initial_inventory_units * landed_cost

        # Add safety stock
        safety_stock = initial_investment * self.constants.SAFETY_STOCK_PERCENT

        # Total initial capital required
        total_capital = initial_investment + safety_stock

        # Monthly ongoing requirement
        monthly_units = mature_units * 30
        monthly_cost = monthly_units * landed_cost

        return {
            "initial_investment": round(initial_investment, 2),
            "safety_stock": round(safety_stock, 2),
            "total_initial_capital": round(total_capital, 2),
            "monthly_ongoing_cost": round(monthly_cost, 2),
            "estimated_months_to_roi": None,  # IMPROVEMENT: Calculate from profit
        }

    def calculate_inventory_plan(
        self, forecast: Dict[str, Any], months: int = 24
    ) -> Dict[str, Any]:
        """
        Calculate simplified inventory plan for N months.

        Args:
            forecast: 3-phase forecast
            months: Number of months to plan (default 24)

        Returns:
            Dictionary with inventory plan
        """
        plan = []

        for month in range(1, months + 1):
            # Determine which phase we're in
            if month <= 1:
                phase = ForecastPhase.LAUNCH
            elif month <= 6:
                phase = ForecastPhase.GROWTH
            else:
                phase = ForecastPhase.MATURE

            phase_data = forecast.get(phase, {})
            daily_units = phase_data.get("estimated_units", 0)

            # Monthly units
            monthly_units = daily_units * 30

            plan.append(
                {
                    "month": month,
                    "phase": phase,
                    "estimated_units": round(monthly_units, 0),
                    "daily_average": round(daily_units, 2),
                }
            )

        return {
            "months": plan,
            "total_units_24_months": sum(m["estimated_units"] for m in plan),
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def get_economics_engine() -> EconomicsEngine:
    """Get economics engine instance."""
    return EconomicsEngine()


# Import ForecastPhase for use in margin check
from app.constants import ForecastPhase
