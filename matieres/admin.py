from django.contrib import admin
from .models import (
    AnneeExercice, Depot, Beneficiaire, ComptePrincipale, SousCompte,
    Fournisseur, Unite, TypeOperation, Profil, SocieteGCS,
    MembreCommission, MembreCommissionReforme, ProfilCommission,
    Produit, MatieresDepot, StockDepot,
    BonEntree, DetailBonEntree,
    BonAffectation, DetailBonAffectation,
    BonRetourAffectation, DetailBonRetourAffectation,
    BonSortieProvisoire, DetailBonSortieProvisoire,
    BonRetourSortieProvisoire, DetailBonRetourSortieProvisoire,
    BonSortieDefinitive, DetailBonSortieDefinitive,
    BonSortieDefinitiveG1, DetailBonSortieDefinitiveG1,
    BalancePeriodique, Journal,
)

admin.site.site_header = "Comptabilité des Matières - Administration"
admin.site.site_title = "Compta Matières"
admin.site.index_title = "Tableau de bord administrateur"


class DetailBonEntreeInline(admin.TabularInline):
    model = DetailBonEntree
    extra = 1


class DetailBonAffectationInline(admin.TabularInline):
    model = DetailBonAffectation
    extra = 1


class DetailBonRetourAffectationInline(admin.TabularInline):
    model = DetailBonRetourAffectation
    extra = 1


class DetailBonSortieProvInline(admin.TabularInline):
    model = DetailBonSortieProvisoire
    extra = 1


class DetailBonRetourSortieProvInline(admin.TabularInline):
    model = DetailBonRetourSortieProvisoire
    extra = 1


class DetailBonSortieDefInline(admin.TabularInline):
    model = DetailBonSortieDefinitive
    extra = 1


class DetailBonSortieDefG1Inline(admin.TabularInline):
    model = DetailBonSortieDefinitiveG1
    extra = 1


@admin.register(AnneeExercice)
class AnneeExerciceAdmin(admin.ModelAdmin):
    list_display = ['annee', 'date_debut', 'date_fin']


@admin.register(Depot)
class DepotAdmin(admin.ModelAdmin):
    list_display = ['code']


@admin.register(Beneficiaire)
class BeneficiaireAdmin(admin.ModelAdmin):
    list_display = ['nom', 'responsable']
    search_fields = ['nom']


@admin.register(ComptePrincipale)
class ComptePrincipaleAdmin(admin.ModelAdmin):
    list_display = ['num_compte', 'famille']
    search_fields = ['famille']


@admin.register(SousCompte)
class SousCompteAdmin(admin.ModelAdmin):
    list_display = ['num_sous_compte', 'famille_sc', 'compte_principal']
    list_filter = ['compte_principal']
    search_fields = ['famille_sc']


@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ['nom', 'ville', 'pays', 'telephone']
    search_fields = ['nom', 'ville']


@admin.register(Unite)
class UniteAdmin(admin.ModelAdmin):
    list_display = ['libelle']


@admin.register(TypeOperation)
class TypeOperationAdmin(admin.ModelAdmin):
    list_display = ['libelle']


@admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ['role']


@admin.register(SocieteGCS)
class SocieteGCSAdmin(admin.ModelAdmin):
    list_display = ['nom', 'ville', 'telephone', 'email']


@admin.register(MembreCommission)
class MembreCommissionAdmin(admin.ModelAdmin):
    list_display = ['nom', 'qualite']


@admin.register(MembreCommissionReforme)
class MembreCommissionReformeAdmin(admin.ModelAdmin):
    list_display = ['nom', 'qualite']


@admin.register(ProfilCommission)
class ProfilCommissionAdmin(admin.ModelAdmin):
    list_display = ['qualite']


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ['nomenclature', 'designation', 'stock_global', 'qte_affectation', 'qte_sp', 'unite']
    list_filter = ['compte_principal', 'sous_compte', 'unite']
    search_fields = ['nomenclature', 'designation']
    ordering = ['nomenclature']


@admin.register(MatieresDepot)
class MatieresDepotAdmin(admin.ModelAdmin):
    list_display = ['depot', 'num_sous_compte']
    list_filter = ['depot']


@admin.register(StockDepot)
class StockDepotAdmin(admin.ModelAdmin):
    list_display = ['nomenclature', 'designation', 'depot', 'qte_stock']
    list_filter = ['depot']
    search_fields = ['nomenclature', 'designation']


@admin.register(BonEntree)
class BonEntreeAdmin(admin.ModelAdmin):
    list_display = ['num_bon', 'date_creation', 'depot', 'fournisseur', 'valide']
    list_filter = ['valide', 'depot', 'annee_exercice']
    search_fields = ['num_bon']
    inlines = [DetailBonEntreeInline]
    date_hierarchy = 'date_creation'


@admin.register(BonAffectation)
class BonAffectationAdmin(admin.ModelAdmin):
    list_display = ['num_bon', 'date_affectation', 'depot', 'beneficiaire', 'valide']
    list_filter = ['valide', 'depot', 'beneficiaire']
    search_fields = ['num_bon']
    inlines = [DetailBonAffectationInline]


@admin.register(BonRetourAffectation)
class BonRetourAffectationAdmin(admin.ModelAdmin):
    list_display = ['num_bon', 'date_creation', 'depot', 'beneficiaire']
    list_filter = ['depot', 'beneficiaire']
    inlines = [DetailBonRetourAffectationInline]


@admin.register(BonSortieProvisoire)
class BonSortieProvAdmin(admin.ModelAdmin):
    list_display = ['num_bon', 'annee_creation', 'depot', 'beneficiaire', 'valide']
    list_filter = ['valide', 'depot', 'beneficiaire']
    inlines = [DetailBonSortieProvInline]


@admin.register(BonRetourSortieProvisoire)
class BonRetourSortieProvAdmin(admin.ModelAdmin):
    list_display = ['num_bon', 'date_retour', 'depot', 'beneficiaire', 'valide']
    list_filter = ['valide', 'depot']
    inlines = [DetailBonRetourSortieProvInline]


@admin.register(BonSortieDefinitive)
class BonSortieDefAdmin(admin.ModelAdmin):
    list_display = ['num_bon', 'date_creation', 'groupe', 'type_sortie', 'depot', 'beneficiaire', 'valide']
    list_filter = ['valide', 'groupe', 'depot', 'beneficiaire', 'type_sortie']
    inlines = [DetailBonSortieDefInline]


@admin.register(BonSortieDefinitiveG1)
class BonSortieDefG1Admin(admin.ModelAdmin):
    list_display = ['num_bon', 'date_creation', 'type_sortie', 'depot', 'beneficiaire', 'valide']
    list_filter = ['valide', 'depot', 'type_sortie']
    inlines = [DetailBonSortieDefG1Inline]


@admin.register(BalancePeriodique)
class BalancePeriodiqueAdmin(admin.ModelAdmin):
    list_display = ['nomenclature', 'designation', 'existant_dp', 'entree_periode', 'sortie_periode', 'existant_fin_periode', 'annee_exercice']
    list_filter = ['annee_exercice']
    search_fields = ['nomenclature', 'designation']


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ['date_creation', 'num_bon', 'type_entree', 'designation', 'qte', 'beneficiaire', 'depot']
    list_filter = ['type_entree', 'depot', 'annee_exercice']
    search_fields = ['designation', 'nomenclature', 'beneficiaire']
    date_hierarchy = 'date_creation'
