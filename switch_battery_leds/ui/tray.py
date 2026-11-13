#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Icône dans la zone de notification (systray), dessin dynamique et boucle d'événements.
"""

import ctypes
import queue
import threading
from typing import Any, Optional

from switch_battery_leds.autostart import fatal
from switch_battery_leds.ui.settings_window import SettingsWindow


def make_tray_image(percent: Optional[int], charging: bool, connected: bool):
    """Icône 64x64 : fond coloré selon le niveau, pourcentage au centre."""
    from PIL import Image, ImageDraw, ImageFont

    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if not connected or percent is None:
        color, text = (110, 110, 110, 255), "--"
    else:
        color = (
            (46, 160, 67, 255)
            if percent >= 25
            else (219, 140, 20, 255)
            if percent >= 10
            else (207, 48, 48, 255)
        )
        text = str(percent)
    d.rounded_rectangle(
        (1, 1, size - 2, size - 2),
        radius=14,
        fill=color,
        outline=(255, 255, 255, 255) if charging else None,
        width=5,
    )
    font_size = 46 if len(text) <= 2 else 31
    font = None
    for name in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            font = ImageFont.truetype(name, font_size)
            break
        except Exception:
            pass
    if font is None:
        font = ImageFont.load_default()
    try:
        d.text((size / 2, size / 2 + 1), text, font=font, fill="white", anchor="mm")
    except Exception:
        d.text((6, 20), text, font=font, fill="white")
    return img


def run_tray(settings: Any, monitor: Any) -> None:
    try:
        import tkinter as tk
        import pystray
        from PIL import Image  # noqa: F401
    except ImportError as err:
        fatal(f"Module manquant : {err}\nInstalle-le avec :  pip install pystray pillow")

    try:  # texte net sur les écrans à haute densité
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()
    root.withdraw()
    commands: queue.Queue = queue.Queue()
    ui = {"signature": None, "window": None}

    def refresh_tray():
        """Appelé depuis le thread de surveillance quand l'état change."""
        st = monitor.status
        signature = (st["connected"], st["percent"], st["charging"])
        text = monitor.status_text()
        try:
            if signature != ui["signature"]:
                ui["signature"] = signature
                icon.icon = make_tray_image(st["percent"], st["charging"], st["connected"])
            icon.title = text[:127]
            icon.update_menu()
        except Exception:
            pass

    def toggle_notifications(icon_, item):
        settings.notifications = not settings.notifications
        settings.save()
        monitor.apply_settings()

    menu = pystray.Menu(
        pystray.MenuItem(lambda item: monitor.status_text(), None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "Paramètres...", lambda icon_, item: commands.put("settings"), default=True
        ),
        pystray.MenuItem(
            "Notifications",
            toggle_notifications,
            checked=lambda item: settings.notifications,
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quitter", lambda icon_, item: commands.put("quit")),
    )
    icon = pystray.Icon(
        "switch_battery_leds",
        make_tray_image(None, False, False),
        monitor.status_text(),
        menu,
    )

    worker = threading.Thread(target=monitor.run, name="surveillance", daemon=True)

    def open_settings():
        win = ui["window"]
        if win and win.exists():
            win.focus()
        else:
            ui["window"] = SettingsWindow(root, settings, monitor)
            ui["window"].focus()

    def poll():
        try:
            while True:
                command = commands.get_nowait()
                if command == "settings":
                    open_settings()
                elif command == "quit":
                    root.quit()
                    return
        except queue.Empty:
            pass
        root.after(200, poll)

    monitor.on_status = refresh_tray
    icon.run_detached()
    worker.start()
    root.after(200, poll)
    try:
        root.mainloop()
    finally:
        monitor.stop()
        worker.join(timeout=5)  # laisse le temps de remettre les LED sur « joueur 1 »
        try:
            icon.stop()
        except Exception:
            pass
        try:
            root.destroy()
        except Exception:
            pass
