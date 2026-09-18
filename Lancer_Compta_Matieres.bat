@echo off
setlocal
cd /d "%~dp0"
title Compta Matieres - Serveur

if not exist ".venv\Scripts\python.exe" (
    echo Environnement Python introuvable : .venv\Scripts\python.exe
    echo Installez d'abord les dependances indiquees dans GUIDE_INSTALLATION_DG.md.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" manage.py migrate --noinput
if errorlevel 1 (
    echo La mise a jour de la base a echoue.
    pause
    exit /b 1
)

start "" /b cmd /c "timeout /t 2 /nobreak >nul & start "" http://127.0.0.1:8000/"
echo Application disponible sur http://127.0.0.1:8000/
echo Fermez cette fenetre ou utilisez Arreter_Compta_Matieres.bat pour arreter le serveur.
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000
pause
