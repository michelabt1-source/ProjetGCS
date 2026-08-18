from django.test import TestCase

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Profil, SocieteGCS, TypeOperation, Unite


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
