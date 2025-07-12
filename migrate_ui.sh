#!/bin/bash

# Source and destination paths
SRC=~/chanclas/ui/
DEST=/var/www/html/

# Copy only changed files
echo "Deploying UI files from $SRC to $DEST ..."
sudo rsync -av --update --delete "$SRC" "$DEST"

# Fix permissions for web server
echo "Setting correct permissions..."

# Set correct ownership (www-data is common for nginx/apache)
sudo chown -R www-data:www-data "$DEST"

# Set correct permissions for directories (755 - read, write, execute for owner; read, execute for group and others)
sudo find "$DEST" -type d -exec chmod 755 {} \;

# Set correct permissions for files (644 - read, write for owner; read for group and others)
sudo find "$DEST" -type f -exec chmod 644 {} \;

# Ensure JavaScript files have correct permissions
sudo chmod 644 "$DEST"*.js 2>/dev/null || true
sudo chmod 644 "$DEST"js/*.js 2>/dev/null || true

echo "✅ Deployment complete with correct permissions."