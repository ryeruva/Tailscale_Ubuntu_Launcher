#!/bin/bash
set -e

APP_DIR="/home/ubuntu/Working_Directory/AppIcon"
DESKTOP_DIR="/home/ubuntu/Desktop"
APPS_DIR="/home/ubuntu/.local/share/applications"

echo "Installing Tailscale Launcher & TailSend..."

# Ensure target directories exist
mkdir -p "$APPS_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "/home/ubuntu/.local/share/icons"

# Copy icons to local share
cp "$APP_DIR/icons/tailscale-launcher.svg" "/home/ubuntu/.local/share/icons/"
cp "$APP_DIR/icons/tailsend.svg" "/home/ubuntu/.local/share/icons/"

# Make python files executable
chmod +x "$APP_DIR/app.py"
chmod +x "$APP_DIR/tailsend.py"

# Copy desktop files to Applications database
cp "$APP_DIR/tailscale-launcher.desktop" "$APPS_DIR/"
cp "$APP_DIR/tailsend.desktop" "$APPS_DIR/"
chmod +x "$APPS_DIR/tailscale-launcher.desktop"
chmod +x "$APPS_DIR/tailsend.desktop"

# Copy desktop files to Desktop screen
cp "$APP_DIR/tailscale-launcher.desktop" "$DESKTOP_DIR/"
cp "$APP_DIR/tailsend.desktop" "$DESKTOP_DIR/"
chmod +x "$DESKTOP_DIR/tailscale-launcher.desktop"
chmod +x "$DESKTOP_DIR/tailsend.desktop"

# Mark as trusted for GNOME Desktop
echo "Trusting desktop files on Ubuntu GNOME Desktop..."
gio set "$DESKTOP_DIR/tailscale-launcher.desktop" metadata::trusted true || true
gio set "$DESKTOP_DIR/tailsend.desktop" metadata::trusted true || true

echo "Installation complete!"
echo "You can now launch 'Tailscale Launcher' or 'TailSend' from your Application Search or Desktop."
