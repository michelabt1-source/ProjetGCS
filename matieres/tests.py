from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import (
    BonEntree, Depot, DetailBonEntree, DetailMarche, ExpressionBesoin, Fournisseur, Journal, Marche, Produit,
    Profil, SocieteGCS, StockDepot, TypeOperation, Unite,
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


class ReceptionMarcheTests(TestCase):
    """Bon d'entrée rattaché à un marché : seules les livraisons conformes au marché passent."""

    def setUp(self):
        self.client.force_login(get_user_model().objects.create_user(username='comptable', password='x'))
        self.titulaire = Fournisseur.objects.create(nom='Titulaire SA')
        self.autre = Fournisseur.objects.create(nom='Concurrent SARL')
        self.depot = Depot.objects.create(code='D-TEST', libelle='Dépôt test')
        self.produit = Produit.objects.create(nomenclature='11.01.001', designation='Ramette')
        self.marche = Marche.objects.create(num_marche='M-2026-01', date_creation=date.today(),
                                            fournisseur=self.titulaire)
        DetailMarche.objects.create(marche=self.marche, produit=self.produit, designation='Ramette',
                                    nomenclature='11.01.001', qte=10, prix_ttc=100, montant_ttc=1000)

    def bon(self, num=1, **kw):
        kw.setdefault('fournisseur', self.titulaire)
        return BonEntree.objects.create(num_bon=num, date_creation=date.today(), depot=self.depot,
                                        marche=self.marche, **kw)

    def ligne(self, bon, qte, nomenclature='11.01.001'):
        return DetailBonEntree.objects.create(bon_entree=bon, produit=self.produit, designation='Ramette',
                                              nomenclature=nomenclature, qte=qte, prix_ttc=100,
                                              montant_ttc=100 * qte)

    def ajouter(self, bon, qte, nomenclature='11.01.001'):
        return self.client.post(reverse('matieres:htmx_be_add_detail', args=[bon.pk]), {
            'designation': 'Ramette', 'produit_id': self.produit.pk, 'nomenclature': nomenclature,
            'qte': qte, 'prix_ttc': '100'})

    def creer(self, **data):
        data = {'num_bon': 50, 'date_creation': date.today().isoformat(), 'marche_id': self.marche.pk, **data}
        self.client.post(reverse('matieres:bon_entree_create'), data)
        return BonEntree.objects.filter(num_bon=50).first()

    def test_livre_ne_compte_que_les_bons_valides(self):
        self.ligne(self.bon(), 4)
        self.assertEqual(self.marche.total_livre(), 0)
        self.assertEqual(self.marche.solde_restant(), 1000)

    def test_creation_sur_marche_solde_refusee(self):
        self.marche.statut = 'solde'
        self.marche.save()
        self.assertIsNone(self.creer())

    def test_creation_avec_autre_fournisseur_refusee(self):
        self.assertIsNone(self.creer(fournisseur=self.autre.pk))

    def test_creation_sans_fournisseur_reprend_le_titulaire(self):
        self.assertEqual(self.creer().fournisseur, self.titulaire)

    def test_article_hors_marche_refuse(self):
        bon = self.bon()
        response = self.ajouter(bon, 1, nomenclature='99.99.999')
        self.assertContains(response, 'ne figure pas au marché')
        self.assertFalse(bon.details.exists())

    def test_quantite_au_dela_du_reste_refusee(self):
        livre = self.bon(num=1)
        self.ligne(livre, 7)
        self.client.post(reverse('matieres:bon_entree_valider', args=[livre.pk]))
        bon = self.bon(num=2)
        self.assertContains(self.ajouter(bon, 4), 'reste à livrer de 3')
        self.ajouter(bon, 3)
        self.assertEqual(bon.details.get().qte, 3)

    def test_deux_brouillons_ne_peuvent_pas_depasser_le_marche_a_la_validation(self):
        premier, second = self.bon(num=1), self.bon(num=2)
        self.ligne(premier, 6)
        self.ligne(second, 6)
        self.client.post(reverse('matieres:bon_entree_valider', args=[premier.pk]))
        self.client.post(reverse('matieres:bon_entree_valider', args=[second.pk]))
        premier.refresh_from_db()
        second.refresh_from_db()
        self.assertTrue(premier.valide)
        self.assertFalse(second.valide)

    def test_en_tete_d_un_bon_valide_non_modifiable(self):
        bon = self.bon()
        self.ligne(bon, 2)
        self.client.post(reverse('matieres:bon_entree_valider', args=[bon.pk]))
        self.client.post(reverse('matieres:bon_entree_update', args=[bon.pk]),
                         {'date_creation': date.today().isoformat(), 'marche_id': ''})
        bon.refresh_from_db()
        self.assertEqual(bon.marche, self.marche)
        self.assertEqual(bon.depot, self.depot)

    def test_rattacher_un_bon_dont_les_lignes_ne_collent_pas_au_marche_refuse(self):
        bon = BonEntree.objects.create(num_bon=3, date_creation=date.today())
        self.ligne(bon, 25)
        self.client.post(reverse('matieres:bon_entree_update', args=[bon.pk]),
                         {'date_creation': date.today().isoformat(), 'marche_id': self.marche.pk})
        bon.refresh_from_db()
        self.assertIsNone(bon.marche)


class SaisieArticlesMarcheTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create_user(username='comptable', password='x'))
        self.marche = Marche.objects.create(num_marche='M-2026-02', date_creation=date.today())
        self.url = reverse('matieres:htmx_marche_add_detail', args=[self.marche.pk])

    def ajouter(self, **data):
        return self.client.post(self.url, {'designation': 'Ramette A4', 'nomenclature': '22.01.001',
                                           'qte': '10', **data})

    def test_ajout_avec_montants_au_format_francais(self):
        self.ajouter(prix_ht='1 500', prix_ttc='1.770,00', observation='Lot 1')
        ligne = self.marche.details.get()
        self.assertEqual(ligne.prix_ttc, Decimal('1770'))
        self.assertEqual(ligne.montant_ttc, Decimal('17700'))
        self.assertEqual(ligne.observation, 'Lot 1')

    def test_saisie_invalide_renvoie_un_message_sans_planter(self):
        for data, message in [({'qte': '0'}, 'supérieure à zéro'),
                              ({'qte': '2,5'}, 'nombre entier'),
                              ({'prix_ttc': 'abc'}, 'Prix TTC invalide'),
                              ({'designation': ''}, 'Choisissez un article')]:
            self.assertContains(self.ajouter(**data), message)
        self.assertFalse(self.marche.details.exists())

    def test_marche_clos_non_modifiable(self):
        self.marche.statut = 'solde'
        self.marche.save()
        self.assertContains(self.ajouter(), 'plus modifiables')
        self.assertFalse(self.marche.details.exists())

    def test_ligne_deja_livree_non_supprimable(self):
        self.ajouter()
        ligne = self.marche.details.get()
        bon = BonEntree.objects.create(num_bon=1, date_creation=date.today(), marche=self.marche, valide=True)
        DetailBonEntree.objects.create(bon_entree=bon, designation='Ramette A4', nomenclature='22.01.001', qte=2)
        self.client.post(reverse('matieres:htmx_marche_delete_detail', args=[ligne.pk]))
        self.assertTrue(self.marche.details.exists())

    def test_page_de_saisie_identique_au_bon_d_entree(self):
        response = self.client.get(reverse('matieres:marche_update', args=[self.marche.pk]))
        for element in ('bs-workspace', 'data-bs-drawer', 'id="f-designation"', 'produit-modal-overlay'):
            self.assertContains(response, element)


class ExpressionSurMarcheTests(TestCase):
    """Le service puise dans un marché en cours : il saisit ses quantités sur les articles du marché."""

    def setUp(self):
        self.client.force_login(get_user_model().objects.create_user(username='service', password='x'))
        self.marche = Marche.objects.create(num_marche='M-2026-03', date_creation=date.today())
        self.ramette = DetailMarche.objects.create(marche=self.marche, designation='Ramette A4', nomenclature='22.01.001',
                                                   qte=500, prix_ttc=3000, montant_ttc=1500000)
        self.encre = DetailMarche.objects.create(marche=self.marche, designation='Encre HP 305', nomenclature='22.01.002',
                                                 qte=80, prix_ttc=12000, montant_ttc=960000)

    def creer(self, **data):
        self.client.post(reverse('matieres:expression_create'), {
            'date_creation': date.today().isoformat(), 'mode': 'sur_marche', 'marche_id': self.marche.pk, **data})
        return ExpressionBesoin.objects.latest('pk')

    def saisir(self, expr, ligne_marche, qte):
        detail = expr.details.get(ligne_marche=ligne_marche)
        return self.client.post(reverse('matieres:htmx_expression_set_qte', args=[detail.pk]), {'qte': qte})

    def test_creation_liste_tous_les_articles_du_marche_a_zero(self):
        expr = self.creer()
        self.assertTrue(expr.sur_marche)
        self.assertEqual(expr.marche, self.marche)
        self.assertEqual(sorted(expr.details.values_list('designation', 'qte')),
                         [('Encre HP 305', 0), ('Ramette A4', 0)])

    def test_saisie_de_quantite_et_montant(self):
        expr = self.creer()
        self.saisir(expr, self.ramette, '40')
        ligne = expr.details.get(ligne_marche=self.ramette)
        self.assertEqual((ligne.qte, ligne.montant_ttc), (40, Decimal('120000')))

    def test_quantite_limitee_au_disponible_toutes_expressions_confondues(self):
        premiere = self.creer()
        self.saisir(premiere, self.encre, '70')
        seconde = self.creer()
        self.assertContains(self.saisir(seconde, self.encre, '20'), '10 encore disponible')
        self.assertEqual(seconde.details.get(ligne_marche=self.encre).qte, 0)

    def test_reception_ecarte_les_articles_laisses_a_zero(self):
        expr = self.creer()
        self.saisir(expr, self.ramette, '40')
        self.client.post(reverse('matieres:expression_recevoir', args=[expr.pk]))
        expr.refresh_from_db()
        self.assertEqual(expr.statut, 'recu')
        self.assertEqual(list(expr.details.values_list('designation', flat=True)), ['Ramette A4'])

    def test_reception_refusee_sans_aucune_quantite(self):
        expr = self.creer()
        self.client.post(reverse('matieres:expression_recevoir', args=[expr.pk]))
        expr.refresh_from_db()
        self.assertEqual(expr.statut, 'nouveau')
        self.assertEqual(expr.details.count(), 2)   # rien n'est perdu

    def test_expression_recue_figee(self):
        expr = self.creer()
        self.saisir(expr, self.ramette, '40')
        self.client.post(reverse('matieres:expression_recevoir', args=[expr.pk]))
        self.saisir(expr, self.ramette, '99')
        self.assertEqual(expr.details.get().qte, 40)

    def test_pas_de_saisie_libre_ni_de_consolidation(self):
        expr = self.creer()
        self.client.post(reverse('matieres:htmx_expression_add_detail', args=[expr.pk]),
                         {'designation': 'Hors marché', 'qte': '1'})
        self.assertFalse(expr.details.filter(designation='Hors marché').exists())
        self.saisir(expr, self.ramette, '5')
        expr.recevoir(date.today())
        with self.assertRaises(ValueError):
            expr.consolider_dans_marche(self.marche)

    def test_changer_de_marche_refuse_si_des_quantites_sont_saisies(self):
        expr = self.creer()
        self.saisir(expr, self.ramette, '5')
        autre = Marche.objects.create(num_marche='M-2026-04', date_creation=date.today())
        self.client.post(reverse('matieres:expression_update', args=[expr.pk]), {
            'date_creation': date.today().isoformat(), 'mode': 'sur_marche', 'marche_id': autre.pk})
        expr.refresh_from_db()
        self.assertEqual(expr.marche, self.marche)

    def test_article_du_marche_demande_non_supprimable(self):
        expr = self.creer()
        self.saisir(expr, self.ramette, '5')
        self.client.post(reverse('matieres:htmx_marche_delete_detail', args=[self.ramette.pk]))
        self.assertTrue(DetailMarche.objects.filter(pk=self.ramette.pk).exists())

    def test_reprendre_ajoute_les_nouveaux_articles_du_marche(self):
        expr = self.creer()
        DetailMarche.objects.create(marche=self.marche, designation='Agrafes', nomenclature='22.01.003', qte=10)
        self.client.post(reverse('matieres:htmx_expression_reprendre', args=[expr.pk]))
        self.assertEqual(expr.details.count(), 3)


class ExpressionLibreTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create_user(username='service', password='x'))

    def test_expression_vide_ni_recue_ni_consolidee(self):
        expr = ExpressionBesoin.objects.create(date_creation=date.today())
        self.client.post(reverse('matieres:expression_recevoir', args=[expr.pk]))
        expr.refresh_from_db()
        self.assertEqual(expr.statut, 'nouveau')

    def test_circuit_libre_inchange(self):
        expr = ExpressionBesoin.objects.create(date_creation=date.today())
        self.client.post(reverse('matieres:htmx_expression_add_detail', args=[expr.pk]),
                         {'designation': 'Classeur', 'nomenclature': '22.02.001', 'qte': '12', 'prix_ttc': '1 500'})
        self.client.post(reverse('matieres:expression_recevoir', args=[expr.pk]))
        marche = Marche.objects.create(num_marche='M-LIBRE', date_creation=date.today())
        self.client.post(reverse('matieres:expression_consolider', args=[expr.pk]), {'marche_id': marche.pk})
        expr.refresh_from_db()
        self.assertEqual(expr.statut, 'consolide')
        self.assertEqual(marche.details.get().qte, 12)
