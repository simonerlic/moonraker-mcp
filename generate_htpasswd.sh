#!/bin/bash

# Script to generate .htpasswd file for nginx basic auth

USERNAME=${1:-admin}
PASSWORD=${2:-password}

# Check if htpasswd is installed
if ! command -v htpasswd &> /dev/null; then
    echo "htpasswd not found. Installing apache2-utils..."
    apt-get update && apt-get install -y apache2-utils
fi

# Generate .htpasswd file
htpasswd -bc /etc/nginx/.htpasswd $USERNAME $PASSWORD

echo ".htpasswd file generated at /etc/nginx/.htpasswd"
