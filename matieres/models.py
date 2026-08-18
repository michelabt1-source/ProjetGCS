from django.db import models


class AnneeExercice(models.Model):
    annee = models.IntegerField(verbose_name="Année")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")

    class Meta:
        verbose_name = "Année d'exercice"
        verbose_name_plural = "Années d'exercice"
        ordering = ['-annee']

    def __str__(self):
        return str(self.annee)


class Depot(models.Model):
    code = models.CharField(max_length=20, unique=True, verbose_name="Code dépôt")

    class Meta:
        verbose_name = "Dépôt"
        verbose_name_plural = "Dépôts"
        ordering = ['code']

    def __str__(self):
        return self.code


class Service(models.Model):
    code     = models.CharField(max_length=20, unique=True, verbose_name="Code")
    libelle  = models.CharField(max_length=200, verbose_name="Libellé")
    responsable = models.CharField(max_length=200, blank=True, verbose_name="Responsable")
    telephone   = models.CharField(max_length=30,  blank=True, verbose_name="Téléphone")
    actif    = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.libelle}"

    @property
    def nb_bureaux(self):
        return self.bureaux.filter(actif=True).count()


class Bureau(models.Model):
    service     = models.ForeignKey(
        Service, on_delete=models.CASCADE,
        related_name='bureaux', verbose_name="Service"
    )
    code        = models.CharField(max_length=20, verbose_name="Code")
    libelle     = models.CharField(max_length=200, verbose_name="Libellé")
    responsable = models.CharField(max_length=200, blank=True, verbose_name="Responsable")
    actif       = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Bureau"
        verbose_name_plural = "Bureaux"
        unique_together = ('service', 'code')
        ordering = ['service__code', 'code']

    def __str__(self):
        return f"{self.service.code}/{self.code} — {self.libelle}"


class Beneficiaire(models.Model):
    nom         = models.CharField(max_length=100, verbose_name="Nom")
    responsable = models.CharField(max_length=100, blank=True, verbose_name="Responsable")
    bureau      = models.ForeignKey(
        Bureau, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='beneficiaires', verbose_name="Bureau"
    )

    class Meta:
        verbose_name = "Bénéficiaire"
        verbose_name_plural = "Bénéficiaires"
        ordering = ['nom']

    def __str__(self):
        return self.nom

    @property
    def service(self):
        return self.bureau.service if self.bureau else None


class ComptePrincipale(models.Model):
    num_compte = models.IntegerField(unique=True, verbose_name="N° Compte")
    famille = models.CharField(max_length=200, verbose_name="Famille")

    class Meta:
        verbose_name = "Compte principal"
        verbose_name_plural = "Comptes principaux"
        ordering = ['num_compte']

    def __str__(self):
        return f"{self.num_compte} - {self.famille}"


class SousCompte(models.Model):
    compte_principal = models.ForeignKey(
        ComptePrincipale, on_delete=models.CASCADE,
        related_name='sous_comptes', verbose_name="Compte principal"
    )
    compte = models.CharField(max_length=20, blank=True, verbose_name="Compte")
    num_sous_compte = models.FloatField(verbose_name="N° Sous-compte")
    famille_sc = models.CharField(max_length=200, verbose_name="Famille sous-compte")
    num_cb = models.CharField(max_length=30, blank=True, verbose_name="NumCB")
    intitule_cb = models.CharField(max_length=255, blank=True, verbose_name="Intitulé CB")

    class Meta:
        verbose_name = "Sous-compte"
        verbose_name_plural = "Sous-comptes"
        ordering = ['num_sous_compte']

    def __str__(self):
        return f"{self.compte or self.num_sous_compte} - {self.famille_sc}"


class Fournisseur(models.Model):
    nom = models.CharField(max_length=200, verbose_name="Fournisseur")
    adresse = models.CharField(max_length=300, blank=True, verbose_name="Adresse")
    telephone = models.CharField(max_length=30, blank=True, verbose_name="Téléphone")
    fax = models.CharField(max_length=30, blank=True, verbose_name="Fax")
    code_postal = models.CharField(max_length=20, blank=True, verbose_name="Code postal")
    ville = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    region = models.CharField(max_length=100, blank=True, verbose_name="Région")
    pays = models.CharField(max_length=100, blank=True, verbose_name="Pays")
    fonction = models.CharField(max_length=100, blank=True, verbose_name="Fonction")

    class Meta:
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Unite(models.Model):
    libelle = models.CharField(max_length=50, verbose_name="Unité")

    class Meta:
        verbose_name = "Unité"
        verbose_name_plural = "Unités"

    def __str__(self):
        return self.libelle


class TypeOperation(models.Model):
    libelle = models.CharField(max_length=100, verbose_name="Type d'opération")

    class Meta:
        verbose_name = "Type d'opération"
        verbose_name_plural = "Types d'opération"

    def __str__(self):
        return self.libelle


class Profil(models.Model):
    role = models.CharField(max_length=100, verbose_name="Rôle")

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profils"

    def __str__(self):
        return self.role


class SocieteGCS(models.Model):
    nom = models.CharField(max_length=200, verbose_name="Nom société")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True, verbose_name="Logo")
    telephone = models.CharField(max_length=30, blank=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, verbose_name="Email")
    adresse = models.CharField(max_length=300, blank=True, verbose_name="Adresse")
    fax = models.CharField(max_length=30, blank=True, verbose_name="Fax")
    ministere = models.CharField(max_length=200, blank=True, verbose_name="Ministère")
    administrateur = models.CharField(max_length=100, blank=True, verbose_name="Administrateur")
    comptable = models.CharField(max_length=100, blank=True, verbose_name="Comptable")
    receptionnaire = models.CharField(max_length=100, blank=True, verbose_name="Réceptionnaire")
    responsable = models.CharField(max_length=100, blank=True, verbose_name="Responsable")
    ville = models.CharField(max_length=100, blank=True, verbose_name="Ville")

    class Meta:
        verbose_name = "Société GCS"

    def __str__(self):
        return self.nom


class MembreCommission(models.Model):
    nom = models.CharField(max_length=200, verbose_name="Nom")
    qualite = models.CharField(max_length=200, verbose_name="Qualité")

    class Meta:
        verbose_name = "Membre de commission"
        verbose_name_plural = "Membres de commission"

    def __str__(self):
        return self.nom


class MembreCommissionReforme(models.Model):
    nom = models.CharField(max_length=200, verbose_name="Nom")
    qualite = models.CharField(max_length=200, verbose_name="Qualité")

    class Meta:
        verbose_name = "Membre de commission de réforme"
        verbose_name_plural = "Membres de commission de réforme"

    def __str__(self):
        return self.nom


class ProfilCommission(models.Model):
    qualite = models.CharField(max_length=200, verbose_name="Qualité")

    class Meta:
        verbose_name = "Profil commission"
        verbose_name_plural = "Profils commission"

    def __str__(self):
        return self.qualite


class Produit(models.Model):
    compte_principal = models.ForeignKey(
        ComptePrincipale, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='produits', verbose_name="Compte principal"
    )
    sous_compte = models.ForeignKey(
        SousCompte, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='produits', verbose_name="Sous-compte"
    )
    nomenclature = models.CharField(max_length=30, unique=True, verbose_name="Nomenclature")
    designation = models.CharField(max_length=300, verbose_name="Désignation")
    stock_global = models.IntegerField(default=0, verbose_name="Stock global")
    qte_affectation = models.IntegerField(default=0, verbose_name="Qté affectée")
    qte_sd = models.IntegerField(default=0, verbose_name="Qté sortie définitive")
    entree = models.IntegerField(default=0, verbose_name="Entrée")
    unite = models.ForeignKey(
        Unite, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Unité"
    )
    specification = models.CharField(max_length=300, blank=True, verbose_name="Spécification")
    observation = models.TextField(blank=True, verbose_name="Observation")
    qte_sp = models.IntegerField(default=0, verbose_name="Qté sortie provisoire")

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['nomenclature']

    def __str__(self):
        return f"{self.nomenclature} - {self.designation}"

    @property
    def stock_disponible(self):
        return self.stock_global - self.qte_affectation - self.qte_sp

    @property
    def groupe(self):
        """'1' si nomenclature 1x.xx.xx, '2' si 2x.xx.xx, '' sinon."""
        return self.nomenclature[0] if self.nomenclature else ''


class MatieresDepot(models.Model):
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, verbose_name="Dépôt")
    num_sous_compte = models.IntegerField(verbose_name="N° Sous-compte")

    class Meta:
        verbose_name = "Matières/Dépôt"
        verbose_name_plural = "Matières/Dépôts"

    def __str__(self):
        return f"{self.depot} - {self.num_sous_compte}"


class StockDepot(models.Model):
    produit = models.ForeignKey(
        Produit, on_delete=models.CASCADE, null=True, blank=True,
        related_name='stocks', verbose_name="Produit"
    )
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, verbose_name="Dépôt")
    nomenclature = models.CharField(max_length=30, verbose_name="Nomenclature")
    designation = models.CharField(max_length=300, verbose_name="Désignation")
    qte_stock = models.IntegerField(default=0, verbose_name="Quantité en stock")

    class Meta:
        verbose_name = "Stock Dépôt"
        verbose_name_plural = "Stocks Dépôts"
        ordering = ['depot', 'nomenclature']

    def __str__(self):
        return f"{self.nomenclature} | {self.depot} : {self.qte_stock}"


# ─────────────────────────── BONS D'ENTRÉE ───────────────────────────

class BonEntree(models.Model):
    num_bon = models.IntegerField(verbose_name="N° Bon")
    date_creation = models.DateField(verbose_name="Date de création")
    annee_exercice = models.ForeignKey(
        AnneeExercice, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Année d'exercice"
    )
    references_pieces = models.CharField(max_length=200, blank=True, verbose_name="Références pièces")
    type_entree = models.ForeignKey(
        TypeOperation, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Type d'entrée"
    )
    valide = models.BooleanField(default=False, verbose_name="Validé")
    depot = models.ForeignKey(Depot, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dépôt")
    fournisseur = models.ForeignKey(
        Fournisseur, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Fournisseur"
    )
    num_bon_engagement = models.IntegerField(default=0, verbose_name="N° Bon d'engagement")
    num_bon_commande = models.IntegerField(default=0, verbose_name="N° Bon de commande")
    num_pvc = models.CharField(max_length=50, blank=True, verbose_name="N° PVC")
    chapitre = models.CharField(max_length=100, blank=True, verbose_name="Chapitre")

    class Meta:
        verbose_name = "Bon d'entrée"
        verbose_name_plural = "Bons d'entrée"
        ordering = ['-date_creation', '-num_bon']

    def __str__(self):
        return f"BE-{self.num_bon:04d} ({self.date_creation})"

    def total_ttc(self):
        return sum(d.montant_ttc for d in self.details.all())


class DetailBonEntree(models.Model):
    bon_entree = models.ForeignKey(BonEntree, on_delete=models.CASCADE, related_name='details')
    produit = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Produit")
    designation = models.CharField(max_length=300, verbose_name="Désignation")
    nomenclature = models.CharField(max_length=30, verbose_name="Nomenclature")
    specification = models.CharField(max_length=300, blank=True, verbose_name="Spécification")
    qte = models.IntegerField(default=0, verbose_name="Quantité")
    unite = models.ForeignKey(Unite, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Unité")
    prix_ht = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix HT")
    prix_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix TTC")
    montant_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Montant TTC")
    observation = models.TextField(blank=True, verbose_name="Observation")

    class Meta:
        verbose_name = "Détail bon d'entrée"
        verbose_name_plural = "Détails bons d'entrée"

    def __str__(self):
        return f"{self.designation} x{self.qte}"


class Marche(models.Model):
    num_marche = models.CharField(max_length=100, unique=True, verbose_name="Numéro du marché")
    date_creation = models.DateField(verbose_name="Date de création")
    date_debut = models.DateField(null=True, blank=True, verbose_name="Date début")
    date_fin = models.DateField(null=True, blank=True, verbose_name="Date fin")
    fournisseur = models.ForeignKey(
        Fournisseur, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Fournisseur"
    )
    num_bon_engagement = models.IntegerField(default=0, verbose_name="N° Bon d'engagement")
    reference_marche = models.CharField(max_length=200, blank=True, verbose_name="Référence du marché")
    chapitre = models.CharField(max_length=100, blank=True, verbose_name="Chapitre")
    bon_entree = models.ForeignKey(
        BonEntree, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bon d'entrée lié"
    )

    class Meta:
        verbose_name = "Marché"
        verbose_name_plural = "Marchés"
        ordering = ['-date_creation', 'num_marche']

    def __str__(self):
        return f"{self.num_marche} ({self.date_creation})"

    def total_ttc(self):
        return sum(d.montant_ttc for d in self.details.all())


class DetailMarche(models.Model):
    marche = models.ForeignKey(Marche, on_delete=models.CASCADE, related_name='details')
    produit = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Produit")
    designation = models.CharField(max_length=300, verbose_name="Désignation")
    nomenclature = models.CharField(max_length=30, verbose_name="Nomenclature")
    specification = models.CharField(max_length=300, blank=True, verbose_name="Spécification")
    qte = models.IntegerField(default=0, verbose_name="Quantité")
    unite = models.ForeignKey(Unite, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Unité")
    prix_ht = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix HT")
    prix_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix TTC")
    montant_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Montant TTC")
    observation = models.TextField(blank=True, verbose_name="Observation")

    class Meta:
        verbose_name = "Détail du marché"
        verbose_name_plural = "Détails du marché"

    def __str__(self):
        return f"{self.designation} x{self.qte}"


class ExpressionBesoin(models.Model):
    STATUT_CHOICES = [
        ('nouveau', 'Nouveau'),
        ('recu', 'Reçu par comptable'),
        ('transforme', 'Transformé en BSD'),
    ]

    reference = models.CharField(max_length=100, blank=True, verbose_name="Référence")
    date_creation = models.DateField(verbose_name="Date de création")
    demandeur_service = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Service demandeur"
    )
    demandeur_bureau = models.ForeignKey(
        Bureau, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bureau demandeur"
    )
    recu_par_comptable = models.BooleanField(default=False, verbose_name="Reçu par le comptable")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='nouveau', verbose_name="Statut")
    date_reception_comptable = models.DateField(null=True, blank=True, verbose_name="Date de réception comptable")
    bon_sortie_definitive = models.ForeignKey(
        'BonSortieDefinitive', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bon de sortie définitive lié"
    )

    class Meta:
        verbose_name = "Expression de besoin"
        verbose_name_plural = "Expressions de besoins"
        ordering = ['-date_creation']

    def __str__(self):
        return self.reference or f"Expression #{self.pk}"

    def total_ttc(self):
        return sum(d.montant_ttc for d in self.details.all())

    def transform_to_bsd(self):
        """Transforme cette expression de besoin en Bon de Sortie Définitive Groupe 2
        (matières de consommation) une fois le matériel disponible. Idempotent."""
        if self.statut == 'transforme' and self.bon_sortie_definitive_id:
            return self.bon_sortie_definitive

        from datetime import date as _date
        last = BonSortieDefinitive.objects.filter(groupe='2').order_by('-num_bon').first()
        next_num = (last.num_bon + 1) if last else 1

        bsd = BonSortieDefinitive.objects.create(
            num_bon=next_num,
            date_creation=_date.today(),
            annee_exercice=_date.today().year,
            groupe='2',
            type_sortie="Expression de besoin",
            service=self.demandeur_service,
            bureau=self.demandeur_bureau,
            observation=f"Généré depuis l'expression de besoin {self.reference or ('#' + str(self.pk))}",
        )
        for d in self.details.all():
            DetailBonSortieDefinitive.objects.create(
                bon_sortie_d=bsd,
                produit=d.produit,
                designation=d.designation,
                nomenclature=d.nomenclature,
                specification=d.specification,
                qte=d.qte,
                unite=d.unite,
                prix_ht=d.prix_ht,
                prix_ttc=d.prix_ttc,
                montant_ttc=d.montant_ttc,
                observation=d.observation,
            )

        self.bon_sortie_definitive = bsd
        self.statut = 'transforme'
        self.save(update_fields=['bon_sortie_definitive', 'statut'])
        return bsd


class DetailExpressionBesoin(models.Model):
    expression = models.ForeignKey(ExpressionBesoin, on_delete=models.CASCADE, related_name='details')
    produit = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Produit")
    designation = models.CharField(max_length=300, verbose_name="Désignation")
    nomenclature = models.CharField(max_length=50, verbose_name="Nomenclature")
    specification = models.CharField(max_length=300, blank=True, verbose_name="Spécification")
    qte = models.IntegerField(default=0, verbose_name="Quantité")
    unite = models.ForeignKey(Unite, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Unité")
    prix_ht = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix HT")
    prix_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix TTC")
    montant_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Montant TTC")
    observation = models.TextField(blank=True, verbose_name="Observation")

    class Meta:
        verbose_name = "Détail expression de besoin"
        verbose_name_plural = "Détails expressions de besoins"

    def __str__(self):
        return f"{self.designation} x{self.qte}"


# ─────────────────────────── BONS D'AFFECTATION ───────────────────────────

class BonAffectation(models.Model):
    num_bon = models.IntegerField(verbose_name="N° Bon")
    date_affectation = models.DateField(null=True, blank=True, verbose_name="Date d'affectation")
    annee_creation = models.IntegerField(null=True, blank=True, verbose_name="Année")
    depot = models.ForeignKey(Depot, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dépôt source")
    depot_destination = models.ForeignKey(
        Depot, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='affectations_destination', verbose_name="Dépôt destination"
    )
    service = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Service"
    )
    bureau = models.ForeignKey(
        Bureau, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bureau"
    )
    valide = models.BooleanField(default=False, verbose_name="Validé")
    observation = models.TextField(blank=True, verbose_name="Observation")

    class Meta:
        verbose_name = "Bon d'affectation"
        verbose_name_plural = "Bons d'affectation"
        ordering = ['-date_affectation', '-num_bon']

    def __str__(self):
        return f"BA-{self.num_bon:04d}"

    def total_ttc(self):
        return sum(d.montant_ttc for d in self.details.all())


class DetailBonAffectation(models.Model):
    bon_affectation = models.ForeignKey(BonAffectation, on_delete=models.CASCADE, related_name='details')
    produit = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Produit")
    designation = models.CharField(max_length=300, verbose_name="Désignation")
    nomenclature = models.CharField(max_length=50, verbose_name="Nomenclature")
    specification = models.CharField(max_length=300, blank=True, verbose_name="Spécification")
    code_immatriculation = models.CharField(max_length=100, blank=True, verbose_name="Code d'immatriculation")
    qte = models.IntegerField(default=0, verbose_name="QTé BA")
    unite = models.ForeignKey(Unite, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Unité")
    prix_ht = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix Unitaire HT")
    prix_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix Unitaire TTC")
    montant_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Montant TTC")
    observation = models.CharField(max_length=300, blank=True, verbose_name="Observation")
    journal = models.ForeignKey(
        'Journal', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Entrée journal", related_name='details_ba'
    )

    class Meta:
        verbose_name = "Détail bon d'affectation"


# ─────────────────────────── BONS RETOUR AFFECTATION ───────────────────────────

class BonRetourAffectation(models.Model):
    num_bon = models.IntegerField(verbose_name="N° Bon")
    date_retour = models.DateField(null=True, blank=True, verbose_name="Date de retour")
    date_creation = models.DateField(null=True, blank=True, verbose_name="Date de création")
    depot = models.ForeignKey(Depot, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dépôt source")
    depot_destination = models.ForeignKey(
        Depot, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='retours_affectation_destination', verbose_name="Dépôt destination"
    )
    service = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Service"
    )
    bureau = models.ForeignKey(
        Bureau, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bureau"
    )
    valide = models.BooleanField(default=False, verbose_name="Validé")
    observation = models.TextField(blank=True, verbose_name="Observation")

    class Meta:
        verbose_name = "Bon de retour d'affectation"
        verbose_name_plural = "Bons de retour d'affectation"
        ordering = ['-date_creation', '-num_bon']

    def __str__(self):
        return f"BRA-{self.num_bon:04d}"

    def total_ttc(self):
        return sum(d.montant_ttc for d in self.details.all())


class DetailBonRetourAffectation(models.Model):
    bon_retour = models.ForeignKey(BonRetourAffectation, on_delete=models.CASCADE, related_name='details')
    produit = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Produit")
    designation = models.CharField(max_length=300, verbose_name="Désignation")
    nomenclature = models.CharField(max_length=30, verbose_name="Nomenclature")
    specification = models.CharField(max_length=300, blank=True, verbose_name="Spécification")
    qte = models.IntegerField(default=0, verbose_name="Quantité")
    unite = models.ForeignKey(Unite, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Unité")
    prix_ht = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix HT")
    prix_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix TTC")
    montant_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Montant TTC")
    observation = models.TextField(blank=True, verbose_name="Observation")

    class Meta:
        verbose_name = "Détail retour d'affectation"


# ─────────────────────────── BONS SORTIE PROVISOIRE ───────────────────────────

class BonSortieProvisoire(models.Model):
    num_bon = models.IntegerField(verbose_name="N° Bon")
    date_sortie = models.DateField(null=True, blank=True, verbose_name="Date de sortie")
    date_retour_prevue = models.DateField(null=True, blank=True, verbose_name="Date retour prévue")
    annee_creation = models.IntegerField(null=True, blank=True, verbose_name="Année")
    depot = models.ForeignKey(Depot, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dépôt")
    service = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Service"
    )
    bureau = models.ForeignKey(
        Bureau, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bureau"
    )
    chapitre = models.CharField(max_length=100, blank=True, verbose_name="Chapitre")
    valide = models.BooleanField(default=False, verbose_name="Validé")
    observation = models.TextField(blank=True, verbose_name="Observation")

    class Meta:
        verbose_name = "Bon de sortie provisoire"
        verbose_name_plural = "Bons de sortie provisoire"
        ordering = ['-annee_creation', '-num_bon']

    def __str__(self):
        return f"BSP-{self.num_bon:04d}"

    def total_ttc(self):
        return sum(d.montant_ttc for d in self.details.all())


class DetailBonSortieProvisoire(models.Model):
    bon_sortie_p = models.ForeignKey(BonSortieProvisoire, on_delete=models.CASCADE, related_name='details')
    produit = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Produit")
    designation = models.CharField(max_length=300, verbose_name="Désignation")
    nomenclature = models.CharField(max_length=30, verbose_name="Nomenclature")
    specification = models.CharField(max_length=300, blank=True, verbose_name="Spécification")
    qte = models.IntegerField(default=0, verbose_name="Quantité")
    unite = models.ForeignKey(Unite, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Unité")
    prix_ht = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix HT")
    prix_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix TTC")
    montant_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Montant TTC")
    observation = models.TextField(blank=True, verbose_name="Observation")

    class Meta:
        verbose_name = "Détail sortie provisoire"


# ─────────────────────────── BONS DE MUTATION ───────────────────────────
# Transfert direct d'une matière Groupe 1 déjà affectée du Bureau A vers le Bureau B,
# sans repasser par le dépôt central (contrairement à l'affectation / retour d'affectation).

class BonMutation(models.Model):
    num_bon = models.IntegerField(verbose_name="N° Bon")
    date_creation = models.DateField(null=True, blank=True, verbose_name="Date de création")
    annee_exercice = models.IntegerField(null=True, blank=True, verbose_name="Année")
    service_origine = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mutations_origine', verbose_name="Service origine"
    )
    bureau_origine = models.ForeignKey(
        Bureau, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mutations_origine', verbose_name="Bureau origine"
    )
    service_destination = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mutations_destination', verbose_name="Service destination"
    )
    bureau_destination = models.ForeignKey(
        Bureau, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mutations_destination', verbose_name="Bureau destination"
    )
    valide = models.BooleanField(default=False, verbose_name="Validé")
    observation = models.TextField(blank=True, verbose_name="Observation")

    class Meta:
        verbose_name = "Bordereau de mutation"
        verbose_name_plural = "Bordereaux de mutation"
        ordering = ['-date_creation', '-num_bon']

    def __str__(self):
        return f"BM-{self.num_bon:04d}"

    def total_ttc(self):
        return sum(d.montant_ttc for d in self.details.all())


class DetailBonMutation(models.Model):
    bon_mutation = models.ForeignKey(BonMutation, on_delete=models.CASCADE, related_name='details')
    produit = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Produit")
    designation = models.CharField(max_length=300, verbose_name="Désignation")
    nomenclature = models.CharField(max_length=30, verbose_name="Nomenclature")
    code_immatriculation = models.CharField(max_length=100, blank=True, verbose_name="Code d'immatriculation")
    qte = models.IntegerField(default=0, verbose_name="Quantité")
    unite = models.ForeignKey(Unite, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Unité")
    prix_ht = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix HT")
    prix_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix TTC")
    montant_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Montant TTC")
    observation = models.CharField(max_length=300, blank=True, verbose_name="Observation")

    class Meta:
        verbose_name = "Détail mutation"


# ─────────────────────────── BONS RETOUR SORTIE PROVISOIRE ───────────────────────────

class BonRetourSortieProvisoire(models.Model):
    num_bon = models.IntegerField(verbose_name="N° Bon")
    date_retour = models.DateField(null=True, blank=True, verbose_name="Date de retour")
    annee_creation = models.IntegerField(null=True, blank=True, verbose_name="Année")
    depot = models.ForeignKey(Depot, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dépôt")
    service = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Service"
    )
    bureau = models.ForeignKey(
        Bureau, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bureau"
    )
    valide = models.BooleanField(default=False, verbose_name="Validé")
    observation = models.TextField(blank=True, verbose_name="Observation")

    class Meta:
        verbose_name = "Bon de retour sortie provisoire"
        verbose_name_plural = "Bons de retour sortie provisoire"
        ordering = ['-annee_creation', '-num_bon']

    def __str__(self):
        return f"BRSP-{self.num_bon:04d}"

    def total_ttc(self):
        return sum(d.montant_ttc for d in self.details.all())


class DetailBonRetourSortieProvisoire(models.Model):
    bon_retour_sp = models.ForeignKey(BonRetourSortieProvisoire, on_delete=models.CASCADE, related_name='details')
    produit = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Produit")
    designation = models.CharField(max_length=300, verbose_name="Désignation")
    nomenclature = models.CharField(max_length=30, verbose_name="Nomenclature")
    specification = models.CharField(max_length=300, blank=True, verbose_name="Spécification")
    code_immatriculation = models.CharField(max_length=100, blank=True, verbose_name="Code d'immatriculation")
    qte = models.IntegerField(default=0, verbose_name="Quantité")
    unite = models.ForeignKey(Unite, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Unité")
    prix_ht = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix HT")
    prix_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix TTC")
    montant_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Montant TTC")
    observation = models.TextField(blank=True, verbose_name="Observation")

    class Meta:
        verbose_name = "Détail retour sortie provisoire"


# ─────────────────────────── BONS SORTIE DÉFINITIVE ───────────────────────────

class BonSortieDefinitive(models.Model):
    GROUPE_CHOICES = [('1', 'Groupe 1 (1x.xx.xx)'), ('2', 'Groupe 2 (2x.xx.xx)')]

    num_bon = models.IntegerField(verbose_name="N° Bon")
    date_creation = models.DateField(null=True, blank=True, verbose_name="Date de création")
    annee_exercice = models.IntegerField(null=True, blank=True, verbose_name="Année d'exercice")
    groupe = models.CharField(max_length=1, choices=GROUPE_CHOICES, default='1', verbose_name="Groupe de matières")
    type_sortie = models.CharField(max_length=100, blank=True, verbose_name="Type de sortie")
    service = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Service"
    )
    bureau = models.ForeignKey(
        Bureau, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bureau"
    )
    depot = models.ForeignKey(Depot, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dépôt")
    chapitre = models.CharField(max_length=100, blank=True, verbose_name="Chapitre")
    valide = models.BooleanField(default=False, verbose_name="Validé")
    observation = models.TextField(blank=True, verbose_name="Observation")
    bon_commande_service = models.ForeignKey(
        'BonCommandeService', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='bons_sortie', verbose_name="Bon de commande de service lié"
    )

    class Meta:
        verbose_name = "Bon de sortie définitive"
        verbose_name_plural = "Bons de sortie définitive"
        ordering = ['-date_creation', '-num_bon']

    def __str__(self):
        return f"BSD-{self.num_bon:04d} (G{self.groupe})"

    def total_ttc(self):
        return sum(d.montant_ttc for d in self.details.all())


class DetailBonSortieDefinitive(models.Model):
    bon_sortie_d = models.ForeignKey(BonSortieDefinitive, on_delete=models.CASCADE, related_name='details')
    produit = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Produit")
    designation = models.CharField(max_length=300, verbose_name="Désignation")
    nomenclature = models.CharField(max_length=30, verbose_name="Nomenclature")
    specification = models.CharField(max_length=300, blank=True, verbose_name="Spécification")
    qte = models.IntegerField(default=0, verbose_name="Quantité")
    unite = models.ForeignKey(Unite, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Unité")
    prix_ht = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix HT")
    prix_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix TTC")
    montant_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Montant TTC")
    observation = models.TextField(blank=True, verbose_name="Observation")
    detail_commande_service = models.ForeignKey(
        'DetailBonCommandeService', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='livraisons', verbose_name="Ligne de commande de service livrée"
    )

    class Meta:
        verbose_name = "Détail sortie définitive"


# ─────────────────────────── BONS DE COMMANDE DE SERVICES ───────────────────────────
# Demande de sortie de matières de consommation (Groupe 2) formulée par un service.
# Distinct du "bon de commande" d'approvisionnement (BonEntree.num_bon_commande) : ici
# il s'agit de la consommation interne, pas de l'achat auprès d'un fournisseur.

class BonCommandeService(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('envoye', 'Envoyé'),
        ('valide', 'Validé'),
        ('rejete', 'Rejeté'),
    ]

    num_bon = models.IntegerField(verbose_name="N° Bon")
    date_creation = models.DateField(verbose_name="Date")
    annee_exercice = models.IntegerField(null=True, blank=True, verbose_name="Année")
    service = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Service"
    )
    bureau = models.ForeignKey(
        Bureau, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bureau"
    )
    destinataire = models.CharField(max_length=200, blank=True, verbose_name="À M. (destinataire)")
    demande_par = models.CharField(max_length=200, blank=True, verbose_name="Chef de Service (demandeur)")
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon', verbose_name="Statut")
    date_envoi = models.DateField(null=True, blank=True, verbose_name="Date d'envoi")
    date_validation = models.DateField(null=True, blank=True, verbose_name="Date de validation")
    valide_par = models.CharField(max_length=200, blank=True, verbose_name="Le S.A.F. (validé par)")
    motif_rejet = models.TextField(blank=True, verbose_name="Motif de rejet")
    observation = models.TextField(blank=True, verbose_name="Observation")

    class Meta:
        verbose_name = "Bon de commande de service"
        verbose_name_plural = "Bons de commande de services"
        ordering = ['-date_creation', '-num_bon']

    def __str__(self):
        return f"BCS-{self.num_bon:04d}"

    @property
    def entierement_livre(self):
        details = list(self.details.all())
        return bool(details) and all(d.qte_restante <= 0 for d in details)


class DetailBonCommandeService(models.Model):
    bon_commande = models.ForeignKey(BonCommandeService, on_delete=models.CASCADE, related_name='details')
    produit = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Produit")
    designation = models.CharField(max_length=300, verbose_name="Désignation")
    nomenclature = models.CharField(max_length=30, blank=True, verbose_name="Nomenclature")
    specification = models.CharField(max_length=300, blank=True, verbose_name="Spécification")
    unite = models.ForeignKey(Unite, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Unité")
    qte_commandee = models.IntegerField(default=0, verbose_name="Quantité commandée")
    observation = models.CharField(max_length=300, blank=True, verbose_name="Observation")

    class Meta:
        verbose_name = "Détail bon de commande de service"
        verbose_name_plural = "Détails bons de commande de services"

    def __str__(self):
        return f"{self.designation} x{self.qte_commandee}"

    @property
    def qte_livree(self):
        return sum(l.qte for l in self.livraisons.all())

    @property
    def qte_restante(self):
        return self.qte_commandee - self.qte_livree


# ─────────────────────────── BONS SORTIE DÉFINITIVE G1 (RÉFORMES) ───────────────────────────

class BonSortieDefinitiveG1(models.Model):
    """Procès-Verbal de Réforme des Matières (Modèle N°5) : une commission de réforme
    statue, pour chaque matière durable Groupe 1 présentée, sur son devenir — la conserver
    ou la transformer (aucun mouvement de stock), la vendre ou la démolir (sortie définitive)."""
    num_bon = models.IntegerField(verbose_name="N° PV")
    date_creation = models.DateField(null=True, blank=True, verbose_name="Date du PV")
    annee_exercice = models.IntegerField(null=True, blank=True, verbose_name="Année d'exercice")
    section = models.CharField(max_length=100, blank=True, verbose_name="Section")
    chapitre = models.CharField(max_length=100, blank=True, verbose_name="Chapitre")
    service = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Service"
    )
    bureau = models.ForeignKey(
        Bureau, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bureau"
    )
    depot = models.ForeignKey(Depot, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dépôt")
    membres_commission = models.TextField(blank=True, verbose_name="Membres de la commission de réforme")
    observations_commission = models.TextField(blank=True, verbose_name="Autres observations de la commission")
    visa_controleur = models.CharField(max_length=300, blank=True, verbose_name="Visa du Contrôleur budgétaire ou du C.R.F.")
    autorite_approbation = models.CharField(max_length=300, blank=True, verbose_name="Approbation de l'Autorité compétente")
    valide = models.BooleanField(default=False, verbose_name="Validé")

    class Meta:
        verbose_name = "PV de réforme des matières (G1)"
        verbose_name_plural = "PV de réforme des matières (G1)"
        ordering = ['-date_creation', '-num_bon']

    def __str__(self):
        return f"PVR-{self.num_bon:04d}"

    def total_qte_reforme(self):
        return sum(d.qte for d in self.details.all() if d.decision in ('vendre', 'demolir'))

    def total_reforme(self):
        return sum(d.montant() for d in self.details.all() if d.decision in ('vendre', 'demolir'))


class DetailBonSortieDefinitiveG1(models.Model):
    DECISION_CHOICES = [
        ('conserver', 'À conserver ou à transformer'),
        ('vendre', 'À vendre'),
        ('demolir', 'À démolir'),
    ]

    bon_sortie_g1 = models.ForeignKey(BonSortieDefinitiveG1, on_delete=models.CASCADE, related_name='details')
    produit = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Produit")
    designation = models.CharField(max_length=300, verbose_name="Désignation")
    nomenclature = models.CharField(max_length=30, verbose_name="Nomenclature")
    specification = models.CharField(max_length=300, blank=True, verbose_name="Spécification")
    unite = models.ForeignKey(Unite, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Unité")

    qte = models.IntegerField(default=0, verbose_name="Quantité")
    prix_unitaire = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="P.U. réforme")
    decision = models.CharField(max_length=10, choices=DECISION_CHOICES, default='conserver', verbose_name="Décision de la commission")

    observation = models.TextField(blank=True, verbose_name="Observation")

    class Meta:
        verbose_name = "Détail PV de réforme (G1)"

    def montant(self):
        return self.qte * self.prix_unitaire


# ─────────────────────────── REPORTING ───────────────────────────

class BalancePeriodique(models.Model):
    annee_exercice = models.ForeignKey(
        AnneeExercice, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Année d'exercice"
    )
    produit = models.ForeignKey(
        Produit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Produit"
    )
    nomenclature = models.CharField(max_length=30, verbose_name="Nomenclature")
    designation = models.CharField(max_length=300, verbose_name="Désignation")
    unite = models.CharField(max_length=50, verbose_name="Unité")
    existant_dp = models.IntegerField(default=0, verbose_name="Existant début période")
    entree_periode = models.IntegerField(default=0, verbose_name="Entrée période")
    total_entree = models.IntegerField(default=0, verbose_name="Total entrée")
    sortie_periode = models.IntegerField(default=0, verbose_name="Sortie période")
    existant_fin_periode = models.IntegerField(default=0, verbose_name="Existant fin période")
    prix_unitaire_ht = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix unitaire HT")
    montant_existant = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Montant existant")

    class Meta:
        verbose_name = "Balance périodique"
        verbose_name_plural = "Balances périodiques"

    def __str__(self):
        return f"{self.nomenclature} - {self.designation}"


class Journal(models.Model):
    # ── Identification ──
    date_creation        = models.DateField(null=True, blank=True, verbose_name="Date création")
    num_bon              = models.IntegerField(default=0, verbose_name="N° Bon")
    type_entree          = models.CharField(max_length=100, verbose_name="Type opération")
    groupe               = models.CharField(max_length=10, blank=True, verbose_name="Groupe")

    # ── Article ──
    designation          = models.CharField(max_length=300, verbose_name="Désignation")
    nomenclature         = models.CharField(max_length=50, verbose_name="Nomenclature")
    specification        = models.CharField(max_length=300, blank=True, verbose_name="Spécification")
    unite                = models.CharField(max_length=50, blank=True, verbose_name="Unité")

    # ── Prix ──
    prix_ht              = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix HT")
    prix_ttc             = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix TTC")
    montant_ttc          = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Montant TTC")

    # ── Mouvements quantitatifs ──
    qte                  = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Quantité")
    existant             = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Existant")
    entree_periode       = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Entrée période")
    total_entree         = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total entrée")
    sortie_periode       = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Sortie période")
    existant_fin_periode = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Existant fin période")
    montant_existant     = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Montant existant")
    qte_stock_partielle  = models.CharField(max_length=50, blank=True, verbose_name="Stock dépôt")

    # ── Affectation (BA) ──
    date_affectation     = models.DateField(null=True, blank=True, verbose_name="Date affectation")
    qte_affectation      = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Qté affectation")
    date_retour_affectation = models.DateField(null=True, blank=True, verbose_name="Date retour BA")
    qte_rba              = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Qté retour BA")

    # ── Sortie Provisoire (BSP/BRSP) ──
    qte_sp               = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Qté sortie prov.")
    date_retour          = models.DateField(null=True, blank=True, verbose_name="Date retour réelle")

    # ── Sortie Définitive (BSD) ──
    qte_sd               = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Qté sortie déf.")
    num_bon_sortie       = models.IntegerField(default=0, verbose_name="N° Bon sortie déf.")

    # ── Tiers / Contexte ──
    beneficiaire         = models.CharField(max_length=200, blank=True, verbose_name="Bénéficiaire")
    service              = models.CharField(max_length=200, blank=True, verbose_name="Service")
    bureau               = models.CharField(max_length=200, blank=True, verbose_name="Bureau")
    depot                = models.CharField(max_length=50, blank=True, verbose_name="Dépôt")
    annee_exercice       = models.IntegerField(null=True, blank=True, verbose_name="Année")
    observation          = models.TextField(blank=True, verbose_name="Observation")

    class Meta:
        verbose_name = "Journal"
        verbose_name_plural = "Journal des opérations"
        ordering = ['-date_creation', '-num_bon']

    def __str__(self):
        return f"{self.type_entree} | {self.designation} ({self.date_creation})"



