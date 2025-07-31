#!/usr/bin/env python3
"""
Detailed investigation of Polymarket CLOB API
"""

import requests
import time
from datetime import datetime, timedelta

def test_older_markets():
    """Test getting older markets that should have more history"""
    print("=== Testing Older Markets ===\n")
    
    # Get older markets from Gamma API
    gamma_url = "https://gamma-api.polymarket.com/markets"
    params = {
        "limit": 10,
        "offset": 0,
        "start_date_max": "2025-05-11"  # This should give us older markets
    }
    
    try:
        response = requests.get(gamma_url, params=params, timeout=10)
        print(f"Gamma API Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            markets = data if isinstance(data, list) else data.get("markets", [])
            
            for i, market in enumerate(markets):
                print(f"\n--- Market {i+1} ---")
                print(f"ID: {market.get('id')}")
                print(f"Title: {market.get('question', market.get('title', 'N/A'))}")
                print(f"Volume: {market.get('volume', 'N/A')}")
                print(f"Liquidity: {market.get('liquidity', 'N/A')}")
                print(f"End Date: {market.get('endDate', 'N/A')}")
                print(f"Closed: {market.get('closed', 'N/A')}")
                
                # Check for CLOB-specific fields
                clob_token_ids = market.get('clobTokenIds', [])
                if clob_token_ids:
                    print(f"CLOB Token IDs: {clob_token_ids}")
                    
                    # Test current price for each token
                    for j, token_id in enumerate(clob_token_ids):
                        test_current_price(token_id, f"Token {j+1}")
                
                print()
                
    except Exception as e:
        print(f"Error: {str(e)}")

def test_current_price(token_id, token_name=""):
    """Test the current price endpoint"""
    print(f"  {token_name} Current Price Test:")
    
    # Test buy side
    clob_url = "https://clob.polymarket.com/price"
    params = {
        "token_id": token_id,
        "side": "buy"
    }
    
    try:
        response = requests.get(clob_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"    Buy Price: {data}")
        else:
            print(f"    Buy Price: Error {response.status_code}")
    except Exception as e:
        print(f"    Buy Price: Exception {str(e)}")
    
    # Test sell side
    params["side"] = "sell"
    try:
        response = requests.get(clob_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"    Sell Price: {data}")
        else:
            print(f"    Sell Price: Error {response.status_code}")
    except Exception as e:
        print(f"    Sell Price: Exception {str(e)}")

def test_history_with_older_markets():
    """Test history for older markets"""
    print("\n=== Testing History for Older Markets ===\n")
    
    # Get a few older markets
    gamma_url = "https://gamma-api.polymarket.com/markets"
    params = {
        "limit": 5,
        "offset": 0,
        "start_date_max": "2025-05-11"
    }
    
    try:
        response = requests.get(gamma_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            markets = data if isinstance(data, list) else data.get("markets", [])
            
            for i, market in enumerate(markets):
                print(f"\nMarket {i+1}: {market.get('question', 'N/A')}")
                print(f"Volume: {market.get('volume', 'N/A')}")
                print(f"Closed: {market.get('closed', 'N/A')}")
                
                clob_token_ids = market.get('clobTokenIds', [])
                if clob_token_ids:
                    # Test history for each token ID
                    for j, token_id in enumerate(clob_token_ids):
                        print(f"  Testing history for token {j+1}: {token_id}")
                        
                        # Test different time ranges
                        time_ranges = [
                            ("Last 7 days", 7),
                            ("Last 30 days", 30),
                            ("Last 90 days", 90)
                        ]
                        
                        for name, days in time_ranges:
                            end_ts = int(time.time())
                            start_ts = end_ts - (days * 24 * 3600)
                            
                            clob_url = "https://clob.polymarket.com/prices-history"
                            params = {
                                "market": token_id,
                                "startTs": start_ts,
                                "endTs": end_ts,
                                "interval": "1h"
                            }
                            
                            try:
                                response = requests.get(clob_url, params=params, timeout=10)
                                if response.status_code == 200:
                                    data = response.json()
                                    history_count = len(data.get("history", []))
                                    print(f"    {name}: {history_count} entries")
                                else:
                                    print(f"    {name}: Error {response.status_code}")
                            except Exception as e:
                                print(f"    {name}: Exception {str(e)}")
                
                print()
                
    except Exception as e:
        print(f"Error: {str(e)}")

def test_market_details():
    """Test getting detailed market information"""
    print("=== Testing Market Details ===\n")
    
    # Get a few markets from Gamma API
    gamma_url = "https://gamma-api.polymarket.com/markets"
    params = {
        "limit": 5,
        "offset": 0,
        "active": "true",
        "closed": "false"
    }
    
    try:
        response = requests.get(gamma_url, params=params, timeout=10)
        print(f"Gamma API Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            markets = data if isinstance(data, list) else data.get("markets", [])
            
            for i, market in enumerate(markets):
                print(f"\n--- Market {i+1} ---")
                print(f"ID: {market.get('id')}")
                print(f"Title: {market.get('question', market.get('title', 'N/A'))}")
                print(f"Status: {market.get('status', 'N/A')}")
                print(f"Open Time: {market.get('openTime', 'N/A')}")
                print(f"Close Time: {market.get('closeTime', 'N/A')}")
                print(f"Expiration Time: {market.get('expirationTime', 'N/A')}")
                
                # Check for CLOB-specific fields
                clob_fields = ['clobTokenIds', 'volumeClob', 'liquidityClob', 'lastTradePrice']
                for field in clob_fields:
                    if field in market:
                        print(f"{field}: {market[field]}")
                
                # Test with different time ranges
                market_id = market.get('id')
                if market_id:
                    test_different_time_ranges(market_id)
                
                print()
                
    except Exception as e:
        print(f"Error: {str(e)}")

def test_different_time_ranges(market_id):
    """Test different time ranges for a market"""
    print(f"  Testing time ranges for market {market_id}:")
    
    # Test different time ranges
    time_ranges = [
        ("Last 24 hours", 1),
        ("Last 7 days", 7),
        ("Last 30 days", 30),
        ("Last 90 days", 90),
        ("Last year", 365)
    ]
    
    for name, days in time_ranges:
        end_ts = int(time.time())
        start_ts = end_ts - (days * 24 * 3600)
        
        clob_url = "https://clob.polymarket.com/prices-history"
        params = {
            "market": market_id,
            "startTs": start_ts,
            "endTs": end_ts,
            "interval": "1h"
        }
        
        try:
            response = requests.get(clob_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                history_count = len(data.get("history", []))
                print(f"    {name}: {history_count} entries")
            else:
                print(f"    {name}: Error {response.status_code}")
        except Exception as e:
            print(f"    {name}: Exception {str(e)}")

def test_clob_token_ids():
    """Test if we need to use clobTokenIds instead of market IDs"""
    print("\n=== Testing CLOB Token IDs ===\n")
    
    # Get markets with clobTokenIds
    gamma_url = "https://gamma-api.polymarket.com/markets"
    params = {
        "limit": 3,
        "offset": 0,
        "active": "true",
        "closed": "false"
    }
    
    try:
        response = requests.get(gamma_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            markets = data if isinstance(data, list) else data.get("markets", [])
            
            for i, market in enumerate(markets):
                print(f"\nMarket {i+1}: {market.get('question', 'N/A')}")
                print(f"Market ID: {market.get('id')}")
                
                clob_token_ids = market.get('clobTokenIds', [])
                print(f"CLOB Token IDs: {clob_token_ids}")
                
                # Test each clob token ID
                for j, token_id in enumerate(clob_token_ids):
                    print(f"  Testing CLOB Token ID {j+1}: {token_id}")
                    
                    end_ts = int(time.time())
                    start_ts = end_ts - (7 * 24 * 3600)  # 7 days
                    
                    clob_url = "https://clob.polymarket.com/prices-history"
                    params = {
                        "market": token_id,  # Try using token ID instead of market ID
                        "startTs": start_ts,
                        "endTs": end_ts,
                        "interval": "1h"
                    }
                    
                    try:
                        response = requests.get(clob_url, params=params, timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            history_count = len(data.get("history", []))
                            print(f"    Result: {history_count} entries")
                        else:
                            print(f"    Result: Error {response.status_code}")
                    except Exception as e:
                        print(f"    Result: Exception {str(e)}")
                
                print()
                
    except Exception as e:
        print(f"Error: {str(e)}")

def test_authentication():
    """Test if CLOB API requires authentication"""
    print("\n=== Testing Authentication ===\n")
    
    # Test with different headers
    headers_to_test = [
        {},
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        {"Accept": "application/json"},
        {"Authorization": "Bearer test"},
        {"X-API-Key": "test"}
    ]
    
    # Use a known market ID
    market_id = "512644"  # Trump term limits market
    
    end_ts = int(time.time())
    start_ts = end_ts - (7 * 24 * 3600)
    
    clob_url = "https://clob.polymarket.com/prices-history"
    params = {
        "market": market_id,
        "startTs": start_ts,
        "endTs": end_ts,
        "interval": "1h"
    }
    
    for i, headers in enumerate(headers_to_test):
        print(f"Test {i+1}: Headers = {headers}")
        
        try:
            response = requests.get(clob_url, params=params, headers=headers, timeout=10)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                history_count = len(data.get("history", []))
                print(f"  History entries: {history_count}")
            else:
                print(f"  Error: {response.text[:100]}")
        except Exception as e:
            print(f"  Exception: {str(e)}")
        print()

if __name__ == "__main__":
    test_older_markets()
    test_history_with_older_markets()
    test_market_details()
    test_clob_token_ids()
    test_authentication() 