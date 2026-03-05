"""
Analyze Route
=============

Main endpoint for analyzing product opportunities.

POST /analyze
- Input: List of ASINs
- Process: Fetch data → Decode → Score → Forecast → Calculate Economics
- Output: Top 5 ranked products with full details

IMPROVEMENT OPPORTUNITIES:
1. Add background task processing (Celery)
2. Add progress tracking
3. Add caching of results
4. Implement pagination for large requests
5. Add request validation
6. Add rate limiting
"""

from typing import List
from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from app.schemas.request import AnalyzeRequest, AnalyzeResponse, CandidateResponse
from app.core import get_keepa_client, KeepaAPIError
from app.core.decoder import get_decoder
from app.services import (
    get_scoring_engine,
    get_forecasting_engine,
    get_economics_engine,
)
from app.constants import ForecastPhase
from app.db import (
    upsert_asin,
    upsert_snapshots,
    upsert_candidate,
    create_forecasts,
)

router = APIRouter(prefix="/analyze", tags=["analyze"])


@router.post("", response_model=AnalyzeResponse)
async def analyze_products(request: AnalyzeRequest):
    """
    Analyze product opportunities.

    This endpoint:
    1. Fetches data from Keepa for each ASIN
    2. Decodes and normalizes time-series data
    3. Calculates opportunity scores
    4. Generates 3-phase forecasts
    5. Calculates economics and enforces margin requirements
    6. Returns top N candidates ranked by score

    Args:
        request: List of ASINs and parameters

    Returns:
        Top ranked candidates with scores, forecasts, and economics
    """
    results = []
    passed_count = 0

    # Initialize services
    keepa_client = get_keepa_client()
    decoder = get_decoder()
    scoring_engine = get_scoring_engine()
    forecasting_engine = get_forecasting_engine()
    economics_engine = get_economics_engine()

    try:
        # Process each ASIN
        for asin in request.asins:
            try:
                # Step 1: Fetch data from Keepa
                product_data = keepa_client.get_product(asin)

                # Step 2: Decode and normalize
                decoded = decoder.decode_product(product_data)
                daily_snapshots = decoder.normalize_to_daily(decoded)

                # Step 3: Calculate metrics
                metrics = decoder.calculate_metrics(daily_snapshots)

                # Step 4: Store ASIN metadata
                asin_data = {
                    "asin": asin,
                    "title": decoded.get("title"),
                    "category": decoded.get("category"),
                    "current_price": decoded.get("current", {}).get("price"),
                    "current_bsr": decoded.get("current", {}).get("bsr"),
                    "current_reviews": decoded.get("current", {}).get("reviews"),
                    "current_rating": decoded.get("current", {}).get("rating"),
                    "current_sellers": decoded.get("current", {}).get("sellers"),
                }
                upsert_asin(asin_data)

                # Step 5: Store daily snapshots
                if daily_snapshots:
                    snapshots_data = [
                        {
                            "asin": s["asin"],
                            "date": s["date"].isoformat()
                            if hasattr(s["date"], "isoformat")
                            else s["date"],
                            "price": s.get("price"),
                            "bsr": s.get("bsr"),
                            "reviews": s.get("reviews"),
                        }
                        for s in daily_snapshots
                    ]
                    upsert_snapshots(snapshots_data)

                # Step 5: Calculate score
                score_result = scoring_engine.calculate_score(
                    metrics, decoded.get("current")
                )

                # Step 6: Generate forecast
                current_price = decoded.get("current", {}).get("price")
                forecast = forecasting_engine.generate_forecast(
                    metrics=metrics,
                    score=score_result["score"],
                    current_price=current_price,
                )

                # Step 7: Calculate economics
                economics = economics_engine.calculate_economics(forecast)

                # Step 8: Check margin requirement (HARD GATE)
                margin_check = economics_engine.check_margin_requirement(economics)
                margin_viable = margin_check["passes"]

                if not margin_viable:
                    # Product failed margin requirement - skip it
                    # Still store for reference but mark as failed
                    pass
                else:
                    passed_count += 1

                # Step 9: Calculate capital requirements
                capital = economics_engine.calculate_capital_requirement(forecast)

                # Step 10: Calculate inventory plan
                inventory = economics_engine.calculate_inventory_plan(forecast)

                # Store candidate
                candidate_data = {
                    "asin": asin,
                    "score": score_result["score"],
                    "demand_consistency": score_result["demand_consistency"],
                    "bsr_variability": score_result["bsr_variability"],
                    "review_gap": score_result["review_gap"],
                    "seller_fragmentation": score_result["seller_fragmentation"],
                    "margin_viable": margin_viable,
                }
                upsert_candidate(candidate_data)

                # Build result
                result = _build_candidate_result(
                    rank=len(results) + 1,
                    asin=asin,
                    decoded=decoded,
                    score_result=score_result,
                    forecast=forecast,
                    economics=economics,
                    capital=capital,
                    inventory=inventory,
                    margin_viable=margin_viable,
                )

                results.append(result)

            except KeepaAPIError as e:
                # Log error but continue with other ASINs
                print(f"Keepa API error for {asin}: {str(e)}")
                continue
            except Exception as e:
                print(f"Error processing {asin}: {str(e)}")
                continue

        # Sort by score and take top N
        results.sort(key=lambda x: x.score, reverse=True)
        top_candidates = results[: request.limit]

        # Re-rank
        for i, candidate in enumerate(top_candidates):
            candidate.rank = i + 1

        return AnalyzeResponse(
            total_analyzed=len(request.asins),
            passed_margin_check=passed_count,
            candidates=top_candidates,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )


def _build_candidate_result(
    rank: int,
    asin: str,
    decoded: dict,
    score_result: dict,
    forecast: dict,
    economics: dict,
    capital: dict,
    inventory: dict,
    margin_viable: bool,
) -> CandidateResponse:
    """Build candidate response object."""

    current = decoded.get("current", {})

    return CandidateResponse(
        rank=rank,
        asin=asin,
        title=decoded.get("title"),
        category=decoded.get("category"),
        score=score_result["score"],
        demand_consistency=score_result["demand_consistency"],
        bsr_variability=score_result["bsr_variability"],
        review_gap=score_result["review_gap"],
        seller_fragmentation=score_result["seller_fragmentation"],
        margin_viable=margin_viable,
        launch=forecast.get(ForecastPhase.LAUNCH),
        growth=forecast.get(ForecastPhase.GROWTH),
        mature=forecast.get(ForecastPhase.MATURE),
        economics_launch=economics.get(ForecastPhase.LAUNCH),
        economics_growth=economics.get(ForecastPhase.GROWTH),
        economics_mature=economics.get(ForecastPhase.MATURE),
        capital_requirement=capital,
        inventory_plan=inventory,
    )
