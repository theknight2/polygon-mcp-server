#!/usr/bin/env python3
"""
Advanced Polygon.io MCP Server - STDIO Version
Provides comprehensive financial market data through the Model Context Protocol (MCP)
with advanced options analytics, Greeks calculation, and real-time market data.
"""

import asyncio
import os
import math
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

import httpx
import numpy as np
from scipy.stats import norm
from dotenv import load_dotenv
from polygon import RESTClient

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

# Load environment variables
load_dotenv()

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

# Initialize the server and client
server = Server("polygon-mcp-server")
polygon_client = PolygonMCPClient()

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="get_stock_price",
            description="Get current stock price and basic information for a given symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., AAPL, TSLA)"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_options_chain",
            description="Get options chain data for a stock symbol. Optionally filter by expiration date",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., AAPL, TSLA)"
                    },
                    "expiration_date": {
                        "type": "string",
                        "description": "Optional expiration date in YYYY-MM-DD format"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="calculate_option_greeks",
            description="Calculate Options Greeks (Delta, Gamma, Theta, Vega, Rho) using Black-Scholes model",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., AAPL, TSLA)"
                    },
                    "strike_price": {
                        "type": "number",
                        "description": "Option strike price"
                    },
                    "expiration_date": {
                        "type": "string",
                        "description": "Expiration date in YYYY-MM-DD format"
                    },
                    "option_type": {
                        "type": "string",
                        "description": "Option type: 'call' or 'put'",
                        "enum": ["call", "put"]
                    },
                    "volatility": {
                        "type": "number",
                        "description": "Optional implied volatility (default: 0.25)"
                    }
                },
                "required": ["symbol", "strike_price", "expiration_date"]
            }
        ),
        Tool(
            name="get_market_status",
            description="Get current market status and trading hours",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    try:
        if name == "get_stock_price":
            result = await polygon_client.get_stock_price(arguments["symbol"])
        elif name == "get_options_chain":
            result = await polygon_client.get_options_chain(
                arguments["symbol"], 
                arguments.get("expiration_date")
            )
        elif name == "calculate_option_greeks":
            result = await polygon_client.calculate_option_greeks(
                arguments["symbol"],
                arguments["strike_price"],
                arguments["expiration_date"],
                arguments.get("option_type", "call"),
                arguments.get("volatility")
            )
        elif name == "get_market_status":
            result = await polygon_client.get_market_status()
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        return [TextContent(type="text", text=str(result))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available resources"""
    return [
        Resource(
            uri="market://status",
            name="Market Status",
            description="Current market status and trading hours",
            mimeType="application/json"
        ),
        Resource(
            uri="options://chain/{symbol}",
            name="Options Chain",
            description="Options chain data for a given symbol",
            mimeType="application/json"
        ),
        Resource(
            uri="stock://price/{symbol}",
            name="Stock Price",
            description="Current stock price and information",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Handle resource reads"""
    try:
        if uri == "market://status":
            result = await polygon_client.get_market_status()
        elif uri.startswith("options://chain/"):
            symbol = uri.split("/")[-1]
            result = await polygon_client.get_options_chain(symbol)
        elif uri.startswith("stock://price/"):
            symbol = uri.split("/")[-1]
            result = await polygon_client.get_stock_price(symbol)
        else:
            result = {"error": f"Unknown resource: {uri}"}
        
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

async def main():
    """Main entry point"""
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main()) 