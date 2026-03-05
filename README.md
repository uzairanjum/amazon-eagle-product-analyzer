# AMZ Eagle Product Analyzer

Internal Amazon Operations Platform - Product Opportunity Decision Engine

## Overview

This module analyzes Amazon product opportunities by:
- Fetching historical data from Keepa API
- Normalizing time-series data to daily resolution
- Scoring product opportunities (demand, BSR, reviews, competition)
- Generating 3-phase growth forecasts (Launch → Growth → Mature)
- Calculating economics and enforcing margin requirements (≥10%)
- Returning Top 5 ranked products with full details

## Tech Stack

- **Language**: Python 3.10+
- **Framework**: FastAPI
- **Database**: Supabase (PostgreSQL)
- **Data Processing**: Pandas, NumPy

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your:
- Supabase URL and key
- Keepa API key (optional - mock mode available)

### 3. Set Up Database

Create tables in Supabase:

```sql
-- asin table
CREATE TABLE asin (
    id SERIAL PRIMARY KEY,
    asin VARCHAR(20) UNIQUE NOT NULL,
    title VARCHAR(500),
    category VARCHAR(100),
    current_price FLOAT,
    current_bsr INTEGER,
    current_reviews INTEGER,
    current_rating FLOAT,
    current_sellers INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- asin_snapshot_daily table
CREATE TABLE asin_snapshot_daily (
    id SERIAL PRIMARY KEY,
    asin VARCHAR(20) REFERENCES asin(asin),
    date DATE NOT NULL,
    price FLOAT,
    bsr INTEGER,
    reviews INTEGER,
    UNIQUE(asin, date)
);

-- opportunity_candidate table
CREATE TABLE opportunity_candidate (
    id SERIAL PRIMARY KEY,
    asin VARCHAR(20) REFERENCES asin(asin),
    score FLOAT,
    demand_consistency FLOAT,
    bsr_variability FLOAT,
    review_gap INTEGER,
    seller_fragmentation FLOAT,
    margin_viable BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

-- forecast_plan table
CREATE TABLE forecast_plan (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES opportunity_candidate(id),
    phase VARCHAR(20),
    estimated_units FLOAT,
    price FLOAT,
    acos FLOAT,
    net_margin_percent FLOAT
);
```

### 4. Run the Server

```bash
python run.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

## API Endpoints

### POST /analyze

Analyze product opportunities:

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"asins": ["B0012345678", "B0012345679"], "limit": 5}'
```

Response includes:
- Opportunity scores
- 3-phase forecasts (Launch/Growth/Mature)
- Economics (revenue, costs, margins)
- Capital requirements
- 24-month inventory plan

### GET /asins/{asin}

Get single ASIN details.

### GET /candidates

List scored candidates.

### GET /health

Health check endpoint.

## Testing with Mock Data

To test without Keepa API, enable mock mode:

```env
ENABLE_MOCK_DATA=true
```

This will generate realistic mock data for any ASIN.

## Project Structure

```
app/
├── main.py              # FastAPI application
├── config.py            # Configuration
├── constants.py         # Business constants
├── api/routes/          # API endpoints
├── core/                # Keepa client, decoder
├── db/                  # Supabase client, models
├── schemas/             # Pydantic schemas
└── services/            # Scoring, forecasting, economics
```

## Business Logic

### Scoring Weights
- Demand Consistency: 40%
- BSR Variability: 30%
- Review Gap: 20%
- Seller Fragmentation: 10%

### Margin Enforcement
- **HARD RULE**: Net margin must be ≥ 10% in Growth and Mature phases
- Products failing this are REJECTED

### Forecasting Phases
- **Launch**: Days 0-30 (10% of mature units)
- **Growth**: Days 31-180 (50% of mature units)
- **Mature**: Days 181+ (100% of mature units)

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| SUPABASE_URL | Supabase project URL | - |
| SUPABASE_KEY | Supabase API key | - |
| KEEPA_API_KEY | Keepa API key | - |
| KEEPA_DOMAIN | Amazon domain (1=com) | 1 |
| ENABLE_MOCK_DATA | Use mock data | false |
| KEEPA_REQUEST_DELAY | Delay between requests | 1.0 |

## License

Internal use only.
