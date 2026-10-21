# Mise a jour de l'application sur le serveur apres de nouveaux developpements.
# A executer en administrateur depuis la racine du projet :
#   powershell -ExecutionPolicy Bypass -File .\deploiement\mettre_a_jour.ps1

param([string]$NomService = "ComptaMatieres")

$ErrorActionPreference = "Stop"
$Racine = Split-Path -Parent $PSScriptRoot
Set-Location $Racine
$Python = Join-Path $Racine ".venv\Scripts\python.exe"
$Nssm = Join-Path $PSScriptRoot "nssm.exe"
if (-not (Test-Path $Nssm)) { $Nssm = (Get-Command nssm).Source }

Write-Host "1/6 Sauvegarde avant mise a jour"
& $Python (Join-Path $PSScriptRoot "sauvegarder_base.py")
if ($LASTEXITCODE -ne 0) { throw "Sauvegarde impossible : mise a jour annulee." }

Write-Host "2/6 Arret du service"
& $Nssm stop $NomService

try {
    Write-Host "3/6 Recuperation du code (git pull)"
    git pull --ff-only
    if ($LASTEXITCODE -ne 0) { throw "git pull a echoue." }

    Write-Host "4/6 Dependances"
    & $Python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "Installation des dependances echouee." }

    Write-Host "5/6 Migrations et fichiers statiques"
    & $Python manage.py migrate --noinput
    if ($LASTEXITCODE -ne 0) { throw "Migrations echouees." }
    & $Python manage.py collectstatic --noinput
}
finally {
    Write-Host "6/6 Redemarrage du service"
    & $Nssm start $NomService
}
Write-Host "Mise a jour terminee." -ForegroundColor Green
