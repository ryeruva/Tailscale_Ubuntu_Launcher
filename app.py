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
import urllib.parse
import re
import gi

# Initialize PyGObject and GTK 3
gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, Pango
from gi.repository import AyatanaAppIndicator3 as AppIndicator

# Constants and Paths
APP_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_CONNECTED = os.path.join(APP_DIR, "icons", "tailscale-connected.svg")
ICON_DISCONNECTED = os.path.join(APP_DIR, "icons", "tailscale-disconnected.svg")
ICON_CONNECTING = os.path.join(APP_DIR, "icons", "tailscale-connecting.svg")
ICON_LAUNCHER = os.path.join(APP_DIR, "icons", "tailscale-launcher.svg")
ICON_TAILSEND = os.path.join(APP_DIR, "icons", "tailsend.svg")
SOCKET_PATH = os.path.expanduser("~/.cache/tailscale-launcher.sock")
DEFAULT_DOWNLOAD_DIR = os.path.expanduser("~/Downloads")

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
    margin: 10px 16px;
}

.card-title {
    font-size: 12px;
    font-weight: 700;
    color: #94a3b8;
    margin-bottom: 6px;
}

.detail-label {
    font-size: 13px;
    color: #94a3b8;
}

.detail-value {
    font-size: 14px;
    font-weight: 600;
    color: #f8fafc;
}

switch {
    border-radius: 20px;
    min-height: 28px;
    min-width: 50px;
}

switch:checked {
    background-color: #00c0a5;
    border-color: #00e5c1;
    background-image: none;
}

switch:not(:checked) {
    background-color: #ef4444;
    border-color: #f87171;
    background-image: none;
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

.peer-row:selected {
    background-color: rgba(0, 192, 165, 0.16);
    border: 1px solid #00c0a5;
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
    padding: 8px 14px;
    border: 1px solid #334155;
    background-image: none;
}

.action-btn:hover {
    background-color: #334155;
}

.primary-btn {
    background-color: #00c0a5;
    color: #0f1015;
    font-weight: 700;
    border-radius: 8px;
    padding: 8px 16px;
    border: 1px solid #00e5c1;
    background-image: none;
}

.primary-btn:hover {
    background-color: #00e5c1;
}

.primary-btn:disabled {
    background-color: #1e293b;
    color: #64748b;
    border-color: #2b2d3a;
}

.peer-send-btn {
    background-color: rgba(0, 192, 165, 0.14);
    color: #00e5c1;
    border: 1px solid rgba(0, 192, 165, 0.35);
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 700;
    background-image: none;
}

.peer-send-btn:hover {
    background-color: #00c0a5;
    color: #0f1015;
}

.copy-btn {
    background: transparent;
    border: none;
    color: #00c0a5;
    padding: 0;
    min-width: 0;
    min-height: 0;
    margin: 0;
}
.copy-btn:hover {
    color: #00e5c1;
}

.dropzone {
    background-color: #13141c;
    border: 1px dashed #334155;
    border-radius: 10px;
    padding: 10px;
}

.file-row {
    padding: 6px 10px;
    border-radius: 6px;
    margin-bottom: 4px;
    background-color: #1c1d26;
    border: 1px solid #262836;
}

.status-bar-box {
    background-color: #14151e;
    border-top: 1px solid #222431;
    padding: 10px 16px;
}

.status-ok {
    color: #00e5c1;
    font-size: 12px;
    font-weight: 600;
}

.status-err {
    color: #f87171;
    font-size: 12px;
    font-weight: 600;
}

.status-info {
    color: #94a3b8;
    font-size: 12px;
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


def format_file_size(size_bytes):
    try:
        size = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0 or unit == "TB":
                return f"{int(size)} B" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024.0
    except Exception:
        return "-"


def send_desktop_notification(title, body, icon_path=ICON_TAILSEND):
    try:
        icon_arg = icon_path if os.path.exists(icon_path) else "network-transmit-receive"
        subprocess.Popen(
            ["notify-send", "-a", "TailSend", "-i", icon_arg, title, body],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def get_peer_short_dns(peer):
    dns_name = peer.get("DNSName", "").strip(".")
    if dns_name:
        return dns_name.split(".")[0]
    return ""


def get_peer_display_name(peer):
    host = (peer.get("HostName") or "").strip()
    short_dns = get_peer_short_dns(peer)
    if not host or host.lower() == "localhost":
        return short_dns or "Unknown"
    if short_dns and short_dns.lower() != host.lower().replace(" ", "-"):
        return f"{host} ({short_dns})"
    return host


def get_peer_target(peer):
    ips = peer.get("TailscaleIPs") or []
    if ips:
        return ips[0]
    short_dns = get_peer_short_dns(peer)
    if short_dns:
        return short_dns
    return peer.get("HostName", "")


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
        if sys.argv[1] in ["--tailsend", "tailsend"]:
            extra_files = [os.path.abspath(p) for p in sys.argv[2:] if os.path.exists(p)]
            cmd = "tailsend:" + "|".join(extra_files) if extra_files else "tailsend"
        else:
            cmd = sys.argv[1]

    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        s.connect(SOCKET_PATH)
        if cmd == "--tray":
            # Already running: autostart has nothing to add
            s.close()
            sys.exit(0)
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
            data = conn.recv(4096).decode('utf-8')
            if data:
                GLib.idle_add(app.handle_ipc_message, data)
            conn.close()
        except Exception:
            break


class TailSendWindow:
    """GUI window for sending and receiving files across Tailnet devices via Taildrop."""

    def __init__(self, app):
        self.app = app
        self.window = None
        self.selected_files = []
        self.selected_peer_target = None
        self.is_sending = False
        self.is_receiving = False
        self.peer_rows_by_target = {}

    def build(self):
        self.window = Gtk.Window(title="TailSend — Tailscale File Share")
        self.window.set_default_size(480, 660)
        self.window.set_resizable(True)
        self.window.set_position(Gtk.WindowPosition.CENTER)

        try:
            if os.path.exists(ICON_TAILSEND):
                self.window.set_icon_from_file(ICON_TAILSEND)
            else:
                self.window.set_icon_from_file(ICON_LAUNCHER)
        except Exception:
            pass

        self.window.connect("delete-event", self.on_delete_event)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window.add(main_box)

        # Header Bar
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header_box.get_style_context().add_class("header-bar")

        logo_image = Gtk.Image()
        try:
            icon_file = ICON_TAILSEND if os.path.exists(ICON_TAILSEND) else ICON_LAUNCHER
            pb = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_file, 32, 32)
            logo_image.set_from_pixbuf(pb)
        except Exception:
            logo_image.set_from_icon_name("document-send-symbolic", Gtk.IconSize.BUTTON)
        header_box.pack_start(logo_image, False, False, 0)

        title_lbl = Gtk.Label(label="TailSend")
        title_lbl.get_style_context().add_class("title-label")
        header_box.pack_start(title_lbl, False, False, 0)

        badge_lbl = Gtk.Label(label="TAILDROP")
        badge_lbl.get_style_context().add_class("status-badge")
        badge_lbl.get_style_context().add_class("connected")
        header_box.pack_start(badge_lbl, False, False, 6)

        spacer = Gtk.Box()
        header_box.pack_start(spacer, True, True, 0)

        refresh_btn = Gtk.Button()
        refresh_btn.set_relief(Gtk.ReliefStyle.NONE)
        refresh_btn.set_tooltip_text("Refresh Tailnet devices")
        refresh_btn.set_image(Gtk.Image.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON))
        refresh_btn.connect("clicked", lambda w: self.app.force_refresh())
        header_box.pack_end(refresh_btn, False, False, 0)

        main_box.pack_start(header_box, False, False, 0)

        # 1. Target Peer Selection Card
        peer_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        peer_card.get_style_context().add_class("card")

        peer_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        peer_title = Gtk.Label(label="1. SELECT TARGET DEVICE", xalign=0)
        peer_title.get_style_context().add_class("card-title")
        peer_hdr.pack_start(peer_title, True, True, 0)

        self.target_hint_lbl = Gtk.Label(label="", xalign=1)
        self.target_hint_lbl.get_style_context().add_class("detail-label")
        peer_hdr.pack_end(self.target_hint_lbl, False, False, 0)
        peer_card.pack_start(peer_hdr, False, False, 0)

        peer_scroll = Gtk.ScrolledWindow()
        peer_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        peer_scroll.set_min_content_height(130)

        self.peer_listbox = Gtk.ListBox()
        self.peer_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.peer_listbox.connect("row-selected", self.on_peer_row_selected)
        peer_scroll.add(self.peer_listbox)

        peer_card.pack_start(peer_scroll, True, True, 0)
        main_box.pack_start(peer_card, True, True, 0)

        # 2. Send Files Card (Picker + Drag & Drop)
        send_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        send_card.get_style_context().add_class("card")

        send_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        send_title = Gtk.Label(label="2. FILES TO SEND (DRAG & DROP OR BROWSE)", xalign=0)
        send_title.get_style_context().add_class("card-title")
        send_hdr.pack_start(send_title, True, True, 0)

        self.files_count_lbl = Gtk.Label(label="0 files", xalign=1)
        self.files_count_lbl.get_style_context().add_class("detail-label")
        send_hdr.pack_end(self.files_count_lbl, False, False, 0)
        send_card.pack_start(send_hdr, False, False, 0)

        # Dropzone + File List ScrolledWindow
        self.drop_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.drop_box.get_style_context().add_class("dropzone")

        target_entry = Gtk.TargetEntry.new("text/uri-list", 0, 0)
        self.drop_box.drag_dest_set(Gtk.DestDefaults.ALL, [target_entry], Gdk.DragAction.COPY)
        self.drop_box.connect("drag-data-received", self.on_drag_data_received)
        self.window.drag_dest_set(Gtk.DestDefaults.ALL, [target_entry], Gdk.DragAction.COPY)
        self.window.connect("drag-data-received", self.on_drag_data_received)

        self.files_scroll = Gtk.ScrolledWindow()
        self.files_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.files_scroll.set_min_content_height(105)

        self.files_listbox = Gtk.ListBox()
        self.files_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.files_scroll.add(self.files_listbox)
        self.drop_box.pack_start(self.files_scroll, True, True, 0)

        send_card.pack_start(self.drop_box, True, True, 0)

        # File Action Buttons
        btn_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        add_btn = Gtk.Button(label="Add Files...")
        add_btn.get_style_context().add_class("action-btn")
        add_btn.connect("clicked", self.on_add_files_clicked)
        btn_hbox.pack_start(add_btn, False, False, 0)

        clear_btn = Gtk.Button(label="Clear")
        clear_btn.get_style_context().add_class("action-btn")
        clear_btn.connect("clicked", self.on_clear_files_clicked)
        btn_hbox.pack_start(clear_btn, False, False, 0)

        self.send_btn = Gtk.Button(label="Send via Tailscale")
        self.send_btn.get_style_context().add_class("primary-btn")
        self.send_btn.connect("clicked", self.on_send_clicked)
        btn_hbox.pack_end(self.send_btn, True, True, 0)

        send_card.pack_start(btn_hbox, False, False, 0)
        main_box.pack_start(send_card, True, True, 0)

        # 3. Receive Files Card (Taildrop Inbox -> ~/Downloads)
        recv_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        recv_card.get_style_context().add_class("card")

        recv_title = Gtk.Label(label="INCOMING TAILDROP FILES", xalign=0)
        recv_title.get_style_context().add_class("card-title")
        recv_card.pack_start(recv_title, False, False, 0)

        auto_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        auto_lbl_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        auto_lbl = Gtk.Label(xalign=0)
        auto_lbl.set_markup("<b>Auto-Receive to Folder</b>")
        auto_lbl.get_style_context().add_class("detail-value")
        auto_lbl_vbox.pack_start(auto_lbl, False, False, 0)

        self.recv_dir_lbl = Gtk.Label(label=self.app.download_dir, xalign=0)
        self.recv_dir_lbl.get_style_context().add_class("peer-ip")
        self.recv_dir_lbl.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        auto_lbl_vbox.pack_start(self.recv_dir_lbl, False, False, 0)

        auto_hbox.pack_start(auto_lbl_vbox, True, True, 0)

        self.auto_recv_switch = Gtk.Switch()
        self.auto_recv_switch.set_valign(Gtk.Align.CENTER)
        self.auto_recv_switch.set_active(self.app.auto_receive_enabled)
        self.auto_recv_switch.connect("state-set", self.on_auto_recv_toggled)
        auto_hbox.pack_end(self.auto_recv_switch, False, False, 0)
        recv_card.pack_start(auto_hbox, False, False, 0)

        recv_btn_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        choose_dir_btn = Gtk.Button(label="Change Folder...")
        choose_dir_btn.get_style_context().add_class("action-btn")
        choose_dir_btn.connect("clicked", self.on_change_folder_clicked)
        recv_btn_hbox.pack_start(choose_dir_btn, False, False, 0)

        open_dir_btn = Gtk.Button(label="Open Downloads")
        open_dir_btn.get_style_context().add_class("action-btn")
        open_dir_btn.connect("clicked", self.on_open_folder_clicked)
        recv_btn_hbox.pack_start(open_dir_btn, False, False, 0)

        self.recv_now_btn = Gtk.Button(label="Receive Now")
        self.recv_now_btn.get_style_context().add_class("action-btn")
        self.recv_now_btn.connect("clicked", lambda w: self.app.receive_taildrop_files(manual=True))
        recv_btn_hbox.pack_end(self.recv_now_btn, True, True, 0)

        recv_card.pack_start(recv_btn_hbox, False, False, 0)
        main_box.pack_start(recv_card, False, False, 0)

        # Status Bar Footer
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        status_box.get_style_context().add_class("status-bar-box")

        self.spinner = Gtk.Spinner()
        status_box.pack_start(self.spinner, False, False, 0)

        self.status_lbl = Gtk.Label(
            label="Ready — select a Tailnet device and add files to share.",
            xalign=0,
        )
        self.status_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        self.status_lbl.get_style_context().add_class("status-info")
        status_box.pack_start(self.status_lbl, True, True, 0)

        main_box.pack_end(status_box, False, False, 0)

        self.refresh_files_ui()
        self.update_peers(self.app.status_data.get("Peer", {}))
        self.update_send_button_sensitivity()

    def show(self, preselect_target=None, initial_files=None):
        if not self.window:
            self.build()
        if preselect_target:
            self.selected_peer_target = preselect_target
        if initial_files:
            self.add_files(initial_files)
        self.update_peers(self.app.status_data.get("Peer", {}))
        self.window.show_all()
        self.window.present()

    def on_delete_event(self, window, event):
        self.window.hide()
        return True

    def set_status(self, message, level="info", spinning=False):
        if not self.window:
            return
        ctx = self.status_lbl.get_style_context()
        for cls in ["status-info", "status-ok", "status-err"]:
            ctx.remove_class(cls)
        ctx.add_class(f"status-{level}")
        self.status_lbl.set_text(message)
        self.status_lbl.set_tooltip_text(message)
        if spinning:
            self.spinner.show()
            self.spinner.start()
        else:
            self.spinner.stop()
            self.spinner.hide()

    def update_peers(self, peers):
        if not self.window:
            return
        for child in self.peer_listbox.get_children():
            self.peer_listbox.remove(child)
        self.peer_rows_by_target.clear()

        online_peers = [p for p in peers.values() if p.get("Online")]
        offline_peers = [p for p in peers.values() if not p.get("Online")]
        sorted_peers = sorted(online_peers, key=lambda x: get_peer_display_name(x).lower()) + \
                       sorted(offline_peers, key=lambda x: get_peer_display_name(x).lower())

        if not sorted_peers:
            empty_row = Gtk.ListBoxRow()
            empty_row.set_selectable(False)
            lbl = Gtk.Label(label="No Tailnet peers available. Connect Tailscale first.")
            lbl.get_style_context().add_class("detail-label")
            lbl.set_margin_top(24)
            lbl.set_margin_bottom(24)
            empty_row.add(lbl)
            self.peer_listbox.add(empty_row)
            self.peer_listbox.show_all()
            self.update_send_button_sensitivity()
            return

        row_to_select = None
        for peer in sorted_peers:
            target = get_peer_target(peer)
            display_name = get_peer_display_name(peer)
            is_online = bool(peer.get("Online"))

            row = Gtk.ListBoxRow()
            row.peer_target = target
            row.peer_name = display_name
            row.peer_online = is_online
            row.get_style_context().add_class("peer-row")

            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

            dot = Gtk.Box()
            dot.set_size_request(8, 8)
            dot.set_valign(Gtk.Align.CENTER)
            dot.get_style_context().add_class("online-dot" if is_online else "offline-dot")
            hbox.pack_start(dot, False, False, 4)

            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            name_lbl = Gtk.Label(label=display_name, xalign=0)
            name_lbl.get_style_context().add_class("peer-name")
            vbox.pack_start(name_lbl, False, False, 0)

            ip_lbl = Gtk.Label(label=target, xalign=0)
            ip_lbl.get_style_context().add_class("peer-ip")
            vbox.pack_start(ip_lbl, False, False, 0)

            hbox.pack_start(vbox, True, True, 0)

            os_name = peer.get("OS") or "device"
            os_badge = Gtk.Label(label=os_name.capitalize())
            os_badge.get_style_context().add_class("peer-os-badge")
            os_badge.set_valign(Gtk.Align.CENTER)
            hbox.pack_end(os_badge, False, False, 4)

            row.add(hbox)
            self.peer_listbox.add(row)
            self.peer_rows_by_target[target] = row

            if self.selected_peer_target and target == self.selected_peer_target:
                row_to_select = row
            elif row_to_select is None and is_online:
                row_to_select = row

        if row_to_select is None and sorted_peers:
            first_target = get_peer_target(sorted_peers[0])
            row_to_select = self.peer_rows_by_target.get(first_target)

        self.peer_listbox.show_all()
        if row_to_select is not None:
            self.peer_listbox.select_row(row_to_select)

    def on_peer_row_selected(self, listbox, row):
        if row and hasattr(row, "peer_target"):
            self.selected_peer_target = row.peer_target
            status_tag = "Online" if getattr(row, "peer_online", False) else "Offline"
            self.target_hint_lbl.set_text(f"Target: {row.peer_name} ({status_tag})")
        else:
            self.target_hint_lbl.set_text("")
        self.update_send_button_sensitivity()

    def add_files(self, paths):
        added = 0
        for p in paths:
            abspath = os.path.abspath(p)
            if os.path.isfile(abspath) and abspath not in self.selected_files:
                self.selected_files.append(abspath)
                added += 1
        if added > 0 and self.window:
            self.refresh_files_ui()
            self.set_status(f"Queued {len(self.selected_files)} file(s) for sending.", "info")

    def refresh_files_ui(self):
        if not self.window:
            return
        for child in self.files_listbox.get_children():
            self.files_listbox.remove(child)

        count = len(self.selected_files)
        self.files_count_lbl.set_text(f"{count} file{'s' if count != 1 else ''}")

        if not self.selected_files:
            empty_row = Gtk.ListBoxRow()
            empty_row.set_selectable(False)
            lbl = Gtk.Label(label="Drag & drop files here, or click 'Add Files...'")
            lbl.get_style_context().add_class("detail-label")
            lbl.set_margin_top(26)
            lbl.set_margin_bottom(26)
            empty_row.add(lbl)
            self.files_listbox.add(empty_row)
        else:
            for filepath in list(self.selected_files):
                row = Gtk.ListBoxRow()
                row.set_selectable(False)
                row.get_style_context().add_class("file-row")

                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                icon = Gtk.Image.new_from_icon_name("text-x-generic-symbolic", Gtk.IconSize.MENU)
                hbox.pack_start(icon, False, False, 2)

                name_lbl = Gtk.Label(label=os.path.basename(filepath), xalign=0)
                name_lbl.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
                name_lbl.set_tooltip_text(filepath)
                name_lbl.get_style_context().add_class("detail-value")
                hbox.pack_start(name_lbl, True, True, 0)

                size_str = format_file_size(os.path.getsize(filepath)) if os.path.exists(filepath) else "-"
                size_lbl = Gtk.Label(label=size_str)
                size_lbl.get_style_context().add_class("peer-ip")
                hbox.pack_start(size_lbl, False, False, 4)

                rm_btn = Gtk.Button()
                rm_btn.set_relief(Gtk.ReliefStyle.NONE)
                rm_btn.get_style_context().add_class("copy-btn")
                rm_btn.set_image(Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU))
                rm_btn.set_tooltip_text("Remove file")
                rm_btn.connect("clicked", self.on_remove_single_file, filepath)
                hbox.pack_end(rm_btn, False, False, 0)

                row.add(hbox)
                self.files_listbox.add(row)

        self.files_listbox.show_all()
        self.update_send_button_sensitivity()

    def on_remove_single_file(self, widget, filepath):
        if filepath in self.selected_files:
            self.selected_files.remove(filepath)
            self.refresh_files_ui()

    def on_clear_files_clicked(self, widget):
        self.selected_files.clear()
        self.refresh_files_ui()
        self.set_status("Cleared file queue.", "info")

    def on_add_files_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select Files to Send via TailSend",
            parent=self.window,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )
        dialog.set_select_multiple(True)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filenames = dialog.get_filenames()
            self.add_files(filenames)
        dialog.destroy()

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, timestamp):
        uris = data.get_uris()
        paths = []
        for uri in uris:
            if uri.startswith("file://"):
                parsed = urllib.parse.urlparse(uri)
                local_path = urllib.parse.unquote(parsed.path)
                if os.path.isfile(local_path):
                    paths.append(local_path)
        if paths:
            self.add_files(paths)
        Gtk.drag_finish(drag_context, True, False, timestamp)

    def update_send_button_sensitivity(self):
        if not self.window:
            return
        can_send = (
            not self.is_sending
            and bool(self.selected_files)
            and bool(self.selected_peer_target)
        )
        self.send_btn.set_sensitive(can_send)

    def on_send_clicked(self, widget):
        if self.is_sending or not self.selected_files or not self.selected_peer_target:
            return

        target = self.selected_peer_target
        files_to_send = list(self.selected_files)
        row = self.peer_rows_by_target.get(target)
        peer_label = row.peer_name if row else target

        self.is_sending = True
        self.update_send_button_sensitivity()
        self.set_status(
            f"Sending {len(files_to_send)} file(s) to {peer_label}...",
            level="info",
            spinning=True,
        )

        def worker():
            cmd = ["tailscale", "file", "cp"] + files_to_send + [f"{target}:"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                err_out = (res.stderr + "\n" + res.stdout).strip()
                err_lower = err_out.lower()
                if "access denied" in err_lower or "permission denied" in err_lower or "not allowed" in err_lower:
                    username = getpass.getuser()
                    auth_res = subprocess.run(
                        ["pkexec", "tailscale", "set", "--operator=" + username],
                        capture_output=True,
                        text=True,
                    )
                    if auth_res.returncode == 0:
                        res = subprocess.run(cmd, capture_output=True, text=True)

            def finish():
                self.is_sending = False
                if res.returncode == 0:
                    names = ", ".join(os.path.basename(f) for f in files_to_send[:3])
                    if len(files_to_send) > 3:
                        names += f" (+{len(files_to_send) - 3} more)"
                    msg = f"Sent {len(files_to_send)} file(s) to {peer_label}: {names}"
                    self.selected_files.clear()
                    self.refresh_files_ui()
                    self.set_status(msg, level="ok", spinning=False)
                    send_desktop_notification("TailSend — Transfer Complete", msg)
                else:
                    err_text = (res.stderr or res.stdout or "Unknown error").strip().splitlines()
                    short_err = err_text[-1] if err_text else "Transfer failed"
                    self.set_status(f"Failed: {short_err}", level="err", spinning=False)
                    send_desktop_notification("TailSend — Transfer Failed", short_err)
                self.update_send_button_sensitivity()

            GLib.idle_add(finish)

        threading.Thread(target=worker, daemon=True).start()

    def on_auto_recv_toggled(self, switch, state):
        self.app.auto_receive_enabled = bool(state)
        state_str = "enabled" if state else "disabled"
        self.set_status(f"Auto-receive incoming Taildrop files {state_str}.", "info")
        return False

    def on_change_folder_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select Download Folder for Incoming Taildrop Files",
            parent=self.window,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )
        dialog.set_filename(self.app.download_dir)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            folder = dialog.get_filename()
            if folder and os.path.isdir(folder):
                self.app.download_dir = folder
                self.recv_dir_lbl.set_text(folder)
                self.set_status(f"Receive folder set to {folder}", "info")
        dialog.destroy()

    def on_open_folder_clicked(self, widget):
        os.makedirs(self.app.download_dir, exist_ok=True)
        subprocess.Popen(["xdg-open", self.app.download_dir])


class TailscaleLauncherApp:
    def __init__(self, start_mode="panel", initial_files=None):
        self.running = True
        self.status_data = {}
        self.is_connecting = False
        self.operator_required = False
        self.updating_ui = False
        self.window = None
        self.download_dir = DEFAULT_DOWNLOAD_DIR
        self.auto_receive_enabled = True
        self.receiving_lock = threading.Lock()
        self.tailsend = TailSendWindow(self)

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

        # Show appropriate window on startup
        if start_mode == "tailsend":
            self.show_tailsend(initial_files=initial_files)
        elif len(sys.argv) == 1:
            # (--tray starts with only the tray icon, for autostart)
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

        tailsend_item = Gtk.MenuItem(label="TailSend (Share Files)...")
        tailsend_item.connect("activate", lambda w: self.show_tailsend())
        self.menu.append(tailsend_item)

        recv_item = Gtk.MenuItem(label="Receive Taildrop Files Now")
        recv_item.connect("activate", lambda w: self.receive_taildrop_files(manual=True))
        self.menu.append(recv_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        exit_item = Gtk.MenuItem(label="Exit Launcher")
        exit_item.connect("activate", self.quit)
        self.menu.append(exit_item)

        self.menu.show_all()
        self.indicator.set_menu(self.menu)

    def build_window(self):
        self.window = Gtk.Window(title="Tailscale Control Panel")
        self.window.set_default_size(430, 600)
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

        tailsend_btn = Gtk.Button(label="TailSend")
        tailsend_btn.get_style_context().add_class("primary-btn")
        tailsend_btn.set_tooltip_text("Share & receive files across your Tailnet")
        tailsend_btn.connect("clicked", lambda w: self.show_tailsend())
        actions_card.pack_start(tailsend_btn, True, True, 0)

        admin_btn = Gtk.Button(label="Admin")
        admin_btn.get_style_context().add_class("action-btn")
        admin_btn.connect("clicked", lambda w: webbrowser.open("https://login.tailscale.com/admin"))
        actions_card.pack_start(admin_btn, True, True, 0)

        docs_btn = Gtk.Button(label="Docs")
        docs_btn.get_style_context().add_class("action-btn")
        docs_btn.connect("clicked", lambda w: webbrowser.open("https://tailscale.com/kb/"))
        actions_card.pack_start(docs_btn, True, True, 0)

        close_btn = Gtk.Button(label="Hide")
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

    def show_tailsend(self, preselect_target=None, initial_files=None):
        self.tailsend.show(preselect_target=preselect_target, initial_files=initial_files)

    def on_window_delete(self, window, event):
        self.window.hide()
        return True

    def copy_to_clipboard(self, text):
        if text and text != "-":
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(text, -1)

    def on_copy_ip_clicked(self, widget):
        ip = self.ip_val.get_text()
        self.copy_to_clipboard(ip)

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
        elif msg == "tailsend" or msg == "--tailsend":
            self.show_tailsend()
        elif msg.startswith("tailsend:"):
            raw_files = msg.split(":", 1)[1]
            files = [f for f in raw_files.split("|") if f and os.path.isfile(f)]
            self.show_tailsend(initial_files=files)
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

    def receive_taildrop_files(self, manual=False):
        if not self.receiving_lock.acquire(blocking=False):
            return

        if manual and self.tailsend.window:
            GLib.idle_add(
                self.tailsend.set_status,
                "Checking Taildrop inbox for incoming files...",
                "info",
                True,
            )

        def worker():
            try:
                os.makedirs(self.download_dir, exist_ok=True)
                cmd = [
                    "tailscale",
                    "file",
                    "get",
                    "--conflict=rename",
                    "--verbose",
                    self.download_dir,
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                if res.returncode != 0 and manual:
                    err_lower = (res.stderr + res.stdout).lower()
                    if "access denied" in err_lower or "permission denied" in err_lower or "not allowed" in err_lower:
                        username = getpass.getuser()
                        auth_res = subprocess.run(
                            ["pkexec", "tailscale", "set", "--operator=" + username],
                            capture_output=True,
                            text=True,
                        )
                        if auth_res.returncode == 0:
                            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

                combined = (res.stdout + "\n" + res.stderr).strip()
                saved_files = []
                for line in combined.splitlines():
                    line_s = line.strip()
                    if line_s.startswith("wrote "):
                        filepath = line_s[len("wrote "):].strip()
                        saved_files.append(os.path.basename(filepath))

                moved_count = len(saved_files)
                m = re.search(r"moved\s+(\d+)/(\d+)\s+files", combined)
                if m and moved_count == 0:
                    moved_count = int(m.group(1))

                if res.returncode == 0:
                    if moved_count > 0:
                        names = ", ".join(saved_files) if saved_files else f"{moved_count} file(s)"
                        msg = f"Received {moved_count} file(s) into {self.download_dir}: {names}"
                        GLib.idle_add(self.tailsend.set_status, msg, "ok", False)
                        send_desktop_notification("TailSend — File Received", msg)
                    elif manual:
                        GLib.idle_add(
                            self.tailsend.set_status,
                            "No incoming files waiting in Taildrop inbox.",
                            "info",
                            False,
                        )
                elif manual:
                    err_lines = combined.splitlines()
                    short_err = err_lines[-1] if err_lines else "Could not check Taildrop inbox"
                    GLib.idle_add(
                        self.tailsend.set_status,
                        f"Receive error: {short_err}",
                        "err",
                        False,
                    )
            except Exception as e:
                if manual:
                    GLib.idle_add(self.tailsend.set_status, f"Receive error: {e}", "err", False)
            finally:
                self.receiving_lock.release()

        threading.Thread(target=worker, daemon=True).start()

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
        tick = 0
        while self.running:
            try:
                res = subprocess.run(["tailscale", "status", "--json"], capture_output=True, text=True, timeout=5)
                if res.returncode == 0:
                    data = json.loads(res.stdout)
                    GLib.idle_add(self.on_status_updated, data, None)
                    if self.auto_receive_enabled and data.get("BackendState") == "Running" and (tick % 2 == 0):
                        self.receive_taildrop_files(manual=False)
                else:
                    err_msg = res.stderr.strip()
                    GLib.idle_add(self.on_status_updated, None, err_msg)
            except Exception as e:
                GLib.idle_add(self.on_status_updated, None, str(e))

            tick += 1
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
                self.tailsend.update_peers(peers)

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
                self.tailsend.update_peers({})

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
                self.tailsend.update_peers({})

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
            self.tailsend.update_peers({})

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

        sorted_peers = sorted(online_peers, key=lambda x: get_peer_display_name(x).lower()) + \
                       sorted(offline_peers, key=lambda x: get_peer_display_name(x).lower())

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

            display_name = get_peer_display_name(peer)
            name_lbl = Gtk.Label(label=display_name, xalign=0)
            name_lbl.get_style_context().add_class("peer-name")
            vbox.pack_start(name_lbl, False, False, 0)

            peer_ips = peer.get("TailscaleIPs", ["-"])
            peer_ip = peer_ips[0] if peer_ips else "-"

            peer_ip_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

            ip_lbl = Gtk.Label(label=peer_ip, xalign=0)
            ip_lbl.get_style_context().add_class("peer-ip")
            peer_ip_hbox.pack_start(ip_lbl, False, False, 0)

            if peer_ip != "-":
                peer_copy_btn = Gtk.Button()
                peer_copy_btn.get_style_context().add_class("copy-btn")
                peer_copy_btn.set_relief(Gtk.ReliefStyle.NONE)
                peer_copy_image = Gtk.Image.new_from_icon_name("edit-copy-symbolic", Gtk.IconSize.MENU)
                peer_copy_btn.set_image(peer_copy_image)
                peer_copy_btn.set_tooltip_text("Copy IP to Clipboard")
                peer_copy_btn.connect("clicked", lambda w, ip=peer_ip: self.copy_to_clipboard(ip))
                peer_ip_hbox.pack_start(peer_copy_btn, False, False, 0)

            vbox.pack_start(peer_ip_hbox, False, False, 0)

            hbox.pack_start(vbox, True, True, 0)

            target_id = get_peer_target(peer)
            send_peer_btn = Gtk.Button(label="Send")
            send_peer_btn.get_style_context().add_class("peer-send-btn")
            send_peer_btn.set_valign(Gtk.Align.CENTER)
            send_peer_btn.set_tooltip_text(f"Send files to {display_name} via TailSend")
            send_peer_btn.connect("clicked", lambda w, tgt=target_id: self.show_tailsend(preselect_target=tgt))
            hbox.pack_end(send_peer_btn, False, False, 2)

            os_name = peer.get("OS") or "device"
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

    start_mode = "panel"
    initial_files = []
    if len(sys.argv) > 1 and sys.argv[1] in ["--tailsend", "tailsend"]:
        start_mode = "tailsend"
        initial_files = [os.path.abspath(p) for p in sys.argv[2:] if os.path.isfile(p)]

    # Set GNOME program name for taskbar matching
    GLib.set_prgname("tailscale-launcher")
    GLib.set_application_name("Tailscale Launcher")

    app = TailscaleLauncherApp(start_mode=start_mode, initial_files=initial_files)

    # Handle termination signals cleanly
    import signal
    signal.signal(signal.SIGINT, lambda sig, frame: app.quit())
    signal.signal(signal.SIGTERM, lambda sig, frame: app.quit())

    Gtk.main()
