#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fonctions système Windows : boîte de message d'erreur, instance unique et démarrage auto.
"""

import ctypes
import os
import sys

from switch_battery_leds.constants import APP_NAME, RUN_KEY, RUN_NAME

_mutex = None


def fatal(message: str) -> None:
    """Erreur bloquante, visible même sans console (pythonw / .exe sans console)."""
    try:
        print(message, file=sys.stderr)
    except Exception:
        pass
    try:
        ctypes.windll.user32.MessageBoxW(0, message, APP_NAME, 0x10)
    except Exception:
        pass
    sys.exit(1)


def already_running() -> bool:
    """Évite de lancer deux instances (ex. démarrage auto + lancement manuel)."""
    global _mutex
    try:
        _mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "SwitchBatteryLEDs_SingleInstance")
        return ctypes.windll.kernel32.GetLastError() == 183   # ERROR_ALREADY_EXISTS
    except Exception:
        return False


def _autostart_command(entry_file: str | None = None) -> str:
    if getattr(sys, "frozen", False):                  # .exe créé avec PyInstaller
        return f'"{sys.executable}"'
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    exe = pythonw if os.path.exists(pythonw) else sys.executable
    if not entry_file:
        entry_file = sys.argv[0] if sys.argv and sys.argv[0] else "switch_battery_leds.py"
    target = os.path.abspath(entry_file)
    return f'"{exe}" "{target}"'


def get_autostart() -> bool:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, RUN_NAME)
        return True
    except Exception:
        return False


def set_autostart(enabled: bool, entry_file: str | None = None) -> None:
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            cmd = _autostart_command(entry_file)
            winreg.SetValueEx(key, RUN_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, RUN_NAME)
            except FileNotFoundError:
                pass
