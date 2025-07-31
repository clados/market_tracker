#!/usr/bin/env python3
"""
Scheduled job to fetch Polymarket data and store it in the database.
This job runs daily to keep the database updated with fresh Polymarket data.
"""

import sys
import os

# Add shared package to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_db, get_engine
from models import Market, PriceHistory, MarketChange
from polymarket_service import PolymarketService
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

def process_polymarket_markets(db, polymarket_service):
    """Process Polymarket markets: create new ones, update existing ones"""
    logger.info("Fetching markets from Polymarket Gamma API...")
    
    # Get active markets with volume using the corrected service
    markets_data = polymarket_service.get_active_markets_with_volume(min_volume=1000)
    
    if not markets_data:
        logger.warning("No active markets with volume found")
        return 0
    
    logger.info(f"Found {len(markets_data)} active markets with volume > 1000")
    
    new_markets_count = 0
    updated_markets_count = 0
    
    for i, market_data in enumerate(markets_data, 1):
        try:
            market_id = market_data["id"]
            
            # Check if market exists in DB (use market_id as ticker for Polymarket)
            existing_market = db.query(Market).filter(Market.ticker == market_id).first()
            
            # Transform Polymarket data to our format
            transformed_data = {
                "ticker": market_id,  # Use Polymarket market ID as ticker
                "series_ticker": market_data.get("event_id"),  # Use event_id from Polymarket
                "title": market_data.get("question", market_data.get("title", "")),
                "subtitle": market_data.get("description", market_data.get("subtitle", "")),
                "category": market_data.get("category", "Other"),
                "status": "active" if market_data.get("active", False) else "inactive",
                "current_price": 0,  # Will be updated from history data
                "volume_24h": int(float(market_data.get("volumeClob", market_data.get("volume24hr", 0)))),
                "liquidity": int(float(market_data.get("liquidityClob", market_data.get("liquidity", 0)))),
                "open_time": None,  # Polymarket doesn't provide these in the API
                "close_time": None,
                "expiration_time": None,
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
                logger.info(f"Created new Polymarket: {market_id}")
                
                # Process history for new market
                process_polymarket_history(db, polymarket_service, new_market, market_data)
                
            else:
                # Update existing market with current data
                for key, value in transformed_data.items():
                    if hasattr(existing_market, key):
                        setattr(existing_market, key, value)
                existing_market.updated_at = datetime.utcnow()
                db.commit()
                updated_markets_count += 1
                logger.info(f"Updated Polymarket: {market_id}")
                
                # Process history for existing market
                process_polymarket_history(db, polymarket_service, existing_market, market_data)
                
        except Exception as e:
            logger.error(f"Failed to process Polymarket {market_data.get('id', 'unknown')}: {str(e)}")
            # Rollback the session to clear any pending transaction
            try:
                db.rollback()
            except:
                pass
            continue
    
    logger.info(f"Processed {len(markets_data)} Polymarket markets: {new_markets_count} new, {updated_markets_count} updated")
    return new_markets_count + updated_markets_count

def process_polymarket_history(db, polymarket_service, market, market_data):
    """Process price history for a Polymarket market using CLOB token IDs"""
    try:
        logger.info(f"Processing history for Polymarket {market.ticker}")
        
        # Get CLOB token IDs from the market data
        clob_token_ids = polymarket_service._parse_clob_token_ids(market_data.get("clobTokenIds"))
        
        if not clob_token_ids:
            logger.warning(f"No CLOB token IDs found for Polymarket {market.ticker}")
            return
        
        # Use the first token ID for price history (usually the "Yes" outcome)
        token_id = clob_token_ids[0]
        logger.info(f"Using CLOB token ID: {token_id}")
        
        # Get price history from CLOB API using the corrected service
        history_data = polymarket_service.get_market_price_history_by_interval(token_id, "1d")
        
        if not history_data:
            logger.info(f"No trading history available for Polymarket {market.ticker} (new market)")
            return
        
        # Update current price with most recent data
        if history_data:
            latest_price = history_data[-1]["price"]
            market.current_price = latest_price
            db.commit()
        
        # Clear existing history for this market
        db.query(PriceHistory).filter(PriceHistory.market_id == market.id).delete()
        
        # Add new history entries
        for entry in history_data:
            price_history = PriceHistory(
                market_id=market.id,
                timestamp=entry["timestamp"],
                price=entry["price"],
                volume=entry["volume"]
            )
            db.add(price_history)
        
        db.commit()
        logger.info(f"Updated history for Polymarket {market.ticker}: {len(history_data)} entries")
        
    except Exception as e:
        logger.warning(f"Failed to process history for Polymarket {market.ticker}: {str(e)}")
        # Don't fail the entire job for history errors
        return

def compute_polymarket_price_changes(db, market):
    """Compute price changes for Polymarket market"""
    try:
        # Get price history for different time windows
        time_windows = [1, 7, 30, 90]  # days
        
        for window_days in time_windows:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=window_days)
            
            # Get price history within window
            history = db.query(PriceHistory).filter(
                PriceHistory.market_id == market.id,
                PriceHistory.timestamp >= cutoff_date
            ).order_by(PriceHistory.timestamp.asc()).all()
            
            if len(history) < 2:
                continue
            
            # Calculate price change
            start_price = history[0].price
            end_price = history[-1].price
            price_change = end_price - start_price
            change_percentage = (price_change / start_price) * 100 if start_price > 0 else 0
            
            # Find min/max prices
            prices = [h.price for h in history]
            min_price = min(prices)
            max_price = max(prices)
            
            # Check if change record already exists
            existing_change = db.query(MarketChange).filter(
                MarketChange.market_id == market.id,
                MarketChange.change_window_days == window_days
            ).first()
            
            if existing_change:
                # Update existing record
                existing_change.price_change = price_change
                existing_change.min_price = min_price
                existing_change.max_price = max_price
                existing_change.change_percentage = change_percentage
                existing_change.calculated_at = datetime.utcnow()
            else:
                # Create new record
                market_change = MarketChange(
                    market_id=market.id,
                    change_window_days=window_days,
                    price_change=price_change,
                    min_price=min_price,
                    max_price=max_price,
                    change_percentage=change_percentage
                )
                db.add(market_change)
        
        db.commit()
        logger.info(f"Computed price changes for Polymarket {market.ticker}")
        
    except Exception as e:
        logger.error(f"Failed to compute price changes for Polymarket {market.ticker}: {str(e)}")

def main():
    """Main job function"""
    try:
        logger.info("Starting Polymarket data processor job")
        
        # Initialize services
        polymarket_service = PolymarketService()
        
        # Test connection
        connection_result = polymarket_service.test_connection()
        if connection_result["status"] != "OK":
            logger.error(f"Polymarket API connection failed: {connection_result['message']}")
            return
        
        logger.info(f"Polymarket API connection test: {connection_result['message']}")
        
        # Get database session
        db = next(get_db())
        
        try:
            # Process markets
            processed_count = process_polymarket_markets(db, polymarket_service)
            logger.info(f"Processed {processed_count} Polymarket markets")
            
            # Compute price changes for all Polymarket markets
            try:
                markets = db.query(Market).filter(Market.ticker.like("%")).all()
                for market in markets:
                    compute_polymarket_price_changes(db, market)
            except Exception as e:
                logger.error(f"Failed to compute price changes: {str(e)}")
                try:
                    db.rollback()
                except:
                    pass
            
            logger.info("Polymarket data processor job completed successfully")
            
        finally:
            try:
                db.close()
            except:
                pass
            
    except Exception as e:
        logger.error(f"Polymarket data processor job failed: {str(e)}")
        try:
            db.rollback()
        except:
            pass
        raise

if __name__ == "__main__":
    main() 