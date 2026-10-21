"""Lance l'application en production avec Waitress (serveur WSGI compatible Windows).

Utilisé par le service Windows « ComptaMatieres » (voir deploiement/installer_serveur.ps1).
Lancement manuel pour test :  .venv\\Scripts\\python.exe serveur.py
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'compta_matieres.settings')

from waitress import serve  # noqa: E402

from compta_matieres.wsgi import application  # noqa: E402

if __name__ == '__main__':
    hote = os.environ.get('SERVEUR_HOTE', '0.0.0.0')
    port = int(os.environ.get('SERVEUR_PORT', '8000'))
    print(f'Compta Matieres en service sur http://{hote}:{port}/', flush=True)
    serve(application, host=hote, port=port, threads=8)
