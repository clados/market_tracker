#!/usr/bin/env python3
"""
Test the working Polymarket API example
"""

import requests
import json

def test_working_example():
    """Test the working example from the documentation"""
    
    api_url = "https://gamma-api.polymarket.com/graphql"
    market_slug = "will-the-fed-hike-by-at-least-25bps-on-or-before-the-dec-2024-fomc-meeting"
    
    print("=== Testing Working Polymarket API Example ===\n")
    
    # Step 1: Get Market Info (including conditionId)
    print("1. Getting market info...")
    info_query = """
        query GetMarket($slug: String!) {
            market(slug: $slug) {
                question
                conditionId
                questionId
            }
        }
    """
    
    try:
        response = requests.post(api_url, json={"query": info_query, "variables": {"slug": market_slug}})
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response data: {json.dumps(data, indent=2)}")
            
            if 'data' in data and 'market' in data['data']:
                market_data = data['data']['market']
                condition_id = market_data['conditionId']
                
                print(f"   Market Question: {market_data['question']}")
                print(f"   Condition ID: {condition_id}")
                print()
                
                # Step 2: Get Price History using the conditionId
                print("2. Getting price history...")
                price_history_query = """
                    query GetMarketPriceChart($conditionId: String!, $period: ChartPeriod!) {
                        getMarketPriceChart(conditionId: $conditionId, period: $period) {
                            prices {
                                time
                                value
                            }
                        }
                    }
                """
                
                variables = {
                    "conditionId": condition_id,
                    "period": "7d"
                }
                
                response = requests.post(api_url, json={"query": price_history_query, "variables": variables})
                print(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   Response data: {json.dumps(data, indent=2)}")
                    
                    if 'data' in data and 'getMarketPriceChart' in data['data']:
                        price_data = data['data']['getMarketPriceChart']['prices']
                        
                        print(f"\n   Retrieved {len(price_data)} price points")
                        
                        # Print the first 5 and last 5 data points
                        print("\n   --- First 5 Price Points ---")
                        for i, point in enumerate(price_data[:5]):
                            print(f"   {i+1}. Time: {point['time']}, Price: {point['value']}")
                        
                        if len(price_data) > 10:
                            print("   ...")
                            print("   --- Last 5 Price Points ---")
                            for i, point in enumerate(price_data[-5:]):
                                print(f"   {len(price_data)-4+i}. Time: {point['time']}, Price: {point['value']}")
                        elif len(price_data) > 5:
                            print("   --- Remaining Price Points ---")
                            for i, point in enumerate(price_data[5:]):
                                print(f"   {i+6}. Time: {point['time']}, Price: {point['value']}")
                    else:
                        print("   No price data found in response")
                else:
                    print(f"   Error response: {response.text}")
            else:
                print("   No market data found in response")
        else:
            print(f"   Error response: {response.text}")
            
    except Exception as e:
        print(f"   Exception: {str(e)}")
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    test_working_example() 