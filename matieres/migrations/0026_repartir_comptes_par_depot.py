from django.db import migrations


# Quel dépôt (comptable des matières) gère quels comptes principaux — d'après
# le compte 10-14 (matériel durable, Groupe 1), 20/22/29 (consommables
# généraux), 23/26/27 (denrées, cuisine), 24/30 (électricité, plomberie,
# outillage — Maintenance), 25/28 (biomédical, pharmaceutique).
COMPTES_PAR_DEPOT = {
    'Depot-ComptaPrincipal': [10, 11, 12, 13, 14],
    'Depot-ComptaSAF': [20, 22, 29],
    'Depot-Pharmacie': [25, 28],
    'Depot-Maintenance': [24, 30],
    'Depot-Economat': [23, 26, 27],
}

# Exceptions à la maille sous-compte, prioritaires sur le compte principal
# ci-dessus : les articles de cuisine et boissons du compte 29 (S.A.F.)
# relèvent en réalité de l'Économat.
SOUS_COMPTES_PAR_DEPOT = {
    'Depot-Economat': ['29.08', '29.10'],
}


def repartir(apps, schema_editor):
    Depot = apps.get_model('matieres', 'Depot')
    ComptePrincipale = apps.get_model('matieres', 'ComptePrincipale')
    SousCompte = apps.get_model('matieres', 'SousCompte')

    for code, comptes in COMPTES_PAR_DEPOT.items():
        depot = Depot.objects.filter(code=code).first()
        if not depot:
            continue
        depot.comptes_principaux.set(
            ComptePrincipale.objects.filter(num_compte__in=comptes)
        )

    for code, sous_comptes in SOUS_COMPTES_PAR_DEPOT.items():
        depot = Depot.objects.filter(code=code).first()
        if not depot:
            continue
        depot.sous_comptes_specifiques.set(
            SousCompte.objects.filter(compte__in=sous_comptes)
        )


def vider(apps, schema_editor):
    Depot = apps.get_model('matieres', 'Depot')
    for depot in Depot.objects.filter(
        code__in=list(COMPTES_PAR_DEPOT) + list(SOUS_COMPTES_PAR_DEPOT)
    ):
        depot.comptes_principaux.clear()
        depot.sous_comptes_specifiques.clear()


class Migration(migrations.Migration):

    dependencies = [
        ('matieres', '0025_depot_comptes_principaux_and_more'),
    ]

    operations = [
        migrations.RunPython(repartir, vider),
    ]
