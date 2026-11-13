#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestion des paramètres utilisateurs (sauvegarde et chargement JSON dans %APPDATA%).
"""

import json
import os
from dataclasses import asdict, dataclass, field


@dataclass
class Settings:
    # Pourcentage minimum pour allumer 4, 3, 2 puis 1 LED (en dessous : LED 1 clignote)
    led_thresholds: list = field(default_factory=lambda: [75, 50, 25, 10])
    blink_when_charging: bool = True      # pendant la charge, la LED suivante clignote
    notifications: bool = True            # notifications Windows
    live_notification: bool = True        # notification avec barre de progression en direct
    live_silent_return: bool = False      # si supprimée, elle revient sans pop-up
    low_alerts: list = field(default_factory=lambda: [20, 10])   # alertes de batterie faible (%)
    interval: float = 5.0                 # secondes entre deux lectures

    @staticmethod
    def path():
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "SwitchBatteryLEDs", "settings.json")

    @classmethod
    def load(cls):
        s = cls()
        try:
            with open(cls.path(), encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return s
        try:
            th = [int(x) for x in data["led_thresholds"]]
            if len(th) == 4 and all(0 <= x <= 100 for x in th) and th == sorted(set(th), reverse=True):
                s.led_thresholds = th
        except Exception:
            pass
        try:
            s.low_alerts = sorted({int(x) for x in data["low_alerts"] if 0 < int(x) <= 100}, reverse=True)
        except Exception:
            pass
        try:
            s.interval = min(60.0, max(2.0, float(data["interval"])))
        except Exception:
            pass
        for key in ("blink_when_charging", "notifications", "live_notification", "live_silent_return"):
            if isinstance(data.get(key), bool):
                setattr(s, key, data[key])
        return s

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path()), exist_ok=True)
            with open(self.path(), "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2)
        except OSError:
            pass
