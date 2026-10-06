from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import (
    BonEntree, Depot, DetailBonEntree, Journal, Produit, Profil, SocieteGCS,
    StockDepot, TypeOperation, Unite,
)


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


class ProduitProprietesTests(TestCase):
    """Garde-fou : groupe et stock_disponible doivent rester des propriétés de Produit
    (toutes les validations de bons s'appuient dessus)."""

    def test_groupe_et_stock_disponible(self):
        p = Produit(nomenclature='24.03.012', designation='Test',
                    stock_global=10, qte_affectation=3, qte_sp=2)
        self.assertEqual(p.groupe, '2')
        self.assertEqual(p.stock_disponible, 5)
        self.assertEqual(Produit(nomenclature='').groupe, '')


class ValidationBonEntreeTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create_user(username='comptable', password='x'))

    def test_validation_met_a_jour_stock_et_journal(self):
        depot = Depot.objects.create(code='D-TEST', libelle='Dépôt test')
        produit = Produit.objects.create(nomenclature='11.01.001', designation='Ramette', stock_global=4)
        bon = BonEntree.objects.create(num_bon=1, date_creation=date.today(), depot=depot)
        DetailBonEntree.objects.create(bon_entree=bon, produit=produit, designation='Ramette',
                                       nomenclature='11.01.001', qte=6, prix_ht=100, prix_ttc=118, montant_ttc=708)

        self.client.post(reverse('matieres:bon_entree_valider', args=[bon.pk]))

        bon.refresh_from_db()
        produit.refresh_from_db()
        self.assertTrue(bon.valide)
        self.assertEqual(produit.stock_global, 10)
        self.assertEqual(StockDepot.objects.get(produit=produit, depot=depot).qte_stock, 6)
        self.assertEqual(Journal.objects.get(num_bon=1).groupe, '1')
