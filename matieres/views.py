from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.http import JsonResponse, HttpResponse
from datetime import date, datetime, timedelta
from decimal import Decimal
import json

from .models import (
    Produit, Depot, StockDepot,
    BonEntree, DetailBonEntree,
    BonAffectation, DetailBonAffectation,
    BonRetourAffectation, DetailBonRetourAffectation,
    BonSortieProvisoire, DetailBonSortieProvisoire,
    BonRetourSortieProvisoire, DetailBonRetourSortieProvisoire,
    BonMutation, DetailBonMutation,
    BonSortieDefinitive, DetailBonSortieDefinitive, BonSortieDefinitiveG1, DetailBonSortieDefinitiveG1,
    Journal, BalancePeriodique,
    Fournisseur, Beneficiaire, AnneeExercice, SocieteGCS,
    ComptePrincipale, SousCompte, Unite, TypeOperation,
    MembreCommission, MembreCommissionReforme, MatieresDepot, Profil,
    Service, Bureau,
    Marche, DetailMarche, ExpressionBesoin, DetailExpressionBesoin,
    BonCommandeService, DetailBonCommandeService,
)
from .importeurs import process_excel, generate_template, IMPORTERS


# ─────────────────────────── DASHBOARD ───────────────────────────

@login_required
def dashboard(request):
    aujourd_hui = date.today()
    mois_courant = aujourd_hui.month
    annee_courante = aujourd_hui.year
    debut_mois = date(annee_courante, mois_courant, 1)

    total_produits = Produit.objects.count()
    total_depots = Depot.objects.count()
    total_fournisseurs = Fournisseur.objects.count()
    total_beneficiaires = Beneficiaire.objects.count()

    bons_entree_mois = BonEntree.objects.filter(date_creation__gte=debut_mois).count()
    bons_affectation_mois = BonAffectation.objects.filter(date_affectation__gte=debut_mois).count()
    bons_sortie_def_mois = BonSortieDefinitive.objects.filter(date_creation__gte=debut_mois).count()
    bons_sortie_prov_mois = BonSortieProvisoire.objects.filter(annee_creation=annee_courante).count()

    valeur_stock = StockDepot.objects.aggregate(total=Sum('qte_stock'))['total'] or 0

    bons_entree_attente = BonEntree.objects.filter(valide=False).count()
    bons_sortie_def_attente = BonSortieDefinitive.objects.filter(valide=False).count()
    bons_affectation_attente = BonAffectation.objects.filter(valide=False).count()

    dernieres_operations = Journal.objects.order_by('-date_creation', '-id')[:10]
    stock_faible = StockDepot.objects.filter(qte_stock__lt=5).order_by('qte_stock')[:8]

    # Graphique 6 derniers mois
    labels_mois = []
    data_entrees = []
    data_sorties = []
    mois_names = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
    for i in range(5, -1, -1):
        if mois_courant - i <= 0:
            mois = mois_courant - i + 12
            an = annee_courante - 1
        else:
            mois = mois_courant - i
            an = annee_courante
        debut = date(an, mois, 1)
        fin = date(an, mois + 1, 1) - timedelta(days=1) if mois < 12 else date(an + 1, 1, 1) - timedelta(days=1)
        labels_mois.append(f"{mois_names[mois-1]} {an}")
        data_entrees.append(BonEntree.objects.filter(date_creation__range=[debut, fin]).count())
        data_sorties.append(BonSortieDefinitive.objects.filter(date_creation__range=[debut, fin]).count())

    # Stock par dépôt
    stock_par_depot = []
    for depot in Depot.objects.all():
        total = StockDepot.objects.filter(depot=depot).aggregate(t=Sum('qte_stock'))['t'] or 0
        stock_par_depot.append({'depot': depot.code, 'total': total})

    societe = SocieteGCS.objects.first()

    context = {
        'page_title': 'Tableau de bord',
        'total_produits': total_produits,
        'total_depots': total_depots,
        'total_fournisseurs': total_fournisseurs,
        'total_beneficiaires': total_beneficiaires,
        'bons_entree_mois': bons_entree_mois,
        'bons_affectation_mois': bons_affectation_mois,
        'bons_sortie_def_mois': bons_sortie_def_mois,
        'bons_sortie_prov_mois': bons_sortie_prov_mois,
        'valeur_stock': valeur_stock,
        'bons_entree_attente': bons_entree_attente,
        'bons_sortie_def_attente': bons_sortie_def_attente,
        'bons_affectation_attente': bons_affectation_attente,
        'dernieres_operations': dernieres_operations,
        'stock_faible': stock_faible,
        'labels_mois': json.dumps(labels_mois),
        'data_entrees': json.dumps(data_entrees),
        'data_sorties': json.dumps(data_sorties),
        'stock_par_depot': json.dumps(stock_par_depot),
        'societe': societe,
        'aujourd_hui': aujourd_hui,
    }
    return render(request, 'dashboard.html', context)


# ─────────────────────────── PRODUITS ───────────────────────────

@login_required
def produits_list(request):
    query = request.GET.get('q', '')
    produits = Produit.objects.select_related('unite', 'compte_principal', 'sous_compte')
    if query:
        produits = produits.filter(Q(designation__icontains=query) | Q(nomenclature__icontains=query))
    produits = produits.order_by('nomenclature')
    context = {
        'page_title': 'Produits / Matières',
        'produits': produits,
        'query': query,
        'total': produits.count(),
    }
    return render(request, 'produits/list.html', context)


@login_required
def produit_detail(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    stocks = StockDepot.objects.filter(produit=produit)
    journal = Journal.objects.filter(nomenclature=produit.nomenclature).order_by('-date_creation')[:20]
    context = {
        'page_title': f'Produit - {produit.designation}',
        'produit': produit,
        'stocks': stocks,
        'journal': journal,
    }
    return render(request, 'produits/detail.html', context)


@login_required
def produit_create(request):
    context = {'page_title': 'Nouveau produit'}
    return render(request, 'produits/form.html', context)


@login_required
def produit_update(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    context = {'page_title': f'Modifier - {produit.designation}', 'produit': produit}
    return render(request, 'produits/form.html', context)


# ─────────────────────────── DÉPÔTS ───────────────────────────

@login_required
def depots_list(request):
    depots = Depot.objects.annotate(nb_articles=Count('stockdepot')).order_by('code')
    context = {'page_title': 'Dépôts', 'depots': depots}
    return render(request, 'depots/list.html', context)


@login_required
def stock_depot_list(request):
    depot_filtre = request.GET.get('depot', '')
    query = request.GET.get('q', '')
    stocks = StockDepot.objects.select_related('depot', 'produit').order_by('depot__code', 'nomenclature')
    if depot_filtre:
        stocks = stocks.filter(depot__code=depot_filtre)
    if query:
        stocks = stocks.filter(Q(designation__icontains=query) | Q(nomenclature__icontains=query))
    context = {
        'page_title': 'Stock par dépôt',
        'stocks': stocks,
        'depots': Depot.objects.all(),
        'depot_filtre': depot_filtre,
        'query': query,
    }
    return render(request, 'depots/stock.html', context)


# ─────────────────────────── BONS D'ENTRÉE ───────────────────────────

@login_required
def bons_entree_list(request):
    bons = BonEntree.objects.select_related('depot', 'fournisseur', 'annee_exercice').order_by('-date_creation', '-num_bon')
    context = {
        'page_title': "Bons d'entrée",
        'bons': bons,
        'nb_non_valides': bons.filter(valide=False).count(),
    }
    return render(request, 'bons/entree_list.html', context)


@login_required
def bon_entree_detail(request, pk):
    bon = get_object_or_404(BonEntree, pk=pk)
    context = {
        'page_title': f"Bon d'entrée N°{bon.num_bon:04d}",
        'bon': bon,
        'details': bon.details.select_related('produit', 'unite').all(),
    }
    return render(request, 'bons/entree_detail.html', context)


@login_required
def bon_entree_etat(request, pk):
    bon = get_object_or_404(BonEntree, pk=pk)
    details = list(bon.details.select_related('produit', 'unite').all())
    for d in details:
        segments = d.nomenclature.split('.') if d.nomenclature else []
        d.groupe_disp = segments[0][0] if segments and segments[0] else ''
        d.compte_principal_disp = segments[0] if len(segments) >= 1 else ''
        d.sous_compte_disp = '.'.join(segments[:2]) if len(segments) >= 2 else ''
    context = {
        'page_title': f"État — Bon d'entrée N°{bon.num_bon:04d}",
        'bon': bon,
        'societe': SocieteGCS.objects.first(),
        'details': details,
        'total_qte': sum(d.qte for d in details),
        'total_ttc': bon.total_ttc(),
    }
    return render(request, 'bons/entree_etat.html', context)


@login_required
def bon_entree_pv_reception(request, pk):
    bon = get_object_or_404(BonEntree, pk=pk)
    details = list(bon.details.select_related('unite').all())
    context = {
        'page_title': f"PV de réception — Bon d'entrée N°{bon.num_bon:04d}",
        'bon': bon,
        'societe': SocieteGCS.objects.first(),
        'details': details,
        'total_qte': sum(d.qte for d in details),
        'total_ttc': bon.total_ttc(),
        'membres_commission': MembreCommission.objects.order_by('nom'),
    }
    return render(request, 'bons/entree_pv_reception.html', context)


@login_required
def bon_entree_create(request):
    if request.method == 'POST':
        try:
            num_bon = int(request.POST.get('num_bon') or 1)
            date_creation = request.POST.get('date_creation') or date.today().isoformat()
            annee_exercice_id = request.POST.get('annee_exercice') or None
            references_pieces = request.POST.get('references_pieces', '')
            type_entree_id = request.POST.get('type_entree') or None
            depot_id = request.POST.get('depot') or None
            fournisseur_id = request.POST.get('fournisseur') or None
            num_bon_engagement = int(request.POST.get('num_bon_engagement') or 0)
            num_bon_commande = int(request.POST.get('num_bon_commande') or 0)
            num_pvc = request.POST.get('num_pvc', '')
            chapitre = request.POST.get('chapitre', '')

            bon = BonEntree.objects.create(
                num_bon=num_bon,
                date_creation=date_creation,
                annee_exercice_id=annee_exercice_id,
                references_pieces=references_pieces,
                type_entree_id=type_entree_id,
                valide=False,
                depot_id=depot_id,
                fournisseur_id=fournisseur_id,
                num_bon_engagement=num_bon_engagement,
                num_bon_commande=num_bon_commande,
                num_pvc=num_pvc,
                chapitre=chapitre,
            )
            messages.success(request, f"Bon d'entrée BE-{bon.num_bon:04d} créé avec succès.")
            return redirect('matieres:bon_entree_update', pk=bon.pk)
        except Exception as e:
            messages.error(request, f"Erreur lors de la création : {e}")

    last = BonEntree.objects.order_by('-num_bon').first()
    next_num = (last.num_bon + 1) if last else 1
    annee_courante = AnneeExercice.objects.filter(annee=date.today().year).first()

    context = {
        'page_title': "Nouveau bon d'entrée",
        'next_num': next_num,
        'depots': Depot.objects.all(),
        'fournisseurs': Fournisseur.objects.all(),
        'annees': AnneeExercice.objects.all(),
        'types_operation': TypeOperation.objects.all(),
        'annee_courante': annee_courante,
        'today': date.today(),
    }
    return render(request, 'bons/entree_form.html', context)


@login_required
def bon_entree_update(request, pk):
    bon = get_object_or_404(BonEntree, pk=pk)
    if request.method == 'POST':
        try:
            bon.date_creation = request.POST.get('date_creation') or bon.date_creation
            bon.annee_exercice_id = request.POST.get('annee_exercice') or None
            bon.references_pieces = request.POST.get('references_pieces', '')
            bon.type_entree_id = request.POST.get('type_entree') or None
            bon.depot_id = request.POST.get('depot') or None
            bon.fournisseur_id = request.POST.get('fournisseur') or None
            bon.num_bon_engagement = int(request.POST.get('num_bon_engagement') or 0)
            bon.num_bon_commande = int(request.POST.get('num_bon_commande') or 0)
            bon.num_pvc = request.POST.get('num_pvc', '')
            bon.chapitre = request.POST.get('chapitre', '')
            bon.save()
            messages.success(request, "En-tête du bon mis à jour.")
        except Exception as e:
            messages.error(request, f"Erreur : {e}")
        return redirect('matieres:bon_entree_update', pk=pk)

    details = bon.details.select_related('produit', 'unite').all()
    context = {
        'page_title': f"Bon d'entrée BE-{bon.num_bon:04d}",
        'bon': bon,
        'details': details,
        'depots': Depot.objects.all(),
        'fournisseurs': Fournisseur.objects.all(),
        'annees': AnneeExercice.objects.all(),
        'types_operation': TypeOperation.objects.all(),
        'unites': Unite.objects.all(),
        'today': date.today(),
    }
    return render(request, 'bons/entree_update.html', context)


# ─────────────────────────── MARCHÉS / EXPRESSIONS DE BESOINS ───────────────────────────


@login_required
def marches_list(request):
    marches = Marche.objects.select_related('fournisseur', 'bon_entree').order_by('-date_creation')
    context = {'page_title': 'Marchés', 'marches': marches}
    return render(request, 'marches/list.html', context)


@login_required
def marche_create(request):
    if request.method == 'POST':
        try:
            num_marche = request.POST.get('num_marche')
            date_creation = request.POST.get('date_creation')
            fournisseur_id = request.POST.get('fournisseur') or None
            num_bon_engagement = int(request.POST.get('num_bon_engagement') or 0)
            reference_marche = request.POST.get('reference_marche', '')
            chapitre = request.POST.get('chapitre', '')
            marche = Marche.objects.create(
                num_marche=num_marche,
                date_creation=date_creation,
                fournisseur_id=fournisseur_id,
                num_bon_engagement=num_bon_engagement,
                reference_marche=reference_marche,
                chapitre=chapitre,
            )
            messages.success(request, f"Marché {marche.num_marche} créé.")
            return redirect('matieres:marches_list')
        except Exception as e:
            messages.error(request, f"Erreur: {e}")

    context = {'page_title': 'Nouveau marché', 'fournisseurs': Fournisseur.objects.all(), 'today': date.today()}
    return render(request, 'marches/form.html', context)


@login_required
def marche_detail(request, pk):
    marche = get_object_or_404(Marche, pk=pk)
    context = {'page_title': f"Marché {marche.num_marche}", 'marche': marche, 'details': marche.details.all()}
    return render(request, 'marches/detail.html', context)


@login_required
def expressions_list(request):
    exprs = ExpressionBesoin.objects.select_related('demandeur_service', 'demandeur_bureau').order_by('-date_creation')
    context = {'page_title': 'Expressions de besoins', 'expressions': exprs}
    return render(request, 'expressions/list.html', context)


@login_required
def expression_create(request):
    if request.method == 'POST':
        try:
            reference = request.POST.get('reference', '')
            date_creation = request.POST.get('date_creation') or date.today().isoformat()
            service_id = request.POST.get('service') or None
            bureau_id = request.POST.get('bureau') or None
            expr = ExpressionBesoin.objects.create(
                reference=reference,
                date_creation=date_creation,
                demandeur_service_id=service_id,
                demandeur_bureau_id=bureau_id,
            )
            messages.success(request, f"Expression de besoin créée (#{expr.id}).")
            return redirect('matieres:expressions_list')
        except Exception as e:
            messages.error(request, f"Erreur: {e}")

    context = {'page_title': 'Nouvelle expression de besoin', 'services': Service.objects.all(), 'bureaux': Bureau.objects.all(), 'today': date.today()}
    return render(request, 'expressions/form.html', context)


@login_required
def expression_detail(request, pk):
    expr = get_object_or_404(ExpressionBesoin, pk=pk)
    context = {'page_title': f'Expression #{expr.id}', 'expression': expr, 'details': expr.details.all()}
    return render(request, 'expressions/detail.html', context)


@login_required
def expression_transform(request, pk):
    expr = get_object_or_404(ExpressionBesoin, pk=pk)
    if request.method == 'POST':
        try:
            bsd = expr.transform_to_bsd()
            messages.success(request, f"Expression transformée en Bon de sortie définitive N°{bsd.num_bon:04d}.")
        except Exception as e:
            messages.error(request, f"Erreur lors de la transformation : {e}")
    return redirect('matieres:expressions_list')


@login_required
def marche_update(request, pk):
    marche = get_object_or_404(Marche, pk=pk)
    if request.method == 'POST':
        marche.date_creation = request.POST.get('date_creation') or marche.date_creation
        marche.date_debut = request.POST.get('date_debut') or None
        marche.date_fin = request.POST.get('date_fin') or None
        marche.fournisseur_id = request.POST.get('fournisseur') or None
        marche.num_bon_engagement = int(request.POST.get('num_bon_engagement') or marche.num_bon_engagement)
        marche.reference_marche = request.POST.get('reference_marche', marche.reference_marche)
        marche.chapitre = request.POST.get('chapitre', marche.chapitre)
        marche.save()
        messages.success(request, "En-tête du marché mis à jour.")
        return redirect('matieres:marche_update', pk=pk)

    context = {
        'page_title': f'Marché {marche.num_marche}',
        'marche': marche,
        'fournisseurs': Fournisseur.objects.all(),
        'unites': Unite.objects.all(),
        'today': date.today(),
    }
    return render(request, 'marches/update.html', context)



@login_required
def expression_update(request, pk):
    expr = get_object_or_404(ExpressionBesoin, pk=pk)
    if request.method == 'POST':
        expr.reference = request.POST.get('reference', expr.reference)
        expr.date_creation = request.POST.get('date_creation') or expr.date_creation
        expr.demandeur_service_id = request.POST.get('service') or None
        expr.demandeur_bureau_id = request.POST.get('bureau') or None
        expr.recu_par_comptable = bool(request.POST.get('recu_par_comptable'))
        if expr.recu_par_comptable and not expr.date_reception_comptable:
            expr.date_reception_comptable = date.today()
        expr.save()
        messages.success(request, "Expression mise à jour.")
        return redirect('matieres:expression_detail', pk=pk)

    context = {'page_title': f'Expression #{expr.id}', 'expression': expr, 'services': Service.objects.all(), 'bureaux': Bureau.objects.all(), 'today': date.today()}
    return render(request, 'expressions/update.html', context)


@login_required
def htmx_marche_add_detail(request, pk):
    marche = get_object_or_404(Marche, pk=pk)
    if request.method == 'POST':
        designation = request.POST.get('designation', '').strip()
        if designation:
            produit_id = request.POST.get('produit_id') or None
            nomenclature = request.POST.get('nomenclature', '').strip()
            specification = request.POST.get('specification', '').strip()
            qte = int(request.POST.get('qte') or 0)
            unite_id = request.POST.get('unite_id') or None
            prix_ht = Decimal(str(request.POST.get('prix_ht') or '0').replace(',', '.'))
            prix_ttc = Decimal(str(request.POST.get('prix_ttc') or '0').replace(',', '.'))
            montant_ttc = qte * prix_ttc
            DetailMarche.objects.create(
                marche=marche,
                produit_id=produit_id,
                designation=designation,
                nomenclature=nomenclature,
                specification=specification,
                qte=qte,
                unite_id=unite_id,
                prix_ht=prix_ht,
                prix_ttc=prix_ttc,
                montant_ttc=montant_ttc,
            )
    details = marche.details.select_related('produit', 'unite').all()
    return render(request, 'partials/marche_detail_rows.html', {'details': details, 'marche': marche})


@login_required
def htmx_marche_delete_detail(request, detail_pk):
    detail = get_object_or_404(DetailMarche, pk=detail_pk)
    marche = detail.marche
    detail.delete()
    details = marche.details.select_related('produit', 'unite').all()
    return render(request, 'partials/marche_detail_rows.html', {'details': details, 'marche': marche})


@login_required
def htmx_expression_add_detail(request, pk):
    expr = get_object_or_404(ExpressionBesoin, pk=pk)
    if request.method == 'POST':
        designation = request.POST.get('designation', '').strip()
        if designation:
            produit_id = request.POST.get('produit_id') or None
            nomenclature = request.POST.get('nomenclature', '').strip()
            specification = request.POST.get('specification', '').strip()
            qte = int(request.POST.get('qte') or 0)
            unite_id = request.POST.get('unite_id') or None
            prix_ht = Decimal(str(request.POST.get('prix_ht') or '0').replace(',', '.'))
            prix_ttc = Decimal(str(request.POST.get('prix_ttc') or '0').replace(',', '.'))
            montant_ttc = qte * prix_ttc
            DetailExpressionBesoin.objects.create(
                expression=expr,
                produit_id=produit_id,
                designation=designation,
                nomenclature=nomenclature,
                specification=specification,
                qte=qte,
                unite_id=unite_id,
                prix_ht=prix_ht,
                prix_ttc=prix_ttc,
                montant_ttc=montant_ttc,
            )
    details = expr.details.select_related('produit', 'unite').all()
    return render(request, 'partials/expression_detail_rows.html', {'details': details, 'expression': expr})


@login_required
def htmx_expression_delete_detail(request, detail_pk):
    detail = get_object_or_404(DetailExpressionBesoin, pk=detail_pk)
    expr = detail.expression
    detail.delete()
    details = expr.details.select_related('produit', 'unite').all()
    return render(request, 'partials/expression_detail_rows.html', {'details': details, 'expression': expr})



@login_required
def bon_entree_valider(request, pk):
    bon = get_object_or_404(BonEntree, pk=pk)
    if request.method == 'POST' and not bon.valide:
        if not bon.details.exists():
            messages.error(request, "Impossible de valider : aucun article dans le bon.")
            return redirect('matieres:bon_entree_update', pk=pk)
        bon.valide = True
        bon.save()
        annee_val = bon.annee_exercice.annee if bon.annee_exercice else None
        for detail in bon.details.select_related('produit', 'unite').all():
            if detail.produit:
                stock_avant = detail.produit.stock_global
                detail.produit.stock_global += detail.qte
                detail.produit.entree += detail.qte
                if detail.unite_id and detail.produit.unite_id != detail.unite_id:
                    detail.produit.unite = detail.unite
                detail.produit.save()
                if bon.depot:
                    sd, _ = StockDepot.objects.get_or_create(
                        produit=detail.produit, depot=bon.depot,
                        defaults={'nomenclature': detail.nomenclature, 'designation': detail.designation}
                    )
                    sd.qte_stock += detail.qte
                    sd.save()
                Journal.objects.create(
                    date_creation=bon.date_creation,
                    num_bon=bon.num_bon,
                    type_entree=bon.type_entree.libelle if bon.type_entree else 'Bon Entrée',
                    groupe=detail.produit.groupe if detail.produit else '',
                    designation=detail.designation,
                    nomenclature=detail.nomenclature,
                    specification=detail.specification,
                    qte=detail.qte,
                    unite=str(detail.unite) if detail.unite else '',
                    prix_ht=detail.prix_ht,
                    prix_ttc=detail.prix_ttc,
                    montant_ttc=detail.montant_ttc,
                    annee_exercice=annee_val,
                    depot=str(bon.depot) if bon.depot else '',
                    observation=detail.observation,
                    existant=stock_avant,
                    entree_periode=detail.qte,
                    total_entree=detail.produit.entree,
                    sortie_periode=0,
                    existant_fin_periode=detail.produit.stock_global,
                    montant_existant=detail.produit.stock_global * detail.prix_ht,
                )
        messages.success(request, f"Bon BE-{bon.num_bon:04d} validé. Stock mis à jour.")
    return redirect('matieres:bon_entree_update', pk=pk)


@login_required
def bon_entree_devalider(request, pk):
    bon = get_object_or_404(BonEntree, pk=pk)
    if request.method == 'POST' and bon.valide:
        # Garde-fou : si les matières de ce bon ont déjà été consommées en aval (affectation,
        # sortie provisoire ou définitive), dévalider romprait la comptabilité des matières —
        # on refuse tant que le stock encore libre ne suffit pas à annuler cette entrée.
        erreurs = []
        for detail in bon.details.select_related('produit').all():
            if detail.produit:
                p = detail.produit
                stock_apres = p.stock_global - detail.qte
                deja_engage = p.qte_affectation + p.qte_sp + p.qte_sd
                if stock_apres < deja_engage:
                    erreurs.append(
                        f"{detail.nomenclature} ({detail.designation}) — {p.qte_affectation + p.qte_sp + p.qte_sd} "
                        f"unité(s) déjà affectée(s)/sortie(s), impossible de retirer {detail.qte} du stock."
                    )
        if erreurs:
            messages.error(
                request,
                "Dévalidation impossible : des matières de ce bon ont déjà été consommées (affectation ou sortie) — "
                + " | ".join(erreurs)
            )
            return redirect('matieres:bon_entree_update', pk=pk)

        bon.valide = False
        bon.save()
        for detail in bon.details.select_related('produit').all():
            if detail.produit:
                detail.produit.stock_global = max(0, detail.produit.stock_global - detail.qte)
                detail.produit.entree = max(0, detail.produit.entree - detail.qte)
                detail.produit.save()
                if bon.depot:
                    try:
                        sd = StockDepot.objects.get(produit=detail.produit, depot=bon.depot)
                        sd.qte_stock = max(0, sd.qte_stock - detail.qte)
                        sd.save()
                    except StockDepot.DoesNotExist:
                        pass
        Journal.objects.filter(num_bon=bon.num_bon,
                               type_entree=bon.type_entree.libelle if bon.type_entree else 'Bon Entrée').delete()
        messages.warning(request, f"Bon BE-{bon.num_bon:04d} dévalidé. Mouvements de stock annulés.")
    return redirect('matieres:bon_entree_update', pk=pk)


@login_required
def htmx_be_add_detail(request, pk):
    bon = get_object_or_404(BonEntree, pk=pk)
    if request.method == 'POST' and not bon.valide:
        designation = request.POST.get('designation', '').strip()
        if designation:
            def _dec(val, default='0'):
                try:
                    return Decimal(str(val).replace(',', '.').strip() or default)
                except Exception:
                    return Decimal(default)

            produit_id  = request.POST.get('produit_id') or None
            nomenclature = request.POST.get('nomenclature', '').strip()
            specification = request.POST.get('specification', '').strip()
            qte          = _dec(request.POST.get('qte', '0'))
            unite_id     = request.POST.get('unite_id') or None
            prix_ht      = _dec(request.POST.get('prix_ht', '0'))
            prix_ttc     = _dec(request.POST.get('prix_ttc', '0'))
            observation  = request.POST.get('observation', '')
            montant_ttc  = qte * prix_ttc

            if unite_id:
                try:
                    from .models import Unite
                    Unite.objects.get(pk=unite_id)
                except Exception:
                    unite_id = None

            DetailBonEntree.objects.create(
                bon_entree=bon,
                produit_id=produit_id,
                designation=designation,
                nomenclature=nomenclature,
                specification=specification,
                qte=qte,
                unite_id=unite_id,
                prix_ht=prix_ht,
                prix_ttc=prix_ttc,
                montant_ttc=montant_ttc,
                observation=observation,
            )

    details = bon.details.select_related('produit', 'unite').all()
    return render(request, 'partials/be_detail_rows.html', {'details': details, 'bon': bon})


@login_required
def htmx_be_delete_detail(request, detail_pk):
    detail = get_object_or_404(DetailBonEntree, pk=detail_pk)
    bon = detail.bon_entree
    if not bon.valide:
        detail.delete()
    details = bon.details.select_related('produit', 'unite').all()
    return render(request, 'partials/be_detail_rows.html', {'details': details, 'bon': bon})


@login_required
def htmx_be_produit_search(request):
    q = request.GET.get('q', '').strip()
    produits = []
    if len(q) >= 1:
        produits = Produit.objects.filter(
            Q(designation__icontains=q) | Q(nomenclature__icontains=q)
        ).select_related('unite').order_by('nomenclature')[:30]
    return render(request, 'partials/be_produit_search.html', {'produits': produits})


@login_required
def htmx_be_modal_produits(request):
    q = request.GET.get('q', '').strip()
    produits = Produit.objects.select_related('unite').order_by('nomenclature')
    if q:
        produits = produits.filter(
            Q(designation__icontains=q) | Q(nomenclature__icontains=q)
        )
    total_all = Produit.objects.count()
    produits = list(produits[:300])
    return render(request, 'partials/be_produit_modal_content.html', {
        'produits': produits,
        'q': q,
        'total_all': total_all,
    })


@login_required
def htmx_be_produit_info(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    return JsonResponse({
        'id': produit.pk,
        'designation': produit.designation,
        'nomenclature': produit.nomenclature,
        'specification': produit.specification,
        'unite_id': produit.unite_id or '',
        'unite_libelle': produit.unite.libelle if produit.unite else '',
        'stock_disponible': produit.stock_disponible,
    })


# ─────────────────────────── BONS D'AFFECTATION ───────────────────────────

@login_required
def bons_affectation_list(request):
    bons = BonAffectation.objects.select_related('depot', 'service', 'bureau').order_by('-date_affectation', '-num_bon')
    context = {
        'page_title': "Bons d'affectation",
        'bons': bons,
        'nb_non_valides': bons.filter(valide=False).count(),
    }
    return render(request, 'bons/affectation_list.html', context)


@login_required
def bon_affectation_detail(request, pk):
    bon = get_object_or_404(BonAffectation, pk=pk)
    context = {
        'page_title': f"Bon d'affectation N°{bon.num_bon:04d}",
        'bon': bon,
        'details': bon.details.select_related('produit', 'unite').all(),
    }
    return render(request, 'bons/affectation_detail.html', context)


@login_required
def bon_affectation_create(request):
    services = Service.objects.filter(actif=True).order_by('code')
    depots = Depot.objects.all().order_by('code')
    annees = AnneeExercice.objects.all().order_by('-annee')
    if request.method == 'POST':
        num_bon = request.POST.get('num_bon', '').strip()
        date_aff = request.POST.get('date_affectation') or None
        annee = request.POST.get('annee_creation') or None
        service_id = request.POST.get('service_id') or None
        bureau_id = request.POST.get('bureau_id') or None
        depot_id = request.POST.get('depot_id') or None
        if num_bon:
            bon = BonAffectation.objects.create(
                num_bon=int(num_bon),
                date_affectation=date_aff,
                annee_creation=int(annee) if annee else None,
                service_id=service_id,
                bureau_id=bureau_id,
                depot_id=depot_id,
            )
            return redirect('matieres:bon_affectation_update', pk=bon.pk)
    context = {
        'page_title': "Nouveau bon d'affectation",
        'services': services,
        'depots': depots,
        'annees': annees,
        'today': date.today(),
        'next_num': (BonAffectation.objects.order_by('-num_bon').values_list('num_bon', flat=True).first() or 0) + 1,
    }
    return render(request, 'bons/affectation_form.html', context)


def _ba_details_with_depot(bon):
    """Retourne les détails du BA annotés avec le dépôt principal du produit."""
    details = list(bon.details.select_related('produit', 'unite').all())
    for d in details:
        if d.produit:
            sd = StockDepot.objects.filter(produit=d.produit).order_by('-qte_stock').first()
            d.depot_nom   = str(sd.depot) if (sd and sd.depot) else '—'
            d.depot_stock = sd.qte_stock if sd else 0
        else:
            d.depot_nom   = '—'
            d.depot_stock = 0
    return details


@login_required
def bon_affectation_update(request, pk):
    bon = get_object_or_404(BonAffectation, pk=pk)
    services = Service.objects.filter(actif=True).order_by('code')
    depots = Depot.objects.all().order_by('code')
    unites = Unite.objects.all().order_by('libelle')
    if request.method == 'POST' and not bon.valide:
        bon.date_affectation = request.POST.get('date_affectation') or bon.date_affectation
        bon.annee_creation = request.POST.get('annee_creation') or bon.annee_creation
        bon.service_id = request.POST.get('service_id') or bon.service_id
        bon.bureau_id = request.POST.get('bureau_id') or bon.bureau_id
        bon.depot_id = request.POST.get('depot_id') or bon.depot_id
        bon.observation = request.POST.get('observation', bon.observation)
        bon.save()
    details = _ba_details_with_depot(bon)
    bureaux = Bureau.objects.filter(service_id=bon.service_id, actif=True).order_by('code') if bon.service_id else Bureau.objects.none()
    context = {
        'page_title': f"Bon d'affectation BA-{bon.num_bon:04d}",
        'bon': bon,
        'details': details,
        'services': services,
        'bureaux': bureaux,
        'depots': depots,
        'unites': unites,
    }
    return render(request, 'bons/affectation_update.html', context)


@login_required
def bon_affectation_valider(request, pk):
    if request.method != 'POST':
        return redirect('matieres:bon_affectation_update', pk=pk)
    bon = get_object_or_404(BonAffectation, pk=pk)
    if bon.valide:
        messages.warning(request, "Ce bon est déjà validé.")
        return redirect('matieres:bon_affectation_update', pk=pk)

    # Garde-fou : vérifier le stock disponible pour chaque ligne
    erreurs = []
    for d in bon.details.select_related('produit').all():
        if d.produit:
            if d.produit.groupe != '1':
                erreurs.append(f"{d.nomenclature} : matière non Groupe 1.")
            elif d.produit.stock_disponible < d.qte:
                erreurs.append(
                    f"{d.nomenclature} — stock dispo {d.produit.stock_disponible} < qté demandée {d.qte}."
                )
    if erreurs:
        messages.error(request, "Validation impossible : " + " | ".join(erreurs))
        return redirect('matieres:bon_affectation_update', pk=pk)

    for d in bon.details.select_related('produit', 'unite').all():
        qte_avant      = 0
        depot_nom      = ''
        stock_apres    = 0

        if d.produit:
            # 1. Incrémenter qte_affectation (stock_global inchangé — produit dans l'entreprise)
            qte_avant = d.produit.qte_affectation
            d.produit.qte_affectation += int(d.qte)
            d.produit.save(update_fields=['qte_affectation'])

            # 2. Décrémenter le stock PARTIEL au dépôt source
            #    (le dépôt sélectionné sur le bon, sinon celui avec le plus de stock)
            if bon.depot:
                sd = StockDepot.objects.filter(produit=d.produit, depot=bon.depot).first()
            else:
                sd = StockDepot.objects.filter(produit=d.produit).order_by('-qte_stock').first()

            if sd:
                sd.qte_stock = max(0, sd.qte_stock - int(d.qte))
                sd.save(update_fields=['qte_stock'])
                depot_nom   = str(sd.depot) if sd.depot else ''
                stock_apres = sd.qte_stock

        j = Journal.objects.create(
            date_creation=bon.date_affectation,
            num_bon=bon.num_bon,
            type_entree='Affectation',
            groupe=d.produit.groupe if d.produit else '1',
            designation=d.designation,
            nomenclature=d.nomenclature,
            specification=d.specification,
            qte=int(d.qte),
            unite=str(d.unite) if d.unite else '',
            prix_ht=d.prix_ht,
            prix_ttc=d.prix_ttc,
            montant_ttc=d.montant_ttc,
            service=str(bon.service) if bon.service else '',
            bureau=str(bon.bureau) if bon.bureau else '',
            annee_exercice=bon.annee_creation,
            depot=depot_nom,
            date_affectation=bon.date_affectation,
            qte_affectation=d.produit.qte_affectation if d.produit else 0,
            qte_stock_partielle=str(stock_apres),
            existant=qte_avant,
            sortie_periode=int(d.qte),
            existant_fin_periode=d.produit.qte_affectation if d.produit else 0,
            montant_existant=(d.produit.qte_affectation * d.prix_ht) if d.produit else 0,
        )
        # Lier le détail à son entrée journal (IDJournal — alignement WinDev)
        d.journal = j
        d.save(update_fields=['journal'])

    bon.valide = True
    bon.save(update_fields=['valide'])
    messages.success(request, f"Bon d'affectation BA-{bon.num_bon:04d} validé avec succès.")
    return redirect('matieres:bon_affectation_update', pk=pk)


@login_required
def bon_affectation_devalider(request, pk):
    if request.method != 'POST':
        return redirect('matieres:bon_affectation_update', pk=pk)
    bon = get_object_or_404(BonAffectation, pk=pk)
    if not bon.valide:
        messages.warning(request, "Ce bon n'est pas validé.")
        return redirect('matieres:bon_affectation_update', pk=pk)

    for d in bon.details.select_related('produit').all():
        if d.produit:
            # Restaurer qte_affectation
            d.produit.qte_affectation = max(0, d.produit.qte_affectation - int(d.qte))
            d.produit.save(update_fields=['qte_affectation'])
            # Restaurer le StockDepot décrémenté lors de la validation
            if bon.depot:
                sd = StockDepot.objects.filter(produit=d.produit, depot=bon.depot).first()
            else:
                sd = StockDepot.objects.filter(produit=d.produit).order_by('qte_stock').first()
            if sd:
                sd.qte_stock += int(d.qte)
                sd.save(update_fields=['qte_stock'])

    Journal.objects.filter(num_bon=bon.num_bon, type_entree='Affectation').delete()
    bon.valide = False
    bon.save(update_fields=['valide'])
    messages.success(request, f"Bon d'affectation BA-{bon.num_bon:04d} dévalidé.")
    return redirect('matieres:bon_affectation_update', pk=pk)


@login_required
def bon_affectation_etat(request, pk):
    """État officiel imprimable — Modèle N°7, Bordereau d'Affectation."""
    bon = get_object_or_404(BonAffectation, pk=pk)
    details = list(bon.details.select_related('produit', 'unite').all())
    context = {
        'page_title': f"État — Bordereau d'affectation BA-{bon.num_bon:04d}",
        'bon': bon,
        'societe': SocieteGCS.objects.first(),
        'details': details,
        'total_qte': sum(d.qte for d in details),
        'total_ttc': bon.total_ttc(),
    }
    return render(request, 'bons/affectation_etat.html', context)


# ─── HTMX — Bon d'Affectation ───

@login_required
def htmx_ba_add_detail(request, pk):
    bon = get_object_or_404(BonAffectation, pk=pk)
    if request.method == 'POST' and not bon.valide:
        designation = request.POST.get('designation', '').strip()
        if designation:
            def _dec(v, d='0'):
                try:
                    return Decimal(str(v).replace(',', '.').strip() or d)
                except Exception:
                    return Decimal(d)

            produit_id   = request.POST.get('produit_id') or None
            nomenclature = request.POST.get('nomenclature', '').strip()
            specification = request.POST.get('specification', '').strip()
            code_immatriculation = request.POST.get('code_immatriculation', '').strip()
            qte          = _dec(request.POST.get('qte', '0'))
            unite_id     = request.POST.get('unite_id') or None
            prix_ht      = _dec(request.POST.get('prix_ht', '0'))
            prix_ttc     = _dec(request.POST.get('prix_ttc', '0'))
            observation  = request.POST.get('observation', '')

            DetailBonAffectation.objects.create(
                bon_affectation=bon,
                produit_id=produit_id,
                designation=designation,
                nomenclature=nomenclature,
                specification=specification,
                code_immatriculation=code_immatriculation,
                qte=qte,
                unite_id=unite_id,
                prix_ht=prix_ht,
                prix_ttc=prix_ttc,
                montant_ttc=qte * prix_ttc,
                observation=observation,
            )

    details = _ba_details_with_depot(bon)
    return render(request, 'partials/ba_detail_rows.html', {'details': details, 'bon': bon})


@login_required
def htmx_ba_delete_detail(request, detail_pk):
    detail = get_object_or_404(DetailBonAffectation, pk=detail_pk)
    bon = detail.bon_affectation
    if not bon.valide:
        detail.delete()
    details = _ba_details_with_depot(bon)
    return render(request, 'partials/ba_detail_rows.html', {'details': details, 'bon': bon})


def _annoter_produits_ba(produits):
    """Annote chaque produit avec : stock dépôt max + dernier prix d'entrée."""
    for p in produits:
        sd = StockDepot.objects.filter(produit=p).order_by('-qte_stock').first()
        p.stock_depot_max = sd.qte_stock if sd else 0
        p.depot_max_nom   = str(sd.depot) if (sd and sd.depot) else '—'
        # Dernier prix connu depuis les Bons d'Entrée
        last_detail = DetailBonEntree.objects.filter(
            produit=p
        ).order_by('-bon_entree__date_creation', '-pk').first()
        p.auto_prix_ht  = last_detail.prix_ht  if last_detail else 0
        p.auto_prix_ttc = last_detail.prix_ttc if last_detail else 0
    return produits


@login_required
def htmx_ba_produit_search(request):
    q = request.GET.get('q', '').strip()
    produits = []
    if len(q) >= 1:
        produits = list(Produit.objects.filter(
            Q(designation__icontains=q) | Q(nomenclature__icontains=q),
            nomenclature__startswith='1',
            stock_global__gt=0,
        ).select_related('unite').order_by('nomenclature')[:30])
        _annoter_produits_ba(produits)
    return render(request, 'partials/ba_produit_search.html', {'produits': produits, 'q': q})


@login_required
def htmx_ba_modal_produits(request):
    q = request.GET.get('q', '').strip()
    base_qs = Produit.objects.filter(
        nomenclature__startswith='1',
        stock_global__gt=0,
    ).select_related('unite').order_by('nomenclature')
    total_all = base_qs.count()
    if q:
        base_qs = base_qs.filter(Q(designation__icontains=q) | Q(nomenclature__icontains=q))
    produits = list(base_qs[:300])
    _annoter_produits_ba(produits)
    return render(request, 'partials/ba_produit_modal_content.html', {
        'produits': produits, 'q': q, 'total_all': total_all
    })


# ─────────────────────────── BONS RETOUR AFFECTATION ───────────────────────────

@login_required
def bons_retour_affectation_list(request):
    bons = BonRetourAffectation.objects.select_related('depot', 'service', 'bureau').order_by('-date_creation', '-num_bon')
    context = {
        'page_title': "Bons de retour d'affectation",
        'bons': bons,
        'nb_non_valides': bons.filter(valide=False).count(),
    }
    return render(request, 'bons/retour_affectation_list.html', context)


@login_required
def bon_retour_affectation_create(request):
    services = Service.objects.filter(actif=True).order_by('code')
    depots = Depot.objects.all().order_by('code')
    annees = AnneeExercice.objects.all().order_by('-annee')
    if request.method == 'POST':
        num_bon   = request.POST.get('num_bon', '').strip()
        date_ret  = request.POST.get('date_retour') or None
        date_crea = request.POST.get('date_creation') or None
        service_id = request.POST.get('service_id') or None
        bureau_id  = request.POST.get('bureau_id') or None
        observation = request.POST.get('observation', '')
        if num_bon:
            bon = BonRetourAffectation.objects.create(
                num_bon=int(num_bon),
                date_retour=date_ret,
                date_creation=date_crea,
                service_id=service_id,
                bureau_id=bureau_id,
                observation=observation,
            )
            return redirect('matieres:bon_retour_affectation_update', pk=bon.pk)
    next_num = (BonRetourAffectation.objects.order_by('-num_bon').values_list('num_bon', flat=True).first() or 0) + 1
    context = {
        'page_title': "Nouveau bon de retour d'affectation",
        'depots': depots, 'services': services,
        'annees': annees, 'today': date.today(), 'next_num': next_num,
    }
    return render(request, 'bons/retour_affectation_form.html', context)


@login_required
def bon_retour_affectation_update(request, pk):
    bon = get_object_or_404(BonRetourAffectation, pk=pk)
    services = Service.objects.filter(actif=True).order_by('code')
    unites = Unite.objects.all().order_by('libelle')
    if request.method == 'POST' and not bon.valide:
        bon.date_retour     = request.POST.get('date_retour') or bon.date_retour
        bon.date_creation   = request.POST.get('date_creation') or bon.date_creation
        bon.service_id      = request.POST.get('service_id') or bon.service_id
        bon.bureau_id       = request.POST.get('bureau_id') or bon.bureau_id
        bon.observation     = request.POST.get('observation', bon.observation)
        bon.save()
    details = bon.details.select_related('produit', 'unite').all()
    bureaux = Bureau.objects.filter(service_id=bon.service_id, actif=True).order_by('code') if bon.service_id else Bureau.objects.none()
    context = {
        'page_title': f"BRA-{bon.num_bon:04d}",
        'bon': bon, 'details': details,
        'services': services, 'bureaux': bureaux, 'unites': unites,
    }
    return render(request, 'bons/retour_affectation_update.html', context)


@login_required
def bon_retour_affectation_valider(request, pk):
    if request.method != 'POST':
        return redirect('matieres:bon_retour_affectation_update', pk=pk)
    bon = get_object_or_404(BonRetourAffectation, pk=pk)
    if bon.valide:
        messages.warning(request, "Ce bon est déjà validé.")
        return redirect('matieres:bon_retour_affectation_update', pk=pk)

    if not bon.bureau:
        messages.error(request, "Validation impossible : sélectionnez le service et le bureau du bon.")
        return redirect('matieres:bon_retour_affectation_update', pk=pk)

    erreurs = []
    for d in bon.details.select_related('produit').all():
        if d.produit:
            if d.produit.groupe != '1':
                erreurs.append(f"{d.nomenclature} : matière non Groupe 1.")
            else:
                dispo = _qte_affectee_disponible(d.produit, bon.bureau)
                if dispo < int(d.qte):
                    erreurs.append(
                        f"{d.nomenclature} — qté affectée à {bon.bureau} : {dispo} < retour demandé {d.qte}."
                    )
    if erreurs:
        messages.error(request, "Validation impossible : " + " | ".join(erreurs))
        return redirect('matieres:bon_retour_affectation_update', pk=pk)

    for d in bon.details.select_related('produit', 'unite').all():
        if d.produit:
            d.produit.qte_affectation = max(0, d.produit.qte_affectation - int(d.qte))
            d.produit.save(update_fields=['qte_affectation'])


        Journal.objects.create(
            date_creation=bon.date_retour or bon.date_creation,
            num_bon=bon.num_bon,
            type_entree='Retour Affectation',
            groupe=d.produit.groupe if d.produit else '1',
            designation=d.designation,
            nomenclature=d.nomenclature,
            specification=d.specification,
            qte=int(d.qte),
            unite=str(d.unite) if d.unite else '',
            prix_ht=d.prix_ht,
            prix_ttc=d.prix_ttc,
            montant_ttc=d.montant_ttc,
            service=str(bon.service) if bon.service else '',
            bureau=str(bon.bureau) if bon.bureau else '',
            date_retour_affectation=bon.date_retour,
            qte_rba=int(d.qte),
            existant=d.produit.qte_affectation if d.produit else 0,
            entree_periode=int(d.qte),
            existant_fin_periode=d.produit.qte_affectation if d.produit else 0,
            montant_existant=(d.produit.qte_affectation * d.prix_ht) if d.produit else 0,
        )

    bon.valide = True
    bon.save(update_fields=['valide'])
    messages.success(request, f"BRA-{bon.num_bon:04d} validé avec succès.")
    return redirect('matieres:bon_retour_affectation_update', pk=pk)


@login_required
def bon_retour_affectation_devalider(request, pk):
    if request.method != 'POST':
        return redirect('matieres:bon_retour_affectation_update', pk=pk)
    bon = get_object_or_404(BonRetourAffectation, pk=pk)
    if not bon.valide:
        messages.warning(request, "Ce bon n'est pas validé.")
        return redirect('matieres:bon_retour_affectation_update', pk=pk)

    for d in bon.details.select_related('produit').all():
        if d.produit:
            d.produit.qte_affectation += int(d.qte)
            d.produit.save(update_fields=['qte_affectation'])

            if bon.depot_id:
                sd, _ = StockDepot.objects.get_or_create(
                    produit=d.produit, depot_id=bon.depot_id,
                    defaults={'nomenclature': d.nomenclature, 'designation': d.designation, 'qte_stock': 0}
                )
                sd.qte_stock += int(d.qte)
                sd.save(update_fields=['qte_stock'])

            if bon.depot_destination_id:
                try:
                    sd = StockDepot.objects.get(produit=d.produit, depot_id=bon.depot_destination_id)
                    sd.qte_stock = max(0, sd.qte_stock - int(d.qte))
                    sd.save(update_fields=['qte_stock'])
                except StockDepot.DoesNotExist:
                    pass

    Journal.objects.filter(num_bon=bon.num_bon, type_entree='Retour Affectation').delete()
    bon.valide = False
    bon.save(update_fields=['valide'])
    messages.success(request, f"BRA-{bon.num_bon:04d} dévalidé.")
    return redirect('matieres:bon_retour_affectation_update', pk=pk)


@login_required
def bon_retour_affectation_etat(request, pk):
    """État officiel imprimable — Modèle N°7 (Bordereau d'affectation), sens retour."""
    bon = get_object_or_404(BonRetourAffectation, pk=pk)
    details = list(bon.details.select_related('produit', 'unite').all())
    context = {
        'page_title': f"État — Bordereau de retour d'affectation BRA-{bon.num_bon:04d}",
        'bon': bon,
        'societe': SocieteGCS.objects.first(),
        'details': details,
        'total_qte': sum(d.qte for d in details),
        'total_ttc': bon.total_ttc(),
    }
    return render(request, 'bons/retour_affectation_etat.html', context)


# ─── HTMX — Bon de Retour d'Affectation ───

@login_required
def htmx_bra_add_detail(request, pk):
    bon = get_object_or_404(BonRetourAffectation, pk=pk)
    if request.method == 'POST' and not bon.valide:
        designation = request.POST.get('designation', '').strip()
        if designation:
            def _dec(v, d='0'):
                try:
                    return Decimal(str(v).replace(',', '.').strip() or d)
                except Exception:
                    return Decimal(d)
            qte     = _dec(request.POST.get('qte', '0'))
            prix_ttc = _dec(request.POST.get('prix_ttc', '0'))
            DetailBonRetourAffectation.objects.create(
                bon_retour=bon,
                produit_id=request.POST.get('produit_id') or None,
                designation=designation,
                nomenclature=request.POST.get('nomenclature', '').strip(),
                specification=request.POST.get('specification', '').strip(),
                qte=qte,
                unite_id=request.POST.get('unite_id') or None,
                prix_ht=_dec(request.POST.get('prix_ht', '0')),
                prix_ttc=prix_ttc,
                montant_ttc=qte * prix_ttc,
                observation=request.POST.get('observation', ''),
            )
    details = bon.details.select_related('produit', 'unite').all()
    return render(request, 'partials/bra_detail_rows.html', {'details': details, 'bon': bon})


@login_required
def htmx_bra_delete_detail(request, detail_pk):
    detail = get_object_or_404(DetailBonRetourAffectation, pk=detail_pk)
    bon = detail.bon_retour
    if not bon.valide:
        detail.delete()
    details = bon.details.select_related('produit', 'unite').all()
    return render(request, 'partials/bra_detail_rows.html', {'details': details, 'bon': bon})


@login_required
def htmx_bra_produit_search(request, pk):
    bon = get_object_or_404(BonRetourAffectation, pk=pk)
    q = request.GET.get('q', '').strip()
    produits = []
    if len(q) >= 1:
        produits = _produits_affectes_bureau(bon.bureau, q)[:30]
    return render(request, 'partials/bra_produit_search.html', {'produits': produits, 'bureau': bon.bureau})


@login_required
def htmx_bra_modal_produits(request, pk):
    bon = get_object_or_404(BonRetourAffectation, pk=pk)
    q = request.GET.get('q', '').strip()
    produits = _produits_affectes_bureau(bon.bureau, q)
    total_all = len(_produits_affectes_bureau(bon.bureau))
    return render(request, 'partials/bra_produit_modal_content.html', {
        'produits': produits[:300], 'q': q, 'total_all': total_all, 'bureau': bon.bureau
    })


# ─────────────────────────── BONS SORTIE PROVISOIRE ───────────────────────────
# Règle de comptabilité des matières : une sortie provisoire ne peut porter que sur des
# matières Groupe 1 déjà affectées au bureau précis d'où sort le bon (bon.bureau), et dans
# la limite de ce qui y est encore affecté et pas déjà sorti provisoirement (non retourné).

def _qte_sortie_prov_bureau(produit, bureau):
    """Qté du produit actuellement sortie provisoirement au bureau précis, pas encore
    retournée (sorties provisoires validées − retours de sortie provisoire validés)."""
    if not bureau:
        return 0
    total_sortie_prov_en_cours = DetailBonSortieProvisoire.objects.filter(
        produit=produit, bon_sortie_p__bureau=bureau, bon_sortie_p__valide=True
    ).aggregate(t=Sum('qte'))['t'] or 0
    total_retour_sortie_prov = DetailBonRetourSortieProvisoire.objects.filter(
        produit=produit, bon_retour_sp__bureau=bureau, bon_retour_sp__valide=True
    ).aggregate(t=Sum('qte'))['t'] or 0
    return max(0, total_sortie_prov_en_cours - total_retour_sortie_prov)


def _qte_affectee_disponible(produit, bureau):
    """Qté du produit affectée à ce bureau précis, encore disponible pour une sortie provisoire
    ou une mutation (affectations validées − retours d'affectation validés
    − sorties provisoires en cours + mutations entrantes − mutations sortantes)."""
    if not bureau:
        return 0
    total_affecte = DetailBonAffectation.objects.filter(
        produit=produit, bon_affectation__bureau=bureau, bon_affectation__valide=True
    ).aggregate(t=Sum('qte'))['t'] or 0
    total_retour_affectation = DetailBonRetourAffectation.objects.filter(
        produit=produit, bon_retour__bureau=bureau, bon_retour__valide=True
    ).aggregate(t=Sum('qte'))['t'] or 0
    total_mutation_entrante = DetailBonMutation.objects.filter(
        produit=produit, bon_mutation__bureau_destination=bureau, bon_mutation__valide=True
    ).aggregate(t=Sum('qte'))['t'] or 0
    total_mutation_sortante = DetailBonMutation.objects.filter(
        produit=produit, bon_mutation__bureau_origine=bureau, bon_mutation__valide=True
    ).aggregate(t=Sum('qte'))['t'] or 0

    net_affecte = total_affecte - total_retour_affectation + total_mutation_entrante - total_mutation_sortante
    return max(0, net_affecte - _qte_sortie_prov_bureau(produit, bureau))


def _produits_sortie_prov_bureau(bureau, q=None):
    """Liste des produits Groupe 1 actuellement sortis provisoirement (non encore retournés)
    du bureau précis, avec leur qté encore à retourner (annotée en p.qte_sp_dispo)."""
    if not bureau:
        return []
    produit_ids = DetailBonSortieProvisoire.objects.filter(
        bon_sortie_p__bureau=bureau, bon_sortie_p__valide=True
    ).values_list('produit_id', flat=True)

    qs = Produit.objects.filter(pk__in=set(produit_ids), nomenclature__startswith='1').select_related('unite').order_by('nomenclature')
    if q:
        qs = qs.filter(Q(designation__icontains=q) | Q(nomenclature__icontains=q))

    produits = []
    for p in qs:
        dispo = _qte_sortie_prov_bureau(p, bureau)
        if dispo > 0:
            p.qte_sp_dispo = dispo
            last_detail = DetailBonEntree.objects.filter(produit=p).order_by('-bon_entree__date_creation', '-pk').first()
            p.auto_prix_ht = last_detail.prix_ht if last_detail else 0
            p.auto_prix_ttc = last_detail.prix_ttc if last_detail else 0
            produits.append(p)
    return produits


def _produits_affectes_bureau(bureau, q=None):
    """Liste des produits Groupe 1 actuellement affectés à ce bureau précis (par affectation
    directe ou par mutation reçue), avec leur qté encore disponible pour une sortie provisoire
    ou une mutation (annotée en p.qte_affectee_dispo)."""
    if not bureau:
        return []
    produit_ids_affectes = DetailBonAffectation.objects.filter(
        bon_affectation__bureau=bureau, bon_affectation__valide=True
    ).values_list('produit_id', flat=True)
    produit_ids_mutes = DetailBonMutation.objects.filter(
        bon_mutation__bureau_destination=bureau, bon_mutation__valide=True
    ).values_list('produit_id', flat=True)
    produit_ids = set(produit_ids_affectes) | set(produit_ids_mutes)

    qs = Produit.objects.filter(pk__in=produit_ids, nomenclature__startswith='1').select_related('unite').order_by('nomenclature')
    if q:
        qs = qs.filter(Q(designation__icontains=q) | Q(nomenclature__icontains=q))

    produits = []
    for p in qs:
        dispo = _qte_affectee_disponible(p, bureau)
        if dispo > 0:
            p.qte_affectee_dispo = dispo
            # Dernier prix connu depuis les Bons d'Entrée, pour pré-remplir la ligne
            last_detail = DetailBonEntree.objects.filter(produit=p).order_by('-bon_entree__date_creation', '-pk').first()
            p.auto_prix_ht = last_detail.prix_ht if last_detail else 0
            p.auto_prix_ttc = last_detail.prix_ttc if last_detail else 0
            produits.append(p)
    return produits


@login_required
def bons_sortie_prov_list(request):
    bons = BonSortieProvisoire.objects.select_related('depot', 'service', 'bureau').order_by('-annee_creation', '-num_bon')
    context = {
        'page_title': "Bons de sortie provisoire",
        'bons': bons,
        'nb_non_valides': bons.filter(valide=False).count(),
    }
    return render(request, 'bons/sortie_prov_list.html', context)


@login_required
def bon_sortie_prov_detail(request, pk):
    bon = get_object_or_404(BonSortieProvisoire, pk=pk)
    context = {
        'page_title': f"Bon de sortie provisoire N°{bon.num_bon:04d}",
        'bon': bon,
        'details': bon.details.select_related('produit', 'unite').all(),
    }
    return render(request, 'bons/sortie_prov_detail.html', context)


@login_required
def bon_sortie_prov_create(request):
    depots = Depot.objects.all().order_by('code')
    services = Service.objects.filter(actif=True).order_by('code')
    annees = AnneeExercice.objects.all().order_by('-annee')
    if request.method == 'POST':
        num_bon = request.POST.get('num_bon', '').strip()
        if num_bon:
            bon = BonSortieProvisoire.objects.create(
                num_bon=int(num_bon),
                date_sortie=request.POST.get('date_sortie') or None,
                date_retour_prevue=request.POST.get('date_retour_prevue') or None,
                annee_creation=request.POST.get('annee_creation') or None,
                depot_id=request.POST.get('depot_id') or None,
                service_id=request.POST.get('service_id') or None,
                bureau_id=request.POST.get('bureau_id') or None,
                chapitre=request.POST.get('chapitre', '').strip(),
                observation=request.POST.get('observation', ''),
            )
            return redirect('matieres:bon_sortie_prov_update', pk=bon.pk)
    next_num = (BonSortieProvisoire.objects.order_by('-num_bon').values_list('num_bon', flat=True).first() or 0) + 1
    context = {
        'page_title': "Nouveau bon de sortie provisoire",
        'depots': depots, 'services': services,
        'annees': annees, 'today': date.today(), 'next_num': next_num,
    }
    return render(request, 'bons/sortie_prov_form.html', context)


@login_required
def bon_sortie_prov_update(request, pk):
    bon = get_object_or_404(BonSortieProvisoire, pk=pk)
    depots = Depot.objects.all().order_by('code')
    services = Service.objects.filter(actif=True).order_by('code')
    unites = Unite.objects.all().order_by('libelle')
    if request.method == 'POST' and not bon.valide:
        bon.date_sortie = request.POST.get('date_sortie') or bon.date_sortie
        bon.date_retour_prevue = request.POST.get('date_retour_prevue') or bon.date_retour_prevue
        bon.annee_creation = request.POST.get('annee_creation') or bon.annee_creation
        bon.depot_id = request.POST.get('depot_id') or bon.depot_id
        bon.service_id = request.POST.get('service_id') or bon.service_id
        bon.bureau_id = request.POST.get('bureau_id') or bon.bureau_id
        bon.chapitre = request.POST.get('chapitre', bon.chapitre)
        bon.observation = request.POST.get('observation', bon.observation)
        bon.save()
    details = bon.details.select_related('produit', 'unite').all()
    bureaux = Bureau.objects.filter(service_id=bon.service_id, actif=True).order_by('code') if bon.service_id else Bureau.objects.none()
    context = {
        'page_title': f"BSP-{bon.num_bon:04d}",
        'bon': bon, 'details': details,
        'depots': depots, 'services': services, 'bureaux': bureaux, 'unites': unites,
    }
    return render(request, 'bons/sortie_prov_update.html', context)


@login_required
def bon_sortie_prov_valider(request, pk):
    if request.method != 'POST':
        return redirect('matieres:bon_sortie_prov_update', pk=pk)
    bon = get_object_or_404(BonSortieProvisoire, pk=pk)
    if bon.valide:
        messages.warning(request, "Ce bon est déjà validé.")
        return redirect('matieres:bon_sortie_prov_update', pk=pk)
    if not bon.bureau:
        messages.error(request, "Validation impossible : sélectionnez le service et le bureau du bon.")
        return redirect('matieres:bon_sortie_prov_update', pk=pk)

    erreurs = []
    for d in bon.details.select_related('produit').all():
        if d.produit:
            if d.produit.groupe != '1':
                erreurs.append(f"{d.nomenclature} : matière non Groupe 1.")
            else:
                dispo = _qte_affectee_disponible(d.produit, bon.bureau)
                if dispo < int(d.qte):
                    erreurs.append(
                        f"{d.nomenclature} — qté affectée à {bon.bureau} : {dispo} < qté demandée {d.qte}."
                    )
    if erreurs:
        messages.error(request, "Validation impossible : " + " | ".join(erreurs))
        return redirect('matieres:bon_sortie_prov_update', pk=pk)

    for d in bon.details.select_related('produit', 'unite').all():
        if d.produit:
            # L'article passe de l'état « affecté présent » à « affecté mais temporairement sorti » :
            # qte_affectation diminue d'autant que qte_sp augmente (même unités, autre sous-état).
            d.produit.qte_affectation = max(0, d.produit.qte_affectation - int(d.qte))
            d.produit.qte_sp += int(d.qte)
            d.produit.save(update_fields=['qte_affectation', 'qte_sp'])
            if bon.depot_id:
                sd, _ = StockDepot.objects.get_or_create(
                    produit=d.produit, depot_id=bon.depot_id,
                    defaults={
                        'nomenclature': d.nomenclature, 'designation': d.designation,
                        'qte_stock': d.produit.stock_global,
                    }
                )
                sd.qte_stock -= int(d.qte)
                sd.save(update_fields=['qte_stock'])

        Journal.objects.create(
            date_creation=bon.date_sortie,
            num_bon=bon.num_bon,
            type_entree='Sortie Provisoire',
            groupe=d.produit.groupe if d.produit else '1',
            designation=d.designation,
            nomenclature=d.nomenclature,
            specification=d.specification,
            qte=int(d.qte),
            unite=str(d.unite) if d.unite else '',
            prix_ht=d.prix_ht,
            prix_ttc=d.prix_ttc,
            montant_ttc=d.montant_ttc,
            service=str(bon.service) if bon.service else '',
            bureau=str(bon.bureau) if bon.bureau else '',
            annee_exercice=bon.annee_creation,
            depot=str(bon.depot) if bon.depot else '',
            qte_sp=int(d.qte),
            existant=d.produit.stock_global if d.produit else 0,
            sortie_periode=int(d.qte),
            existant_fin_periode=d.produit.stock_disponible if d.produit else 0,
            montant_existant=(d.produit.stock_disponible * d.prix_ht) if d.produit else 0,
        )

    bon.valide = True
    bon.save(update_fields=['valide'])
    messages.success(request, f"BSP-{bon.num_bon:04d} validé avec succès.")
    return redirect('matieres:bon_sortie_prov_update', pk=pk)


@login_required
def bon_sortie_prov_devalider(request, pk):
    if request.method != 'POST':
        return redirect('matieres:bon_sortie_prov_update', pk=pk)
    bon = get_object_or_404(BonSortieProvisoire, pk=pk)
    if not bon.valide:
        messages.warning(request, "Ce bon n'est pas validé.")
        return redirect('matieres:bon_sortie_prov_update', pk=pk)

    for d in bon.details.select_related('produit').all():
        if d.produit:
            d.produit.qte_sp = max(0, d.produit.qte_sp - int(d.qte))
            d.produit.qte_affectation += int(d.qte)
            d.produit.save(update_fields=['qte_sp', 'qte_affectation'])
            if bon.depot_id:
                try:
                    sd = StockDepot.objects.get(produit=d.produit, depot_id=bon.depot_id)
                    sd.qte_stock += int(d.qte)
                    sd.save(update_fields=['qte_stock'])
                except StockDepot.DoesNotExist:
                    pass

    Journal.objects.filter(num_bon=bon.num_bon, type_entree='Sortie Provisoire').delete()
    bon.valide = False
    bon.save(update_fields=['valide'])
    messages.success(request, f"BSP-{bon.num_bon:04d} dévalidé.")
    return redirect('matieres:bon_sortie_prov_update', pk=pk)


@login_required
def bon_sortie_prov_etat(request, pk):
    bon = get_object_or_404(BonSortieProvisoire, pk=pk)
    details = list(bon.details.select_related('produit', 'unite').all())
    for d in details:
        segments = d.nomenclature.split('.') if d.nomenclature else []
        d.groupe_disp = segments[0][0] if segments and segments[0] else ''
        d.compte_principal_disp = segments[0] if len(segments) >= 1 else ''
        d.sous_compte_disp = '.'.join(segments[:2]) if len(segments) >= 2 else ''
    context = {
        'page_title': f"État — Bon de sortie provisoire N°{bon.num_bon:04d}",
        'bon': bon,
        'societe': SocieteGCS.objects.first(),
        'details': details,
        'total_qte': sum(d.qte for d in details),
        'total_ttc': bon.total_ttc(),
    }
    return render(request, 'bons/sortie_prov_etat.html', context)


# ─── HTMX — Bon de Sortie Provisoire ───

@login_required
def htmx_bsp_add_detail(request, pk):
    bon = get_object_or_404(BonSortieProvisoire, pk=pk)
    if request.method == 'POST' and not bon.valide:
        designation = request.POST.get('designation', '').strip()
        if designation:
            def _dec(v, d='0'):
                try:
                    return Decimal(str(v).replace(',', '.').strip() or d)
                except Exception:
                    return Decimal(d)
            qte      = _dec(request.POST.get('qte', '0'))
            prix_ttc = _dec(request.POST.get('prix_ttc', '0'))
            DetailBonSortieProvisoire.objects.create(
                bon_sortie_p=bon,
                produit_id=request.POST.get('produit_id') or None,
                designation=designation,
                nomenclature=request.POST.get('nomenclature', '').strip(),
                specification=request.POST.get('specification', '').strip(),
                qte=qte,
                unite_id=request.POST.get('unite_id') or None,
                prix_ht=_dec(request.POST.get('prix_ht', '0')),
                prix_ttc=prix_ttc,
                montant_ttc=qte * prix_ttc,
                observation=request.POST.get('observation', ''),
            )
    details = bon.details.select_related('produit', 'unite').all()
    return render(request, 'partials/bsp_detail_rows.html', {'details': details, 'bon': bon})


@login_required
def htmx_bsp_delete_detail(request, detail_pk):
    detail = get_object_or_404(DetailBonSortieProvisoire, pk=detail_pk)
    bon = detail.bon_sortie_p
    if not bon.valide:
        detail.delete()
    details = bon.details.select_related('produit', 'unite').all()
    return render(request, 'partials/bsp_detail_rows.html', {'details': details, 'bon': bon})


@login_required
def htmx_bsp_produit_search(request, pk):
    bon = get_object_or_404(BonSortieProvisoire, pk=pk)
    q = request.GET.get('q', '').strip()
    produits = []
    if len(q) >= 1:
        produits = _produits_affectes_bureau(bon.bureau, q)[:30]
    return render(request, 'partials/bsp_produit_search.html', {'produits': produits, 'bureau': bon.bureau})


@login_required
def htmx_bsp_modal_produits(request, pk):
    bon = get_object_or_404(BonSortieProvisoire, pk=pk)
    q = request.GET.get('q', '').strip()
    produits = _produits_affectes_bureau(bon.bureau, q)
    total_all = len(_produits_affectes_bureau(bon.bureau))
    return render(request, 'partials/bsp_produit_modal_content.html', {
        'produits': produits[:300], 'q': q, 'total_all': total_all, 'bureau': bon.bureau
    })


# ─────────────────────────── BONS RETOUR SORTIE PROVISOIRE ───────────────────────────

@login_required
def bons_retour_sortie_prov_list(request):
    bons = BonRetourSortieProvisoire.objects.select_related('depot', 'service', 'bureau').order_by('-annee_creation', '-num_bon')
    nb_non_valides = bons.filter(valide=False).count()
    context = {'page_title': "Bons de retour sortie provisoire", 'bons': bons, 'nb_non_valides': nb_non_valides}
    return render(request, 'bons/retour_sortie_prov_list.html', context)


@login_required
def bon_retour_sortie_prov_create(request):
    depots = Depot.objects.all().order_by('code')
    services = Service.objects.filter(actif=True).order_by('code')
    annees = AnneeExercice.objects.all().order_by('-annee')
    if request.method == 'POST':
        num_bon = request.POST.get('num_bon', '').strip()
        if num_bon:
            bon = BonRetourSortieProvisoire.objects.create(
                num_bon=int(num_bon),
                date_retour=request.POST.get('date_retour') or None,
                annee_creation=request.POST.get('annee_creation') or None,
                depot_id=request.POST.get('depot_id') or None,
                service_id=request.POST.get('service_id') or None,
                bureau_id=request.POST.get('bureau_id') or None,
                observation=request.POST.get('observation', ''),
            )
            return redirect('matieres:bon_retour_sortie_prov_update', pk=bon.pk)
    next_num = (BonRetourSortieProvisoire.objects.order_by('-num_bon').values_list('num_bon', flat=True).first() or 0) + 1
    context = {
        'page_title': "Nouveau bon de retour sortie provisoire",
        'depots': depots, 'services': services,
        'annees': annees, 'today': date.today(), 'next_num': next_num,
    }
    return render(request, 'bons/retour_sortie_prov_form.html', context)


@login_required
def bon_retour_sortie_prov_update(request, pk):
    bon = get_object_or_404(BonRetourSortieProvisoire, pk=pk)
    depots = Depot.objects.all().order_by('code')
    services = Service.objects.filter(actif=True).order_by('code')
    unites = Unite.objects.all().order_by('libelle')
    if request.method == 'POST' and not bon.valide:
        bon.date_retour = request.POST.get('date_retour') or bon.date_retour
        bon.annee_creation = request.POST.get('annee_creation') or bon.annee_creation
        bon.depot_id = request.POST.get('depot_id') or bon.depot_id
        bon.service_id = request.POST.get('service_id') or bon.service_id
        bon.bureau_id = request.POST.get('bureau_id') or bon.bureau_id
        bon.observation = request.POST.get('observation', bon.observation)
        bon.save()
    details = bon.details.select_related('produit', 'unite').all()
    bureaux = Bureau.objects.filter(service_id=bon.service_id, actif=True).order_by('code') if bon.service_id else Bureau.objects.none()
    context = {
        'page_title': f"BRSP-{bon.num_bon:04d}",
        'bon': bon, 'details': details,
        'depots': depots, 'services': services, 'bureaux': bureaux, 'unites': unites,
    }
    return render(request, 'bons/retour_sortie_prov_update.html', context)


@login_required
def bon_retour_sortie_prov_valider(request, pk):
    if request.method != 'POST':
        return redirect('matieres:bon_retour_sortie_prov_update', pk=pk)
    bon = get_object_or_404(BonRetourSortieProvisoire, pk=pk)
    if bon.valide:
        messages.warning(request, "Ce bon est déjà validé.")
        return redirect('matieres:bon_retour_sortie_prov_update', pk=pk)
    if not bon.bureau:
        messages.error(request, "Validation impossible : sélectionnez le service et le bureau du bon.")
        return redirect('matieres:bon_retour_sortie_prov_update', pk=pk)

    erreurs = []
    for d in bon.details.select_related('produit').all():
        if d.produit:
            if d.produit.groupe != '1':
                erreurs.append(f"{d.nomenclature} : matière non Groupe 1.")
            else:
                dispo = _qte_sortie_prov_bureau(d.produit, bon.bureau)
                if dispo < int(d.qte):
                    erreurs.append(
                        f"{d.nomenclature} — qté sortie provisoire à {bon.bureau} : {dispo} < retour demandé {d.qte}."
                    )
    if erreurs:
        messages.error(request, "Validation impossible : " + " | ".join(erreurs))
        return redirect('matieres:bon_retour_sortie_prov_update', pk=pk)

    for d in bon.details.select_related('produit', 'unite').all():
        if d.produit:
            # L'article revient de sortie provisoire : il redevient simplement « affecté présent ».
            d.produit.qte_sp = max(0, d.produit.qte_sp - int(d.qte))
            d.produit.qte_affectation += int(d.qte)
            d.produit.save(update_fields=['qte_sp', 'qte_affectation'])
            if bon.depot_id:
                sd, _ = StockDepot.objects.get_or_create(
                    produit=d.produit, depot_id=bon.depot_id,
                    defaults={'nomenclature': d.nomenclature, 'designation': d.designation, 'qte_stock': 0}
                )
                sd.qte_stock += int(d.qte)
                sd.save(update_fields=['qte_stock'])

        Journal.objects.create(
            date_creation=bon.date_retour,
            num_bon=bon.num_bon,
            type_entree='Retour Sortie Provisoire',
            groupe=d.produit.groupe if d.produit else '1',
            designation=d.designation,
            nomenclature=d.nomenclature,
            specification=d.specification,
            qte=int(d.qte),
            unite=str(d.unite) if d.unite else '',
            prix_ht=d.prix_ht,
            prix_ttc=d.prix_ttc,
            montant_ttc=d.montant_ttc,
            service=str(bon.service) if bon.service else '',
            bureau=str(bon.bureau) if bon.bureau else '',
            annee_exercice=bon.annee_creation,
            depot=str(bon.depot) if bon.depot else '',
            date_retour=bon.date_retour,
            qte_sp=int(d.qte),
            existant=d.produit.stock_global if d.produit else 0,
            entree_periode=int(d.qte),
            existant_fin_periode=d.produit.stock_disponible if d.produit else 0,
            montant_existant=(d.produit.stock_disponible * d.prix_ht) if d.produit else 0,
        )

    bon.valide = True
    bon.save(update_fields=['valide'])
    messages.success(request, f"BRSP-{bon.num_bon:04d} validé avec succès.")
    return redirect('matieres:bon_retour_sortie_prov_update', pk=pk)


@login_required
def bon_retour_sortie_prov_devalider(request, pk):
    if request.method != 'POST':
        return redirect('matieres:bon_retour_sortie_prov_update', pk=pk)
    bon = get_object_or_404(BonRetourSortieProvisoire, pk=pk)
    if not bon.valide:
        messages.warning(request, "Ce bon n'est pas validé.")
        return redirect('matieres:bon_retour_sortie_prov_update', pk=pk)

    for d in bon.details.select_related('produit').all():
        if d.produit:
            d.produit.qte_sp += int(d.qte)
            d.produit.qte_affectation = max(0, d.produit.qte_affectation - int(d.qte))
            d.produit.save(update_fields=['qte_sp', 'qte_affectation'])
            if bon.depot_id:
                try:
                    sd = StockDepot.objects.get(produit=d.produit, depot_id=bon.depot_id)
                    sd.qte_stock -= int(d.qte)
                    sd.save(update_fields=['qte_stock'])
                except StockDepot.DoesNotExist:
                    pass

    Journal.objects.filter(num_bon=bon.num_bon, type_entree='Retour Sortie Provisoire').delete()
    bon.valide = False
    bon.save(update_fields=['valide'])
    messages.success(request, f"BRSP-{bon.num_bon:04d} dévalidé.")
    return redirect('matieres:bon_retour_sortie_prov_update', pk=pk)


@login_required
def bon_retour_sortie_prov_etat(request, pk):
    """État officiel imprimable — Modèle N°4 (Bon de sortie provisoire), sens retour."""
    bon = get_object_or_404(BonRetourSortieProvisoire, pk=pk)
    details = list(bon.details.select_related('produit', 'unite').all())
    for d in details:
        segments = d.nomenclature.split('.') if d.nomenclature else []
        d.groupe_disp = segments[0][0] if segments and segments[0] else ''
        d.compte_principal_disp = segments[0] if len(segments) >= 1 else ''
        d.sous_compte_disp = '.'.join(segments[:2]) if len(segments) >= 2 else ''
    context = {
        'page_title': f"État — Bon de retour sortie provisoire N°{bon.num_bon:04d}",
        'bon': bon,
        'societe': SocieteGCS.objects.first(),
        'details': details,
        'total_qte': sum(d.qte for d in details),
        'total_ttc': bon.total_ttc(),
    }
    return render(request, 'bons/retour_sortie_prov_etat.html', context)


# ─── HTMX — Bon de Retour Sortie Provisoire ───

@login_required
def htmx_brsp_add_detail(request, pk):
    bon = get_object_or_404(BonRetourSortieProvisoire, pk=pk)
    if request.method == 'POST' and not bon.valide:
        designation = request.POST.get('designation', '').strip()
        if designation:
            def _dec(v, d='0'):
                try:
                    return Decimal(str(v).replace(',', '.').strip() or d)
                except Exception:
                    return Decimal(d)
            qte      = _dec(request.POST.get('qte', '0'))
            prix_ttc = _dec(request.POST.get('prix_ttc', '0'))
            DetailBonRetourSortieProvisoire.objects.create(
                bon_retour_sp=bon,
                produit_id=request.POST.get('produit_id') or None,
                designation=designation,
                nomenclature=request.POST.get('nomenclature', '').strip(),
                specification=request.POST.get('specification', '').strip(),
                code_immatriculation=request.POST.get('code_immatriculation', '').strip(),
                qte=qte,
                unite_id=request.POST.get('unite_id') or None,
                prix_ht=_dec(request.POST.get('prix_ht', '0')),
                prix_ttc=prix_ttc,
                montant_ttc=qte * prix_ttc,
                observation=request.POST.get('observation', ''),
            )
    details = bon.details.select_related('produit', 'unite').all()
    return render(request, 'partials/brsp_detail_rows.html', {'details': details, 'bon': bon})


@login_required
def htmx_brsp_delete_detail(request, detail_pk):
    detail = get_object_or_404(DetailBonRetourSortieProvisoire, pk=detail_pk)
    bon = detail.bon_retour_sp
    if not bon.valide:
        detail.delete()
    details = bon.details.select_related('produit', 'unite').all()
    return render(request, 'partials/brsp_detail_rows.html', {'details': details, 'bon': bon})


@login_required
def htmx_brsp_produit_search(request, pk):
    bon = get_object_or_404(BonRetourSortieProvisoire, pk=pk)
    q = request.GET.get('q', '').strip()
    produits = []
    if len(q) >= 1:
        produits = _produits_sortie_prov_bureau(bon.bureau, q)[:30]
    return render(request, 'partials/brsp_produit_search.html', {'produits': produits, 'bureau': bon.bureau})


@login_required
def htmx_brsp_modal_produits(request, pk):
    bon = get_object_or_404(BonRetourSortieProvisoire, pk=pk)
    q = request.GET.get('q', '').strip()
    produits = _produits_sortie_prov_bureau(bon.bureau, q)
    total_all = len(_produits_sortie_prov_bureau(bon.bureau))
    return render(request, 'partials/brsp_produit_modal_content.html', {
        'produits': produits[:300], 'q': q, 'total_all': total_all, 'bureau': bon.bureau
    })


# ─────────────────────────── BONS DE MUTATION ───────────────────────────
# Transfert direct Bureau A → Bureau B d'une matière Groupe 1 déjà affectée, sans passer
# par le dépôt central. Ne touche ni stock_global ni qte_affectation (l'article reste
# « affecté » au global) — seule la répartition par bureau (calculée via le grand-livre
# des DetailBonMutation dans _qte_affectee_disponible) change.

@login_required
def bons_mutation_list(request):
    bons = BonMutation.objects.select_related(
        'service_origine', 'bureau_origine', 'service_destination', 'bureau_destination'
    ).order_by('-date_creation', '-num_bon')
    context = {
        'page_title': "Bordereaux de mutation",
        'bons': bons,
        'nb_non_valides': bons.filter(valide=False).count(),
    }
    return render(request, 'bons/mutation_list.html', context)


@login_required
def bon_mutation_detail(request, pk):
    bon = get_object_or_404(BonMutation, pk=pk)
    context = {
        'page_title': f"Bordereau de mutation N°{bon.num_bon:04d}",
        'bon': bon,
        'details': bon.details.select_related('produit', 'unite').all(),
    }
    return render(request, 'bons/mutation_detail.html', context)


@login_required
def bon_mutation_create(request):
    services = Service.objects.filter(actif=True).order_by('code')
    annees = AnneeExercice.objects.all().order_by('-annee')
    if request.method == 'POST':
        num_bon = request.POST.get('num_bon', '').strip()
        if num_bon:
            bon = BonMutation.objects.create(
                num_bon=int(num_bon),
                date_creation=request.POST.get('date_creation') or None,
                annee_exercice=request.POST.get('annee_exercice') or None,
                service_origine_id=request.POST.get('service_origine_id') or None,
                bureau_origine_id=request.POST.get('bureau_origine_id') or None,
                service_destination_id=request.POST.get('service_destination_id') or None,
                bureau_destination_id=request.POST.get('bureau_destination_id') or None,
                observation=request.POST.get('observation', ''),
            )
            return redirect('matieres:bon_mutation_update', pk=bon.pk)
    next_num = (BonMutation.objects.order_by('-num_bon').values_list('num_bon', flat=True).first() or 0) + 1
    context = {
        'page_title': "Nouveau bordereau de mutation",
        'services': services,
        'annees': annees, 'today': date.today(), 'next_num': next_num,
    }
    return render(request, 'bons/mutation_form.html', context)


@login_required
def bon_mutation_update(request, pk):
    bon = get_object_or_404(BonMutation, pk=pk)
    services = Service.objects.filter(actif=True).order_by('code')
    unites = Unite.objects.all().order_by('libelle')
    if request.method == 'POST' and not bon.valide:
        bon.date_creation = request.POST.get('date_creation') or bon.date_creation
        bon.annee_exercice = request.POST.get('annee_exercice') or bon.annee_exercice
        bon.service_origine_id = request.POST.get('service_origine_id') or bon.service_origine_id
        bon.bureau_origine_id = request.POST.get('bureau_origine_id') or bon.bureau_origine_id
        bon.service_destination_id = request.POST.get('service_destination_id') or bon.service_destination_id
        bon.bureau_destination_id = request.POST.get('bureau_destination_id') or bon.bureau_destination_id
        bon.observation = request.POST.get('observation', bon.observation)
        bon.save()
    details = bon.details.select_related('produit', 'unite').all()
    bureaux_origine = Bureau.objects.filter(service_id=bon.service_origine_id, actif=True).order_by('code') if bon.service_origine_id else Bureau.objects.none()
    bureaux_destination = Bureau.objects.filter(service_id=bon.service_destination_id, actif=True).order_by('code') if bon.service_destination_id else Bureau.objects.none()
    context = {
        'page_title': f"Bordereau de mutation BM-{bon.num_bon:04d}",
        'bon': bon,
        'details': details,
        'services': services,
        'bureaux_origine': bureaux_origine,
        'bureaux_destination': bureaux_destination,
        'unites': unites,
    }
    return render(request, 'bons/mutation_update.html', context)


@login_required
def bon_mutation_valider(request, pk):
    if request.method != 'POST':
        return redirect('matieres:bon_mutation_update', pk=pk)
    bon = get_object_or_404(BonMutation, pk=pk)
    if bon.valide:
        messages.warning(request, "Ce bon est déjà validé.")
        return redirect('matieres:bon_mutation_update', pk=pk)
    if not bon.bureau_origine or not bon.bureau_destination:
        messages.error(request, "Validation impossible : sélectionnez le bureau origine et le bureau destination.")
        return redirect('matieres:bon_mutation_update', pk=pk)
    if bon.bureau_origine_id == bon.bureau_destination_id:
        messages.error(request, "Validation impossible : le bureau destination doit être différent du bureau origine.")
        return redirect('matieres:bon_mutation_update', pk=pk)
    if not bon.details.exists():
        messages.error(request, "Validation impossible : aucun article dans le bordereau.")
        return redirect('matieres:bon_mutation_update', pk=pk)

    erreurs = []
    for d in bon.details.select_related('produit').all():
        if d.produit:
            if d.produit.groupe != '1':
                erreurs.append(f"{d.nomenclature} : matière non Groupe 1.")
            else:
                dispo = _qte_affectee_disponible(d.produit, bon.bureau_origine)
                if dispo < int(d.qte):
                    erreurs.append(
                        f"{d.nomenclature} — qté affectée à {bon.bureau_origine} : {dispo} < qté demandée {d.qte}."
                    )
    if erreurs:
        messages.error(request, "Validation impossible : " + " | ".join(erreurs))
        return redirect('matieres:bon_mutation_update', pk=pk)

    for d in bon.details.select_related('produit', 'unite').all():
        Journal.objects.create(
            date_creation=bon.date_creation,
            num_bon=bon.num_bon,
            type_entree='Mutation',
            groupe=d.produit.groupe if d.produit else '1',
            designation=d.designation,
            nomenclature=d.nomenclature,
            specification='',
            qte=int(d.qte),
            unite=str(d.unite) if d.unite else '',
            prix_ht=d.prix_ht,
            prix_ttc=d.prix_ttc,
            montant_ttc=d.montant_ttc,
            service=str(bon.service_destination) if bon.service_destination else '',
            bureau=str(bon.bureau_destination) if bon.bureau_destination else '',
            annee_exercice=bon.annee_exercice,
            observation=f"Mutation depuis {bon.bureau_origine}",
            existant=_qte_affectee_disponible(d.produit, bon.bureau_origine) if d.produit else 0,
            sortie_periode=int(d.qte),
            entree_periode=int(d.qte),
        )

    bon.valide = True
    bon.save(update_fields=['valide'])
    messages.success(request, f"Bordereau BM-{bon.num_bon:04d} validé — mutation de {bon.bureau_origine} vers {bon.bureau_destination}.")
    return redirect('matieres:bon_mutation_update', pk=pk)


@login_required
def bon_mutation_devalider(request, pk):
    if request.method != 'POST':
        return redirect('matieres:bon_mutation_update', pk=pk)
    bon = get_object_or_404(BonMutation, pk=pk)
    if not bon.valide:
        messages.warning(request, "Ce bon n'est pas validé.")
        return redirect('matieres:bon_mutation_update', pk=pk)

    Journal.objects.filter(num_bon=bon.num_bon, type_entree='Mutation').delete()
    bon.valide = False
    bon.save(update_fields=['valide'])
    messages.success(request, f"Bordereau BM-{bon.num_bon:04d} dévalidé.")
    return redirect('matieres:bon_mutation_update', pk=pk)


@login_required
def bon_mutation_etat(request, pk):
    bon = get_object_or_404(BonMutation, pk=pk)
    details = list(bon.details.select_related('produit', 'unite').all())
    context = {
        'page_title': f"État — Bordereau de mutation N°{bon.num_bon:04d}",
        'bon': bon,
        'societe': SocieteGCS.objects.first(),
        'details': details,
        'total_qte': sum(d.qte for d in details),
        'total_ttc': bon.total_ttc(),
    }
    return render(request, 'bons/mutation_etat.html', context)


@login_required
def htmx_bm_add_detail(request, pk):
    bon = get_object_or_404(BonMutation, pk=pk)
    if request.method == 'POST' and not bon.valide:
        designation = request.POST.get('designation', '').strip()
        if designation:
            def _dec(v, d='0'):
                try:
                    return Decimal(str(v).replace(',', '.').strip() or d)
                except Exception:
                    return Decimal(d)
            qte = _dec(request.POST.get('qte', '0'))
            prix_ttc = _dec(request.POST.get('prix_ttc', '0'))
            DetailBonMutation.objects.create(
                bon_mutation=bon,
                produit_id=request.POST.get('produit_id') or None,
                designation=designation,
                nomenclature=request.POST.get('nomenclature', '').strip(),
                code_immatriculation=request.POST.get('code_immatriculation', '').strip(),
                qte=qte,
                unite_id=request.POST.get('unite_id') or None,
                prix_ht=_dec(request.POST.get('prix_ht', '0')),
                prix_ttc=prix_ttc,
                montant_ttc=qte * prix_ttc,
                observation=request.POST.get('observation', ''),
            )
    details = bon.details.select_related('produit', 'unite').all()
    return render(request, 'partials/bm_detail_rows.html', {'details': details, 'bon': bon})


@login_required
def htmx_bm_delete_detail(request, detail_pk):
    detail = get_object_or_404(DetailBonMutation, pk=detail_pk)
    bon = detail.bon_mutation
    if not bon.valide:
        detail.delete()
    details = bon.details.select_related('produit', 'unite').all()
    return render(request, 'partials/bm_detail_rows.html', {'details': details, 'bon': bon})


@login_required
def htmx_bm_produit_search(request, pk):
    bon = get_object_or_404(BonMutation, pk=pk)
    q = request.GET.get('q', '').strip()
    produits = []
    if len(q) >= 1:
        produits = _produits_affectes_bureau(bon.bureau_origine, q)[:30]
    return render(request, 'partials/bm_produit_search.html', {'produits': produits, 'bureau': bon.bureau_origine})


@login_required
def htmx_bm_modal_produits(request, pk):
    bon = get_object_or_404(BonMutation, pk=pk)
    q = request.GET.get('q', '').strip()
    produits = _produits_affectes_bureau(bon.bureau_origine, q)
    total_all = len(_produits_affectes_bureau(bon.bureau_origine))
    return render(request, 'partials/bm_produit_modal_content.html', {
        'produits': produits[:300], 'q': q, 'total_all': total_all, 'bureau': bon.bureau_origine
    })


# ─────────────────────────── BONS SORTIE DÉFINITIVE ───────────────────────────

@login_required
def bons_sortie_def_list(request):
    bons = BonSortieDefinitive.objects.filter(groupe='1').select_related('depot', 'service', 'bureau').order_by('-date_creation', '-num_bon')
    context = {
        'page_title': "Bons de sortie définitive — Groupe 1",
        'bons': bons,
        'nb_non_valides': bons.filter(valide=False).count(),
    }
    return render(request, 'bons/sortie_def_list.html', context)


@login_required
def bon_sortie_def_detail(request, pk):
    bon = get_object_or_404(BonSortieDefinitive, pk=pk)
    context = {
        'page_title': f"Bon de sortie définitive N°{bon.num_bon:04d}",
        'bon': bon,
        'details': bon.details.select_related('produit', 'unite').all(),
    }
    return render(request, 'bons/sortie_def_detail.html', context)


@login_required
def bon_sortie_def_create(request):
    context = {'page_title': "Nouveau bon de sortie définitive"}
    return render(request, 'bons/sortie_def_form.html', context)


# ─────────────────────────── BONS SORTIE DÉFINITIVE G1 ───────────────────────────

@login_required
def bons_sortie_def_g1_list(request):
    bons = BonSortieDefinitiveG1.objects.select_related('depot', 'service', 'bureau').order_by('-date_creation', '-num_bon')
    context = {'page_title': "PV de réforme des matières (Groupe 1)", 'bons': bons}
    return render(request, 'bons/sortie_def_g1_list.html', context)


@login_required
def bon_sortie_def_g1_create(request):
    services = Service.objects.filter(actif=True).order_by('code')
    depots = Depot.objects.all().order_by('code')
    annees = AnneeExercice.objects.all().order_by('-annee')
    if request.method == 'POST':
        num_bon = request.POST.get('num_bon', '').strip()
        if num_bon:
            bon = BonSortieDefinitiveG1.objects.create(
                num_bon=int(num_bon),
                date_creation=request.POST.get('date_creation') or None,
                annee_exercice=request.POST.get('annee_exercice') or None,
                section=request.POST.get('section', '').strip(),
                chapitre=request.POST.get('chapitre', '').strip(),
                service_id=request.POST.get('service_id') or None,
                bureau_id=request.POST.get('bureau_id') or None,
                depot_id=request.POST.get('depot_id') or None,
            )
            return redirect('matieres:bon_sortie_def_g1_update', pk=bon.pk)
    next_num = (BonSortieDefinitiveG1.objects.order_by('-num_bon').values_list('num_bon', flat=True).first() or 0) + 1
    context = {
        'page_title': "Nouveau PV de réforme des matières",
        'services': services, 'depots': depots, 'annees': annees,
        'today': date.today(), 'next_num': next_num,
    }
    return render(request, 'bons/sortie_def_g1_form.html', context)


@login_required
def bon_sortie_def_g1_update(request, pk):
    bon = get_object_or_404(BonSortieDefinitiveG1, pk=pk)
    services = Service.objects.filter(actif=True).order_by('code')
    depots = Depot.objects.all().order_by('code')
    unites = Unite.objects.all().order_by('libelle')
    if request.method == 'POST' and not bon.valide:
        bon.date_creation = request.POST.get('date_creation') or bon.date_creation
        bon.annee_exercice = request.POST.get('annee_exercice') or bon.annee_exercice
        bon.section = request.POST.get('section', bon.section)
        bon.chapitre = request.POST.get('chapitre', bon.chapitre)
        bon.service_id = request.POST.get('service_id') or bon.service_id
        bon.bureau_id = request.POST.get('bureau_id') or bon.bureau_id
        bon.depot_id = request.POST.get('depot_id') or bon.depot_id
        bon.membres_commission = request.POST.get('membres_commission', bon.membres_commission)
        bon.observations_commission = request.POST.get('observations_commission', bon.observations_commission)
        bon.visa_controleur = request.POST.get('visa_controleur', bon.visa_controleur)
        bon.autorite_approbation = request.POST.get('autorite_approbation', bon.autorite_approbation)
        bon.save()
    details = bon.details.select_related('produit', 'unite').all()
    bureaux = Bureau.objects.filter(service_id=bon.service_id, actif=True).order_by('code') if bon.service_id else Bureau.objects.none()
    context = {
        'page_title': f"PV de réforme PVR-{bon.num_bon:04d}",
        'bon': bon, 'details': details,
        'services': services, 'bureaux': bureaux, 'depots': depots, 'unites': unites,
    }
    return render(request, 'bons/sortie_def_g1_update.html', context)


@login_required
def bon_sortie_def_g1_valider(request, pk):
    if request.method != 'POST':
        return redirect('matieres:bon_sortie_def_g1_update', pk=pk)
    bon = get_object_or_404(BonSortieDefinitiveG1, pk=pk)
    if bon.valide:
        messages.warning(request, "Ce PV est déjà validé.")
        return redirect('matieres:bon_sortie_def_g1_update', pk=pk)
    if not bon.details.exists():
        messages.error(request, "Validation impossible : aucun article dans le PV.")
        return redirect('matieres:bon_sortie_def_g1_update', pk=pk)

    # Garde-fou : matière bien du Groupe 1, et stock disponible suffisant pour couvrir
    # la quantité examinée sur chaque ligne.
    erreurs = []
    for d in bon.details.select_related('produit').all():
        if d.produit:
            if d.produit.groupe != '1':
                erreurs.append(f"{d.nomenclature} : matière non Groupe 1.")
            elif d.produit.stock_disponible < d.qte:
                erreurs.append(
                    f"{d.nomenclature} — stock dispo {d.produit.stock_disponible} < qté examinée {d.qte}."
                )
    if erreurs:
        messages.error(request, "Validation impossible : " + " | ".join(erreurs))
        return redirect('matieres:bon_sortie_def_g1_update', pk=pk)

    for d in bon.details.select_related('produit', 'unite').all():
        # Seules les décisions « à vendre » et « à démolir » constituent une véritable sortie
        # définitive — « à conserver ou à transformer » reste dans l'existant, sans mouvement.
        qte_reforme = d.qte if d.decision in ('vendre', 'demolir') else 0
        stock_avant = 0
        stock_apres = 0
        if d.produit:
            stock_avant = d.produit.stock_global
            d.produit.stock_global = max(0, d.produit.stock_global - qte_reforme)
            d.produit.qte_sd += qte_reforme
            d.produit.save(update_fields=['stock_global', 'qte_sd'])
            stock_apres = d.produit.stock_global

            if bon.depot_id and qte_reforme:
                sd = StockDepot.objects.filter(produit=d.produit, depot_id=bon.depot_id).first()
                if not sd:
                    sd = StockDepot.objects.filter(produit=d.produit).order_by('-qte_stock').first()
                if sd:
                    sd.qte_stock = max(0, sd.qte_stock - qte_reforme)
                    sd.save(update_fields=['qte_stock'])

        if qte_reforme:
            montant_reforme = d.montant()
            prix_unitaire = d.prix_unitaire
            Journal.objects.create(
                date_creation=bon.date_creation,
                num_bon=bon.num_bon,
                type_entree='Sortie Définitive',
                groupe='1',
                designation=d.designation,
                nomenclature=d.nomenclature,
                specification=d.specification,
                qte=qte_reforme,
                unite=str(d.unite) if d.unite else '',
                prix_ht=prix_unitaire,
                prix_ttc=prix_unitaire,
                montant_ttc=montant_reforme,
                service=str(bon.service) if bon.service else '',
                bureau=str(bon.bureau) if bon.bureau else '',
                annee_exercice=bon.annee_exercice,
                depot=str(bon.depot) if bon.depot else '',
                observation=f"PV de réforme — {d.get_decision_display()}",
                qte_sd=qte_reforme,
                num_bon_sortie=bon.num_bon,
                existant=stock_avant,
                sortie_periode=qte_reforme,
                existant_fin_periode=stock_apres,
                montant_existant=stock_apres * prix_unitaire,
            )

    bon.valide = True
    bon.save(update_fields=['valide'])
    messages.success(request, f"PV de réforme PVR-{bon.num_bon:04d} validé. Stock mis à jour définitivement.")
    return redirect('matieres:bon_sortie_def_g1_update', pk=pk)


@login_required
def bon_sortie_def_g1_devalider(request, pk):
    if request.method != 'POST':
        return redirect('matieres:bon_sortie_def_g1_update', pk=pk)
    bon = get_object_or_404(BonSortieDefinitiveG1, pk=pk)
    if not bon.valide:
        messages.warning(request, "Ce PV n'est pas validé.")
        return redirect('matieres:bon_sortie_def_g1_update', pk=pk)

    for d in bon.details.select_related('produit').all():
        qte_reforme = d.qte if d.decision in ('vendre', 'demolir') else 0
        if d.produit and qte_reforme:
            d.produit.stock_global += qte_reforme
            d.produit.qte_sd = max(0, d.produit.qte_sd - qte_reforme)
            d.produit.save(update_fields=['stock_global', 'qte_sd'])
            if bon.depot_id:
                try:
                    sd = StockDepot.objects.get(produit=d.produit, depot_id=bon.depot_id)
                    sd.qte_stock += qte_reforme
                    sd.save(update_fields=['qte_stock'])
                except StockDepot.DoesNotExist:
                    pass

    Journal.objects.filter(num_bon=bon.num_bon, type_entree='Sortie Définitive', groupe='1').delete()
    bon.valide = False
    bon.save(update_fields=['valide'])
    messages.success(request, f"PV de réforme PVR-{bon.num_bon:04d} dévalidé. Mouvements de stock annulés.")
    return redirect('matieres:bon_sortie_def_g1_update', pk=pk)


@login_required
def bon_sortie_def_g1_etat(request, pk):
    bon = get_object_or_404(BonSortieDefinitiveG1, pk=pk)
    details = list(bon.details.select_related('produit', 'unite').all())
    for d in details:
        segments = d.nomenclature.split('.') if d.nomenclature else []
        d.groupe_disp = segments[0][0] if segments and segments[0] else ''
        d.compte_principal_disp = segments[0] if len(segments) >= 1 else ''
        d.sous_compte_disp = '.'.join(segments[:2]) if len(segments) >= 2 else ''
    context = {
        'page_title': f"État — PV de réforme PVR-{bon.num_bon:04d}",
        'bon': bon,
        'societe': SocieteGCS.objects.first(),
        'details': details,
        'total_conserver': sum(d.qte for d in details if d.decision == 'conserver'),
        'total_vendre': sum(d.qte for d in details if d.decision == 'vendre'),
        'total_demolir': sum(d.qte for d in details if d.decision == 'demolir'),
    }
    return render(request, 'bons/sortie_def_g1_etat.html', context)


@login_required
def bon_sortie_def_g1_etat_sortie(request, pk):
    bon = get_object_or_404(BonSortieDefinitiveG1, pk=pk)
    details = list(bon.details.select_related('produit', 'unite').filter(decision__in=['vendre', 'demolir']))
    for d in details:
        segments = d.nomenclature.split('.') if d.nomenclature else []
        d.groupe_disp = segments[0][0] if segments and segments[0] else ''
        d.compte_principal_disp = segments[0] if len(segments) >= 1 else ''
        d.sous_compte_disp = '.'.join(segments[:2]) if len(segments) >= 2 else ''
    context = {
        'page_title': f"État — Bon de sortie définitive PVR-{bon.num_bon:04d}",
        'bon': bon,
        'societe': SocieteGCS.objects.first(),
        'details': details,
        'total_qte': sum(d.qte for d in details),
        'total_montant': sum(d.montant() for d in details),
    }
    return render(request, 'bons/sortie_def_g1_etat_sortie.html', context)


@login_required
def bon_sortie_def_g1_etat_vd(request, pk):
    bon = get_object_or_404(BonSortieDefinitiveG1, pk=pk)
    details = list(bon.details.select_related('produit', 'unite').filter(decision__in=['vendre', 'demolir']))
    for d in details:
        segments = d.nomenclature.split('.') if d.nomenclature else []
        d.groupe_disp = segments[0][0] if segments and segments[0] else ''
        d.compte_principal_disp = segments[0] if len(segments) >= 1 else ''
        d.sous_compte_disp = '.'.join(segments[:2]) if len(segments) >= 2 else ''
    context = {
        'page_title': f"État — PV de vente/destruction PVR-{bon.num_bon:04d}",
        'bon': bon,
        'societe': SocieteGCS.objects.first(),
        'details': details,
        'total_qte': sum(d.qte for d in details),
        'total_montant': sum(d.montant() for d in details),
    }
    return render(request, 'bons/sortie_def_g1_etat_vd.html', context)


# ─── HTMX — PV de Réforme (Sortie Définitive G1) ───

@login_required
def htmx_bsdg1_add_detail(request, pk):
    bon = get_object_or_404(BonSortieDefinitiveG1, pk=pk)
    if request.method == 'POST' and not bon.valide:
        designation = request.POST.get('designation', '').strip()
        if designation:
            def _int(v):
                try:
                    return int(float(str(v).replace(',', '.').strip() or 0))
                except Exception:
                    return 0

            def _dec(v):
                try:
                    return Decimal(str(v).replace(',', '.').strip() or '0')
                except Exception:
                    return Decimal('0')

            decision = request.POST.get('decision', '').strip()
            if decision not in dict(DetailBonSortieDefinitiveG1.DECISION_CHOICES):
                decision = 'conserver'

            DetailBonSortieDefinitiveG1.objects.create(
                bon_sortie_g1=bon,
                produit_id=request.POST.get('produit_id') or None,
                designation=designation,
                nomenclature=request.POST.get('nomenclature', '').strip(),
                specification=request.POST.get('specification', '').strip(),
                unite_id=request.POST.get('unite_id') or None,
                qte=_int(request.POST.get('qte', '0')),
                prix_unitaire=_dec(request.POST.get('prix_unitaire', '0')),
                decision=decision,
                observation=request.POST.get('observation', ''),
            )
    details = bon.details.select_related('produit', 'unite').all()
    return render(request, 'partials/bsdg1_detail_rows.html', {'details': details, 'bon': bon})


@login_required
def htmx_bsdg1_delete_detail(request, detail_pk):
    detail = get_object_or_404(DetailBonSortieDefinitiveG1, pk=detail_pk)
    bon = detail.bon_sortie_g1
    if not bon.valide:
        detail.delete()
    details = bon.details.select_related('produit', 'unite').all()
    return render(request, 'partials/bsdg1_detail_rows.html', {'details': details, 'bon': bon})


@login_required
def htmx_bsdg1_produit_search(request):
    q = request.GET.get('q', '').strip()
    produits = []
    if len(q) >= 1:
        produits = list(Produit.objects.filter(
            Q(designation__icontains=q) | Q(nomenclature__icontains=q),
            nomenclature__startswith='1',
            stock_global__gt=0,
        ).select_related('unite').order_by('nomenclature')[:30])
        _annoter_produits_ba(produits)
    return render(request, 'partials/bsdg1_produit_search.html', {'produits': produits})


@login_required
def htmx_bsdg1_modal_produits(request):
    q = request.GET.get('q', '').strip()
    qs = Produit.objects.filter(
        nomenclature__startswith='1',
        stock_global__gt=0,
    ).select_related('unite').order_by('nomenclature')
    total_all = qs.count()
    if q:
        qs = qs.filter(Q(designation__icontains=q) | Q(nomenclature__icontains=q))
    produits = list(qs[:300])
    _annoter_produits_ba(produits)
    return render(request, 'partials/bsdg1_produit_modal_content.html', {
        'produits': produits, 'q': q, 'total_all': total_all
    })


# ─────────────────────────── BONS SORTIE DÉFINITIVE GROUPE 2 (CONSOMMABLES) ───────────────────────────
# Matières 2e groupe (nomenclature 2x.xx.xx) : consommables à usage unique (ex. stylos, papier).
# Contrairement au Groupe 1, il n'y a ni affectation ni sortie provisoire : l'article quitte
# définitivement l'existant dès la sortie — d'où la décrémentation immédiate de stock_global.

TYPES_SORTIE_G2 = [
    "Distribution / Consommation courante",
    "Dotation initiale",
    "Réapprovisionnement service",
    "Commande de service",
    "Perte",
    "Casse / Détérioration",
    "Péremption",
]


@login_required
def bons_sortie_def_g2_list(request):
    bons = BonSortieDefinitive.objects.filter(groupe='2').select_related('depot', 'service', 'bureau').order_by('-date_creation', '-num_bon')
    context = {
        'page_title': "Bons de sortie définitive — Groupe 2 (consommables)",
        'bons': bons,
        'nb_non_valides': bons.filter(valide=False).count(),
    }
    return render(request, 'bons/sortie_def_g2_list.html', context)


@login_required
def bon_sortie_def_g2_create(request):
    services = Service.objects.filter(actif=True).order_by('code')
    depots = Depot.objects.all().order_by('code')
    annees = AnneeExercice.objects.all().order_by('-annee')
    if request.method == 'POST':
        num_bon = request.POST.get('num_bon', '').strip()
        date_creation = request.POST.get('date_creation') or None
        annee = request.POST.get('annee_exercice') or None
        type_sortie = request.POST.get('type_sortie', '').strip()
        service_id = request.POST.get('service_id') or None
        bureau_id = request.POST.get('bureau_id') or None
        depot_id = request.POST.get('depot_id') or None
        chapitre = request.POST.get('chapitre', '').strip()
        if num_bon:
            bon = BonSortieDefinitive.objects.create(
                num_bon=int(num_bon),
                date_creation=date_creation,
                annee_exercice=int(annee) if annee else None,
                groupe='2',
                type_sortie=type_sortie,
                service_id=service_id,
                bureau_id=bureau_id,
                depot_id=depot_id,
                chapitre=chapitre,
            )
            return redirect('matieres:bon_sortie_def_g2_update', pk=bon.pk)
    context = {
        'page_title': "Nouveau bon de sortie définitive — Groupe 2",
        'services': services,
        'depots': depots,
        'annees': annees,
        'types_sortie': TYPES_SORTIE_G2,
        'today': date.today(),
        'next_num': (BonSortieDefinitive.objects.filter(groupe='2').order_by('-num_bon').values_list('num_bon', flat=True).first() or 0) + 1,
    }
    return render(request, 'bons/sortie_def_g2_form.html', context)


def _bsdg2_details_with_depot(bon):
    """Retourne les détails du BSD-G2 annotés avec le dépôt principal du produit."""
    details = list(bon.details.select_related('produit', 'unite').all())
    for d in details:
        if d.produit:
            sd = StockDepot.objects.filter(produit=d.produit).order_by('-qte_stock').first()
            d.depot_nom = str(sd.depot) if (sd and sd.depot) else '—'
        else:
            d.depot_nom = '—'
    return details


@login_required
def bon_sortie_def_g2_update(request, pk):
    bon = get_object_or_404(BonSortieDefinitive, pk=pk, groupe='2')
    services = Service.objects.filter(actif=True).order_by('code')
    depots = Depot.objects.all().order_by('code')
    unites = Unite.objects.all().order_by('libelle')
    if request.method == 'POST' and not bon.valide:
        bon.date_creation = request.POST.get('date_creation') or bon.date_creation
        bon.annee_exercice = request.POST.get('annee_exercice') or bon.annee_exercice
        bon.type_sortie = request.POST.get('type_sortie', bon.type_sortie)
        bon.service_id = request.POST.get('service_id') or bon.service_id
        bon.bureau_id = request.POST.get('bureau_id') or bon.bureau_id
        bon.depot_id = request.POST.get('depot_id') or bon.depot_id
        bon.chapitre = request.POST.get('chapitre', bon.chapitre)
        bon.observation = request.POST.get('observation', bon.observation)
        bon.save()
    details = _bsdg2_details_with_depot(bon)
    bureaux = Bureau.objects.filter(service_id=bon.service_id, actif=True).order_by('code') if bon.service_id else Bureau.objects.none()
    bcs_ouverts = [
        b for b in BonCommandeService.objects.filter(statut='valide').select_related('service', 'bureau')
        if not b.entierement_livre
    ]
    context = {
        'page_title': f"Bon de sortie définitive BSD-{bon.num_bon:04d} (Groupe 2)",
        'bon': bon,
        'details': details,
        'services': services,
        'bureaux': bureaux,
        'depots': depots,
        'unites': unites,
        'types_sortie': TYPES_SORTIE_G2,
        'bcs_ouverts': bcs_ouverts,
    }
    return render(request, 'bons/sortie_def_g2_update.html', context)


@login_required
def bon_sortie_def_g2_valider(request, pk):
    if request.method != 'POST':
        return redirect('matieres:bon_sortie_def_g2_update', pk=pk)
    bon = get_object_or_404(BonSortieDefinitive, pk=pk, groupe='2')
    if bon.valide:
        messages.warning(request, "Ce bon est déjà validé.")
        return redirect('matieres:bon_sortie_def_g2_update', pk=pk)
    if not bon.details.exists():
        messages.error(request, "Validation impossible : aucun article dans le bon.")
        return redirect('matieres:bon_sortie_def_g2_update', pk=pk)

    # Garde-fou : matière bien du Groupe 2, et stock disponible suffisant
    erreurs = []
    for d in bon.details.select_related('produit').all():
        if d.produit:
            if d.produit.groupe != '2':
                erreurs.append(f"{d.nomenclature} : matière non Groupe 2 (consommable).")
            elif d.produit.stock_disponible < d.qte:
                erreurs.append(
                    f"{d.nomenclature} — stock dispo {d.produit.stock_disponible} < qté demandée {d.qte}."
                )
    if erreurs:
        messages.error(request, "Validation impossible : " + " | ".join(erreurs))
        return redirect('matieres:bon_sortie_def_g2_update', pk=pk)

    for d in bon.details.select_related('produit', 'unite').all():
        stock_avant = 0
        stock_apres = 0
        if d.produit:
            # Sortie définitive : l'article quitte l'existant pour de bon.
            stock_avant = d.produit.stock_global
            d.produit.stock_global = max(0, d.produit.stock_global - int(d.qte))
            d.produit.qte_sd += int(d.qte)
            d.produit.save(update_fields=['stock_global', 'qte_sd'])
            stock_apres = d.produit.stock_global

            if bon.depot_id:
                sd = StockDepot.objects.filter(produit=d.produit, depot_id=bon.depot_id).first()
                if not sd:
                    sd = StockDepot.objects.filter(produit=d.produit).order_by('-qte_stock').first()
                if sd:
                    sd.qte_stock = max(0, sd.qte_stock - int(d.qte))
                    sd.save(update_fields=['qte_stock'])

        Journal.objects.create(
            date_creation=bon.date_creation,
            num_bon=bon.num_bon,
            type_entree='Sortie Définitive',
            groupe='2',
            designation=d.designation,
            nomenclature=d.nomenclature,
            specification=d.specification,
            qte=int(d.qte),
            unite=str(d.unite) if d.unite else '',
            prix_ht=d.prix_ht,
            prix_ttc=d.prix_ttc,
            montant_ttc=d.montant_ttc,
            service=str(bon.service) if bon.service else '',
            bureau=str(bon.bureau) if bon.bureau else '',
            annee_exercice=bon.annee_exercice,
            depot=str(bon.depot) if bon.depot else '',
            observation=bon.type_sortie,
            qte_sd=int(d.qte),
            num_bon_sortie=bon.num_bon,
            existant=stock_avant,
            sortie_periode=int(d.qte),
            existant_fin_periode=stock_apres,
            montant_existant=stock_apres * d.prix_ht,
        )

    bon.valide = True
    bon.save(update_fields=['valide'])
    messages.success(request, f"Bon BSD-{bon.num_bon:04d} (Groupe 2) validé. Stock mis à jour définitivement.")
    return redirect('matieres:bon_sortie_def_g2_update', pk=pk)


@login_required
def bon_sortie_def_g2_devalider(request, pk):
    if request.method != 'POST':
        return redirect('matieres:bon_sortie_def_g2_update', pk=pk)
    bon = get_object_or_404(BonSortieDefinitive, pk=pk, groupe='2')
    if not bon.valide:
        messages.warning(request, "Ce bon n'est pas validé.")
        return redirect('matieres:bon_sortie_def_g2_update', pk=pk)

    for d in bon.details.select_related('produit').all():
        if d.produit:
            d.produit.stock_global += int(d.qte)
            d.produit.qte_sd = max(0, d.produit.qte_sd - int(d.qte))
            d.produit.save(update_fields=['stock_global', 'qte_sd'])
            if bon.depot_id:
                try:
                    sd = StockDepot.objects.get(produit=d.produit, depot_id=bon.depot_id)
                    sd.qte_stock += int(d.qte)
                    sd.save(update_fields=['qte_stock'])
                except StockDepot.DoesNotExist:
                    pass

    Journal.objects.filter(num_bon=bon.num_bon, type_entree='Sortie Définitive', groupe='2').delete()
    bon.valide = False
    bon.save(update_fields=['valide'])
    messages.success(request, f"Bon BSD-{bon.num_bon:04d} (Groupe 2) dévalidé. Mouvements de stock annulés.")
    return redirect('matieres:bon_sortie_def_g2_update', pk=pk)


@login_required
def bon_sortie_def_g2_etat(request, pk):
    bon = get_object_or_404(BonSortieDefinitive, pk=pk, groupe='2')
    details = list(bon.details.select_related('produit', 'unite').all())
    for d in details:
        segments = d.nomenclature.split('.') if d.nomenclature else []
        d.groupe_disp = segments[0][0] if segments and segments[0] else ''
        d.compte_principal_disp = segments[0] if len(segments) >= 1 else ''
        d.sous_compte_disp = '.'.join(segments[:2]) if len(segments) >= 2 else ''
    context = {
        'page_title': f"État — Bon de sortie définitive N°{bon.num_bon:04d}",
        'bon': bon,
        'societe': SocieteGCS.objects.first(),
        'details': details,
        'total_qte': sum(d.qte for d in details),
        'total_ttc': bon.total_ttc(),
    }
    return render(request, 'bons/sortie_def_g2_etat.html', context)


def _annoter_produits_g2(produits):
    """Annote chaque produit Groupe 2 avec : stock dépôt max + dernier prix d'entrée connu."""
    for p in produits:
        sd = StockDepot.objects.filter(produit=p).order_by('-qte_stock').first()
        p.stock_depot_max = sd.qte_stock if sd else 0
        p.depot_max_nom = str(sd.depot) if (sd and sd.depot) else '—'
        last_detail = DetailBonEntree.objects.filter(produit=p).order_by('-bon_entree__date_creation', '-pk').first()
        p.auto_prix_ht = last_detail.prix_ht if last_detail else 0
        p.auto_prix_ttc = last_detail.prix_ttc if last_detail else 0
    return produits


# ─── HTMX — Bon de Sortie Définitive Groupe 2 ───

@login_required
def htmx_bsdg2_add_detail(request, pk):
    bon = get_object_or_404(BonSortieDefinitive, pk=pk, groupe='2')
    if request.method == 'POST' and not bon.valide:
        designation = request.POST.get('designation', '').strip()
        if designation:
            def _dec(v, d='0'):
                try:
                    return Decimal(str(v).replace(',', '.').strip() or d)
                except Exception:
                    return Decimal(d)

            produit_id = request.POST.get('produit_id') or None
            nomenclature = request.POST.get('nomenclature', '').strip()
            specification = request.POST.get('specification', '').strip()
            qte = _dec(request.POST.get('qte', '0'))
            unite_id = request.POST.get('unite_id') or None
            prix_ht = _dec(request.POST.get('prix_ht', '0'))
            prix_ttc = _dec(request.POST.get('prix_ttc', '0'))
            observation = request.POST.get('observation', '')
            detail_commande_service_id = request.POST.get('detail_commande_service_id') or None

            DetailBonSortieDefinitive.objects.create(
                bon_sortie_d=bon,
                produit_id=produit_id,
                designation=designation,
                nomenclature=nomenclature,
                specification=specification,
                qte=qte,
                unite_id=unite_id,
                prix_ht=prix_ht,
                prix_ttc=prix_ttc,
                montant_ttc=qte * prix_ttc,
                observation=observation,
                detail_commande_service_id=detail_commande_service_id,
            )

            if detail_commande_service_id and not bon.bon_commande_service_id:
                detail_bcs = DetailBonCommandeService.objects.filter(pk=detail_commande_service_id).first()
                if detail_bcs:
                    bon.bon_commande_service_id = detail_bcs.bon_commande_id
                    bon.save(update_fields=['bon_commande_service'])

    details = _bsdg2_details_with_depot(bon)
    return render(request, 'partials/bsdg2_detail_rows.html', {'details': details, 'bon': bon})


@login_required
def htmx_bsdg2_delete_detail(request, detail_pk):
    detail = get_object_or_404(DetailBonSortieDefinitive, pk=detail_pk)
    bon = detail.bon_sortie_d
    if not bon.valide:
        detail.delete()
    details = _bsdg2_details_with_depot(bon)
    return render(request, 'partials/bsdg2_detail_rows.html', {'details': details, 'bon': bon})


@login_required
def htmx_bsdg2_produit_search(request):
    q = request.GET.get('q', '').strip()
    produits = []
    if len(q) >= 1:
        produits = list(Produit.objects.filter(
            Q(designation__icontains=q) | Q(nomenclature__icontains=q),
            nomenclature__startswith='2',
            stock_global__gt=0,
        ).select_related('unite').order_by('nomenclature')[:30])
        _annoter_produits_g2(produits)
    return render(request, 'partials/bsdg2_produit_search.html', {'produits': produits, 'q': q})


@login_required
def htmx_bsdg2_modal_produits(request):
    q = request.GET.get('q', '').strip()
    base_qs = Produit.objects.filter(
        nomenclature__startswith='2',
        stock_global__gt=0,
    ).select_related('unite').order_by('nomenclature')
    total_all = base_qs.count()
    if q:
        base_qs = base_qs.filter(Q(designation__icontains=q) | Q(nomenclature__icontains=q))
    produits = list(base_qs[:300])
    _annoter_produits_g2(produits)
    return render(request, 'partials/bsdg2_produit_modal_content.html', {
        'produits': produits, 'q': q, 'total_all': total_all
    })


# ─────────────────────────── BONS DE COMMANDE DE SERVICES ───────────────────────────
# Demande de sortie de matières de consommation (Groupe 2) formulée par un service.
# Distinct du bon de commande d'approvisionnement (BonEntree.num_bon_commande, achat fournisseur) :
# ici il s'agit de la consommation interne, validée par le chef de service Comptabilité des Matières.

@login_required
def bons_commande_service_list(request):
    bons = BonCommandeService.objects.select_related('service', 'bureau').order_by('-date_creation', '-num_bon')
    context = {
        'page_title': "Bons de commande de services",
        'bons': bons,
        'nb_a_valider': bons.filter(statut='envoye').count(),
    }
    return render(request, 'bons/commande_service_list.html', context)


@login_required
def bon_commande_service_create(request):
    services = Service.objects.filter(actif=True).order_by('code')
    if request.method == 'POST':
        num_bon = request.POST.get('num_bon', '').strip()
        date_creation = request.POST.get('date_creation') or date.today().isoformat()
        annee = request.POST.get('annee_exercice') or date.today().year
        service_id = request.POST.get('service_id') or None
        bureau_id = request.POST.get('bureau_id') or None
        destinataire = request.POST.get('destinataire', '').strip()
        demande_par = request.POST.get('demande_par', '').strip()
        observation = request.POST.get('observation', '').strip()
        try:
            lignes = json.loads(request.POST.get('details_json') or '[]')
        except (ValueError, TypeError):
            lignes = []
        if num_bon:
            with transaction.atomic():
                bon = BonCommandeService.objects.create(
                    num_bon=int(num_bon),
                    date_creation=date_creation,
                    annee_exercice=int(annee) if annee else None,
                    service_id=service_id,
                    bureau_id=bureau_id,
                    destinataire=destinataire,
                    demande_par=demande_par,
                    observation=observation,
                )
                for ligne in lignes:
                    designation = (ligne.get('designation') or '').strip()
                    if not designation:
                        continue
                    try:
                        qte = int(ligne.get('qte_commandee') or 0)
                    except (ValueError, TypeError):
                        qte = 0
                    DetailBonCommandeService.objects.create(
                        bon_commande=bon,
                        produit_id=ligne.get('produit_id') or None,
                        designation=designation,
                        nomenclature=(ligne.get('nomenclature') or '').strip(),
                        specification=(ligne.get('specification') or '').strip(),
                        qte_commandee=qte,
                        unite_id=ligne.get('unite_id') or None,
                    )
            nb = bon.details.count()
            messages.success(request, f"BCS-{bon.num_bon:04d} créé avec {nb} article{'s' if nb != 1 else ''}.")
            return redirect('matieres:bon_commande_service_update', pk=bon.pk)
    context = {
        'page_title': "Nouveau bon de commande de service",
        'services': services,
        'today': date.today(),
        'next_num': (BonCommandeService.objects.order_by('-num_bon').values_list('num_bon', flat=True).first() or 0) + 1,
    }
    return render(request, 'bons/commande_service_form.html', context)


@login_required
def bon_commande_service_update(request, pk):
    bon = get_object_or_404(BonCommandeService, pk=pk)
    services = Service.objects.filter(actif=True).order_by('code')
    editable = bon.statut in ('brouillon', 'rejete')
    if request.method == 'POST' and editable:
        bon.date_creation = request.POST.get('date_creation') or bon.date_creation
        bon.annee_exercice = request.POST.get('annee_exercice') or bon.annee_exercice
        bon.service_id = request.POST.get('service_id') or bon.service_id
        bon.bureau_id = request.POST.get('bureau_id') or bon.bureau_id
        bon.destinataire = request.POST.get('destinataire', bon.destinataire)
        bon.demande_par = request.POST.get('demande_par', bon.demande_par)
        bon.observation = request.POST.get('observation', bon.observation)
        if bon.statut == 'rejete':
            bon.statut = 'brouillon'
            bon.motif_rejet = ''
        bon.save()
        messages.success(request, "En-tête mis à jour.")
        return redirect('matieres:bon_commande_service_update', pk=pk)

    bureaux = Bureau.objects.filter(service_id=bon.service_id, actif=True).order_by('code') if bon.service_id else Bureau.objects.none()
    context = {
        'page_title': f"Bon de commande de service BCS-{bon.num_bon:04d}",
        'bon': bon,
        'editable': editable,
        'details': bon.details.select_related('produit', 'unite').all(),
        'services': services,
        'bureaux': bureaux,
    }
    return render(request, 'bons/commande_service_update.html', context)


@login_required
def bon_commande_service_etat(request, pk):
    bon = get_object_or_404(BonCommandeService, pk=pk)
    context = {
        'bon': bon,
        'details': bon.details.all(),
        'societe': SocieteGCS.objects.first(),
    }
    return render(request, 'bons/commande_service_etat.html', context)


@login_required
def bon_commande_service_envoyer(request, pk):
    bon = get_object_or_404(BonCommandeService, pk=pk)
    if request.method == 'POST' and bon.statut in ('brouillon', 'rejete'):
        if not bon.details.exists():
            messages.error(request, "Ajoutez au moins un article avant d'envoyer ce bon.")
        else:
            bon.statut = 'envoye'
            bon.date_envoi = date.today()
            bon.motif_rejet = ''
            bon.save(update_fields=['statut', 'date_envoi', 'motif_rejet'])
            messages.success(request, f"BCS-{bon.num_bon:04d} envoyé pour validation.")
    return redirect('matieres:bon_commande_service_update', pk=pk)


@login_required
def bon_commande_service_valider(request, pk):
    bon = get_object_or_404(BonCommandeService, pk=pk)
    if request.method == 'POST' and bon.statut == 'envoye':
        bon.statut = 'valide'
        bon.date_validation = date.today()
        bon.valide_par = request.POST.get('valide_par', '').strip() or request.user.get_full_name() or request.user.username
        bon.save(update_fields=['statut', 'date_validation', 'valide_par'])
        messages.success(request, f"BCS-{bon.num_bon:04d} validé.")
    return redirect('matieres:bon_commande_service_update', pk=pk)


@login_required
def bon_commande_service_rejeter(request, pk):
    bon = get_object_or_404(BonCommandeService, pk=pk)
    if request.method == 'POST' and bon.statut == 'envoye':
        bon.statut = 'rejete'
        bon.motif_rejet = request.POST.get('motif_rejet', '')
        bon.save(update_fields=['statut', 'motif_rejet'])
        messages.warning(request, f"BCS-{bon.num_bon:04d} rejeté.")
    return redirect('matieres:bon_commande_service_update', pk=pk)


@login_required
def htmx_bcs_add_detail(request, pk):
    bon = get_object_or_404(BonCommandeService, pk=pk)
    if request.method == 'POST' and bon.statut in ('brouillon', 'rejete'):
        designation = request.POST.get('designation', '').strip()
        if designation:
            produit_id = request.POST.get('produit_id') or None
            nomenclature = request.POST.get('nomenclature', '').strip()
            specification = request.POST.get('specification', '').strip()
            qte_commandee = int(request.POST.get('qte_commandee') or 0)
            unite_id = request.POST.get('unite_id') or None
            DetailBonCommandeService.objects.create(
                bon_commande=bon,
                produit_id=produit_id,
                designation=designation,
                nomenclature=nomenclature,
                specification=specification,
                qte_commandee=qte_commandee,
                unite_id=unite_id,
            )
    details = bon.details.select_related('produit', 'unite').all()
    return render(request, 'partials/bcs_detail_rows.html', {'details': details, 'bon': bon})


@login_required
def htmx_bcs_delete_detail(request, detail_pk):
    detail = get_object_or_404(DetailBonCommandeService, pk=detail_pk)
    bon = detail.bon_commande
    if bon.statut in ('brouillon', 'rejete'):
        detail.delete()
    details = bon.details.select_related('produit', 'unite').all()
    return render(request, 'partials/bcs_detail_rows.html', {'details': details, 'bon': bon})


@login_required
def htmx_bcs_produit_search(request):
    q = request.GET.get('q', '').strip()
    produits = []
    if len(q) >= 1:
        produits = list(Produit.objects.filter(
            Q(designation__icontains=q) | Q(nomenclature__icontains=q),
            nomenclature__startswith='2',
        ).select_related('unite').order_by('nomenclature')[:30])
    return render(request, 'partials/bcs_produit_search.html', {'produits': produits})


@login_required
def htmx_bcs_modal_produits(request):
    q = request.GET.get('q', '').strip()
    base_qs = Produit.objects.filter(nomenclature__startswith='2').select_related('unite').order_by('nomenclature')
    total_all = base_qs.count()
    if q:
        base_qs = base_qs.filter(Q(designation__icontains=q) | Q(nomenclature__icontains=q))
    produits = list(base_qs[:300])
    return render(request, 'partials/bcs_produit_modal_content.html', {
        'produits': produits, 'q': q, 'total_all': total_all,
    })


@login_required
def htmx_bcs_lignes(request):
    """Service/bureau + lignes disponibles (qte_restante > 0) d'un BCS validé, pour
    l'auto-chargement dans le formulaire de Bon de Sortie Définitive Groupe 2."""
    bcs_id = request.GET.get('bon_commande_service_id') or None
    bon = BonCommandeService.objects.filter(pk=bcs_id, statut='valide').first() if bcs_id else None
    lignes = [d for d in bon.details.select_related('produit', 'unite').all() if d.qte_restante > 0] if bon else []
    return render(request, 'partials/bcs_lignes_disponibles.html', {'bon': bon, 'lignes': lignes})


# ─────────────────────────── JOURNAL ───────────────────────────

def _journal_state_rows(qs):
    rows = []
    for j in qs:
        segments = (j.nomenclature or '').split('.')
        groupe = segments[0][0] if segments and segments[0] else ''
        compte_principal = segments[0] if len(segments) >= 1 else ''
        compte_secondaire = segments[1] if len(segments) >= 2 else ''
        compte_divisionnaire = segments[2] if len(segments) >= 3 else ''
        sous_compte = '.'.join(segments[:4]) if len(segments) >= 4 else '.'.join(segments) if segments else ''
        qte_entree = j.entree_periode or 0
        qte_sortie = j.sortie_periode or 0
        prix = j.prix_ttc or 0
        rows.append({
            'date': j.date_creation,
            'num_bon_entree': j.num_bon,
            'num_bon_sortie': j.num_bon_sortie or j.num_bon,
            'groupe': groupe,
            'compte_principal': compte_principal,
            'compte_secondaire': compte_secondaire,
            'compte_divisionnaire': compte_divisionnaire,
            'sous_compte': sous_compte,
            'designation': j.designation,
            'nature_matiere': j.specification or j.unite or '',
            'qte_entree': qte_entree,
            'qte_sortie': qte_sortie,
            'nature_unite_entree': j.unite or '',
            'nature_unite_sortie': j.unite or '',
            'prix_unitaire': prix,
            'montant_entree': qte_entree * prix,
            'montant_sortie': qte_sortie * prix,
            'qte_sp': j.qte_sp or 0,
            'observation': j.observation,
            'service_ou_bureau': j.bureau or j.service or '',
            'depot': j.depot or '',
        })
    return rows


@login_required
def journal_list(request):
    query   = request.GET.get('q', '')
    type_op = request.GET.get('type', '')
    depot   = request.GET.get('depot', '')
    groupe  = request.GET.get('groupe', '')
    annee   = request.GET.get('annee', '')

    qs = Journal.objects.order_by('-date_creation', '-num_bon', '-id')
    if query:
        qs = qs.filter(
            Q(designation__icontains=query) | Q(nomenclature__icontains=query) |
            Q(beneficiaire__icontains=query) | Q(specification__icontains=query) |
            Q(service__icontains=query) | Q(bureau__icontains=query)
        )
    if type_op:
        qs = qs.filter(type_entree=type_op)
    if depot:
        qs = qs.filter(depot=depot)
    if groupe:
        qs = qs.filter(groupe=groupe)
    if annee:
        qs = qs.filter(annee_exercice=annee)

    total = qs.count()
    context = {
        'page_title': 'Journal des opérations',
        'journal': qs[:500],
        'types':  Journal.objects.values_list('type_entree', flat=True).distinct().order_by('type_entree'),
        'depots': Journal.objects.exclude(depot='').values_list('depot', flat=True).distinct().order_by('depot'),
        'annees': Journal.objects.exclude(annee_exercice=None).values_list('annee_exercice', flat=True).distinct().order_by('-annee_exercice'),
        'query': query, 'type_op': type_op, 'depot': depot, 'groupe': groupe, 'annee': annee,
        'total': total,
    }
    return render(request, 'journal/list.html', context)


@login_required
def journal_etat(request):
    query   = request.GET.get('q', '')
    type_op = request.GET.get('type', '')
    depot   = request.GET.get('depot', '')
    groupe  = request.GET.get('groupe', '')
    annee   = request.GET.get('annee', '')

    qs = Journal.objects.order_by('date_creation', 'num_bon', 'id')
    if query:
        qs = qs.filter(
            Q(designation__icontains=query) | Q(nomenclature__icontains=query) |
            Q(beneficiaire__icontains=query) | Q(specification__icontains=query) |
            Q(service__icontains=query) | Q(bureau__icontains=query)
        )
    if type_op:
        qs = qs.filter(type_entree=type_op)
    if depot:
        qs = qs.filter(depot=depot)
    if groupe:
        qs = qs.filter(groupe=groupe)
    if annee:
        qs = qs.filter(annee_exercice=annee)

    journal_rows = _journal_state_rows(qs[:500])
    totaux = {
        'total_entrees': sum(row['qte_entree'] for row in journal_rows),
        'total_sorties': sum(row['qte_sortie'] for row in journal_rows),
        'total_montant_entree': sum(row['montant_entree'] for row in journal_rows),
        'total_montant_sortie': sum(row['montant_sortie'] for row in journal_rows),
        'total_qte_sp': sum(row['qte_sp'] for row in journal_rows),
    }

    context = {
        'page_title': 'État — Livre Journal des Matières',
        'societe': SocieteGCS.objects.first(),
        'journal': journal_rows,
        'query': query,
        'type_op': type_op,
        'depot': depot,
        'groupe': groupe,
        'annee': annee,
        'totaux': totaux,
        'total': qs.count(),
    }
    return render(request, 'journal/journal_etat.html', context)


# ─────────────────────────── BALANCE ───────────────────────────

def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


# Mouvements internes (n'affectent pas l'existant global, seulement sa répartition
# entre bureaux/états) — tout type_entree HORS de cette liste et hors 'Sortie Définitive'
# est traité comme une vraie entrée (Bon d'Entrée, quel que soit le libellé configuré).
_TYPES_AFFECTATION = 'Affectation'
_TYPES_RETOUR_AFFECTATION = 'Retour Affectation'
_TYPES_SORTIE_PROV = 'Sortie Provisoire'
_TYPES_RETOUR_SORTIE_PROV = 'Retour Sortie Provisoire'
_TYPES_MUTATION = 'Mutation'
_TYPES_SORTIE_DEF = 'Sortie Définitive'
_TYPES_INTERNES = {_TYPES_AFFECTATION, _TYPES_RETOUR_AFFECTATION, _TYPES_SORTIE_PROV,
                   _TYPES_RETOUR_SORTIE_PROV, _TYPES_MUTATION}


def _calculer_balance_periodique(date_debut, date_fin):
    """Reconstitue, pour chaque nomenclature, la Balance Générale des Comptes (Modèle N°22)
    sur l'intervalle [date_debut, date_fin] à partir du Journal — seule source de vérité.

    - Existant début/fin de gestion : ne bouge qu'avec les vraies entrées (Bon d'Entrée)
      et les sorties définitives — jamais avec l'affectation, la sortie provisoire ou la mutation.
    - Répartition « en fin de gestion » (attente d'affectation / en service / en sortie
      provisoire) : reconstituée en rejouant tout l'historique jusqu'à date_fin, exactement
      comme les compteurs stock_global / qte_affectation / qte_sp le font en temps réel.
    """
    par_nomenclature = {}
    for j in Journal.objects.all().order_by('nomenclature', 'date_creation', 'id'):
        par_nomenclature.setdefault(j.nomenclature, []).append(j)

    lignes = []
    for nomenclature, mouvements in par_nomenclature.items():
        if date_fin:
            mouvements = [j for j in mouvements if not j.date_creation or j.date_creation <= date_fin]
        if not mouvements:
            continue

        existant = 0
        en_service = 0
        en_sortie_prov = 0
        existant_debut = 0
        entree_periode = 0
        sortie_def_periode = 0
        dernier_prix = 0
        debut_marque = date_debut is None

        for j in mouvements:
            if not debut_marque and j.date_creation and j.date_creation >= date_debut:
                existant_debut = existant
                debut_marque = True

            dans_periode = (
                (not date_debut or not j.date_creation or j.date_creation >= date_debut)
                and (not date_fin or not j.date_creation or j.date_creation <= date_fin)
            )
            e = j.entree_periode or 0
            s = j.sortie_periode or 0
            t = j.type_entree

            if t == _TYPES_AFFECTATION:
                en_service += s
            elif t == _TYPES_RETOUR_AFFECTATION:
                en_service -= e
            elif t == _TYPES_SORTIE_PROV:
                en_service -= s
                en_sortie_prov += s
            elif t == _TYPES_RETOUR_SORTIE_PROV:
                en_sortie_prov -= e
                en_service += e
            elif t == _TYPES_MUTATION:
                pass
            elif t == _TYPES_SORTIE_DEF:
                existant -= s
                if dans_periode:
                    sortie_def_periode += s
            else:
                existant += e
                if dans_periode:
                    entree_periode += e

            if j.prix_ttc:
                dernier_prix = j.prix_ttc

        if not debut_marque:
            # Aucun mouvement n'a atteint date_debut : tout l'historique (déjà borné à
            # date_fin) est antérieur à la période -> l'existant accumulé EST l'existant début.
            existant_debut = existant

        total_entrees = existant_debut + entree_periode
        existant_fin = existant_debut + entree_periode - sortie_def_periode
        en_attente = max(0, existant_fin - en_service - en_sortie_prov)

        lignes.append({
            'nomenclature': nomenclature,
            'designation': mouvements[0].designation,
            'unite': mouvements[0].unite,
            'existant_debut': existant_debut,
            'entree_periode': entree_periode,
            'total_entrees': total_entrees,
            'sortie_def_periode': sortie_def_periode,
            'en_attente_affectation': en_attente,
            'en_service': max(0, en_service),
            'en_sortie_provisoire': max(0, en_sortie_prov),
            'existant_fin': existant_fin,
            'prix_unitaire': dernier_prix,
            'montant_existant': existant_fin * dernier_prix,
        })

    lignes.sort(key=lambda b: b['nomenclature'])
    return lignes


def _calculer_releve_recapitulatif(date_limite, groupe='1'):
    qs = Journal.objects.order_by('nomenclature', 'date_creation', 'id')
    if groupe:
        qs = qs.filter(groupe=groupe)
    if date_limite:
        qs = qs.filter(Q(date_creation__lte=date_limite) | Q(date_creation__isnull=True))

    par_nomenclature = {}
    for j in qs:
        par_nomenclature.setdefault(j.nomenclature, []).append(j)

    lignes = []
    for nomenclature, mouvements in par_nomenclature.items():
        existant = 0
        en_service = 0
        en_sortie_prov = 0
        dernier_prix = 0

        for j in mouvements:
            e = j.entree_periode or 0
            s = j.sortie_periode or 0
            t = j.type_entree

            if t == _TYPES_AFFECTATION:
                en_service += s
            elif t == _TYPES_RETOUR_AFFECTATION:
                en_service -= e
            elif t == _TYPES_SORTIE_PROV:
                en_service -= s
                en_sortie_prov += s
            elif t == _TYPES_RETOUR_SORTIE_PROV:
                en_sortie_prov -= e
                en_service += e
            elif t == _TYPES_MUTATION:
                pass
            elif t == _TYPES_SORTIE_DEF:
                existant -= s
            else:
                existant += e

            if j.prix_ttc:
                dernier_prix = j.prix_ttc

        en_attente = max(0, existant - en_service - en_sortie_prov)
        segments = nomenclature.split('.') if nomenclature else []

        lignes.append({
            'nomenclature': nomenclature,
            'designation': mouvements[0].designation,
            'groupe': segments[0][0] if segments and segments[0] else '',
            'compte_principal': segments[0] if len(segments) >= 1 else '',
            'compte_secondaire': segments[1] if len(segments) >= 2 else '',
            'compte_divisionnaire': segments[2] if len(segments) >= 3 else '',
            'sous_compte': '.'.join(segments[:4]) if len(segments) >= 4 else '.'.join(segments),
            'qte_attente': en_attente,
            'qte_service': max(0, en_service),
            'qte_sortie': max(0, en_sortie_prov),
            'total': existant,
            'prix_total': existant * dernier_prix,
            'observation': '',
        })

    lignes.sort(key=lambda b: b['nomenclature'] or '')
    return lignes


def _balance_list_context(request, report_kind):
    date_debut = _parse_date(request.GET.get('date_debut', ''))
    date_fin = _parse_date(request.GET.get('date_fin', ''))

    balances = _calculer_balance_periodique(date_debut, date_fin)

    totaux = {
        'total_existant_debut': sum(b['existant_debut'] for b in balances),
        'total_entrees': sum(b['entree_periode'] for b in balances),
        'total_sorties_def': sum(b['sortie_def_periode'] for b in balances),
        'total_en_attente': sum(b['en_attente_affectation'] for b in balances),
        'total_en_service': sum(b['en_service'] for b in balances),
        'total_en_sortie_prov': sum(b['en_sortie_provisoire'] for b in balances),
        'total_fin': sum(b['existant_fin'] for b in balances),
        'total_montant': sum(b['montant_existant'] for b in balances),
    }
    return {
        'balances': balances,
        'date_debut': request.GET.get('date_debut', ''),
        'date_fin': request.GET.get('date_fin', ''),
        'totaux': totaux,
        'report_kind': report_kind,
    }


@login_required
def balance_list(request):
    """Balance Générale des Comptes (Modèle N°22), calculée en direct depuis le Journal —
    comme le Grand Livre et la Fiche de Stock, bornée par un intervalle de dates précis."""
    context = _balance_list_context(request, 'general')
    context['page_title'] = 'Balance générale des comptes'
    return render(request, 'balance/list.html', context)


@login_required
def balance_periodique_list(request):
    """Balance périodique des comptes, calculée avec le même moteur que la balance générale."""
    context = _balance_list_context(request, 'periodique')
    context['page_title'] = 'Balance périodique des comptes'
    return render(request, 'balance/list.html', context)


@login_required
def balance_general_etat(request):
    """État officiel imprimable — Balance Générale des Comptes."""
    date_debut = _parse_date(request.GET.get('date_debut', ''))
    date_fin = _parse_date(request.GET.get('date_fin', ''))
    balances = _calculer_balance_periodique(date_debut, date_fin)
    for b in balances:
        segments = b['nomenclature'].split('.') if b['nomenclature'] else []
        b['groupe_disp'] = segments[0][0] if segments and segments[0] else ''
        b['compte_principal_disp'] = segments[0] if len(segments) >= 1 else ''
        b['sous_compte_disp'] = '.'.join(segments[:2]) if len(segments) >= 2 else ''

    totaux = {
        'total_existant_debut': sum(b['existant_debut'] for b in balances),
        'total_entrees': sum(b['entree_periode'] for b in balances),
        'total_sorties_def': sum(b['sortie_def_periode'] for b in balances),
        'total_en_attente': sum(b['en_attente_affectation'] for b in balances),
        'total_en_service': sum(b['en_service'] for b in balances),
        'total_en_sortie_prov': sum(b['en_sortie_provisoire'] for b in balances),
        'total_fin': sum(b['existant_fin'] for b in balances),
        'total_montant': sum(b['montant_existant'] for b in balances),
    }

    context = {
        'page_title': 'État — Balance Générale des Comptes',
        'societe': SocieteGCS.objects.first(),
        'date_debut': date_debut,
        'date_fin': date_fin,
        'balances': balances,
        'totaux': totaux,
    }
    return render(request, 'balance/balance_etat.html', context)


@login_required
def balance_periodique_etat(request):
    """État officiel imprimable — Balance Périodique des Comptes."""
    date_debut = _parse_date(request.GET.get('date_debut', ''))
    date_fin = _parse_date(request.GET.get('date_fin', ''))
    balances = _calculer_balance_periodique(date_debut, date_fin)
    for b in balances:
        segments = b['nomenclature'].split('.') if b['nomenclature'] else []
        b['groupe_disp'] = segments[0][0] if segments and segments[0] else ''
        b['compte_principal_disp'] = segments[0] if len(segments) >= 1 else ''
        b['sous_compte_disp'] = '.'.join(segments[:2]) if len(segments) >= 2 else ''

    totaux = {
        'total_existant_debut': sum(b['existant_debut'] for b in balances),
        'total_entrees': sum(b['entree_periode'] for b in balances),
        'total_sorties_def': sum(b['sortie_def_periode'] for b in balances),
        'total_en_attente': sum(b['en_attente_affectation'] for b in balances),
        'total_en_service': sum(b['en_service'] for b in balances),
        'total_en_sortie_prov': sum(b['en_sortie_provisoire'] for b in balances),
        'total_fin': sum(b['existant_fin'] for b in balances),
        'total_montant': sum(b['montant_existant'] for b in balances),
    }

    context = {
        'page_title': 'État — Balance Périodique des Comptes',
        'societe': SocieteGCS.objects.first(),
        'date_debut': date_debut,
        'date_fin': date_fin,
        'balances': balances,
        'totaux': totaux,
    }
    return render(request, 'balance/balanceP_etat.html', context)


# ─────────────────────────── RÉFÉRENTIELS ───────────────────────────

@login_required
def fournisseurs_list(request):
    context = {'page_title': 'Fournisseurs', 'fournisseurs': Fournisseur.objects.order_by('nom')}
    return render(request, 'referentiels/fournisseurs.html', context)


@login_required
def beneficiaires_list(request):
    beneficiaires = Beneficiaire.objects.select_related('bureau__service').order_by('nom')
    context = {
        'page_title': 'Bénéficiaires',
        'beneficiaires': beneficiaires,
        'services': Service.objects.filter(actif=True).order_by('code'),
    }
    return render(request, 'referentiels/beneficiaires.html', context)


@login_required
def beneficiaire_create(request):
    if request.method == 'POST':
        nom         = request.POST.get('nom', '').strip()
        responsable = request.POST.get('responsable', '').strip()
        bureau_id   = request.POST.get('bureau_id') or None
        if nom:
            Beneficiaire.objects.create(nom=nom, responsable=responsable, bureau_id=bureau_id)
            messages.success(request, f"Bénéficiaire « {nom} » créé.")
        else:
            messages.error(request, "Le nom est obligatoire.")
    return redirect('matieres:beneficiaires_list')


@login_required
def beneficiaire_update(request, pk):
    b = get_object_or_404(Beneficiaire, pk=pk)
    if request.method == 'POST':
        b.nom         = request.POST.get('nom', b.nom).strip()
        b.responsable = request.POST.get('responsable', '').strip()
        b.bureau_id   = request.POST.get('bureau_id') or None
        b.save()
        messages.success(request, f"Bénéficiaire mis à jour.")
    return redirect('matieres:beneficiaires_list')


@login_required
def beneficiaire_delete(request, pk):
    b = get_object_or_404(Beneficiaire, pk=pk)
    if request.method == 'POST':
        nom = b.nom
        b.delete()
        messages.success(request, f"Bénéficiaire « {nom} » supprimé.")
    return redirect('matieres:beneficiaires_list')


# ═══════════════════════════ SERVICES ════════════════════════════

@login_required
def service_list(request):
    services = Service.objects.prefetch_related('bureaux').order_by('code')
    context = {'page_title': 'Services', 'services': services}
    return render(request, 'referentiels/services.html', context)


@login_required
def service_create(request):
    if request.method == 'POST':
        code    = request.POST.get('code', '').strip().upper()
        libelle = request.POST.get('libelle', '').strip()
        if not code or not libelle:
            messages.error(request, "Code et libellé obligatoires.")
        elif Service.objects.filter(code=code).exists():
            messages.error(request, f"Le code « {code} » existe déjà.")
        else:
            Service.objects.create(
                code=code, libelle=libelle,
                responsable=request.POST.get('responsable', '').strip(),
                telephone=request.POST.get('telephone', '').strip(),
            )
            messages.success(request, f"Service « {code} » créé.")
    return redirect('matieres:service_list')


@login_required
def service_update(request, pk):
    s = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        if code and Service.objects.filter(code=code).exclude(pk=pk).exists():
            messages.error(request, f"Le code « {code} » est déjà utilisé.")
        else:
            s.code        = code or s.code
            s.libelle     = request.POST.get('libelle', s.libelle).strip()
            s.responsable = request.POST.get('responsable', '').strip()
            s.telephone   = request.POST.get('telephone', '').strip()
            s.actif       = request.POST.get('actif') == 'on'
            s.save()
            messages.success(request, "Service mis à jour.")
    return redirect('matieres:service_list')


@login_required
def service_delete(request, pk):
    s = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        if s.bureaux.exists():
            messages.error(request, f"Impossible : le service « {s.code} » contient des bureaux.")
        else:
            s.delete()
            messages.success(request, f"Service supprimé.")
    return redirect('matieres:service_list')


# ═══════════════════════════ BUREAUX ═════════════════════════════

@login_required
def bureau_list(request):
    bureaux = Bureau.objects.select_related('service').order_by('service__code', 'code')
    services = Service.objects.filter(actif=True).order_by('code')
    context = {'page_title': 'Bureaux', 'bureaux': bureaux, 'services': services}
    return render(request, 'referentiels/bureaux.html', context)


@login_required
def bureau_create(request):
    if request.method == 'POST':
        service_id = request.POST.get('service_id') or None
        code       = request.POST.get('code', '').strip().upper()
        libelle    = request.POST.get('libelle', '').strip()
        if not service_id or not code or not libelle:
            messages.error(request, "Service, code et libellé sont obligatoires.")
        elif Bureau.objects.filter(service_id=service_id, code=code).exists():
            messages.error(request, f"Le code « {code} » existe déjà dans ce service.")
        else:
            Bureau.objects.create(
                service_id=service_id, code=code, libelle=libelle,
                responsable=request.POST.get('responsable', '').strip(),
            )
            messages.success(request, f"Bureau « {code} » créé.")
    return redirect('matieres:bureau_list')


@login_required
def bureau_update(request, pk):
    b = get_object_or_404(Bureau, pk=pk)
    if request.method == 'POST':
        service_id = request.POST.get('service_id') or b.service_id
        code = request.POST.get('code', '').strip().upper()
        if code and Bureau.objects.filter(service_id=service_id, code=code).exclude(pk=pk).exists():
            messages.error(request, f"Le code « {code} » existe déjà dans ce service.")
        else:
            b.service_id  = service_id
            b.code        = code or b.code
            b.libelle     = request.POST.get('libelle', b.libelle).strip()
            b.responsable = request.POST.get('responsable', '').strip()
            b.actif       = request.POST.get('actif') == 'on'
            b.save()
            messages.success(request, "Bureau mis à jour.")
    return redirect('matieres:bureau_list')


@login_required
def bureau_delete(request, pk):
    b = get_object_or_404(Bureau, pk=pk)
    if request.method == 'POST':
        if b.beneficiaires.exists():
            messages.error(request, f"Impossible : le bureau « {b.code} » a des bénéficiaires liés.")
        else:
            b.delete()
            messages.success(request, "Bureau supprimé.")
    return redirect('matieres:bureau_list')


# ── HTMX : liste de bureaux filtrée par service ──
@login_required
def htmx_bureaux_par_service(request, service_pk):
    bureaux = Bureau.objects.filter(service_id=service_pk, actif=True).order_by('code')
    return render(request, 'partials/bureaux_options.html', {'bureaux': bureaux})


@login_required
def htmx_bureaux_options(request):
    """Retourne les bureaux d'un service donné.

    Compatible avec les formulaires qui envoient `service_id` ainsi qu'avec
    les bordereaux de mutation qui transmettent `service_origine_id` ou
    `service_destination_id` via hx-include.
    """
    service_id = (
        request.GET.get('service_id')
        or request.GET.get('service_origine_id')
        or request.GET.get('service_destination_id')
        or None
    )
    bureaux = Bureau.objects.filter(service_id=service_id, actif=True).order_by('code') if service_id else Bureau.objects.none()
    return render(request, 'partials/bureaux_options.html', {'bureaux': bureaux})


# ─────────────────────────── HTMX ───────────────────────────

@login_required
def htmx_stats_bons(request):
    aujourd_hui = date.today()
    debut_mois = date(aujourd_hui.year, aujourd_hui.month, 1)
    return JsonResponse({
        'bons_entree': BonEntree.objects.filter(date_creation__gte=debut_mois).count(),
        'bons_affectation': BonAffectation.objects.filter(date_affectation__gte=debut_mois).count(),
        'bons_sortie_def': BonSortieDefinitive.objects.filter(date_creation__gte=debut_mois).count(),
    })


@login_required
def htmx_chart_data(request):
    aujourd_hui = date.today()
    mois_courant = aujourd_hui.month
    annee_courante = aujourd_hui.year
    labels, entrees, sorties = [], [], []
    mois_names = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
    for i in range(5, -1, -1):
        if mois_courant - i <= 0:
            mois = mois_courant - i + 12
            an = annee_courante - 1
        else:
            mois = mois_courant - i
            an = annee_courante
        debut = date(an, mois, 1)
        fin = date(an, mois + 1, 1) - timedelta(days=1) if mois < 12 else date(an + 1, 1, 1) - timedelta(days=1)
        labels.append(mois_names[mois - 1])
        entrees.append(BonEntree.objects.filter(date_creation__range=[debut, fin]).count())
        sorties.append(BonSortieDefinitive.objects.filter(date_creation__range=[debut, fin]).count())
    return JsonResponse({'labels': labels, 'entrees': entrees, 'sorties': sorties})


@login_required
def htmx_recherche_produit(request):
    q = request.GET.get('q', '')
    produits = []
    if len(q) >= 2:
        produits = list(
            Produit.objects.filter(Q(designation__icontains=q) | Q(nomenclature__icontains=q))
            .values('id', 'nomenclature', 'designation', 'stock_global')[:10]
        )
    return render(request, 'partials/recherche_produit.html', {'produits': produits, 'q': q})


# ─────────────────────────── IMPORT EXCEL ───────────────────────────

@login_required
def import_index(request):
    results = None

    if request.method == 'POST':
        fichier = request.FILES.get('fichier')
        if not fichier:
            messages.error(request, "Veuillez sélectionner un fichier Excel (.xlsx).")
        elif not fichier.name.lower().endswith('.xlsx'):
            messages.error(request, "Format non supporté. Utilisez un fichier .xlsx (Excel 2007+).")
        elif fichier.size > 20 * 1024 * 1024:
            messages.error(request, "Fichier trop volumineux (max 20 Mo).")
        else:
            try:
                results = process_excel(fichier)
                tot_created = sum(r['created'] for r in results if not r.get('skipped'))
                tot_updated = sum(r['updated'] for r in results if not r.get('skipped'))
                tot_errors  = sum(len(r['errors']) for r in results if not r.get('skipped'))
                if tot_errors == 0:
                    messages.success(request,
                        f"Import terminé avec succès — {tot_created} enregistrement(s) créé(s), "
                        f"{tot_updated} mis à jour.")
                else:
                    messages.warning(request,
                        f"Import terminé — {tot_created} créé(s), {tot_updated} mis à jour, "
                        f"{tot_errors} erreur(s) détectée(s). Consultez le rapport ci-dessous.")
            except Exception as exc:
                messages.error(request, f"Erreur lors du traitement du fichier : {exc}")

    return render(request, 'import/index.html', {
        'page_title': "Import de données",
        'results':    results,
        'importers':  IMPORTERS,
    })


@login_required
def import_template_download(request):
    buf = generate_template()
    response = HttpResponse(
        buf.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="template_import_gestmat.xlsx"'
    return response


# ─────────────────────────── STRUCTURE ───────────────────────────

@login_required
def compte_principal_list(request):
    query = request.GET.get('q', '')
    comptes = ComptePrincipale.objects.annotate(nb_sc=Count('sous_comptes'))
    if query:
        comptes = comptes.filter(Q(famille__icontains=query) | Q(num_compte__icontains=query))
    context = {
        'page_title': 'Comptes principaux',
        'comptes': comptes.order_by('num_compte'),
        'total': comptes.count(),
        'query': query,
    }
    return render(request, 'structure/comptes.html', context)


@login_required
def sous_compte_list(request):
    query = request.GET.get('q', '')
    compte_id = request.GET.get('compte', '')
    sous_comptes = SousCompte.objects.select_related('compte_principal')
    if query:
        criteria = (
            Q(compte__icontains=query)
            | Q(famille_sc__icontains=query)
            | Q(num_cb__icontains=query)
            | Q(intitule_cb__icontains=query)
            | Q(compte_principal__famille__icontains=query)
        )
        normalized = query.replace('.', '', 1)
        if normalized.isdigit():
            criteria |= Q(compte_principal__num_compte=float(query) if '.' in query else int(query))
        sous_comptes = sous_comptes.filter(criteria)
    if compte_id:
        sous_comptes = sous_comptes.filter(compte_principal_id=compte_id)
    context = {
        'page_title': 'Sous-comptes',
        'sous_comptes': sous_comptes.order_by('num_sous_compte'),
        'comptes': ComptePrincipale.objects.order_by('num_compte'),
        'compte_id': compte_id,
        'total': sous_comptes.count(),
        'query': query,
    }
    return render(request, 'structure/sous_comptes.html', context)


# ─────────────────────────── CONFIGURATION ───────────────────────────

@login_required
def societe_view(request):
    societe = SocieteGCS.objects.first()
    if request.method == 'POST':
        data = request.POST
        if societe:
            societe.nom = data.get('nom', societe.nom)
            societe.telephone = data.get('telephone', '')
            societe.email = data.get('email', '')
            societe.adresse = data.get('adresse', '')
            societe.fax = data.get('fax', '')
            societe.ministere = data.get('ministere', '')
            societe.administrateur = data.get('administrateur', '')
            societe.comptable = data.get('comptable', '')
            societe.receptionnaire = data.get('receptionnaire', '')
            societe.responsable = data.get('responsable', '')
            societe.ville = data.get('ville', '')
            if request.FILES.get('logo'):
                societe.logo = request.FILES['logo']
            societe.save()
            messages.success(request, "Informations société mises à jour.")
        else:
            societe = SocieteGCS.objects.create(
                nom=data.get('nom', ''), telephone=data.get('telephone', ''),
                email=data.get('email', ''), adresse=data.get('adresse', ''),
                fax=data.get('fax', ''), ministere=data.get('ministere', ''),
                administrateur=data.get('administrateur', ''), comptable=data.get('comptable', ''),
                receptionnaire=data.get('receptionnaire', ''), responsable=data.get('responsable', ''),
                ville=data.get('ville', ''),
            )
            if request.FILES.get('logo'):
                societe.logo = request.FILES['logo']
                societe.save()
            messages.success(request, "Société créée avec succès.")
        return redirect('matieres:societe_view')
    if request.GET.get('delete') and societe:
        societe.delete()
        messages.success(request, "Société supprimée.")
        return redirect('matieres:societe_view')
    return render(request, 'configuration/societe.html', {'page_title': 'Société GCS', 'societe': societe})


@login_required
def unite_list(request):
    editing = None
    if request.method == 'POST':
        pk = request.POST.get('pk', '').strip()
        libelle = request.POST.get('libelle', '').strip()
        if pk:
            obj = get_object_or_404(Unite, pk=pk)
            if Unite.objects.filter(libelle=libelle).exclude(pk=pk).exists():
                messages.error(request, "Cette unité existe déjà.")
            elif libelle:
                obj.libelle = libelle
                obj.save()
                messages.success(request, "Unité mise à jour.")
        elif libelle:
            if Unite.objects.filter(libelle=libelle).exists():
                messages.error(request, "Cette unité existe déjà.")
            else:
                Unite.objects.create(libelle=libelle)
                messages.success(request, f"Unité « {libelle} » créée.")
        return redirect('matieres:unite_list')
    if request.GET.get('edit'):
        editing = get_object_or_404(Unite, pk=request.GET['edit'])
    if request.GET.get('delete'):
        obj = get_object_or_404(Unite, pk=request.GET['delete'])
        obj.delete()
        messages.success(request, "Unité supprimée.")
        return redirect('matieres:unite_list')
    unites = Unite.objects.annotate(nb=Count('produit')).order_by('libelle')
    return render(request, 'configuration/unites.html', {'page_title': 'Unités', 'unites': unites, 'editing': editing})


@login_required
def type_op_list(request):
    editing = None
    if request.method == 'POST':
        pk = request.POST.get('pk', '').strip()
        libelle = request.POST.get('libelle', '').strip()
        if pk:
            obj = get_object_or_404(TypeOperation, pk=pk)
            if TypeOperation.objects.filter(libelle=libelle).exclude(pk=pk).exists():
                messages.error(request, "Ce type existe déjà.")
            elif libelle:
                obj.libelle = libelle
                obj.save()
                messages.success(request, "Type mis à jour.")
        elif libelle:
            if TypeOperation.objects.filter(libelle=libelle).exists():
                messages.error(request, "Ce type existe déjà.")
            else:
                TypeOperation.objects.create(libelle=libelle)
                messages.success(request, f"Type « {libelle} » créé.")
        return redirect('matieres:type_op_list')
    if request.GET.get('edit'):
        editing = get_object_or_404(TypeOperation, pk=request.GET['edit'])
    if request.GET.get('delete'):
        obj = get_object_or_404(TypeOperation, pk=request.GET['delete'])
        obj.delete()
        messages.success(request, "Type supprimé.")
        return redirect('matieres:type_op_list')
    types = TypeOperation.objects.order_by('libelle')
    return render(request, 'configuration/type_operations.html', {'page_title': "Types d'opération", 'types': types, 'editing': editing})


@login_required
def membre_commission_list(request):
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        qualite = request.POST.get('qualite', '').strip()
        pk = request.POST.get('pk', '')
        if pk:
            obj = get_object_or_404(MembreCommission, pk=pk)
            obj.nom = nom; obj.qualite = qualite; obj.save()
            messages.success(request, "Membre mis à jour.")
        elif nom:
            MembreCommission.objects.create(nom=nom, qualite=qualite)
            messages.success(request, f"Membre « {nom} » ajouté.")
        return redirect('matieres:membre_commission_list')
    if request.GET.get('delete'):
        get_object_or_404(MembreCommission, pk=request.GET['delete']).delete()
        messages.success(request, "Membre supprimé.")
        return redirect('matieres:membre_commission_list')
    membres = MembreCommission.objects.order_by('nom')
    return render(request, 'configuration/membres_commission.html', {'page_title': 'Membres de commission', 'membres': membres})


@login_required
def membre_reforme_list(request):
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        qualite = request.POST.get('qualite', '').strip()
        pk = request.POST.get('pk', '')
        if pk:
            obj = get_object_or_404(MembreCommissionReforme, pk=pk)
            obj.nom = nom; obj.qualite = qualite; obj.save()
            messages.success(request, "Membre mis à jour.")
        elif nom:
            MembreCommissionReforme.objects.create(nom=nom, qualite=qualite)
            messages.success(request, f"Membre « {nom} » ajouté.")
        return redirect('matieres:membre_reforme_list')
    if request.GET.get('delete'):
        get_object_or_404(MembreCommissionReforme, pk=request.GET['delete']).delete()
        messages.success(request, "Membre supprimé.")
        return redirect('matieres:membre_reforme_list')
    membres = MembreCommissionReforme.objects.order_by('nom')
    return render(request, 'configuration/membres_reforme.html', {'page_title': 'Commission de réforme', 'membres': membres})


@login_required
def annee_exercice_list(request):
    if request.method == 'POST':
        annee = request.POST.get('annee', '').strip()
        dd = request.POST.get('date_debut', '')
        df = request.POST.get('date_fin', '')
        pk = request.POST.get('pk', '')
        if pk:
            obj = get_object_or_404(AnneeExercice, pk=pk)
            try:
                obj.annee = int(annee)
                if dd: obj.date_debut = dd
                if df: obj.date_fin = df
                obj.save()
                messages.success(request, "Année mise à jour.")
            except Exception as e:
                messages.error(request, str(e))
        elif annee:
            try:
                AnneeExercice.objects.create(annee=int(annee), date_debut=dd or date(int(annee), 1, 1), date_fin=df or date(int(annee), 12, 31))
                messages.success(request, f"Année {annee} créée.")
            except Exception as e:
                messages.error(request, str(e))
        return redirect('matieres:annee_exercice_list')
    if request.GET.get('delete'):
        get_object_or_404(AnneeExercice, pk=request.GET['delete']).delete()
        messages.success(request, "Année supprimée.")
        return redirect('matieres:annee_exercice_list')
    annees = AnneeExercice.objects.order_by('-annee')
    return render(request, 'configuration/annees.html', {'page_title': "Années d'exercice", 'annees': annees})


@login_required
def matieres_depot_config(request):
    editing = None
    if request.method == 'POST':
        pk = request.POST.get('pk', '').strip()
        depot_id = request.POST.get('depot', '')
        num_sc = request.POST.get('num_sous_compte', '').strip()
        if depot_id and num_sc:
            depot_obj = get_object_or_404(Depot, pk=depot_id)
            num_sc_value = int(num_sc)
            if pk:
                obj = get_object_or_404(MatieresDepot, pk=pk)
                if MatieresDepot.objects.filter(depot=depot_obj, num_sous_compte=num_sc_value).exclude(pk=pk).exists():
                    messages.error(request, "Ce lien dépôt/sous-compte existe déjà.")
                else:
                    obj.depot = depot_obj
                    obj.num_sous_compte = num_sc_value
                    obj.save()
                    messages.success(request, "Lien mis à jour.")
            else:
                if MatieresDepot.objects.filter(depot=depot_obj, num_sous_compte=num_sc_value).exists():
                    messages.error(request, "Ce lien dépôt/sous-compte existe déjà.")
                else:
                    MatieresDepot.objects.create(depot=depot_obj, num_sous_compte=num_sc_value)
                    messages.success(request, "Lien créé.")
        return redirect('matieres:matieres_depot_config')
    if request.GET.get('edit'):
        editing = get_object_or_404(MatieresDepot, pk=request.GET['edit'])
    if request.GET.get('delete'):
        get_object_or_404(MatieresDepot, pk=request.GET['delete']).delete()
        messages.success(request, "Lien supprimé.")
        return redirect('matieres:matieres_depot_config')
    liens = MatieresDepot.objects.select_related('depot').order_by('depot__code', 'num_sous_compte')
    return render(request, 'configuration/matieres_depot.html', {
        'page_title': 'Matières / Dépôt', 'liens': liens, 'depots': Depot.objects.all(), 'editing': editing,
    })


@login_required
def profil_list(request):
    editing = None
    if request.method == 'POST':
        pk = request.POST.get('pk', '').strip()
        role = request.POST.get('role', '').strip()
        if pk:
            obj = get_object_or_404(Profil, pk=pk)
            if Profil.objects.filter(role=role).exclude(pk=pk).exists():
                messages.error(request, "Ce profil existe déjà.")
            elif role:
                obj.role = role
                obj.save()
                messages.success(request, "Profil mis à jour.")
        elif role:
            if Profil.objects.filter(role=role).exists():
                messages.error(request, "Ce profil existe déjà.")
            else:
                Profil.objects.create(role=role)
                messages.success(request, f"Profil « {role} » créé.")
        return redirect('matieres:profil_list')
    if request.GET.get('edit'):
        editing = get_object_or_404(Profil, pk=request.GET['edit'])
    if request.GET.get('delete'):
        get_object_or_404(Profil, pk=request.GET['delete']).delete()
        messages.success(request, "Profil supprimé.")
        return redirect('matieres:profil_list')
    profils = Profil.objects.order_by('role')
    return render(request, 'configuration/profils.html', {'page_title': 'Profils', 'profils': profils, 'editing': editing})


# ─────────────────────────── ÉTATS / INVENTAIRES ───────────────────────────

@login_required
def inventaire_global(request):
    query = request.GET.get('q', '')
    compte_id = request.GET.get('compte', '')
    produits = Produit.objects.select_related('unite', 'compte_principal', 'sous_compte')
    if query:
        produits = produits.filter(Q(designation__icontains=query) | Q(nomenclature__icontains=query))
    if compte_id:
        produits = produits.filter(compte_principal_id=compte_id)
    totaux = produits.aggregate(
        total_stock=Sum('stock_global'),
        total_affectation=Sum('qte_affectation'),
        total_sp=Sum('qte_sp'),
        total_sd=Sum('qte_sd'),
    )
    context = {
        'page_title': 'Inventaire Global',
        'produits': produits.order_by('nomenclature'),
        'comptes': ComptePrincipale.objects.order_by('num_compte'),
        'compte_id': compte_id,
        'totaux': totaux,
        'total': produits.count(),
        'query': query,
    }
    return render(request, 'etats/inventaire_global.html', context)


@login_required
def inventaire_depot(request):
    depot_code = request.GET.get('depot', '')
    query = request.GET.get('q', '')
    depots = Depot.objects.all()
    stocks = StockDepot.objects.select_related('depot', 'produit__unite')
    if depot_code:
        stocks = stocks.filter(depot__code=depot_code)
    if query:
        stocks = stocks.filter(Q(designation__icontains=query) | Q(nomenclature__icontains=query))
    total_qte = stocks.aggregate(t=Sum('qte_stock'))['t'] or 0
    context = {
        'page_title': 'Inventaire par Dépôt',
        'stocks': stocks.order_by('depot__code', 'nomenclature'),
        'depots': depots,
        'depot_code': depot_code,
        'total_qte': total_qte,
        'total': stocks.count(),
        'query': query,
    }
    return render(request, 'etats/inventaire_depot.html', context)


@login_required
def releve_recapitulatif(request):
    date = _parse_date(request.GET.get('date', ''))
    balances = _calculer_releve_recapitulatif(date, groupe='1') if date else []
    totaux = {
        'total_attente': sum(b['qte_attente'] for b in balances),
        'total_service': sum(b['qte_service'] for b in balances),
        'total_sortie': sum(b['qte_sortie'] for b in balances),
        'total': sum(b['total'] for b in balances),
    }
    context = {
        'page_title': 'Relevé Récapitulatif des Matières',
        'societe': SocieteGCS.objects.first(),
        'balances': balances,
        'date': date,
        'date_str': request.GET.get('date', ''),
        'totaux': totaux,
        'total': len(balances),
    }
    return render(request, 'etats/releve_recapitulatif.html', context)


@login_required
def inventaire_individuel(request):
    query = request.GET.get('q', '')
    depot_code = request.GET.get('depot', '')
    produits = Produit.objects.select_related('unite', 'compte_principal')
    if query:
        produits = produits.filter(Q(designation__icontains=query) | Q(nomenclature__icontains=query))

    # Construction de la comparaison stock théorique vs physique (StockDepot)
    stock_depot_map = {}
    qs_sd = StockDepot.objects.select_related('depot')
    if depot_code:
        qs_sd = qs_sd.filter(depot__code=depot_code)
    for sd in qs_sd:
        stock_depot_map[sd.nomenclature] = stock_depot_map.get(sd.nomenclature, 0) + sd.qte_stock

    inventaire = []
    for p in produits.order_by('nomenclature')[:500]:
        stock_physique = stock_depot_map.get(p.nomenclature, 0)
        ecart = p.stock_global - stock_physique
        inventaire.append({
            'produit': p,
            'stock_theorique': p.stock_global,
            'stock_physique': stock_physique,
            'ecart': ecart,
            'ok': ecart == 0,
        })

    nb_ecarts = sum(1 for i in inventaire if not i['ok'])
    context = {
        'page_title': 'Inventaire Individuel Contradictoire',
        'inventaire': inventaire,
        'depots': Depot.objects.all(),
        'depot_code': depot_code,
        'nb_ecarts': nb_ecarts,
        'total': len(inventaire),
        'query': query,
    }
    return render(request, 'etats/inventaire_individuel.html', context)


@login_required
def inventaire_individuel_etat(request):
    query = request.GET.get('q', '')
    journal_qs = Journal.objects.filter(nomenclature__startswith='1')
    if query:
        journal_qs = journal_qs.filter(Q(designation__icontains=query) | Q(nomenclature__icontains=query))

    nomenclatures = list(journal_qs.values_list('nomenclature', flat=True).distinct())
    produits_qs = Produit.objects.select_related('unite', 'compte_principal', 'sous_compte')
    produits_qs = produits_qs.filter(nomenclature__in=nomenclatures)
    if query:
        produits_qs = produits_qs.filter(Q(designation__icontains=query) | Q(nomenclature__icontains=query))
    produits = list(produits_qs.order_by('nomenclature')[:500])

    lignes = []
    controle_mismatches = []
    controle_totals = {
        'total': len(produits),
        'stock_ok': 0,
        'service_ok': 0,
        'sortie_prov_ok': 0,
        'sortie_def_ok': 0,
        'journal_entries': 0,
    }

    for produit in produits:
        mouvements = Journal.objects.filter(nomenclature=produit.nomenclature).order_by('date_creation', 'id')
        journal_existant = 0
        journal_en_service = 0
        journal_en_sortie_prov = 0
        journal_sortie_def = 0
        premier_entree = None

        for j in mouvements:
            entree = j.entree_periode or 0
            sortie = j.sortie_periode or 0
            t = j.type_entree

            if t == _TYPES_AFFECTATION:
                journal_en_service += sortie
            elif t == _TYPES_RETOUR_AFFECTATION:
                journal_en_service -= entree
            elif t == _TYPES_SORTIE_PROV:
                journal_en_service -= sortie
                journal_en_sortie_prov += sortie
            elif t == _TYPES_RETOUR_SORTIE_PROV:
                journal_en_sortie_prov -= entree
                journal_en_service += entree
            elif t == _TYPES_MUTATION:
                pass
            elif t == _TYPES_SORTIE_DEF:
                journal_existant -= sortie
                journal_sortie_def += sortie
            else:
                journal_existant += entree
                if premier_entree is None:
                    premier_entree = j

        if premier_entree:
            bon_entree = f"{premier_entree.num_bon:04d}"
            annee_bud = premier_entree.annee_exercice or ''
        else:
            bon_entree = ''
            annee_bud = ''

        stock_ok = produit.stock_global == journal_existant
        service_ok = produit.qte_affectation == journal_en_service
        sortie_prov_ok = produit.qte_sp == journal_en_sortie_prov
        sortie_def_ok = produit.qte_sd == journal_sortie_def

        if stock_ok:
            controle_totals['stock_ok'] += 1
        if service_ok:
            controle_totals['service_ok'] += 1
        if sortie_prov_ok:
            controle_totals['sortie_prov_ok'] += 1
        if sortie_def_ok:
            controle_totals['sortie_def_ok'] += 1
        if mouvements.exists():
            controle_totals['journal_entries'] += 1

        if not (stock_ok and service_ok and sortie_prov_ok and sortie_def_ok and premier_entree):
            messages = []
            if not premier_entree:
                messages.append('Aucune entrée BE trouvée dans le Journal')
            if not stock_ok:
                messages.append(f"Stock global attendu {journal_existant} d'après le Journal")
            if not service_ok:
                messages.append(f"Qté affectée attendue {journal_en_service} d'après le Journal")
            if not sortie_prov_ok:
                messages.append(f"Qté sortie provisoire attendue {journal_en_sortie_prov} d'après le Journal")
            if not sortie_def_ok:
                messages.append(f"Qté sortie définitive attendue {journal_sortie_def} d'après le Journal")
            controle_mismatches.append({
                'nomenclature': produit.nomenclature,
                'designation': produit.designation,
                'messages': messages,
            })

        lignes.append({
            'produit': produit,
            'bon_entree': bon_entree,
            'annee_bud': annee_bud,
            'immatriculation': '',
            'journal_existant': journal_existant,
            'journal_en_service': journal_en_service,
            'journal_en_sortie_prov': journal_en_sortie_prov,
            'journal_sortie_def': journal_sortie_def,
            'controle_ok': stock_ok and service_ok and sortie_prov_ok and sortie_def_ok and premier_entree,
        })

    context = {
        'page_title': 'Fiche d\'Inventaire Individuel Contradictoire',
        'societe': SocieteGCS.objects.first(),
        'lignes': lignes,
        'query': query,
        'total': len(lignes),
        'controle_totals': controle_totals,
        'controle_mismatches': controle_mismatches,
    }
    return render(request, 'etats/inventaire_individuel_etat.html', context)


@login_required
def grand_livre(request):
    query = request.GET.get('q', '')
    type_op = request.GET.get('type', '')
    depot_f = request.GET.get('depot', '')
    annee_f = request.GET.get('annee', '')
    journal = Journal.objects.order_by('-date_creation', 'nomenclature')
    if query:
        journal = journal.filter(Q(designation__icontains=query) | Q(nomenclature__icontains=query))
    if type_op:
        journal = journal.filter(type_entree=type_op)
    if depot_f:
        journal = journal.filter(depot=depot_f)
    if annee_f:
        journal = journal.filter(annee_exercice=annee_f)
    types = Journal.objects.values_list('type_entree', flat=True).distinct()
    depots_j = Journal.objects.values_list('depot', flat=True).distinct()
    annees_j = Journal.objects.values_list('annee_exercice', flat=True).distinct().order_by('-annee_exercice')
    context = {
        'page_title': 'Grand Livre',
        'journal': journal,
        'types': types,
        'depots': depots_j,
        'annees': annees_j,
        'query': query,
        'type_op': type_op,
        'depot_f': depot_f,
        'annee_f': annee_f,
        'total': journal.count(),
    }
    return render(request, 'etats/grand_livre.html', context)


@login_required
def fiche_stock(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    stocks_depot = StockDepot.objects.filter(produit=produit).select_related('depot')
    mouvements = Journal.objects.filter(nomenclature=produit.nomenclature).order_by('date_creation', 'id')
    total_physique = stocks_depot.aggregate(t=Sum('qte_stock'))['t'] or 0
    context = {
        'page_title': f'Fiche de Stock — {produit.nomenclature}',
        'produit': produit,
        'stocks_depot': stocks_depot,
        'mouvements': mouvements,
        'total_physique': total_physique,
        'ecart': produit.stock_global - total_physique,
    }
    return render(request, 'etats/fiche_stock.html', context)


@login_required
def fiche_stock_etat(request, pk):
    """État officiel Modèle N°9 — fiche de casier chronologique (entrée/sortie/solde),
    valable pour les matières des deux groupes : le Journal trace déjà chaque type
    de mouvement avec entree_periode/sortie_periode correctement renseignés."""
    produit = get_object_or_404(Produit, pk=pk)
    mouvements = list(Journal.objects.filter(nomenclature=produit.nomenclature).order_by('date_creation', 'id'))

    solde_qte = 0
    lignes = []
    for j in mouvements:
        entree_qte = j.entree_periode or 0
        sortie_qte = j.sortie_periode or 0
        solde_qte += entree_qte - sortie_qte
        prix = j.prix_ttc or 0
        lignes.append({
            'date': j.date_creation,
            'num_bon': j.num_bon,
            'type_entree': j.type_entree,
            'observation': j.observation,
            'entree_qte': entree_qte if entree_qte else None,
            'entree_prix': prix if entree_qte else None,
            'entree_montant': (entree_qte * prix) if entree_qte else None,
            'sortie_qte': sortie_qte if sortie_qte else None,
            'sortie_prix': prix if sortie_qte else None,
            'sortie_montant': (sortie_qte * prix) if sortie_qte else None,
            'solde_qte': solde_qte,
            'solde_prix': prix,
            'solde_montant': solde_qte * prix,
        })

    context = {
        'page_title': f"État — Fiche de stock {produit.nomenclature}",
        'societe': SocieteGCS.objects.first(),
        'produit': produit,
        'lignes': lignes,
    }
    return render(request, 'etats/fiche_stock_etat.html', context)


@login_required
def grand_livre_compte_etat(request, nomenclature):
    """État officiel imprimable — Modèle N°12, Grand-Livre des Comptes.

    Un compte (= nomenclature) par page. Seuls les vrais mouvements du compte y figurent :
    Entrée et Sortie Définitive font bouger l'Existant ; la Sortie Provisoire et son retour
    ne sont que « pour mémoire » (ils ne modifient jamais l'Existant du compte, exactement
    comme dans la Balance Générale des Comptes) — l'Affectation, le Retour d'Affectation et
    la Mutation sont de purs mouvements internes entre bureaux et n'apparaissent pas ici.
    """
    produit = Produit.objects.filter(nomenclature=nomenclature).first()
    mouvements = list(Journal.objects.filter(nomenclature=nomenclature).order_by('date_creation', 'id'))

    existant = 0
    lignes = []
    for j in mouvements:
        t = j.type_entree
        if t in (_TYPES_AFFECTATION, _TYPES_RETOUR_AFFECTATION, _TYPES_MUTATION):
            continue

        entree = sortie_def = sortie_prov = None
        origine_destination = ''

        if t == _TYPES_SORTIE_DEF:
            sortie_def = j.sortie_periode or 0
            existant -= sortie_def
            origine_destination = f"{j.service or ''} {('/ ' + j.bureau) if j.bureau else ''}".strip() or j.type_entree
        elif t == _TYPES_SORTIE_PROV:
            sortie_prov = j.qte_sp or j.sortie_periode or 0
            origine_destination = f"{j.service or ''} {('/ ' + j.bureau) if j.bureau else ''}".strip() or j.type_entree
        elif t == _TYPES_RETOUR_SORTIE_PROV:
            origine_destination = f"Retour de {j.service or ''} {('/ ' + j.bureau) if j.bureau else ''}".strip()
        else:
            entree = j.entree_periode or 0
            existant += entree
            origine_destination = f"Dépôt {j.depot}" if j.depot else j.type_entree

        prix = j.prix_ttc or 0
        lignes.append({
            'date': j.date_creation,
            'num_bon': j.num_bon,
            'origine_destination': origine_destination,
            'entree': entree,
            'sortie_def': sortie_def,
            'prix_unitaire': prix,
            'existant': existant,
            'montant_existant': existant * prix,
            'sortie_prov': sortie_prov,
            'date_retour': j.date_retour if t == _TYPES_RETOUR_SORTIE_PROV else None,
        })

    context = {
        'page_title': f"État — Grand-Livre des Comptes {nomenclature}",
        'societe': SocieteGCS.objects.first(),
        'produit': produit,
        'nomenclature': nomenclature,
        'designation': produit.designation if produit else (mouvements[0].designation if mouvements else ''),
        'unite': produit.unite if produit else (mouvements[0].unite if mouvements else ''),
        'lignes': lignes,
    }
    return render(request, 'etats/grand_livre_etat.html', context)
