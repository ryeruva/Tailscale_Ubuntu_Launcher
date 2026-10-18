# Tailscale Launcher & TailSend for Ubuntu Desktop

A premium, native system tray indicator, control panel, and **TailSend** file-sharing GUI for **Tailscale** on Ubuntu GNOME. The suite provides an intuitive visual interface to connect, disconnect, monitor your secure VPN tunnel and active peer nodes, and send/receive files across your Tailnet via Taildrop.

---

## Features

1. **System Tray AppIndicator**:
   - Resides cleanly in the GNOME top menu bar.
   - Dynamic status icons (teal for Connected, gray for Disconnected, orange/yellow for Connecting) using custom vector graphics.
   - Right-click menu with connection status, IP address, connect toggles, direct Control Panel focus, and **TailSend** file transfer shortcuts.

2. **Control Panel Dashboard**:
   - Modern dark theme styled with custom GTK 3 CSS.
   - **Slider Tunnel Switch**: A premium sliding toggle (`Gtk.Switch`) that transitions state asynchronously.
   - **Connection Details Card**: Displays your active account profile, current Tailscale IP (with a copy-to-clipboard button), and client key expiry date.
   - **Active Peers Card**: Shows active peers in the tailnet with online status indicators (green/gray), hostnames/DNS names, IPs (with click-to-copy), OS badges, and a quick **Send** button per peer that opens TailSend targeting that device.
   - **Footer Bar**: Direct access to **TailSend**, the Tailscale Admin Console, and KB documentation.

3. **TailSend File Sharing GUI (Integrated & Standalone)**:
   - **Target Device Picker**: Lists all Tailnet peers with online status, friendly device names, IPs, and OS badges.
   - **File Picker & Drag-and-Drop**: Drag and drop multiple files directly from Ubuntu Files (Nautilus) or browse via the native file chooser (`tailscale file cp <files...> <target>:`).
   - **Incoming Taildrop Receiver**: Automatically polls or manually pulls incoming Taildrop files (`tailscale file get --conflict=rename --verbose`) directly into `~/Downloads` (or a custom folder) with native desktop notifications (`notify-send`).
   - **Standalone Launch Mode**: Run `python3 app.py --tailsend [files...]`, `./tailsend.py [files...]`, or launch the **TailSend** desktop shortcut directly.

4. **Self-Healing Operator Authentication**:
   - Toggling Tailscale or using Taildrop without operator privileges automatically launches a native policykit authorization popup (`pkexec tailscale set --operator=$USER`).
   - Once authenticated, your user is permanently set as a Tailscale operator, making all future connects, disconnects, and file transfers **completely password-free**.

5. **Right-Click Desktop Actions**:
   - Right-click the **Tailscale Launcher** shortcut on your desktop or Ubuntu dock to immediately choose **TailSend (Share Files)**, **Connect Tailscale**, **Disconnect Tailscale**, or **Toggle Connection**.

6. **Single Instance Control**:
   - Utilizes a Unix socket (`~/.cache/tailscale-launcher.sock`) to enforce a single running daemon and route `--tailsend` / CLI actions seamlessly via IPC.

---

## Installation

### Method 1: System-Wide Debian Package (Recommended)
You can install the pre-packaged `.deb` archive directly:
```bash
sudo apt install ./tailscale-launcher_1.0.0_all.deb
```
This installs both `tailscale-launcher` and `tailsend` binaries, scalable icons, and desktop shortcuts globally.

### Method 2: From Source
To run or install locally without package managers:
1. Navigate to the source directory.
2. Register the applications and desktop shortcuts:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
3. Launch **Tailscale Launcher** or **TailSend** from the Ubuntu application menu or your Desktop.

---

## Rebuilding the Package
If you modify the source files and want to regenerate the `.deb` file:
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
