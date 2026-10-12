$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $MyInvocation.MyCommand.Path
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop 'Compta Matieres - Presentation.lnk'
$target = Join-Path $project 'Lancer_Compta_Matieres.bat'

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $target
$shortcut.WorkingDirectory = $project
$shortcut.Description = 'Demarrer Compta Matieres pour la presentation'
$shortcut.IconLocation = "$env:SystemRoot\System32\imageres.dll,14"
$shortcut.Save()

Write-Host "Raccourci cree : $shortcutPath"
