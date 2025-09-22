#!/usr/bin/env python3
"""
Startup script for Polygon MCP Server with SSE transport
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    api_key = os.getenv("POLYGON_API_KEY") or os.getenv("API_KEY")
    if not api_key:
        print("❌ Error: POLYGON_API_KEY or API_KEY environment variable is required")
        sys.exit(1)
    
    # Get port from command line or default
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    
    print(f"🚀 Starting Polygon MCP Server...")
    print(f"📊 Port: {port}")
    print(f"🔑 API Key: {api_key[:10]}...")
    print(f"🌐 SSE Endpoint: http://localhost:{port}/sse")
    print(f"📋 Use this URL in Claude Desktop")
    
    # Set environment variables
    env = os.environ.copy()
    env["POLYGON_API_KEY"] = api_key
    env["API_KEY"] = api_key
    
    # Run the server
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "polygon_mcp_server_sse:mcp.create_app()",
            "--host", "0.0.0.0",
            "--port", str(port),
            "--reload"
        ], env=env, check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 