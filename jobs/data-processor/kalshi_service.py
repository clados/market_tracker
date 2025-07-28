import requests
import time
import base64
import json
import os
import boto3
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from typing import List, Dict, Any, Optional

class KalshiService:
    def __init__(self):
        self.base_url = os.getenv("KALSHI_API_BASE_URL", "https://api.elections.kalshi.com/trade-api/v2")
        self.key_id = os.getenv("KALSHI_KEY_ID")
        
        if not self.key_id:
            raise ValueError("KALSHI_KEY_ID environment variable is required")
        
        # Get private key from environment (Copilot injects secret values directly)
        self.private_key_pem = os.getenv("KALSHI_PRIVATE_KEY")
        if not self.private_key_pem:
            raise ValueError("KALSHI_PRIVATE_KEY environment variable is required")
    
    def _sign(self, timestamp: str, method: str, path: str) -> str:
        """Sign the request using the private key from environment"""
        try:
            # Load private key from environment variable
            private_key = serialization.load_pem_private_key(
                self.private_key_pem.encode(), 
                password=None
            )
            
            # Create message to sign
            message = f"{timestamp}{method}{path}".encode()
            
            # Sign the message
            signature = private_key.sign(
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.DIGEST_LENGTH
                ),
                hashes.SHA256()
            )
            
            return base64.b64encode(signature).decode()
        except Exception as e:
            raise Exception(f"Failed to sign request: {str(e)}")
    
    def _get_auth_headers(self, method: str, path: str) -> Dict[str, str]:
        """Generate authentication headers for Kalshi API"""
        timestamp = str(int(time.time() * 1000))
        signature = self._sign(timestamp, method, path)
        
        return {
            "KALSHI-ACCESS-KEY": self.key_id,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Kalshi API"""
        url = f"{self.base_url}{path}"
        
        # Add query parameters to path for signing
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            path_with_params = f"{path}?{query_string}"
        else:
            path_with_params = path
        
        headers = self._get_auth_headers(method, path_with_params)
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            else:
                response = requests.request(method, url, headers=headers, json=params)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
    def get_markets(self, limit: int = 100, cursor: Optional[str] = None, 
                    status: str = "open") -> Dict[str, Any]:
        """Get markets from Kalshi API"""
        params = {
            "limit": limit,
            "status": status
        }
        
        if cursor:
            params["cursor"] = cursor
        
        path = "/markets"
        return self._make_request("GET", path, params)
    
    def get_market_detail(self, ticker: str) -> Dict[str, Any]:
        """Get specific market details"""
        path = f"/markets/{ticker}"
        return self._make_request("GET", path)
    
    def get_market_history(self, ticker: str, period_minutes: int = 60) -> List[Dict[str, Any]]:
        """Get market price history using candlesticks endpoint"""
        # First get market details to find the series ticker
        market_data = self.get_market_detail(ticker)
        market = market_data.get("market", market_data)
        series_ticker = market.get("series_ticker") or market.get("event_ticker") or ticker
        
        # Calculate time range
        def _iso_to_ts(iso: str) -> int:
            return int(datetime.fromisoformat(iso.rstrip("Z")).timestamp())
        
        open_time_str = market.get("openTime", market.get("open_time", ""))
        if open_time_str:
            open_ts = _iso_to_ts(open_time_str)
        else:
            open_ts = int(time.time()) - 30*24*3600  # 30 days ago
        
        end_ts = int(time.time())
        
        print(f"Fetching history for {ticker}: open_ts={open_ts} ({datetime.fromtimestamp(open_ts)}), end_ts={end_ts} ({datetime.fromtimestamp(end_ts)})")
        
        # Download candlesticks in chunks
        path = f"/series/{series_ticker}/markets/{ticker}/candlesticks"
        period_seconds = period_minutes * 60
        max_periods = 5000  # API limit per call
        max_span_seconds = period_seconds * max_periods
        
        all_candles = []
        current_end_ts = end_ts
        
        while current_end_ts > open_ts:
            current_start_ts = max(open_ts, current_end_ts - max_span_seconds)
            
            params = {
                "period_interval": period_minutes,
                "start_ts": current_start_ts,
                "end_ts": current_end_ts
            }
            
            print(f"  Requesting chunk: start_ts={current_start_ts} ({datetime.fromtimestamp(current_start_ts)}), end_ts={current_end_ts} ({datetime.fromtimestamp(current_end_ts)})")
            
            try:
                response = self._make_request("GET", path, params)
                candles = response.get("candlesticks", [])
                all_candles.extend(candles)
                
                print(f"  Got {len(candles)} candles in this chunk")
                
                # If we got fewer than max_periods, we've reached the beginning
                if len(candles) < max_periods:
                    print(f"  Reached beginning (got {len(candles)} < {max_periods})")
                    break
                    
                # Move backward for next chunk
                current_end_ts = current_start_ts
                
            except Exception as e:
                print(f"Failed to get candlesticks for {ticker}: {str(e)}")
                break
        
        print(f"Total candles fetched for {ticker}: {len(all_candles)}")
        
        # Transform candlesticks to our format
        history = []
        for candle in all_candles:
            yes_bid_close = float(candle.get("yes_bid", {}).get("close", 0))
            yes_ask_close = float(candle.get("yes_ask", {}).get("close", 0))
            mid_price = (yes_bid_close + yes_ask_close) / 2
            probability = round(mid_price / 100, 3)
            
            history.append({
                "timestamp": datetime.fromtimestamp(candle.get("end_period_ts", 0)),
                "price": probability,
                "volume": int(candle.get("volume", 0))
            })
        
        return history
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Kalshi API connection"""
        try:
            response = self.get_markets(limit=1)
            return {"success": True, "message": "Successfully connected to Kalshi API"}
        except Exception as e:
            return {"success": False, "message": f"Connection failed: {str(e)}"} 