<#
.SYNOPSIS
    Script de compilation de SwitchBatteryLEDs en exécutable autonome (.exe).
.DESCRIPTION
    Détecte l'environnement Python approprié, vérifie les dépendances requises,
    ferme toute instance résiduelle de l'exécutable et compile le projet avec PyInstaller.
.PARAMETER Clean
    Supprime complètement les dossiers build et dist avant de compiler.
#>
[CmdletBinding()]
param(
    [switch]$Clean = $true
)

$ErrorActionPreference = "Stop"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       SwitchBatteryLEDs - Script de compilation        " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

# 1. Fermeture d'une éventuelle instance en cours d'exécution
$existingProcesses = Get-Process -Name "SwitchBatteryLEDs" -ErrorAction SilentlyContinue
if ($existingProcesses) {
    Write-Host "[INFO] Fermeture de l'instance SwitchBatteryLEDs existante..." -ForegroundColor Yellow
    $existingProcesses | Stop-Process -Force
    Start-Sleep -Milliseconds 500
}

# 2. Détection de l'interpréteur Python
$pythonCommand = $null

if (Test-Path "$ProjectRoot\.venv\Scripts\python.exe") {
    $pythonCommand = "$ProjectRoot\.venv\Scripts\python.exe"
} elseif (Test-Path "$ProjectRoot\venv\Scripts\python.exe") {
    $pythonCommand = "$ProjectRoot\venv\Scripts\python.exe"
} else {
    # Test lanceur 'py -3.12'
    try {
        $null = & py -3.12 -c "import sys" 2>$null
        $pythonCommand = "py"
        $pyArgs = @("-3.12")
    } catch {
        # Test python standard
        try {
            $null = & python -c "import sys" 2>$null
            $pythonCommand = "python"
            $pyArgs = @()
        } catch {
            Write-Error "[ERREUR] Aucun interpréteur Python trouvé (testé: .venv, py -3.12, python)."
            exit 1
        }
    }
}

if (-not $pyArgs) { $pyArgs = @() }

Write-Host "[INFO] Interpréteur Python sélectionné : $pythonCommand $($pyArgs -join ' ')" -ForegroundColor Green

# 3. Vérification de PyInstaller
$hasPyinstaller = $false
try {
    & $pythonCommand @pyArgs -m PyInstaller --version | Out-Null
    $hasPyinstaller = $true
} catch {
    $hasPyinstaller = $false
}

if (-not $hasPyinstaller) {
    Write-Host "[INFO] PyInstaller non détecté. Installation via pip..." -ForegroundColor Yellow
    & $pythonCommand @pyArgs -m pip install -r requirements-dev.txt
}

# 4. Nettoyage
if ($Clean) {
    Write-Host "[INFO] Nettoyage des répertoires 'build' et 'dist'..." -ForegroundColor Gray
    if (Test-Path "$ProjectRoot\build") { Remove-Item -Path "$ProjectRoot\build" -Recurse -Force }
    if (Test-Path "$ProjectRoot\dist\SwitchBatteryLEDs.exe") { Remove-Item -Path "$ProjectRoot\dist\SwitchBatteryLEDs.exe" -Force }
}

# 5. Compilation
Write-Host "[INFO] Compilation avec SwitchBatteryLEDs.spec..." -ForegroundColor Cyan
$buildArgs = @($pyArgs) + @("-m", "PyInstaller", "--clean", "SwitchBatteryLEDs.spec")

& $pythonCommand @buildArgs

$exePath = Join-Path $ProjectRoot "dist\SwitchBatteryLEDs.exe"
if (Test-Path $exePath) {
    $exeSizeMb = [math]::Round((Get-Item $exePath).Length / 1MB, 2)
    Write-Host ""
    Write-Host "========================================================" -ForegroundColor Green
    Write-Host " [SUCCÈS] Compilation terminée avec succès !" -ForegroundColor Green
    Write-Host " Fichier exécutable : $exePath ($exeSizeMb Mo)" -ForegroundColor Green
    Write-Host "========================================================" -ForegroundColor Green
} else {
    Write-Error "[ERREUR] Le fichier dist\SwitchBatteryLEDs.exe n'a pas été généré."
}
