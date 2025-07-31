#!/usr/bin/env python3
"""
Test the corrected CLOB API implementation
"""

import logging
import json
from polymarket_service import PolymarketService

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_corrected_clob():
    """Test the corrected CLOB API implementation"""
    service = PolymarketService()
    
    print("=== Testing Corrected CLOB API ===\n")
    
    # Test 1: Connection test
    print("1. Testing connection...")
    connection_result = service.test_connection()
    print(f"   Result: {connection_result}")
    print()
    
    # Test 2: Get markets and find ones with clobTokenIds
    print("2. Getting markets with CLOB token IDs...")
    try:
        markets_response = service.get_markets(limit=20)
        markets = markets_response.get("markets", [])
        print(f"   Found {len(markets)} total markets")
        
        # Find markets with clobTokenIds
        markets_with_clob = []
        for market in markets:
            clob_token_ids = service._parse_clob_token_ids(market.get("clobTokenIds"))
            if clob_token_ids:
                markets_with_clob.append(market)
                print(f"   Market: {market.get('question', 'N/A')}")
                print(f"     ID: {market.get('id')}")
                print(f"     CLOB Token IDs: {clob_token_ids}")
                print(f"     Volume: {market.get('volumeClob', 0)}")
                print()
        
        print(f"   Found {len(markets_with_clob)} markets with CLOB token IDs")
        
        # Test 3: Test price history for a market with CLOB token IDs
        if markets_with_clob:
            test_market = markets_with_clob[0]
            clob_token_ids = service._parse_clob_token_ids(test_market.get("clobTokenIds"))
            
            if clob_token_ids:
                test_token_id = clob_token_ids[0]
                print(f"3. Testing price history for market: {test_market.get('question')}")
                print(f"   Using token ID: {test_token_id}")
                
                # Test raw data first
                print("   Testing raw data retrieval...")
                try:
                    # Get raw data to see the structure
                    params = {
                        "market": test_token_id,
                        "interval": "1h"
                    }
                    
                    import requests
                    url = "https://clob.polymarket.com/prices-history"
                    response = requests.get(url, params=params, timeout=30)
                    if response.status_code == 200:
                        raw_data = response.json()
                        print(f"     Raw response structure: {json.dumps(raw_data, indent=2)[:500]}...")
                        
                        if "history" in raw_data and raw_data["history"]:
                            sample_entry = raw_data["history"][0]
                            print(f"     Sample history entry: {json.dumps(sample_entry, indent=2)}")
                    else:
                        print(f"     Error: {response.status_code} - {response.text}")
                except Exception as e:
                    print(f"     Error getting raw data: {str(e)}")
                print()
                
                # Test different intervals
                intervals = ["1d", "1w", "1h"]
                
                for interval in intervals:
                    print(f"   Testing interval: {interval}")
                    try:
                        history = service.get_market_price_history_by_interval(test_token_id, interval)
                        print(f"     Retrieved {len(history)} price points")
                        
                        if history:
                            print("     Sample points:")
                            for i, point in enumerate(history[:3]):
                                print(f"       {i+1}. Time: {point['timestamp']}, Price: {point['price']}, Volume: {point['volume']}")
                        else:
                            print("     No price history available")
                    except Exception as e:
                        print(f"     Error: {str(e)}")
                    print()
                
                # Test with time range
                print("   Testing with time range (last 7 days)...")
                try:
                    history = service.get_market_price_history_by_days(test_token_id, 7)
                    print(f"     Retrieved {len(history)} price points for last 7 days")
                    
                    if history:
                        print("     Sample points:")
                        for i, point in enumerate(history[:3]):
                            print(f"       {i+1}. Time: {point['timestamp']}, Price: {point['price']}, Volume: {point['volume']}")
                    else:
                        print("     No price history available")
                except Exception as e:
                    print(f"     Error: {str(e)}")
            else:
                print("   No CLOB token IDs found in test market")
        else:
            print("   No markets with CLOB token IDs found")
            
    except Exception as e:
        print(f"   Error: {str(e)}")
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    test_corrected_clob() 