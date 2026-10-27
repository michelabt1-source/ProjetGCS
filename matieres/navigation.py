"""Navigation de l'application : source unique pour la barre latérale, le fil
d'Ariane et la palette de commandes (Ctrl+K).

Chaque entrée déclare :
  · ``url``     nom d'URL Django (namespacé) à inverser ;
  · ``match``   expressions régulières testées sur ``url_name`` pour savoir si
                l'entrée est la page courante (par défaut : le nom d'URL exact) ;
  · ``params``  paramètres GET ajoutés au lien et exigés pour l'état actif ;
  · ``roles``   rôles autorisés (``ProfilUtilisateur.role``) — absent = tous ;
  · ``icon``    clé de ``ICONS``.

Ajouter un module (ex. Suivi budgétaire) revient à ajouter un élément à
``MODULES`` et ses sections à ``NAV``.
"""
import re
from urllib.parse import urlencode

from django.urls import NoReverseMatch, reverse

# Tracés SVG (viewBox 24×24, trait) — une icône peut combiner plusieurs tracés.
ICONS = {
    'home': ['M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6'],
    'bank': ['M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4z'],
    'building': ['M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5'],
    'office': ['M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4'],
    'inbox': ['M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4'],
    'truck': ['M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z', 'M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0'],
    'folder': ['M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z'],
    'users': ['M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z'],
    'archive': ['M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4'],
    'download': ['M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12'],
    'switch': ['M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4'],
    'logout': ['M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1'],
    'reply': ['M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6'],
    'arrow-down': ['M16 17l-4 4m0 0l-4-4m4 4V3'],
    'document': ['M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'],
    'cog': ['M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z', 'M15 12a3 3 0 11-6 0 3 3 0 016 0z'],
    'clipboard-check': ['M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-5 8l2 2 4-4'],
    'clipboard': ['M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2'],
    'clipboard-list': ['M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01m-.01 4h.01'],
    'arrow-right': ['M13 7l5 5m0 0l-5 5m5-5H6'],
    'store': ['M3 9l1-5h16l1 5', 'M3 9a2 2 0 004 0 2 2 0 004 0 2 2 0 004 0 2 2 0 004 0', 'M4 9v10a1 1 0 001 1h14a1 1 0 001-1V9', 'M9 21v-6a1 1 0 011-1h4a1 1 0 011 1v6'],
    'chat': ['M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z'],
    'book': ['M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253'],
    'ledger': ['M4 6h16M4 10h16M4 14h16M4 18h7', 'M15 18l2 2 4-4'],
    'clock': ['M12 6v6l4 2m5 0a9 9 0 11-18 0 9 9 0 0118 0z'],
    'chart': ['M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'],
    'globe': ['M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064'],
    'pin': ['M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z', 'M15 11a3 3 0 11-6 0 3 3 0 016 0z'],
    'report': ['M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'],
    'tag': ['M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z'],
    'filter': ['M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z'],
    'user-group': ['M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z'],
    'calendar': ['M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z'],
    'user-circle': ['M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z'],
    'upload': ['M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12'],
    'trash': ['M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16'],
    'wallet': ['M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z'],
    'cube': ['M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4'],
}

# Modules de l'application (sélecteur en haut de la barre latérale).
MODULES = [
    {'key': 'matieres', 'label': 'Comptabilité des matières', 'short': 'Matières', 'icon': 'cube', 'available': True},
    {'key': 'budget', 'label': 'Suivi budgétaire', 'short': 'Budget', 'icon': 'wallet', 'available': False},
]

NAV = [
    {
        'key': 'demandes', 'label': 'Demandes & achats',
        'items': [
            {'label': 'Expressions de besoins', 'url': 'matieres:expressions_list', 'icon': 'chat',
             'match': [r'^expressions?_'], 'hint': 'Besoins exprimés par les services', 'badge': 'expressions'},
            {'label': 'Bons de commande de service', 'url': 'matieres:bons_commande_service_list', 'icon': 'clipboard-check',
             'match': [r'^bons?_commande_service(?!_a_livrer$|_livrer$)']},
            {'label': 'BCS à livrer', 'url': 'matieres:bons_commande_service_a_livrer', 'icon': 'arrow-right',
             'match': [r'^bons_commande_service_a_livrer$', r'^bon_commande_service_livrer$'],
             'roles': ('comptable',)},
            {'label': 'Marchés', 'url': 'matieres:marches_list', 'icon': 'store', 'match': [r'^marches?_']},
        ],
    },
    {
        'key': 'groupe1', 'label': 'Mouvements · 1er groupe',
        'items': [
            {'label': "Bons d'entrée", 'url': 'matieres:bons_entree_list', 'icon': 'download', 'match': [r'^bons?_entree']},
            {'label': "Bons d'affectation", 'url': 'matieres:bons_affectation_list', 'icon': 'switch', 'match': [r'^bons?_affectation']},
            {'label': 'Sorties provisoires', 'url': 'matieres:bons_sortie_prov_list', 'icon': 'logout', 'match': [r'^bons?_sortie_prov']},
            {'label': "Retours d'affectation", 'url': 'matieres:bons_retour_affectation_list', 'icon': 'reply', 'match': [r'retour_affectation']},
            {'label': 'Retours de sortie provisoire', 'url': 'matieres:bons_retour_sortie_prov_list', 'icon': 'arrow-down', 'match': [r'retour_sortie_prov']},
            {'label': 'Bordereaux de mutation', 'url': 'matieres:bons_mutation_list', 'icon': 'switch', 'match': [r'mutation']},
            {'label': 'Sorties définitives', 'url': 'matieres:bons_sortie_def_list', 'icon': 'document',
             'match': [r'^bons?_sortie_def_(list|detail|create)$']},
            {'label': 'Réformes', 'url': 'matieres:bons_sortie_def_g1_list', 'icon': 'cog', 'match': [r'sortie_def_g1']},
        ],
    },
    {
        'key': 'groupe2', 'label': 'Mouvements · 2e groupe',
        'items': [
            {'label': 'Sorties définitives (consommables)', 'url': 'matieres:bons_sortie_def_g2_list', 'icon': 'document', 'match': [r'sortie_def_g2']},
        ],
    },
    {
        'key': 'comptabilite', 'label': 'Comptabilité & états',
        'items': [
            {'label': 'Stock par dépôt', 'url': 'matieres:stock_depot_list', 'icon': 'clipboard'},
            {'label': 'Livre journal', 'url': 'matieres:journal_list', 'icon': 'book', 'match': [r'^journal_']},
            {'label': 'Grand livre', 'url': 'matieres:grand_livre', 'icon': 'ledger', 'match': [r'^grand_livre']},
            {'label': 'Fiches de stock', 'url': 'matieres:inventaire_individuel', 'icon': 'clipboard-list',
             'match': [r'^inventaire_individuel$', r'^fiche_stock']},
            {'label': 'Balance périodique', 'url': 'matieres:balance_periodique_list', 'icon': 'clock', 'match': [r'^balance_periodique']},
            {'label': 'Balance générale des comptes', 'url': 'matieres:balance_list', 'icon': 'chart',
             'match': [r'^balance_list$', r'^balance_general']},
        ],
    },
    {
        'key': 'inventaires', 'label': 'Inventaires',
        'items': [
            {'label': 'Inventaire global', 'url': 'matieres:inventaire_global', 'icon': 'globe'},
            {'label': 'Inventaire par dépôt', 'url': 'matieres:inventaire_depot', 'icon': 'pin'},
            {'label': 'Relevé récapitulatif · G1', 'url': 'matieres:releve_recapitulatif', 'icon': 'report',
             'params': {'groupe': '1'}, 'default_params': {'groupe': '1'}},
            {'label': 'Inventaire contradictoire · G1', 'url': 'matieres:inventaire_individuel_etat', 'icon': 'clipboard',
             'params': {'groupe': '1'}, 'default_params': {'groupe': '1'}},
            {'label': 'Relevé récapitulatif · G2', 'url': 'matieres:releve_recapitulatif', 'icon': 'report',
             'params': {'groupe': '2'}},
            {'label': 'Inventaire contradictoire · G2', 'url': 'matieres:inventaire_individuel_etat', 'icon': 'clipboard',
             'params': {'groupe': '2'}},
        ],
    },
    {
        'key': 'referentiels', 'label': 'Référentiels',
        'items': [
            {'label': 'Produits', 'url': 'matieres:produits_list', 'icon': 'inbox', 'match': [r'^produits?_']},
            {'label': 'Comptes principaux', 'url': 'matieres:compte_principal_list', 'icon': 'bank'},
            {'label': 'Sous-comptes', 'url': 'matieres:sous_compte_list', 'icon': 'building'},
            {'label': 'Fournisseurs', 'url': 'matieres:fournisseurs_list', 'icon': 'truck', 'match': [r'^fournisseurs?_']},
            {'label': 'Services', 'url': 'matieres:service_list', 'icon': 'office', 'match': [r'^service_']},
            {'label': 'Bureaux', 'url': 'matieres:bureau_list', 'icon': 'folder', 'match': [r'^bureau_']},
            {'label': 'Bénéficiaires', 'url': 'matieres:beneficiaires_list', 'icon': 'users', 'match': [r'^beneficiaires?_']},
            {'label': 'Dépôts', 'url': 'matieres:depots_list', 'icon': 'archive'},
        ],
    },
    {
        'key': 'administration', 'label': 'Administration',
        'items': [
            {'label': 'Société', 'url': 'matieres:societe_view', 'icon': 'building'},
            {'label': "Années d'exercice", 'url': 'matieres:annee_exercice_list', 'icon': 'calendar'},
            {'label': 'Unités', 'url': 'matieres:unite_list', 'icon': 'tag'},
            {'label': "Types d'opération", 'url': 'matieres:type_op_list', 'icon': 'filter'},
            {'label': 'Membres de commission', 'url': 'matieres:membre_commission_list', 'icon': 'users'},
            {'label': 'Commission de réforme', 'url': 'matieres:membre_reforme_list', 'icon': 'cog'},
            {'label': 'Matières par dépôt', 'url': 'matieres:matieres_depot_config', 'icon': 'archive'},
            {'label': 'Profils', 'url': 'matieres:profil_list', 'icon': 'user-circle'},
            {'label': 'Utilisateurs', 'url': 'admin:index', 'icon': 'user-group', 'match': [], 'external': True},
            {'label': 'Import Excel', 'url': 'matieres:import_index', 'icon': 'upload',
             'match': [r'^import_index$', r'^import_template$']},
        ],
    },
]

HOME = {'label': 'Tableau de bord', 'url': 'matieres:dashboard', 'icon': 'home', 'match': [r'^dashboard$']}


def _badge_expressions(user):
    from .views import _expressions_visibles, expressions_a_traiter
    statuts = expressions_a_traiter(user)
    return _expressions_visibles(user).filter(statut__in=statuts).count() if statuts else 0


# Compteurs « à traiter » affichés à côté d'une entrée (une requête par page affichée).
BADGES = {'expressions': _badge_expressions}


def _role(user):
    profil = getattr(user, 'profil_utilisateur', None)
    return getattr(profil, 'role', None)


def _allowed(item, user, role):
    roles = item.get('roles')
    return not roles or user.is_superuser or role in roles


def _href(item):
    try:
        href = reverse(item['url'])
    except NoReverseMatch:
        return None
    if item.get('params'):
        href += '?' + urlencode(item['params'])
    return href


def _is_active(item, url_name, query):
    patterns = item.get('match')
    if patterns is None:
        patterns = [r'^%s$' % re.escape(item['url'].split(':')[-1])]
    if not any(re.search(p, url_name) for p in patterns):
        return False
    for key, value in (item.get('params') or {}).items():
        current = query.get(key) or (item.get('default_params') or {}).get(key)
        if current != value:
            return False
    return True


def _build_item(item, url_name, query, user=None):
    href = _href(item)
    if href is None:
        return None
    badge = BADGES[item['badge']](user) if item.get('badge') and user is not None else 0
    return {
        'badge': badge,
        'label': item['label'],
        'href': href,
        'icon': ICONS.get(item.get('icon'), ICONS['document']),
        'hint': item.get('hint', ''),
        'external': item.get('external', False),
        'active': bool(url_name) and _is_active(item, url_name, query),
        # Page racine de l'entrée (sa liste) : le fil d'Ariane n'y ajoute pas le titre de page.
        'is_root': url_name == item['url'].split(':')[-1],
    }


def navigation(request):
    """Contexte de navigation : sections filtrées par rôle, entrée active, fil d'Ariane."""
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {}

    match = getattr(request, 'resolver_match', None)
    url_name = match.url_name if match and match.namespace == 'matieres' else ''
    role = _role(user)

    home = _build_item(HOME, url_name, request.GET)
    sections, current_section, current_item = [], None, home if home and home['active'] else None
    for section in NAV:
        items = [built for item in section['items'] if _allowed(item, user, role)
                 for built in [_build_item(item, url_name, request.GET, user)] if built]
        if not items:
            continue
        active = next((i for i in items if i['active']), None)
        if active and current_item is None:
            current_section, current_item = section, active
        sections.append({'key': section['key'], 'label': section['label'],
                         'items': items, 'open': active is not None})

    palette = [{'label': home['label'], 'section': 'Général', 'href': home['href']}] if home else []
    palette += [{'label': i['label'], 'section': s['label'], 'href': i['href'], 'hint': i['hint']}
                for s in sections for i in s['items']]

    return {
        'nav_home': home,
        'nav_sections': sections,
        'nav_modules': [dict(m, icon=ICONS[m['icon']]) for m in MODULES],
        'nav_current_section': current_section['label'] if current_section else '',
        'nav_current_item': current_item,
        'nav_palette': palette,
        'nav_role_label': user.profil_utilisateur.get_role_display() if role else (
            'Administrateur' if user.is_superuser else ''),
    }
