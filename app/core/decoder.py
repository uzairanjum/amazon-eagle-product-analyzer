"""
Time-Series Decoder
===================

This module decodes and normalizes Keepa's compressed time-series data
into clean daily snapshots.

Keepa stores historical data in compressed arrays:
- timestamps: Unix timestamps (milliseconds)
- values: The actual data points

The key challenge is that Keepa returns data at varying intervals
(hourly, daily, weekly), so we need to normalize to daily resolution.

IMPROVEMENT OPPORTUNITIES:
1. Add interpolation for missing data points
2. Implement more sophisticated aggregation (weighted averages)
3. Add outlier detection and handling
4. Support for different aggregation methods (mean, median, etc.)
5. Add data quality scoring
6. Implement incremental updates (only fetch new data)
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np


class KeepaDecoder:
    """
    Decoder for Keepa time-series data.

    Keepa returns data in a specific format that needs to be decoded
    and normalized to daily resolution.
    """

    def __init__(self):
        """Initialize decoder."""
        pass

    def decode_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode raw Keepa product data into usable format.

        Args:
            product_data: Raw product data from Keepa API

        Returns:
            Dictionary with decoded time-series data
        """
        return {
            "asin": product_data.get("asin"),
            "title": product_data.get("title"),
            "category": product_data.get("productType"),
            "current": {
                "price": product_data.get("price"),
                "bsr": product_data.get("bsr"),
                "reviews": product_data.get("reviews"),
                "rating": product_data.get("rating"),
                "sellers": product_data.get("offerCount"),
            },
            "history": {
                "price": self._decode_time_series(
                    product_data.get("priceHistory", []),
                    product_data.get("priceHistoryValues", []),
                ),
                "bsr": self._decode_time_series(
                    product_data.get("salesRankHistory", []),
                    product_data.get("salesRankValues", []),
                ),
                "reviews": self._decode_time_series(
                    product_data.get("reviewCountHistory", []),
                    product_data.get("reviewCountValues", []),
                ),
                "sellers": self._decode_time_series(
                    product_data.get("offerHistory", []),
                    product_data.get("offerHistoryValues", []),
                ),
            },
        }

    def _decode_time_series(
        self, timestamps: List[int], values: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Decode Keepa time-series format to list of date-value pairs.

        Keepa format: timestamps are Unix timestamps in milliseconds

        Args:
            timestamps: List of Unix timestamps (milliseconds)
            values: List of values

        Returns:
            List of {"date": datetime, "value": any} dictionaries
        """
        if not timestamps or not values:
            return []

        result = []
        for ts, val in zip(timestamps, values):
            # Convert milliseconds to seconds
            dt = datetime.fromtimestamp(ts / 1000)
            result.append({"date": dt.date(), "value": val})

        return result

    def normalize_to_daily(self, decoded_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Normalize all time-series to daily resolution.

        This takes the decoded data and produces a list of daily snapshots
        with interpolated values where needed.

        Args:
            decoded_data: Decoded product data from decode_product()

        Returns:
            List of daily snapshots with all metrics
        """
        # Get all unique dates from all time-series
        all_dates = set()
        for metric, history in decoded_data["history"].items():
            for point in history:
                all_dates.add(point["date"])

        # Sort dates
        sorted_dates = sorted(all_dates)

        # Create daily snapshots
        daily_snapshots = []

        for current_date in sorted_dates:
            snapshot = {
                "asin": decoded_data["asin"],
                "date": current_date,
            }

            # Get value for each metric (or interpolate)
            for metric, history in decoded_data["history"].items():
                value = self._get_value_for_date(history, current_date)
                # Map to database field names
                field_map = {
                    "price": "price",
                    "bsr": "bsr",
                    "reviews": "reviews",
                    "sellers": "sellers",
                }
                if metric in field_map:
                    snapshot[field_map[metric]] = value

            daily_snapshots.append(snapshot)

        return daily_snapshots

    def _get_value_for_date(
        self, history: List[Dict[str, Any]], target_date: date
    ) -> Optional[Any]:
        """
        Get value for a specific date from history.

        Uses linear interpolation for missing dates.

        IMPROVEMENT: Add more sophisticated interpolation methods.

        Args:
            history: List of {"date": date, "value": any}
            target_date: Date to get value for

        Returns:
            Value at target date or None
        """
        if not history:
            return None

        # Find exact match
        for point in history:
            if point["date"] == target_date:
                return point["value"]

        # No exact match - return None (or could implement interpolation)
        # IMPROVEMENT: Add interpolation here
        return None

    def process_product(self, product_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Full pipeline: decode and normalize product data.

        This is the main entry point for processing Keepa data.

        Args:
            product_data: Raw product data from Keepa API

        Returns:
            List of daily snapshots ready for database storage
        """
        # Step 1: Decode Keepa format
        decoded = self.decode_product(product_data)

        # Step 2: Normalize to daily resolution
        daily_snapshots = self.normalize_to_daily(decoded)

        return daily_snapshots

    def calculate_metrics(self, snapshots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate key metrics from daily snapshots.

        These metrics are used for scoring and forecasting.

        Args:
            snapshots: List of daily snapshots

        Returns:
            Dictionary of calculated metrics
        """
        if not snapshots:
            return {}

        # Convert to DataFrame for easier analysis
        # IMPROVEMENT: Use pandas more effectively
        df = pd.DataFrame(snapshots)

        metrics = {}

        # Price metrics
        if "price" in df.columns:
            prices = df["price"].dropna()
            if len(prices) > 0:
                metrics["price_current"] = prices.iloc[-1]
                metrics["price_mean"] = prices.mean()
                metrics["price_std"] = prices.std()
                metrics["price_min"] = prices.min()
                metrics["price_max"] = prices.max()

        # BSR metrics
        if "bsr" in df.columns:
            bsr = df["bsr"].dropna()
            if len(bsr) > 0:
                metrics["bsr_current"] = bsr.iloc[-1]
                metrics["bsr_mean"] = bsr.mean()
                metrics["bsr_std"] = bsr.std()
                metrics["bsr_min"] = bsr.min()
                metrics["bsr_max"] = bsr.max()
                # Coefficient of variation (lower = more stable)
                metrics["bsr_cv"] = bsr.std() / bsr.mean() if bsr.mean() > 0 else 0

        # Review metrics
        if "reviews" in df.columns:
            reviews = df["reviews"].dropna()
            if len(reviews) > 0:
                metrics["reviews_current"] = reviews.iloc[-1]
                # Review growth rate
                if len(reviews) > 1:
                    first_valid = reviews.iloc[0]
                    last_valid = reviews.iloc[-1]
                    if first_valid > 0:
                        metrics["review_growth_rate"] = (
                            last_valid - first_valid
                        ) / first_valid
                    else:
                        metrics["review_growth_rate"] = 0

        # Seller metrics
        if "sellers" in df.columns:
            sellers = df["sellers"].dropna()
            if len(sellers) > 0:
                metrics["sellers_current"] = sellers.iloc[-1]
                metrics["sellers_mean"] = sellers.mean()
                metrics["sellers_std"] = sellers.std()

        # Demand consistency (based on BSR stability)
        if "bsr_cv" in metrics:
            # Lower CV = more consistent demand
            metrics["demand_consistency"] = max(0, 100 - (metrics["bsr_cv"] * 100))

        return metrics


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def get_decoder() -> KeepaDecoder:
    """Get decoder instance."""
    return KeepaDecoder()
