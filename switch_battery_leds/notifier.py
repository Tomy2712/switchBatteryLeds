#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notifications Windows (toasts) avec support barre de progression en direct.
"""

from typing import Any, Callable, Optional, Set

from switch_battery_leds.constants import APP_NAME


class Notifier:
    """Notifications Windows (toasts). Ne plante jamais le programme : en cas de
    problème, les notifications sont simplement indisponibles."""

    def __init__(self, settings: Any):
        self.s = settings
        self.log: Callable[[str], None] = lambda message: None
        self.toaster = None
        self.can_live = False
        self.unavailable: Optional[str] = None
        self.live = None            # (toast, barre, titre)
        self.failures = 0           # mises à jour ratées d'affilée
        self.gave_up = False
        self.announced = False      # « Manette détectée » déjà affiché pour cette connexion
        self.alerted: Set[int] = set()
        self.full_notified = False
        try:
            from windows_toasts import InteractableWindowsToaster
            self.toaster = InteractableWindowsToaster(APP_NAME)
            self.can_live = True
        except Exception:
            try:
                from windows_toasts import WindowsToaster
                self.toaster = WindowsToaster(APP_NAME)
            except Exception as err:
                self.unavailable = str(err)

    @property
    def active(self) -> bool:
        return bool(self.toaster and self.s.notifications)

    def _live_wanted(self) -> bool:
        return self.active and self.can_live and self.s.live_notification

    @staticmethod
    def _live_text(percent: int, charging: bool) -> str:
        return f"Batterie ~{percent} %" + (" - en charge" if charging else "")

    def reset(self) -> None:
        self.alerted.clear()
        self.full_notified = False
        self.failures = 0
        self.gave_up = False
        self.announced = False

    def alert(self, title: str, message: str) -> None:
        if not self.active:
            return
        try:
            from windows_toasts import Toast
            self.toaster.show_toast(Toast([title, message]))
        except Exception as err:
            self.log(f"  (notification impossible : {err})")

    # --- Notification en direct -------------------------------------------

    def on_connect(self, title: str, percent: int, charging: bool) -> None:
        """Nouvelle connexion. Si le direct est coupé, simple notification de détection ;
        sinon c'est update_live() qui crée la notification en direct."""
        self.reset()
        if self.active and not self._live_wanted():
            self.alert(f"Manette détectée : {title}", self._live_text(percent, charging))
            self.announced = True

    def _create(self, title: str, percent: int, charging: bool) -> None:
        from windows_toasts import Toast, ToastProgressBar
        first = not self.announced
        bar = ToastProgressBar("Batterie", progress=percent / 100)
        heading = f"Manette détectée : {title}" if first else f"Manette : {title}"
        toast = Toast([heading, self._live_text(percent, charging)])
        toast.progress_bar = bar
        if not first and self.s.live_silent_return:
            toast.suppress_popup = True            # revient directement dans le centre de notifications
        self.toaster.show_toast(toast)
        self.live = (toast, bar, title)
        self.announced = True

    def update_live(self, title: str, percent: int, charging: bool) -> None:
        """Crée, met à jour ou recrée (si supprimée) la notification en direct."""
        if not self._live_wanted():
            if self.live:
                self.stop_live()
            return
        if self.live is None:
            if not self.gave_up:
                try:
                    self._create(title, percent, charging)
                except Exception as err:
                    self.gave_up = True
                    self.log(f"  (notification en direct impossible : {err})")
            return

        toast, bar, title = self.live
        try:
            bar.progress = percent / 100
            toast.text_fields = [f"Manette : {title}", self._live_text(percent, charging)]
            # update_toast renvoie False (sans exception) si la notification n'existe plus
            ok = self.toaster.update_toast(toast)
        except Exception:
            ok = False
        if ok:
            self.failures = 0
            return

        self.failures += 1
        self.live = None
        if self.failures > 3:
            # Elle échoue juste après chaque recréation : on abandonne pour ne pas spammer
            self.gave_up = True
            self.log("  Notification en direct : trop d'échecs, mises à jour arrêtées.")
            return
        self.log("  Notification en direct supprimée : je la réaffiche.")
        try:
            self._create(title, percent, charging)
        except Exception as err:
            self.gave_up = True
            self.log(f"  (réaffichage impossible : {err})")

    def stop_live(self) -> None:
        if self.live and self.toaster:
            try:
                self.toaster.remove_toast(self.live[0])
            except Exception:
                pass
        self.live = None

    # --- Alertes ----------------------------------------------------------

    def check_alerts(self, name: str, percent: int, charging: bool, level: int) -> None:
        if charging:
            self.alerted.clear()
            if level == 8 and not self.full_notified:
                self.alert(name, "Batterie pleine, tu peux la débrancher.")
                self.full_notified = True
            return
        self.full_notified = False
        crossed = [t for t in self.s.low_alerts if percent <= t]
        if crossed and min(crossed) not in self.alerted:
            self.alert(name, f"Batterie faible : ~{percent} %")
        self.alerted.update(crossed)
        # Réarme l'alerte si la batterie remonte nettement au-dessus du seuil
        self.alerted = {t for t in self.alerted if percent <= t + 5}
