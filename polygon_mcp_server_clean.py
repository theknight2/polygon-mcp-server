#!/usr/bin/env python3
"""
Advanced Polygon.io MCP Server - Clean Version
Provides comprehensive financial market data through the Model Context Protocol (MCP)
with advanced options analytics, Greeks calculation, and real-time market data.
"""

import os
import math
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

import httpx
import numpy as np
from scipy.stats import norm
from dotenv import load_dotenv
from polygon import RESTClient
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("Polygon.io Advanced Options MCP Server")

class OptionsGreeks:
    """Advanced Options Greeks calculator using Black-Scholes model"""
    
    @staticmethod
    def calculate_greeks(
        spot_price: float,
        strike_price: float,
        time_to_expiry: float,  # in years
        risk_free_rate: float = 0.05,
        volatility: float = 0.25,
        option_type: str = "call"
    ) -> Dict[str, float]:
        
        # Black-Scholes calculations
        d1 = (np.log(spot_price / strike_price) + (risk_free_rate + 0.5 * volatility**2) * time_to_expiry) / (volatility * np.sqrt(time_to_expiry))
        d2 = d1 - volatility * np.sqrt(time_to_expiry)
        
        # Greeks calculations
        if option_type.lower() == "call":
            delta = norm.cdf(d1)
            theta = (-spot_price * norm.pdf(d1) * volatility / (2 * np.sqrt(time_to_expiry)) 
                    - risk_free_rate * strike_price * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2)) / 365
        else:  # put
            delta = norm.cdf(d1) - 1
            theta = (-spot_price * norm.pdf(d1) * volatility / (2 * np.sqrt(time_to_expiry)) 
                    + risk_free_rate * strike_price * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2)) / 365
        
        gamma = norm.pdf(d1) / (spot_price * volatility * np.sqrt(time_to_expiry))
        vega = spot_price * norm.pdf(d1) * np.sqrt(time_to_expiry) / 100
        rho = (strike_price * time_to_expiry * np.exp(-risk_free_rate * time_to_expiry) * 
               (norm.cdf(d2) if option_type.lower() == "call" else norm.cdf(-d2))) / 100
        
        return {
            "delta": round(delta, 4),
            "gamma": round(gamma, 4),
            "theta": round(theta, 4),
            "vega": round(vega, 4),
            "rho": round(rho, 4)
        }

class PolygonMCPClient:
    """Enhanced Polygon.io client with advanced options analytics"""
    
    def __init__(self):
        self.api_key = os.getenv("POLYGON_API_KEY")
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY environment variable is required")
        
        self.client = RESTClient(self.api_key)
        self.http_client = httpx.AsyncClient()
    
    async def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """Get current stock price and basic information"""
        try:
            # Get previous close data
            prev_close = self.client.get_previous_close_agg(symbol)
            
            # Get last trade
            last_trade = self.client.get_last_trade(symbol)
            
            return {
                "symbol": symbol.upper(),
                "current_price": last_trade.price if last_trade else prev_close[0].close,
                "previous_close": prev_close[0].close,
                "volume": prev_close[0].volume,
                "change": round((last_trade.price - prev_close[0].close) if last_trade else 0, 2),
                "change_percent": round(((last_trade.price - prev_close[0].close) / prev_close[0].close * 100) if last_trade else 0, 2),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Failed to get stock price: {str(e)}"}
    
    async def get_options_chain(self, symbol: str, expiration_date: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive options chain data"""
        try:
            # Get options contracts
            contracts = list(self.client.list_options_contracts(
                underlying_ticker=symbol,
                expiration_date=expiration_date,
                limit=100
            ))
            
            if not contracts:
                return {"error": f"No options contracts found for {symbol}"}
            
            # Get current stock price for context
            stock_data = await self.get_stock_price(symbol)
            
            options_data = []
            for contract in contracts:
                try:
                    # Get option snapshot
                    snapshot = self.client.get_snapshot_option(contract.ticker)
                    
                    option_info = {
                        "contract_ticker": contract.ticker,
                        "strike_price": contract.strike_price,
                        "expiration_date": contract.expiration_date,
                        "option_type": contract.contract_type,
                        "last_price": snapshot.last_quote.bid if snapshot.last_quote else None,
                        "bid": snapshot.last_quote.bid if snapshot.last_quote else None,
                        "ask": snapshot.last_quote.ask if snapshot.last_quote else None,
                        "volume": snapshot.day.volume if snapshot.day else 0,
                        "open_interest": snapshot.open_interest if hasattr(snapshot, 'open_interest') else None
                    }
                    options_data.append(option_info)
                except Exception as e:
                    continue
            
            return {
                "symbol": symbol.upper(),
                "stock_price": stock_data.get("current_price"),
                "options_count": len(options_data),
                "options": options_data[:50],  # Limit to first 50 for readability
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Failed to get options chain: {str(e)}"}
    
    async def calculate_option_greeks(
        self, 
        symbol: str, 
        strike_price: float, 
        expiration_date: str,
        option_type: str = "call",
        volatility: Optional[float] = None
    ) -> Dict[str, Any]:
        """Calculate Options Greeks using Black-Scholes model"""
        try:
            # Get current stock price
            stock_data = await self.get_stock_price(symbol)
            if "error" in stock_data:
                return stock_data
            
            spot_price = stock_data["current_price"]
            
            # Calculate time to expiry
            exp_date = datetime.strptime(expiration_date, "%Y-%m-%d")
            time_to_expiry = (exp_date - datetime.now()).days / 365.0
            
            if time_to_expiry <= 0:
                return {"error": "Option has already expired"}
            
            # Use provided volatility or default
            vol = volatility or 0.25
            
            # Calculate Greeks
            greeks = OptionsGreeks.calculate_greeks(
                spot_price=spot_price,
                strike_price=strike_price,
                time_to_expiry=time_to_expiry,
                volatility=vol,
                option_type=option_type
            )
            
            return {
                "symbol": symbol.upper(),
                "spot_price": spot_price,
                "strike_price": strike_price,
                "expiration_date": expiration_date,
                "time_to_expiry_days": round(time_to_expiry * 365),
                "option_type": option_type,
                "volatility": vol,
                "greeks": greeks,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Failed to calculate Greeks: {str(e)}"}
    
    async def get_market_status(self) -> Dict[str, Any]:
        """Get current market status"""
        try:
            status = self.client.get_market_status()
            return {
                "market": status.market,
                "server_time": status.server_time,
                "exchanges": {
                    exchange.name: {
                        "status": exchange.status,
                        "reason": getattr(exchange, 'reason', None)
                    } for exchange in status.exchanges
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Failed to get market status: {str(e)}"}

# Initialize the client
polygon_client = PolygonMCPClient()

# MCP Tools
@mcp.tool()
async def get_stock_price(symbol: str) -> str:
    """Get current stock price and basic information for a given symbol"""
    result = await polygon_client.get_stock_price(symbol)
    return str(result)

@mcp.tool()
async def get_options_chain(symbol: str, expiration_date: Optional[str] = None) -> str:
    """Get options chain data for a stock symbol. Optionally filter by expiration date (YYYY-MM-DD)"""
    result = await polygon_client.get_options_chain(symbol, expiration_date)
    return str(result)

@mcp.tool()
async def calculate_option_greeks(
    symbol: str, 
    strike_price: float, 
    expiration_date: str,
    option_type: str = "call",
    volatility: Optional[float] = None
) -> str:
    """Calculate Options Greeks (Delta, Gamma, Theta, Vega, Rho) for an option using Black-Scholes model"""
    result = await polygon_client.calculate_option_greeks(symbol, strike_price, expiration_date, option_type, volatility)
    return str(result)

@mcp.tool()
async def get_market_status() -> str:
    """Get current market status and trading hours"""
    result = await polygon_client.get_market_status()
    return str(result)

# MCP Resources
@mcp.resource("market://status")
async def market_status_resource() -> str:
    """Current market status and trading hours"""
    return await get_market_status()

@mcp.resource("options://chain/{symbol}")
async def options_chain_resource(symbol: str) -> str:
    """Options chain data for the specified symbol"""
    return await get_options_chain(symbol)

@mcp.resource("stock://price/{symbol}")
async def stock_price_resource(symbol: str) -> str:
    """Stock price data as a resource"""
    return await get_stock_price(symbol)

# Add health check endpoint using FastMCP custom route
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request) -> dict:
    """Health check endpoint for cloud deployment"""
    return {"status": "healthy", "service": "polygon-mcp-server"}

# Main entry point - simplified for MCP Inspector compatibility
if __name__ == "__main__":
    # This will be handled by FastMCP's run system
    pass 