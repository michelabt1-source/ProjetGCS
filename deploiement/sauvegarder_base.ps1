# Sauvegarde de la base et des medias dans le dossier sauvegardes\ du projet.
# Lancee chaque nuit par la tache planifiee "ComptaMatieres-Sauvegarde".
# Pour sauvegarder ailleurs (disque externe, partage) :
#   .\deploiement\sauvegarder_base.ps1 -Dossier "E:\Sauvegardes\ComptaMatieres"

param([string]$Dossier = "")

$Racine = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Racine ".venv\Scripts\python.exe"
$Script = Join-Path $PSScriptRoot "sauvegarder_base.py"

if ($Dossier) { & $Python $Script $Dossier } else { & $Python $Script }
exit $LASTEXITCODE
