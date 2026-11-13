#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Constantes matérielles, protocolaires et de configuration pour SwitchBatteryLEDs.
"""

APP_NAME = "Manette Switch"

# Identifiants USB/Bluetooth Nintendo
NINTENDO_VID = 0x057E
CONTROLLERS = {
    0x2009: "Pro Controller",
    0x2006: "Joy-Con (gauche)",
    0x2007: "Joy-Con (droit)",
}

# « Rumble » neutre (aucune vibration), joint à chaque commande HID
RUMBLE_OFF = bytes([0x00, 0x01, 0x40, 0x40, 0x00, 0x01, 0x40, 0x40])

# Paliers bruts de la manette -> pourcentage « milieu de palier » (secours)
COARSE_PERCENT = {8: 87, 6: 62, 4: 37, 2: 12, 0: 0}

# Courbe de décharge typique d'une batterie Li-ion : (millivolts, %)
VOLTAGE_CURVE = [
    (4150, 100), (4100, 90), (4000, 80), (3950, 70), (3870, 60), (3840, 50),
    (3800, 40), (3770, 30), (3730, 20), (3690, 10), (3610, 5), (3300, 0),
]

# Plage de tension jugée plausible ; en dehors, on ignore la mesure
PLAUSIBLE_MV = (3000, 4400)

# Registre Windows pour le démarrage automatique
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "SwitchBatteryLEDs"
