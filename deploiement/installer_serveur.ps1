# Installation de Compta Matieres sur le serveur Windows de l'entreprise.
# A executer dans PowerShell OUVERT EN ADMINISTRATEUR, depuis la racine du projet :
#   powershell -ExecutionPolicy Bypass -File .\deploiement\installer_serveur.ps1
#
# Le script peut etre relance sans risque : il ne recree pas ce qui existe deja
# (.env, base de donnees, service).

param(
    [int]$Port = 8000,
    [string]$NomService = "ComptaMatieres"
)

$ErrorActionPreference = "Stop"
$Racine = Split-Path -Parent $PSScriptRoot
Set-Location $Racine
$Python = Join-Path $Racine ".venv\Scripts\python.exe"

function Etape($texte) { Write-Host "`n=== $texte ===" -ForegroundColor Cyan }

# 1. Droits administrateur (pare-feu, service, tache planifiee)
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) {
    Write-Host "Relancez PowerShell en tant qu'administrateur." -ForegroundColor Red
    exit 1
}

# 2. Environnement Python
Etape "Environnement Python"
if (-not (Test-Path $Python)) {
    if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
        Write-Host "Python introuvable. Installez Python 3.14 (python.org, cocher 'Add to PATH')." -ForegroundColor Red
        exit 1
    }
    py -m venv .venv
}
& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Echec de l'installation des dependances." }

# 3. Fichier .env (reglages de production)
Etape "Reglages de production (.env)"
$NomMachine = $env:COMPUTERNAME.ToLower()
$IPs = @(Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } |
    Select-Object -ExpandProperty IPAddress)
if (-not (Test-Path ".env")) {
    $cle = & $Python -c "import secrets; print(secrets.token_urlsafe(50))"
    $hotes = @("localhost", "127.0.0.1", $NomMachine) + $IPs
    $origines = $hotes | ForEach-Object { "http://${_}:$Port" }
    @(
        "# Reglages du serveur de production - NE PAS COMMITTER",
        "DJANGO_DEBUG=False",
        "DJANGO_SECRET_KEY=$cle",
        "DJANGO_ALLOWED_HOSTS=$($hotes -join ',')",
        "DJANGO_CSRF_TRUSTED_ORIGINS=$($origines -join ',')",
        "SERVEUR_PORT=$Port"
    ) | Set-Content -Path ".env" -Encoding ASCII
    Write-Host ".env cree. Hotes autorises : $($hotes -join ', ')"
} else {
    Write-Host ".env existe deja : conserve."
}

# 4. Base de donnees et fichiers statiques
Etape "Base de donnees et fichiers statiques"
& $Python manage.py migrate --noinput
if ($LASTEXITCODE -ne 0) { throw "Echec des migrations." }
& $Python manage.py collectstatic --noinput
& $Python manage.py check --deploy

# 5. Pare-feu
Etape "Pare-feu Windows (port $Port)"
if (-not (Get-NetFirewallRule -DisplayName "Compta Matieres $Port" -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName "Compta Matieres $Port" -Direction Inbound -Protocol TCP `
        -LocalPort $Port -Action Allow -Profile Domain,Private | Out-Null
    Write-Host "Regle de pare-feu creee."
} else {
    Write-Host "Regle de pare-feu deja presente."
}

# 6. Service Windows (NSSM)
Etape "Service Windows $NomService"
$Nssm = Join-Path $PSScriptRoot "nssm.exe"
if (-not (Test-Path $Nssm)) { $Nssm = (Get-Command nssm -ErrorAction SilentlyContinue).Source }
if (-not $Nssm) {
    Write-Host "nssm.exe introuvable : telechargez-le sur https://nssm.cc/download et copiez" -ForegroundColor Yellow
    Write-Host "win64\nssm.exe dans le dossier deploiement\, puis relancez ce script." -ForegroundColor Yellow
    Write-Host "En attendant, test manuel possible :  .venv\Scripts\python.exe serveur.py"
    exit 0
}
New-Item -ItemType Directory -Force (Join-Path $Racine "logs") | Out-Null
if (-not (Get-Service $NomService -ErrorAction SilentlyContinue)) {
    & $Nssm install $NomService $Python (Join-Path $Racine "serveur.py")
}
& $Nssm set $NomService AppDirectory $Racine
& $Nssm set $NomService DisplayName "Compta Matieres (HOGIP)"
& $Nssm set $NomService Description "Application web de comptabilite des matieres"
& $Nssm set $NomService Start SERVICE_AUTO_START
& $Nssm set $NomService AppStdout (Join-Path $Racine "logs\service.log")
& $Nssm set $NomService AppStderr (Join-Path $Racine "logs\service.log")
& $Nssm set $NomService AppRotateFiles 1
& $Nssm set $NomService AppRotateBytes 5242880
& $Nssm stop $NomService 2>$null
& $Nssm start $NomService

# 7. Sauvegarde automatique chaque nuit a 22h
Etape "Sauvegarde quotidienne (tache planifiee)"
$script = Join-Path $PSScriptRoot "sauvegarder_base.ps1"
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$script`""
$declencheur = New-ScheduledTaskTrigger -Daily -At 22:00
Register-ScheduledTask -TaskName "ComptaMatieres-Sauvegarde" -Action $action -Trigger $declencheur `
    -User "SYSTEM" -RunLevel Highest -Force | Out-Null
Write-Host "Tache 'ComptaMatieres-Sauvegarde' programmee a 22h00."

Etape "Termine"
Write-Host "Application accessible depuis les postes du reseau :"
Write-Host "  http://${NomMachine}:$Port/"
$IPs | ForEach-Object { Write-Host "  http://${_}:$Port/" }
