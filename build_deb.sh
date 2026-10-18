#!/bin/bash
set -e

echo "Starting Debian package build..."

# Define directories
APP_DIR="/home/ubuntu/Working_Directory/AppIcon"
BUILD_DIR="$APP_DIR/tailscale-launcher-deb"
ARTIFACTS_DIR="${ARTIFACTS_DIR:-/home/ubuntu/.gemini/antigravity-cli/brain/204a6413-aa60-42df-8c42-0f1d8827f86e}"
OUTPUT_DEB="$APP_DIR/tailscale-launcher_1.0.0_all.deb"

# Clean previous builds
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/share/tailscale-launcher/icons"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps"

# 1. Create Control file
cat << 'EOF' > "$BUILD_DIR/DEBIAN/control"
Package: tailscale-launcher
Version: 1.0.0
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-gi, gir1.2-gtk-3.0, gir1.2-ayatanaappindicator3-0.1, tailscale
Maintainer: Antigravity AI <antigravity@google.com>
Description: System Tray Indicator, Control Panel, and TailSend File Sharing GUI for Tailscale
 A native Ubuntu GNOME system tray indicator, desktop launcher, and TailSend
 file-sharing utility to connect, monitor peers, and send/receive Taildrop files.
EOF

# 2. Create Post-Install script
cat << 'EOF' > "$BUILD_DIR/DEBIAN/postinst"
#!/bin/bash
set -e

# Update Desktop database
if [ -x "$(which update-desktop-database 2>/dev/null)" ]; then
    update-desktop-database -q /usr/share/applications || true
fi

# Update Icon cache
if [ -x "$(which gtk-update-icon-cache 2>/dev/null)" ]; then
    gtk-update-icon-cache -q -f -t /usr/share/icons/hicolor || true
fi

echo "Tailscale Launcher & TailSend post-installation completed successfully."
EOF
chmod 755 "$BUILD_DIR/DEBIAN/postinst"

# 3. Create Post-Remove script
cat << 'EOF' > "$BUILD_DIR/DEBIAN/postrm"
#!/bin/bash
set -e

# Update Desktop database on removal
if [ -x "$(which update-desktop-database 2>/dev/null)" ]; then
    update-desktop-database -q /usr/share/applications || true
fi

# Update Icon cache on removal
if [ -x "$(which gtk-update-icon-cache 2>/dev/null)" ]; then
    gtk-update-icon-cache -q -f -t /usr/share/icons/hicolor || true
fi
EOF
chmod 755 "$BUILD_DIR/DEBIAN/postrm"

# 4. Create wrapper executables
cat << 'EOF' > "$BUILD_DIR/usr/bin/tailscale-launcher"
#!/bin/bash
exec python3 /usr/share/tailscale-launcher/app.py "$@"
EOF
chmod 755 "$BUILD_DIR/usr/bin/tailscale-launcher"

cat << 'EOF' > "$BUILD_DIR/usr/bin/tailsend"
#!/bin/bash
exec python3 /usr/share/tailscale-launcher/app.py --tailsend "$@"
EOF
chmod 755 "$BUILD_DIR/usr/bin/tailsend"

# 5. Copy application code and assets
cp "$APP_DIR/app.py" "$BUILD_DIR/usr/share/tailscale-launcher/"
cp "$APP_DIR/tailsend.py" "$BUILD_DIR/usr/share/tailscale-launcher/"
chmod 755 "$BUILD_DIR/usr/share/tailscale-launcher/app.py"
chmod 755 "$BUILD_DIR/usr/share/tailscale-launcher/tailsend.py"
cp "$APP_DIR/icons"/*.svg "$BUILD_DIR/usr/share/tailscale-launcher/icons/"

# 6. Copy system applications entries
cat << 'EOF' > "$BUILD_DIR/usr/share/applications/tailscale-launcher.desktop"
[Desktop Entry]
Name=Tailscale Launcher
Comment=Manage Tailscale connections, view active peers, and share files with TailSend
Exec=tailscale-launcher
Icon=tailscale-launcher
Terminal=false
Type=Application
Categories=Network;Utility;
Actions=TailSend;Connect;Disconnect;Toggle;
StartupNotify=true
StartupWMClass=tailscale-launcher

[Desktop Action TailSend]
Name=TailSend (Share Files)
Exec=tailscale-launcher --tailsend

[Desktop Action Connect]
Name=Connect Tailscale
Exec=tailscale-launcher --connect

[Desktop Action Disconnect]
Name=Disconnect Tailscale
Exec=tailscale-launcher --disconnect

[Desktop Action Toggle]
Name=Toggle Connection
Exec=tailscale-launcher --toggle
EOF
chmod 644 "$BUILD_DIR/usr/share/applications/tailscale-launcher.desktop"

cat << 'EOF' > "$BUILD_DIR/usr/share/applications/tailsend.desktop"
[Desktop Entry]
Name=TailSend
Comment=Send and receive files across your Tailscale network (Taildrop)
Exec=tailsend %F
Icon=tailsend
Terminal=false
Type=Application
Categories=Network;FileTransfer;Utility;
StartupNotify=true
StartupWMClass=tailscale-launcher
EOF
chmod 644 "$BUILD_DIR/usr/share/applications/tailsend.desktop"

# 7. Copy global scalable icons
cp "$APP_DIR/icons/tailscale-launcher.svg" "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps/"
cp "$APP_DIR/icons/tailsend.svg" "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps/"
chmod 644 "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps/tailscale-launcher.svg"
chmod 644 "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps/tailsend.svg"

# 8. Build the Debian package
dpkg-deb --root-owner-group --build "$BUILD_DIR" "$OUTPUT_DEB"

# 9. Copy to Artifacts folder if it exists
if [ -d "$ARTIFACTS_DIR" ]; then
    cp "$OUTPUT_DEB" "$ARTIFACTS_DIR/tailscale-launcher_1.0.0_all.deb"
fi

# Cleanup build workspace
rm -rf "$BUILD_DIR"

echo "Debian package build completed successfully!"
echo "Package saved as: $OUTPUT_DEB"
