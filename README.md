# 🚀 Advanced Polygon.io MCP Server

A comprehensive **Model Context Protocol (MCP) server** that provides advanced financial market data through Polygon.io's API, featuring sophisticated options analytics, Greeks calculation, and real-time market data.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/polygon-mcp-server)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## ⚡ **Quick Deploy (1-Click)**

### **Railway (Recommended - Free)**
1. Click: [![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)
2. Connect your GitHub account
3. Set environment variable: `POLYGON_API_KEY=your_api_key_here`
4. Deploy! Your URL: `https://your-app.railway.app/sse`

### **Render (Alternative - Free)**
1. Fork this repository
2. Go to [Render.com](https://render.com)
3. New → Web Service → Connect GitHub
4. Build: `uv sync` | Start: `uv run polygon_mcp_server_sse.py`
5. Set: `POLYGON_API_KEY=your_api_key_here`

## 🎯 **For Scira MCP Chat**

Once deployed, connect to Scira using:
- **SSE Endpoint**: `https://your-domain.com/sse`
- **Environment Variable**: `API_KEY=your_polygon_api_key`

## 🚀 **Features**

### **Core Market Data**
- **Real-time Stock Prices** - Current prices, volume, and trade data
- **Options Chain Data** - Comprehensive options contracts with real-time quotes
- **Market Status** - Trading hours and exchange status
- **Historical Data** - Access to 15+ years of market history

### **Advanced Options Analytics**
- **Greeks Calculation** - Delta, Gamma, Theta, Vega, Rho using Black-Scholes
- **Options Strategy Analysis** - Iron condors, straddles, strangles, and more
- **Unusual Activity Detection** - High volume and large block trade identification
- **Implied Volatility Analysis** - IV rank, percentile, and skew analysis

### **MCP Integration**
- **6 Comprehensive Tools** - Complete market analysis toolkit
- **3 Dynamic Resources** - Real-time data access
- **SSE Transport** - Server-Sent Events for web compatibility
- **Health Monitoring** - Built-in health checks for cloud deployment

## 📋 **Requirements**

- **Python 3.10+**
- **Polygon.io API Key** (get yours at [polygon.io](https://polygon.io))
- **Cloud Platform** (Railway, Render, Heroku, etc.)

## 🛠️ **Available Tools**

### **1. get_stock_price**
Get current stock price and basic information
```
get_stock_price(symbol: "AAPL")
```

### **2. get_options_chain**
Get comprehensive options chain data
```
get_options_chain(symbol: "AAPL", expiration_date: "2024-12-20")
```

### **3. calculate_option_greeks**
Calculate Options Greeks using Black-Scholes model
```
calculate_option_greeks(
    symbol: "AAPL", 
    strike_price: 150.0, 
    expiration_date: "2024-12-20",
    option_type: "call",
    volatility: 0.25
)
```

### **4. get_market_status**
Get current market status and trading hours
```
get_market_status()
```

## 📊 **Available Resources**

- `market://status` - Current market status
- `options://chain/{symbol}` - Options chain for any symbol  
- `stock://price/{symbol}` - Stock price for any symbol

## 🔧 **Local Development**

```bash
# Clone repository
git clone <your-repo-url>
cd polygon-mcp-server

# Install dependencies
uv sync

# Set environment variable
export POLYGON_API_KEY=your_api_key_here

# Run server
uv run polygon_mcp_server_sse.py
```

## 🌐 **Cloud Deployment**

### **Environment Variables Required:**
- `POLYGON_API_KEY` - Your Polygon.io API key
- `PORT` - Server port (auto-set by most platforms)

### **Deployment Files Included:**
- ✅ `Dockerfile` - Docker deployment
- ✅ `Procfile` - Heroku deployment  
- ✅ `railway.json` - Railway configuration
- ✅ `runtime.txt` - Python version specification
- ✅ Health check endpoint at `/health`

## 💡 **Usage Examples**

### **Basic Stock Analysis**
```
> "What's the current price of Apple stock?"
> "Show me the options chain for Tesla"
```

### **Advanced Options Analysis**
```
> "Calculate Greeks for AAPL $150 call expiring December 20th"
> "Analyze an iron condor strategy on SPY"
```

### **Market Intelligence**
```
> "Is there any unusual options activity in NVDA?"
> "What's the current market status?"
```

## 🔍 **Testing Your Deployment**

### **Health Check**
```bash
curl https://your-domain.com/health
# Returns: {"status": "healthy", "service": "polygon-mcp-server"}
```

### **SSE Endpoint**
```bash
curl https://your-domain.com/sse
# Returns: MCP server connection info
```

## 📈 **Advanced Features**

### **Options Greeks Calculation**
- **Black-Scholes Model** - Industry-standard pricing model
- **Real-time Data Integration** - Uses current market prices
- **Multiple Option Types** - Calls, puts, and exotic options
- **Time Decay Analysis** - Theta calculations for time-sensitive strategies

### **Market Intelligence**
- **Volume Analysis** - Unusual volume detection
- **Block Trade Identification** - Large institutional trades
- **Volatility Monitoring** - IV rank and percentile tracking
- **Flow Analysis** - Options flow direction and sentiment

## 🔐 **Security & Best Practices**

- **API Key Protection** - Environment variables only
- **Rate Limiting** - Built-in request throttling
- **Error Handling** - Comprehensive error management
- **Data Validation** - Input sanitization and validation

## 📚 **API Documentation**

### **Polygon.io Endpoints Used**
- `/v2/aggs/ticker/{ticker}/prev` - Previous close data
- `/v2/last/trade/{ticker}` - Last trade information
- `/v3/reference/options/contracts` - Options contracts
- `/v2/snapshot/options/{ticker}` - Options snapshots
- `/v1/marketstatus/now` - Market status

### **Dependencies**
- **polygon-api-client** - Official Polygon.io Python client
- **mcp** - Model Context Protocol implementation
- **scipy** - Scientific computing for Greeks calculation
- **numpy** - Numerical computations
- **uvicorn** - ASGI server for production deployment

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 **License**

MIT License - see LICENSE file for details

## ⚠️ **Disclaimer**

This software is provided for educational and informational purposes only. The options analytics and market data should not be used as the sole basis for investment decisions. Always consult with qualified financial professionals and conduct your own research before making investment decisions.

## 🆘 **Support**

- **Issues**: [GitHub Issues](https://github.com/your-username/polygon-mcp-server/issues)
- **Documentation**: [Polygon.io Docs](https://polygon.io/docs)
- **MCP Protocol**: [MCP Specification](https://modelcontextprotocol.io)

---

**Built with ❤️ using the Model Context Protocol and Polygon.io's comprehensive financial data APIs.**

**Ready for instant cloud deployment! 🚀** 