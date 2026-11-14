# SwitchBatteryLEDs

**SwitchBatteryLEDs** permet de surveiller facilement le niveau de batterie de vos manettes Nintendo Switch (**Pro Controller** et **Joy-Con**) connectées à votre PC sous Windows (via **Bluetooth** ou **câble USB**).

L'application affiche le niveau de batterie :
1. **Sur les 4 LED de joueur de la manette** (nombre de LED allumées selon le pourcentage restant, clignotement pendant la charge ou en cas de batterie critique).
2. **Dans la barre des tâches (systray)** : une icône dynamique près de l'horloge affiche le pourcentage exact avec un code couleur (vert, orange, rouge). Un clic gauche ouvre les paramètres, un clic droit affiche le menu contextuel.
3. **Via les notifications Windows (toasts)** : notification de détection, alerte de batterie faible ou pleine, et notification interactive avec **barre de progression en direct** dans le centre de notifications Windows.

> **Note importante** : Fermez Steam, BetterJoy ou DS4Windows avant de lancer l'application, sinon ils risquent de monopoliser le périphérique HID ou de réécrire le motif des LED.

---

## Prérequis

- **Système d'exploitation** : Windows 10 ou Windows 11 (64-bit).
- **Python** : Python 3.10+ (recommandé : Python 3.12).
- Une manette Nintendo Switch connectée en Bluetooth ou en USB :
  - Nintendo Switch Pro Controller
  - Joy-Con (gauche)
  - Joy-Con (droit)

---

## Installation

1. **Cloner le dépôt Git :**
   ```bash
   git clone https://github.com/votre-utilisateur/switchBatteryLeds.git
   cd switchBatteryLeds
   ```

2. **Créer un environnement virtuel (recommandé) :**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

3. **Installer les dépendances requises :**
   ```bash
   pip install -r requirements.txt
   ```

---

## Utilisation

### Mode normal (zone de notification / arrière-plan)
Pour lancer l'application en arrière-plan sans fenêtre de console :
```bash
pythonw switch_battery_leds.py
```
*(ou via le module)* :
```bash
pythonw -m switch_battery_leds
```

### Mode console (texte uniquement)
Affiche le journal d'état directement dans le terminal (sans icône systray ni fenêtre) :
```bash
python switch_battery_leds.py --console
```

### Options en ligne de commande
```text
options:
  -h, --help   Affiche l'aide
  --console    Mode texte : pas d'icône ni d'interface graphique
  --verbose    Affiche chaque lecture brute (tension mV, pourcentage calculé)
  --no-notify  Désactive les notifications Windows pour la session courante
```

---

## Configuration

Les paramètres sont automatiquement sauvegardés dans :  
`%APPDATA%\SwitchBatteryLEDs\settings.json`

Ils sont modifiables directement depuis la fenêtre de paramètres (clic gauche sur l'icône de la barre des tâches) :
- **Seuils de LED** : pourcentages pour allumer 4, 3, 2 ou 1 LED (par défaut : 75%, 50%, 25%, 10%).
- **Clignotement pendant la charge** : fait clignoter la LED suivante pour indiquer la recharge.
- **Alertes de batterie faible** : notification personnalisée selon les seuils (ex. 20% et 10%).
- **Notification en direct** : barre de progression dynamique dans le centre de notifications.
- **Intervalle de rafraîchissement** : délai entre chaque mesure (2 à 60 secondes).
- **Lancement au démarrage** : active ou désactive le lancement automatique avec Windows.

---

## Compilation en exécutable autonome (.exe)

Pour générer un fichier exécutable indépendant ne nécessitant pas d'installation préalable de Python :

### Option 1 : Avec le script PowerShell (recommandé)
```powershell
.\build.ps1
```

### Option 2 : Avec le fichier de commande Windows
Double-cliquez sur `build.bat` ou lancez-le dans un terminal :
```cmd
build.bat
```

### Option 3 : Avec PyInstaller manuellement
```bash
pip install -r requirements-dev.txt
pyinstaller --clean SwitchBatteryLEDs.spec
```

L'exécutable autonome est généré dans le répertoire **`dist/SwitchBatteryLEDs.exe`**.

---

## Structure du projet

```text
switchBatteryLeds/
├── switch_battery_leds/            # Paquet principal
│   ├── __init__.py                 # Métadonnées et exports du paquet
│   ├── __main__.py                 # Point d'entrée pour `python -m switch_battery_leds`
│   ├── constants.py                # Identifiants matériels, constantes et courbes de tension
│   ├── settings.py                 # Gestionnaire de configuration (JSON dans %APPDATA%)
│   ├── autostart.py                # Gestion du registre Windows, mutex d'instance unique
│   ├── controller.py               # Protocole HID bas niveau avec les manettes Switch
│   ├── notifier.py                 # Notifications Windows et barre de progression
│   ├── monitor.py                  # Thread de surveillance et orchestrateur d'état
│   ├── cli.py                      # Analyseur d'arguments CLI et routine de lancement
│   └── ui/                         # Interface utilisateur moderne PyQt6
│       ├── __init__.py
│       ├── tray.py                 # Icône systray native et menu contextuel (QSystemTrayIcon)
│       └── settings_window.py      # Fenêtre de configuration Fluent Dark (PyQt6)
├── switch_battery_leds.py          # Script exécutable d'entrée (rétro-compatible)
├── SwitchBatteryLEDs.spec          # Fichier de configuration PyInstaller
├── build.ps1                       # Script de compilation PowerShell
├── build.bat                       # Script de compilation Windows Batch
├── requirements.txt                # Dépendances applicatives (PyQt6, hidapi, windows-toasts)
├── requirements-dev.txt            # Dépendances de développement et de build
├── .gitignore                      # Fichiers exclus du suivi Git
└── README.md                       # Documentation du projet
```

---

## Licence

Projet sous licence MIT (ou Domaine Public). Vous êtes libre de l'utiliser, le modifier et le redistribuer.
