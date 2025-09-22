#!/bin/bash

echo "🚀 Polygon MCP Server - Cloud Deployment Helper"
echo "=============================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit: Polygon MCP Server"
fi

echo ""
echo "🌐 Choose your deployment platform:"
echo "1) Railway (Recommended - Free)"
echo "2) Render (Free)"
echo "3) Heroku"
echo "4) Manual setup"

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "🚂 Setting up for Railway..."
        echo "1. Go to: https://railway.app"
        echo "2. Sign up with GitHub"
        echo "3. Create New Project → Deploy from GitHub"
        echo "4. Set environment variable: POLYGON_API_KEY=5b9gXwiZEx2kskt24s35eIHMpS2aAgPI"
        echo "5. Your URL will be: https://your-app-name.railway.app/sse"
        ;;
    2)
        echo "🎨 Setting up for Render..."
        echo "1. Go to: https://render.com"
        echo "2. New → Web Service"
        echo "3. Build Command: uv sync"
        echo "4. Start Command: uv run polygon_mcp_server_sse.py"
        echo "5. Set environment variable: POLYGON_API_KEY=5b9gXwiZEx2kskt24s35eIHMpS2aAgPI"
        echo "6. Your URL will be: https://your-app-name.onrender.com/sse"
        ;;
    3)
        echo "🟣 Setting up for Heroku..."
        if command -v heroku &> /dev/null; then
            read -p "Enter your app name: " app_name
            heroku create $app_name
            heroku config:set POLYGON_API_KEY=5b9gXwiZEx2kskt24s35eIHMpS2aAgPI
            git push heroku main
            echo "✅ Deployed! Your URL: https://$app_name.herokuapp.com/sse"
        else
            echo "❌ Heroku CLI not found. Install from: https://devcenter.heroku.com/articles/heroku-cli"
        fi
        ;;
    4)
        echo "📋 Manual setup instructions:"
        echo "- Use the DEPLOYMENT_GUIDE.md for detailed instructions"
        echo "- Your API key: 5b9gXwiZEx2kskt24s35eIHMpS2aAgPI"
        echo "- SSE endpoint: /sse"
        echo "- Health check: /health"
        ;;
    *)
        echo "❌ Invalid choice"
        ;;
esac

echo ""
echo "📖 For detailed instructions, see: DEPLOYMENT_GUIDE.md"
echo "🔗 Once deployed, use your URL in Scira MCP Chat!" 