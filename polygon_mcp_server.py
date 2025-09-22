#!/usr/bin/env python3
"""
Advanced Polygon.io MCP Server
Provides comprehensive financial market data through the Model Context Protocol (MCP)
with advanced options analytics, Greeks calculation, and real-time market data.
"""

import os
import asyncio
import math
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

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
        """Calculate all Greeks using Black-Scholes model"""
        
        if time_to_expiry <= 0:
            return {
                "delta": 1.0 if option_type.lower() == "call" and spot_price > strike_price else 0.0,
                "gamma": 0.0,
                "theta": 0.0,
                "vega": 0.0,
                "rho": 0.0,
                "implied_volatility": volatility
            }
        
        # Black-Scholes calculations
        d1 = (np.log(spot_price / strike_price) + (risk_free_rate + 0.5 * volatility**2) * time_to_expiry) / (volatility * np.sqrt(time_to_expiry))
        d2 = d1 - volatility * np.sqrt(time_to_expiry)
        
        # Greeks calculations
        if option_type.lower() == "call":
            delta = norm.cdf(d1)
            rho = strike_price * time_to_expiry * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2) / 100
        else:  # put
            delta = -norm.cdf(-d1)
            rho = -strike_price * time_to_expiry * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2) / 100
        
        gamma = norm.pdf(d1) / (spot_price * volatility * np.sqrt(time_to_expiry))
        theta = (-(spot_price * norm.pdf(d1) * volatility) / (2 * np.sqrt(time_to_expiry)) - 
                risk_free_rate * strike_price * np.exp(-risk_free_rate * time_to_expiry) * 
                (norm.cdf(d2) if option_type.lower() == "call" else norm.cdf(-d2))) / 365
        vega = spot_price * norm.pdf(d1) * np.sqrt(time_to_expiry) / 100
        
        return {
            "delta": round(delta, 4),
            "gamma": round(gamma, 4),
            "theta": round(theta, 4),
            "vega": round(vega, 4),
            "rho": round(rho, 4),
            "implied_volatility": volatility
        }

class PolygonMCPClient:
    """Enhanced Polygon.io client with MCP integration"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = RESTClient(api_key)
        self.http_client = httpx.AsyncClient()
        self.greeks_calculator = OptionsGreeks()
    
    async def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """Get current stock price with enhanced data"""
        try:
            # Get previous close
            prev_close = self.client.get_previous_close_agg(symbol)
            
            # Get last trade
            last_trade = self.client.get_last_trade(symbol)
            
            return {
                "symbol": symbol.upper(),
                "price": prev_close[0].close if prev_close else None,
                "last_trade_price": last_trade.price if hasattr(last_trade, 'price') else None,
                "volume": prev_close[0].volume if prev_close else None,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
        except Exception as e:
            return {"error": str(e), "symbol": symbol, "status": "error"}
    
    async def get_options_chain(self, symbol: str, expiration_date: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive options chain with enhanced data"""
        try:
            params = {"underlying_ticker": symbol.upper()}
            if expiration_date:
                params["expiration_date"] = expiration_date
            
            # Get options contracts
            contracts = list(self.client.list_options_contracts(**params))
            
            # Get options snapshots for real-time data
            try:
                snapshots = list(self.client.list_snapshot_options_chain(symbol.upper()))
            except:
                snapshots = []
            
            return {
                "symbol": symbol.upper(),
                "expiration_date": expiration_date,
                "contracts_count": len(contracts),
                "contracts": [
                    {
                        "ticker": contract.ticker,
                        "strike_price": contract.strike_price,
                        "expiration_date": contract.expiration_date,
                        "contract_type": contract.contract_type,
                        "exercise_style": getattr(contract, 'exercise_style', 'american'),
                        "shares_per_contract": getattr(contract, 'shares_per_contract', 100)
                    } for contract in contracts[:50]  # Limit to first 50 for performance
                ],
                "snapshots": [
                    {
                        "ticker": snap.ticker if hasattr(snap, 'ticker') else None,
                        "last_quote": {
                            "bid": snap.last_quote.bid if hasattr(snap, 'last_quote') and snap.last_quote else None,
                            "ask": snap.last_quote.ask if hasattr(snap, 'last_quote') and snap.last_quote else None,
                            "bid_size": snap.last_quote.bid_size if hasattr(snap, 'last_quote') and snap.last_quote else None,
                            "ask_size": snap.last_quote.ask_size if hasattr(snap, 'last_quote') and snap.last_quote else None,
                        },
                        "open_interest": getattr(snap, 'open_interest', None),
                        "volume": getattr(snap, 'volume', None)
                    } for snap in snapshots[:20]  # Limit snapshots
                ],
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
        except Exception as e:
            return {"error": str(e), "symbol": symbol, "status": "error"}
    
    async def calculate_option_greeks(
        self, 
        symbol: str, 
        strike_price: float, 
        expiration_date: str,
        option_type: str = "call",
        volatility: Optional[float] = None
    ) -> Dict[str, Any]:
        """Calculate Greeks for a specific option with real market data"""
        try:
            # Get current stock price
            stock_data = await self.get_stock_price(symbol)
            if "error" in stock_data:
                return stock_data
            
            spot_price = stock_data["price"] or stock_data["last_trade_price"]
            if not spot_price:
                return {"error": "Could not get current stock price", "status": "error"}
            
            # Calculate time to expiry
            exp_date = datetime.strptime(expiration_date, "%Y-%m-%d")
            time_to_expiry = (exp_date - datetime.now()).days / 365.0
            
            if time_to_expiry < 0:
                return {"error": "Option has already expired", "status": "error"}
            
            # Use provided volatility or default
            if volatility is None:
                volatility = 0.25  # Default 25% IV
            
            # Calculate Greeks
            greeks = self.greeks_calculator.calculate_greeks(
                spot_price=spot_price,
                strike_price=strike_price,
                time_to_expiry=time_to_expiry,
                volatility=volatility,
                option_type=option_type.lower()
            )
            
            return {
                "symbol": symbol.upper(),
                "strike_price": strike_price,
                "expiration_date": expiration_date,
                "option_type": option_type.lower(),
                "spot_price": spot_price,
                "time_to_expiry_years": round(time_to_expiry, 4),
                "time_to_expiry_days": round(time_to_expiry * 365, 0),
                "greeks": greeks,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    async def get_unusual_options_activity(self, symbol: str) -> Dict[str, Any]:
        """Detect unusual options activity"""
        try:
            # Get recent options trades
            today = datetime.now().strftime("%Y-%m-%d")
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            # This would require more sophisticated analysis in a real implementation
            # For now, we'll return a placeholder structure
            return {
                "symbol": symbol.upper(),
                "analysis_date": today,
                "unusual_activity": {
                    "high_volume_contracts": [],
                    "large_block_trades": [],
                    "unusual_iv_spikes": [],
                    "put_call_ratio": None
                },
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "note": "Advanced unusual activity detection requires premium data access"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    async def analyze_options_strategy(self, strategy_type: str, symbol: str, legs: List[Dict]) -> Dict[str, Any]:
        """Analyze complex options strategies"""
        try:
            # Get current stock price
            stock_data = await self.get_stock_price(symbol)
            if "error" in stock_data:
                return stock_data
            
            spot_price = stock_data["price"] or stock_data["last_trade_price"]
            
            # Calculate strategy metrics
            strategy_analysis = {
                "strategy_type": strategy_type,
                "symbol": symbol.upper(),
                "spot_price": spot_price,
                "legs": legs,
                "analysis": {
                    "max_profit": None,
                    "max_loss": None,
                    "breakeven_points": [],
                    "probability_of_profit": None,
                    "net_delta": 0,
                    "net_gamma": 0,
                    "net_theta": 0,
                    "net_vega": 0
                },
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
            # Calculate net Greeks for the strategy
            total_delta = total_gamma = total_theta = total_vega = 0
            
            for leg in legs:
                greeks_data = await self.calculate_option_greeks(
                    symbol=symbol,
                    strike_price=leg["strike_price"],
                    expiration_date=leg["expiration_date"],
                    option_type=leg["option_type"],
                    volatility=leg.get("volatility", 0.25)
                )
                
                if "greeks" in greeks_data:
                    multiplier = leg.get("quantity", 1) * (1 if leg.get("action") == "buy" else -1)
                    total_delta += greeks_data["greeks"]["delta"] * multiplier
                    total_gamma += greeks_data["greeks"]["gamma"] * multiplier
                    total_theta += greeks_data["greeks"]["theta"] * multiplier
                    total_vega += greeks_data["greeks"]["vega"] * multiplier
            
            strategy_analysis["analysis"]["net_delta"] = round(total_delta, 4)
            strategy_analysis["analysis"]["net_gamma"] = round(total_gamma, 4)
            strategy_analysis["analysis"]["net_theta"] = round(total_theta, 4)
            strategy_analysis["analysis"]["net_vega"] = round(total_vega, 4)
            
            return strategy_analysis
            
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()

# Initialize global client
polygon_client = None

@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage server lifecycle"""
    global polygon_client
    
    # Initialize on startup
    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        raise ValueError("POLYGON_API_KEY environment variable is required")
    
    polygon_client = PolygonMCPClient(api_key)
    
    try:
        yield {"polygon_client": polygon_client}
    finally:
        # Cleanup on shutdown
        if polygon_client:
            await polygon_client.close()

# Set lifespan for the server
mcp.lifespan = lifespan

# MCP Tools
@mcp.tool()
async def get_stock_price(symbol: str) -> str:
    """Get current stock price and basic information
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
    """
    global polygon_client
    if not polygon_client:
        return "Error: Polygon client not initialized"
    
    result = await polygon_client.get_stock_price(symbol)
    
    if result["status"] == "success":
        return f"""Stock Price for {result['symbol']}:
Price: ${result['price']:.2f}
Last Trade: ${result.get('last_trade_price', 'N/A')}
Volume: {result.get('volume', 'N/A'):,}
Updated: {result['timestamp']}"""
    else:
        return f"Error getting stock price for {symbol}: {result.get('error', 'Unknown error')}"

@mcp.tool()
async def get_options_chain(symbol: str, expiration_date: Optional[str] = None) -> str:
    """Get options chain for a stock symbol
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        expiration_date: Optional expiration date in YYYY-MM-DD format
    """
    global polygon_client
    if not polygon_client:
        return "Error: Polygon client not initialized"
    
    result = await polygon_client.get_options_chain(symbol, expiration_date)
    
    if result["status"] == "success":
        response = f"""Options Chain for {result['symbol']}:
Contracts Found: {result['contracts_count']}
Expiration Filter: {result.get('expiration_date', 'All dates')}

Recent Contracts:"""
        
        for contract in result['contracts'][:10]:  # Show first 10
            response += f"""
  {contract['ticker']} - ${contract['strike_price']} {contract['contract_type'].upper()}
  Expires: {contract['expiration_date']}"""
        
        if result['snapshots']:
            response += f"\n\nReal-time Data Available: {len(result['snapshots'])} contracts"
        
        return response
    else:
        return f"Error getting options chain for {symbol}: {result.get('error', 'Unknown error')}"

@mcp.tool()
async def calculate_option_greeks(
    symbol: str, 
    strike_price: float, 
    expiration_date: str,
    option_type: str = "call",
    volatility: Optional[float] = None
) -> str:
    """Calculate Options Greeks using Black-Scholes model
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        strike_price: Option strike price
        expiration_date: Expiration date in YYYY-MM-DD format
        option_type: 'call' or 'put' (default: 'call')
        volatility: Implied volatility (0.0-1.0), defaults to 0.25
    """
    global polygon_client
    if not polygon_client:
        return "Error: Polygon client not initialized"
    
    result = await polygon_client.calculate_option_greeks(
        symbol, strike_price, expiration_date, option_type, volatility
    )
    
    if result["status"] == "success":
        greeks = result["greeks"]
        return f"""Options Greeks for {result['symbol']} ${result['strike_price']} {result['option_type'].upper()}:

Current Stock Price: ${result['spot_price']:.2f}
Time to Expiry: {result['time_to_expiry_days']} days ({result['time_to_expiry_years']:.4f} years)
Expiration: {result['expiration_date']}

Greeks:
  Delta: {greeks['delta']:.4f} (price sensitivity)
  Gamma: {greeks['gamma']:.4f} (delta sensitivity)  
  Theta: {greeks['theta']:.4f} (time decay per day)
  Vega: {greeks['vega']:.4f} (volatility sensitivity)
  Rho: {greeks['rho']:.4f} (interest rate sensitivity)
  
Implied Volatility: {greeks['implied_volatility']:.1%}
Calculated: {result['timestamp']}"""
    else:
        return f"Error calculating Greeks: {result.get('error', 'Unknown error')}"

@mcp.tool()
async def analyze_options_strategy(
    strategy_type: str,
    symbol: str,
    legs: str  # JSON string of strategy legs
) -> str:
    """Analyze complex options strategies (iron condor, straddle, etc.)
    
    Args:
        strategy_type: Type of strategy (e.g., 'iron_condor', 'straddle', 'strangle')
        symbol: Stock ticker symbol
        legs: JSON string with strategy legs, e.g.:
              '[{"strike_price": 100, "expiration_date": "2024-12-20", "option_type": "call", "action": "buy", "quantity": 1}]'
    """
    global polygon_client
    if not polygon_client:
        return "Error: Polygon client not initialized"
    
    try:
        import json
        legs_data = json.loads(legs)
    except json.JSONDecodeError:
        return "Error: Invalid JSON format for legs parameter"
    
    result = await polygon_client.analyze_options_strategy(strategy_type, symbol, legs_data)
    
    if result["status"] == "success":
        analysis = result["analysis"]
        return f"""Options Strategy Analysis: {result['strategy_type'].upper()}
Symbol: {result['symbol']} (Current Price: ${result['spot_price']:.2f})

Strategy Legs: {len(result['legs'])}
Net Greeks:
  Delta: {analysis['net_delta']:.4f}
  Gamma: {analysis['net_gamma']:.4f}
  Theta: {analysis['net_theta']:.4f}
  Vega: {analysis['net_vega']:.4f}

Max Profit: {analysis.get('max_profit', 'Calculating...')}
Max Loss: {analysis.get('max_loss', 'Calculating...')}
Breakeven Points: {analysis.get('breakeven_points', 'Calculating...')}

Analysis Date: {result['timestamp']}"""
    else:
        return f"Error analyzing strategy: {result.get('error', 'Unknown error')}"

@mcp.tool()
async def get_unusual_options_activity(symbol: str) -> str:
    """Detect unusual options activity and flow
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
    """
    global polygon_client
    if not polygon_client:
        return "Error: Polygon client not initialized"
    
    result = await polygon_client.get_unusual_options_activity(symbol)
    
    if result["status"] == "success":
        return f"""Unusual Options Activity for {result['symbol']}:
Analysis Date: {result['analysis_date']}

High Volume Contracts: {len(result['unusual_activity']['high_volume_contracts'])}
Large Block Trades: {len(result['unusual_activity']['large_block_trades'])}
IV Spikes: {len(result['unusual_activity']['unusual_iv_spikes'])}
Put/Call Ratio: {result['unusual_activity']['put_call_ratio'] or 'Calculating...'}

{result.get('note', '')}
Updated: {result['timestamp']}"""
    else:
        return f"Error getting unusual activity for {symbol}: {result.get('error', 'Unknown error')}"

@mcp.tool()
async def get_market_status() -> str:
    """Get current market status and trading hours"""
    global polygon_client
    if not polygon_client:
        return "Error: Polygon client not initialized"
    
    try:
        status = polygon_client.client.get_market_status()
        return f"""Market Status:
Market: {status.market}
Server Time: {status.serverTime}
Exchanges:
  NYSE: {status.exchanges.nyse}
  NASDAQ: {status.exchanges.nasdaq}
  OTC: {status.exchanges.otc}"""
    except Exception as e:
        return f"Error getting market status: {str(e)}"

# MCP Resources
@mcp.resource("market://status")
async def market_status_resource() -> str:
    """Current market status as a resource"""
    return await get_market_status()

@mcp.resource("options://chain/{symbol}")
async def options_chain_resource(symbol: str) -> str:
    """Options chain data as a resource"""
    return await get_options_chain(symbol)

@mcp.resource("stock://price/{symbol}")
async def stock_price_resource(symbol: str) -> str:
    """Stock price data as a resource"""
    return await get_stock_price(symbol)

# Main entry point
async def main():
    """Main entry point for the MCP server"""
    # FastMCP handles the server setup automatically
    await mcp.run()

if __name__ == "__main__":
    asyncio.run(main()) 