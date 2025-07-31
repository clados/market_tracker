#!/usr/bin/env python3
"""
Test the current price endpoint
"""

import requests
import json

def test_price_endpoint():
    """Test the current price endpoint you mentioned"""
    
    print("=== Testing Current Price Endpoint ===\n")
    
    # Test the example you provided
    token_id = "104922653398308252162693972588076790648474105976181114906086822751938769459610"
    
    print(f"Testing token ID: {token_id}")
    
    # Test buy side
    print("\n1. Testing buy side...")
    clob_url = "https://clob.polymarket.com/price"
    params = {
        "token_id": token_id,
        "side": "buy"
    }
    
    try:
        response = requests.get(clob_url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Buy Price Data: {json.dumps(data, indent=2)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {str(e)}")
    
    # Test sell side
    print("\n2. Testing sell side...")
    params["side"] = "sell"
    
    try:
        response = requests.get(clob_url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Sell Price Data: {json.dumps(data, indent=2)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {str(e)}")
    
    # Test different GraphQL endpoints
    print("\n3. Testing different GraphQL endpoints...")
    
    endpoints = [
        "https://gamma-api.polymarket.com/graphql",
        "https://api.polymarket.com/graphql",
        "https://polymarket.com/graphql",
        "https://gamma-api.polymarket.com/api/graphql"
    ]
    
    test_query = """
    query TestConnection {
        markets(limit: 1) {
            id
            question
        }
    }
    """
    
    for endpoint in endpoints:
        print(f"   Testing endpoint: {endpoint}")
        try:
            response = requests.post(endpoint, json={"query": test_query}, timeout=10)
            print(f"     Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"     Success! Found {len(data.get('data', {}).get('markets', []))} markets")
                break
            else:
                print(f"     Error: {response.text[:100]}")
        except Exception as e:
            print(f"     Exception: {str(e)}")
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    test_price_endpoint() 