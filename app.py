#!/usr/bin/env python3
import sys
import os
import socket
import threading
import json
import subprocess
import webbrowser
import getpass
import time
import gi

# Initialize PyGObject and GTK 3
gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf
from gi.repository import AyatanaAppIndicator3 as AppIndicator

# Constants and Paths
APP_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_CONNECTED = os.path.join(APP_DIR, "icons", "tailscale-connected.svg")
ICON_DISCONNECTED = os.path.join(APP_DIR, "icons", "tailscale-disconnected.svg")
ICON_CONNECTING = os.path.join(APP_DIR, "icons", "tailscale-connecting.svg")
ICON_LAUNCHER = os.path.join(APP_DIR, "icons", "tailscale-launcher.svg")
SOCKET_PATH = os.path.expanduser("~/.cache/tailscale-launcher.sock")

CSS_DATA = """
window {
    background-color: #0f1015;
    color: #e2e8f0;
    font-family: 'Inter', 'Ubuntu', 'Segoe UI', sans-serif;
}

.header-bar {
    background: linear-gradient(135deg, #1c1d26 0%, #12131a 100%);
    padding: 16px 20px;
    border-bottom: 1px solid #2b2d3a;
}

.title-label {
    font-size: 20px;
    font-weight: 800;
    color: #ffffff;
}

.status-badge {
    font-size: 11px;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 12px;
    color: #ffffff;
}

.status-badge.connected {
    background-color: #00c0a5;
}

.status-badge.disconnected {
    background-color: #455a64;
}

.status-badge.connecting {
    background-color: #ff9800;
}

.card {
    background-color: #171821;
    border: 1px solid #222431;
    border-radius: 12px;
    padding: 16px;
    margin: 12px 16px;
}

.card-title {
    font-size: 13px;
    font-weight: 700;
    color: #94a3b8;
    margin-bottom: 8px;
}

.detail-label {
    font-size: 14px;
    color: #94a3b8;
}

.detail-value {
    font-size: 14px;
    font-weight: 600;
    color: #f8fafc;
}

switch {
    border-radius: 20px;
    background-color: #263238;
    border: 1px solid #37474f;
    min-height: 28px;
    min-width: 50px;
}

switch:checked {
    background-color: #00c0a5;
    border-color: #00e5c1;
}

switch slider {
    background-color: #ffffff;
    border-radius: 50%;
    min-width: 22px;
    min-height: 22px;
    margin: 3px;
}

.peer-row {
    padding: 10px 12px;
    border-radius: 8px;
    margin-bottom: 6px;
    background-color: #1c1d26;
    border: 1px solid #262836;
}

.peer-name {
    font-size: 14px;
    font-weight: 600;
    color: #f8fafc;
}

.peer-ip {
    font-size: 12px;
    color: #64748b;
    font-family: monospace;
}

.peer-os-badge {
    font-size: 10px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
    background-color: #2b2d3a;
    color: #94a3b8;
}

.online-dot {
    background-color: #00c0a5;
    border-radius: 50%;
}

.offline-dot {
    background-color: #455a64;
    border-radius: 50%;
}

.action-btn {
    background-color: #1e293b;
    color: #f1f5f9;
    font-weight: 600;
    border-radius: 8px;
    padding: 8px 16px;
    border: 1px solid #334155;
}

.action-btn:hover {
    background-color: #334155;
}

.copy-btn {
    background: transparent;
    border: none;
    color: #00c0a5;
}
.copy-btn:hover {
    color: #00e5c1;
}

.warning-banner {
    background-color: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 8px;
    padding: 12px;
    margin: 12px 16px;
}

.warning-text {
    font-size: 13px;
    color: #fca5a5;
}

.warning-fix-btn {
    background-color: #ef4444;
    color: white;
    font-weight: 700;
    border-radius: 6px;
    padding: 6px 12px;
    border: none;
}
.warning-fix-btn:hover {
    background-color: #dc2626;
}
"""

def run_direct_up():
    print("Direct connection trigger requested...")
    res = subprocess.run(["tailscale", "up"], capture_output=True, text=True)
    if res.returncode != 0:
        err = res.stderr.lower() + res.stdout.lower()
        print(f"Direct connection trigger failed: {res.stderr.strip()}")
        if "access denied" in err or "permission denied" in err or "prefs write access denied" in err:
            print("Access denied. Attempting to set operator permissions using pkexec...")
            username = getpass.getuser()
            auth_res = subprocess.run(["pkexec", "tailscale", "set", "--operator=" + username])
            if auth_res.returncode == 0:
                print("Permissions set. Retrying connection...")
                subprocess.run(["tailscale", "up"])
            else:
                print("Operator setup failed. Fallback to direct pkexec...")
                subprocess.run(["pkexec", "tailscale", "up"])
        elif "http" in err:
            for line in (res.stderr + res.stdout).split("\n"):
                if "https://" in line:
                    parts = line.split()
                    for p in parts:
                        if p.startswith("https://"):
                            print(f"Found login URL: {p}. Opening...")
                            webbrowser.open(p)
                            break

def run_direct_down():
    print("Direct disconnection trigger requested...")
    res = subprocess.run(["tailscale", "down"], capture_output=True, text=True)
    if res.returncode != 0:
        err = res.stderr.lower() + res.stdout.lower()
        print(f"Direct disconnection trigger failed: {res.stderr.strip()}")
        if "access denied" in err or "permission denied" in err or "prefs write access denied" in err:
            print("Access denied. Attempting to set operator permissions using pkexec...")
            username = getpass.getuser()
            auth_res = subprocess.run(["pkexec", "tailscale", "set", "--operator=" + username])
            if auth_res.returncode == 0:
                print("Permissions set. Retrying disconnection...")
                subprocess.run(["tailscale", "down"])
            else:
                print("Operator setup failed. Fallback to direct pkexec...")
                subprocess.run(["pkexec", "tailscale", "down"])

def run_direct_toggle():
    print("Direct toggle trigger requested...")
    res = subprocess.run(["tailscale", "status", "--json"], capture_output=True, text=True)
    if res.returncode == 0:
        try:
            data = json.loads(res.stdout)
            if data.get("BackendState") == "Running":
                run_direct_down()
            else:
                run_direct_up()
        except Exception:
            run_direct_up()
    else:
        run_direct_up()

def check_single_instance():
    os.makedirs(os.path.dirname(SOCKET_PATH), exist_ok=True)
    
    cmd = "show_gui"
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        s.connect(SOCKET_PATH)
        s.sendall(cmd.encode('utf-8'))
        s.close()
        sys.exit(0)
    except socket.error:
        try:
            os.unlink(SOCKET_PATH)
        except OSError:
            pass
            
        if cmd in ["--connect", "--disconnect", "--toggle"]:
            if cmd == "--connect":
                run_direct_up()
            elif cmd == "--disconnect":
                run_direct_down()
            elif cmd == "--toggle":
                run_direct_toggle()
            sys.exit(0)

def run_ipc_server(app):
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen(1)
    while app.running:
        try:
            conn, _ = server.accept()
            data = conn.recv(1024).decode('utf-8')
            if data:
                GLib.idle_add(app.handle_ipc_message, data)
            conn.close()
        except Exception:
            break

class TailscaleLauncherApp:
    def __init__(self):
        self.running = True
        self.status_data = {}
        self.is_connecting = False
        self.operator_required = False
        self.updating_ui = False
        self.window = None
        
        # Initialize AppIndicator
        self.indicator = AppIndicator.Indicator.new(
            "tailscale-launcher",
            ICON_DISCONNECTED,
            AppIndicator.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        
        self.setup_menu()
        self.load_css()
        
        # Start IPC Server Thread
        self.ipc_thread = threading.Thread(target=run_ipc_server, args=(self,), daemon=True)
        self.ipc_thread.start()
        
        # Start Status Poller Thread
        self.poll_thread = threading.Thread(target=self.poll_loop, daemon=True)
        self.poll_thread.start()
        
        # Build GTK Window
        self.build_window()
        
        # If launched with no args, show the control panel window on startup
        if len(sys.argv) == 1:
            self.show_window()

    def load_css(self):
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(CSS_DATA.encode('utf-8'))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def setup_menu(self):
        self.menu = Gtk.Menu()
        
        self.status_menu_item = Gtk.MenuItem(label="Status: Checking...")
        self.status_menu_item.set_sensitive(False)
        self.menu.append(self.status_menu_item)
        
        self.ip_menu_item = Gtk.MenuItem(label="IP: -")
        self.ip_menu_item.set_sensitive(False)
        self.menu.append(self.ip_menu_item)
        self.ip_menu_item.hide()
        
        self.menu.append(Gtk.SeparatorMenuItem())
        
        self.connect_menu_item = Gtk.MenuItem(label="Connect")
        self.connect_menu_item.connect("activate", self.on_menu_toggle_connect)
        self.menu.append(self.connect_menu_item)
        
        open_item = Gtk.MenuItem(label="Open Control Panel")
        open_item.connect("activate", lambda w: self.show_window())
        self.menu.append(open_item)
        
        self.menu.append(Gtk.SeparatorMenuItem())
        
        exit_item = Gtk.MenuItem(label="Exit Launcher")
        exit_item.connect("activate", self.quit)
        self.menu.append(exit_item)
        
        self.menu.show_all()
        self.indicator.set_menu(self.menu)

    def build_window(self):
        self.window = Gtk.Window(title="Tailscale Control Panel")
        self.window.set_default_size(420, 580)
        self.window.set_resizable(False)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        
        try:
            self.window.set_icon_from_file(ICON_LAUNCHER)
        except Exception:
            pass
            
        self.window.connect("delete-event", self.on_window_delete)
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window.add(main_box)
        
        # Header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header_box.get_style_context().add_class("header-bar")
        
        logo_image = Gtk.Image()
        try:
            pb = GdkPixbuf.Pixbuf.new_from_file_at_size(ICON_LAUNCHER, 32, 32)
            logo_image.set_from_pixbuf(pb)
        except Exception:
            logo_image.set_from_icon_name("network-vpn-symbolic", Gtk.IconSize.BUTTON)
        header_box.pack_start(logo_image, False, False, 0)
        
        title_label = Gtk.Label(label="Tailscale")
        title_label.get_style_context().add_class("title-label")
        header_box.pack_start(title_label, False, False, 0)
        
        self.status_badge = Gtk.Label(label="DISCONNECTED")
        self.status_badge.get_style_context().add_class("status-badge")
        self.status_badge.get_style_context().add_class("disconnected")
        header_box.pack_start(self.status_badge, False, False, 8)
        
        spacer = Gtk.Box()
        header_box.pack_start(spacer, True, True, 0)
        
        refresh_btn = Gtk.Button()
        refresh_btn.set_relief(Gtk.ReliefStyle.NONE)
        refresh_image = Gtk.Image.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON)
        refresh_btn.set_image(refresh_image)
        refresh_btn.connect("clicked", lambda w: self.force_refresh())
        header_box.pack_end(refresh_btn, False, False, 0)
        
        main_box.pack_start(header_box, False, False, 0)
        
        # Warning/Operator Banner
        self.warning_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.warning_box.get_style_context().add_class("warning-banner")
        
        warning_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        warning_icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic", Gtk.IconSize.BUTTON)
        warning_hbox.pack_start(warning_icon, False, False, 0)
        
        warning_label = Gtk.Label(label="Operator permission required to control connection.")
        warning_label.set_line_wrap(True)
        warning_label.get_style_context().add_class("warning-text")
        warning_hbox.pack_start(warning_label, True, True, 0)
        self.warning_box.pack_start(warning_hbox, False, False, 0)
        
        fix_btn = Gtk.Button(label="Configure Access")
        fix_btn.get_style_context().add_class("warning-fix-btn")
        fix_btn.connect("clicked", lambda w: self.run_configure_operator())
        self.warning_box.pack_start(fix_btn, False, False, 4)
        
        main_box.pack_start(self.warning_box, False, False, 0)
        self.warning_box.set_no_show_all(True)
        self.warning_box.hide()
        
        # Connection details card (fixed layout, direct in main_box)
        conn_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        conn_card.get_style_context().add_class("card")
        
        # Switch Row HBox
        switch_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        switch_lbl_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        switch_title = Gtk.Label(xalign=0)
        switch_title.set_markup("<b>Secure VPN Tunnel</b>")
        switch_title.get_style_context().add_class("detail-value")
        switch_lbl_vbox.pack_start(switch_title, False, False, 0)
        
        self.switch_desc = Gtk.Label(label="Disconnected", xalign=0)
        self.switch_desc.get_style_context().add_class("detail-label")
        switch_lbl_vbox.pack_start(self.switch_desc, False, False, 0)
        
        switch_hbox.pack_start(switch_lbl_vbox, True, True, 0)
        
        self.connection_switch = Gtk.Switch()
        self.connection_switch.set_valign(Gtk.Align.CENTER)
        self.connection_switch.connect("state-set", self.on_switch_state_set)
        switch_hbox.pack_end(self.connection_switch, False, False, 0)
        
        conn_card.pack_start(switch_hbox, False, False, 4)
        
        grid = Gtk.Grid(column_spacing=12, row_spacing=10)
        
        acc_title = Gtk.Label(label="Account", xalign=0)
        acc_title.get_style_context().add_class("detail-label")
        grid.attach(acc_title, 0, 0, 1, 1)
        self.acc_val = Gtk.Label(label="Not connected", xalign=1)
        self.acc_val.get_style_context().add_class("detail-value")
        self.acc_val.set_ellipsize(3)
        grid.attach(self.acc_val, 1, 0, 1, 1)
        
        ip_title = Gtk.Label(label="IP Address", xalign=0)
        ip_title.get_style_context().add_class("detail-label")
        grid.attach(ip_title, 0, 1, 1, 1)
        
        ip_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.ip_val = Gtk.Label(label="-", xalign=1)
        self.ip_val.get_style_context().add_class("detail-value")
        ip_hbox.pack_start(self.ip_val, True, True, 0)
        
        copy_btn = Gtk.Button()
        copy_btn.get_style_context().add_class("copy-btn")
        copy_btn.set_relief(Gtk.ReliefStyle.NONE)
        copy_image = Gtk.Image.new_from_icon_name("edit-copy-symbolic", Gtk.IconSize.BUTTON)
        copy_btn.set_image(copy_image)
        copy_btn.set_tooltip_text("Copy IP to Clipboard")
        copy_btn.connect("clicked", self.on_copy_ip_clicked)
        ip_hbox.pack_end(copy_btn, False, False, 0)
        grid.attach(ip_hbox, 1, 1, 1, 1)
        
        exp_title = Gtk.Label(label="Key Expiry", xalign=0)
        exp_title.get_style_context().add_class("detail-label")
        grid.attach(exp_title, 0, 2, 1, 1)
        self.exp_val = Gtk.Label(label="-", xalign=1)
        self.exp_val.get_style_context().add_class("detail-value")
        grid.attach(self.exp_val, 1, 2, 1, 1)
        
        conn_card.pack_start(grid, False, False, 4)
        main_box.pack_start(conn_card, False, False, 0)
        
        # Peers list card (expands to fill vertical layout)
        self.peers_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.peers_card.get_style_context().add_class("card")
        
        peers_title = Gtk.Label(label="ACTIVE PEERS", xalign=0)
        peers_title.get_style_context().add_class("card-title")
        self.peers_card.pack_start(peers_title, False, False, 0)
        
        # Scrolled window exclusively for the listbox
        self.peers_scroll = Gtk.ScrolledWindow()
        self.peers_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.peers_scroll.set_min_content_height(160)
        
        self.peers_listbox = Gtk.ListBox()
        self.peers_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.peers_listbox.set_header_func(None)
        
        self.peers_scroll.add(self.peers_listbox)
        self.peers_card.pack_start(self.peers_scroll, True, True, 0)
        
        main_box.pack_start(self.peers_card, True, True, 0)
        self.peers_card.set_no_show_all(True)
        self.peers_card.hide()
        
        # Footer Action Links
        actions_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        actions_card.get_style_context().add_class("card")
        
        admin_btn = Gtk.Button(label="Admin Console")
        admin_btn.get_style_context().add_class("action-btn")
        admin_btn.connect("clicked", lambda w: webbrowser.open("https://login.tailscale.com/admin"))
        actions_card.pack_start(admin_btn, True, True, 0)
        
        docs_btn = Gtk.Button(label="Docs")
        docs_btn.get_style_context().add_class("action-btn")
        docs_btn.connect("clicked", lambda w: webbrowser.open("https://tailscale.com/kb/"))
        actions_card.pack_start(docs_btn, True, True, 0)
        
        close_btn = Gtk.Button(label="Hide Panel")
        close_btn.get_style_context().add_class("action-btn")
        close_btn.connect("clicked", lambda w: self.window.hide())
        actions_card.pack_start(close_btn, True, True, 0)
        
        main_box.pack_end(actions_card, False, False, 0)

    def show_window(self):
        if not self.window:
            self.build_window()
        self.window.show_all()
        self.window.present()
        if not self.operator_required:
            self.warning_box.hide()
        if not self.peers_listbox.get_children():
            self.peers_card.hide()

    def on_window_delete(self, window, event):
        self.window.hide()
        return True

    def on_copy_ip_clicked(self, widget):
        ip = self.ip_val.get_text()
        if ip and ip != "-":
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(ip, -1)

    def on_switch_state_set(self, widget, state):
        if self.updating_ui:
            return False
            
        if self.is_connecting:
            return True
            
        is_running = self.status_data.get("BackendState") == "Running"
        if state and not is_running:
            self.connect_tailscale()
        elif not state and is_running:
            self.disconnect_tailscale()
            
        return True

    def on_menu_toggle_connect(self, widget):
        if self.is_connecting:
            return
            
        is_running = self.status_data.get("BackendState") == "Running"
        if is_running:
            self.disconnect_tailscale()
        else:
            self.connect_tailscale()

    def handle_ipc_message(self, message):
        msg = message.strip()
        print(f"Received IPC command: {msg}")
        if msg == "show_gui":
            self.show_window()
        elif msg == "--connect" or msg == "connect":
            self.connect_tailscale()
        elif msg == "--disconnect" or msg == "disconnect":
            self.disconnect_tailscale()
        elif msg == "--toggle" or msg == "toggle":
            is_running = self.status_data.get("BackendState") == "Running"
            if is_running:
                self.disconnect_tailscale()
            else:
                self.connect_tailscale()

    def connect_tailscale(self):
        self.is_connecting = True
        self.operator_required = False
        print("Initiating Tailscale connection...")
        
        # Update Switch UI immediately to Connecting state
        self.updating_ui = True
        self.connection_switch.set_active(True)
        self.connection_switch.set_sensitive(False)
        self.switch_desc.set_text("Connecting...")
        self.updating_ui = False
        
        self.status_badge.set_text("CONNECTING...")
        self.status_badge.get_style_context().remove_class("connected")
        self.status_badge.get_style_context().remove_class("disconnected")
        self.status_badge.get_style_context().add_class("connecting")
        
        def run():
            print("Running 'tailscale up'...")
            res = subprocess.run(["tailscale", "up"], capture_output=True, text=True)
            print(f"'tailscale up' returned exit code: {res.returncode}")
            if res.returncode != 0:
                err = res.stderr.lower() + res.stdout.lower()
                print(f"Error output: {res.stderr.strip()}")
                if "access denied" in err or "permission denied" in err or "prefs write access denied" in err:
                    print("Access denied. Attempting to set operator permissions using pkexec...")
                    username = getpass.getuser()
                    auth_res = subprocess.run(["pkexec", "tailscale", "set", "--operator=" + username], capture_output=True, text=True)
                    print(f"pkexec operator setup returned exit code: {auth_res.returncode}")
                    if auth_res.returncode == 0:
                        print("Operator permission successfully configured. Retrying 'tailscale up'...")
                        retry_res = subprocess.run(["tailscale", "up"], capture_output=True, text=True)
                        print(f"Retry 'tailscale up' returned exit code: {retry_res.returncode}")
                        if retry_res.returncode != 0:
                            print(f"Retry failed: {retry_res.stderr.strip()}")
                            self.check_for_login_url(retry_res.stderr + retry_res.stdout)
                    else:
                        print("User cancelled or failed policykit authentication.")
                        self.operator_required = True
                else:
                    self.check_for_login_url(res.stderr + res.stdout)
            else:
                print("Tailscale successfully connected.")
            self.is_connecting = False
            self.force_refresh()
                
        threading.Thread(target=run, daemon=True).start()

    def check_for_login_url(self, output):
        if "http" in output.lower():
            for line in output.split("\n"):
                if "https://" in line:
                    parts = line.split()
                    for p in parts:
                        if p.startswith("https://"):
                            print(f"Found authentication URL: {p}. Opening in browser...")
                            GLib.idle_add(webbrowser.open, p)
                            break

    def disconnect_tailscale(self):
        self.operator_required = False
        print("Initiating Tailscale disconnection...")
        
        # Update Switch UI immediately to Disconnecting state
        self.updating_ui = True
        self.connection_switch.set_active(False)
        self.connection_switch.set_sensitive(False)
        self.switch_desc.set_text("Disconnecting...")
        self.updating_ui = False
        
        def run():
            print("Running 'tailscale down'...")
            res = subprocess.run(["tailscale", "down"], capture_output=True, text=True)
            print(f"'tailscale down' returned exit code: {res.returncode}")
            if res.returncode != 0:
                err = res.stderr.lower() + res.stdout.lower()
                print(f"Error output: {res.stderr.strip()}")
                if "access denied" in err or "permission denied" in err or "prefs write access denied" in err:
                    print("Access denied. Attempting to set operator permissions using pkexec...")
                    username = getpass.getuser()
                    auth_res = subprocess.run(["pkexec", "tailscale", "set", "--operator=" + username], capture_output=True, text=True)
                    if auth_res.returncode == 0:
                        print("Operator permission successfully configured. Retrying 'tailscale down'...")
                        subprocess.run(["tailscale", "down"])
                    else:
                        print("Operator setup failed. Fallback to pkexec tailscale down...")
                        subprocess.run(["pkexec", "tailscale", "down"])
            self.force_refresh()
        threading.Thread(target=run, daemon=True).start()

    def run_configure_operator(self):
        username = getpass.getuser()
        print("Explicit operator configuration requested...")
        def run():
            res = subprocess.run(["pkexec", "tailscale", "set", "--operator=" + username], capture_output=True, text=True)
            print(f"pkexec operator setup returned exit code: {res.returncode}")
            if res.returncode == 0:
                self.operator_required = False
                self.force_refresh()
                self.connect_tailscale()
        threading.Thread(target=run, daemon=True).start()

    def force_refresh(self):
        # Trigger an immediate background poll
        def run():
            try:
                res = subprocess.run(["tailscale", "status", "--json"], capture_output=True, text=True, timeout=5)
                if res.returncode == 0:
                    data = json.loads(res.stdout)
                    GLib.idle_add(self.on_status_updated, data, None)
                else:
                    err_msg = res.stderr.strip()
                    GLib.idle_add(self.on_status_updated, None, err_msg)
            except Exception as e:
                GLib.idle_add(self.on_status_updated, None, str(e))
        threading.Thread(target=run, daemon=True).start()

    def poll_loop(self):
        while self.running:
            try:
                res = subprocess.run(["tailscale", "status", "--json"], capture_output=True, text=True, timeout=5)
                if res.returncode == 0:
                    data = json.loads(res.stdout)
                    GLib.idle_add(self.on_status_updated, data, None)
                else:
                    err_msg = res.stderr.strip()
                    GLib.idle_add(self.on_status_updated, None, err_msg)
            except Exception as e:
                GLib.idle_add(self.on_status_updated, None, str(e))
                
            # Sleep 3 seconds in small increments to stop quickly
            for _ in range(30):
                if not self.running:
                    break
                time.sleep(0.1)

    def on_status_updated(self, data, error_msg):
        if data:
            self.status_data = data
            state = data.get("BackendState", "Stopped")
            
            if state == "Running":
                self.indicator.set_icon_full(ICON_CONNECTED, "Connected")
                self.status_badge.set_text("CONNECTED")
                self.status_badge.get_style_context().remove_class("disconnected")
                self.status_badge.get_style_context().remove_class("connecting")
                self.status_badge.get_style_context().add_class("connected")
                
                self.connect_menu_item.set_label("Disconnect")
                self.status_menu_item.set_label("Status: Connected")
                
                ips = data.get("Self", {}).get("TailscaleIPs", [])
                ip_str = ips[0] if ips else "-"
                self.ip_val.set_text(ip_str)
                self.ip_menu_item.set_label(f"IP: {ip_str}")
                self.ip_menu_item.show()
                
                acc = data.get("CurrentTailnet", {}).get("Name", "")
                if not acc:
                    user_dict = data.get("User", {})
                    if user_dict:
                        acc = list(user_dict.values())[0].get("LoginName", "")
                self.acc_val.set_text(acc if acc else "Unknown")
                
                expiry = data.get("Self", {}).get("KeyExpiry", "")
                if expiry:
                    expiry_date = expiry.split("T")[0]
                    self.exp_val.set_text(expiry_date)
                else:
                    self.exp_val.set_text("-")
                    
                peers = data.get("Peer", {})
                self.update_peers_ui(peers)
                
            elif state in ["Starting", "NeedsLogin", "Connecting"]:
                self.indicator.set_icon_full(ICON_CONNECTING, "Connecting")
                self.status_badge.set_text("CONNECTING...")
                self.status_badge.get_style_context().remove_class("connected")
                self.status_badge.get_style_context().remove_class("disconnected")
                self.status_badge.get_style_context().add_class("connecting")
                
                self.connect_menu_item.set_label("Connecting...")
                self.status_menu_item.set_label("Status: Connecting")
                self.ip_menu_item.hide()
                
                self.acc_val.set_text("Connecting...")
                self.ip_val.set_text("-")
                self.exp_val.set_text("-")
                self.peers_card.hide()
                
            else:
                self.indicator.set_icon_full(ICON_DISCONNECTED, "Disconnected")
                self.status_badge.set_text("STOPPED")
                self.status_badge.get_style_context().remove_class("connected")
                self.status_badge.get_style_context().remove_class("connecting")
                self.status_badge.get_style_context().add_class("disconnected")
                
                self.connect_menu_item.set_label("Connect")
                self.status_menu_item.set_label("Status: Stopped")
                self.ip_menu_item.hide()
                
                self.acc_val.set_text("Disconnected")
                self.ip_val.set_text("-")
                self.exp_val.set_text("-")
                self.peers_card.hide()
                
        else:
            self.status_data = {}
            if error_msg and "tailscale" in error_msg.lower():
                self.status_badge.set_text("SERVICE ERROR")
                self.acc_val.set_text("Daemon not running?")
            else:
                self.status_badge.set_text("STOPPED")
                self.acc_val.set_text("Disconnected")
                
            self.indicator.set_icon_full(ICON_DISCONNECTED, "Disconnected")
            self.connect_menu_item.set_label("Connect")
            self.status_menu_item.set_label("Status: Stopped")
            self.ip_menu_item.hide()
            self.ip_val.set_text("-")
            self.exp_val.set_text("-")
            self.peers_card.hide()

        # Handle toggle switch states
        self.updating_ui = True
        state = self.status_data.get("BackendState", "Stopped")
        if self.is_connecting:
            self.connection_switch.set_active(True)
            self.connection_switch.set_sensitive(False)
            self.switch_desc.set_text("Connecting...")
        elif state == "Running":
            self.connection_switch.set_active(True)
            self.connection_switch.set_sensitive(True)
            self.switch_desc.set_text("Connected")
        elif state in ["Starting", "Connecting"]:
            self.connection_switch.set_active(True)
            self.connection_switch.set_sensitive(False)
            self.switch_desc.set_text("Connecting...")
        else:
            self.connection_switch.set_active(False)
            self.connection_switch.set_sensitive(True)
            self.switch_desc.set_text("Disconnected")
        self.updating_ui = False

        if self.operator_required:
            self.warning_box.show()
        else:
            self.warning_box.hide()

    def update_peers_ui(self, peers):
        for child in self.peers_listbox.get_children():
            self.peers_listbox.remove(child)
            
        if not peers:
            self.peers_card.hide()
            return
            
        online_peers = [p for p in peers.values() if p.get("Online")]
        offline_peers = [p for p in peers.values() if not p.get("Online")]
        
        sorted_peers = sorted(online_peers, key=lambda x: x.get("HostName", "").lower()) + \
                       sorted(offline_peers, key=lambda x: x.get("HostName", "").lower())
                       
        display_peers = sorted_peers[:10]
        
        for peer in display_peers:
            row = Gtk.ListBoxRow()
            row.get_style_context().add_class("peer-row")
            
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            
            dot = Gtk.Box()
            dot.set_size_request(8, 8)
            dot.set_valign(Gtk.Align.CENTER)
            dot.get_style_context().add_class("online-dot" if peer.get("Online") else "offline-dot")
            hbox.pack_start(dot, False, False, 4)
            
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            
            name_lbl = Gtk.Label(label=peer.get("HostName", "Unknown"), xalign=0)
            name_lbl.get_style_context().add_class("peer-name")
            vbox.pack_start(name_lbl, False, False, 0)
            
            peer_ips = peer.get("TailscaleIPs", ["-"])
            ip_lbl = Gtk.Label(label=peer_ips[0] if peer_ips else "-", xalign=0)
            ip_lbl.get_style_context().add_class("peer-ip")
            vbox.pack_start(ip_lbl, False, False, 0)
            
            hbox.pack_start(vbox, True, True, 0)
            
            os_name = peer.get("OS", "unknown")
            os_badge = Gtk.Label(label=os_name.capitalize())
            os_badge.get_style_context().add_class("peer-os-badge")
            os_badge.set_valign(Gtk.Align.CENTER)
            hbox.pack_end(os_badge, False, False, 4)
            
            row.add(hbox)
            self.peers_listbox.add(row)
            
        self.peers_scroll.show_all()
        self.peers_card.show()

    def quit(self, widget=None):
        self.running = False
        try:
            # Wake up IPC listener from blocking accept()
            temp_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            temp_sock.connect(SOCKET_PATH)
            temp_sock.close()
        except Exception:
            pass
            
        try:
            if os.path.exists(SOCKET_PATH):
                os.unlink(SOCKET_PATH)
        except OSError:
            pass
            
        Gtk.main_quit()

if __name__ == "__main__":
    check_single_instance()
    
    # Set GNOME program name for taskbar matching
    GLib.set_prgname("tailscale-launcher")
    GLib.set_application_name("Tailscale Launcher")
    
    app = TailscaleLauncherApp()
    
    # Handle termination signals cleanly
    import signal
    signal.signal(signal.SIGINT, lambda sig, frame: app.quit())
    signal.signal(signal.SIGTERM, lambda sig, frame: app.quit())
    
    Gtk.main()
