#!/usr/bin/env python3
"""
Simple test script to verify API endpoints work correctly after OpenBanking spec updates
"""
import asyncio
import sys
import os
import json
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_endpoint(endpoint, method="GET", data=None, headers=None):
    """Test an endpoint and print results"""
    print(f"\n{'='*50}")
    print(f"Testing: {method} {endpoint}")
    print(f"{'='*50}")
    
    try:
        if method == "GET":
            response = client.get(endpoint, headers=headers or {})
        elif method == "POST":
            response = client.post(endpoint, json=data, headers=headers or {})
        elif method == "DELETE":
            response = client.delete(endpoint, headers=headers or {})
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code < 400:
            try:
                response_json = response.json()
                print("Response Structure:")
                print(json.dumps(response_json, indent=2))
                
                # Check for OpenBanking structure
                if "Data" in response_json:
                    print("✅ Contains 'Data' field (OpenBanking compliant)")
                else:
                    print("❌ Missing 'Data' field (not OpenBanking compliant)")
                
                if "Links" in response_json:
                    print("✅ Contains 'Links' field (OpenBanking compliant)")
                else:
                    print("❌ Missing 'Links' field (not OpenBanking compliant)")
                
                if "Meta" in response_json:
                    print("✅ Contains 'Meta' field (OpenBanking compliant)")
                else:
                    print("❌ Missing 'Meta' field (not OpenBanking compliant)")
                    
            except json.JSONDecodeError:
                print("❌ Response is not valid JSON")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def main():
    print("Testing API endpoints for OpenBanking compliance")
    print(f"Test started at: {datetime.now()}")
    
    # Test endpoints
    test_endpoint("/products")
    test_endpoint("/products/prod-vbank-deposit-001")
    
    # These would require authentication, but we can test the structure
    # test_endpoint("/accounts")
    # test_endpoint("/account-consents")
    # test_endpoint("/payments")
    # test_endpoint("/product-agreements")
    # test_endpoint("/vrp-consents")
    # test_endpoint("/domestic-vrp-payments")
    # test_endpoint("/product-offers")
    # test_endpoint("/customer-leads")
    
    print(f"\n{'='*50}")
    print("Test completed")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()