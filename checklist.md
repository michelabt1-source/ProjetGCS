Checklist complète — Fonctionnalité Balance Périodique

Comprendre la fonctionnalité
Identifier l’objectif : produire une vue périodique des stocks/comptes sur une période donnée.
Savoir que la source de vérité est le Journal, pas uniquement le modèle de balance.
Comprendre les colonnes principales :
Existant début
Entrée période
Total entrées
Sortie période
Existant fin
Prix unitaire
Montant existant
Parcours technique à reproduire
Vérifier que la route d’accès existe :
Liste de la balance périodique
État imprimable de la balance périodique
Vérifier que la vue reçoit les dates via les paramètres GET :
date_debut
date_fin
Vérifier que la vue parse les dates et appelle le moteur de calcul.
Vérifier que le moteur retourne une liste de lignes par nomenclature.
Vérifier que le template affiche le résultat et les totaux.
Logique métier à maîtriser
Regrouper tous les mouvements par nomenclature.
Trier dans un ordre stable :
par nomenclature
puis par date
puis par identifiant
Appliquer les règles de calcul selon le type de mouvement :
Bon d’entrée : augmente l’existant et l’entrée période
Sortie définitive : diminue l’existant et ajoute à la sortie période
Affectation : impacte l’état “en service”
Retour affectation : inverse l’impact de l’affectation
Sortie provisoire : passe en sortie provisoire
Retour sortie provisoire : inverse l’impact
Mutation : ne change pas l’état global de façon directe
Calculs essentiels à respecter
Calculer l’existant de début à partir de l’historique avant la période.
Calculer l’entrée période uniquement pour les mouvements dans la période.
Calculer la sortie période uniquement pour les sorties définitives dans la période.
Calculer l’existant fin :
existant_fin = existant_debut + entrée_période - sortie_def_période
Calculer l’attente d’affectation :
en_attente = max(0, existant_fin - en_service - en_sortie_prov)
Calculer le montant existant :
montant_existant = existant_fin × prix_unitaire
Champs à préparer pour chaque ligne
nomenclature
designation
unite
existant_debut
entree_periode
total_entrees
sortie_def_periode
en_attente_affectation
en_service
en_sortie_provisoire
existant_fin
prix_unitaire
montant_existant
Vérifications fonctionnelles
Vérifier le cas sans dates : toute l’historique est pris en compte.
Vérifier le cas avec date de début seulement.
Vérifier le cas avec date de fin seulement.
Vérifier les totaux du tableau.
Vérifier que les lignes vides ou sans mouvement ne cassent pas l’affichage.
Vérifier l’état imprimable et le bouton “État officiel”.
Interface utilisateur à contrôler
Vérifier la présence du formulaire de filtrage par dates.
Vérifier que le bouton “État officiel” conserve les filtres.
Vérifier que le template affiche correctement les totaux.
Vérifier que le template imprimable est propre pour l’impression.
Points sensibles à ne pas oublier
Les mouvements internes ne doivent pas fausser l’existant global.
Le calcul est répliqué à partir du Journal, donc toute nouvelle opération doit être prise en compte.
L’ordre des mouvements est important pour la cohérence des soldes.
Le prix unitaire doit venir du dernier prix trouvé dans l’historique.

---------Pipeline--------------

Données --> Preprocessing

Variable : {
    ->type {
        ->qualitative
        ->quantitative     
    }
    ->Valeur
    ->format
    ->Role{
        ->Explicative
        -> A expliquer
    } 
}