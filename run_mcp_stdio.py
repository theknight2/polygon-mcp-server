#!/usr/bin/env python3
"""
Wrapper script to run the Polygon MCP Server with STDIO transport
"""

import subprocess
import sys
import os

def main():
    # Set environment variables
    env = os.environ.copy()
    
    # Ensure POLYGON_API_KEY is set
    if not env.get("POLYGON_API_KEY"):
        env["POLYGON_API_KEY"] = "5b9gXwiZEx2kskt24s35eIHMpS2aAgPI"
    
    # Run the STDIO server with uv
    try:
        subprocess.run([
            "uv", "run", "python", "polygon_mcp_server_stdio.py"
        ], env=env, check=True)
    except KeyboardInterrupt:
        print("\nServer stopped")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 