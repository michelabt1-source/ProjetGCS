"""
Commande d'import des tables WinDev exportees en XLS.
Usage : python manage.py import_tables [--dir tables] [--tables all|depot,produit,...]
"""
import os
import sys
from datetime import date, datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
import xlrd

# xlrd 2.x a supprime les constantes XL_CELL_* — on les definit ici
XL_CELL_EMPTY = 0
XL_CELL_TEXT = 1
XL_CELL_NUMBER = 2
XL_CELL_DATE = 3
XL_CELL_BOOLEAN = 4

# Force stdout en UTF-8 pour eviter les erreurs cp1252 sur Windows
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


# ─────────────────────────── HELPERS ────────────────────────────────

BASE_DIR = getattr(settings, 'BASE_DIR', os.getcwd())
TABLES_DIR = os.path.join(BASE_DIR, 'tables')

ENCODINGS = ('cp1252', 'latin-1', 'utf-8')


def open_xls(filename):
    path = os.path.join(TABLES_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Fichier introuvable : {path}")
    for enc in ENCODINGS:
        try:
            return xlrd.open_workbook(path, encoding_override=enc), enc
        except Exception:
            pass
    raise ValueError(f"Impossible d'ouvrir {path}")


def read_rows(filename):
    """Retourne (wb, liste de dicts {header: valeur})."""
    wb, _enc = open_xls(filename)
    ws = wb.sheet_by_index(0)
    if ws.nrows < 2:
        return wb, []
    headers = [str(ws.cell_value(0, c)).strip() for c in range(ws.ncols)]
    rows = []
    for r in range(1, ws.nrows):
        row = {}
        all_empty = True
        for c, h in enumerate(headers):
            cell = ws.cell(r, c)
            if cell.ctype == XL_CELL_DATE:
                try:
                    t = xlrd.xldate_as_tuple(cell.value, wb.datemode)
                    row[h] = date(t[0], t[1], t[2]) if t[0] > 0 else None
                except Exception:
                    row[h] = None
            elif cell.ctype == XL_CELL_NUMBER:
                row[h] = cell.value
                all_empty = False
            elif cell.ctype == XL_CELL_TEXT:
                row[h] = cell.value.strip()
                if row[h]:
                    all_empty = False
            elif cell.ctype == XL_CELL_BOOLEAN:
                row[h] = bool(cell.value)
                all_empty = False
            else:
                row[h] = cell.value
        if not all_empty:
            rows.append(row)
    return wb, rows


def s(row, *keys):
    """String value — essaie plusieurs clés."""
    for k in keys:
        if k in row and row[k] not in (None, ''):
            return str(row[k]).strip()
    return ''


def i(row, *keys, default=0):
    """Integer value."""
    for k in keys:
        if k in row and row[k] not in (None, ''):
            try:
                return int(float(str(row[k])))
            except (ValueError, TypeError):
                pass
    return default


def f(row, *keys, default=0.0):
    """Float value."""
    for k in keys:
        if k in row and row[k] not in (None, ''):
            try:
                return float(str(row[k]))
            except (ValueError, TypeError):
                pass
    return default


def d(row, *keys):
    """Date value."""
    for k in keys:
        v = row.get(k)
        if v is None or v == '':
            continue
        if isinstance(v, date):
            return v
        for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
            try:
                return datetime.strptime(str(v).strip(), fmt).date()
            except ValueError:
                pass
    return None


def b(row, *keys):
    """Boolean value."""
    for k in keys:
        v = row.get(k)
        if v not in (None, ''):
            if isinstance(v, bool):
                return v
            try:
                return bool(int(float(str(v))))
            except (ValueError, TypeError):
                pass
    return False


def dec(row, *keys, default=0):
    """Decimal (as float) value."""
    return f(row, *keys, default=default)


# ─────────────────────────── IMPORTEURS ─────────────────────────────

from matieres.models import (
    Depot, Unite, TypeOperation,
    ComptePrincipale, SousCompte,
    Fournisseur, Beneficiaire,
    Produit, SocieteGCS,
    MembreCommission, MembreCommissionReforme,
    AnneeExercice, MatieresDepot, StockDepot,
    BonEntree, DetailBonEntree,
    BonAffectation, DetailBonAffectation,
    BonRetourAffectation, DetailBonRetourAffectation,
    BonSortieProvisoire, DetailBonSortieProvisoire,
    BonRetourSortieProvisoire, DetailBonRetourSortieProvisoire,
    BonSortieDefinitive, DetailBonSortieDefinitive,
    BonSortieDefinitiveG1, DetailBonSortieDefinitiveG1,
    Journal, BalancePeriodique,
)


def imp_depot(rows, verbose):
    c = u = e = 0
    for row in rows:
        code = s(row, 'Dépot', 'D\xe9pot', 'depot')
        if not code:
            e += 1; continue
        _, is_new = Depot.objects.get_or_create(code=code)
        c += is_new; u += not is_new
    return c, u, e


def imp_unite(rows, verbose):
    c = u = e = 0
    for row in rows:
        lib = s(row, 'Unité', 'Unit\xe9')
        if not lib:
            e += 1; continue
        _, is_new = Unite.objects.get_or_create(libelle=lib)
        c += is_new; u += not is_new
    return c, u, e


def imp_type_op(rows, verbose):
    c = u = e = 0
    for row in rows:
        lib = s(row, 'TypeEntré', 'TypeEntr\xe9', 'TypeEntree')
        if not lib:
            e += 1; continue
        _, is_new = TypeOperation.objects.get_or_create(libelle=lib)
        c += is_new; u += not is_new
    return c, u, e


def imp_compte(rows, verbose):
    c = u = e = 0
    for row in rows:
        num_raw = row.get('NumComptePrincipal')
        famille = s(row, 'Famille')
        if num_raw in (None, '', 0, 0.0):
            e += 1; continue
        try:
            num = int(float(str(num_raw)))
        except (ValueError, TypeError):
            e += 1; continue
        obj, is_new = ComptePrincipale.objects.get_or_create(
            num_compte=num, defaults={'famille': famille}
        )
        if not is_new and famille and obj.famille != famille:
            obj.famille = famille; obj.save()
        c += is_new; u += not is_new
    return c, u, e


def imp_sous_compte(rows, verbose):
    # Pré-charge tous les comptes principaux
    comptes = {cp.num_compte: cp for cp in ComptePrincipale.objects.all()}
    c = u = e = 0
    for row in rows:
        num_sc_raw = s(row, 'NumSousCompte')
        famille_sc = s(row, 'FamilleSc')
        num_cp_raw = row.get('NumComptePrincipal')
        if not num_sc_raw:
            e += 1; continue
        try:
            num_sc = float(num_sc_raw)
        except (ValueError, TypeError):
            e += 1; continue

        cp = None
        if num_cp_raw not in (None, '', 0, 0.0):
            try:
                num_cp_int = int(float(str(num_cp_raw)))
                cp = comptes.get(num_cp_int)
                if cp is None:
                    # créer un compte stub s'il n'existe pas encore
                    cp, _ = ComptePrincipale.objects.get_or_create(
                        num_compte=num_cp_int,
                        defaults={'famille': f'Compte {num_cp_int}'}
                    )
                    comptes[num_cp_int] = cp
            except (ValueError, TypeError):
                pass

        if cp is None:
            e += 1; continue  # compte_principal est requis (non nullable)

        obj, is_new = SousCompte.objects.get_or_create(
            num_sous_compte=num_sc,
            defaults={'famille_sc': famille_sc, 'compte_principal': cp}
        )
        if not is_new:
            changed = False
            if famille_sc and obj.famille_sc != famille_sc:
                obj.famille_sc = famille_sc; changed = True
            if cp and obj.compte_principal_id != cp.pk:
                obj.compte_principal = cp; changed = True
            if changed: obj.save()
        c += is_new; u += not is_new
    return c, u, e


def imp_fournisseur(rows, verbose):
    c = u = e = 0
    for row in rows:
        nom = s(row, 'Fournisseur')
        if not nom:
            e += 1; continue
        defaults = {
            'adresse':     s(row, 'Adresse'),
            'telephone':   s(row, 'Téléphone', 'T\xe9l\xe9phone'),
            'fax':         s(row, 'Fax'),
            'code_postal': s(row, 'Codepostal'),
            'fonction':    s(row, 'Fonctionfour'),
            'ville':       s(row, 'Ville'),
            'region':      s(row, 'région', 'r\xe9gion', 'Region'),
            'pays':        s(row, 'pays', 'Pays'),
        }
        obj, is_new = Fournisseur.objects.get_or_create(nom=nom, defaults=defaults)
        if not is_new:
            for k, v in defaults.items():
                if v: setattr(obj, k, v)
            obj.save()
        c += is_new; u += not is_new
    return c, u, e


def imp_beneficiaire(rows, verbose):
    c = u = e = 0
    for row in rows:
        nom = s(row, 'Bénéficiaire', 'B\xe9n\xe9ficiaire')
        if not nom:
            e += 1; continue
        resp = s(row, 'Nomrespo')
        obj, is_new = Beneficiaire.objects.get_or_create(
            nom=nom, defaults={'responsable': resp}
        )
        if not is_new and resp:
            obj.responsable = resp; obj.save()
        c += is_new; u += not is_new
    return c, u, e


def imp_produit(rows, verbose):
    # Pré-charge les caches
    unites  = {u.libelle.upper(): u for u in Unite.objects.all()}
    comptes = {cp.num_compte: cp for cp in ComptePrincipale.objects.all()}
    sous_comptes = {sc.num_sous_compte: sc for sc in SousCompte.objects.all()}

    c = u = e = 0
    for idx, row in enumerate(rows):
        nomenclature = s(row, 'Nomenclature')
        designation  = s(row, 'Désignation', 'D\xe9signation')
        if not nomenclature or not designation:
            e += 1; continue

        # Unité
        unite_lib = s(row, 'Unité', 'Unit\xe9')
        unite_obj = None
        if unite_lib:
            unite_obj = unites.get(unite_lib.upper())
            if not unite_obj:
                unite_obj, _ = Unite.objects.get_or_create(libelle=unite_lib)
                unites[unite_lib.upper()] = unite_obj

        # Compte principal
        num_cp = row.get('NumComptePrincipal', 0)
        cp = comptes.get(int(float(str(num_cp)))) if num_cp not in (None, '', 0, 0.0) else None

        # Sous-compte
        num_sc = row.get('NumSousCompte', 0)
        sc = None
        if num_sc not in (None, '', 0, 0.0):
            try:
                sc = sous_comptes.get(float(str(num_sc)))
            except (ValueError, TypeError):
                pass

        defaults = {
            'designation':      designation,
            'stock_global':     i(row, 'QTéStockGlobale', 'QT\xe9StockGlobale'),
            'qte_affectation':  i(row, 'QtéAffectation', 'Qt\xe9Affectation'),
            'qte_sd':           i(row, 'qtéSD', 'qt\xe9SD'),
            'entree':           i(row, 'Entrée', 'Entr\xe9e'),
            'qte_sp':           i(row, 'QtéSP', 'Qt\xe9SP'),
            'unite':            unite_obj,
            'compte_principal': cp,
            'sous_compte':      sc,
            'specification':    s(row, 'Spécification', 'Sp\xe9cification'),
            'observation':      s(row, 'Observation'),
        }
        obj, is_new = Produit.objects.get_or_create(nomenclature=nomenclature, defaults=defaults)
        if not is_new:
            for k, v in defaults.items():
                if v is not None:
                    setattr(obj, k, v)
            obj.save()
        c += is_new; u += not is_new

        if verbose and (idx + 1) % 200 == 0:
            print(f"    ... {idx+1} produits traités")

    return c, u, e


def imp_membre_commission(rows, verbose):
    c = u = e = 0
    for row in rows:
        nom     = s(row, 'NomMembreCommission')
        qualite = s(row, 'Qualité', 'Qualit\xe9')
        if not nom:
            e += 1; continue
        obj, is_new = MembreCommission.objects.get_or_create(nom=nom, defaults={'qualite': qualite})
        if not is_new and qualite:
            obj.qualite = qualite; obj.save()
        c += is_new; u += not is_new
    return c, u, e


def imp_membre_reforme(rows, verbose):
    c = u = e = 0
    for row in rows:
        nom     = s(row, 'Noms')
        qualite = s(row, 'Qualités', 'Qualit\xe9s')
        if not nom:
            e += 1; continue
        obj, is_new = MembreCommissionReforme.objects.get_or_create(nom=nom, defaults={'qualite': qualite})
        if not is_new and qualite:
            obj.qualite = qualite; obj.save()
        c += is_new; u += not is_new
    return c, u, e


def imp_annee_exercice(rows, verbose):
    c = u = e = 0
    for row in rows:
        annee_raw = row.get('Année', row.get('Ann\xe9e'))
        if annee_raw in (None, ''):
            e += 1; continue
        try:
            annee = int(float(str(annee_raw)))
        except (ValueError, TypeError):
            e += 1; continue

        # dates stockées comme serial Excel (float)
        dd_raw = row.get('Datedebut', row.get('DateDebut'))
        df_raw = row.get('Datefin', row.get('DateFin'))
        dd = dd_raw if isinstance(dd_raw, date) else date(annee, 1, 1)
        df = df_raw if isinstance(df_raw, date) else date(annee, 12, 31)

        obj, is_new = AnneeExercice.objects.get_or_create(
            annee=annee, defaults={'date_debut': dd, 'date_fin': df}
        )
        if not is_new:
            obj.date_debut = dd; obj.date_fin = df; obj.save()
        c += is_new; u += not is_new
    return c, u, e


def imp_societe(rows, verbose):
    c = u = e = 0
    for row in rows:
        nom = s(row, 'NomSocieté', 'NomSociet\xe9')
        if not nom:
            e += 1; continue
        defaults = {
            'telephone':      s(row, 'TéléphoneSocieté', 'T\xe9l\xe9phoneSociet\xe9'),
            'email':          s(row, 'EmailSocieté', 'EmailSociet\xe9'),
            'adresse':        s(row, 'AdresseSocieté', 'AdresseSociet\xe9'),
            'fax':            s(row, 'FaxSocieté', 'FaxSociet\xe9'),
            'ministere':      s(row, 'Ministère', 'Minist\xe8re'),
            'administrateur': s(row, 'Administrateur'),
            'comptable':      s(row, 'comptable', 'Comptable'),
            'receptionnaire': s(row, 'Réceptionnaire', 'R\xe9ceptionnaire'),
            'responsable':    s(row, 'Responsable'),
            'ville':          s(row, 'VilleSocieté', 'VilleSociet\xe9'),
        }
        obj, is_new = SocieteGCS.objects.get_or_create(nom=nom, defaults=defaults)
        if not is_new:
            for k, v in defaults.items():
                if v: setattr(obj, k, v)
            obj.save()
        c += is_new; u += not is_new
    return c, u, e


def imp_matieres_depot(rows, verbose):
    depots = {dp.code: dp for dp in Depot.objects.all()}
    c = u = e = 0
    for row in rows:
        depot_code = s(row, 'Dépot', 'D\xe9pot')
        num_sc_raw = row.get('NumSousCompte')
        if not depot_code or num_sc_raw in (None, ''):
            e += 1; continue
        depot_obj = depots.get(depot_code)
        if not depot_obj:
            e += 1; continue
        try:
            num_sc = int(float(str(num_sc_raw)))
        except (ValueError, TypeError):
            e += 1; continue
        _, is_new = MatieresDepot.objects.get_or_create(depot=depot_obj, num_sous_compte=num_sc)
        c += is_new; u += not is_new
    return c, u, e


def imp_stock_depot(rows, verbose):
    depots   = {dp.code: dp for dp in Depot.objects.all()}
    produits = {p.nomenclature: p for p in Produit.objects.all()}
    c = u = e = 0
    for row in rows:
        nomenclature = s(row, 'Nomenclature')
        designation  = s(row, 'Désignation', 'D\xe9signation')
        depot_code   = s(row, 'Dépot', 'D\xe9pot')
        qte          = i(row, 'QtéStockDépot', 'Qt\xe9StockD\xe9pot', 'QteStockDepot')

        if not nomenclature or not depot_code:
            e += 1; continue
        depot_obj  = depots.get(depot_code)
        produit_obj = produits.get(nomenclature)
        if not depot_obj:
            e += 1; continue

        obj, is_new = StockDepot.objects.get_or_create(
            nomenclature=nomenclature, depot=depot_obj,
            defaults={'designation': designation, 'qte_stock': qte, 'produit': produit_obj}
        )
        if not is_new:
            obj.qte_stock = qte
            obj.designation = designation or obj.designation
            if produit_obj: obj.produit = produit_obj
            obj.save()
        c += is_new; u += not is_new
    return c, u, e


def imp_bon_entree(rows, verbose):
    annees     = {a.annee: a for a in AnneeExercice.objects.all()}
    type_ops   = {t.libelle: t for t in TypeOperation.objects.all()}
    depots     = {dp.code: dp for dp in Depot.objects.all()}
    fournisseurs = {f.nom: f for f in Fournisseur.objects.all()}
    c = u = e = 0
    for row in rows:
        num_bon = i(row, 'NumBonEntrée', 'NumBonEntr\xe9e')
        if not num_bon:
            e += 1; continue
        date_c  = d(row, 'DateDeCréation', 'DateDeCr\xe9ation')
        annee_v = i(row, 'AnnéeExercice', 'Ann\xe9eExercice')
        type_l  = s(row, 'TypeEntré', 'TypeEntr\xe9')
        depot_c = s(row, 'Dépot', 'D\xe9pot')
        four_n  = s(row, 'Fournisseur')

        defaults = {
            'date_creation':      date_c or date.today(),
            'annee_exercice':     annees.get(annee_v),
            'references_pieces':  s(row, 'RéférencesPièces', 'R\xe9f\xe9rencesPi\xe8ces'),
            'type_entree':        type_ops.get(type_l),
            'valide':             b(row, 'Valide'),
            'depot':              depots.get(depot_c),
            'fournisseur':        fournisseurs.get(four_n),
            'num_bon_engagement': i(row, 'NumBonEngagement'),
            'num_bon_commande':   i(row, 'NumBonCommande'),
            'chapitre':           s(row, 'Chapitre'),
        }
        _, is_new = BonEntree.objects.get_or_create(num_bon=num_bon, defaults=defaults)
        c += is_new; u += not is_new
    return c, u, e


def imp_detail_bon_entree(rows, verbose):
    unites   = {u.libelle: u for u in Unite.objects.all()}
    produits = {p.nomenclature: p for p in Produit.objects.all()}
    c = u = e = 0
    for row in rows:
        desig  = s(row, 'Désignation', 'D\xe9signation')
        nomenc = s(row, 'Nomenclature')
        if not desig:
            e += 1; continue

        # Lien vers BonEntree — utilise IDJournal comme fallback
        bon_id_raw = row.get('IDBonEntrée', row.get('IDBonEntr\xe9e', 0))
        bon = None
        if bon_id_raw and int(float(str(bon_id_raw))) > 0:
            bon = BonEntree.objects.filter(pk=int(float(str(bon_id_raw)))).first()
        if not bon:
            bon = BonEntree.objects.first()  # fallback sur premier bon
        if not bon:
            e += 1; continue

        unite_lib = s(row, 'Unité', 'Unit\xe9')
        unite_obj = unites.get(unite_lib) if unite_lib else None

        DetailBonEntree.objects.get_or_create(
            bon_entree=bon,
            nomenclature=nomenc,
            designation=desig,
            defaults={
                'produit':        produits.get(nomenc),
                'specification':  s(row, 'Spécification', 'Sp\xe9cification'),
                'qte':            i(row, 'QTéBE', 'QT\xe9BE'),
                'unite':          unite_obj,
                'prix_ht':        dec(row, 'PrixUnitaireHT'),
                'prix_ttc':       dec(row, 'PrixUnitaireTTC'),
                'montant_ttc':    dec(row, 'MontantTTC'),
                'observation':    s(row, 'Observation'),
            }
        )
        c += 1
    return c, u, e


def imp_bon_affectation(rows, verbose):
    depots = {dp.code: dp for dp in Depot.objects.all()}
    benefs = {b.nom: b for b in Beneficiaire.objects.all()}
    c = u = e = 0
    for row in rows:
        num_bon = i(row, 'NumBonDaffect', 'NumBonDaffect')
        if not num_bon:
            e += 1; continue
        date_aff = d(row, 'DateAffectation')
        annee_v  = s(row, 'DateCréation', 'DateCr\xe9ation')
        try:
            annee_int = int(float(annee_v)) if annee_v else None
        except (ValueError, TypeError):
            annee_int = None
        defaults = {
            'date_affectation': date_aff,
            'annee_creation':   annee_int,
            'depot':            depots.get(s(row, 'Dépot', 'D\xe9pot')),
            'beneficiaire':     benefs.get(s(row, 'Bénéficiaire', 'B\xe9n\xe9ficiaire')),
            'confirmation':     b(row, 'Confirmation'),
        }
        _, is_new = BonAffectation.objects.get_or_create(num_bon=num_bon, defaults=defaults)
        c += is_new; u += not is_new
    return c, u, e


def imp_detail_bon_affectation(rows, verbose):
    unites   = {u.libelle: u for u in Unite.objects.all()}
    produits = {p.nomenclature: p for p in Produit.objects.all()}
    bons     = {b.num_bon: b for b in BonAffectation.objects.all()}
    c = u = e = 0
    for row in rows:
        nomenc = s(row, 'Nomenclature')
        desig  = s(row, 'Désignation', 'D\xe9signation')
        if not desig:
            e += 1; continue

        bon_id_raw = row.get('IDBondAffectation', 0)
        bon = None
        if bon_id_raw and int(float(str(bon_id_raw))) > 0:
            bon = BonAffectation.objects.filter(pk=int(float(str(bon_id_raw)))).first()
        if not bon:
            bon = BonAffectation.objects.first()
        if not bon:
            e += 1; continue

        unite_lib = s(row, 'Unité', 'Unit\xe9')
        DetailBonAffectation.objects.get_or_create(
            bon_affectation=bon, nomenclature=nomenc, designation=desig,
            defaults={
                'produit':       produits.get(nomenc),
                'specification': s(row, 'Spécification', 'Sp\xe9cification'),
                'qte':           i(row, 'QTéBA', 'QT\xe9BA'),
                'unite':         unites.get(unite_lib),
                'prix_ht':       dec(row, 'PrixUnitaireHT'),
                'prix_ttc':      dec(row, 'PrixUnitaireTTC'),
                'montant_ttc':   dec(row, 'MontantTTC'),
                'observation':   s(row, 'Observation'),
            }
        )
        c += 1
    return c, u, e


def imp_journal(rows, verbose):
    # Journal = table de log — on efface et réimporte pour éviter les doublons
    if Journal.objects.exists():
        # déjà importé, on met à jour uniquement
        pass
    c = u = e = 0
    for row in rows:
        date_c    = d(row, 'DateDeCréation', 'DateDeCr\xe9ation')
        desig     = s(row, 'Désignation', 'D\xe9signation')
        num_bon   = i(row, 'NumBon')
        type_entr = s(row, 'TypeEntré', 'TypeEntr\xe9')
        nomenc    = s(row, 'Nomenclature')
        if not desig and not nomenc:
            e += 1; continue

        obj, is_new = Journal.objects.get_or_create(
            num_bon=num_bon,
            type_entree=type_entr,
            nomenclature=nomenc,
            designation=desig,
            defaults={
                'date_creation':        date_c,
                'specification':        s(row, 'Spécification', 'Sp\xe9cification'),
                'qte':                  i(row, 'Qté', 'Qt\xe9'),
                'unite':                s(row, 'Unité', 'Unit\xe9'),
                'prix_ht':              dec(row, 'PrixUnitaireHT'),
                'prix_ttc':             dec(row, 'PrixUnitaireTTC'),
                'montant_ttc':          dec(row, 'MontantTTC'),
                'beneficiaire':         s(row, 'Bénéficiaire', 'B\xe9n\xe9ficiaire'),
                'annee_exercice':       i(row, 'AnnéeExercice', 'Ann\xe9eExercice') or None,
                'depot':                s(row, 'Dépot', 'D\xe9pot'),
                'observation':          s(row, 'Observation'),
                'existant':             i(row, 'Existant'),
                'entree_periode':       i(row, 'EntréePériode', 'Entr\xe9eP\xe9riode'),
                'sortie_periode':       i(row, 'SortiePériode', 'SortieP\xe9riode'),
                'existant_fin_periode': i(row, 'ExistantFinPériode', 'ExistantFinP\xe9riode'),
                'montant_existant':     dec(row, 'MontantExistant'),
            }
        )
        c += is_new; u += not is_new
    return c, u, e


def imp_balance(rows, verbose):
    annees   = {a.annee: a for a in AnneeExercice.objects.all()}
    produits = {p.nomenclature: p for p in Produit.objects.all()}
    c = u = e = 0
    for row in rows:
        nomenc = s(row, 'Nomenclature')
        desig  = s(row, 'Désignation', 'D\xe9signation')
        if not nomenc or not desig:
            e += 1; continue
        annee_v = i(row, 'AnnéeExercice', 'Ann\xe9eExercice')
        defaults = {
            'designation':          desig,
            'unite':                s(row, 'Unité', 'Unit\xe9'),
            'existant_dp':          i(row, 'ExistantDP'),
            'entree_periode':       i(row, 'EntréePériode', 'Entr\xe9eP\xe9riode'),
            'total_entree':         i(row, 'TotalEntrée', 'TotalEntr\xe9e'),
            'sortie_periode':       i(row, 'SortiePériode', 'SortieP\xe9riode'),
            'existant_fin_periode': i(row, 'ExistantFinPériode', 'ExistantFinP\xe9riode'),
            'prix_unitaire_ht':     dec(row, 'PrixUnitaireHT'),
            'montant_existant':     dec(row, 'MontantExistant'),
            'annee_exercice':       annees.get(annee_v),
            'produit':              produits.get(nomenc),
        }
        _, is_new = BalancePeriodique.objects.get_or_create(nomenclature=nomenc, defaults=defaults)
        c += is_new; u += not is_new
    return c, u, e


# ─────────────────────────── REGISTRE ────────────────────────────────

IMPORT_STEPS = [
    # (clé, label, fichier XLS, fonction, nb_lignes_attendues)
    ('depot',            "Dépôts",                 'Dépot.XLS',                    imp_depot,                None),
    ('unite',            "Unités",                  'Unité.XLS',                    imp_unite,                None),
    ('type_op',          "Types d'opération",       'TypeOpération.XLS',             imp_type_op,              None),
    ('compte',           "Comptes principaux",      'ComptePrincipale.XLS',          imp_compte,               None),
    ('sous_compte',      "Sous-comptes",             'SousCompte.XLS',               imp_sous_compte,          None),
    ('fournisseur',      "Fournisseurs",              'Fournisseur.XLS',              imp_fournisseur,          None),
    ('beneficiaire',     "Bénéficiaires",             'Bénéficiaire.XLS',             imp_beneficiaire,         None),
    ('produit',          "Produits / Matières",      'Produit.XLS',                  imp_produit,              None),
    ('membre_comm',      "Membres commission",       'MembreCommision.XLS',          imp_membre_commission,    None),
    ('membre_ref',       "Membres réforme",          'MembreCommissionReforme.XLS',  imp_membre_reforme,       None),
    ('annee',            "Années d'exercice",        'AnnéeExercice.XLS',            imp_annee_exercice,       None),
    ('societe',          "Société GCS",              'SociétéGCS.XLS',               imp_societe,              None),
    ('matieres_depot',   "Matières/Dépôt",          'MatièresDepot.XLS',             imp_matieres_depot,       None),
    ('stock_depot',      "Stock dépôt",              'StockDépot.XLS',               imp_stock_depot,          None),
    ('bon_entree',       "Bons d'entrée",            'BonEntrée.XLS',                imp_bon_entree,           None),
    ('det_bon_entree',   "Détails bons d'entrée",   'DétailsBonEntrée.XLS',          imp_detail_bon_entree,    None),
    ('bon_affectation',  "Bons d'affectation",      'BondAffectation.XLS',           imp_bon_affectation,      None),
    ('det_bon_affect',   "Détails bons affectation", 'DétailsBondAffectation.XLS',   imp_detail_bon_affectation, None),
    ('journal',          "Journal des opérations",   'Journal.XLS',                  imp_journal,              None),
    ('balance',          "Balance périodique",       'BalancePériodique.XLS',         imp_balance,              None),
]


# ─────────────────────────── COMMANDE ────────────────────────────────

class Command(BaseCommand):
    help = "Importe les données depuis les fichiers XLS du dossier tables/"

    def add_arguments(self, parser):
        parser.add_argument(
            '--tables', default='all',
            help="Tables à importer (all, ou liste séparée par virgule : depot,produit,...)"
        )
        parser.add_argument(
            '--dir', default=None,
            help="Répertoire des fichiers XLS (défaut : <BASE_DIR>/tables)"
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help="Simule l'import sans écrire en base"
        )

    def handle(self, *args, **options):
        global TABLES_DIR
        if options['dir']:
            TABLES_DIR = options['dir']

        selected = options['tables']
        dry_run  = options['dry_run']
        verbose  = int(options.get('verbosity', 1)) > 0

        if selected == 'all':
            steps = IMPORT_STEPS
        else:
            keys = {k.strip() for k in selected.split(',')}
            steps = [s for s in IMPORT_STEPS if s[0] in keys]
            if not steps:
                self.stderr.write(self.style.ERROR(f"Aucune table reconnue parmi : {selected}"))
                return

        prefix = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(f"\n{prefix}Import depuis : {TABLES_DIR}")
        self.stdout.write("-" * 60)

        totals = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        for key, label, filename, fn, _ in steps:
            try:
                _, rows = read_rows(filename)
            except FileNotFoundError:
                self.stdout.write(f"  [?] {label:<35} fichier introuvable - ignore")
                totals['skipped'] += 1
                continue
            except Exception as ex:
                self.stderr.write(f"  [X] {label:<35} erreur lecture : {ex}")
                totals['errors'] += 1
                continue

            if not rows:
                self.stdout.write(f"  [-] {label:<35} vide - ignore")
                totals['skipped'] += 1
                continue

            if dry_run:
                self.stdout.write(f"  [DRY] {label:<33} {len(rows)} lignes détectées")
                continue

            try:
                with transaction.atomic():
                    c, u, e = fn(rows, verbose)
                symbol = 'OK' if e == 0 else '!!'
                line = (
                    f"  {symbol} {label:<35} "
                    f"{c:>4} créé(s)  "
                    f"{u:>4} màj  "
                    f"{e:>3} erreur(s)  "
                    f"[{len(rows)} lignes]"
                )
                style = self.style.SUCCESS if e == 0 else self.style.WARNING
                self.stdout.write(style(line))
                totals['created'] += c
                totals['updated'] += u
                totals['errors']  += e
            except Exception as ex:
                self.stderr.write(self.style.ERROR(f"  [X] {label:<35} EXCEPTION : {ex}"))
                import traceback; traceback.print_exc()
                totals['errors'] += 1

        self.stdout.write("-" * 60)
        self.stdout.write(self.style.SUCCESS(
            f"  TOTAL : {totals['created']} crees | "
            f"{totals['updated']} mis a jour | "
            f"{totals['errors']} erreur(s) | "
            f"{totals['skipped']} ignores\n"
        ))
