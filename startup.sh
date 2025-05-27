#!/bin/bash

# Function to create and start a screen session if it doesn't exist
start_screen_session() {
    local session_name=$1
    local command=$2
    
    if ! screen -list | grep -q "$session_name"; then
        # Try to create the screen session
        if screen -dmS "$session_name" bash -c "$command 2>&1 | tee /tmp/${session_name}_error.log"; then
            # Wait a moment to ensure the session is created
            sleep 1
            # Verify the session exists
            if screen -list | grep -q "$session_name"; then
                echo "✅ Started $session_name screen session"
            else
                echo "❌ Failed to start $session_name screen session"
                echo "Check error log: /tmp/${session_name}_error.log"
                return 1
            fi
        else
            echo "❌ Failed to create $session_name screen session"
            return 1
        fi
    else
        echo "ℹ️ $session_name screen session already exists"
    fi
}

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start gunicorn screen session
echo "Starting backend service..."
echo "Using project directory: $PROJECT_DIR"
start_screen_session "backend" "cd $PROJECT_DIR/backend && source venv/bin/activate && gunicorn -c gunicorn.conf.py api:app"

# Start cloudflared screen session
echo "Starting cloudflared service..."
start_screen_session "cloudflared" "cd $PROJECT_DIR && cloudflared tunnel run chanclas"

# Show final status
echo -e "\nCurrent screen sessions:"
screen -ls

echo -e "\nTo attach to a screen session:"
echo "  screen -r backend    # For backend service"
echo "  screen -r cloudflared # For cloudflared tunnel"

# If backend failed, show the error log
if [ -f /tmp/backend_error.log ]; then
    echo -e "\nBackend error log:"
    cat /tmp/backend_error.log
fi

# Keep the script running and monitor the sessions
while true; do
    sleep 30
    if ! screen -list | grep -q "backend" || ! screen -list | grep -q "cloudflared"; then
        echo "One or more screen sessions died, restarting..."
        # Restart the dead sessions
        if ! screen -list | grep -q "backend"; then
            start_screen_session "backend" "cd $PROJECT_DIR/backend && source venv/bin/activate && gunicorn -c gunicorn.conf.py api:app"
        fi
        if ! screen -list | grep -q "cloudflared"; then
            start_screen_session "cloudflared" "cd $PROJECT_DIR && cloudflared tunnel run chanclas"
        fi
    fi
done 