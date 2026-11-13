#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Switch Battery LEDs
Affiche le niveau de batterie d'une manette Switch (Pro Controller / Joy-Con)
sur ses 4 LED de joueur, dans le systray et via des notifications Windows.
"""

__version__ = "1.0.0"
__author__ = "Tom"

from switch_battery_leds.constants import APP_NAME
from switch_battery_leds.controller import Controller, find_controller
from switch_battery_leds.monitor import Monitor
from switch_battery_leds.settings import Settings

__all__ = [
    "APP_NAME",
    "Controller",
    "Monitor",
    "Settings",
    "find_controller",
]
