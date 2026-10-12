/* ══════════════════════════════════════════════════════════════════
   Volet de saisie d'un article (page « bon ») : calcul HT ⇄ TTC (TVA 18 %),
   autocomplete et catalogue produit, transfert vers les champs cachés HTMX.
   Identifiants attendus : f-designation, f-nomenclature, f-specification, f-qte,
   f-unite-sel, f-unite-id, f-produit-id, f-prix-ht, f-prix-ttc, f-montant-ttc,
   f-observation, produit-dropdown, produit-wrap, h-* (champs cachés),
   produit-modal-overlay, modal-search-input.
   Utilisé par : bons/entree_update.html, marches/update.html
══════════════════════════════════════════════════════════════════ */
// ── Calcul montant TTC (qte × prix_ttc) ──
function calcMontant() {
  const qte     = parseFloat(document.getElementById('f-qte').value)      || 0;
  const ttc     = parseFloat(document.getElementById('f-prix-ttc').value)  || 0;
  const montant = qte * ttc;
  document.getElementById('f-montant-ttc').value =
    new Intl.NumberFormat('de-DE', {minimumFractionDigits:2, maximumFractionDigits:2}).format(montant) + ' FCFA';
}

// ── Saisie du HT → calcule le TTC = HT × 1,18 (TVA 18%) ──
function calcTTCFromHT() {
  const ht  = parseFloat(document.getElementById('f-prix-ht').value) || 0;
  const ttc = Math.round(ht * 118) / 100;          // ×1.18 arrondi à 2 décimales
  document.getElementById('f-prix-ttc').value = ttc.toFixed(2);
  calcMontant();
}

// ── Saisie du TTC → calcule le HT = TTC / 1,18 (certains bons arrivent déjà en TTC) ──
function calcHTFromTTC() {
  const ttc = parseFloat(document.getElementById('f-prix-ttc').value) || 0;
  const ht  = Math.round((ttc / 1.18) * 100) / 100;
  document.getElementById('f-prix-ht').value = ht.toFixed(2);
  calcMontant();
}

// ── Effacer le formulaire article ──
function clearArticleForm() {
  ['f-designation','f-nomenclature','f-specification','f-observation'].forEach(id => {
    document.getElementById(id).value = '';
  });
  document.getElementById('f-qte').value      = '0';
  document.getElementById('f-prix-ht').value  = '0';
  document.getElementById('f-prix-ttc').value = '0';
  document.getElementById('f-montant-ttc').value = '0,00 FCFA';
  document.getElementById('f-produit-id').value  = '';
  document.getElementById('f-unite-id').value    = '';
  document.getElementById('f-unite-sel').value   = '';
  document.getElementById('produit-dropdown').classList.remove('open');
  document.getElementById('produit-dropdown').innerHTML = '';
  document.getElementById('f-designation').focus();
}

// ── Préparer les champs cachés avant submit HTMX ──
function prepareSubmit() {
  document.getElementById('h-produit-id').value   = document.getElementById('f-produit-id').value;
  document.getElementById('h-designation').value  = document.getElementById('f-designation').value;
  document.getElementById('h-nomenclature').value = document.getElementById('f-nomenclature').value;
  document.getElementById('h-specification').value= document.getElementById('f-specification').value;
  document.getElementById('h-qte').value          = document.getElementById('f-qte').value;
  document.getElementById('h-unite-id').value     = document.getElementById('f-unite-sel').value
                                                  || document.getElementById('f-unite-id').value;
  document.getElementById('h-prix-ht').value      = document.getElementById('f-prix-ht').value;
  document.getElementById('h-prix-ttc').value     = document.getElementById('f-prix-ttc').value;
  document.getElementById('h-observation').value  = document.getElementById('f-observation').value;
}

// ── Sélectionner une ligne du tableau ──
let selectedDetailId = null;
function selectLine(pk, tr) {
  document.querySelectorAll('.lines-table tbody tr').forEach(r => r.classList.remove('selected-line'));
  tr.classList.add('selected-line');
  selectedDetailId = pk;
}

// ── Fermer l'autocomplete en cliquant ailleurs ──
document.addEventListener('click', function(e) {
  const wrap = document.getElementById('produit-wrap');
  if (wrap && !wrap.contains(e.target)) {
    const dd = document.getElementById('produit-dropdown');
    if (dd) dd.classList.remove('open');
  }
});

// ── Autocomplete : afficher quand HTMX retourne du contenu ──
document.body.addEventListener('htmx:afterSwap', function(e) {
  if (e.target && e.target.id === 'produit-dropdown') {
    e.target.classList.toggle('open', !!e.target.innerHTML.trim());
  }
});

// ── Modal : ouvrir ──
function openProduitModal() {
  document.getElementById('produit-modal-overlay').classList.add('open');
  document.getElementById('modal-search-input').value = '';
  document.getElementById('modal-search-input').focus();
}

// ── Modal : fermer ──
function closeProduitModal() {
  document.getElementById('produit-modal-overlay').classList.remove('open');
}
function closeModalOnBg(e) {
  if (e.target === document.getElementById('produit-modal-overlay')) closeProduitModal();
}

// ── Sélectionner un produit depuis le modal ──
function pickProduit(id, designation, nomenclature, specification, uniteId, uniteLibelle, stockDispo) {
  document.getElementById('f-produit-id').value = id;
  document.getElementById('f-designation').value = designation;
  document.getElementById('f-nomenclature').value = nomenclature;
  document.getElementById('f-specification').value = specification;
  document.getElementById('f-unite-id').value = uniteId;

  const sel = document.getElementById('f-unite-sel');
  for (const opt of sel.options) {
    if (opt.value == uniteId) { sel.value = uniteId; break; }
  }

  document.getElementById('produit-dropdown').classList.remove('open');
  document.getElementById('produit-dropdown').innerHTML = '';
  closeProduitModal();
  document.getElementById('f-qte').focus();
  document.getElementById('f-qte').select();
}

// Alias pour compatibilité avec le partial autocomplete
function selectProduit(id, designation, nomenclature, specification, uniteId, uniteLibelle, stockDispo) {
  pickProduit(id, designation, nomenclature, specification, uniteId, uniteLibelle, stockDispo);
}

// Touche Échap ferme le modal
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeProduitModal();
});

// Quantité modifiée dans le tableau (.qte-cell) : Entrée valide comme une sortie du champ
document.addEventListener('keydown', function (e) {
  if (e.key === 'Enter' && e.target.classList && e.target.classList.contains('qte-cell')) {
    e.preventDefault();
    e.target.blur();
  }
});
