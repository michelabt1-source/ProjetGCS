@echo off
setlocal
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$processes = Get-CimInstance Win32_Process -Filter 'Name = ''python.exe''' | Where-Object { $_.CommandLine -like '*manage.py runserver 127.0.0.1:8000*' }; $processes | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }; if ($processes) { Write-Host 'Serveur arrete.' } else { Write-Host 'Aucun serveur Compta Matieres actif.' }"
pause
