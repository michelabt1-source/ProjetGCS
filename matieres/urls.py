from django.urls import path
from . import views

app_name = 'matieres'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Stock / Produits
    path('produits/', views.produits_list, name='produits_list'),
    path('produits/<int:pk>/', views.produit_detail, name='produit_detail'),
    path('produits/ajouter/', views.produit_create, name='produit_create'),
    path('produits/<int:pk>/modifier/', views.produit_update, name='produit_update'),

    # Depots
    path('depots/', views.depots_list, name='depots_list'),
    path('stock-depot/', views.stock_depot_list, name='stock_depot_list'),

    # Bons d'entrée
    path('bons-entree/', views.bons_entree_list, name='bons_entree_list'),
    path('bons-entree/<int:pk>/', views.bon_entree_detail, name='bon_entree_detail'),
    path('bons-entree/nouveau/', views.bon_entree_create, name='bon_entree_create'),
    path('bons-entree/<int:pk>/modifier/', views.bon_entree_update, name='bon_entree_update'),
    path('bons-entree/<int:pk>/valider/', views.bon_entree_valider, name='bon_entree_valider'),
    path('bons-entree/<int:pk>/devalider/', views.bon_entree_devalider, name='bon_entree_devalider'),

    # Bons d'affectation
    path('bons-affectation/', views.bons_affectation_list, name='bons_affectation_list'),
    path('bons-affectation/<int:pk>/', views.bon_affectation_detail, name='bon_affectation_detail'),
    path('bons-affectation/nouveau/', views.bon_affectation_create, name='bon_affectation_create'),
    path('bons-affectation/<int:pk>/modifier/', views.bon_affectation_update, name='bon_affectation_update'),
    path('bons-affectation/<int:pk>/valider/', views.bon_affectation_valider, name='bon_affectation_valider'),
    path('bons-affectation/<int:pk>/devalider/', views.bon_affectation_devalider, name='bon_affectation_devalider'),

    # Bons retour affectation
    path('bons-retour-affectation/', views.bons_retour_affectation_list, name='bons_retour_affectation_list'),
    path('bons-retour-affectation/nouveau/', views.bon_retour_affectation_create, name='bon_retour_affectation_create'),
    path('bons-retour-affectation/<int:pk>/modifier/', views.bon_retour_affectation_update, name='bon_retour_affectation_update'),
    path('bons-retour-affectation/<int:pk>/valider/', views.bon_retour_affectation_valider, name='bon_retour_affectation_valider'),
    path('bons-retour-affectation/<int:pk>/devalider/', views.bon_retour_affectation_devalider, name='bon_retour_affectation_devalider'),

    # Bons sortie provisoire
    path('bons-sortie-provisoire/', views.bons_sortie_prov_list, name='bons_sortie_prov_list'),
    path('bons-sortie-provisoire/<int:pk>/', views.bon_sortie_prov_detail, name='bon_sortie_prov_detail'),
    path('bons-sortie-provisoire/nouveau/', views.bon_sortie_prov_create, name='bon_sortie_prov_create'),
    path('bons-sortie-provisoire/<int:pk>/modifier/', views.bon_sortie_prov_update, name='bon_sortie_prov_update'),
    path('bons-sortie-provisoire/<int:pk>/valider/', views.bon_sortie_prov_valider, name='bon_sortie_prov_valider'),
    path('bons-sortie-provisoire/<int:pk>/devalider/', views.bon_sortie_prov_devalider, name='bon_sortie_prov_devalider'),

    # Bons retour sortie provisoire
    path('bons-retour-sortie-provisoire/', views.bons_retour_sortie_prov_list, name='bons_retour_sortie_prov_list'),
    path('bons-retour-sortie-provisoire/nouveau/', views.bon_retour_sortie_prov_create, name='bon_retour_sortie_prov_create'),
    path('bons-retour-sortie-provisoire/<int:pk>/modifier/', views.bon_retour_sortie_prov_update, name='bon_retour_sortie_prov_update'),
    path('bons-retour-sortie-provisoire/<int:pk>/valider/', views.bon_retour_sortie_prov_valider, name='bon_retour_sortie_prov_valider'),
    path('bons-retour-sortie-provisoire/<int:pk>/devalider/', views.bon_retour_sortie_prov_devalider, name='bon_retour_sortie_prov_devalider'),

    # Bons sortie définitive
    path('bons-sortie-definitive/', views.bons_sortie_def_list, name='bons_sortie_def_list'),
    path('bons-sortie-definitive/<int:pk>/', views.bon_sortie_def_detail, name='bon_sortie_def_detail'),
    path('bons-sortie-definitive/nouveau/', views.bon_sortie_def_create, name='bon_sortie_def_create'),

    # Bons sortie définitive G1
    path('bons-sortie-definitive-g1/', views.bons_sortie_def_g1_list, name='bons_sortie_def_g1_list'),

    # Journal
    path('journal/', views.journal_list, name='journal_list'),

    # Balance
    path('balance/', views.balance_list, name='balance_list'),

    # Référentiels
    path('fournisseurs/', views.fournisseurs_list, name='fournisseurs_list'),
    path('beneficiaires/', views.beneficiaires_list, name='beneficiaires_list'),

    # HTMX partials
    path('htmx/stats-bons/', views.htmx_stats_bons, name='htmx_stats_bons'),
    path('htmx/chart-data/', views.htmx_chart_data, name='htmx_chart_data'),
    path('htmx/recherche-produit/', views.htmx_recherche_produit, name='htmx_recherche_produit'),
    # Bon de retour sortie provisoire — HTMX
    path('htmx/brsp/<int:pk>/add-detail/', views.htmx_brsp_add_detail, name='htmx_brsp_add_detail'),
    path('htmx/brsp/detail/<int:detail_pk>/delete/', views.htmx_brsp_delete_detail, name='htmx_brsp_delete_detail'),
    path('htmx/brsp/produit-search/', views.htmx_brsp_produit_search, name='htmx_brsp_produit_search'),
    path('htmx/brsp/modal-produits/', views.htmx_brsp_modal_produits, name='htmx_brsp_modal_produits'),
    # Bon de sortie provisoire — HTMX
    path('htmx/bsp/<int:pk>/add-detail/', views.htmx_bsp_add_detail, name='htmx_bsp_add_detail'),
    path('htmx/bsp/detail/<int:detail_pk>/delete/', views.htmx_bsp_delete_detail, name='htmx_bsp_delete_detail'),
    path('htmx/bsp/produit-search/', views.htmx_bsp_produit_search, name='htmx_bsp_produit_search'),
    path('htmx/bsp/modal-produits/', views.htmx_bsp_modal_produits, name='htmx_bsp_modal_produits'),
    # Bon de retour d'affectation — HTMX
    path('htmx/bra/<int:pk>/add-detail/', views.htmx_bra_add_detail, name='htmx_bra_add_detail'),
    path('htmx/bra/detail/<int:detail_pk>/delete/', views.htmx_bra_delete_detail, name='htmx_bra_delete_detail'),
    path('htmx/bra/produit-search/', views.htmx_bra_produit_search, name='htmx_bra_produit_search'),
    path('htmx/bra/modal-produits/', views.htmx_bra_modal_produits, name='htmx_bra_modal_produits'),
    # Bon d'affectation — HTMX
    path('htmx/ba/<int:pk>/add-detail/', views.htmx_ba_add_detail, name='htmx_ba_add_detail'),
    path('htmx/ba/detail/<int:detail_pk>/delete/', views.htmx_ba_delete_detail, name='htmx_ba_delete_detail'),
    path('htmx/ba/produit-search/', views.htmx_ba_produit_search, name='htmx_ba_produit_search'),
    path('htmx/ba/modal-produits/', views.htmx_ba_modal_produits, name='htmx_ba_modal_produits'),
    # Bon d'entrée — HTMX
    path('htmx/be/<int:pk>/add-detail/', views.htmx_be_add_detail, name='htmx_be_add_detail'),
    path('htmx/be/detail/<int:detail_pk>/delete/', views.htmx_be_delete_detail, name='htmx_be_delete_detail'),
    path('htmx/be/produit-search/', views.htmx_be_produit_search, name='htmx_be_produit_search'),
    path('htmx/be/produit-info/<int:pk>/', views.htmx_be_produit_info, name='htmx_be_produit_info'),
    path('htmx/be/modal-produits/', views.htmx_be_modal_produits, name='htmx_be_modal_produits'),

    # Import Excel
    path('import/', views.import_index, name='import_index'),
    path('import/template/', views.import_template_download, name='import_template'),

    # Structure
    path('comptes/', views.compte_principal_list, name='compte_principal_list'),
    path('sous-comptes/', views.sous_compte_list, name='sous_compte_list'),

    # Configuration
    path('config/societe/', views.societe_view, name='societe_view'),
    path('config/unites/', views.unite_list, name='unite_list'),
    path('config/type-operations/', views.type_op_list, name='type_op_list'),
    path('config/membres-commission/', views.membre_commission_list, name='membre_commission_list'),
    path('config/membres-reforme/', views.membre_reforme_list, name='membre_reforme_list'),
    path('config/annees-exercice/', views.annee_exercice_list, name='annee_exercice_list'),
    path('config/matieres-depot/', views.matieres_depot_config, name='matieres_depot_config'),
    path('config/profils/', views.profil_list, name='profil_list'),

    # États / Inventaires
    path('etats/inventaire-global/', views.inventaire_global, name='inventaire_global'),
    path('etats/inventaire-depot/', views.inventaire_depot, name='inventaire_depot'),
    path('etats/releve-recapitulatif/', views.releve_recapitulatif, name='releve_recapitulatif'),
    path('etats/inventaire-individuel/', views.inventaire_individuel, name='inventaire_individuel'),
    path('etats/grand-livre/', views.grand_livre, name='grand_livre'),
    path('etats/fiche-stock/<int:pk>/', views.fiche_stock, name='fiche_stock'),
]
