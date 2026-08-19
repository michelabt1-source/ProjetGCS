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
    path('bons-entree/<int:pk>/etat/', views.bon_entree_etat, name='bon_entree_etat'),
    path('bons-entree/<int:pk>/pv-reception/', views.bon_entree_pv_reception, name='bon_entree_pv_reception'),

    # Bons d'affectation
    path('bons-affectation/', views.bons_affectation_list, name='bons_affectation_list'),
    path('bons-affectation/<int:pk>/', views.bon_affectation_detail, name='bon_affectation_detail'),
    path('bons-affectation/nouveau/', views.bon_affectation_create, name='bon_affectation_create'),
    path('bons-affectation/<int:pk>/modifier/', views.bon_affectation_update, name='bon_affectation_update'),
    path('bons-affectation/<int:pk>/valider/', views.bon_affectation_valider, name='bon_affectation_valider'),
    path('bons-affectation/<int:pk>/devalider/', views.bon_affectation_devalider, name='bon_affectation_devalider'),
    path('bons-affectation/<int:pk>/etat/', views.bon_affectation_etat, name='bon_affectation_etat'),

    # Bons retour affectation
    path('bons-retour-affectation/', views.bons_retour_affectation_list, name='bons_retour_affectation_list'),
    path('bons-retour-affectation/nouveau/', views.bon_retour_affectation_create, name='bon_retour_affectation_create'),
    path('bons-retour-affectation/<int:pk>/modifier/', views.bon_retour_affectation_update, name='bon_retour_affectation_update'),
    path('bons-retour-affectation/<int:pk>/valider/', views.bon_retour_affectation_valider, name='bon_retour_affectation_valider'),
    path('bons-retour-affectation/<int:pk>/devalider/', views.bon_retour_affectation_devalider, name='bon_retour_affectation_devalider'),
    path('bons-retour-affectation/<int:pk>/etat/', views.bon_retour_affectation_etat, name='bon_retour_affectation_etat'),

    # Bons sortie provisoire
    path('bons-sortie-provisoire/', views.bons_sortie_prov_list, name='bons_sortie_prov_list'),
    path('bons-sortie-provisoire/<int:pk>/', views.bon_sortie_prov_detail, name='bon_sortie_prov_detail'),
    path('bons-sortie-provisoire/nouveau/', views.bon_sortie_prov_create, name='bon_sortie_prov_create'),
    path('bons-sortie-provisoire/<int:pk>/modifier/', views.bon_sortie_prov_update, name='bon_sortie_prov_update'),
    path('bons-sortie-provisoire/<int:pk>/valider/', views.bon_sortie_prov_valider, name='bon_sortie_prov_valider'),
    path('bons-sortie-provisoire/<int:pk>/devalider/', views.bon_sortie_prov_devalider, name='bon_sortie_prov_devalider'),
    path('bons-sortie-provisoire/<int:pk>/etat/', views.bon_sortie_prov_etat, name='bon_sortie_prov_etat'),

    # Bons retour sortie provisoire
    path('bons-retour-sortie-provisoire/', views.bons_retour_sortie_prov_list, name='bons_retour_sortie_prov_list'),
    path('bons-retour-sortie-provisoire/nouveau/', views.bon_retour_sortie_prov_create, name='bon_retour_sortie_prov_create'),
    path('bons-retour-sortie-provisoire/<int:pk>/modifier/', views.bon_retour_sortie_prov_update, name='bon_retour_sortie_prov_update'),
    path('bons-retour-sortie-provisoire/<int:pk>/valider/', views.bon_retour_sortie_prov_valider, name='bon_retour_sortie_prov_valider'),
    path('bons-retour-sortie-provisoire/<int:pk>/devalider/', views.bon_retour_sortie_prov_devalider, name='bon_retour_sortie_prov_devalider'),
    path('bons-retour-sortie-provisoire/<int:pk>/etat/', views.bon_retour_sortie_prov_etat, name='bon_retour_sortie_prov_etat'),

    # Bordereaux de mutation
    path('bons-mutation/', views.bons_mutation_list, name='bons_mutation_list'),
    path('bons-mutation/<int:pk>/', views.bon_mutation_detail, name='bon_mutation_detail'),
    path('bons-mutation/nouveau/', views.bon_mutation_create, name='bon_mutation_create'),
    path('bons-mutation/<int:pk>/modifier/', views.bon_mutation_update, name='bon_mutation_update'),
    path('bons-mutation/<int:pk>/valider/', views.bon_mutation_valider, name='bon_mutation_valider'),
    path('bons-mutation/<int:pk>/devalider/', views.bon_mutation_devalider, name='bon_mutation_devalider'),
    path('bons-mutation/<int:pk>/etat/', views.bon_mutation_etat, name='bon_mutation_etat'),

    # Bons sortie définitive (Groupe 1 — matières durables)
    path('bons-sortie-definitive/', views.bons_sortie_def_list, name='bons_sortie_def_list'),
    path('bons-sortie-definitive/<int:pk>/', views.bon_sortie_def_detail, name='bon_sortie_def_detail'),
    path('bons-sortie-definitive/nouveau/', views.bon_sortie_def_create, name='bon_sortie_def_create'),

    # Marchés
    path('marches/', views.marches_list, name='marches_list'),
    path('marches/nouveau/', views.marche_create, name='marche_create'),
    path('marches/<int:pk>/', views.marche_detail, name='marche_detail'),
    path('marches/<int:pk>/modifier/', views.marche_update, name='marche_update'),
    path('htmx/marche/<int:pk>/add-detail/', views.htmx_marche_add_detail, name='htmx_marche_add_detail'),
    path('htmx/marche/detail/<int:detail_pk>/delete/', views.htmx_marche_delete_detail, name='htmx_marche_delete_detail'),

    # Expressions de besoins
    path('expressions-besoin/', views.expressions_list, name='expressions_list'),
    path('expressions-besoin/nouveau/', views.expression_create, name='expression_create'),
    path('expressions-besoin/<int:pk>/', views.expression_detail, name='expression_detail'),
    path('expressions-besoin/<int:pk>/transformer/', views.expression_transform, name='expression_transform'),
    path('expressions-besoin/<int:pk>/modifier/', views.expression_update, name='expression_update'),
    path('htmx/expression/<int:pk>/add-detail/', views.htmx_expression_add_detail, name='htmx_expression_add_detail'),
    path('htmx/expression/detail/<int:detail_pk>/delete/', views.htmx_expression_delete_detail, name='htmx_expression_delete_detail'),

    # Bons de commande de services
    path('bons-commande-service/', views.bons_commande_service_list, name='bons_commande_service_list'),
    path('bons-commande-service/nouveau/', views.bon_commande_service_create, name='bon_commande_service_create'),
    path('bons-commande-service/a-livrer/', views.bons_commande_service_a_livrer, name='bons_commande_service_a_livrer'),
    path('bons-commande-service/<int:pk>/livrer/', views.bon_commande_service_livrer, name='bon_commande_service_livrer'),
    path('bons-commande-service/<int:pk>/', views.bon_commande_service_update, name='bon_commande_service_update'),
    path('bons-commande-service/<int:pk>/etat/', views.bon_commande_service_etat, name='bon_commande_service_etat'),
    path('bons-commande-service/<int:pk>/envoyer/', views.bon_commande_service_envoyer, name='bon_commande_service_envoyer'),
    path('bons-commande-service/<int:pk>/valider/', views.bon_commande_service_valider, name='bon_commande_service_valider'),
    path('bons-commande-service/<int:pk>/rejeter/', views.bon_commande_service_rejeter, name='bon_commande_service_rejeter'),
    path('htmx/bcs/<int:pk>/add-detail/', views.htmx_bcs_add_detail, name='htmx_bcs_add_detail'),
    path('htmx/bcs/detail/<int:detail_pk>/delete/', views.htmx_bcs_delete_detail, name='htmx_bcs_delete_detail'),
    path('htmx/bcs/produit-search/', views.htmx_bcs_produit_search, name='htmx_bcs_produit_search'),
    path('htmx/bcs/modal-produits/', views.htmx_bcs_modal_produits, name='htmx_bcs_modal_produits'),
    path('htmx/bcs/lignes/', views.htmx_bcs_lignes, name='htmx_bcs_lignes'),

    # Bons sortie définitive G1 (Réformes)
    path('bons-sortie-definitive-g1/', views.bons_sortie_def_g1_list, name='bons_sortie_def_g1_list'),
    path('bons-sortie-definitive-g1/nouveau/', views.bon_sortie_def_g1_create, name='bon_sortie_def_g1_create'),
    path('bons-sortie-definitive-g1/<int:pk>/modifier/', views.bon_sortie_def_g1_update, name='bon_sortie_def_g1_update'),
    path('bons-sortie-definitive-g1/<int:pk>/valider/', views.bon_sortie_def_g1_valider, name='bon_sortie_def_g1_valider'),
    path('bons-sortie-definitive-g1/<int:pk>/devalider/', views.bon_sortie_def_g1_devalider, name='bon_sortie_def_g1_devalider'),
    path('bons-sortie-definitive-g1/<int:pk>/etat/', views.bon_sortie_def_g1_etat, name='bon_sortie_def_g1_etat'),
    path('bons-sortie-definitive-g1/<int:pk>/etat-sortie/', views.bon_sortie_def_g1_etat_sortie, name='bon_sortie_def_g1_etat_sortie'),
    path('bons-sortie-definitive-g1/<int:pk>/etat-vente-destruction/', views.bon_sortie_def_g1_etat_vd, name='bon_sortie_def_g1_etat_vd'),
    path('htmx/bsdg1/<int:pk>/add-detail/', views.htmx_bsdg1_add_detail, name='htmx_bsdg1_add_detail'),
    path('htmx/bsdg1/detail/<int:detail_pk>/delete/', views.htmx_bsdg1_delete_detail, name='htmx_bsdg1_delete_detail'),
    path('htmx/bsdg1/produit-search/', views.htmx_bsdg1_produit_search, name='htmx_bsdg1_produit_search'),
    path('htmx/bsdg1/modal-produits/', views.htmx_bsdg1_modal_produits, name='htmx_bsdg1_modal_produits'),

    # Bons sortie définitive Groupe 2 (consommables)
    path('bons-sortie-definitive-g2/', views.bons_sortie_def_g2_list, name='bons_sortie_def_g2_list'),
    path('bons-sortie-definitive-g2/nouveau/', views.bon_sortie_def_g2_create, name='bon_sortie_def_g2_create'),
    path('bons-sortie-definitive-g2/<int:pk>/modifier/', views.bon_sortie_def_g2_update, name='bon_sortie_def_g2_update'),
    path('bons-sortie-definitive-g2/<int:pk>/valider/', views.bon_sortie_def_g2_valider, name='bon_sortie_def_g2_valider'),
    path('bons-sortie-definitive-g2/<int:pk>/devalider/', views.bon_sortie_def_g2_devalider, name='bon_sortie_def_g2_devalider'),
    path('bons-sortie-definitive-g2/<int:pk>/etat/', views.bon_sortie_def_g2_etat, name='bon_sortie_def_g2_etat'),

    # Journal
    path('journal/', views.journal_list, name='journal_list'),
    path('journal/etat/', views.journal_etat, name='journal_etat'),

    # Balance
    path('balance/', views.balance_list, name='balance_list'),
    path('balance/periodique/', views.balance_periodique_list, name='balance_periodique_list'),
    path('balance/etat/', views.balance_general_etat, name='balance_general_etat'),
    path('balance/periodique/etat/', views.balance_periodique_etat, name='balance_periodique_etat'),

    # Référentiels
    path('fournisseurs/', views.fournisseurs_list, name='fournisseurs_list'),
    path('beneficiaires/', views.beneficiaires_list, name='beneficiaires_list'),
    path('beneficiaires/nouveau/', views.beneficiaire_create, name='beneficiaire_create'),
    path('beneficiaires/<int:pk>/modifier/', views.beneficiaire_update, name='beneficiaire_update'),
    path('beneficiaires/<int:pk>/supprimer/', views.beneficiaire_delete, name='beneficiaire_delete'),

    # Services & Bureaux
    path('services/', views.service_list, name='service_list'),
    path('services/nouveau/', views.service_create, name='service_create'),
    path('services/<int:pk>/modifier/', views.service_update, name='service_update'),
    path('services/<int:pk>/supprimer/', views.service_delete, name='service_delete'),
    path('bureaux/', views.bureau_list, name='bureau_list'),
    path('bureaux/nouveau/', views.bureau_create, name='bureau_create'),
    path('bureaux/<int:pk>/modifier/', views.bureau_update, name='bureau_update'),
    path('bureaux/<int:pk>/supprimer/', views.bureau_delete, name='bureau_delete'),
    path('htmx/bureaux-par-service/<int:service_pk>/', views.htmx_bureaux_par_service, name='htmx_bureaux_par_service'),
    path('htmx/bureaux-options/', views.htmx_bureaux_options, name='htmx_bureaux_options'),

    # HTMX partials
    path('htmx/stats-bons/', views.htmx_stats_bons, name='htmx_stats_bons'),
    path('htmx/chart-data/', views.htmx_chart_data, name='htmx_chart_data'),
    path('htmx/recherche-produit/', views.htmx_recherche_produit, name='htmx_recherche_produit'),
    # Bon de retour sortie provisoire — HTMX
    path('htmx/brsp/<int:pk>/add-detail/', views.htmx_brsp_add_detail, name='htmx_brsp_add_detail'),
    path('htmx/brsp/detail/<int:detail_pk>/delete/', views.htmx_brsp_delete_detail, name='htmx_brsp_delete_detail'),
    path('htmx/brsp/<int:pk>/produit-search/', views.htmx_brsp_produit_search, name='htmx_brsp_produit_search'),
    path('htmx/brsp/<int:pk>/modal-produits/', views.htmx_brsp_modal_produits, name='htmx_brsp_modal_produits'),
    # Bordereau de mutation — HTMX
    path('htmx/bm/<int:pk>/add-detail/', views.htmx_bm_add_detail, name='htmx_bm_add_detail'),
    path('htmx/bm/detail/<int:detail_pk>/delete/', views.htmx_bm_delete_detail, name='htmx_bm_delete_detail'),
    path('htmx/bm/<int:pk>/produit-search/', views.htmx_bm_produit_search, name='htmx_bm_produit_search'),
    path('htmx/bm/<int:pk>/modal-produits/', views.htmx_bm_modal_produits, name='htmx_bm_modal_produits'),
    # Bon de sortie provisoire — HTMX
    path('htmx/bsp/<int:pk>/add-detail/', views.htmx_bsp_add_detail, name='htmx_bsp_add_detail'),
    path('htmx/bsp/detail/<int:detail_pk>/delete/', views.htmx_bsp_delete_detail, name='htmx_bsp_delete_detail'),
    path('htmx/bsp/<int:pk>/produit-search/', views.htmx_bsp_produit_search, name='htmx_bsp_produit_search'),
    path('htmx/bsp/<int:pk>/modal-produits/', views.htmx_bsp_modal_produits, name='htmx_bsp_modal_produits'),
    # Bon de retour d'affectation — HTMX
    path('htmx/bra/<int:pk>/add-detail/', views.htmx_bra_add_detail, name='htmx_bra_add_detail'),
    path('htmx/bra/detail/<int:detail_pk>/delete/', views.htmx_bra_delete_detail, name='htmx_bra_delete_detail'),
    path('htmx/bra/<int:pk>/produit-search/', views.htmx_bra_produit_search, name='htmx_bra_produit_search'),
    path('htmx/bra/<int:pk>/modal-produits/', views.htmx_bra_modal_produits, name='htmx_bra_modal_produits'),
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
    # Bon de sortie définitive Groupe 2 — HTMX
    path('htmx/bsdg2/<int:pk>/add-detail/', views.htmx_bsdg2_add_detail, name='htmx_bsdg2_add_detail'),
    path('htmx/bsdg2/detail/<int:detail_pk>/delete/', views.htmx_bsdg2_delete_detail, name='htmx_bsdg2_delete_detail'),
    path('htmx/bsdg2/produit-search/', views.htmx_bsdg2_produit_search, name='htmx_bsdg2_produit_search'),
    path('htmx/bsdg2/modal-produits/', views.htmx_bsdg2_modal_produits, name='htmx_bsdg2_modal_produits'),

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
    path('etats/inventaire-individuel/etat/', views.inventaire_individuel_etat, name='inventaire_individuel_etat'),
    path('etats/grand-livre/', views.grand_livre, name='grand_livre'),
    path('etats/grand-livre/<str:nomenclature>/etat/', views.grand_livre_compte_etat, name='grand_livre_compte_etat'),
    path('etats/fiche-stock/<int:pk>/', views.fiche_stock, name='fiche_stock'),
    path('etats/fiche-stock/<int:pk>/etat/', views.fiche_stock_etat, name='fiche_stock_etat'),
]
