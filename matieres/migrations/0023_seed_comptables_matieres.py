from django.db import migrations


DEPOTS = [
    ('D1', 'Comptable des Matières Principales (Groupe 1)', 'Cheikh DIOP'),
    ('D2', 'Comptable des Matières S.A.F. (Consommables)', 'Aïda FALL'),
    ('D3', 'Pharmacie', 'Moussa NDIAYE'),
    ('D4', 'Maintenance', 'Ibrahima SARR'),
    ('D5', 'Économat', 'Ndèye GUEYE'),
]

# Identifiant de connexion, prénom, nom, code dépôt. Compte créé sans mot de
# passe utilisable — l'administrateur doit en définir un depuis la page
# Utilisateurs de l'admin Django avant la première connexion du comptable.
COMPTES = [
    ('comptable.principal', 'Cheikh', 'DIOP', 'D1'),
    ('comptable.saf', 'Aïda', 'FALL', 'D2'),
    ('comptable.pharmacie', 'Moussa', 'NDIAYE', 'D3'),
    ('comptable.maintenance', 'Ibrahima', 'SARR', 'D4'),
    ('comptable.economat', 'Ndèye', 'GUEYE', 'D5'),
]


def seed(apps, schema_editor):
    Depot = apps.get_model('matieres', 'Depot')
    ProfilUtilisateur = apps.get_model('matieres', 'ProfilUtilisateur')
    User = apps.get_model('auth', 'User')

    depots = {}
    for code, libelle, responsable in DEPOTS:
        depot, created = Depot.objects.get_or_create(code=code)
        if created or not depot.libelle:
            depot.libelle = libelle
        if created or not depot.responsable:
            depot.responsable = responsable
        depot.actif = True
        depot.save()
        depots[code] = depot

    for username, first, last, depot_code in COMPTES:
        user, user_created = User.objects.get_or_create(username=username)
        if user_created:
            user.set_unusable_password()
            user.first_name = first
            user.last_name = last
            user.is_active = True
            user.save()
        profil, profil_created = ProfilUtilisateur.objects.get_or_create(
            user=user, defaults={'role': 'comptable', 'depot': depots[depot_code]}
        )
        if profil_created:
            continue
        if not profil.depot_id:
            profil.depot = depots[depot_code]
            profil.save(update_fields=['depot'])


def unseed(apps, schema_editor):
    """Pas de retour arrière automatique : ces comptes/dépôts peuvent avoir été
    renommés ou pris en usage réel entre-temps."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('matieres', '0022_profilutilisateur_depot'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
