#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zone de notification (systray) native Windows avec PyQt6 (QSystemTrayIcon).
"""

import sys
import threading
from typing import Any, Optional

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from switch_battery_leds.autostart import fatal
from switch_battery_leds.constants import APP_NAME
from switch_battery_leds.ui.settings_window import SettingsWindow


def make_tray_pixmap(percent: Optional[int], charging: bool, connected: bool) -> QPixmap:
    """Génère un pixmap 64x64 net avec fond coloré arrondi et pourcentage centré."""
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # Détermination de la couleur et du texte
    if not connected or percent is None:
        bg_color = QColor(110, 110, 110)
        text = "--"
    else:
        if percent >= 25:
            bg_color = QColor(46, 160, 67)    # Vert
        elif percent >= 10:
            bg_color = QColor(219, 140, 20)   # Orange
        else:
            bg_color = QColor(207, 48, 48)    # Rouge
        text = str(percent)

    # Contour blanc pendant la charge
    if charging:
        pen = QPen(QColor(255, 255, 255), 4)
        painter.setPen(pen)
    else:
        painter.setPen(Qt.PenStyle.NoPen)

    painter.setBrush(bg_color)
    margin = 3 if charging else 2
    painter.drawRoundedRect(
        margin, margin, size - margin * 2, size - margin * 2, 14, 14
    )

    # Texte centré
    painter.setPen(QColor(255, 255, 255))
    font_size = 28 if len(text) <= 2 else 20
    font = QFont("Segoe UI", font_size, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)

    painter.end()
    return pixmap


def make_tray_icon(percent: Optional[int], charging: bool, connected: bool) -> QIcon:
    return QIcon(make_tray_pixmap(percent, charging, connected))


class MonitorBridge(QObject):
    """Pont de communication thread-safe entre le thread Monitor et la boucle d'événements Qt."""
    status_changed = pyqtSignal()


def run_tray(settings: Any, monitor: Any) -> None:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Empêche l'application de se fermer quand on ferme la fenêtre des paramètres
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName(APP_NAME)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        fatal("La zone de notification système (systray) n'est pas disponible.")

    # Icône systray
    initial_icon = make_tray_icon(None, False, False)
    tray = QSystemTrayIcon(initial_icon, app)
    tray.setToolTip(monitor.status_text())

    # Fenêtre des paramètres
    settings_win = SettingsWindow(settings, monitor)

    # Menu contextuel
    menu = QMenu()
    menu.setStyleSheet("""
        QMenu {
            background-color: #2b2b2b;
            color: #ffffff;
            border: 1px solid #3f3f3f;
            border-radius: 8px;
            padding: 5px;
            font-family: 'Segoe UI', sans-serif;
            font-size: 13px;
        }
        QMenu::item {
            padding: 6px 20px 6px 12px;
            border-radius: 4px;
        }
        QMenu::item:selected {
            background-color: #0078d4;
        }
        QMenu::separator {
            height: 1px;
            background: #3f3f3f;
            margin: 4px 6px;
        }
    """)

    action_status = QAction(monitor.status_text(), menu)
    action_status.setEnabled(False)
    menu.addAction(action_status)

    menu.addSeparator()

    action_settings = QAction("Paramètres...", menu)
    action_settings.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
    action_settings.triggered.connect(settings_win.focus)
    menu.addAction(action_settings)

    action_notif = QAction("Notifications", menu)
    action_notif.setCheckable(True)
    action_notif.setChecked(settings.notifications)

    def toggle_notifications():
        settings.notifications = action_notif.isChecked()
        settings.save()
        monitor.apply_settings()
        if settings_win.isVisible():
            settings_win.chk_notif.setChecked(settings.notifications)

    action_notif.triggered.connect(toggle_notifications)
    menu.addAction(action_notif)

    menu.addSeparator()

    action_quit = QAction("Quitter", menu)
    action_quit.triggered.connect(app.quit)
    menu.addAction(action_quit)

    tray.setContextMenu(menu)

    # Clic gauche sur l'icône -> ouvrir / basculer les paramètres
    def on_tray_activated(reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            if settings_win.isVisible() and not settings_win.isMinimized():
                settings_win.hide()
            else:
                settings_win.focus()

    tray.activated.connect(on_tray_activated)

    # Mise à jour graphique
    bridge = MonitorBridge()
    last_signature = [None]

    def on_monitor_status():
        st = monitor.status
        sig = (st["connected"], st["percent"], st["charging"])
        text = monitor.status_text()

        if sig != last_signature[0]:
            last_signature[0] = sig
            tray.setIcon(make_tray_icon(st["percent"], st["charging"], st["connected"]))

        tray.setToolTip(text[:127])
        action_status.setText(text)
        action_notif.setChecked(settings.notifications)

        if settings_win.isVisible():
            settings_win.update_status()

    bridge.status_changed.connect(on_monitor_status)
    monitor.on_status = bridge.status_changed.emit

    # Démarrage du thread de surveillance
    worker = threading.Thread(target=monitor.run, name="surveillance", daemon=True)
    tray.show()
    worker.start()

    try:
        app.exec()
    finally:
        monitor.stop()
        worker.join(timeout=5)
        tray.hide()
