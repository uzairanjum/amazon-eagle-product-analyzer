# AMZ Eagle - Product Analyzer Architecture

## 1. System Overview

### Purpose
Decision engine for Amazon product opportunities that analyzes historical data to determine:
- How long to grow
- Capital required
- Profitability

### Input/Output
- **Input**: List of ASINs (Amazon product IDs)
- **Output**: Top 5 ranked products with scores, forecasts, economics, capital requirements

---

## 2. Tech Stack

| Component | Technology | Rationale |
|-----------|------------|------------|
| Language | Python 3.10+ | Great for data processing, time-series |
| Framework | FastAPI | Fast, async, automatic docs |
| Database | Supabase (PostgreSQL) | Managed SQL database |
| HTTP Client | httpx | Async HTTP requests |
| Data Processing | Pandas, NumPy | Time-series analysis |

### Alternative Considerations
- **Async**: Could use `httpx.AsyncClient` for better concurrency
- **Queue**: Could add Celery for background processing
- **Cache**: Could add Redis for caching Keepa responses

---

## 3. Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW                                   │
└─────────────────────────────────────────────────────────────────────┘

  POST /analyze (ASINs)
         │
         ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  Keepa Client                                               │
  │  • Fetch product data from Keepa API                        │
  │  • Store raw JSON                                           │
  └────────────────────────────┬────────────────────────────────┘
                                │
         ┌──────────────────────┴──────────────────────┐
         │                                             │
         ▼                                             ▼
  ┌────────────────────────┐              ┌─────────────────────────┐
  │  Time-Series Decoder   │              │ Database                │
  │  • Decode Keepa format │              │  • asin (metadata)      │
  │  • Normalize to daily  │              │  • asin_snapshot_daily  │
  │  • Calculate metrics   │              │  • opportunity_candidate│
  └───────────┬────────────┘              │  • forecast_plan        │
              │                           └─────────────────────────┘
              ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  Services Pipeline                                          │
  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
  │  │ Scoring      │ │ Forecasting  │ │ Economics            │ │
  │  │ - Demand     │ │ - Launch     │ │ - Revenue            │ │
  │  │ - BSR        │ │ - Growth     │ │ - Costs              │ │
  │  │ - Reviews    │ │ - Mature     │ │ - Margin Check (10%) │ │
  │  │ - Sellers    │ │              │ │                      │ │
  │  └──────────────┘ └──────────────┘ └──────────────────────┘ │
  └────────────────────────────┬────────────────────────────────┘
                               │
                               ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  Ranking + Output                                           │
  │  • Filter: margin >= 10%                                    │
  │  • Sort: by score                                           │
  │  • Return: Top 5                                            │
  └─────────────────────────────────────────────────────────────┘
```

---

## 4. Database Schema

### Tables

#### asin
Product metadata from Keepa.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| asin | VARCHAR(20) | Amazon product ID (unique) |
| title | VARCHAR(500) | Product title |
| category | VARCHAR(100) | Product category |
| current_price | FLOAT | Current price |
| current_bsr | INTEGER | Current Best Seller Rank |
| current_reviews | INTEGER | Current review count |
| current_rating | FLOAT | Average rating |
| current_sellers | INTEGER | Number of sellers |
| created_at | TIMESTAMP | Record creation time |

#### asin_snapshot_daily
Normalized daily time-series data.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| asin | VARCHAR(20) | Foreign key to asin |
| date | DATE | Snapshot date |
| price | FLOAT | Product price |
| bsr | INTEGER | Best Seller Rank |
| reviews | INTEGER | Review count |

#### opportunity_candidate
Scored products after analysis.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| asin | VARCHAR(20) | Foreign key to asin |
| score | FLOAT | Overall score (0-100) |
| demand_consistency | FLOAT | Demand stability |
| bsr_variability | FLOAT | BSR variation |
| review_gap | INTEGER | Review opportunity |
| seller_fragmentation | FLOAT | Competition metric |
| margin_viable | BOOLEAN | Passes 10% margin |
| created_at | TIMESTAMP | Record creation time |

#### forecast_plan
3-phase forecasts for each candidate.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| candidate_id | INTEGER | Foreign key to candidate |
| phase | VARCHAR(20) | launch/growth/mature |
| estimated_units | FLOAT | Units per day |
| price | FLOAT | Projected price |
| acos | FLOAT | Advertising cost % |
| net_margin_percent | FLOAT | Net margin % |

---

## 5. Core Components

### KeepaClient (`app/core/keepa_client.py`)
- Fetches product data from Keepa API
- Supports batch requests (up to 100 ASINs)
- Mock mode for testing without API key
- Rate limiting (1 req/sec for free tier)

### Decoder (`app/core/decoder.py`)
- Decodes Keepa's compressed time-series format
- Normalizes to daily resolution
- Calculates metrics (BSR CV, price stats, etc.)

### ScoringEngine (`app/services/scoring.py`)
Weighted scoring:
- Demand Consistency: 40%
- BSR Variability: 30%
- Review Gap: 20%
- Seller Fragmentation: 10%

### ForecastingEngine (`app/services/forecasting.py`)
3-phase model:
- **Launch** (Days 0-30): 10% of mature units
- **Growth** (Days 31-180): 50% of mature units
- **Mature** (Days 181+): 100% of mature units

### EconomicsEngine (`app/services/economics.py`)
- Calculates revenue, costs, margin
- **HARD GATE**: Rejects if margin < 10% in Growth/Mature
- Calculates capital requirements
- Generates 24-month inventory plan

---

## 6. API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /analyze | POST | Analyze ASINs → Top 5 results |
| /asins/{asin} | GET | Get single ASIN details |
| /asins | GET | List all ASINs |
| /candidates | GET | List scored candidates |
| /health | GET | Health check |

---

## 7. Business Rules

### Scoring
- Deterministic formulas (no randomness)
- Weights sum to 1.0
- Scores normalized to 0-100

### Forecasting
- Based on BSR-to-units conversion
- Growth multiplier from opportunity score
- Price adjustments per phase

### Economics
- Amazon fees: ~30% (15% referral + 15% FBA)
- Default landed cost: 30% of price
- ACOS assumptions: Launch 50%, Growth 35%, Mature 25%

### Margin Enforcement
- **HARD RULE**: Margin must be ≥ 10% in Growth and Mature phases
- Products failing this are REJECTED (not included in Top 5)

---

## 8. Rate Limiting

- Keepa free tier: 1 request/second
- Current strategy: Sequential processing with 1-second delay
- Improvement: Add Redis-based rate limiter

---

## 9. Security Considerations

- Supabase credentials in environment variables
- No hardcoded secrets
- CORS configured for development (restrict in production)
- Input validation on all endpoints

---

## 10. Scaling Considerations

### Current (V1)
- Sequential processing
- No caching
- Single-threaded

### Future Improvements
| Component | Improvement | Benefit |
|-----------|-------------|---------|
| Processing | Celery workers | Parallel processing |
| Caching | Redis | Reduce API calls |
| Database | Connection pool | Better concurrency |
| API | Rate limiting | Prevent abuse |
| Data | Incremental updates | Efficiency |

---

## 11. File Structure

```
amazon-eagle-product-analyzer/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── constants.py         # Business constants
│   ├── api/
│   │   └── routes/
│   │       ├── analyze.py  # POST /analyze
│   │       ├── asins.py    # ASIN endpoints
│   │       └── candidates.py
│   ├── core/
│   │   ├── keepa_client.py # Keepa API
│   │   ├── decoder.py      # Time-series decoder
│   │   └── exceptions.py
│   ├── db/
│   │   ├── client.py       # Supabase client
│   │   └── models.py        # Database models
│   ├── schemas/
│   │   └── request.py      # Pydantic schemas
│   └── services/
│       ├── scoring.py       # Scoring engine
│       ├── forecasting.py  # 3-phase forecast
│       └── economics.py    # Margin enforcement
├── run.py                   # Runner script
├── requirements.txt
├── .env.example
└── ARCHITECTURE.md
```

---

## 12. Testing Considerations

### Mock Mode
Set `ENABLE_MOCK_DATA=true` in .env to test without Keepa API.

### Test Coverage
- Keepa client (mock vs real)
- Decoder accuracy
- Scoring determinism
- Margin enforcement
- API responses

---

## 13. Next Steps

1. Set up Supabase with tables
2. Configure .env with credentials
3. Run `pip install -r requirements.txt`
4. Run `python run.py`
5. Test with POST /analyze

---

*Last Updated: 2026-03-05*
