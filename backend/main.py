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

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Kalshi Market Tracker API", "status": "running"}

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
    min_change: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Get markets with precomputed percentage changes"""
    try:
        # First get all markets that match basic filters
        query = db.query(Market)
        if status:
            query = query.filter(Market.status == status)
        if min_liquidity is not None:
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
        
        # Filter out markets with less than 2 price history points
        # This ensures we only show markets that can display meaningful charts
        markets_with_history = db.query(Market.id).join(PriceHistory).group_by(Market.id).having(
            func.count(PriceHistory.id) >= 2
        ).subquery()
        query = query.filter(Market.id.in_(markets_with_history))
        
        # Get filtered market ids
        market_ids = [m.id for m in query.with_entities(Market.id).all()]
        
        # Apply min_change filter if specified
        if min_change is not None and market_ids:
            markets_with_change = db.query(MarketChange.market_id).filter(
                MarketChange.market_id.in_(market_ids),
                func.abs(MarketChange.price_change) >= min_change
            ).distinct().all()
            filtered_market_ids = [m[0] for m in markets_with_change]
        else:
            filtered_market_ids = market_ids
        
        # Get the actual market objects for the filtered IDs
        if filtered_market_ids:
            markets = db.query(Market).filter(Market.id.in_(filtered_market_ids)).offset(offset).limit(limit).all()
        else:
            markets = []
        
        return MarketListResponse(
            markets=markets,
            total=len(filtered_market_ids),
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
    """Get aggregate market stats with filter-based metrics"""
    try:
        # 1. Total Active Markets - always the total number of active markets in DB (unfiltered)
        total_active = db.query(Market).filter(Market.status == 'active').count()
        
        # 2. High Volume Markets - count of markets with volume >= min_liquidity filter
        high_volume_query = db.query(Market).filter(Market.status == 'active')
        if min_liquidity and min_liquidity > 0:
            high_volume_query = high_volume_query.filter(Market.volume_24h >= min_liquidity)
        else:
            # If no min_liquidity filter, show markets with volume >= $10K
            high_volume_query = high_volume_query.filter(Market.volume_24h >= 10000)
        high_volume_count = high_volume_query.count()
        
        # 3. Big Movers - count of markets with price change >= min_change filter
        big_movers_count = 0
        if min_change and min_change > 0:
            # Count markets that meet the min_change criteria (absolute value)
            markets_with_change = db.query(MarketChange.market_id).filter(
                func.abs(MarketChange.price_change) >= min_change
            ).distinct().all()
            big_movers_count = len(markets_with_change)
        else:
            # If no min_change filter, show markets with >= 10% change (absolute value)
            markets_with_change = db.query(MarketChange.market_id).filter(
                func.abs(MarketChange.price_change) >= 0.1  # 10% change
            ).distinct().all()
            big_movers_count = len(markets_with_change)
        
        return {
            "total_active": total_active,
            "high_volume": high_volume_count,
            "big_movers": big_movers_count
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

@app.get("/api/markets/{ticker}/changes")
async def get_market_changes(
    ticker: str,
    db: Session = Depends(get_db)
):
    """Get precomputed market changes for different time windows"""
    try:
        market = market_service.get_market_detail(db=db, ticker=ticker)
        if not market:
            raise HTTPException(status_code=404, detail="Market not found")
        
        # Get all market changes for this market
        changes = db.query(MarketChange).filter(
            MarketChange.market_id == market.id
        ).all()
        
        # Transform to response format
        changes_data = []
        for change in changes:
            changes_data.append({
                "change_window_days": change.change_window_days,
                "price_change": change.price_change,
                "min_price": change.min_price,
                "max_price": change.max_price,
                "change_percentage": change.change_percentage,
                "calculated_at": change.calculated_at.isoformat() if change.calculated_at else None
            })
        
        return {"changes": changes_data}
    except HTTPException:
        raise
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