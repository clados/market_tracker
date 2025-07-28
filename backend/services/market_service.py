from models import Market, PriceHistory, MarketChange
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional
from datetime import datetime, timedelta
import json

class MarketService:
    def __init__(self):
        pass
    
    def get_markets(self, db: Session, limit: int = 100, offset: int = 0,
                    status: Optional[str] = None, min_liquidity: Optional[int] = None,
                    category: Optional[str] = None, search: Optional[str] = None) -> List[Market]:
        """Get markets with filtering"""
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
        
        return query.offset(offset).limit(limit).all()
    
    def get_market_detail(self, db: Session, ticker: str) -> Optional[Market]:
        """Get detailed market information"""
        return db.query(Market).filter(Market.ticker == ticker).first()
    
    def get_market_history(self, db: Session, ticker: str, days: int = 30) -> List[PriceHistory]:
        """Get market price history"""
        market = self.get_market_detail(db, ticker)
        if not market:
            return []
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return db.query(PriceHistory).filter(
            and_(
                PriceHistory.market_id == market.id,
                PriceHistory.timestamp >= cutoff_date
            )
        ).order_by(PriceHistory.timestamp.asc()).all()
    
    def get_categories(self, db: Session) -> List[str]:
        """Get available market categories"""
        categories = db.query(Market.category).distinct().all()
        return [cat[0] for cat in categories if cat[0]]
    
    def calculate_market_changes(self, db: Session, market: Market, 
                               change_windows: List[int] = [1, 7, 30, 90]) -> None:
        """Calculate and store percentage changes for different time windows"""
        for window_days in change_windows:
            cutoff_date = datetime.utcnow() - timedelta(days=window_days)
            
            # Get price history for the window
            history = db.query(PriceHistory).filter(
                and_(
                    PriceHistory.market_id == market.id,
                    PriceHistory.timestamp >= cutoff_date
                )
            ).order_by(PriceHistory.timestamp.asc()).all()
            
            if not history:
                continue
            
            # Calculate price changes
            prices = [h.price for h in history]
            min_price = min(prices)
            max_price = max(prices)
            current_price = market.current_price
            
            # Calculate the most dramatic change
            change_from_min = abs(current_price - min_price)
            change_from_max = abs(current_price - max_price)
            price_change = max(change_from_min, change_from_max)
            
            # Calculate percentage change
            change_percentage = (price_change / current_price) * 100 if current_price > 0 else 0
            
            # Update or create market change record
            existing_change = db.query(MarketChange).filter(
                and_(
                    MarketChange.market_id == market.id,
                    MarketChange.change_window_days == window_days
                )
            ).first()
            
            if existing_change:
                existing_change.probability_change = price_change
                existing_change.min_probability = min_price
                existing_change.max_probability = max_price
                existing_change.change_percentage = change_percentage
                existing_change.calculated_at = datetime.utcnow()
            else:
                new_change = MarketChange(
                    market_id=market.id,
                    change_window_days=window_days,
                    probability_change=price_change,
                    min_probability=min_price,
                    max_probability=max_price,
                    change_percentage=change_percentage
                )
                db.add(new_change)
    
    def update_market_data(self, db: Session, market_data: dict) -> Market:
        """Update or create market data"""
        ticker = market_data["ticker"]
        existing_market = db.query(Market).filter(Market.ticker == ticker).first()
        
        if existing_market:
            # Update existing market
            for key, value in market_data.items():
                if hasattr(existing_market, key):
                    setattr(existing_market, key, value)
            existing_market.updated_at = datetime.utcnow()
            market = existing_market
        else:
            # Create new market
            market = Market(**market_data)
            db.add(market)
        
        db.commit()
        db.refresh(market)
        return market
    
    def update_price_history(self, db: Session, market: Market, history_data: List[dict]) -> None:
        """Update price history for a market"""
        # Clear existing history
        db.query(PriceHistory).filter(PriceHistory.market_id == market.id).delete()
        
        # Add new history
        for data in history_data:
            price_history = PriceHistory(
                market_id=market.id,
                timestamp=data["timestamp"],
                price=data["price"],
                volume=data.get("volume", 0)
            )
            db.add(price_history)
        
        db.commit()
    
    async def refresh_market_data(self, db: Session, kalshi_service) -> None:
        """Refresh all market data from Kalshi API"""
        try:
            # Get markets from Kalshi API
            kalshi_response = kalshi_service.get_markets(limit=1000, status="open")
            all_markets_data = kalshi_response.get("markets", [])
            
            # Filter for active markets only
            markets_data = [market for market in all_markets_data if market.get("status") == "active"]
            
            for market_data in markets_data:
                # Transform Kalshi data to our format
                transformed_data = {
                    "ticker": market_data["ticker"],
                    "series_ticker": market_data.get("event_ticker"),  # Use event_ticker from Kalshi API
                    "title": market_data["title"],
                    "subtitle": market_data.get("subtitle"),
                    "category": market_data.get("category", "Other"),
                    "status": market_data.get("status", "active"),
                    "current_price": market_data.get("last_price", 0) / 100,  # Convert cents to probability
                    "volume_24h": market_data.get("volume_24h", 0),
                    "liquidity": market_data.get("liquidity", 0),
                    "open_time": datetime.fromisoformat(market_data["open_time"].rstrip("Z")) if market_data.get("open_time") else None,
                    "close_time": datetime.fromisoformat(market_data["close_time"].rstrip("Z")) if market_data.get("close_time") else None,
                    "expiration_time": datetime.fromisoformat(market_data["expiration_time"].rstrip("Z")) if market_data.get("expiration_time") else None,
                    "resolution_rules": market_data.get("resolution_rules"),
                    "tags": json.dumps(market_data.get("tags", []))
                }
                
                # Update market data
                market = self.update_market_data(db, transformed_data)
                
                # Get and update price history
                try:
                    history_data = kalshi_service.get_market_history(market.ticker)
                    self.update_price_history(db, market, history_data)
                    
                    # Calculate percentage changes
                    self.calculate_market_changes(db, market)
                except Exception as e:
                    print(f"Failed to update history for {market.ticker}: {str(e)}")
                    continue
            
            db.commit()
            print(f"Successfully refreshed {len(markets_data)} markets")
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to refresh market data: {str(e)}") 