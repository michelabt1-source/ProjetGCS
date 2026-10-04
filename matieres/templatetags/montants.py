from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django import template

register = template.Library()

UNITES = ['zéro', 'un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf',
          'dix', 'onze', 'douze', 'treize', 'quatorze', 'quinze', 'seize',
          'dix-sept', 'dix-huit', 'dix-neuf']
DIZAINES = {2: 'vingt', 3: 'trente', 4: 'quarante', 5: 'cinquante', 6: 'soixante'}


def _moins_de_cent(n):
    if n < 20:
        return UNITES[n]
    d, u = divmod(n, 10)
    if d in (7, 9):                       # 70-79 → soixante-dix…, 90-99 → quatre-vingt-dix…
        base = 'soixante' if d == 7 else 'quatre-vingt'
        if d == 7 and u == 1:
            return 'soixante et onze'
        return f'{base}-{UNITES[10 + u]}'
    if d == 8:
        return 'quatre-vingts' if u == 0 else f'quatre-vingt-{UNITES[u]}'
    if u == 0:
        return DIZAINES[d]
    if u == 1:
        return f'{DIZAINES[d]} et un'
    return f'{DIZAINES[d]}-{UNITES[u]}'


def _moins_de_mille(n, final=True):
    """final=False : le nombre est suivi de « mille », donc « cent » et « quatre-vingt » restent au singulier."""
    c, r = divmod(n, 100)
    if c == 0:
        mots = _moins_de_cent(r)
    else:
        cent = 'cent' if c == 1 else f'{UNITES[c]} cent'
        if r == 0:
            mots = cent + ('s' if c > 1 and final else '')
        else:
            mots = f'{cent} {_moins_de_cent(r)}'
    if not final and mots.endswith('quatre-vingts'):
        mots = mots[:-1]
    return mots


def entier_en_lettres(n):
    if n == 0:
        return 'zéro'
    parties = []
    for valeur, sing, plur in ((10**9, 'milliard', 'milliards'), (10**6, 'million', 'millions')):
        q, n = divmod(n, valeur)
        if q:
            parties.append(f'{_moins_de_mille(q)} {sing if q == 1 else plur}' if q < 1000
                           else f'{entier_en_lettres(q)} {plur}')
    q, n = divmod(n, 1000)
    if q:
        parties.append('mille' if q == 1 else f'{_moins_de_mille(q, final=False)} mille')
    if n:
        parties.append(_moins_de_mille(n))
    return ' '.join(parties)


@register.filter
def en_lettres(valeur, devise='francs CFA'):
    """Montant en toutes lettres : 150000 → « Cent cinquante mille francs CFA »."""
    try:
        montant = Decimal(str(valeur or 0)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return ''
    signe = 'moins ' if montant < 0 else ''
    montant = abs(montant)
    entier = int(montant)
    centimes = int((montant - entier) * 100)
    texte = f'{signe}{entier_en_lettres(entier)}'
    if devise == 'francs CFA' and entier < 2:
        devise = 'franc CFA'
    if devise:
        texte += (' de ' if entier >= 10**6 and entier % 10**6 == 0 else ' ') + devise
    if centimes:
        texte += f' et {entier_en_lettres(centimes)} centime' + ('s' if centimes > 1 else '')
    return texte[0].upper() + texte[1:]
