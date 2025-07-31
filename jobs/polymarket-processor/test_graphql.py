#!/usr/bin/env python3
"""
Test script for Polymarket GraphQL API
"""

import logging
from polymarket_service import PolymarketService

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_graphql_api():
    """Test the GraphQL API functionality"""
    service = PolymarketService()
    
    print("=== Testing Polymarket GraphQL API ===\n")
    
    # Test 1: Connection test
    print("1. Testing connection...")
    connection_result = service.test_connection()
    print(f"   Result: {connection_result}")
    print()
    
    # Test 2: Get markets
    print("2. Getting markets...")
    try:
        markets = service.get_markets(limit=5)
        print(f"   Found {len(markets)} markets")
        
        for i, market in enumerate(markets[:3]):
            print(f"   Market {i+1}: {market.get('question', 'N/A')}")
            print(f"     ID: {market.get('id')}")
            print(f"     Condition ID: {market.get('conditionId')}")
            print(f"     Volume: {market.get('volumeClob', 0)}")
            print(f"     Active: {market.get('active', False)}")
            print()
    except Exception as e:
        print(f"   Error: {str(e)}")
        return
    
    # Test 3: Get active markets with volume
    print("3. Getting active markets with volume...")
    try:
        active_markets = service.get_active_markets_with_volume(min_volume=1000)
        print(f"   Found {len(active_markets)} active markets with volume > 1000")
        
        if active_markets:
            # Test price history for the first market with a conditionId
            test_market = None
            for market in active_markets:
                if market.get('conditionId'):
                    test_market = market
                    break
            
            if test_market:
                print(f"   Testing price history for: {test_market.get('question')}")
                print(f"   Condition ID: {test_market.get('conditionId')}")
                
                # Test price history
                history = service.get_market_price_history(test_market['conditionId'], "7d")
                print(f"   Retrieved {len(history)} price points for 7-day period")
                
                if history:
                    print("   Sample price points:")
                    for i, point in enumerate(history[:5]):
                        print(f"     {i+1}. Time: {point.get('datetime')}, Price: {point.get('value')}")
                    
                    if len(history) > 5:
                        print(f"     ... and {len(history) - 5} more points")
                else:
                    print("   No price history available")
            else:
                print("   No markets with conditionId found for testing")
        else:
            print("   No active markets with volume found")
            
    except Exception as e:
        print(f"   Error: {str(e)}")
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    test_graphql_api() 