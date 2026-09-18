from django.test import TestCase

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import ExpressionBesoin, Marche, Profil, SocieteGCS, TypeOperation, Unite


class ConfigurationCrudTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='admin', password='secret123')

    def login(self):
        self.client.force_login(self.user)

    def test_unite_update_via_post(self):
        self.login()
        unite = Unite.objects.create(libelle='Kg')

        response = self.client.post(reverse('matieres:unite_list'), {'pk': unite.pk, 'libelle': 'Kilogramme'})

        self.assertRedirects(response, reverse('matieres:unite_list'))
        unite.refresh_from_db()
        self.assertEqual(unite.libelle, 'Kilogramme')

    def test_type_operation_update_via_post(self):
        self.login()
        operation = TypeOperation.objects.create(libelle='Entrée')

        response = self.client.post(reverse('matieres:type_op_list'), {'pk': operation.pk, 'libelle': 'Sortie'})

        self.assertRedirects(response, reverse('matieres:type_op_list'))
        operation.refresh_from_db()
        self.assertEqual(operation.libelle, 'Sortie')

    def test_profil_update_via_post(self):
        self.login()
        profil = Profil.objects.create(role='Comptable')

        response = self.client.post(reverse('matieres:profil_list'), {'pk': profil.pk, 'role': 'Responsable'})

        self.assertRedirects(response, reverse('matieres:profil_list'))
        profil.refresh_from_db()
        self.assertEqual(profil.role, 'Responsable')

    def test_societe_delete_via_get(self):
        self.login()
        SocieteGCS.objects.create(nom='GCS Test')

        response = self.client.get(reverse('matieres:societe_view'), {'delete': '1'})

        self.assertRedirects(response, reverse('matieres:societe_view'))
        self.assertFalse(SocieteGCS.objects.exists())


class MarchePeriodTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='marches', password='secret123')

    def test_create_saves_period(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('matieres:marche_create'), {
            'num_marche': 'M-2026-001',
            'date_creation': '2026-01-10',
            'date_debut': '2026-02-01',
            'date_fin': '2026-12-31',
            'num_bon_engagement': '12',
        })

        marche = Marche.objects.get(num_marche='M-2026-001')
        self.assertRedirects(response, reverse('matieres:marche_update', kwargs={'pk': marche.pk}))
        self.assertEqual(str(marche.date_debut), '2026-02-01')
        self.assertEqual(str(marche.date_fin), '2026-12-31')

    def test_create_rejects_reversed_period(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('matieres:marche_create'), {
            'num_marche': 'M-2026-002',
            'date_creation': '2026-01-10',
            'date_debut': '2026-12-31',
            'date_fin': '2026-02-01',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Marche.objects.filter(num_marche='M-2026-002').exists())

    def test_create_rejects_missing_number(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('matieres:marche_create'), {
            'date_creation': '2026-01-10',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Marche.objects.exists())

    def test_solder_rejects_empty_market(self):
        self.client.force_login(self.user)
        marche = Marche.objects.create(num_marche='M-2026-003', date_creation='2026-01-10')

        response = self.client.post(reverse('matieres:marche_solder', kwargs={'pk': marche.pk}))

        self.assertRedirects(response, reverse('matieres:marche_update', kwargs={'pk': marche.pk}))
        marche.refresh_from_db()
        self.assertEqual(marche.statut, 'en_cours')


class ExpressionWorkflowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='expressions', password='secret123')

    def test_consolidation_rejects_expression_without_lines(self):
        self.client.force_login(self.user)
        expression = ExpressionBesoin.objects.create(date_creation='2026-01-10', recu_par_comptable=True, statut='recu')
        marche = Marche.objects.create(num_marche='M-2026-004', date_creation='2026-01-10')

        response = self.client.post(reverse('matieres:expression_consolider', kwargs={'pk': expression.pk}), {
            'marche_id': marche.pk,
        })

        self.assertRedirects(response, reverse('matieres:expression_detail', kwargs={'pk': expression.pk}))
        expression.refresh_from_db()
        self.assertEqual(expression.statut, 'recu')
        self.assertIsNone(expression.marche_id)
