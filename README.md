# Moonraker MCP Server

This is a Model Context Protocol (MCP) server that interfaces with a Moonraker instance to control a 3D printer. It has been dockerized for robustness and secured with nginx reverse proxy using basic authentication.

## Features

- Get printer state
- Emergency stop
- Firmware restart
- Pause, resume, cancel print jobs
- Get print status

## Security

The server is secured with nginx basic authentication. By default, the username is `admin` and password is `securepassword`. **Change these credentials immediately for production use.**

To change the password, regenerate the `.htpasswd` file:

```bash
htpasswd -bc nginx/.htpasswd yourusername yourpassword
```

For better security, consider:
- Using HTTPS (e.g., with Let's Encrypt)
- Strong passwords
- Limiting access by IP if possible
- Ensuring Moonraker itself is secured

## Prerequisites

- Docker and Docker Compose installed
- Moonraker instance running (default URL: http://192.168.1.124)

## Setup

1. Clone or ensure you have the project files.

2. Set the `MOONRAKER_URL` environment variable if different from default:
   ```bash
   export MOONRAKER_URL=http://your-moonraker-ip
   ```

3. Build and run the containers:
   ```bash
   docker-compose up --build
   ```

4. The server will be accessible at `http://localhost` (or your server's IP) on port 80.

5. When accessing, provide the basic auth credentials.

## Usage

The MCP server can be used by MCP clients (e.g., Claude Desktop) by connecting to the HTTP endpoint with authentication.

Note: The client must handle the basic auth when making requests.

## Environment Variables

- `MOONRAKER_URL`: URL of the Moonraker instance (default: http://192.168.1.124)

## Ports

- 80: nginx reverse proxy (secured)

## Stopping

```bash
docker-compose down
```
