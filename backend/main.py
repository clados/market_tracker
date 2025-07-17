import sys
import os

# Add shared package to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, or_

from database import get_db, get_engine
from models import Base, Market, PriceHistory, MarketChange
from schemas import MarketResponse, MarketListResponse, PriceHistoryResponse
from services.market_service import MarketService

app = FastAPI(
    title="Kalshi Market Tracker API",
    description="API for accessing precomputed Kalshi market data and percentage changes",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
market_service = MarketService()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/markets", response_model=MarketListResponse)
async def get_markets(
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = "active",
    min_liquidity: Optional[int] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get markets with precomputed percentage changes"""
    try:
        markets = market_service.get_markets(
            db=db,
            limit=limit,
            offset=offset,
            status=status,
            min_liquidity=min_liquidity,
            category=category,
            search=search
        )
        
        return MarketListResponse(
            markets=markets,
            total=len(markets),
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/markets/stats")
async def get_market_stats(
    status: Optional[str] = None,
    min_liquidity: Optional[int] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    min_change: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Get aggregate market stats: total, avg_volume, big movers, with filters"""
    try:
        query = db.query(Market)
        if status:
            query = query.filter(Market.status == status)
        if min_liquidity:
            query = query.filter(Market.liquidity >= min_liquidity)
        if category:
            query = query.filter(Market.category == category)
        if search:
            search_filter = or_(
                Market.title.ilike(f"%{search}%"),
                Market.subtitle.ilike(f"%{search}%"),
                Market.ticker.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Get filtered market ids
        market_ids = [m.id for m in query.with_entities(Market.id).all()]
        
        # Apply min_change filter to get markets that meet the price change criteria
        if min_change is not None and market_ids:
            markets_with_change = db.query(MarketChange.market_id).filter(
                MarketChange.market_id.in_(market_ids),
                MarketChange.price_change >= min_change
            ).distinct().all()
            filtered_market_ids = [m[0] for m in markets_with_change]
        else:
            filtered_market_ids = market_ids
        
        total = len(filtered_market_ids)
        avg_volume = 0
        if filtered_market_ids:
            avg_volume = db.query(func.avg(Market.volume_24h)).filter(Market.id.in_(filtered_market_ids)).scalar() or 0
        
        # Big movers: price change >= min_change in any window
        big_movers = 0
        if filtered_market_ids:
            if min_change is not None:
                big_movers = db.query(MarketChange.market_id).filter(
                    MarketChange.market_id.in_(filtered_market_ids),
                    MarketChange.price_change >= min_change
                ).distinct().count()
            else:
                # Default: price change > 0.1
                big_movers = db.query(MarketChange.market_id).filter(
                    MarketChange.market_id.in_(filtered_market_ids),
                    MarketChange.price_change > 0.1
                ).distinct().count()
        
        return {
            "total": total,
            "avg_volume": int(avg_volume),
            "big_movers": big_movers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/markets/{ticker}", response_model=MarketResponse)
async def get_market_detail(
    ticker: str,
    db: Session = Depends(get_db)
):
    """Get detailed market information with price history"""
    try:
        market = market_service.get_market_detail(db=db, ticker=ticker)
        if not market:
            raise HTTPException(status_code=404, detail="Market not found")
        
        return market
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/markets/{ticker}/history", response_model=List[PriceHistoryResponse])
async def get_market_history(
    ticker: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get market price history"""
    try:
        history = market_service.get_market_history(
            db=db,
            ticker=ticker,
            days=days
        )
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories")
async def get_categories(db: Session = Depends(get_db)):
    """Get available market categories"""
    try:
        categories = market_service.get_categories(db=db)
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/refresh")
async def refresh_market_data(db: Session = Depends(get_db)):
    """Manually trigger market data refresh (admin only)"""
    try:
        # This would typically require authentication
        await market_service.refresh_market_data(db=db)
        return {"message": "Market data refresh initiated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 