#!/usr/bin/env python3
"""
Test script for the Polygon MCP Server
"""

import asyncio
import os
from polygon_mcp_server import mcp, polygon_client, PolygonMCPClient

async def test_mcp_server():
    """Test the MCP server functionality"""
    print("🧪 Testing Polygon MCP Server...")
    
    # Test 1: Check if API key is available
    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        print("❌ POLYGON_API_KEY not found in environment")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Test 2: Initialize client
    try:
        test_client = PolygonMCPClient(api_key)
        print("✅ Polygon client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False
    
    # Test 3: Test stock price function
    try:
        result = await test_client.get_stock_price("AAPL")
        if result["status"] == "success":
            print(f"✅ Stock price test passed: AAPL = ${result.get('price', 'N/A')}")
        else:
            print(f"⚠️ Stock price test returned error: {result.get('error')}")
    except Exception as e:
        print(f"❌ Stock price test failed: {e}")
    
    # Test 4: Test Greeks calculation
    try:
        result = await test_client.calculate_option_greeks(
            symbol="AAPL",
            strike_price=150.0,
            expiration_date="2024-12-20",
            option_type="call"
        )
        if result["status"] == "success":
            print(f"✅ Greeks calculation test passed: Delta = {result['greeks']['delta']}")
        else:
            print(f"⚠️ Greeks calculation returned error: {result.get('error')}")
    except Exception as e:
        print(f"❌ Greeks calculation test failed: {e}")
    
    # Test 5: Test options chain
    try:
        result = await test_client.get_options_chain("AAPL")
        if result["status"] == "success":
            print(f"✅ Options chain test passed: {result['contracts_count']} contracts found")
        else:
            print(f"⚠️ Options chain returned error: {result.get('error')}")
    except Exception as e:
        print(f"❌ Options chain test failed: {e}")
    
    # Cleanup
    await test_client.close()
    print("✅ Client closed successfully")
    
    print("\n🎉 MCP Server tests completed!")
    return True

if __name__ == "__main__":
    asyncio.run(test_mcp_server()) 