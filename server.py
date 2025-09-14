#!/usr/bin/env python3
import os
import base64
from fastapi import HTTPException, Depends, Header
from fastmcp import FastMCP
import requests
import google.generativeai as genai

mcp_server = os.getenv("MOONRAKER_URL", "http://192.168.1.124")

mcp = FastMCP("Moonraker MCP Server")

def get_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    api_key = os.getenv("API_KEY")
    if api_key and (not x_api_key or x_api_key != api_key):
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

@mcp.tool(description="Greet a user by name with a welcome message from the MCP server")
def greet(name: str, api_key: str = Depends(get_api_key)) -> str:
    return f"Hello, {name}! Welcome to our sample MCP server running on Heroku!"

@mcp.tool(description="Get state information about the 3D printer")
def get_printer_state(api_key: str = Depends(get_api_key)) -> dict:
    try:
        # send a GET request to the /printer/info endpoint of moonraker to get printer information
        response = requests.get(mcp_server + "/printer/info")
        response.raise_for_status()  # Raises an exception for bad status codes

        data = response.json()

        # Validate response structure
        if 'result' not in data:
            return {"error": "Invalid response structure from Moonraker API", "raw_response": data}

        result = data['result']

        return {
            "state_message": result.get("state_message", "Unknown"),
            "state": result.get("state", "Unknown"),
            "hostname": result.get("hostname", "Unknown"),
            "software_version": result.get("software_version", "Unknown"),
            "cpu_info": result.get("cpu_info", "Unknown"),
            "raw_result": result  # Include full result for debugging
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to connect to Moonraker: {str(e)}"}
    except (KeyError, ValueError) as e:
        return {"error": f"Failed to parse response: {str(e)}"}

@mcp.tool(description="Activate an emergency stop on the 3D printer")
def emergency_stop(api_key: str = Depends(get_api_key)) -> dict:
    info = requests.post(mcp_server + "/printer/emergency_stop")
    return info.json()

@mcp.tool(description="Activate an complete firmware restart of the 3D printer")
def firmware_restart(api_key: str = Depends(get_api_key)) -> dict:
    info = requests.post(mcp_server + "/printer/firmware_restart")
    return info.json()

# pause the print
@mcp.tool(description="Pause the current print job on the 3D printer")
def pause_print(api_key: str = Depends(get_api_key)) -> dict:
    info = requests.post(mcp_server + "/printer/print/pause")
    return info.json()

# resume the print
@mcp.tool(description="Resume the current print job on the 3D printer")
def resume_print(api_key: str = Depends(get_api_key)) -> dict:
    info = requests.post(mcp_server + "/printer/print/resume")
    return info.json()

# cancel the print
@mcp.tool(description="Cancel the current print job on the 3D printer")
def cancel_print(api_key: str = Depends(get_api_key)) -> dict:
    info = requests.post(mcp_server + "/printer/print/cancel")
    return info.json()

# get print status
@mcp.tool(description="Get the current print job status from the 3D printer")
def get_print_status(api_key: str = Depends(get_api_key)) -> dict:
    try:
        response = requests.get(mcp_server + "/printer/objects/query?webhooks&print_stats&display_status")
        response.raise_for_status()  # Raises an exception for bad status codes

        data = response.json()

        # Validate response structure
        if 'result' not in data or 'status' not in data['result']:
            return {"error": "Invalid response structure from Moonraker API"}

        status = data['result']['status']

        return {
            "webhooks": status.get("webhooks", {}),
            "print_stats": status.get("print_stats", {}),
            "display_status": status.get("display_status", {}),
            "eventtime": data['result'].get("eventtime")
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to connect to Moonraker: {str(e)}"}
    except (KeyError, ValueError) as e:
        return {"error": f"Failed to parse response: {str(e)}"}

@mcp.tool(description="Analyze the 3D print via webcam snapshot using AI to describe the print and identify any issues. Provide a prompt to guide the analysis.")
def analyze_print_via_webcam(prompt: str, api_key: str = Depends(get_api_key)) -> dict:
    try:
        # Grab the snapshot from the webcam
        snapshot_url = mcp_server + "/webcam/?action=snapshot"
        response = requests.get(snapshot_url)
        response.raise_for_status()

        # Encode image to base64
        image_data = base64.b64encode(response.content).decode('utf-8')

        # Configure Google Generative AI
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel('models/gemma-3-27b-it')

        # Generate content with prompt and image
        ai_response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": image_data}])

        return {
            "description": ai_response.text
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch snapshot: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

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
