"""Sauvegarde à chaud de la base SQLite et du dossier media.

Utilise l'API de sauvegarde de SQLite : la copie est cohérente même si des
utilisateurs travaillent pendant la sauvegarde (contrairement à un copier-coller).
Les sauvegardes de plus de JOURS_CONSERVES jours sont supprimées.
"""
import shutil
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
JOURS_CONSERVES = 30


def main():
    dossier = Path(sys.argv[1]) if len(sys.argv) > 1 else RACINE / 'sauvegardes'
    dossier.mkdir(parents=True, exist_ok=True)
    horodatage = datetime.now().strftime('%Y%m%d_%H%M%S')

    source = sqlite3.connect(RACINE / 'db.sqlite3')
    cible_db = dossier / f'db_{horodatage}.sqlite3'
    destination = sqlite3.connect(cible_db)
    with destination:
        source.backup(destination)
    destination.close()
    source.close()

    media = RACINE / 'media'
    if media.exists():
        shutil.make_archive(str(dossier / f'media_{horodatage}'), 'zip', media)

    limite = time.time() - JOURS_CONSERVES * 86400
    for ancien in dossier.glob('*_*'):
        if ancien.stat().st_mtime < limite:
            ancien.unlink()

    print(f'Sauvegarde terminee : {cible_db}')


if __name__ == '__main__':
    main()
