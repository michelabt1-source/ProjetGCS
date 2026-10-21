# Déploiement de Compta Matières sur le serveur Windows de l'entreprise

Résultat attendu : l'application tourne en permanence sur le serveur (service Windows,
démarrage automatique) et chaque poste du réseau y accède par `http://NOM-DU-SERVEUR:8000/`.

---

## Étape 0 — Sur votre PC, avant d'aller au serveur

1. Pousser la dernière version du code : `git push`.
2. Arrêter `runserver`, puis faire une sauvegarde propre des données :
   ```powershell
   .\.venv\Scripts\python.exe deploiement\sauvegarder_base.py E:\transfert
   ```
   Le dossier `E:\transfert` (une clé USB par exemple) contient alors `db_AAAAMMJJ_HHMMSS.sqlite3` et `media_….zip`.
3. Télécharger **NSSM** sur https://nssm.cc/download (fichier zip) et le mettre sur la clé.
4. Télécharger l'installateur **Python 3.14** (64 bits) sur https://www.python.org/downloads/windows/.

## Étape 1 — Préparer le serveur

Ouvrez une session avec un compte **administrateur**.

1. Installer Python et cocher **« Add python.exe to PATH »**.
2. Installer Git (https://git-scm.com), ou copier le dossier du projet depuis la clé.
3. Choisir l'emplacement de l'application, par exemple `D:\Applications\compta_matieres`
   (à éviter : le Bureau, `Documents` ou un lecteur réseau).

```powershell
cd D:\Applications
git clone https://github.com/michelabt1-source/ProjetGCS.git compta_matieres
cd compta_matieres
```

> Sans Git : copier le dossier du projet **sans** `.venv`, `staticfiles`, `logs` et `db.sqlite3`.

## Étape 2 — Mettre les données en place

1. Copier le fichier `db_….sqlite3` de la clé à la racine du projet et le renommer en **`db.sqlite3`**.
2. Décompresser `media_….zip` dans un dossier **`media`** à la racine du projet.
3. Extraire `nssm.exe` du zip (sous-dossier `win64`) et le copier dans le dossier **`deploiement\`**.

## Étape 3 — Lancer l'installation automatique

Ouvrez PowerShell **en administrateur** (clic droit → *Exécuter en tant qu'administrateur*) :

```powershell
cd D:\Applications\compta_matieres
powershell -ExecutionPolicy Bypass -File .\deploiement\installer_serveur.ps1
```

Le script s'occupe de tout :
- environnement Python et dépendances ;
- fichier `.env` avec une **clé secrète unique**, `DEBUG=False`, le nom et les adresses IP du serveur ;
- migrations de la base et fichiers statiques ;
- règle du **pare-feu** pour le port 8000 ;
- **service Windows** `ComptaMatieres` (démarrage automatique, redémarrage en cas de plantage) ;
- **sauvegarde automatique** chaque soir à 22 h dans `sauvegardes\` (30 jours conservés).

À la fin, il affiche les adresses à utiliser depuis les postes.
Port différent : `...installer_serveur.ps1 -Port 80`.

## Étape 4 — Sécuriser les comptes

Le compte de développement `admin / admin123` ne doit **pas** rester en production :

```powershell
.\.venv\Scripts\python.exe manage.py changepassword admin
```

Créez ensuite un compte nominatif par utilisateur (menu *Configuration → Profils*, ou `/admin/`).

## Étape 5 — Vérifier

**Sur le serveur :**
```powershell
Get-Service ComptaMatieres          # doit afficher Running
```
Ouvrir `http://localhost:8000/`.

**Depuis un autre poste du réseau :** ouvrir `http://NOM-DU-SERVEUR:8000/`.
Si la page ne s'ouvre pas, essayer l'adresse IP. Si l'IP fonctionne mais pas le nom,
c'est un problème de DNS : voir avec l'informaticien, ou utiliser l'IP.

**Recette de bout en bout**, à faire avec **2 ou 3 postes en même temps** :

| # | Test | Résultat attendu |
|---|------|------------------|
| 1 | Connexion / déconnexion | Tableau de bord affiché, retour à la page de connexion |
| 2 | Logo de la société (Configuration → Société) | Logo visible |
| 3 | Expression de besoin : création + lignes + réception | Enregistrée, statut mis à jour |
| 4 | Marché : création, consolidation de l'EB, total TTC | Totaux corrects |
| 5 | Bon d'entrée lié au marché | Livré / reste à jour, stock augmenté |
| 6 | Bon d'affectation, sortie provisoire, retour, mutation, sortie définitive | Stock et journal cohérents |
| 7 | Journal, balance, grand livre, inventaires | États affichés et imprimables |
| 8 | Saisies refusées : date incohérente, quantité négative, EB vide, clôture d'un marché non livré | Message d'erreur, rien d'enregistré |
| 9 | Deux utilisateurs valident un bon **au même moment** | Les deux passent, sans erreur « database is locked » |
| 10 | Redémarrer le serveur Windows | L'application revient seule |
| 11 | Lancer `.\deploiement\sauvegarder_base.ps1` | Fichier créé dans `sauvegardes\` |

---

## Au quotidien

| Besoin | Commande (PowerShell administrateur, dossier du projet) |
|--------|---------------------------------------------------------|
| Arrêter / démarrer / redémarrer | `Stop-Service ComptaMatieres` · `Start-Service ComptaMatieres` · `Restart-Service ComptaMatieres` |
| Installer une nouvelle version | `powershell -ExecutionPolicy Bypass -File .\deploiement\mettre_a_jour.ps1` (sauvegarde, git pull, migrations, redémarrage) |
| Sauvegarde manuelle | `.\deploiement\sauvegarder_base.ps1` ou `... -Dossier E:\Sauvegardes` |
| Voir les erreurs | `logs\compta_matieres.log` (erreurs Django) et `logs\service.log` (démarrage du serveur) |

**Restaurer une sauvegarde** : `Stop-Service ComptaMatieres`, copier `sauvegardes\db_….sqlite3`
à la place de `db.sqlite3`, supprimer `db.sqlite3-wal` et `db.sqlite3-shm` s'ils existent,
puis `Start-Service ComptaMatieres`.

> Copiez régulièrement le dossier `sauvegardes\` **hors du serveur** (disque externe ou partage) :
> une sauvegarde qui reste sur le même disque ne protège pas d'une panne de ce disque.

## Problèmes fréquents

| Symptôme | Cause / solution |
|----------|------------------|
| `Bad Request (400)` | Le nom ou l'IP utilisé n'est pas dans `DJANGO_ALLOWED_HOSTS` du fichier `.env` : l'ajouter, puis redémarrer le service |
| `Forbidden (403) CSRF` à l'enregistrement | Ajouter l'adresse (`http://nom:8000`) dans `DJANGO_CSRF_TRUSTED_ORIGINS`, puis redémarrer |
| Page sans mise en forme | Lancer `manage.py collectstatic --noinput`, puis redémarrer |
| Inaccessible depuis les postes, mais OK sur le serveur | Pare-feu : vérifier la règle « Compta Matieres 8000 » ; le réseau doit être de type *Privé* ou *Domaine* |
| Le service s'arrête aussitôt | Lire `logs\service.log` ; tester à la main avec `.\.venv\Scripts\python.exe serveur.py` |
| L'IP du serveur a changé | Demander une **IP fixe** à l'informaticien, puis corriger le `.env` |
