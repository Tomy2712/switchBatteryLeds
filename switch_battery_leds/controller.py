#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Communication HID bas niveau avec les manettes Nintendo Switch (Pro Controller / Joy-Con).
"""

import time
from typing import Any, Dict, Optional, Tuple

try:
    import hid  # fourni par le paquet « hidapi »
except ImportError:
    hid = None

from switch_battery_leds.autostart import fatal
from switch_battery_leds.constants import (
    CONTROLLERS,
    NINTENDO_VID,
    RUMBLE_OFF,
    VOLTAGE_CURVE,
)


def ensure_hid():
    """Vérifie que hidapi est bien installé."""
    if hid is None:
        fatal("Module manquant. Installe-le avec :  pip install hidapi")


def voltage_to_percent(mv: float) -> int:
    """Convertit une tension en millivolts en pourcentage selon la courbe de décharge Li-ion."""
    if mv >= VOLTAGE_CURVE[0][0]:
        return 100
    for (v_hi, p_hi), (v_lo, p_lo) in zip(VOLTAGE_CURVE, VOLTAGE_CURVE[1:]):
        if mv >= v_lo:
            return round(p_lo + (p_hi - p_lo) * (mv - v_lo) / (v_hi - v_lo))
    return 0


def leds_for_percent(percent: int, thresholds: list) -> int:
    """Retourne le nombre de LED à allumer selon les seuils configurés."""
    for min_pct, count in zip(thresholds, (4, 3, 2, 1)):
        if percent >= min_pct:
            return count
    return 0


def led_pattern(percent: int, charging: bool, settings: Any) -> int:
    """Octet pour la sous-commande 0x30 :
    quartet bas = LED allumées, quartet haut = LED clignotantes."""
    n = leds_for_percent(percent, settings.led_thresholds)
    solid = (1 << n) - 1
    flash = 0
    if charging:
        if settings.blink_when_charging and n < 4:
            flash = 1 << n                # la LED suivante clignote pendant la charge
    elif n == 0:
        flash = 0b0001                    # critique : LED 1 clignote
    return solid | (flash << 4)


def find_controller() -> Optional[Dict[str, Any]]:
    """Énumère les périphériques USB/Bluetooth et retourne les infos du premier trouvé."""
    ensure_hid()
    for info in hid.enumerate(NINTENDO_VID, 0):
        if info["product_id"] in CONTROLLERS:
            return info
    return None


class Controller:
    """Gère la connexion et les échanges de rapports HID avec une manette Switch."""

    def __init__(self, info: Dict[str, Any]):
        ensure_hid()
        self.name = CONTROLLERS[info["product_id"]]
        self.mode = "Bluetooth"
        self.timer = 0
        self.dev = hid.device()
        self.dev.open_path(info["path"])
        self.dev.set_nonblocking(1)

    # --- E/S de bas niveau -------------------------------------------------

    def _write(self, data: Any) -> None:
        result = self.dev.write(bytes(data))
        if isinstance(result, int) and result < 0:
            raise OSError("écriture HID échouée")

    def _read(self, timeout_ms: int = 0):
        data = self.dev.read(64, timeout_ms) if timeout_ms else self.dev.read(64)
        if data == -1:
            raise OSError("lecture HID échouée")
        return data

    def _wait_for(self, report_id: int, timeout: float = 0.5):
        end = time.time() + timeout
        while time.time() < end:
            data = self._read(50)
            if data and data[0] == report_id:
                return data
        return None

    def _subcommand(self, sub_id: int, args: bytes = b"") -> None:
        packet = bytearray(49)
        packet[0] = 0x01                       # rapport de sortie « commande »
        packet[1] = self.timer
        self.timer = (self.timer + 1) & 0x0F
        packet[2:10] = RUMBLE_OFF
        packet[10] = sub_id
        packet[11:11 + len(args)] = args
        self._write(packet)

    # --- Initialisation ----------------------------------------------------

    def _try_usb_handshake(self) -> bool:
        """En USB, la manette attend une poignée de main avant de répondre."""
        try:
            self._write([0x80, 0x01])
        except OSError:
            return False                       # pas en USB (Bluetooth)
        if not self._wait_for(0x81):
            return False
        for cmd in (0x02, 0x03, 0x02, 0x04):   # handshake, baudrate, handshake, pas de timeout
            self._write([0x80, cmd])
            self._wait_for(0x81, 0.5)
            time.sleep(0.05)
        return True

    def setup(self) -> None:
        if self._try_usb_handshake():
            self.mode = "USB"
        # Rapports complets (60 Hz) : seuls eux contiennent le niveau de batterie
        self._subcommand(0x03, b"\x30")
        time.sleep(0.1)

    # --- Lectures ----------------------------------------------------------

    def read_battery(self, timeout_ms: int = 1000) -> Optional[Tuple[int, bool]]:
        """Retourne (palier 0/2/4/6/8, en_charge) ou None si rien reçu."""
        latest = None
        data = self._read(timeout_ms)
        while data:
            if data[0] in (0x21, 0x30) and len(data) > 2:
                latest = data[2] >> 4          # quartet haut de l'octet 2
            data = self._read()                # on vide la file, on garde le dernier
        if latest is None:
            return None
        return latest & 0xE, bool(latest & 0x1)

    def read_voltage(self, timeout: float = 1.0) -> Optional[Tuple[int, float]]:
        """Sous-commande 0x50 : retourne (valeur_brute, millivolts) ou None."""
        for _ in range(300):                   # vider les rapports en attente
            if not self._read():
                break
        self._subcommand(0x50)
        end = time.time() + timeout
        while time.time() < end:
            data = self._read(100)
            if data and data[0] == 0x21 and len(data) > 16 and data[14] == 0x50:
                raw = data[15] | (data[16] << 8)
                return raw, raw * 2.5          # 1 unité = 2,5 mV
        return None

    def set_player_leds(self, pattern: int) -> None:
        self._subcommand(0x30, bytes([pattern]))

    def close(self) -> None:
        try:
            self.dev.close()
        except Exception:
            pass
