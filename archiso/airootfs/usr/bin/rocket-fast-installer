#!/usr/bin/env python3
"""
Rocket Fast Installer — Cyberpunk Neon UI
Centro de control y gestor de paquetes para Rocket OS.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk, Gio, GLib, Pango
import subprocess, json, os, threading
from pathlib import Path

APP_ID = "os.rocket.fast-installer"
VERSION = "1.0.0"

# ── Catálogo de módulos ──────────────────────────────────
MODULES = {
    "gaming": {
        "icon": "input-gaming-symbolic",
        "title": "🎮 Gaming",
        "packages": [
            {"name":"steam","desc":"Plataforma de juegos Steam","suggested":True},
            {"name":"lutris","desc":"Gestor de juegos universal"},
            {"name":"heroic-games-launcher","desc":"Launcher para Epic/GOG"},
            {"name":"mangohud","desc":"Overlay de rendimiento en juegos","suggested":True},
            {"name":"gamemode","desc":"Optimización automática al jugar","suggested":True},
            {"name":"wine-staging","desc":"Capa de compatibilidad Windows"},
            {"name":"proton-ge-custom","desc":"Proton GE para Steam"},
            {"name":"vkd3d-proton","desc":"DirectX 12 → Vulkan"},
            {"name":"dxvk","desc":"DirectX 9/10/11 → Vulkan","suggested":True},
        ]
    },
    "drivers": {
        "icon": "preferences-system-symbolic",
        "title": "🔧 Drivers",
        "packages": [
            {"name":"nvidia-dkms","desc":"Driver NVIDIA propietario (GPUs modernas)"},
            {"name":"nvidia-470xx-dkms","desc":"Driver NVIDIA legacy (GPUs antiguas)"},
            {"name":"mesa","desc":"Drivers OpenGL/Vulkan AMD/Intel","suggested":True},
            {"name":"vulkan-radeon","desc":"Vulkan para AMD"},
            {"name":"vulkan-intel","desc":"Vulkan para Intel"},
            {"name":"xf86-video-amdgpu","desc":"X11 driver AMD"},
            {"name":"pipewire","desc":"Audio moderno (recomendado)","suggested":True},
            {"name":"pipewire-pulse","desc":"Compatibilidad PulseAudio","suggested":True},
            {"name":"pulseaudio","desc":"Audio clásico (hardware viejo)"},
            {"name":"bluez","desc":"Soporte Bluetooth","suggested":True},
            {"name":"blueman","desc":"Gestor gráfico Bluetooth"},
        ]
    },
    "apps": {
        "icon": "system-software-install-symbolic",
        "title": "📦 Aplicaciones",
        "packages": [
            {"name":"firefox","desc":"Navegador web"},
            {"name":"chromium","desc":"Navegador Chromium"},
            {"name":"vlc","desc":"Reproductor multimedia"},
            {"name":"gimp","desc":"Editor de imágenes"},
            {"name":"libreoffice-fresh","desc":"Suite ofimática"},
            {"name":"thunderbird","desc":"Cliente de correo"},
            {"name":"obs-studio","desc":"Streaming y grabación"},
            {"name":"kdenlive","desc":"Editor de video"},
            {"name":"filemanager (thunar/dolphin)","desc":"Gestor de archivos"},
        ]
    },
    "network": {
        "icon": "network-wireless-symbolic",
        "title": "🌐 Red & Optimización",
        "packages": [
            {"name":"networkmanager","desc":"Gestor de red","suggested":True},
            {"name":"iwd","desc":"WiFi backend moderno (WPA3)","suggested":True},
            {"name":"nftables","desc":"Firewall moderno"},
            {"name":"ufw","desc":"Firewall simplificado"},
            {"name":"wireguard-tools","desc":"VPN WireGuard"},
            {"name":"iptraf-ng","desc":"Monitor de tráfico de red"},
        ]
    },
    "privacy": {
        "icon": "security-high-symbolic",
        "title": "🛡️ Privacidad & Seguridad",
        "packages": [
            {"name":"apparmor","desc":"Control de acceso obligatorio"},
            {"name":"firejail","desc":"Sandbox para aplicaciones"},
            {"name":"clamav","desc":"Antivirus open-source"},
            {"name":"keepassxc","desc":"Gestor de contraseñas"},
            {"name":"tor","desc":"Red de anonimato"},
        ]
    },
    "system": {
        "icon": "utilities-system-monitor-symbolic",
        "title": "⚙️ Sistema",
        "packages": [
            {"name":"btop","desc":"Monitor de recursos avanzado","suggested":True,"warning":"Recomendado para monitorear rendimiento"},
            {"name":"timeshift","desc":"Snapshots del sistema (Btrfs)","suggested":True},
            {"name":"zram-generator","desc":"Compresión de RAM","suggested":True},
            {"name":"thermald","desc":"Control térmico Intel"},
            {"name":"tlp","desc":"Ahorro de batería laptops"},
            {"name":"powertop","desc":"Diagnóstico de energía"},
            {"name":"flatpak","desc":"Apps universales Flatpak"},
        ]
    },
    "rocket_mode": {
        "icon": "media-playback-start-symbolic",
        "title": "🚀 Rocket Mode",
        "packages": [
            {"name":"rocket-mode","desc":"Dual boot gaming inteligente","suggested":True},
            {"name":"ntfs-3g","desc":"Soporte NTFS para Windows","suggested":True},
            {"name":"efibootmgr","desc":"Gestión de arranque EFI","suggested":True},
        ]
    },
}


NEON_CSS = """
window.rocket-installer {
    background: #080810;
}
.neon-sidebar {
    background: linear-gradient(180deg, #0a0a18 0%, #08081a 100%);
    border-right: 1px solid rgba(0, 240, 255, 0.15);
    padding: 8px 0;
    min-width: 220px;
}
.sidebar-title {
    font-family: 'Orbitron', 'Inter', monospace;
    font-size: 18px;
    font-weight: 900;
    padding: 16px 14px 8px;
    letter-spacing: 2px;
}
.sidebar-title-rocket {
    color: #00f0ff;
    text-shadow: 0 0 20px rgba(0, 240, 255, 0.6);
}
.sidebar-btn {
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 10px 16px;
    color: rgba(200, 220, 255, 0.6);
    font-size: 13px;
    font-weight: 600;
    border-left: 3px solid transparent;
    transition: all 150ms ease;
}
.sidebar-btn:hover {
    background: rgba(0, 240, 255, 0.06);
    color: #00f0ff;
    border-left-color: rgba(0, 240, 255, 0.4);
}
.sidebar-btn.active {
    background: rgba(0, 240, 255, 0.1);
    color: #00f0ff;
    border-left-color: #00f0ff;
    text-shadow: 0 0 8px rgba(0, 240, 255, 0.5);
}
.content-area {
    background: #0c0c18;
    padding: 20px 24px;
}
.section-title {
    font-family: 'Orbitron', 'Inter', monospace;
    font-size: 20px;
    font-weight: 800;
    color: #00f0ff;
    text-shadow: 0 0 15px rgba(0, 240, 255, 0.4);
    margin-bottom: 8px;
    letter-spacing: 1px;
}
.pkg-row {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(0, 240, 255, 0.08);
    border-radius: 12px;
    padding: 10px 16px;
    margin: 3px 0;
    transition: all 150ms ease;
}
.pkg-row:hover {
    background: rgba(0, 240, 255, 0.05);
    border-color: rgba(0, 240, 255, 0.2);
}
.pkg-name {
    font-weight: 700;
    font-size: 13px;
    color: #e0e8ff;
}
.pkg-desc {
    font-size: 11px;
    color: rgba(180, 200, 230, 0.55);
}
.pkg-suggested {
    background: rgba(0, 240, 255, 0.08);
    border: 1px solid rgba(0, 240, 255, 0.12);
    padding: 1px 8px;
    border-radius: 6px;
    font-size: 9px;
    font-weight: 700;
    color: #00f0ff;
    letter-spacing: 0.5px;
}
.pkg-warning {
    font-size: 10px;
    color: #ffb020;
    font-style: italic;
}
.neon-install-btn {
    background: linear-gradient(135deg, #00c8e0, #0090ff);
    color: #000;
    font-weight: 800;
    font-size: 14px;
    border-radius: 12px;
    padding: 12px 32px;
    border: none;
    box-shadow: 0 0 25px rgba(0, 200, 255, 0.4);
    letter-spacing: 1px;
}
.neon-install-btn:hover {
    background: linear-gradient(135deg, #00e0ff, #00b0ff);
    box-shadow: 0 0 40px rgba(0, 230, 255, 0.6);
}
.status-line {
    background: rgba(0, 0, 0, 0.5);
    border-top: 1px solid rgba(0, 240, 255, 0.1);
    padding: 6px 16px;
    font-size: 11px;
    color: rgba(0, 240, 255, 0.5);
    font-family: monospace;
}
.net-diag-card {
    background: rgba(0, 240, 255, 0.04);
    border: 1px solid rgba(0, 240, 255, 0.15);
    border-radius: 14px;
    padding: 16px;
}
.net-diag-title {
    font-weight: 800;
    color: #00f0ff;
    font-size: 13px;
}
.net-diag-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 22px;
    font-weight: 800;
    color: #ffffff;
}
"""


def load_neon_css():
    prov = Gtk.CssProvider()
    prov.load_from_data(NEON_CSS.encode())
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), prov,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


def run_pacman_install(packages, callback):
    """Instala paquetes via pacman en hilo separado."""
    def _thread():
        pkg_str = " ".join(packages)
        result = subprocess.run(
            ["pkexec", "pacman", "-S", "--noconfirm", "--needed"] + packages,
            capture_output=True, text=True
        )
        GLib.idle_add(callback, result.returncode == 0, result.stderr or result.stdout)
    threading.Thread(target=_thread, daemon=True).start()


class PackageRow(Gtk.Box):
    def __init__(self, pkg_info):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.add_css_class("pkg-row")
        self.pkg = pkg_info

        self.check = Gtk.CheckButton()
        self.check.set_active(pkg_info.get("suggested", False))
        self.append(self.check)

        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_box.set_hexpand(True)

        name_row = Gtk.Box(spacing=8)
        name_lbl = Gtk.Label(label=pkg_info["name"])
        name_lbl.add_css_class("pkg-name")
        name_lbl.set_halign(Gtk.Align.START)
        name_row.append(name_lbl)

        if pkg_info.get("suggested"):
            sug = Gtk.Label(label="SUGERIDO")
            sug.add_css_class("pkg-suggested")
            name_row.append(sug)

        info_box.append(name_row)

        desc = Gtk.Label(label=pkg_info["desc"])
        desc.add_css_class("pkg-desc")
        desc.set_halign(Gtk.Align.START)
        info_box.append(desc)

        if pkg_info.get("warning"):
            warn = Gtk.Label(label=f"⚠ {pkg_info['warning']}")
            warn.add_css_class("pkg-warning")
            warn.set_halign(Gtk.Align.START)
            info_box.append(warn)

        self.append(info_box)

    def is_selected(self):
        return self.check.get_active()


class RocketFastInstaller(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Rocket Fast Installer")
        self.set_default_size(960, 640)
        self.add_css_class("rocket-installer")
        load_neon_css()

        self.pkg_rows = {}
        self.active_section = None
        self.sidebar_buttons = {}

        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)

        # ── Sidebar ──
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar.add_css_class("neon-sidebar")

        title_lbl = Gtk.Label()
        title_lbl.set_markup("<span weight='ultrabold' size='14000'>🚀 ROCKET</span>")
        title_lbl.add_css_class("sidebar-title")
        title_lbl.add_css_class("sidebar-title-rocket")
        title_lbl.set_halign(Gtk.Align.START)
        sidebar.append(title_lbl)

        sub = Gtk.Label(label="FAST INSTALLER")
        sub.set_halign(Gtk.Align.START)
        sub.set_margin_start(16)
        sub.set_margin_bottom(16)
        sub.set_opacity(0.4)
        sidebar.append(sub)

        sep = Gtk.Separator()
        sidebar.append(sep)

        for key, mod in MODULES.items():
            btn = Gtk.Button(label=mod["title"])
            btn.add_css_class("sidebar-btn")
            btn.connect("clicked", self._on_section, key)
            sidebar.append(btn)
            self.sidebar_buttons[key] = btn

        sidebar.append(Gtk.Box(vexpand=True))  # spacer

        install_btn = Gtk.Button(label="⚡ INSTALAR SELECCIONADOS")
        install_btn.add_css_class("neon-install-btn")
        install_btn.set_margin_start(12)
        install_btn.set_margin_end(12)
        install_btn.set_margin_bottom(12)
        install_btn.connect("clicked", self._on_install)
        sidebar.append(install_btn)

        paned.set_start_child(sidebar)
        paned.set_resize_start_child(False)
        paned.set_shrink_start_child(False)

        # ── Content Area ──
        self.content_stack = Gtk.Stack()
        self.content_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.content_stack.set_transition_duration(200)
        self.content_stack.add_css_class("content-area")

        for key, mod in MODULES.items():
            page = self._build_module_page(key, mod)
            self.content_stack.add_named(page, key)

        paned.set_end_child(self.content_stack)

        # ── Main layout ──
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(paned)

        self.status = Gtk.Label(label="[ROCKET] Sistema listo")
        self.status.add_css_class("status-line")
        self.status.set_halign(Gtk.Align.START)
        self.status.set_hexpand(True)
        main_box.append(self.status)

        self.set_content(main_box)

        # Activar primera sección
        self._on_section(None, "gaming")

    def _build_module_page(self, key, mod):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(8)
        box.set_margin_end(8)

        title = Gtk.Label(label=mod["title"])
        title.add_css_class("section-title")
        title.set_halign(Gtk.Align.START)
        box.append(title)

        self.pkg_rows[key] = []
        for pkg in mod["packages"]:
            row = PackageRow(pkg)
            box.append(row)
            self.pkg_rows[key].append(row)

        # Select all / none buttons
        btn_row = Gtk.Box(spacing=8)
        btn_row.set_margin_top(12)

        sel_all = Gtk.Button(label="Seleccionar todo")
        sel_all.connect("clicked", lambda _: [r.check.set_active(True) for r in self.pkg_rows[key]])
        btn_row.append(sel_all)

        sel_none = Gtk.Button(label="Deseleccionar todo")
        sel_none.connect("clicked", lambda _: [r.check.set_active(False) for r in self.pkg_rows[key]])
        btn_row.append(sel_none)

        box.append(btn_row)
        scroll.set_child(box)
        return scroll

    def _on_section(self, _btn, key):
        self.content_stack.set_visible_child_name(key)
        for k, b in self.sidebar_buttons.items():
            if k == key:
                b.add_css_class("active")
            else:
                b.remove_css_class("active")
        self.active_section = key

    def _on_install(self, _btn):
        selected = []
        for key, rows in self.pkg_rows.items():
            for row in rows:
                if row.is_selected():
                    selected.append(row.pkg["name"])

        if not selected:
            self.status.set_text("[ROCKET] No hay paquetes seleccionados")
            return

        self.status.set_text(f"[ROCKET] Instalando {len(selected)} paquetes...")
        run_pacman_install(selected, self._install_done)

    def _install_done(self, success, output):
        if success:
            self.status.set_text("[ROCKET] ✅ Instalación completada")
        else:
            self.status.set_text(f"[ROCKET] ❌ Error: {output[:100]}")


class RocketFastApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.connect("activate", lambda app: RocketFastInstaller(app).present())


def main():
    return RocketFastApp().run()

if __name__ == "__main__":
    raise SystemExit(main())
