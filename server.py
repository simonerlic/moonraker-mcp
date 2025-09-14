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
    name="emergency_stop",
    description="Activate an emergency stop on the 3D printer",
)
def emergency_stop() -> dict:
    info = requests.post(mcp_server + "/printer/emergency_stop")
    return info.json()

@mcp.tool(
    name="firmware_restart",
    description="Activate an complete firmware restart of the 3D printer",
)
def firmware_restart() -> dict:
    info = requests.post(mcp_server + "/printer/firmware_restart")
    return info.json()

# pause the print
@mcp.tool(
    name="pause_print",
    description="Pause the current print job on the 3D printer",
)
def pause_print() -> dict:
    info = requests.post(mcp_server + "/printer/print/pause")
    return info.json()

# resume the print
@mcp.tool(
    name="resume_print",
    description="Resume the current print job on the 3D printer",
)
def resume_print() -> dict:
    info = requests.post(mcp_server + "/printer/print/resume")
    return info.json()

# cancel the print
@mcp.tool(
    name="cancel_print",
    description="Cancel the current print job on the 3D printer",
)
def cancel_print() -> dict:
    info = requests.post(mcp_server + "/printer/print/cancel")
    return info.json()

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
    name="pause_job_queue",
    description="Pause the job queue",
)
def pause_job_queue() -> dict:
    try:
        response = requests.post(mcp_server + "/server/job_queue/pause")
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
    name="start_job_queue",
    description="Start the job queue",
)
def start_job_queue() -> dict:
    try:
        response = requests.post(mcp_server + "/server/job_queue/start")
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
    name="jump_job_queue",
    description="Jump a job to the front of the queue",
)
def jump_job_queue(job_id: str) -> dict:
    try:
        payload = {"job_id": job_id}
        response = requests.post(mcp_server + "/server/job_queue/jump", json=payload)
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
    name="set_nozzle_temp",
    description="Set the nozzle temperature",
)
def set_nozzle_temp(temp: float) -> dict:
    try:
        script = f"M104 S{temp}"
        payload = {"script": script}
        response = requests.post(mcp_server + "/printer/gcode/script", json=payload)
        response.raise_for_status()
        data = response.json()
        if 'result' not in data:
            return {"error": "Invalid response structure from Moonraker API", "raw_response": data}
        return {"status": "Temperature set", "script": script, "result": data['result']}
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to connect to Moonraker: {str(e)}"}
    except (KeyError, ValueError) as e:
        return {"error": f"Failed to parse response: {str(e)}"}

@mcp.tool(
    name="set_bed_temp",
    description="Set the bed temperature",
)
def set_bed_temp(temp: float) -> dict:
    try:
        script = f"M140 S{temp}"
        payload = {"script": script}
        response = requests.post(mcp_server + "/printer/gcode/script", json=payload)
        response.raise_for_status()
        data = response.json()
        if 'result' not in data:
            return {"error": "Invalid response structure from Moonraker API", "raw_response": data}
        return {"status": "Temperature set", "script": script, "result": data['result']}
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to connect to Moonraker: {str(e)}"}
    except (KeyError, ValueError) as e:
        return {"error": f"Failed to parse response: {str(e)}"}

@mcp.tool(
    name="set_enclosure_temp",
    description="Set the enclosure temperature",
)
def set_enclosure_temp(temp: float) -> dict:
    try:
        script = f"M141 S{temp}"
        payload = {"script": script}
        response = requests.post(mcp_server + "/printer/gcode/script", json=payload)
        response.raise_for_status()
        data = response.json()
        if 'result' not in data:
            return {"error": "Invalid response structure from Moonraker API", "raw_response": data}
        return {"status": "Temperature set", "script": script, "result": data['result']}
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
