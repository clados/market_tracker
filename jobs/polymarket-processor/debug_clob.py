#!/usr/bin/env python3
"""
Debug script to investigate Polymarket CLOB API issues
"""

import requests
import time
from datetime import datetime

def test_clob_api():
    """Test different CLOB API endpoints and parameters"""
    
    # Test different base URLs
    base_urls = [
        "https://clob.polymarket.com",
        "https://api.polymarket.com",
        "https://gamma-api.polymarket.com"
    ]
    
    # Test different endpoints
    endpoints = [
        "/prices-history",
        "/price-history", 
        "/history",
        "/markets/{market_id}/history",
        "/markets/{market_id}/prices"
    ]
    
    # Test different market IDs (from the logs)
    market_ids = [
        "516729",
        "516730", 
        "516731",
        "516732",
        "516733"
    ]
    
    print("=== Testing CLOB API Endpoints ===\n")
    
    for base_url in base_urls:
        print(f"\n--- Testing base URL: {base_url} ---")
        
        for endpoint in endpoints:
            for market_id in market_ids[:2]:  # Test first 2 markets per endpoint
                # Replace placeholder in endpoint
                test_endpoint = endpoint.replace("{market_id}", market_id)
                
                # Test different parameter combinations
                test_params = [
                    # Original parameters
                    {
                        "market": market_id,
                        "startTs": int(time.time()) - (7 * 24 * 3600),  # 7 days ago
                        "endTs": int(time.time()),
                        "interval": "1h"
                    },
                    # Without interval
                    {
                        "market": market_id,
                        "startTs": int(time.time()) - (7 * 24 * 3600),
                        "endTs": int(time.time())
                    },
                    # With different interval
                    {
                        "market": market_id,
                        "startTs": int(time.time()) - (7 * 24 * 3600),
                        "endTs": int(time.time()),
                        "interval": "1d"
                    },
                    # Just market ID
                    {
                        "market": market_id
                    }
                ]
                
                for i, params in enumerate(test_params):
                    url = f"{base_url}{test_endpoint}"
                    
                    try:
                        print(f"  Testing: {url}")
                        print(f"  Params: {params}")
                        
                        response = requests.get(url, params=params, timeout=10)
                        
                        print(f"  Status: {response.status_code}")
                        if response.status_code == 200:
                            data = response.json()
                            print(f"  Success! Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                            if isinstance(data, dict) and "history" in data:
                                print(f"  History entries: {len(data['history'])}")
                            break  # Found working endpoint
                        else:
                            print(f"  Error: {response.text[:200]}")
                            
                    except Exception as e:
                        print(f"  Exception: {str(e)}")
                    
                    print()

def test_gamma_api_for_clob_ids():
    """Test if Gamma API provides different market IDs for CLOB"""
    print("\n=== Testing Gamma API for CLOB-compatible IDs ===\n")
    
    try:
        # Get markets from Gamma API
        gamma_url = "https://gamma-api.polymarket.com/markets"
        params = {
            "limit": 10,
            "offset": 0,
            "active": "true",
            "closed": "false"
        }
        
        response = requests.get(gamma_url, params=params, timeout=10)
        print(f"Gamma API Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            markets = data if isinstance(data, list) else data.get("markets", [])
            
            print(f"Found {len(markets)} markets")
            
            for i, market in enumerate(markets[:5]):
                print(f"\nMarket {i+1}:")
                print(f"  ID: {market.get('id')}")
                print(f"  Title: {market.get('question', market.get('title', 'N/A'))}")
                print(f"  Status: {market.get('status', 'N/A')}")
                
                # Look for potential CLOB-related fields
                for key, value in market.items():
                    if 'clob' in key.lower() or 'trade' in key.lower() or 'price' in key.lower():
                        print(f"  {key}: {value}")
                
                # Test this market ID with CLOB API
                market_id = market.get('id')
                if market_id:
                    clob_url = "https://clob.polymarket.com/prices-history"
                    clob_params = {
                        "market": market_id,
                        "startTs": int(time.time()) - (1 * 24 * 3600),  # 1 day ago
                        "endTs": int(time.time()),
                        "interval": "1h"
                    }
                    
                    try:
                        clob_response = requests.get(clob_url, params=clob_params, timeout=10)
                        print(f"  CLOB test: {clob_response.status_code}")
                        if clob_response.status_code == 200:
                            clob_data = clob_response.json()
                            print(f"  CLOB success! History: {len(clob_data.get('history', []))}")
                        else:
                            print(f"  CLOB error: {clob_response.text[:100]}")
                    except Exception as e:
                        print(f"  CLOB exception: {str(e)}")
                
                print()
                
    except Exception as e:
        print(f"Gamma API test failed: {str(e)}")

def test_documentation():
    """Test if there's any documentation or examples"""
    print("\n=== Testing for Documentation/Examples ===\n")
    
    # Test common documentation endpoints
    doc_urls = [
        "https://clob.polymarket.com/docs",
        "https://clob.polymarket.com/api",
        "https://api.polymarket.com/docs",
        "https://gamma-api.polymarket.com/docs"
    ]
    
    for url in doc_urls:
        try:
            response = requests.get(url, timeout=5)
            print(f"{url}: {response.status_code}")
            if response.status_code == 200:
                print(f"  Content type: {response.headers.get('content-type', 'unknown')}")
        except Exception as e:
            print(f"{url}: Error - {str(e)}")

if __name__ == "__main__":
    test_clob_api()
    test_gamma_api_for_clob_ids()
    test_documentation() 