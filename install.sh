#!/bin/bash
set -e

APP_DIR="/home/ubuntu/Working_Directory/AppIcon"
DESKTOP_DIR="/home/ubuntu/Desktop"
APPS_DIR="/home/ubuntu/.local/share/applications"

echo "Installing Tailscale Launcher..."

# Ensure target directories exist
mkdir -p "$APPS_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "/home/ubuntu/.local/share/icons"

# Copy icon to local share
cp "$APP_DIR/icons/tailscale-launcher.svg" "/home/ubuntu/.local/share/icons/"

# Make python file executable
chmod +x "$APP_DIR/app.py"

# Copy desktop file to Applications database
cp "$APP_DIR/tailscale-launcher.desktop" "$APPS_DIR/"
chmod +x "$APPS_DIR/tailscale-launcher.desktop"

# Copy desktop file to Desktop screen
cp "$APP_DIR/tailscale-launcher.desktop" "$DESKTOP_DIR/"
chmod +x "$DESKTOP_DIR/tailscale-launcher.desktop"

# Mark as trusted for GNOME Desktop
echo "Trusting desktop file on Ubuntu GNOME Desktop..."
gio set "$DESKTOP_DIR/tailscale-launcher.desktop" metadata::trusted true || true

echo "Installation complete!"
echo "You can now launch 'Tailscale Launcher' from your Application Search or Desktop."
