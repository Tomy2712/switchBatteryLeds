#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
switch_battery_leds.py  -  Batterie de la manette Switch dans la barre des tâches

Affiche le niveau de batterie d'une manette Switch (Pro Controller ou Joy-Con)
connectée au PC (USB ou Bluetooth) :
  - sur ses 4 LED de joueur ;
  - dans une icône de la zone de notification (en bas à droite) qui affiche le
    pourcentage ; clic gauche = fenêtre de paramètres, clic droit = menu ;
  - par des notifications Windows (détection, direct, batterie faible, pleine).

Le pourcentage est ESTIMÉ à partir de la tension de la batterie (la manette
elle-même ne donne que 5 paliers).

Installation :   pip install -r requirements.txt
Utilisation  :   pythonw switch_battery_leds.py        (sans fenêtre console)
                 python  switch_battery_leds.py --console   (mode texte, sans icône)

Les paramètres sont enregistrés dans  %APPDATA%\\SwitchBatteryLEDs\\settings.json
Ferme Steam / BetterJoy / DS4Windows avant de lancer le script, sinon ils
peuvent monopoliser la manette ou réécrire les LED.
"""

from switch_battery_leds.cli import main

if __name__ == "__main__":
    main()
