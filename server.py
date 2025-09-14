#!/usr/bin/env python3
import os
from fastmcp import FastMCP
import requests

mcp_server = os.getenv("MOONRAKER_URL", "http://192.168.1.124")

mcp = FastMCP("Moonraker MCP Server")

@mcp.tool(description="Greet a user by name with a welcome message from the MCP server")
def greet(name: str) -> str:
    return f"Hello, {name}! Welcome to our sample MCP server running on Heroku!"

@mcp.tool(description="Get state information about the 3D printer")
def get_printer_state() -> dict:
    # send a GET request to the /printer/info endpoint of moonraker to get printer information
    info = requests.get(mcp_server + "/printer/info")

    return {
        "state_message": info.json().get("state_message", "Unknown"),
        "state": info.json().get("state", "Unknown"),
    }

@mcp.tool(description="Activate an emergency stop on the 3D printer")
def emergency_stop() -> dict:
    info = requests.post(mcp_server + "/printer/emergency_stop")
    return info.json()

@mcp.tool(description="Activate an complete firmware restart of the 3D printer")
def firmware_restart() -> dict:
    info = requests.post(mcp_server + "/printer/firmware_restart")
    return info.json()

# pause the print
@mcp.tool(description="Pause the current print job on the 3D printer")
def pause_print() -> dict:
    info = requests.post(mcp_server + "/printer/print/pause")
    return info.json()

# resume the print
@mcp.tool(description="Resume the current print job on the 3D printer")
def resume_print() -> dict:
    info = requests.post(mcp_server + "/printer/print/resume")
    return info.json()

# cancel the print
@mcp.tool(description="Cancel the current print job on the 3D printer")
def cancel_print() -> dict:
    info = requests.post(mcp_server + "/printer/print/cancel")
    return info.json()

# get print status
@mcp.tool(description="Get the current print job status from the 3D printer")
def get_print_status() -> dict:
    info = requests.get(mcp_server + "/printer/objects/query?webhooks&print_stats&display_status")
    return {
        "webhooks": info.json().get("webhooks", {}),
        "print_stats": info.json().get("print_stats", {}),
        "display_status": info.json().get("display_status", {}),
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"

    print(f"Starting FastMCP server on {host}:{port}")

    mcp.run(
        transport="http",
        host=host,
        port=port,
        stateless_http=True
    )
