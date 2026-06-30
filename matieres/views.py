from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import JsonResponse, HttpResponse
from datetime import date, timedelta
from decimal import Decimal
import json

from .models import (
    Produit, Depot, StockDepot,
    BonEntree, DetailBonEntree,
    BonAffectation, DetailBonAffectation,
    BonRetourAffectation, DetailBonRetourAffectation,
    BonSortieProvisoire, DetailBonSortieProvisoire,
    BonRetourSortieProvisoire, DetailBonRetourSortieProvisoire,
    BonSortieDefinitive, BonSortieDefinitiveG1,
    Journal, BalancePeriodique,
    Fournisseur, Beneficiaire, AnneeExercice, SocieteGCS,
    ComptePrincipale, SousCompte, Unite, TypeOperation,
    MembreCommission, MembreCommissionReforme, MatieresDepot, Profil,
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
    bons = BonAffectation.objects.select_related('depot', 'beneficiaire').order_by('-date_affectation', '-num_bon')
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
    beneficiaires = Beneficiaire.objects.all().order_by('nom')
    annees = AnneeExercice.objects.all().order_by('-annee')
    if request.method == 'POST':
        num_bon = request.POST.get('num_bon', '').strip()
        date_aff = request.POST.get('date_affectation') or None
        annee = request.POST.get('annee_creation') or None
        benef_id = request.POST.get('beneficiaire_id') or None
        observation = request.POST.get('observation', '')
        if num_bon:
            bon = BonAffectation.objects.create(
                num_bon=int(num_bon),
                date_affectation=date_aff,
                annee_creation=int(annee) if annee else None,
                beneficiaire_id=benef_id,
                observation=observation,
            )
            return redirect('matieres:bon_affectation_update', pk=bon.pk)
    context = {
        'page_title': "Nouveau bon d'affectation",
        'beneficiaires': beneficiaires,
        'annees': annees,
        'today': date.today(),
        'next_num': (BonAffectation.objects.order_by('-num_bon').values_list('num_bon', flat=True).first() or 0) + 1,
    }
    return render(request, 'bons/affectation_form.html', context)


@login_required
def bon_affectation_update(request, pk):
    bon = get_object_or_404(BonAffectation, pk=pk)
    beneficiaires = Beneficiaire.objects.all().order_by('nom')
    unites = Unite.objects.all().order_by('libelle')
    if request.method == 'POST' and not bon.valide:
        bon.date_affectation = request.POST.get('date_affectation') or bon.date_affectation
        bon.annee_creation = request.POST.get('annee_creation') or bon.annee_creation
        bon.beneficiaire_id = request.POST.get('beneficiaire_id') or bon.beneficiaire_id
        bon.observation = request.POST.get('observation', bon.observation)
        bon.save()
    details = bon.details.select_related('produit', 'unite').all()
    context = {
        'page_title': f"Bon d'affectation BA-{bon.num_bon:04d}",
        'bon': bon,
        'details': details,
        'beneficiaires': beneficiaires,
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
        if d.produit:
            d.produit.qte_affectation += int(d.qte)
            d.produit.save(update_fields=['qte_affectation'])

        Journal.objects.create(
            date_creation=bon.date_affectation,
            num_bon=bon.num_bon,
            type_entree='Affectation',
            designation=d.designation,
            nomenclature=d.nomenclature,
            specification=d.specification,
            qte=int(d.qte),
            unite=str(d.unite) if d.unite else '',
            prix_ht=d.prix_ht,
            prix_ttc=d.prix_ttc,
            montant_ttc=d.montant_ttc,
            beneficiaire=str(bon.beneficiaire) if bon.beneficiaire else '',
            annee_exercice=bon.annee_creation,
            depot=str(bon.depot_destination) if bon.depot_destination else str(bon.depot) if bon.depot else '',
            sortie_periode=int(d.qte),
        )

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
            d.produit.qte_affectation = max(0, d.produit.qte_affectation - int(d.qte))
            d.produit.save(update_fields=['qte_affectation'])


    Journal.objects.filter(num_bon=bon.num_bon, type_entree='Affectation').delete()
    bon.valide = False
    bon.save(update_fields=['valide'])
    messages.success(request, f"Bon d'affectation BA-{bon.num_bon:04d} dévalidé.")
    return redirect('matieres:bon_affectation_update', pk=pk)


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
                qte=qte,
                unite_id=unite_id,
                prix_ht=prix_ht,
                prix_ttc=prix_ttc,
                montant_ttc=qte * prix_ttc,
                observation=observation,
            )

    details = bon.details.select_related('produit', 'unite').all()
    return render(request, 'partials/ba_detail_rows.html', {'details': details, 'bon': bon})


@login_required
def htmx_ba_delete_detail(request, detail_pk):
    detail = get_object_or_404(DetailBonAffectation, pk=detail_pk)
    bon = detail.bon_affectation
    if not bon.valide:
        detail.delete()
    details = bon.details.select_related('produit', 'unite').all()
    return render(request, 'partials/ba_detail_rows.html', {'details': details, 'bon': bon})


@login_required
def htmx_ba_produit_search(request):
    q = request.GET.get('q', '').strip()
    produits = []
    if len(q) >= 1:
        produits = Produit.objects.filter(
            Q(designation__icontains=q) | Q(nomenclature__icontains=q),
            nomenclature__startswith='1',
            stock_global__gt=0,
        ).select_related('unite').order_by('nomenclature')[:30]
    return render(request, 'partials/ba_produit_search.html', {'produits': produits, 'q': q})


@login_required
def htmx_ba_modal_produits(request):
    q = request.GET.get('q', '').strip()
    qs = Produit.objects.filter(
        nomenclature__startswith='1',
        stock_global__gt=0,
    ).select_related('unite').order_by('nomenclature')
    total_all = qs.count()
    if q:
        qs = qs.filter(Q(designation__icontains=q) | Q(nomenclature__icontains=q))
    return render(request, 'partials/ba_produit_modal_content.html', {
        'produits': qs[:300], 'q': q, 'total_all': total_all
    })


# ─────────────────────────── BONS RETOUR AFFECTATION ───────────────────────────

@login_required
def bons_retour_affectation_list(request):
    bons = BonRetourAffectation.objects.select_related('depot', 'beneficiaire').order_by('-date_creation', '-num_bon')
    context = {
        'page_title': "Bons de retour d'affectation",
        'bons': bons,
        'nb_non_valides': bons.filter(valide=False).count(),
    }
    return render(request, 'bons/retour_affectation_list.html', context)


@login_required
def bon_retour_affectation_create(request):
    beneficiaires = Beneficiaire.objects.all().order_by('nom')
    annees = AnneeExercice.objects.all().order_by('-annee')
    if request.method == 'POST':
        num_bon   = request.POST.get('num_bon', '').strip()
        date_ret  = request.POST.get('date_retour') or None
        date_crea = request.POST.get('date_creation') or None
        benef_id  = request.POST.get('beneficiaire_id') or None
        observation = request.POST.get('observation', '')
        if num_bon:
            bon = BonRetourAffectation.objects.create(
                num_bon=int(num_bon),
                date_retour=date_ret,
                date_creation=date_crea,
                beneficiaire_id=benef_id,
                observation=observation,
            )
            return redirect('matieres:bon_retour_affectation_update', pk=bon.pk)
    next_num = (BonRetourAffectation.objects.order_by('-num_bon').values_list('num_bon', flat=True).first() or 0) + 1
    context = {
        'page_title': "Nouveau bon de retour d'affectation",
        'depots': depots, 'beneficiaires': beneficiaires,
        'annees': annees, 'today': date.today(), 'next_num': next_num,
    }
    return render(request, 'bons/retour_affectation_form.html', context)


@login_required
def bon_retour_affectation_update(request, pk):
    bon = get_object_or_404(BonRetourAffectation, pk=pk)
    beneficiaires = Beneficiaire.objects.all().order_by('nom')
    unites = Unite.objects.all().order_by('libelle')
    if request.method == 'POST' and not bon.valide:
        bon.date_retour     = request.POST.get('date_retour') or bon.date_retour
        bon.date_creation   = request.POST.get('date_creation') or bon.date_creation
        bon.beneficiaire_id = request.POST.get('beneficiaire_id') or bon.beneficiaire_id
        bon.observation     = request.POST.get('observation', bon.observation)
        bon.save()
    details = bon.details.select_related('produit', 'unite').all()
    context = {
        'page_title': f"BRA-{bon.num_bon:04d}",
        'bon': bon, 'details': details,
        'beneficiaires': beneficiaires, 'unites': unites,
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

    erreurs = []
    for d in bon.details.select_related('produit').all():
        if d.produit:
            if d.produit.groupe != '1':
                erreurs.append(f"{d.nomenclature} : matière non Groupe 1.")
            elif d.produit.qte_affectation < int(d.qte):
                erreurs.append(
                    f"{d.nomenclature} — qté affectée {d.produit.qte_affectation} < retour demandé {d.qte}."
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
            designation=d.designation,
            nomenclature=d.nomenclature,
            specification=d.specification,
            qte=int(d.qte),
            unite=str(d.unite) if d.unite else '',
            prix_ht=d.prix_ht,
            prix_ttc=d.prix_ttc,
            montant_ttc=d.montant_ttc,
            beneficiaire=str(bon.beneficiaire) if bon.beneficiaire else '',
            depot=str(bon.depot_destination) if bon.depot_destination else str(bon.depot) if bon.depot else '',
            entree_periode=int(d.qte),
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
def htmx_bra_produit_search(request):
    q = request.GET.get('q', '').strip()
    produits = []
    if len(q) >= 1:
        produits = Produit.objects.filter(
            Q(designation__icontains=q) | Q(nomenclature__icontains=q),
            nomenclature__startswith='1',
            qte_affectation__gt=0,
        ).select_related('unite').order_by('nomenclature')[:30]
    return render(request, 'partials/bra_produit_search.html', {'produits': produits})


@login_required
def htmx_bra_modal_produits(request):
    q = request.GET.get('q', '').strip()
    qs = Produit.objects.filter(
        nomenclature__startswith='1',
        qte_affectation__gt=0,
    ).select_related('unite').order_by('nomenclature')
    total_all = qs.count()
    if q:
        qs = qs.filter(Q(designation__icontains=q) | Q(nomenclature__icontains=q))
    return render(request, 'partials/bra_produit_modal_content.html', {
        'produits': qs[:300], 'q': q, 'total_all': total_all
    })


# ─────────────────────────── BONS SORTIE PROVISOIRE ───────────────────────────

@login_required
def bons_sortie_prov_list(request):
    bons = BonSortieProvisoire.objects.select_related('depot', 'beneficiaire').order_by('-annee_creation', '-num_bon')
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
    beneficiaires = Beneficiaire.objects.all().order_by('nom')
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
                beneficiaire_id=request.POST.get('beneficiaire_id') or None,
                observation=request.POST.get('observation', ''),
            )
            return redirect('matieres:bon_sortie_prov_update', pk=bon.pk)
    next_num = (BonSortieProvisoire.objects.order_by('-num_bon').values_list('num_bon', flat=True).first() or 0) + 1
    context = {
        'page_title': "Nouveau bon de sortie provisoire",
        'depots': depots, 'beneficiaires': beneficiaires,
        'annees': annees, 'today': date.today(), 'next_num': next_num,
    }
    return render(request, 'bons/sortie_prov_form.html', context)


@login_required
def bon_sortie_prov_update(request, pk):
    bon = get_object_or_404(BonSortieProvisoire, pk=pk)
    depots = Depot.objects.all().order_by('code')
    beneficiaires = Beneficiaire.objects.all().order_by('nom')
    unites = Unite.objects.all().order_by('libelle')
    if request.method == 'POST' and not bon.valide:
        bon.date_sortie = request.POST.get('date_sortie') or bon.date_sortie
        bon.date_retour_prevue = request.POST.get('date_retour_prevue') or bon.date_retour_prevue
        bon.annee_creation = request.POST.get('annee_creation') or bon.annee_creation
        bon.depot_id = request.POST.get('depot_id') or bon.depot_id
        bon.beneficiaire_id = request.POST.get('beneficiaire_id') or bon.beneficiaire_id
        bon.observation = request.POST.get('observation', bon.observation)
        bon.save()
    details = bon.details.select_related('produit', 'unite').all()
    context = {
        'page_title': f"BSP-{bon.num_bon:04d}",
        'bon': bon, 'details': details,
        'depots': depots, 'beneficiaires': beneficiaires, 'unites': unites,
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

    erreurs = []
    for d in bon.details.select_related('produit').all():
        if d.produit:
            if d.produit.groupe != '1':
                erreurs.append(f"{d.nomenclature} : matière non Groupe 1.")
            elif d.produit.stock_disponible < int(d.qte):
                erreurs.append(f"{d.nomenclature} — stock dispo {d.produit.stock_disponible} < qté {d.qte}.")
    if erreurs:
        messages.error(request, "Validation impossible : " + " | ".join(erreurs))
        return redirect('matieres:bon_sortie_prov_update', pk=pk)

    for d in bon.details.select_related('produit', 'unite').all():
        if d.produit:
            d.produit.qte_sp += int(d.qte)
            d.produit.save(update_fields=['qte_sp'])
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
            designation=d.designation,
            nomenclature=d.nomenclature,
            specification=d.specification,
            qte=int(d.qte),
            unite=str(d.unite) if d.unite else '',
            prix_ht=d.prix_ht,
            prix_ttc=d.prix_ttc,
            montant_ttc=d.montant_ttc,
            beneficiaire=str(bon.beneficiaire) if bon.beneficiaire else '',
            annee_exercice=bon.annee_creation,
            depot=str(bon.depot) if bon.depot else '',
            sortie_periode=int(d.qte),
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
            d.produit.save(update_fields=['qte_sp'])
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
def htmx_bsp_produit_search(request):
    q = request.GET.get('q', '').strip()
    produits = []
    if len(q) >= 1:
        produits = Produit.objects.filter(
            Q(designation__icontains=q) | Q(nomenclature__icontains=q),
            nomenclature__startswith='1',
            stock_global__gt=0,
        ).select_related('unite').order_by('nomenclature')[:30]
    return render(request, 'partials/bsp_produit_search.html', {'produits': produits})


@login_required
def htmx_bsp_modal_produits(request):
    q = request.GET.get('q', '').strip()
    qs = Produit.objects.filter(
        nomenclature__startswith='1',
        stock_global__gt=0,
    ).select_related('unite').order_by('nomenclature')
    total_all = qs.count()
    if q:
        qs = qs.filter(Q(designation__icontains=q) | Q(nomenclature__icontains=q))
    return render(request, 'partials/bsp_produit_modal_content.html', {
        'produits': qs[:300], 'q': q, 'total_all': total_all
    })


# ─────────────────────────── BONS RETOUR SORTIE PROVISOIRE ───────────────────────────

@login_required
def bons_retour_sortie_prov_list(request):
    bons = BonRetourSortieProvisoire.objects.select_related('depot', 'beneficiaire').order_by('-annee_creation', '-num_bon')
    nb_non_valides = bons.filter(valide=False).count()
    context = {'page_title': "Bons de retour sortie provisoire", 'bons': bons, 'nb_non_valides': nb_non_valides}
    return render(request, 'bons/retour_sortie_prov_list.html', context)


@login_required
def bon_retour_sortie_prov_create(request):
    depots = Depot.objects.all().order_by('code')
    beneficiaires = Beneficiaire.objects.all().order_by('nom')
    annees = AnneeExercice.objects.all().order_by('-annee')
    if request.method == 'POST':
        num_bon = request.POST.get('num_bon', '').strip()
        if num_bon:
            bon = BonRetourSortieProvisoire.objects.create(
                num_bon=int(num_bon),
                date_retour=request.POST.get('date_retour') or None,
                annee_creation=request.POST.get('annee_creation') or None,
                depot_id=request.POST.get('depot_id') or None,
                beneficiaire_id=request.POST.get('beneficiaire_id') or None,
                observation=request.POST.get('observation', ''),
            )
            return redirect('matieres:bon_retour_sortie_prov_update', pk=bon.pk)
    next_num = (BonRetourSortieProvisoire.objects.order_by('-num_bon').values_list('num_bon', flat=True).first() or 0) + 1
    context = {
        'page_title': "Nouveau bon de retour sortie provisoire",
        'depots': depots, 'beneficiaires': beneficiaires,
        'annees': annees, 'today': date.today(), 'next_num': next_num,
    }
    return render(request, 'bons/retour_sortie_prov_form.html', context)


@login_required
def bon_retour_sortie_prov_update(request, pk):
    bon = get_object_or_404(BonRetourSortieProvisoire, pk=pk)
    depots = Depot.objects.all().order_by('code')
    beneficiaires = Beneficiaire.objects.all().order_by('nom')
    unites = Unite.objects.all().order_by('libelle')
    if request.method == 'POST' and not bon.valide:
        bon.date_retour = request.POST.get('date_retour') or bon.date_retour
        bon.annee_creation = request.POST.get('annee_creation') or bon.annee_creation
        bon.depot_id = request.POST.get('depot_id') or bon.depot_id
        bon.beneficiaire_id = request.POST.get('beneficiaire_id') or bon.beneficiaire_id
        bon.observation = request.POST.get('observation', bon.observation)
        bon.save()
    details = bon.details.select_related('produit', 'unite').all()
    context = {
        'page_title': f"BRSP-{bon.num_bon:04d}",
        'bon': bon, 'details': details,
        'depots': depots, 'beneficiaires': beneficiaires, 'unites': unites,
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

    erreurs = []
    for d in bon.details.select_related('produit').all():
        if d.produit:
            if d.produit.groupe != '1':
                erreurs.append(f"{d.nomenclature} : matière non Groupe 1.")
            elif d.produit.qte_sp < int(d.qte):
                erreurs.append(f"{d.nomenclature} — qté SP {d.produit.qte_sp} < qté {d.qte}.")
    if erreurs:
        messages.error(request, "Validation impossible : " + " | ".join(erreurs))
        return redirect('matieres:bon_retour_sortie_prov_update', pk=pk)

    for d in bon.details.select_related('produit', 'unite').all():
        if d.produit:
            d.produit.qte_sp = max(0, d.produit.qte_sp - int(d.qte))
            d.produit.save(update_fields=['qte_sp'])
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
            designation=d.designation,
            nomenclature=d.nomenclature,
            specification=d.specification,
            qte=int(d.qte),
            unite=str(d.unite) if d.unite else '',
            prix_ht=d.prix_ht,
            prix_ttc=d.prix_ttc,
            montant_ttc=d.montant_ttc,
            beneficiaire=str(bon.beneficiaire) if bon.beneficiaire else '',
            annee_exercice=bon.annee_creation,
            depot=str(bon.depot) if bon.depot else '',
            entree_periode=int(d.qte),
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
            d.produit.save(update_fields=['qte_sp'])
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
def htmx_brsp_produit_search(request):
    q = request.GET.get('q', '').strip()
    produits = []
    if len(q) >= 1:
        produits = Produit.objects.filter(
            Q(designation__icontains=q) | Q(nomenclature__icontains=q),
            nomenclature__startswith='1',
            qte_sp__gt=0,
        ).select_related('unite').order_by('nomenclature')[:30]
    return render(request, 'partials/brsp_produit_search.html', {'produits': produits})


@login_required
def htmx_brsp_modal_produits(request):
    q = request.GET.get('q', '').strip()
    qs = Produit.objects.filter(
        nomenclature__startswith='1',
        qte_sp__gt=0,
    ).select_related('unite').order_by('nomenclature')
    total_all = qs.count()
    if q:
        qs = qs.filter(Q(designation__icontains=q) | Q(nomenclature__icontains=q))
    return render(request, 'partials/brsp_produit_modal_content.html', {
        'produits': qs[:300], 'q': q, 'total_all': total_all
    })


# ─────────────────────────── BONS SORTIE DÉFINITIVE ───────────────────────────

@login_required
def bons_sortie_def_list(request):
    bons = BonSortieDefinitive.objects.select_related('depot', 'beneficiaire').order_by('-date_creation', '-num_bon')
    context = {
        'page_title': "Bons de sortie définitive",
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
    bons = BonSortieDefinitiveG1.objects.select_related('depot', 'beneficiaire').order_by('-date_creation', '-num_bon')
    context = {'page_title': "Bons de sortie définitive G1 (Réformes)", 'bons': bons}
    return render(request, 'bons/sortie_def_g1_list.html', context)


# ─────────────────────────── JOURNAL ───────────────────────────

@login_required
def journal_list(request):
    query = request.GET.get('q', '')
    type_op = request.GET.get('type', '')
    depot = request.GET.get('depot', '')
    journal = Journal.objects.order_by('-date_creation', '-id')
    if query:
        journal = journal.filter(Q(designation__icontains=query) | Q(nomenclature__icontains=query) | Q(beneficiaire__icontains=query))
    if type_op:
        journal = journal.filter(type_entree=type_op)
    if depot:
        journal = journal.filter(depot=depot)
    types = Journal.objects.values_list('type_entree', flat=True).distinct()
    depots_j = Journal.objects.values_list('depot', flat=True).distinct()
    context = {
        'page_title': 'Journal des opérations',
        'journal': journal[:200],
        'types': types,
        'depots': depots_j,
        'query': query,
        'type_op': type_op,
        'depot': depot,
        'total': journal.count(),
    }
    return render(request, 'journal/list.html', context)


# ─────────────────────────── BALANCE ───────────────────────────

@login_required
def balance_list(request):
    annee_id = request.GET.get('annee', '')
    balances = BalancePeriodique.objects.select_related('annee_exercice')
    if annee_id:
        balances = balances.filter(annee_exercice_id=annee_id)
    totaux = balances.aggregate(
        total_existant=Sum('existant_dp'),
        total_entrees=Sum('entree_periode'),
        total_sorties=Sum('sortie_periode'),
        total_fin=Sum('existant_fin_periode'),
        total_montant=Sum('montant_existant'),
    )
    context = {
        'page_title': 'Balance périodique',
        'balances': balances.order_by('nomenclature'),
        'annees': AnneeExercice.objects.all(),
        'annee_id': annee_id,
        'totaux': totaux,
    }
    return render(request, 'balance/list.html', context)


# ─────────────────────────── RÉFÉRENTIELS ───────────────────────────

@login_required
def fournisseurs_list(request):
    context = {'page_title': 'Fournisseurs', 'fournisseurs': Fournisseur.objects.order_by('nom')}
    return render(request, 'referentiels/fournisseurs.html', context)


@login_required
def beneficiaires_list(request):
    context = {'page_title': 'Bénéficiaires', 'beneficiaires': Beneficiaire.objects.order_by('nom')}
    return render(request, 'referentiels/beneficiaires.html', context)


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
        sous_comptes = sous_comptes.filter(Q(famille_sc__icontains=query) | Q(num_sous_compte__icontains=query))
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
            societe.save()
            messages.success(request, "Informations société mises à jour.")
        else:
            SocieteGCS.objects.create(
                nom=data.get('nom', ''), telephone=data.get('telephone', ''),
                email=data.get('email', ''), adresse=data.get('adresse', ''),
                fax=data.get('fax', ''), ministere=data.get('ministere', ''),
                administrateur=data.get('administrateur', ''), comptable=data.get('comptable', ''),
                receptionnaire=data.get('receptionnaire', ''), responsable=data.get('responsable', ''),
                ville=data.get('ville', ''),
            )
            messages.success(request, "Société créée avec succès.")
        return redirect('matieres:societe_view')
    return render(request, 'configuration/societe.html', {'page_title': 'Société GCS', 'societe': societe})


@login_required
def unite_list(request):
    if request.method == 'POST':
        libelle = request.POST.get('libelle', '').strip()
        if libelle:
            _, created = Unite.objects.get_or_create(libelle=libelle)
            messages.success(request, f"Unité « {libelle} » {'créée' if created else 'déjà existante'}.")
        return redirect('matieres:unite_list')
    if request.GET.get('delete'):
        obj = get_object_or_404(Unite, pk=request.GET['delete'])
        obj.delete()
        messages.success(request, "Unité supprimée.")
        return redirect('matieres:unite_list')
    unites = Unite.objects.annotate(nb=Count('produit')).order_by('libelle')
    return render(request, 'configuration/unites.html', {'page_title': 'Unités', 'unites': unites})


@login_required
def type_op_list(request):
    if request.method == 'POST':
        libelle = request.POST.get('libelle', '').strip()
        if libelle:
            _, created = TypeOperation.objects.get_or_create(libelle=libelle)
            messages.success(request, f"Type « {libelle} » {'créé' if created else 'déjà existant'}.")
        return redirect('matieres:type_op_list')
    if request.GET.get('delete'):
        obj = get_object_or_404(TypeOperation, pk=request.GET['delete'])
        obj.delete()
        messages.success(request, "Type supprimé.")
        return redirect('matieres:type_op_list')
    types = TypeOperation.objects.order_by('libelle')
    return render(request, 'configuration/type_operations.html', {'page_title': "Types d'opération", 'types': types})


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
    if request.method == 'POST':
        depot_id = request.POST.get('depot', '')
        num_sc = request.POST.get('num_sous_compte', '').strip()
        if depot_id and num_sc:
            depot_obj = get_object_or_404(Depot, pk=depot_id)
            _, created = MatieresDepot.objects.get_or_create(depot=depot_obj, num_sous_compte=int(num_sc))
            messages.success(request, "Lien créé." if created else "Lien déjà existant.")
        return redirect('matieres:matieres_depot_config')
    if request.GET.get('delete'):
        get_object_or_404(MatieresDepot, pk=request.GET['delete']).delete()
        messages.success(request, "Lien supprimé.")
        return redirect('matieres:matieres_depot_config')
    liens = MatieresDepot.objects.select_related('depot').order_by('depot__code', 'num_sous_compte')
    return render(request, 'configuration/matieres_depot.html', {
        'page_title': 'Matières / Dépôt', 'liens': liens, 'depots': Depot.objects.all(),
    })


@login_required
def profil_list(request):
    if request.method == 'POST':
        role = request.POST.get('role', '').strip()
        if role:
            _, created = Profil.objects.get_or_create(role=role)
            messages.success(request, f"Profil « {role} » {'créé' if created else 'déjà existant'}.")
        return redirect('matieres:profil_list')
    if request.GET.get('delete'):
        get_object_or_404(Profil, pk=request.GET['delete']).delete()
        messages.success(request, "Profil supprimé.")
        return redirect('matieres:profil_list')
    profils = Profil.objects.order_by('role')
    return render(request, 'configuration/profils.html', {'page_title': 'Profils', 'profils': profils})


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
    annee_id = request.GET.get('annee', '')
    balances = BalancePeriodique.objects.select_related('annee_exercice', 'produit')
    if annee_id:
        balances = balances.filter(annee_exercice_id=annee_id)
    totaux = balances.aggregate(
        t_existant=Sum('existant_dp'),
        t_entree=Sum('entree_periode'),
        t_total=Sum('total_entree'),
        t_sortie=Sum('sortie_periode'),
        t_fin=Sum('existant_fin_periode'),
        t_montant=Sum('montant_existant'),
    )
    context = {
        'page_title': 'Relevé Récapitulatif',
        'balances': balances.order_by('nomenclature'),
        'annees': AnneeExercice.objects.order_by('-annee'),
        'annee_id': annee_id,
        'totaux': totaux,
        'total': balances.count(),
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
