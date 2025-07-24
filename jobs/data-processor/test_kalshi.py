#!/usr/bin/env python3
"""
Test script to verify KalshiService works correctly in the data-processor job.
Run this to test the Kalshi API connection before deploying the job.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the local KalshiService
from kalshi_service import KalshiService

def test_kalshi_connection():
    """Test Kalshi API connection"""
    try:
        print("Testing Kalshi API connection...")
        
        # Check environment variables
        key_id = os.getenv("KALSHI_KEY_ID")
        if not key_id:
            print("❌ KALSHI_KEY_ID environment variable not set")
            return False
        
        print(f"✅ KALSHI_KEY_ID found: {key_id[:8]}...")
        
        # Check for private key
        private_key = os.getenv("KALSHI_PRIVATE_KEY")
        if not private_key:
            print("❌ KALSHI_PRIVATE_KEY environment variable not set")
            return False
        
        print("✅ KALSHI_PRIVATE_KEY found")
        
        # Test KalshiService
        kalshi_service = KalshiService()
        
        # Test connection
        connection_test = kalshi_service.test_connection()
        if connection_test["success"]:
            print("✅ Kalshi API connection successful")
            
            # Test getting markets
            markets_response = kalshi_service.get_markets(limit=5)
            markets = markets_response.get("markets", [])
            print(f"✅ Retrieved {len(markets)} markets from Kalshi API")
            
            if markets:
                print(f"Sample market: {markets[0].get('title', 'N/A')}")
            
            return True
        else:
            print(f"❌ Kalshi API connection failed: {connection_test['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Kalshi connection: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_kalshi_connection()
    sys.exit(0 if success else 1) 