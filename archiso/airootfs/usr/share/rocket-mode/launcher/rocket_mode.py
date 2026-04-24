#!/usr/bin/env python3
"""
Rocket Mode Launcher — Rocket OS
Detecta juegos instalados en partición Windows y gestiona el arranque dual.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk, GdkPixbuf, Gio
import subprocess, os, json, threading, shutil, struct
from pathlib import Path

APP_ID = "os.rocket.mode"
VERSION = "1.0.0"
CONFIG_FILE = Path.home() / ".config" / "rocket-os" / "rocket-mode.json"

GAME_SCAN_DIRS = [
    "Program Files/Steam/steamapps/common",
    "Program Files (x86)/Steam/steamapps/common",
    "Program Files/Epic Games",
    "Program Files (x86)/Epic Games",
    "Program Files",
    "Program Files (x86)",
    "Games",
]

CSS = """
window {
    background: linear-gradient(135deg, #0d0d1a 0%, #0a0a14 60%, #12091e 100%);
}
.rocket-header {
    background: transparent;
    border-bottom: 1px solid rgba(120, 80, 255, 0.3);
    padding: 8px 16px;
}
.rocket-title {
    font-family: 'Inter', 'Cantarell', sans-serif;
    font-size: 22px;
    font-weight: 800;
    color: #ffffff;
}
.rocket-title span {
    color: #7c4dff;
}
.game-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 12px;
    transition: all 200ms ease;
}
.game-card:hover {
    background: rgba(124,77,255,0.15);
    border-color: rgba(124,77,255,0.5);
}
.game-name {
    font-family: 'Inter', 'Cantarell', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: #e8e8ff;
}
.game-path {
    font-size: 10px;
    color: rgba(200,200,220,0.5);
}
.launch-btn {
    background: linear-gradient(135deg, #7c4dff, #5c2de0);
    color: white;
    border-radius: 10px;
    font-weight: 700;
    padding: 8px 18px;
    border: none;
    box-shadow: 0 4px 20px rgba(124,77,255,0.4);
}
.launch-btn:hover {
    background: linear-gradient(135deg, #9c6dff, #7c4dff);
    box-shadow: 0 6px 28px rgba(124,77,255,0.6);
}
.install-btn {
    background: rgba(255,255,255,0.07);
    color: rgba(200,200,220,0.9);
    border-radius: 10px;
    font-weight: 600;
    padding: 6px 14px;
    border: 1px solid rgba(255,255,255,0.1);
}
.status-bar {
    background: rgba(0,0,0,0.3);
    border-top: 1px solid rgba(120,80,255,0.2);
    padding: 6px 16px;
    font-size: 11px;
    color: rgba(180,180,200,0.7);
}
.search-entry {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    color: white;
    padding: 8px 14px;
}
.section-label {
    font-size: 11px;
    font-weight: 700;
    color: rgba(124,77,255,0.9);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin: 8px 4px 4px 4px;
}
.win-partition-badge {
    background: rgba(0,200,100,0.15);
    border: 1px solid rgba(0,200,100,0.3);
    border-radius: 8px;
    padding: 2px 10px;
    font-size: 11px;
    color: #00c864;
}
.no-win-badge {
    background: rgba(255,80,80,0.15);
    border: 1px solid rgba(255,80,80,0.3);
    border-radius: 8px;
    padding: 2px 10px;
    font-size: 11px;
    color: #ff5050;
}
.spinner-overlay {
    background: rgba(13,13,26,0.85);
}
"""


def load_css():
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS.encode())
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


def find_windows_partitions():
    """Encuentra particiones NTFS montadas o montables."""
    partitions = []
    try:
        result = subprocess.run(
            ["lsblk", "-J", "-o", "NAME,FSTYPE,MOUNTPOINT,LABEL,SIZE"],
            capture_output=True, text=True
        )
        data = json.loads(result.stdout)
        def walk(devices):
            for dev in devices:
                if dev.get("fstype") in ("ntfs", "ntfs-3g"):
                    partitions.append({
                        "name": dev["name"],
                        "mountpoint": dev.get("mountpoint"),
                        "label": dev.get("label", ""),
                        "size": dev.get("size", ""),
                    })
                for child in dev.get("children", []):
                    walk([child])
        walk(data.get("blockdevices", []))
    except Exception:
        pass
    return partitions


def mount_partition(devname, mountpoint="/mnt/rocket-windows"):
    """Monta una partición NTFS si no está montada."""
    os.makedirs(mountpoint, exist_ok=True)
    try:
        subprocess.run(
            ["pkexec", "mount", "-t", "ntfs3", f"/dev/{devname}", mountpoint],
            check=True, capture_output=True
        )
        return mountpoint
    except subprocess.CalledProcessError:
        try:
            subprocess.run(
                ["pkexec", "mount", f"/dev/{devname}", mountpoint],
                check=True, capture_output=True
            )
            return mountpoint
        except Exception:
            return None


def scan_games(mount_path):
    """Escanea directorios comunes de juegos en la partición Windows."""
    games = []
    seen = set()
    base = Path(mount_path)
    for rel in GAME_SCAN_DIRS:
        scan_dir = base / rel
        if not scan_dir.exists():
            continue
        try:
            for entry in scan_dir.iterdir():
                if entry.is_dir() and entry.name not in seen:
                    exe = find_main_exe(entry)
                    if exe:
                        seen.add(entry.name)
                        games.append({
                            "name": entry.name,
                            "path": str(entry),
                            "exe": str(exe),
                            "win_path": to_windows_path(str(exe), mount_path),
                            "source_dir": rel,
                        })
        except PermissionError:
            continue
    return sorted(games, key=lambda g: g["name"].lower())


def find_main_exe(game_dir):
    """Encuentra el ejecutable principal de un juego."""
    exes = []
    try:
        for f in game_dir.glob("*.exe"):
            if not any(x in f.name.lower() for x in
                       ["unins", "crash", "setup", "redist", "vc_", "dxsetup"]):
                exes.append(f)
        if exes:
            return max(exes, key=lambda f: f.stat().st_size)
    except Exception:
        pass
    return None


def to_windows_path(linux_path, mount_path):
    """Convierte path Linux a path Windows (C:\\...)."""
    rel = linux_path.replace(mount_path, "").lstrip("/")
    return "C:\\" + rel.replace("/", "\\")


def set_boot_next_windows():
    """Configura EFI BootNext para arrancar Windows en el siguiente inicio."""
    try:
        result = subprocess.run(
            ["efibootmgr"], capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            if "Windows" in line or "windows" in line:
                boot_num = line[4:8]
                subprocess.run(
                    ["pkexec", "efibootmgr", "--bootnext", boot_num],
                    check=True, capture_output=True
                )
                return True, boot_num
        return False, None
    except Exception as e:
        return False, str(e)


def save_game_launch_config(game_info):
    """Guarda la configuración del juego a lanzar para que Windows lo lea."""
    config_path = Path("/boot/rocket-mode-next.json")
    data = {
        "game_name": game_info["name"],
        "exe_path": game_info["win_path"],
        "return_to_rocket": True,
        "timestamp": GLib.get_monotonic_time(),
    }
    try:
        config_path.write_text(json.dumps(data, indent=2))
        return True
    except PermissionError:
        try:
            import tempfile
            tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            json.dump(data, tmp)
            tmp.close()
            subprocess.run(["pkexec", "cp", tmp.name, str(config_path)], check=True)
            return True
        except Exception:
            return False


class GameCard(Gtk.Box):
    def __init__(self, game_info, on_launch, on_install):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.game_info = game_info
        self.add_css_class("game-card")
        self.set_size_request(180, 140)

        # Icon placeholder (rocket icon por defecto)
        icon = Gtk.Image.new_from_icon_name("applications-games")
        icon.set_pixel_size(48)
        icon.set_opacity(0.8)
        self.append(icon)

        # Game name
        name_label = Gtk.Label(label=game_info["name"])
        name_label.add_css_class("game-name")
        name_label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        name_label.set_max_width_chars(18)
        name_label.set_tooltip_text(game_info["name"])
        self.append(name_label)

        # Source label
        src = game_info.get("source_dir", "").split("/")[-1]
        src_label = Gtk.Label(label=src)
        src_label.add_css_class("game-path")
        self.append(src_label)

        # Buttons
        btn_box = Gtk.Box(spacing=6)
        btn_box.set_halign(Gtk.Align.CENTER)

        launch_btn = Gtk.Button(label="🚀 Jugar")
        launch_btn.add_css_class("launch-btn")
        launch_btn.connect("clicked", lambda _: on_launch(game_info))

        btn_box.append(launch_btn)
        self.append(btn_box)


class InstallerDialog(Adw.Window):
    """Diálogo overlay para instaladores (FitGirl, etc.)"""

    def __init__(self, parent, game_name, exe_path):
        super().__init__(title=f"Instalando: {game_name}", transient_for=parent)
        self.set_default_size(500, 300)
        self.set_modal(True)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(24)
        box.set_margin_bottom(24)
        box.set_margin_start(24)
        box.set_margin_end(24)

        title = Gtk.Label(label=f"Instalando: {game_name}")
        title.add_css_class("rocket-title")
        box.append(title)

        info = Gtk.Label(label="Windows iniciará el instalador en Rocket Mode.\nSe reiniciará automáticamente al terminar.")
        info.set_wrap(True)
        info.set_justify(Gtk.Justification.CENTER)
        box.append(info)

        sep = Gtk.Separator()
        box.append(sep)

        btn_row = Gtk.Box(spacing=12, homogeneous=True)

        retry_btn = Gtk.Button(label="🔄 Reintentar")
        retry_btn.add_css_class("install-btn")
        retry_btn.connect("clicked", self._on_retry)

        terminal_btn = Gtk.Button(label="💻 Terminal")
        terminal_btn.add_css_class("install-btn")
        terminal_btn.connect("clicked", self._on_terminal)

        cancel_btn = Gtk.Button(label="✕ Cancelar y volver")
        cancel_btn.add_css_class("install-btn")
        cancel_btn.connect("clicked", lambda _: self.close())

        btn_row.append(retry_btn)
        btn_row.append(terminal_btn)
        btn_row.append(cancel_btn)
        box.append(btn_row)

        self.set_content(box)

    def _on_retry(self, _btn):
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Reintentar instalación",
            body="El sistema reiniciará en Windows y relanzará el instalador. ¿Continuar?"
        )
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("ok", "Reiniciar")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", lambda d, r: (self._do_reboot_installer() if r == "ok" else None))
        dialog.present()

    def _on_terminal(self, _btn):
        # La terminal Windows se lanza via winpe-script
        subprocess.Popen(["rocket-winterm"], start_new_session=True)

    def _do_reboot_installer(self):
        ok, _ = set_boot_next_windows()
        if ok:
            subprocess.run(["systemctl", "reboot"])


class RocketModeWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Rocket Mode")
        self.set_default_size(1100, 720)
        self.games = []
        self.win_partition = None
        self.mount_path = None

        load_css()
        self._build_ui()
        self._detect_windows()

    def _build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header.add_css_class("rocket-header")
        header.set_margin_start(8)
        header.set_margin_end(8)

        title_label = Gtk.Label()
        title_label.set_markup("<span weight='ultrabold' size='16000' foreground='white'>🚀 Rocket</span><span weight='ultrabold' size='16000' foreground='#7c4dff'> Mode</span>")
        header.append(title_label)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header.append(spacer)

        # Partition badge
        self.partition_badge = Gtk.Label(label="Detectando Windows...")
        self.partition_badge.add_css_class("no-win-badge")
        header.append(self.partition_badge)

        # Search
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Buscar juego...")
        self.search_entry.add_css_class("search-entry")
        self.search_entry.set_size_request(200, -1)
        self.search_entry.connect("search-changed", self._on_search)
        header.append(self.search_entry)

        # Refresh button
        refresh_btn = Gtk.Button.new_from_icon_name("view-refresh")
        refresh_btn.set_tooltip_text("Re-escanear juegos")
        refresh_btn.connect("clicked", lambda _: self._detect_windows())
        header.append(refresh_btn)

        main_box.append(header)

        # Content area (scrollable grid)
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.content_box.set_margin_top(16)
        self.content_box.set_margin_bottom(16)
        self.content_box.set_margin_start(20)
        self.content_box.set_margin_end(20)

        # Loading state
        self.spinner = Gtk.Spinner()
        self.spinner.set_size_request(48, 48)
        self.spinner.set_halign(Gtk.Align.CENTER)
        self.spinner.set_valign(Gtk.Align.CENTER)
        self.spinner.set_vexpand(True)
        self.spinner.start()

        self.status_label = Gtk.Label(label="Buscando partición de Windows...")
        self.status_label.set_halign(Gtk.Align.CENTER)

        loading_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        loading_box.set_valign(Gtk.Align.CENTER)
        loading_box.set_vexpand(True)
        loading_box.append(self.spinner)
        loading_box.append(self.status_label)
        self.content_box.append(loading_box)

        scroll.set_child(self.content_box)
        main_box.append(scroll)

        # Status bar
        self.status_bar = Gtk.Label(label="Rocket Mode — Rocket OS")
        self.status_bar.add_css_class("status-bar")
        self.status_bar.set_halign(Gtk.Align.START)
        main_box.append(self.status_bar)

        self.set_content(main_box)

    def _detect_windows(self):
        self.spinner.start()
        threading.Thread(target=self._scan_thread, daemon=True).start()

    def _scan_thread(self):
        GLib.idle_add(self._set_status, "Detectando particiones NTFS...")
        partitions = find_windows_partitions()

        if not partitions:
            GLib.idle_add(self._show_no_windows)
            return

        part = partitions[0]
        GLib.idle_add(self._set_status, f"Encontrada: /dev/{part['name']} ({part['size']}). Montando...")

        mount = part.get("mountpoint")
        if not mount:
            mount = mount_partition(part["name"])

        if not mount:
            GLib.idle_add(self._show_mount_error, part["name"])
            return

        self.mount_path = mount
        self.win_partition = part

        GLib.idle_add(self._set_status, "Escaneando juegos...")
        games = scan_games(mount)
        GLib.idle_add(self._show_games, games, part)

    def _show_no_windows(self):
        self._clear_content()
        self.spinner.stop()
        self.partition_badge.set_text("Sin partición Windows")
        self.partition_badge.set_css_classes(["no-win-badge"])

        icon = Gtk.Image.new_from_icon_name("dialog-warning")
        icon.set_pixel_size(64)
        icon.set_halign(Gtk.Align.CENTER)

        msg = Gtk.Label()
        msg.set_markup("<b>No se encontró partición Windows</b>\n\n"
                       "Rocket Mode requiere un dual boot con Windows.\n"
                       "Usa Rocket Fast Installer para configurar el dual boot.")
        msg.set_justify(Gtk.Justification.CENTER)
        msg.set_halign(Gtk.Align.CENTER)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_valign(Gtk.Align.CENTER)
        box.set_vexpand(True)
        box.append(icon)
        box.append(msg)

        setup_btn = Gtk.Button(label="Configurar Dual Boot")
        setup_btn.add_css_class("launch-btn")
        setup_btn.set_halign(Gtk.Align.CENTER)
        setup_btn.connect("clicked", lambda _: subprocess.Popen(["rocket-fast-installer", "--section=rocket-mode"]))
        box.append(setup_btn)

        self.content_box.append(box)

    def _show_mount_error(self, devname):
        self._clear_content()
        self.spinner.stop()
        self.status_label.set_text(f"Error montando /dev/{devname}. ¿Permisos de administrador?")

    def _show_games(self, games, partition):
        self._clear_content()
        self.spinner.stop()
        self.games = games

        label = partition.get("label") or f"/dev/{partition['name']}"
        self.partition_badge.set_text(f"Windows: {label} ({partition['size']})")
        self.partition_badge.set_css_classes(["win-partition-badge"])

        if not games:
            empty = Gtk.Label(label="No se encontraron juegos instalados en Windows.\nInstala juegos desde Steam, Epic, etc. o usando Rocket Mode.")
            empty.set_justify(Gtk.Justification.CENTER)
            empty.set_halign(Gtk.Align.CENTER)
            empty.set_valign(Gtk.Align.CENTER)
            empty.set_vexpand(True)
            self.content_box.append(empty)
            return

        section = Gtk.Label(label=f"JUEGOS DETECTADOS ({len(games)})")
        section.add_css_class("section-label")
        section.set_halign(Gtk.Align.START)
        self.content_box.append(section)

        self.grid = Gtk.FlowBox()
        self.grid.set_max_children_per_line(6)
        self.grid.set_min_children_per_line(2)
        self.grid.set_row_spacing(12)
        self.grid.set_column_spacing(12)
        self.grid.set_homogeneous(True)
        self.grid.set_selection_mode(Gtk.SelectionMode.NONE)

        self.all_cards = []
        for g in games:
            card = GameCard(g, self._on_launch, self._on_install)
            self.grid.append(card)
            self.all_cards.append(card)

        self.content_box.append(self.grid)
        self._set_status(f"{len(games)} juegos encontrados en {label}")

    def _on_search(self, entry):
        query = entry.get_text().lower()
        if not hasattr(self, "grid"):
            return
        child = self.grid.get_first_child()
        while child:
            card = child.get_child()
            if hasattr(card, "game_info"):
                visible = query in card.game_info["name"].lower()
                child.set_visible(visible)
            child = child.get_next_sibling()

    def _on_launch(self, game_info):
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=f"🚀 Lanzar en Rocket Mode",
            body=f"Se reiniciará en Windows para ejecutar:\n{game_info['name']}\n\nAl cerrar el juego, volverás automáticamente a Rocket OS."
        )
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("launch", "🚀 Jugar ahora")
        dialog.set_response_appearance("launch", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", lambda d, r: self._do_launch(game_info) if r == "launch" else None)
        dialog.present()

    def _do_launch(self, game_info):
        save_game_launch_config(game_info)
        ok, info = set_boot_next_windows()
        if ok:
            self._set_status(f"Reiniciando para lanzar: {game_info['name']}...")
            GLib.timeout_add(1500, lambda: subprocess.run(["systemctl", "reboot"]))
        else:
            self._show_error("No se pudo configurar el arranque Windows.\nVerifica que efibootmgr esté instalado y Windows tenga entrada EFI.")

    def _on_install(self, game_info):
        dlg = InstallerDialog(self, game_info["name"], game_info["exe"])
        dlg.present()

    def _show_error(self, msg):
        dialog = Adw.MessageDialog(transient_for=self, heading="Error", body=msg)
        dialog.add_response("ok", "Cerrar")
        dialog.present()

    def _clear_content(self):
        child = self.content_box.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.content_box.remove(child)
            child = nxt

    def _set_status(self, msg):
        self.status_bar.set_text(msg)
        return False


class RocketModeApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self._on_activate)

    def _on_activate(self, app):
        win = RocketModeWindow(app)
        win.present()


def main():
    app = RocketModeApp()
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
