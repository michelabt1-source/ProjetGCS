/* ══════════════════════════════════════════════════════════════════
   Pages de bons — volet de saisie des articles (voir bon-saisie.css)

   Balisage attendu :
     <section class="bs-drawer" data-bs-drawer
              data-rows="#id-du-conteneur-des-lignes"
              data-add-btn="#id-du-bouton-saisir"
              data-focus="#id-du-champ-designation"> … </section>
     <div class="bs-backdrop" data-bs-backdrop></div>
     Boutons d'ouverture : [data-bs-open]   ·   fermeture : [data-bs-close]
     Résumé du tableau   : [data-bs-summary] contenant [data-bs-count],
                           [data-bs-count-label] et [data-bs-total]
     Total dans le tableau rechargé par HTMX : [data-bs-total-source]

   Clavier : Échap ferme le volet (après le catalogue s'il est ouvert),
             Ctrl+Entrée n'ajoute une ligne que si le volet est ouvert,
             F2 ouvre le volet (la page ouvre ensuite son catalogue).
══════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  const drawer   = () => document.querySelector('[data-bs-drawer]');
  const backdrop = () => document.querySelector('[data-bs-backdrop]');
  const estOuvert = () => !!(drawer() && drawer().classList.contains('open'));
  let dernierDeclencheur = null;

  function ouvrir(declencheur) {
    const d = drawer();
    if (!d) return;
    dernierDeclencheur = declencheur || document.querySelector('[data-bs-open]');
    d.classList.add('open');
    d.setAttribute('aria-hidden', 'false');
    if (backdrop()) backdrop().classList.add('open');
    const champ = d.dataset.focus && document.querySelector(d.dataset.focus);
    if (champ) setTimeout(() => champ.focus(), 260);
  }

  function fermer() {
    const d = drawer();
    if (!d) return;
    d.classList.remove('open');
    d.setAttribute('aria-hidden', 'true');
    if (backdrop()) backdrop().classList.remove('open');
    if (dernierDeclencheur && document.body.contains(dernierDeclencheur)) dernierDeclencheur.focus();
  }

  /* Un catalogue produit (…-modal-overlay) est-il affiché ? */
  function catalogueOuvert() {
    return Array.prototype.some.call(
      document.querySelectorAll('[id$="modal-overlay"]'),
      el => getComputedStyle(el).display !== 'none'
    );
  }

  function conteneurLignes() {
    const d = drawer();
    const sel = (d && d.dataset.rows) || document.querySelector('[data-bs-rows]')?.dataset.bsRows;
    return sel ? document.querySelector(sel) : null;
  }

  /* Lignes d'articles réelles (la ligne « Aucun article » n'a qu'une cellule) */
  function nbLignes() {
    const c = conteneurLignes();
    if (!c) return 0;
    return Array.prototype.filter.call(c.querySelectorAll('tbody tr'), tr => tr.cells.length > 1).length;
  }

  function majResume() {
    const resume = document.querySelector('[data-bs-summary]');
    if (!resume) return;
    const n = nbLignes();
    resume.hidden = n === 0;
    const count = resume.querySelector('[data-bs-count]');
    const label = resume.querySelector('[data-bs-count-label]');
    const total = resume.querySelector('[data-bs-total]');
    if (count) count.textContent = n;
    if (label) label.textContent = n > 1 ? 'articles' : 'article';
    const source = conteneurLignes()?.querySelector('[data-bs-total-source]');
    if (total && source) total.textContent = source.textContent.replace(/\s+/g, ' ').trim();
  }

  let flashTimer = null;
  function flash(texte, type) {
    const el = drawer()?.querySelector('.bs-flash');
    if (!el) return;
    el.textContent = texte;
    el.className = 'bs-flash show ' + type;
    clearTimeout(flashTimer);
    flashTimer = setTimeout(() => el.classList.remove('show'), 3500);
  }

  /* ── Ouverture / fermeture à la souris ── */
  document.addEventListener('click', function (e) {
    const btnOuvrir = e.target.closest('[data-bs-open]');
    if (btnOuvrir) { e.preventDefault(); ouvrir(btnOuvrir); return; }
    if (e.target.closest('[data-bs-close]') || e.target.closest('[data-bs-backdrop]')) fermer();
  });

  /* ── Clavier (phase de capture : remplace les raccourcis propres à chaque page) ── */
  window.addEventListener('keydown', function (e) {
    const d = drawer();
    if (!d) return;
    if (e.key === 'Escape') {
      if (catalogueOuvert()) return;            // la page ferme d'abord son catalogue
      if (estOuvert()) { e.stopImmediatePropagation(); fermer(); }
      return;
    }
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      e.stopImmediatePropagation();
      const btn = estOuvert() && d.dataset.addBtn && document.querySelector(d.dataset.addBtn);
      if (btn && !btn.disabled) btn.click();    // pas d'ajout avec le volet fermé
      return;
    }
    if (e.key === 'F2') {
      e.preventDefault();
      e.stopImmediatePropagation();
      if (!estOuvert()) ouvrir();
      const catalogue = d.querySelector('[data-bs-catalogue]');
      if (catalogue) catalogue.click();
    }
  }, true);

  /* ── Suivi des ajouts faits par HTMX ── */
  let lignesAvantAjout = null;
  document.addEventListener('htmx:beforeRequest', function (e) {
    const d = drawer();
    if (d && d.dataset.addBtn && e.detail.elt && e.detail.elt.matches(d.dataset.addBtn)) {
      lignesAvantAjout = nbLignes();
    }
  });
  document.addEventListener('htmx:afterSwap', function (e) {
    const c = conteneurLignes();
    if (!c || e.detail.target !== c) return;
    majResume();
    if (lignesAvantAjout === null) return;
    if (nbLignes() > lignesAvantAjout) {
      flash('✓ Article ajouté au bon. Vous pouvez saisir le suivant.', 'ok');
    } else {
      flash("Article non ajouté : choisissez d'abord un article dans la liste ou le catalogue, puis la quantité.", 'warn');
    }
    lignesAvantAjout = null;
  });

  window.BonSaisie = { ouvrir: ouvrir, fermer: fermer, majResume: majResume };
})();
