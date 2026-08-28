from django.db import migrations


RENOMMAGE = [
    ('D1', 'Depot-ComptaPrincipal'),
    ('D2', 'Depot-ComptaSAF'),
    ('D3', 'Depot-Pharmacie'),
    ('D4', 'Depot-Maintenance'),
    ('D5', 'Depot-Economat'),
]


def renommer(apps, schema_editor):
    Depot = apps.get_model('matieres', 'Depot')
    for ancien_code, nouveau_code in RENOMMAGE:
        Depot.objects.filter(code=ancien_code).update(code=nouveau_code)


def restaurer(apps, schema_editor):
    Depot = apps.get_model('matieres', 'Depot')
    for ancien_code, nouveau_code in RENOMMAGE:
        Depot.objects.filter(code=nouveau_code).update(code=ancien_code)


class Migration(migrations.Migration):

    dependencies = [
        ('matieres', '0023_seed_comptables_matieres'),
    ]

    operations = [
        migrations.RunPython(renommer, restaurer),
    ]
