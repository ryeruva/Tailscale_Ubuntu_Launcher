# Tailscale Launcher for Ubuntu Desktop

A premium, native system tray indicator and control panel for **Tailscale** on Ubuntu GNOME. The launcher provides an intuitive visual interface to connect, disconnect, and monitor your secure VPN tunnel and active peer nodes.

---

## Features

1. **System Tray AppIndicator**:
   - Resides cleanly in the GNOME top menu bar.
   - Dynamic status icons (teal for Connected, gray for Disconnected, orange/yellow for Connecting) using custom vector graphics.
   - Right-click menu with connection status, IP address, connect toggles, and direct control panel focus.

2. **Control Panel Dashboard**:
   - Modern dark theme styled with custom GTK 3 CSS.
   - **Slider Tunnel Switch**: A premium sliding toggle (`Gtk.Switch`) that transitions state asynchronously.
   - **Connection Details Card**: Displays your active account profile, current Tailscale IP (with a copy-to-clipboard button), and client key expiry date.
   - **Active Peers Card**: Shows up to 10 active peers in the tailnet with online status indicators (green/gray), hostnames, IPs, and operating system badges. Packaged in a scrolled container that remains hidden when empty and scrolls automatically when nodes overflow.
   - **Admin Console & KB Links**: Direct integration to open the Tailscale web portal and documentation in your default browser.

3. **Self-Healing Operator Authentication**:
   - Toggling Tailscale up or down usually requires administrative privileges.
   - The app automatically intercepts "access denied" errors and launches a native policykit authorization popup (`pkexec tailscale set --operator=$USER`).
   - Once authenticated, your user is permanently set as a Tailscale operator, making all future connects, disconnects, and shortcuts **completely password-free**.

4. **Right-Click Desktop Actions**:
   - The launcher shortcut integrates native desktop actions.
   - Right-click the shortcut on your desktop or Ubuntu dock to immediately choose **Connect Tailscale**, **Disconnect Tailscale**, or **Toggle Connection** without opening the GUI.

5. **Single Instance Control**:
   - Utilizes a Unix socket (`~/.cache/tailscale-launcher.sock`) to enforce a single running daemon.
   - Double-clicking the launcher when already running will bring the active panel window to the front. 
   - CLI actions communicate commands directly to the background daemon via IPC.

---

## Installation

### Method 1: System-Wide Debian Package (Recommended)
You can install the pre-packaged `.deb` archive directly:
```bash
sudo apt install ./tailscale-launcher_1.0.0_all.deb
```
This automatically handles all dependency bindings, sets up the binary wrapper, installs global scalable icons, and registers the desktop shortcut globally.

### Method 2: From Source
To run or install locally without package managers:
1. Clone the repository or navigate to the source directory.
2. Register the application and desktop shortcuts:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
3. Launch the app from the Ubuntu application menu search or double-click the **Tailscale Launcher** shortcut on your Desktop.

---

## Rebuilding the Package
If you modify the source files (e.g., editing `app.py` or icons) and want to regenerate the `.deb` file:
```bash
chmod +x build_deb.sh
./build_deb.sh
```
The script will output `tailscale-launcher_1.0.0_all.deb` in the project root directory.

---

## Requirements
* Ubuntu 20.04+ (GNOME Desktop Environment)
* Python 3
* `python3-gi` (PyGObject bindings)
* GTK 3 & Ayatana AppIndicator (`gir1.2-gtk-3.0`, `gir1.2-ayatanaappindicator3-0.1`)
* Tailscale client installed (`tailscale`)

---

## License
Licensed under the GNU General Public License v3 (GPLv3). See the [LICENSE](LICENSE) file for the full legal text.
