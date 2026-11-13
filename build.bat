@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo       SwitchBatteryLEDs - Script de compilation
echo ========================================================
echo.

cd /d "%~dp0"

:: 1. Tenter de fermer une instance existante de l'exécutable pour éviter les blocages de fichier
taskkill /f /im SwitchBatteryLEDs.exe >nul 2>&1

:: 2. Recherche du bon interpréteur Python
set "PYTHON_CMD="

:: Vérification si un venv local existe
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
    goto :found_python
)
if exist "venv\Scripts\python.exe" (
    set "PYTHON_CMD=venv\Scripts\python.exe"
    goto :found_python
)

:: Vérification du lanceur 'py -3.12'
py -3.12 -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py -3.12"
    goto :found_python
)

:: Vérification de 'python' standard
python -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    goto :found_python
)

echo [ERREUR] Aucun interpréteur Python détecté dans le PATH ou via le lanceur 'py'.
pause
exit /b 1

:found_python
echo Utilisation de : %PYTHON_CMD%
echo.

:: 3. Vérification de PyInstaller
%PYTHON_CMD% -m PyInstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] PyInstaller n'est pas encore installe. Installation en cours...
    %PYTHON_CMD% -m pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [ERREUR] Echec de l'installation de PyInstaller.
        pause
        exit /b 1
    )
)

:: 4. Nettoyage des anciens dossiers de build
echo [INFO] Nettoyage des dossiers build et dist...
if exist "build" rmdir /s /q "build"
if exist "dist\SwitchBatteryLEDs.exe" del /f /q "dist\SwitchBatteryLEDs.exe"

:: 5. Compilation
echo [INFO] Lancement de PyInstaller avec SwitchBatteryLEDs.spec...
%PYTHON_CMD% -m PyInstaller --clean SwitchBatteryLEDs.spec

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo  Compilation reussie !
    echo  Executable genere : dist\SwitchBatteryLEDs.exe
    echo ========================================================
) else (
    echo.
    echo [ERREUR] La compilation a echoue.
)

echo.
pause
