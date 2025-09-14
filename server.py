#!/usr/bin/env python3
import os
import base64
from fastmcp import FastMCP
import requests
import google.generativeai as genai
from typing import Optional

mcp_server = os.getenv("MOONRAKER_URL", "http://192.168.1.124")

mcp = FastMCP("Moonraker MCP Server")



@mcp.tool(
    name="greet_user",
    description="Greet a user by name with a welcome message from the MCP server",
)
def greet(name: str) -> str:
    return f"Hello, {name}! Welcome to our sample MCP server running on Heroku!"

@mcp.tool(
    name="get_printer_state",
    description="Get state information about the 3D printer",
)
def get_printer_state() -> dict:
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

@mcp.tool(
    name="restart_printer",
    description="Restart or stop the 3D printer. Action options: 'emergency_stop', 'firmware_restart'",
)
def restart_printer(action: str) -> dict:
    try:
        # Map action to appropriate endpoint
        endpoints = {
            "emergency_stop": "/printer/emergency_stop",
            "firmware_restart": "/printer/firmware_restart"
        }

        if action not in endpoints:
            return {"error": f"Invalid action '{action}'. Valid options: {list(endpoints.keys())}"}

        response = requests.post(mcp_server + endpoints[action])
        response.raise_for_status()
        data = response.json()

        return {"status": f"Printer {action} command executed", "result": data}
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to connect to Moonraker: {str(e)}"}
    except (KeyError, ValueError) as e:
        return {"error": f"Failed to parse response: {str(e)}"}

@mcp.tool(
    name="control_print",
    description="Control the current print job. Action options: 'pause', 'resume', 'cancel'",
)
def control_print(action: str) -> dict:
    try:
        # Map action to appropriate endpoint
        endpoints = {
            "pause": "/printer/print/pause",
            "resume": "/printer/print/resume",
            "cancel": "/printer/print/cancel"
        }

        if action not in endpoints:
            return {"error": f"Invalid action '{action}'. Valid options: {list(endpoints.keys())}"}

        response = requests.post(mcp_server + endpoints[action])
        response.raise_for_status()
        data = response.json()

        return {"status": f"Print {action} command executed", "result": data}
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to connect to Moonraker: {str(e)}"}
    except (KeyError, ValueError) as e:
        return {"error": f"Failed to parse response: {str(e)}"}

# get print status
@mcp.tool(
    name="get_print_status",
    description="Get the current print job status from the 3D printer",
)
def get_print_status() -> dict:
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

@mcp.tool(
    name="analyze_print_via_webcam",
    description="Analyze the 3D print via webcam snapshot using AI to describe the print and identify any issues. Provide a prompt to guide the analysis.",
)
def analyze_print_via_webcam(prompt: str) -> dict:
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

@mcp.tool(
    name="get_job_queue_status",
    description="Get the current status of the job queue",
)
def get_job_queue_status() -> dict:
    try:
        response = requests.get(mcp_server + "/server/job_queue/status")
        response.raise_for_status()
        data = response.json()
        if 'result' not in data:
            return {"error": "Invalid response structure from Moonraker API", "raw_response": data}
        return data['result']
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to connect to Moonraker: {str(e)}"}
    except (KeyError, ValueError) as e:
        return {"error": f"Failed to parse response: {str(e)}"}

@mcp.tool(
    name="enqueue_job",
    description="Enqueue one or more jobs to the job queue",
)
def enqueue_job(filenames: list[str], reset: bool = False) -> dict:
    try:
        payload = {"filenames": filenames, "reset": reset}
        response = requests.post(mcp_server + "/server/job_queue/job", json=payload)
        response.raise_for_status()
        data = response.json()
        if 'result' not in data:
            return {"error": "Invalid response structure from Moonraker API", "raw_response": data}
        return data['result']
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to connect to Moonraker: {str(e)}"}
    except (KeyError, ValueError) as e:
        return {"error": f"Failed to parse response: {str(e)}"}

@mcp.tool(
    name="remove_job",
    description="Remove one or more jobs from the job queue",
)
def remove_job(job_ids: Optional[list[str]] = None, all: bool = False) -> dict:
    try:
        if all:
            payload = {"all": True}
        else:
            if not job_ids:
                return {"error": "Either job_ids must be provided or all set to True"}
            payload = {"job_ids": job_ids}
        response = requests.delete(mcp_server + "/server/job_queue/job", json=payload)
        response.raise_for_status()
        data = response.json()
        if 'result' not in data:
            return {"error": "Invalid response structure from Moonraker API", "raw_response": data}
        return data['result']
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to connect to Moonraker: {str(e)}"}
    except (KeyError, ValueError) as e:
        return {"error": f"Failed to parse response: {str(e)}"}

@mcp.tool(
    name="control_job_queue",
    description="Control the job queue. Action options: 'pause', 'start', 'jump'. For 'jump' action, job_id is required.",
)
def control_job_queue(action: str, job_id: Optional[str] = None) -> dict:
    try:
        # Map action to appropriate endpoint
        endpoints = {
            "pause": "/server/job_queue/pause",
            "start": "/server/job_queue/start",
            "jump": "/server/job_queue/jump"
        }

        if action not in endpoints:
            return {"error": f"Invalid action '{action}'. Valid options: {list(endpoints.keys())}"}

        if action == "jump" and not job_id:
            return {"error": "job_id is required for 'jump' action"}

        # Prepare payload
        payload = None
        if action == "jump":
            payload = {"job_id": job_id}

        response = requests.post(mcp_server + endpoints[action], json=payload if payload else None)
        response.raise_for_status()
        data = response.json()
        if 'result' not in data:
            return {"error": "Invalid response structure from Moonraker API", "raw_response": data}

        status_msg = f"Job queue {action} command executed"
        if action == "jump":
            status_msg += f" for job {job_id}"

        return {"status": status_msg, "result": data['result']}
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to connect to Moonraker: {str(e)}"}
    except (KeyError, ValueError) as e:
        return {"error": f"Failed to parse response: {str(e)}"}

@mcp.tool(
    name="set_temperature",
    description="Set temperature for nozzle, bed, or enclosure. Component options: 'nozzle', 'bed', 'enclosure'",
)
def set_temperature(component: str, temp: float) -> dict:
    try:
        # Map component to appropriate G-code command
        gcode_commands = {
            "nozzle": f"M104 S{temp}",
            "bed": f"M140 S{temp}",
            "enclosure": f"M141 S{temp}"
        }

        if component not in gcode_commands:
            return {"error": f"Invalid component '{component}'. Valid options: {list(gcode_commands.keys())}"}

        script = gcode_commands[component]
        payload = {"script": script}
        response = requests.post(mcp_server + "/printer/gcode/script", json=payload)
        response.raise_for_status()
        data = response.json()
        if 'result' not in data:
            return {"error": "Invalid response structure from Moonraker API", "raw_response": data}
        return {"status": f"{component.title()} temperature set to {temp}°C", "script": script, "result": data['result']}
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to connect to Moonraker: {str(e)}"}
    except (KeyError, ValueError) as e:
        return {"error": f"Failed to parse response: {str(e)}"}

@mcp.tool(
    name="get_temps",
    description="Get the current temperatures of nozzle, bed, and enclosure",
)
def get_temps() -> dict:
    try:
        script = "M105"
        payload = {"script": script}
        response = requests.post(mcp_server + "/printer/gcode/script", json=payload)
        response.raise_for_status()
        data = response.json()
        if 'result' not in data:
            return {"error": "Invalid response structure from Moonraker API", "raw_response": data}
        return {"temperatures": data['result'], "script": script}
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to connect to Moonraker: {str(e)}"}
    except (KeyError, ValueError) as e:
        return {"error": f"Failed to parse response: {str(e)}"}

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
