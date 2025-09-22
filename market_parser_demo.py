#!/usr/bin/env python3
"""
Market Parser with Polygon MCP Server
A simple Python CLI for natural language financial queries using the Polygon.io MCP server and Anthropic Claude 4 via the Pydantic AI Agent Framework.
"""

import os
import sys
import asyncio
import math
from datetime import datetime, timedelta
from typing import Optional
from scipy.stats import norm
import numpy as np

import httpx
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

# Load environment variables
load_dotenv()

console = Console()

class MarketQuery(BaseModel):
    """Model for market query responses"""
    symbol: Optional[str] = None
    price: Optional[float] = None
    timestamp: Optional[str] = None
    response: str

class OptionsGreeks(BaseModel):
    """Model for options Greeks calculations"""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    implied_volatility: float

class BlackScholesCalculator:
    """Black-Scholes options pricing and Greeks calculator"""
    
    @staticmethod
    def calculate_greeks(
        spot_price: float,
        strike_price: float,
        time_to_expiry: float,  # in years
        risk_free_rate: float = 0.05,  # 5% default
        volatility: float = 0.25,  # 25% default if not provided
        option_type: str = "call"
    ) -> OptionsGreeks:
        """Calculate Black-Scholes Greeks"""
        
        # Calculate d1 and d2
        d1 = (math.log(spot_price / strike_price) + 
              (risk_free_rate + 0.5 * volatility**2) * time_to_expiry) / (volatility * math.sqrt(time_to_expiry))
        d2 = d1 - volatility * math.sqrt(time_to_expiry)
        
        # Standard normal CDF and PDF
        N_d1 = norm.cdf(d1)
        N_d2 = norm.cdf(d2)
        n_d1 = norm.pdf(d1)
        
        if option_type.lower() == "call":
            # Call option Greeks
            delta = N_d1
            theta = (-(spot_price * n_d1 * volatility) / (2 * math.sqrt(time_to_expiry)) -
                    risk_free_rate * strike_price * math.exp(-risk_free_rate * time_to_expiry) * N_d2) / 365
            rho = strike_price * time_to_expiry * math.exp(-risk_free_rate * time_to_expiry) * N_d2 / 100
        else:  # put option
            delta = N_d1 - 1
            theta = (-(spot_price * n_d1 * volatility) / (2 * math.sqrt(time_to_expiry)) +
                    risk_free_rate * strike_price * math.exp(-risk_free_rate * time_to_expiry) * (1 - N_d2)) / 365
            rho = -strike_price * time_to_expiry * math.exp(-risk_free_rate * time_to_expiry) * (1 - N_d2) / 100
        
        # Gamma and Vega are the same for calls and puts
        gamma = n_d1 / (spot_price * volatility * math.sqrt(time_to_expiry))
        vega = spot_price * n_d1 * math.sqrt(time_to_expiry) / 100
        
        return OptionsGreeks(
            delta=round(delta, 4),
            gamma=round(gamma, 4),
            theta=round(theta, 4),
            vega=round(vega, 4),
            rho=round(rho, 4),
            implied_volatility=volatility
        )

class PolygonMCPClient:
    """Client for interacting with Polygon.io API through MCP-like interface"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
        self.client = httpx.AsyncClient()
        self.bs_calculator = BlackScholesCalculator()
    
    async def get_stock_price(self, symbol: str) -> dict:
        """Get current stock price"""
        try:
            url = f"{self.base_url}/v2/aggs/ticker/{symbol}/prev"
            params = {"apikey": self.api_key}
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("results") and len(data["results"]) > 0:
                result = data["results"][0]
                return {
                    "symbol": symbol,
                    "price": result.get("c"),  # closing price
                    "volume": result.get("v"),
                    "timestamp": result.get("t")
                }
            return {"error": f"No data found for {symbol}"}
        except Exception as e:
            return {"error": f"Failed to get price for {symbol}: {str(e)}"}
    
    async def get_option_chain(self, symbol: str, expiration_date: Optional[str] = None) -> dict:
        """Get option chain data"""
        try:
            url = f"{self.base_url}/v3/reference/options/contracts"
            params = {
                "underlying_ticker": symbol,
                "apikey": self.api_key,
                "limit": 20
            }
            if expiration_date:
                params["expiration_date"] = expiration_date
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return {
                "symbol": symbol,
                "options": data.get("results", []),
                "count": len(data.get("results", []))
            }
        except Exception as e:
            return {"error": f"Failed to get option chain for {symbol}: {str(e)}"}
    
    async def get_today_date(self) -> str:
        """Get today's date"""
        return datetime.now().strftime("%Y-%m-%d")
    
    async def calculate_option_greeks(
        self, 
        symbol: str, 
        strike_price: float, 
        expiration_date: str,
        option_type: str = "call",
        volatility: Optional[float] = None
    ) -> dict:
        """Calculate Greeks for a specific option"""
        try:
            # Get current stock price
            stock_data = await self.get_stock_price(symbol)
            if "error" in stock_data:
                return stock_data
            
            spot_price = stock_data["price"]
            
            # Calculate time to expiry
            expiry = datetime.strptime(expiration_date, "%Y-%m-%d")
            today = datetime.now()
            time_to_expiry = (expiry - today).days / 365.0
            
            if time_to_expiry <= 0:
                return {"error": "Option has already expired"}
            
            # Use default volatility if not provided
            if volatility is None:
                volatility = 0.25  # 25% default
            
            # Calculate Greeks
            greeks = self.bs_calculator.calculate_greeks(
                spot_price=spot_price,
                strike_price=strike_price,
                time_to_expiry=time_to_expiry,
                volatility=volatility,
                option_type=option_type
            )
            
            return {
                "symbol": symbol,
                "strike_price": strike_price,
                "expiration_date": expiration_date,
                "option_type": option_type,
                "spot_price": spot_price,
                "time_to_expiry_days": round(time_to_expiry * 365),
                "greeks": greeks.dict(),
                "note": f"Greeks calculated using Black-Scholes model with {volatility*100}% volatility assumption"
            }
        except Exception as e:
            return {"error": f"Failed to calculate Greeks: {str(e)}"}
    
    async def analyze_option_strategy(self, symbol: str, strategy_type: str = "covered_call") -> dict:
        """Analyze common option strategies"""
        try:
            # Get current stock price and option chain
            stock_data = await self.get_stock_price(symbol)
            options_data = await self.get_option_chain(symbol)
            
            if "error" in stock_data or "error" in options_data:
                return {"error": "Could not fetch required data for strategy analysis"}
            
            spot_price = stock_data["price"]
            
            # Simple covered call analysis
            if strategy_type == "covered_call":
                # Find ATM and OTM call options
                analysis = {
                    "strategy": "Covered Call",
                    "current_stock_price": spot_price,
                    "recommendation": f"Consider selling call options with strikes 5-10% above current price (${spot_price * 1.05:.2f} - ${spot_price * 1.10:.2f})",
                    "risk": "Limited upside if stock rises above strike price",
                    "reward": "Premium income + potential capital gains up to strike price"
                }
                return analysis
            
            return {"error": f"Strategy type '{strategy_type}' not implemented yet"}
            
        except Exception as e:
            return {"error": f"Failed to analyze strategy: {str(e)}"}
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

class MarketParserAgent:
    """Main agent for processing market queries"""
    
    def __init__(self, anthropic_api_key: str, polygon_api_key: str):
        self.polygon_client = PolygonMCPClient(polygon_api_key)
        
        # Initialize the Anthropic model - API key is read from environment
        # Set the API key in environment for the model to use
        import os
        os.environ['ANTHROPIC_API_KEY'] = anthropic_api_key
        self.model = AnthropicModel('claude-3-5-sonnet-20241022')
        
        # System prompt for the agent
        system_prompt = (
            "You are an expert financial analyst and options trader. Note that when using Polygon tools, prices are already stock split adjusted. "
            "Use the latest data available. Always double check your math. "
            "For any questions about the current date, use the 'get_today_date' tool. "
            "For long or complex queries, break the query into logical subtasks and process each subtask in order. "
            "When asked about option chains, provide clear information about strikes, expirations, and pricing. "
            "You can calculate Greeks (delta, gamma, theta, vega, rho) using the Black-Scholes model with the 'calculate_option_greeks' tool. "
            "You can also analyze option strategies like covered calls using the 'analyze_option_strategy' tool. "
            "When calculating Greeks, always mention that they are theoretical values based on Black-Scholes assumptions."
        )
        
        # Create the agent
        self.agent = Agent(
            model=self.model,
            system_prompt=system_prompt,
            retries=2,
        )
        
        # Store polygon client reference for tools
        polygon_client = self.polygon_client
        
        # Define and register tools
        @self.agent.tool_plain
        async def get_stock_price(symbol: str) -> dict:
            """Get current stock price for a symbol"""
            return await polygon_client.get_stock_price(symbol.upper())
        
        @self.agent.tool_plain
        async def get_option_chain(symbol: str, expiration_date: Optional[str] = None) -> dict:
            """Get option chain for a symbol"""
            return await polygon_client.get_option_chain(symbol.upper(), expiration_date)
        
        @self.agent.tool_plain
        async def get_today_date() -> str:
            """Get today's date"""
            return await polygon_client.get_today_date()
        
        @self.agent.tool_plain
        async def calculate_option_greeks(
            symbol: str, 
            strike_price: float, 
            expiration_date: str,
            option_type: str = "call",
            volatility: Optional[float] = None
        ) -> dict:
            """Calculate Greeks (delta, gamma, theta, vega, rho) for a specific option using Black-Scholes model"""
            return await polygon_client.calculate_option_greeks(
                symbol, strike_price, expiration_date, option_type, volatility
            )
        
        @self.agent.tool_plain
        async def analyze_option_strategy(symbol: str, strategy_type: str = "covered_call") -> dict:
            """Analyze common option strategies like covered calls, protective puts, etc."""
            return await polygon_client.analyze_option_strategy(symbol, strategy_type)
    
    async def process_query(self, query: str) -> str:
        """Process a natural language market query"""
        try:
            result = await self.agent.run(query)
            return result.data if hasattr(result, 'data') else str(result)
        except Exception as e:
            return f"Error processing query: {str(e)}"
    
    async def close(self):
        """Close connections"""
        await self.polygon_client.close()

async def main():
    """Main CLI loop"""
    # Check for required API keys
    polygon_api_key = os.getenv("POLYGON_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not polygon_api_key:
        console.print("[red]Error: POLYGON_API_KEY not found in environment variables.[/red]")
        console.print("Please create a .env file with your API keys. See .env_example for reference.")
        return
    
    if not anthropic_api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY not found in environment variables.[/red]")
        console.print("Please create a .env file with your API keys. See .env_example for reference.")
        return
    
    # Initialize the agent
    agent = MarketParserAgent(anthropic_api_key, polygon_api_key)
    
    # Welcome message
    console.print(Panel.fit(
        Text("Market Parser with Polygon MCP Server", style="bold blue"),
        subtitle="Ask questions about stocks, options, and market data in natural language"
    ))
    
    console.print("\n[green]Examples:[/green]")
    console.print("• Tesla price now")
    console.print("• AAPL volume last week") 
    console.print("• Show me NVDA option chain")
    console.print("• SPY put options expiring this Friday")
    console.print("• Type 'exit' to quit\n")
    
    try:
        while True:
            try:
                # Get user input
                query = console.input("[bold cyan]> [/bold cyan]")
                
                if query.lower().strip() in ['exit', 'quit', 'q']:
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                
                if not query.strip():
                    continue
                
                # Process the query
                console.print("[dim]Processing...[/dim]")
                response = await agent.process_query(query)
                
                # Display the response
                console.print("✔ [green]Query processed successfully![/green]")
                console.print("\n[bold]Agent Response:[/bold]")
                console.print(response)
                console.print("-" * 50 + "\n")
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Goodbye![/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
    
    finally:
        await agent.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")
        sys.exit(0) 