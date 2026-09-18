# Installation et presentation sur le PC du DG

## 1. Preparation sur votre PC

1. Faire une copie de securite de `db.sqlite3`.
2. Copier tout le dossier `compta_matieres` sur une cle USB ou un partage reseau.
3. Ne pas copier le dossier `.venv` s'il existe deja : il sera recree sur le PC du DG.
4. Copier aussi le dossier `media` s'il contient un logo ou des fichiers importes.

## 2. Installation sur le PC du DG

1. Installer Python 3.12 ou une version compatible avec `requirements.txt`.
2. Ouvrir PowerShell dans le dossier du projet.
3. Executer :

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
```

4. Remplacer ensuite `db.sqlite3` par la copie de donnees preparee, si elle doit etre presentee au DG.
5. Creer le raccourci du Bureau : clic droit sur `Creer_Raccourci_DG.ps1`, puis **Executer avec PowerShell**.
   En cas de blocage, executer dans PowerShell :

```powershell
powershell -ExecutionPolicy Bypass -File .\Creer_Raccourci_DG.ps1
```

## 3. Demarrage le jour de la presentation

1. Double-cliquer sur **Compta Matieres - Presentation** sur le Bureau.
2. Attendre l'ouverture automatique du navigateur.
3. Se connecter avec le compte de presentation.
4. L'application est accessible uniquement sur ce PC à l'adresse `http://127.0.0.1:8000/`.
5. Pour arrêter l'application, double-cliquer sur `Arreter_Compta_Matieres.bat`.

## 4. Parcours a tester avant la presentation

1. Connexion et affichage du tableau de bord.
2. Creation d'une expression de besoin avec date, service et bureau.
3. Ajout d'une ligne avec designation, nomenclature, unite, quantite et prix.
4. Reception par le comptable.
5. Creation d'un marche avec numero, dates, fournisseur, bon d'engagement et chapitre.
6. Consolidation de l'expression dans le marche.
7. Verification du total TTC et des articles consolides.
8. Creation d'un bon d'entree lie au marche.
9. Impression de l'etat du marche.
10. Verification que les controles refusent une date incoherente, une quantite negative, une expression vide et la cloture d'un marche non livre.

## 5. Sauvegarde

Avant toute presentation, fermer le serveur puis copier `db.sqlite3` vers un emplacement de sauvegarde date. Ne jamais modifier la base originale sans copie.
