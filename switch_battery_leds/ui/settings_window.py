#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fenêtre des paramètres (Tkinter / ttk).
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from switch_battery_leds.autostart import get_autostart, set_autostart
from switch_battery_leds.constants import APP_NAME


class SettingsWindow:
    def __init__(self, root: tk.Tk, settings: Any, monitor: Any):
        self.tk = tk
        self.s = settings
        self.monitor = monitor

        win = self.win = tk.Toplevel(root)
        win.title(f"{APP_NAME} - Paramètres")
        win.resizable(False, False)
        outer = ttk.Frame(win, padding=12)
        outer.grid()

        # --- État ---------------------------------------------------------
        self.status_var = tk.StringVar()
        ttk.Label(
            outer,
            textvariable=self.status_var,
            font=("Segoe UI", 10, "bold"),
            justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        # --- LED ----------------------------------------------------------
        led = ttk.LabelFrame(outer, text="LED de la manette", padding=8)
        led.grid(row=1, column=0, sticky="ew", pady=4)
        self.th_vars = []
        for i, (count, value) in enumerate(zip((4, 3, 2, 1), settings.led_thresholds)):
            var = tk.IntVar(value=value)
            self.th_vars.append(var)
            ttk.Label(
                led, text=f"{count} LED allumée{'s' if count > 1 else ''} à partir de"
            ).grid(row=i, column=0, sticky="w", pady=1)
            ttk.Spinbox(led, from_=0, to=100, width=5, textvariable=var).grid(
                row=i, column=1, padx=6
            )
            ttk.Label(led, text="%").grid(row=i, column=2, sticky="w")
        ttk.Label(led, text="En dessous du dernier seuil : la LED 1 clignote.").grid(
            row=4, column=0, columnspan=3, sticky="w", pady=(4, 2)
        )
        self.blink_var = tk.BooleanVar(value=settings.blink_when_charging)
        ttk.Checkbutton(
            led,
            text="Pendant la charge, la LED suivante clignote",
            variable=self.blink_var,
        ).grid(row=5, column=0, columnspan=3, sticky="w")

        # --- Notifications ------------------------------------------------
        notif = ttk.LabelFrame(outer, text="Notifications Windows", padding=8)
        notif.grid(row=2, column=0, sticky="ew", pady=4)
        self.notif_var = tk.BooleanVar(value=settings.notifications)
        self.live_var = tk.BooleanVar(value=settings.live_notification)
        self.silent_var = tk.BooleanVar(value=settings.live_silent_return)
        ttk.Checkbutton(
            notif,
            text="Activer les notifications",
            variable=self.notif_var,
        ).grid(row=0, column=0, columnspan=5, sticky="w")
        ttk.Checkbutton(
            notif,
            text="Notification en direct (barre de progression)",
            variable=self.live_var,
        ).grid(row=1, column=0, columnspan=5, sticky="w")
        ttk.Checkbutton(
            notif,
            text="Si je la supprime, elle revient sans pop-up",
            variable=self.silent_var,
        ).grid(row=2, column=0, columnspan=5, sticky="w")
        alerts = (list(settings.low_alerts) + [0, 0])[:2]
        self.alert_vars = [tk.IntVar(value=a) for a in alerts]
        ttk.Label(notif, text="Alertes batterie faible à").grid(
            row=3, column=0, sticky="w", pady=(6, 0)
        )
        ttk.Spinbox(notif, from_=0, to=100, width=4, textvariable=self.alert_vars[0]).grid(
            row=3, column=1, padx=4, pady=(6, 0)
        )
        ttk.Label(notif, text="% et").grid(row=3, column=2, pady=(6, 0))
        ttk.Spinbox(notif, from_=0, to=100, width=4, textvariable=self.alert_vars[1]).grid(
            row=3, column=3, padx=4, pady=(6, 0)
        )
        ttk.Label(notif, text="%  (0 = désactivée)").grid(
            row=3, column=4, sticky="w", pady=(6, 0)
        )

        # --- Général ------------------------------------------------------
        gen = ttk.LabelFrame(outer, text="Général", padding=8)
        gen.grid(row=3, column=0, sticky="ew", pady=4)
        self.interval_var = tk.IntVar(value=int(round(settings.interval)))
        ttk.Label(gen, text="Lire la batterie toutes les").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(gen, from_=2, to=60, width=4, textvariable=self.interval_var).grid(
            row=0, column=1, padx=6
        )
        ttk.Label(gen, text="secondes").grid(row=0, column=2, sticky="w")
        self.auto_var = tk.BooleanVar(value=get_autostart())
        ttk.Checkbutton(
            gen,
            text="Lancer au démarrage de Windows",
            variable=self.auto_var,
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))

        # --- Boutons ------------------------------------------------------
        bar = ttk.Frame(outer)
        bar.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        self.saved_var = tk.StringVar()
        ttk.Label(bar, textvariable=self.saved_var, foreground="#2e7d32").pack(side="left")
        ttk.Button(bar, text="Fermer", command=win.destroy).pack(side="right")
        ttk.Button(bar, text="Enregistrer", command=self.save).pack(side="right", padx=6)

        self._tick()

    def exists(self) -> bool:
        try:
            return bool(self.win.winfo_exists())
        except Exception:
            return False

    def focus(self) -> None:
        self.win.deiconify()
        self.win.lift()
        self.win.focus_force()

    def _tick(self) -> None:
        if not self.exists():
            return
        self.status_var.set(self.monitor.status_text_long())
        self.win.after(1000, self._tick)

    def save(self) -> None:
        try:
            th = [v.get() for v in self.th_vars]
            alerts = [v.get() for v in self.alert_vars]
            interval = self.interval_var.get()
        except self.tk.TclError:
            messagebox.showerror(
                APP_NAME, "Une des valeurs n'est pas un nombre entier.", parent=self.win
            )
            return
        if not all(0 <= t <= 100 for t in th + alerts) or not (
            th[0] > th[1] > th[2] > th[3]
        ):
            messagebox.showerror(
                APP_NAME,
                "Les seuils de LED doivent être compris entre 0 et 100 et décroissants\n"
                "(par exemple 75, 50, 25, 10).",
                parent=self.win,
            )
            return

        s = self.s
        s.led_thresholds = th
        s.blink_when_charging = self.blink_var.get()
        s.notifications = self.notif_var.get()
        s.live_notification = self.live_var.get()
        s.live_silent_return = self.silent_var.get()
        s.low_alerts = sorted({a for a in alerts if a > 0}, reverse=True)
        s.interval = float(min(60, max(2, interval)))
        try:
            if self.auto_var.get() != get_autostart():
                set_autostart(self.auto_var.get())
        except Exception as err:
            messagebox.showwarning(
                APP_NAME, f"Démarrage automatique impossible : {err}", parent=self.win
            )
        s.save()
        self.monitor.apply_settings()
        self.saved_var.set("Paramètres enregistrés.")
