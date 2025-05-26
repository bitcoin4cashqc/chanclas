#!/bin/bash

# Source and destination paths
SRC=~/chanclas/ui/
DEST=/var/www/html/

# Copy only changed files
echo "Deploying UI files from $SRC to $DEST ..."
sudo rsync -av --update --delete "$SRC" "$DEST"

echo "✅ Deployment complete."