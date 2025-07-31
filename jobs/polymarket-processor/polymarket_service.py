#!/usr/bin/env python3
"""
Polymarket Service using CLOB API for price history and GraphQL for market data
"""

import requests
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class PolymarketService:
    def __init__(self, gamma_base_url: str = "https://gamma-api.polymarket.com", 
                 clob_base_url: str = "https://clob.polymarket.com"):
        self.gamma_base_url = gamma_base_url
        self.clob_base_url = clob_base_url
        
    def _make_gamma_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make request to Polymarket Gamma API"""
        url = f"{self.gamma_base_url}{endpoint}"
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Gamma API request failed: {str(e)}")
            raise Exception(f"Gamma API request failed: {str(e)}")
    
    def _make_clob_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make request to Polymarket CLOB API"""
        url = f"{self.clob_base_url}{endpoint}"
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"CLOB API request failed: {str(e)}")
            raise Exception(f"CLOB API request failed: {str(e)}")
    
    def _parse_clob_token_ids(self, clob_token_ids_field) -> List[str]:
        """Parse clobTokenIds field which might be a JSON string or list"""
        if not clob_token_ids_field:
            return []
        
        if isinstance(clob_token_ids_field, list):
            return clob_token_ids_field
        elif isinstance(clob_token_ids_field, str):
            try:
                # Try to parse as JSON string
                parsed = json.loads(clob_token_ids_field)
                if isinstance(parsed, list):
                    return parsed
                else:
                    return []
            except (json.JSONDecodeError, TypeError):
                return []
        else:
            return []
    
    def get_markets(self, limit: int = 100, offset: int = 0, 
                    active: bool = True, closed: bool = False) -> Dict[str, Any]:
        """Get markets from Polymarket Gamma API"""
        params = {
            "limit": limit,
            "offset": offset,
            "active": str(active).lower(),
            "closed": str(closed).lower()
        }
        
        response = self._make_gamma_request("/markets", params)
        
        # Handle different response formats
        if isinstance(response, list):
            # If response is a list, wrap it in a dict
            return {"markets": response}
        elif isinstance(response, dict) and "markets" in response:
            # If response already has markets key
            return response
        else:
            # If response is a dict but no markets key, assume it's the markets list
            return {"markets": [response]}
    
    def get_market_detail(self, market_id: str) -> Dict[str, Any]:
        """Get specific market details from Gamma API"""
        return self._make_gamma_request(f"/markets/{market_id}")
    
    def get_market_price_history(self, market_token_id: str, interval: str = "1h", 
                                start_ts: Optional[int] = None, end_ts: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get market price history from CLOB API using the correct endpoint"""
        
        # Build parameters
        params = {
            "market": market_token_id,
            "interval": interval
        }
        
        # Add time range if provided
        if start_ts is not None:
            params["startTs"] = start_ts
        if end_ts is not None:
            params["endTs"] = end_ts
        
        try:
            data = self._make_clob_request("/prices-history", params)
            history = data.get("history", [])
            
            logger.info(f"Retrieved {len(history)} price history points for market {market_token_id}")
            
            # Transform to our format
            transformed_history = []
            for entry in history:
                # Handle timestamp - CLOB API uses "t" for timestamp
                timestamp = entry.get("t", 0)
                if isinstance(timestamp, str):
                    try:
                        timestamp = int(timestamp)
                    except (ValueError, TypeError):
                        timestamp = 0
                
                # Convert timestamp to datetime
                try:
                    if timestamp > 1e12:  # If timestamp is in milliseconds
                        timestamp = timestamp / 1000
                    elif timestamp == 0:  # If timestamp is 0, skip this entry
                        continue
                    
                    dt = datetime.fromtimestamp(timestamp)
                except (ValueError, TypeError, OSError):
                    # If timestamp conversion fails, skip this entry
                    continue
                
                # Handle price - CLOB API uses "p" for price
                price = entry.get("p", 0)
                
                # Convert to appropriate types
                try:
                    price = float(price) if price is not None else 0.0
                except (ValueError, TypeError):
                    price = 0.0
                
                # Add all entries with valid timestamps and prices
                if price >= 0:  # Allow 0 prices as they might be valid
                    transformed_history.append({
                        "timestamp": dt,
                        "price": price,
                        "volume": 0  # CLOB API doesn't provide volume in this endpoint
                    })
            
            logger.info(f"Transformed {len(transformed_history)} valid price history points")
            return transformed_history
            
        except Exception as e:
            logger.error(f"Failed to get price history for market {market_token_id}: {str(e)}")
            return []
    
    def get_market_price_history_by_days(self, market_token_id: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get market price history for the last N days"""
        end_ts = int(time.time())
        start_ts = end_ts - (days_back * 24 * 3600)  # days_back days ago
        
        return self.get_market_price_history(market_token_id, start_ts=start_ts, end_ts=end_ts)
    
    def get_market_price_history_by_interval(self, market_token_id: str, interval: str = "1d") -> List[Dict[str, Any]]:
        """Get market price history using interval parameter"""
        return self.get_market_price_history(market_token_id, interval=interval)
    
    def test_connection(self) -> Dict[str, str]:
        """Test connectivity to both Gamma and CLOB APIs"""
        try:
            # Test Gamma API
            gamma_response = self.get_markets(limit=1)
            gamma_success = "markets" in gamma_response and len(gamma_response["markets"]) > 0
            
            # Test CLOB API with a sample market
            clob_success = True
            try:
                # Get a sample market to test CLOB API
                sample_markets = self.get_markets(limit=5)
                if sample_markets.get("markets"):
                    # Find a market with clobTokenIds
                    for market in sample_markets["markets"]:
                        clob_token_ids = self._parse_clob_token_ids(market.get("clobTokenIds"))
                        if clob_token_ids:
                            # Test with the first token ID
                            test_token_id = clob_token_ids[0]
                            self.get_market_price_history_by_interval(test_token_id, "1d")
                            break
                    else:
                        clob_success = False
                        logger.warning("No markets with clobTokenIds found for CLOB API test")
                else:
                    clob_success = False
            except Exception as e:
                clob_success = False
                logger.warning(f"CLOB API test failed: {str(e)}")
            
            return {
                "status": "OK" if gamma_success and clob_success else "FAILED",
                "message": f"Gamma API: {'OK' if gamma_success else 'FAILED'}, CLOB API: {'OK' if clob_success else 'FAILED'}",
                "gamma_api": gamma_success,
                "clob_api": clob_success
            }
                
        except Exception as e:
            return {"status": "FAILED", "message": f"Connection failed: {str(e)}"}
    
    def get_active_markets_with_volume(self, min_volume: float = 0) -> List[Dict[str, Any]]:
        """Get active markets with minimum volume"""
        try:
            # Get markets in batches to find ones with volume
            all_markets = []
            offset = 0
            limit = 100
            
            while len(all_markets) < 500:  # Limit to prevent infinite loop
                markets_response = self.get_markets(limit=limit, offset=offset)
                markets = markets_response.get("markets", [])
                
                if not markets:
                    break
                
                # Filter for active markets with volume and clobTokenIds
                active_markets = []
                for market in markets:
                    clob_token_ids = self._parse_clob_token_ids(market.get("clobTokenIds"))
                    if (market.get("active", False) and 
                        not market.get("closed", False) and
                        clob_token_ids and  # Must have CLOB token IDs
                        (market.get("volumeClob", 0) > min_volume or market.get("volume24hr", 0) > min_volume)):
                        # Add parsed clobTokenIds to the market data
                        market["parsed_clob_token_ids"] = clob_token_ids
                        active_markets.append(market)
                
                all_markets.extend(active_markets)
                offset += limit
                
                if len(markets) < limit:  # No more markets
                    break
            
            logger.info(f"Found {len(all_markets)} active markets with volume > {min_volume}")
            return all_markets
            
        except Exception as e:
            logger.error(f"Failed to get active markets with volume: {str(e)}")
            return [] 