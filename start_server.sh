#!/bin/bash
# Resume Customizer Server Launcher (Shell Script)

# Change to the script's directory
cd "$(dirname "$0")"

# Run the Python script
python3 start_server.py "$@"
