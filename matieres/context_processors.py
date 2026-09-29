from django.urls import Resolver404, resolve, reverse

# Pages dont la sortie ne suit pas la règle générale « premier segment de l'URL ».
FERMER_OVERRIDES = {
    'fiche_stock': 'matieres:inventaire_individuel',
    'bon_commande_service_livrer': 'matieres:bons_commande_service_a_livrer',
}


def fermer_url(request):
    """URL du bouton standard « Fermer » affiché en haut de chaque page.

    Un bon, une fiche ou un formulaire ferme vers sa liste (premier segment de
    l'URL, ex. /bons-commande-service/12/ → /bons-commande-service/) ; une liste
    ou une page sans liste parente ferme vers l'accueil.
    """
    match = getattr(request, 'resolver_match', None)
    if match is None or match.namespace != 'matieres' or match.url_name == 'dashboard':
        return {'fermer_url': None}

    override = FERMER_OVERRIDES.get(match.url_name)
    if override:
        return {'fermer_url': reverse(override)}

    parent = '/' + request.path.strip('/').split('/')[0] + '/'
    if parent != request.path:
        try:
            resolve(parent)
            return {'fermer_url': parent}
        except Resolver404:
            pass
    return {'fermer_url': reverse('matieres:dashboard')}
