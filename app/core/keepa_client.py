"""
Keepa API Client
================

This module handles all interactions with the Keepa API.
Keepa provides historical Amazon product data including:
- Price history
- Sales rank (BSR) history
- Review count history
- Seller/offer count history

IMPROVEMENT OPPORTUNITIES:
1. Add request retry logic with exponential backoff
2. Implement proper rate limiting with token bucket
3. Add caching layer to reduce API calls
4. Support for batch requests (Keepa supports up to 100 ASINs)
5. Add data validation before storing
6. Implement proper error handling for different API errors
7. Add support for more Keepa endpoints (category search, etc.)
"""

import asyncio
import time
from typing import Optional, List, Dict, Any
import httpx

from app.config import get_settings
from app.constants import KeepaConstants


class KeepaAPIError(Exception):
    """Exception raised for Keepa API errors."""

    pass


class KeepaClient:
    """
    Client for interacting with Keepa API.

    This client handles authentication, request building, and response parsing.

    IMPROVEMENT: Consider using httpx.AsyncClient for better concurrency.
    """

    BASE_URL = "https://api.keepa.com"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Keepa client.

        Args:
            api_key: Keepa API key. If None, uses settings from config.
        """
        settings = get_settings()
        self.api_key = api_key or settings.keepa_api_key
        self.domain = settings.keepa_domain
        self.request_delay = settings.keepa_request_delay

        # Enable mock mode for testing
        self.mock_mode = settings.enable_mock_data

        # HTTP client - could be async for better performance
        # IMPROVEMENT: Use httpx.AsyncClient for async operations
        self.client = httpx.Client(timeout=30.0)

    def _build_url(self, endpoint: str) -> str:
        """Build full URL for Keepa API endpoint."""
        return f"{self.BASE_URL}/{endpoint}"

    def _get_headers(self) -> dict:
        """Get request headers with authentication."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def get_product(
        self,
        asin: str,
        history: int = KeepaConstants.DEFAULT_HISTORY_DAYS,
        domain: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Fetch product data from Keepa API.

        Args:
            asin: Amazon Standard Identification Number
            history: Number of days of history to fetch (default 730 = 2 years)
            domain: Amazon domain (1=com, 2=co.uk, etc.). Uses setting if None.

        Returns:
            Product data including current values and historical data

        Raises:
            KeepaAPIError: If API returns an error
        """
        if self.mock_mode:
            return self._get_mock_product(asin)

        domain = domain or self.domain

        # Build API request URL
        # See: https://keepa.com/#!api for API documentation
        url = f"{self.BASE_URL}/product/{domain}/{asin}"

        params = {
            "domain": domain,
            "history": history,
            "offers": 20,  # Include offer history
        }

        # Rate limiting - delay between requests
        # IMPROVEMENT: Implement proper token bucket for rate limiting
        time.sleep(self.request_delay)

        try:
            response = self.client.get(url, params=params, headers=self._get_headers())

            if response.status_code == 200:
                data = response.json()

                # Keepa returns data in a specific format
                # See Keepa API docs for response structure
                if "products" in data and len(data["products"]) > 0:
                    return data["products"][0]
                else:
                    raise KeepaAPIError(f"No product found for ASIN: {asin}")

            elif response.status_code == 401:
                raise KeepaAPIError("Invalid API key")
            elif response.status_code == 429:
                raise KeepaAPIError("Rate limit exceeded")
            else:
                raise KeepaAPIError(f"API error: {response.status_code}")

        except httpx.RequestError as e:
            raise KeepaAPIError(f"Request failed: {str(e)}")

    def get_products_batch(
        self, asins: List[str], history: int = KeepaConstants.DEFAULT_HISTORY_DAYS
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple products in a single request.

        Keepa supports batch requests up to 100 ASINs.

        Args:
            asins: List of Amazon product IDs
            history: Number of days of history

        Returns:
            List of product data dictionaries
        """
        if self.mock_mode:
            return [self._get_mock_product(asin) for asin in asins]

        # Join ASINs with comma (Keepa format)
        asin_string = ",".join(asins)

        url = f"{self.BASE_URL}/product/{self.domain}/{asin_string}"

        params = {
            "domain": self.domain,
            "history": history,
            "offers": 20,
        }

        time.sleep(self.request_delay)

        try:
            response = self.client.get(url, params=params, headers=self._get_headers())

            if response.status_code == 200:
                data = response.json()
                return data.get("products", [])
            else:
                raise KeepaAPIError(f"Batch request failed: {response.status_code}")

        except httpx.RequestError as e:
            raise KeepaAPIError(f"Request failed: {str(e)}")

    def _get_mock_product(self, asin: str) -> Dict[str, Any]:
        """
        Generate mock product data for testing.

        This allows testing without a real Keepa API key.

        IMPROVEMENT: Add more sophisticated mock data generation
        based on realistic patterns.
        """
        import random
        from datetime import datetime, timedelta

        # Generate mock historical data
        days = KeepaConstants.DEFAULT_HISTORY_DAYS
        base_date = datetime.now()

        # Generate timestamps (days ago from now)
        timestamps = []
        prices = []
        bsr_values = []
        reviews = []
        sellers = []

        base_price = random.uniform(20, 100)
        base_bsr = random.randint(1000, 50000)
        base_reviews = random.randint(50, 5000)
        base_sellers = random.randint(1, 20)

        for i in range(0, days, 7):  # Weekly data points
            date = base_date - timedelta(days=i)
            timestamp = int(date.timestamp() * 1000)
            timestamps.append(timestamp)

            # Add some variation
            price_variation = random.uniform(0.85, 1.15)
            prices.append(round(base_price * price_variation, 2))

            bsr_variation = random.uniform(0.7, 1.3)
            bsr_values.append(int(base_bsr * bsr_variation))

            # Reviews only increase over time
            reviews.append(base_reviews - int(i / 10))

            sellers.append(base_sellers + random.randint(-3, 3))

        # Reverse to get chronological order
        timestamps.reverse()
        prices.reverse()
        bsr_values.reverse()
        reviews.reverse()
        sellers.reverse()

        return {
            "asin": asin,
            "title": f"Mock Product {asin}",
            "productType": random.choice(["Kitchen", "Electronics", "Home", "Sports"]),
            "price": prices[-1] if prices else base_price,
            "bsr": bsr_values[-1] if bsr_values else base_bsr,
            "reviews": reviews[-1] if reviews else base_reviews,
            "rating": round(random.uniform(3.5, 4.8), 1),
            "offerCount": sellers[-1] if sellers else base_sellers,
            # Historical data arrays (Keepa format)
            "priceHistory": timestamps,
            "priceHistoryValues": prices,
            "salesRankHistory": timestamps,
            "salesRankValues": bsr_values,
            "reviewCountHistory": timestamps,
            "reviewCountValues": reviews,
            "offerHistory": timestamps,
            "offerHistoryValues": sellers,
        }

    def close(self):
        """Close HTTP client."""
        self.client.close()


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def get_keepa_client() -> KeepaClient:
    """
    Get Keepa client instance.

    This is the recommended way to get a Keepa client.
    """
    return KeepaClient()
