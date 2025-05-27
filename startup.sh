#!/bin/bash

# Function to create and start a screen session if it doesn't exist
start_screen_session() {
    local session_name=$1
    local command=$2
    
    if ! screen -list | grep -q "$session_name"; then
        screen -dmS "$session_name" bash -c "$command"
        echo "Started $session_name screen session"
    else
        echo "$session_name screen session already exists"
    fi
}

# Start gunicorn screen session
start_screen_session "backend" "cd ./backend/ && gunicorn -c gunicorn.conf.py api:app"

# Start cloudflared screen session
start_screen_session "cloudflared" "cloudflared tunnel run chanclas"

echo "All screen sessions have been started"
echo "To attach to backend screen: screen -r backend"
echo "To attach to cloudflared screen: screen -r cloudflared" 