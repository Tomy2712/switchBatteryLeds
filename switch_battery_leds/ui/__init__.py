#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Composants d'interface utilisateur PyQt6 (icône systray et fenêtre moderne de paramètres).
"""

from switch_battery_leds.ui.settings_window import SettingsWindow
from switch_battery_leds.ui.tray import make_tray_icon, make_tray_pixmap, run_tray

__all__ = ["SettingsWindow", "make_tray_icon", "make_tray_pixmap", "run_tray"]
