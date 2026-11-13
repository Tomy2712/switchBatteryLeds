#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fenêtre moderne des paramètres avec PyQt6 (thème sombre façon Windows 11).
"""

from typing import Any

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from switch_battery_leds.autostart import get_autostart, set_autostart
from switch_battery_leds.constants import APP_NAME

DARK_STYLE = """
QWidget {
    background-color: #202020;
    color: #f3f3f3;
    font-family: "Segoe UI Variable Text", "Segoe UI", sans-serif;
    font-size: 13px;
}

QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    border: none;
    background: #202020;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #3f3f3f;
    min-height: 25px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #555555;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QFrame.card {
    background-color: #2b2b2b;
    border: 1px solid #383838;
    border-radius: 8px;
    padding: 12px;
}

QLabel.card-title {
    font-size: 14px;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 6px;
}

QLabel.muted {
    color: #9e9e9e;
    font-size: 12px;
}

QSpinBox {
    background-color: #353535;
    color: #ffffff;
    border: 1px solid #4a4a4a;
    border-radius: 6px;
    padding: 4px 8px;
    min-width: 60px;
    font-size: 13px;
}

QSpinBox:hover {
    border: 1px solid #0078d4;
    background-color: #3c3c3c;
}

QSpinBox:focus {
    border: 1px solid #0078d4;
    background-color: #404040;
}

QSpinBox::up-button, QSpinBox::down-button {
    background: transparent;
    width: 16px;
}

QCheckBox {
    spacing: 8px;
    color: #f0f0f0;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #5a5a5a;
    background-color: #303030;
}

QCheckBox::indicator:hover {
    border-color: #0078d4;
    background-color: #383838;
}

QCheckBox::indicator:checked {
    background-color: #0078d4;
    border-color: #0078d4;
}

QPushButton {
    background-color: #383838;
    color: #ffffff;
    border: 1px solid #484848;
    border-radius: 6px;
    padding: 7px 18px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #444444;
    border-color: #585858;
}

QPushButton:pressed {
    background-color: #2d2d2d;
}

QPushButton.primary {
    background-color: #0078d4;
    border: 1px solid #0078d4;
    font-weight: 600;
}

QPushButton.primary:hover {
    background-color: #1084d8;
    border-color: #1084d8;
}

QPushButton.primary:pressed {
    background-color: #006cc1;
    border-color: #006cc1;
}

QProgressBar {
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    background-color: #1a1a1a;
    text-align: center;
    color: #ffffff;
    font-weight: 600;
    height: 14px;
}

QProgressBar::chunk {
    border-radius: 5px;
    background-color: #2ea043;
}
"""


class SettingsWindow(QWidget):
    """Fenêtre de configuration moderne au style Windows 11."""

    def __init__(self, settings: Any, monitor: Any, parent=None):
        super().__init__(parent)
        self.s = settings
        self.monitor = monitor

        self.setWindowTitle(f"{APP_NAME} — Paramètres")
        self.setFixedSize(540, 680)
        self.setStyleSheet(DARK_STYLE)

        # Empêcher la fermeture totale de l'appli quand on ferme la fenêtre
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Zone déroulante pour le contenu
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 8, 0)
        content_layout.setSpacing(12)

        # ---------------- 1. CARTE ÉTAT EN DIRECT ----------------
        self.status_card = QFrame()
        self.status_card.setProperty("class", "card")
        status_layout = QVBoxLayout(self.status_card)
        status_layout.setSpacing(8)

        top_status = QHBoxLayout()
        self.lbl_device_title = QLabel("En attente d'une manette Switch...")
        self.lbl_device_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #ffffff;")
        self.badge_status = QLabel("Déconnecté")
        self.badge_status.setStyleSheet(
            "background-color: #4a4a4a; color: #ffffff; padding: 3px 8px; border-radius: 10px; font-size: 11px; font-weight: 600;"
        )
        top_status.addWidget(self.lbl_device_title, 1)
        top_status.addWidget(self.badge_status, 0)
        status_layout.addLayout(top_status)

        self.progress_battery = QProgressBar()
        self.progress_battery.setRange(0, 100)
        self.progress_battery.setValue(0)
        self.progress_battery.setTextVisible(False)
        status_layout.addWidget(self.progress_battery)

        self.lbl_status_detail = QLabel(
            "Branchez votre Pro Controller ou Joy-Con en USB ou connectez-le en Bluetooth."
        )
        self.lbl_status_detail.setProperty("class", "muted")
        self.lbl_status_detail.setWordWrap(True)
        status_layout.addWidget(self.lbl_status_detail)

        content_layout.addWidget(self.status_card)

        # ---------------- 2. CARTE LED DE LA MANETTE ----------------
        led_card = QFrame()
        led_card.setProperty("class", "card")
        led_layout = QVBoxLayout(led_card)
        led_layout.setSpacing(8)

        lbl_led_title = QLabel("Comportement des 4 LED de joueur")
        lbl_led_title.setProperty("class", "card-title")
        led_layout.addWidget(lbl_led_title)

        self.th_spins = []
        for count, val in zip((4, 3, 2, 1), settings.led_thresholds):
            row = QHBoxLayout()
            lbl = QLabel(f"{count} LED allumée{'s' if count > 1 else ''} à partir de")
            spin = QSpinBox()
            spin.setRange(0, 100)
            spin.setValue(val)
            spin.setSuffix(" %")
            self.th_spins.append(spin)

            row.addWidget(lbl, 1)
            row.addWidget(spin, 0)
            led_layout.addLayout(row)

        lbl_crit = QLabel("En dessous du dernier seuil, la LED 1 clignote.")
        lbl_crit.setProperty("class", "muted")
        led_layout.addWidget(lbl_crit)

        self.chk_blink = QCheckBox("Pendant la charge, la LED suivante clignote")
        self.chk_blink.setChecked(settings.blink_when_charging)
        led_layout.addWidget(self.chk_blink)

        content_layout.addWidget(led_card)

        # ---------------- 3. CARTE NOTIFICATIONS WINDOWS ----------------
        notif_card = QFrame()
        notif_card.setProperty("class", "card")
        notif_layout = QVBoxLayout(notif_card)
        notif_layout.setSpacing(8)

        lbl_notif_title = QLabel("Notifications Windows (toasts)")
        lbl_notif_title.setProperty("class", "card-title")
        notif_layout.addWidget(lbl_notif_title)

        self.chk_notif = QCheckBox("Activer les notifications système")
        self.chk_notif.setChecked(settings.notifications)
        notif_layout.addWidget(self.chk_notif)

        self.chk_live = QCheckBox("Notification interactive en direct (barre de progression)")
        self.chk_live.setChecked(settings.live_notification)
        notif_layout.addWidget(self.chk_live)

        self.chk_silent = QCheckBox("Si la notification en direct est fermée, la réafficher sans pop-up")
        self.chk_silent.setChecked(settings.live_silent_return)
        notif_layout.addWidget(self.chk_silent)

        # Seuils alertes faibles
        alerts = (list(settings.low_alerts) + [0, 0])[:2]
        row_alerts = QHBoxLayout()
        row_alerts.addWidget(QLabel("Alertes batterie faible à :"))

        self.spin_alert1 = QSpinBox()
        self.spin_alert1.setRange(0, 100)
        self.spin_alert1.setValue(alerts[0])
        self.spin_alert1.setSuffix(" %")
        row_alerts.addWidget(self.spin_alert1)

        row_alerts.addWidget(QLabel("et"))

        self.spin_alert2 = QSpinBox()
        self.spin_alert2.setRange(0, 100)
        self.spin_alert2.setValue(alerts[1])
        self.spin_alert2.setSuffix(" %")
        row_alerts.addWidget(self.spin_alert2)

        lbl_alert_info = QLabel("(0 = désactivée)")
        lbl_alert_info.setProperty("class", "muted")
        row_alerts.addWidget(lbl_alert_info)
        row_alerts.addStretch(1)
        notif_layout.addLayout(row_alerts)

        content_layout.addWidget(notif_card)

        # ---------------- 4. CARTE GÉNÉRAL ----------------
        gen_card = QFrame()
        gen_card.setProperty("class", "card")
        gen_layout = QVBoxLayout(gen_card)
        gen_layout.setSpacing(8)

        lbl_gen_title = QLabel("Général")
        lbl_gen_title.setProperty("class", "card-title")
        gen_layout.addWidget(lbl_gen_title)

        row_interval = QHBoxLayout()
        row_interval.addWidget(QLabel("Fréquence de lecture de la batterie :"))
        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(2, 60)
        self.spin_interval.setValue(int(round(settings.interval)))
        self.spin_interval.setSuffix(" sec")
        row_interval.addWidget(self.spin_interval)
        row_interval.addStretch(1)
        gen_layout.addLayout(row_interval)

        self.chk_autostart = QCheckBox("Démarrer automatiquement avec Windows")
        self.chk_autostart.setChecked(get_autostart())
        gen_layout.addWidget(self.chk_autostart)

        content_layout.addWidget(gen_card)
        content_layout.addStretch(1)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # ---------------- 5. BARRE DE BOUTONS INFÉRIEURE ----------------
        bottom_bar = QHBoxLayout()
        self.lbl_saved = QLabel("")
        self.lbl_saved.setStyleSheet("color: #2ea043; font-weight: 600;")
        bottom_bar.addWidget(self.lbl_saved, 1)

        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.hide)
        bottom_bar.addWidget(btn_close)

        btn_save = QPushButton("Enregistrer")
        btn_save.setProperty("class", "primary")
        btn_save.clicked.connect(self.save)
        bottom_bar.addWidget(btn_save)

        main_layout.addLayout(bottom_bar)

        # Timer pour rafraîchir l'affichage du statut en direct
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)
        self.update_status()

    def update_status(self) -> None:
        """Met à jour les informations en direct de la manette."""
        st = self.monitor.status
        if not st["connected"]:
            self.lbl_device_title.setText("Aucune manette détectée")
            self.badge_status.setText("Déconnecté")
            self.badge_status.setStyleSheet(
                "background-color: #4a4a4a; color: #ffffff; padding: 3px 8px; border-radius: 10px; font-size: 11px; font-weight: 600;"
            )
            self.progress_battery.setValue(0)
            self.progress_battery.setStyleSheet(
                "QProgressBar::chunk { background-color: #4a4a4a; }"
            )
            self.lbl_status_detail.setText(
                "Branchez votre Pro Controller ou Joy-Con en USB ou connectez-le en Bluetooth."
            )
            return

        name = st["name"] or "Manette Switch"
        mode = st["mode"] or "Inconnu"
        pct = st["percent"]
        charging = st["charging"]

        self.lbl_device_title.setText(f"{name} ({mode})")
        if pct is None:
            self.badge_status.setText("Lecture...")
            self.badge_status.setStyleSheet(
                "background-color: #0078d4; color: #ffffff; padding: 3px 8px; border-radius: 10px; font-size: 11px; font-weight: 600;"
            )
            self.lbl_status_detail.setText("Initialisation de la communication HID...")
            self.progress_battery.setValue(0)
            return

        # Couleur selon le niveau
        if pct >= 25:
            color = "#2ea043"   # Vert
            badge_bg = "#238636"
        elif pct >= 10:
            color = "#d29922"   # Orange
            badge_bg = "#9e6a03"
        else:
            color = "#da3633"   # Rouge
            badge_bg = "#b62324"

        self.badge_status.setText(f"~{pct} %" + (" (en charge)" if charging else ""))
        self.badge_status.setStyleSheet(
            f"background-color: {badge_bg}; color: #ffffff; padding: 3px 8px; border-radius: 10px; font-size: 11px; font-weight: 600;"
        )

        self.progress_battery.setValue(pct)
        self.progress_battery.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {color}; border-radius: 5px; }}"
        )

        detail_text = f"Niveau estimé : ~{pct} %"
        if charging:
            detail_text += " — Manette en charge"
        if st.get("mv"):
            detail_text += f" | Tension : {st['mv']:.0f} mV"
        elif st.get("source") == "palier":
            detail_text += " | Estimation d'après les paliers matériels"

        self.lbl_status_detail.setText(detail_text)

    def save(self) -> None:
        th = [spin.value() for spin in self.th_spins]
        if not (th[0] > th[1] > th[2] > th[3]):
            QMessageBox.critical(
                self,
                APP_NAME,
                "Les seuils de LED doivent être strictement décroissants\n(ex. 75, 50, 25, 10).",
            )
            return

        s = self.s
        s.led_thresholds = th
        s.blink_when_charging = self.chk_blink.isChecked()
        s.notifications = self.chk_notif.isChecked()
        s.live_notification = self.chk_live.isChecked()
        s.live_silent_return = self.chk_silent.isChecked()

        raw_alerts = [self.spin_alert1.value(), self.spin_alert2.value()]
        s.low_alerts = sorted({a for a in raw_alerts if a > 0}, reverse=True)
        s.interval = float(self.spin_interval.value())

        try:
            if self.chk_autostart.isChecked() != get_autostart():
                set_autostart(self.chk_autostart.isChecked())
        except Exception as err:
            QMessageBox.warning(
                self, APP_NAME, f"Démarrage automatique impossible : {err}"
            )

        s.save()
        self.monitor.apply_settings()
        self.lbl_saved.setText("Paramètres enregistrés !")
        QTimer.singleShot(3000, lambda: self.lbl_saved.setText(""))

    def focus(self) -> None:
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.raise_()
        self.activateWindow()

    def exists(self) -> bool:
        return self.isVisible()
