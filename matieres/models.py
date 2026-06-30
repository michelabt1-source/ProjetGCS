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


class Beneficiaire(models.Model):
    nom = models.CharField(max_length=100, verbose_name="Bénéficiaire")
    responsable = models.CharField(max_length=100, blank=True, verbose_name="Responsable")

    class Meta:
        verbose_name = "Bénéficiaire"
        verbose_name_plural = "Bénéficiaires"
        ordering = ['nom']

    def __str__(self):
        return self.nom


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
    num_sous_compte = models.FloatField(verbose_name="N° Sous-compte")
    famille_sc = models.CharField(max_length=200, verbose_name="Famille sous-compte")

    class Meta:
        verbose_name = "Sous-compte"
        verbose_name_plural = "Sous-comptes"
        ordering = ['num_sous_compte']

    def __str__(self):
        return f"{self.num_sous_compte} - {self.famille_sc}"


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
    beneficiaire = models.ForeignKey(
        Beneficiaire, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bénéficiaire"
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

    def total_ttc(self):
        return sum(d.montant_ttc for d in self.details.all())


class DetailBonAffectation(models.Model):
    bon_affectation = models.ForeignKey(BonAffectation, on_delete=models.CASCADE, related_name='details')
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
    beneficiaire = models.ForeignKey(
        Beneficiaire, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bénéficiaire"
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
    beneficiaire = models.ForeignKey(
        Beneficiaire, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bénéficiaire"
    )
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


# ─────────────────────────── BONS RETOUR SORTIE PROVISOIRE ───────────────────────────

class BonRetourSortieProvisoire(models.Model):
    num_bon = models.IntegerField(verbose_name="N° Bon")
    date_retour = models.DateField(null=True, blank=True, verbose_name="Date de retour")
    annee_creation = models.IntegerField(null=True, blank=True, verbose_name="Année")
    depot = models.ForeignKey(Depot, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dépôt")
    beneficiaire = models.ForeignKey(
        Beneficiaire, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bénéficiaire"
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
    beneficiaire = models.ForeignKey(
        Beneficiaire, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bénéficiaire"
    )
    depot = models.ForeignKey(Depot, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dépôt")
    valide = models.BooleanField(default=False, verbose_name="Validé")
    observation = models.TextField(blank=True, verbose_name="Observation")

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

    class Meta:
        verbose_name = "Détail sortie définitive"


# ─────────────────────────── BONS SORTIE DÉFINITIVE G1 (RÉFORMES) ───────────────────────────

class BonSortieDefinitiveG1(models.Model):
    num_bon = models.IntegerField(verbose_name="N° Bon")
    date_creation = models.DateField(null=True, blank=True, verbose_name="Date de création")
    annee_exercice = models.IntegerField(null=True, blank=True, verbose_name="Année d'exercice")
    type_sortie = models.CharField(max_length=100, blank=True, verbose_name="Type de sortie")
    beneficiaire = models.ForeignKey(
        Beneficiaire, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bénéficiaire"
    )
    depot = models.ForeignKey(Depot, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dépôt")
    valide = models.BooleanField(default=False, verbose_name="Validé")

    class Meta:
        verbose_name = "Bon de sortie définitive G1"
        verbose_name_plural = "Bons de sortie définitive G1 (Réformes)"
        ordering = ['-date_creation', '-num_bon']

    def __str__(self):
        return f"BSD-G1-{self.num_bon:04d}"


class DetailBonSortieDefinitiveG1(models.Model):
    bon_sortie_g1 = models.ForeignKey(BonSortieDefinitiveG1, on_delete=models.CASCADE, related_name='details')
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
        verbose_name = "Détail sortie définitive G1"


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
    date_creation = models.DateField(null=True, blank=True, verbose_name="Date")
    num_bon = models.IntegerField(default=0, verbose_name="N° Bon")
    type_entree = models.CharField(max_length=100, verbose_name="Type opération")
    designation = models.CharField(max_length=300, verbose_name="Désignation")
    nomenclature = models.CharField(max_length=30, verbose_name="Nomenclature")
    specification = models.CharField(max_length=300, blank=True, verbose_name="Spécification")
    qte = models.IntegerField(default=0, verbose_name="Quantité")
    unite = models.CharField(max_length=50, blank=True, verbose_name="Unité")
    prix_ht = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix HT")
    prix_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Prix TTC")
    montant_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Montant TTC")
    beneficiaire = models.CharField(max_length=200, blank=True, verbose_name="Bénéficiaire")
    annee_exercice = models.IntegerField(null=True, blank=True, verbose_name="Année")
    depot = models.CharField(max_length=50, blank=True, verbose_name="Dépôt")
    observation = models.TextField(blank=True, verbose_name="Observation")
    existant = models.IntegerField(default=0, verbose_name="Existant")
    entree_periode = models.IntegerField(default=0, verbose_name="Entrée")
    sortie_periode = models.IntegerField(default=0, verbose_name="Sortie")
    existant_fin_periode = models.IntegerField(default=0, verbose_name="Existant fin période")
    montant_existant = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Montant existant")

    class Meta:
        verbose_name = "Journal"
        verbose_name_plural = "Journal des opérations"
        ordering = ['-date_creation', '-num_bon']

    def __str__(self):
        return f"{self.type_entree} | {self.designation} ({self.date_creation})"
