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
from models import Market, PriceHistory, MarketChange
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

def process_markets(db, kalshi_service):
    """Process markets: create new ones, update existing ones"""
    logger.info("Fetching markets from Kalshi API...")
    kalshi_response = kalshi_service.get_markets(limit=1000, status="open")
    all_markets_data = kalshi_response.get("markets", [])
    
    # Filter for active markets only
    markets_data = [market for market in all_markets_data if market.get("status") == "active"]
    
    logger.info(f"Found {len(all_markets_data)} total markets, {len(markets_data)} active markets")
    
    new_markets_count = 0
    updated_markets_count = 0
    
    for i, market_data in enumerate(markets_data, 1):
        try:
            ticker = market_data["ticker"]
            
            # Check if market exists in DB
            existing_market = db.query(Market).filter(Market.ticker == ticker).first()
            
            # Transform Kalshi data to our format
            transformed_data = {
                "ticker": market_data["ticker"],
                "series_ticker": market_data.get("event_ticker"),  # Use event_ticker from Kalshi API
                "title": market_data["title"],
                "subtitle": market_data.get("subtitle"),
                "category": market_data.get("category", "Other"),
                "status": market_data.get("status", "active"),
                "current_price": 0,  # Will be updated from history data
                "volume_24h": market_data.get("volume_24h", 0),
                "liquidity": market_data.get("liquidity", 0),
                "open_time": datetime.fromisoformat(market_data["open_time"].rstrip("Z")) if market_data.get("open_time") else None,
                "close_time": datetime.fromisoformat(market_data["close_time"].rstrip("Z")) if market_data.get("close_time") else None,
                "expiration_time": datetime.fromisoformat(market_data["expiration_time"].rstrip("Z")) if market_data.get("expiration_time") else None,
                "resolution_rules": market_data.get("resolution_rules"),
                "tags": json.dumps(market_data.get("tags", []))
            }
            
            if not existing_market:
                # Create new market
                new_market = Market(**transformed_data)
                db.add(new_market)
                db.commit()
                db.refresh(new_market)
                new_markets_count += 1
                logger.info(f"Created new market: {ticker}")
                
                # Process history for new market
                process_market_history(db, kalshi_service, new_market)
                
            else:
                # Update existing market with current data
                for key, value in transformed_data.items():
                    if hasattr(existing_market, key):
                        setattr(existing_market, key, value)
                existing_market.updated_at = datetime.utcnow()
                db.commit()
                updated_markets_count += 1
                logger.info(f"Updated market: {ticker}")
                
                # Process history for existing market
                process_market_history(db, kalshi_service, existing_market)
                
        except Exception as e:
            logger.error(f"Failed to process market {market_data.get('ticker', 'unknown')}: {str(e)}")
            continue
    
    logger.info(f"Processed {len(markets_data)} markets: {new_markets_count} new, {updated_markets_count} updated")
    return new_markets_count + updated_markets_count

def process_market_history(db, kalshi_service, market):
    """Process and store market history from candlestick data"""
    try:
        # Get candlestick history data
        history_data = kalshi_service.get_market_history(market.ticker)
        
        if not history_data:
            logger.info(f"No history data available for {market.ticker}")
            return
        
        new_history_points = 0
        
        for data_point in history_data:
            timestamp = data_point["timestamp"]
            
            # Check if this timestamp already exists for this market
            existing_history = db.query(PriceHistory).filter(
                PriceHistory.market_id == market.id,
                PriceHistory.timestamp == timestamp
            ).first()
            
            if not existing_history:
                # Store new history point
                history_point = PriceHistory(
                    market_id=market.id,
                    timestamp=timestamp,
                    price=data_point["price"],
                    volume=data_point.get("volume", 0)
                )
                db.add(history_point)
                new_history_points += 1
        
        db.commit()
        
        if new_history_points > 0:
            logger.info(f"Added {new_history_points} new history points for {market.ticker}")
            
            # Update current price to match the latest history point for consistency
            latest_history = db.query(PriceHistory).filter(
                PriceHistory.market_id == market.id
            ).order_by(PriceHistory.timestamp.desc()).first()
            
            if latest_history:
                logger.info(f"Updating current price for {market.ticker} from {market.current_price} to {latest_history.price}")
                market.current_price = latest_history.price
                db.commit()
        else:
            # Even if no new history points, ensure current_price matches latest history
            latest_history = db.query(PriceHistory).filter(
                PriceHistory.market_id == market.id
            ).order_by(PriceHistory.timestamp.desc()).first()
            
            if latest_history and latest_history.price != market.current_price:
                logger.info(f"Syncing current price for {market.ticker} from {market.current_price} to {latest_history.price}")
                market.current_price = latest_history.price
                db.commit()
        
        # Compute price changes after adding new history
        compute_price_changes(db, market)
        
    except Exception as e:
        logger.warning(f"Failed to process history for {market.ticker}: {str(e)}")

def compute_price_changes(db, market):
    """Compute price changes based on stored history data"""
    try:
        # Get all history for this market, ordered by timestamp
        history = db.query(PriceHistory).filter(
            PriceHistory.market_id == market.id
        ).order_by(PriceHistory.timestamp.desc()).all()
        
        if len(history) < 2:
            logger.info(f"Insufficient history for {market.ticker} to compute changes")
            return
        
        current_price = market.current_price
        
        # Use the latest history timestamp as the reference point
        # This ensures we're calculating changes relative to the most recent data
        latest_timestamp = history[0].timestamp
        
        logger.info(f"Computing changes for {market.ticker}: current_price={current_price}, latest_timestamp={latest_timestamp}, history_points={len(history)}")
        
        # Calculate changes for different time windows
        change_windows = [1, 7, 30, 90]  # days
        
        for window_days in change_windows:
            cutoff_date = latest_timestamp - timedelta(days=window_days)
            
            # Get history within the window (from cutoff to latest)
            window_history = [h for h in history if h.timestamp >= cutoff_date]
            
            logger.info(f"  Window {window_days}d: cutoff={cutoff_date}, points_in_window={len(window_history)}")
            
            if len(window_history) < 2:
                logger.info(f"  Skipping {window_days}d window - insufficient data")
                continue
            
            # Calculate price changes
            prices = [h.price for h in window_history]
            min_price = min(prices)
            max_price = max(prices)
            
            # Calculate directional changes (positive = increase, negative = decrease)
            change_from_min = current_price - min_price
            change_from_max = current_price - max_price
            
            # Use the more dramatic change while preserving direction
            if abs(change_from_min) > abs(change_from_max):
                price_change = change_from_min
            else:
                price_change = change_from_max
            
            # Calculate percentage change
            change_percentage = (price_change / current_price) * 100 if current_price > 0 else 0
            
            logger.info(f"  {window_days}d change: min={min_price}, max={max_price}, change={price_change}, percentage={change_percentage}")
            
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
        
        db.commit()
        logger.info(f"Computed price changes for {market.ticker}")
        
    except Exception as e:
        logger.warning(f"Failed to compute price changes for {market.ticker}: {str(e)}")

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
        
        # Process markets (create new, update existing)
        processed_count = process_markets(db, kalshi_service)
        
        logger.info(f"Successfully processed {processed_count} markets")
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