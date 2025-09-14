# Moonraker MCP Server

This is a Model Context Protocol (MCP) server that interfaces with a Moonraker instance to control a 3D printer.

## Features

- Get printer state
- Emergency stop
- Firmware restart
- Pause, resume, cancel print jobs
- Get print status
- Return a live webcam view of the printer

## Prerequisites

- Docker and Docker Compose installed
- Moonraker instance running

## Setup

1. Clone or ensure you have the project files.

2. Set the `MOONRAKER_URL` environment variable if different from default:
   ```bash
   export MOONRAKER_URL=http://your-moonraker-ip
   ```

3. (Optional) Set the `API_KEY` environment variable for authentication:
   ```bash
   export API_KEY=your-secret-api-key
   ```

4. Build and run the containers:
   ```bash
   docker-compose up --build
   ```

5. The server will be accessible at `http://localhost` (or your server's IP) on port 80.

6. When accessing, provide the API key in the X-API-Key header if API_KEY is set.

## Usage

The MCP server can be used by MCP clients (e.g., Claude Desktop) by connecting to the HTTP endpoint with API key authentication.

Note: If API_KEY is set, the client must provide the X-API-Key header in requests.

## Environment Variables

- `MOONRAKER_URL`: URL of the Moonraker instance (default: http://192.168.1.124)
- `API_KEY`: Optional API key for securing the server (if set, clients must provide X-API-Key header)

## Ports

- 80: nginx reverse proxy (secured)

## Stopping

```bash
docker-compose down
```
