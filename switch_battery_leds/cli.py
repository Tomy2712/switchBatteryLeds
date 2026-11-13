#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyse de la ligne de commande et point d'entrée de l'application.
"""

import argparse
import ctypes

from switch_battery_leds.autostart import already_running
from switch_battery_leds.constants import APP_NAME
from switch_battery_leds.monitor import Monitor
from switch_battery_leds.settings import Settings
from switch_battery_leds.ui.tray import run_tray


def parse_args():
    parser = argparse.ArgumentParser(
        description="Batterie de la manette Switch (LED, icône, notifications)"
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="mode texte : pas d'icône ni de fenêtre, tout s'affiche dans la console",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="affiche chaque lecture (tension, pourcentage)",
    )
    parser.add_argument(
        "--no-notify",
        action="store_true",
        help="désactive les notifications pour cette session",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    settings = Settings.load()
    if args.no_notify:
        settings.notifications = False
    monitor = Monitor(settings, verbose=args.verbose)

    if args.console:
        print("Ctrl+C pour quitter.")
        try:
            monitor.run()
        except KeyboardInterrupt:
            pass
        return

    if already_running():
        try:
            ctypes.windll.user32.MessageBoxW(
                0,
                "Le programme est déjà lancé : cherche l'icône près de l'horloge "
                "(clique sur la flèche ^ si elle est masquée).",
                APP_NAME,
                0x40,
            )
        except Exception:
            print("Le programme est déjà lancé.")
        return

    run_tray(settings, monitor)


if __name__ == "__main__":
    main()
