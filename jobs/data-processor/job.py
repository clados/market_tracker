#!/usr/bin/env python3
"""
Scheduled job to fetch Kalshi market data and store it in the database.
This job runs every 6 hours to keep the database updated with fresh market data.
"""

import sys
import os

# Add shared package to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_db, get_engine
from models import Base, Market, PriceHistory, MarketChange
from kalshi_service import KalshiService
from datetime import datetime, timedelta
import json
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local', override=False)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_market_data(db, market_data):
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

def update_price_history(db, market, history_data):
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

def calculate_market_changes(db, market, change_windows=[1, 7, 30, 90]):
    """Calculate and store percentage changes for different time windows"""
    for window_days in change_windows:
        cutoff_date = datetime.utcnow() - timedelta(days=window_days)
        
        # Get price history for the window
        history = db.query(PriceHistory).filter(
            PriceHistory.market_id == market.id,
            PriceHistory.timestamp >= cutoff_date
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
            MarketChange.market_id == market.id,
            MarketChange.change_window_days == window_days
        ).first()
        
        if existing_change:
            existing_change.price_change = price_change
            existing_change.min_price = min_price
            existing_change.max_price = max_price
            existing_change.change_percentage = change_percentage
            existing_change.calculated_at = datetime.utcnow()
        else:
            new_change = MarketChange(
                market_id=market.id,
                change_window_days=window_days,
                price_change=price_change,
                min_price=min_price,
                max_price=max_price,
                change_percentage=change_percentage
            )
            db.add(new_change)

def main():
    """Main job function"""
    logger.info("Starting Kalshi market data refresh job")
    
    try:
        # Get database session
        db = next(get_db())
        
        # Initialize Kalshi service
        kalshi_service = KalshiService()
        
        # Test Kalshi connection
        connection_test = kalshi_service.test_connection()
        if not connection_test["success"]:
            logger.error(f"Kalshi API connection failed: {connection_test['message']}")
            return 1
        
        logger.info("Kalshi API connection successful")
        
        # Get markets from Kalshi API
        logger.info("Fetching markets from Kalshi API...")
        kalshi_response = kalshi_service.get_markets(limit=1000, status="open")
        markets_data = kalshi_response.get("markets", [])
        
        logger.info(f"Found {len(markets_data)} markets to process")
        
        for i, market_data in enumerate(markets_data, 1):
            try:
                # Transform Kalshi data to our format
                transformed_data = {
                    "ticker": market_data["ticker"],
                    "title": market_data["title"],
                    "subtitle": market_data.get("subtitle"),
                    "category": market_data.get("category", "Other"),
                    "status": market_data.get("status", "open"),
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
                market = update_market_data(db, transformed_data)
                
                # Get and update price history
                try:
                    history_data = kalshi_service.get_market_history(market.ticker)
                    update_price_history(db, market, history_data)
                    
                    # Calculate percentage changes
                    calculate_market_changes(db, market)
                    
                    logger.info(f"Processed market {i}/{len(markets_data)}: {market.ticker}")
                except Exception as e:
                    logger.warning(f"Failed to update history for {market.ticker}: {str(e)}")
                    continue
                    
            except Exception as e:
                logger.error(f"Failed to process market {market_data.get('ticker', 'unknown')}: {str(e)}")
                continue
        
        db.commit()
        logger.info(f"Successfully processed {len(markets_data)} markets")
        return 0
        
    except Exception as e:
        logger.error(f"Job failed with error: {str(e)}")
        return 1
    finally:
        try:
            db.close()
        except:
            pass

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 