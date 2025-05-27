# Chanclas Service Management

This repository contains scripts for managing the Chanclas services and UI deployment.

## Service Management (`startup.sh`)

The `startup.sh` script manages the backend and cloudflared tunnel services using GNU Screen sessions. It provides automatic service monitoring and recovery.

### Features
- Creates and manages screen sessions for:
  - Backend (Gunicorn) service
  - Cloudflared tunnel
- Automatic service monitoring
- Automatic recovery if services die
- Detailed logging

### Usage
```bash
# Start the services
./startup.sh

# View running screen sessions
screen -ls

# Attach to backend screen
screen -r backend

# Attach to cloudflared screen
screen -r cloudflared
```

### Systemd Integration
The script is configured to run as a systemd service for automatic startup on boot:
```bash
# Service file location
/etc/systemd/system/chanclas-startup.service

# Check service status
systemctl status chanclas-startup.service

# View service logs
journalctl -u chanclas-startup.service
```

## UI Deployment (`migrate_ui.sh`)

The `migrate_ui.sh` script handles the deployment of UI files to the web server directory.

### Features
- Efficient file synchronization using rsync
- Only copies changed files
- Removes files that no longer exist in source
- Preserves file permissions

### Usage
```bash
# Deploy UI files
./migrate_ui.sh
```

### Configuration
- Source: `~/chanclas/ui/`
- Destination: `/var/www/html/`

## Directory Structure
```
chanclas/
├── backend/           # Backend service files
├── ui/               # UI source files
├── startup.sh        # Service management script
└── migrate_ui.sh     # UI deployment script
```

## Requirements
- GNU Screen
- Gunicorn
- Cloudflared
- rsync
- systemd (for service management) 