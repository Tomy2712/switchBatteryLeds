#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Thread de surveillance de la manette Switch et mise à jour de l'état.
"""

import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple

from switch_battery_leds.constants import COARSE_PERCENT, PLAUSIBLE_MV
from switch_battery_leds.controller import (
    Controller,
    find_controller,
    led_pattern,
    voltage_to_percent,
)
from switch_battery_leds.notifier import Notifier


class Monitor:
    """Boucle de surveillance de la manette (tourne dans son propre thread)."""

    def __init__(self, settings: Any, verbose: bool = False):
        self.s = settings
        self.verbose = verbose
        self.notifier = Notifier(settings)
        self.notifier.log = self.log
        self.stop_event = threading.Event()
        self.wake = threading.Event()
        self.refresh = False
        self.on_status: Optional[Callable[[], None]] = None
        self.status: Dict[str, Any] = {
            "connected": False,
            "name": "",
            "mode": "",
            "percent": None,
            "charging": False,
            "source": "",
            "mv": None,
        }
        self._vstate: Dict[str, bool] = {}

    # --- Utilitaires ------------------------------------------------------

    def log(self, message: str) -> None:
        try:
            print(message, flush=True)
        except Exception:
            pass

    def stop(self) -> None:
        self.stop_event.set()
        self.wake.set()

    def apply_settings(self) -> None:
        """À appeler après un changement de paramètres : applique tout de suite."""
        self.refresh = True
        self.wake.set()

    def _sleep(self, seconds: float) -> None:
        self.wake.wait(seconds)
        self.wake.clear()

    def _set_status(self, **changes) -> None:
        new = dict(self.status, **changes)
        if new == self.status:
            return
        self.status = new
        if self.on_status:
            try:
                self.on_status()
            except Exception:
                pass

    def status_text(self) -> str:
        st = self.status
        if not st["connected"]:
            return "Aucune manette détectée"
        if st["percent"] is None:
            return f"{st['name']} : lecture en cours..."
        return f"{st['name']} : ~{st['percent']} %" + (" (en charge)" if st["charging"] else "")

    def status_text_long(self) -> str:
        st = self.status
        if not st["connected"]:
            return "Aucune manette détectée. Branche-la en USB ou connecte-la en Bluetooth."
        if st["percent"] is None:
            return f"{st['name']} ({st['mode']}) : lecture en cours..."
        text = f"{st['name']} ({st['mode']}) : batterie ~{st['percent']} %"
        if st["charging"]:
            text += " (en charge)"
        if st["mv"]:
            text += f"\nTension mesurée : {st['mv']:.0f} mV"
        elif st["source"] == "palier":
            text += "\nEstimation d'après les paliers de la manette"
        return text

    def estimate_percent(
        self, controller: Controller, level: int, charging: bool
    ) -> Tuple[int, str, Optional[float]]:
        """Retourne (pourcentage, source, millivolts ou None)."""
        if charging:
            # Pendant la charge la tension est gonflée : on se fie au palier brut
            return COARSE_PERCENT.get(level, 0), "palier", None
        reading = controller.read_voltage()
        if reading:
            raw, mv = reading
            if not self._vstate.get("shown") or self.verbose:
                self.log(f"  Tension lue : {mv:.0f} mV (valeur brute {raw})")
                self._vstate["shown"] = True
            if PLAUSIBLE_MV[0] <= mv <= PLAUSIBLE_MV[1]:
                return voltage_to_percent(mv), "tension", mv
            if not self._vstate.get("warned"):
                self.log("  Tension hors plage plausible : j'utilise le palier brut à la place.")
                self._vstate["warned"] = True
        return COARSE_PERCENT.get(level, 0), "palier", None

    # --- Boucle principale ------------------------------------------------

    def run(self) -> None:
        s = self.s
        controller: Optional[Controller] = None
        last_pattern = last_printed = None
        last_sent = 0.0
        first_reading = True
        misses = 0

        if self.notifier.unavailable and s.notifications:
            self.log(
                f"Notifications indisponibles ({self.notifier.unavailable}).\n"
                "  Pour les activer :  pip install windows-toasts"
            )
        self.log("En attente d'une manette Switch...")
        try:
            while not self.stop_event.is_set():
                if self.refresh:
                    last_pattern, self.refresh = None, False

                if controller is None:
                    info = find_controller()
                    if info is None:
                        self._set_status(connected=False, name="", percent=None, mv=None)
                        self._sleep(2)
                        continue
                    try:
                        controller = Controller(info)
                        controller.setup()
                        self.log(f"Manette détectée : {controller.name} ({controller.mode})")
                        last_pattern = last_printed = None
                        first_reading, misses = True, 0
                        self._set_status(
                            connected=True,
                            name=controller.name,
                            mode=controller.mode,
                            percent=None,
                            mv=None,
                        )
                    except OSError as err:
                        self.log(f"Impossible d'ouvrir la manette : {err}")
                        if controller:
                            controller.close()
                        controller = None
                        self._sleep(2)
                        continue

                try:
                    battery = controller.read_battery()
                    if battery:
                        level, charging = battery
                        percent, source, mv = self.estimate_percent(controller, level, charging)
                except OSError:
                    battery = None

                if battery is None:
                    misses += 1
                    if misses >= 3:
                        self.log("Manette perdue, nouvelle recherche...")
                        self.notifier.stop_live()
                        self.notifier.alert("Manette déconnectée", controller.name)
                        controller.close()
                        controller = None
                        self._set_status(connected=False, name="", percent=None, mv=None)
                    continue
                misses = 0

                pattern = led_pattern(percent, charging, s)
                if pattern != last_pattern or time.time() - last_sent > 30:
                    try:
                        controller.set_player_leds(pattern)
                    except OSError:
                        misses = 3
                        continue
                    last_pattern, last_sent = pattern, time.time()

                if self.verbose or last_printed is None or abs(percent - last_printed) >= 5:
                    self.log(
                        f"Batterie ~{percent} % ({source})"
                        + (" - en charge" if charging else "")
                    )
                    last_printed = percent

                self._set_status(percent=percent, charging=charging, source=source, mv=mv)

                title = f"{controller.name} ({controller.mode})"
                if first_reading:
                    self.notifier.on_connect(title, percent, charging)
                    first_reading = False
                self.notifier.update_live(title, percent, charging)   # détecte aussi une suppression
                self.notifier.check_alerts(controller.name, percent, charging, level)

                self._sleep(max(1.0, float(s.interval)))
        finally:
            self.notifier.stop_live()
            if controller:
                try:
                    controller.set_player_leds(0x01)   # retour sur « joueur 1 »
                except OSError:
                    pass
                controller.close()
            self._set_status(connected=False, name="", percent=None, mv=None)
            self.log("Surveillance arrêtée.")
