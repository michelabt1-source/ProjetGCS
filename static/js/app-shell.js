/* ══════════════════════════════════════════════════════════════════
   Gestima — comportements de la coque (voir static/css/app-shell.css)
   · repli de la barre latérale (mémorisé), tiroir mobile
   · ouverture / fermeture des groupes de navigation (mémorisée)
   · palette de commandes : Ctrl+K, « / », flèches, Entrée, Échap
   · notifications : fermeture manuelle, disparition auto des succès
   · bouton « Fermer » : affiché si la page n'a pas sa propre sortie
   · HTMX : jeton CSRF sur les requêtes non-GET
══════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var root = document.documentElement;
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) { /* stockage indisponible */ } }
  };
  var desktop = window.matchMedia('(min-width: 1024px)');

  /* ── Barre latérale : repli (bureau) / tiroir (mobile) ── */
  function setDrawer(open) {
    root.classList.toggle('sb-open', open);
    document.querySelectorAll('[data-action="toggle-drawer"]').forEach(function (b) {
      b.setAttribute('aria-expanded', String(open));
    });
  }

  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-action]');
    if (!btn) return;
    switch (btn.dataset.action) {
      case 'toggle-sidebar':
        var collapsed = !root.classList.contains('sb-collapsed');
        root.classList.toggle('sb-collapsed', collapsed);
        store.set('gestima.sb-collapsed', collapsed ? '1' : '0');
        btn.setAttribute('aria-pressed', String(collapsed));
        break;
      case 'toggle-drawer':
        setDrawer(!root.classList.contains('sb-open'));
        break;
      case 'close-drawer':
        setDrawer(false);
        break;
      case 'open-palette':
        openPalette();
        break;
      case 'dismiss-toast':
        dismissToast(btn.closest('.toast'));
        break;
    }
  });
  desktop.addEventListener('change', function () { setDrawer(false); });

  /* ── Groupes de navigation ── */
  var openGroups = {};
  try { openGroups = JSON.parse(store.get('gestima.nav-groups') || '{}'); } catch (e) { openGroups = {}; }

  document.querySelectorAll('.nav-group').forEach(function (group) {
    var key = group.dataset.key;
    var hasActive = !!group.querySelector('.nav-link.is-active');
    var open = hasActive || openGroups[key] === true;
    var toggle = group.querySelector('.nav-group-toggle');
    group.dataset.open = String(open);
    toggle.setAttribute('aria-expanded', String(open));
    toggle.addEventListener('click', function () {
      var next = group.dataset.open !== 'true';
      group.dataset.open = String(next);
      toggle.setAttribute('aria-expanded', String(next));
      openGroups[key] = next;
      store.set('gestima.nav-groups', JSON.stringify(openGroups));
    });
  });

  var activeLink = document.querySelector('.sb-nav .nav-link.is-active');
  if (activeLink) activeLink.scrollIntoView({ block: 'nearest' });

  /* ── Palette de commandes ── */
  var palette = document.getElementById('cmdk');
  var input = document.getElementById('cmdk-input');
  var list = document.getElementById('cmdk-list');
  var entries = [];
  try { entries = JSON.parse(document.getElementById('nav-palette-data').textContent); } catch (e) { entries = []; }
  var results = [];
  var selected = 0;
  var lastFocus = null;

  function normalize(s) {
    return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
  }
  entries.forEach(function (en) { en._n = normalize(en.label + ' ' + en.section + ' ' + (en.hint || '')); en._l = normalize(en.label); });

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; });
  }
  function highlight(label, q) {
    if (!q) return escapeHtml(label);
    var i = normalize(label).indexOf(q);
    if (i < 0) return escapeHtml(label);
    return escapeHtml(label.slice(0, i)) + '<mark>' + escapeHtml(label.slice(i, i + q.length)) + '</mark>' + escapeHtml(label.slice(i + q.length));
  }

  function render() {
    var q = normalize(input.value.trim());
    var terms = q.split(/\s+/).filter(Boolean);
    results = entries.filter(function (en) {
      return terms.every(function (t) { return en._n.indexOf(t) >= 0; });
    });
    if (q) {
      results.sort(function (a, b) {
        var sa = a._l.indexOf(q) === 0 ? 0 : a._l.indexOf(q) > 0 ? 1 : 2;
        var sb = b._l.indexOf(q) === 0 ? 0 : b._l.indexOf(q) > 0 ? 1 : 2;
        return sa - sb;
      });
    }
    selected = Math.min(selected, Math.max(results.length - 1, 0));

    if (!results.length) {
      list.innerHTML = '<li class="cmdk-empty">Aucune page ne correspond à « ' + escapeHtml(input.value) + ' »</li>';
      input.removeAttribute('aria-activedescendant');
      return;
    }
    var html = '', section = null;
    results.forEach(function (en, i) {
      if (!q && en.section !== section) {
        section = en.section;
        html += '<li class="cmdk-section" role="presentation">' + escapeHtml(section) + '</li>';
      }
      html += '<li role="option" id="cmdk-opt-' + i + '" class="cmdk-item" data-index="' + i + '" aria-selected="' + (i === selected) + '">' +
        '<span>' + highlight(en.label, terms[0] || '') + '</span>' +
        (q ? '<span class="cmdk-meta">' + escapeHtml(en.section) + '</span>' : '') + '</li>';
    });
    list.innerHTML = html;
    input.setAttribute('aria-activedescendant', 'cmdk-opt-' + selected);
    var sel = list.querySelector('[aria-selected="true"]');
    if (sel) sel.scrollIntoView({ block: 'nearest' });
  }

  function move(delta) {
    if (!results.length) return;
    selected = (selected + delta + results.length) % results.length;
    render();
  }
  function go(index) {
    var en = results[index];
    if (en) window.location.href = en.href;
  }

  function openPalette() {
    if (!palette || !palette.hidden) return;
    lastFocus = document.activeElement;
    palette.hidden = false;
    input.value = '';
    selected = 0;
    render();
    input.focus();
  }
  function closePalette() {
    if (!palette || palette.hidden) return;
    palette.hidden = true;
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  if (palette) {
    input.addEventListener('input', function () { selected = 0; render(); });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
      else if (e.key === 'Enter') { e.preventDefault(); go(selected); }
      else if (e.key === 'Tab') { e.preventDefault(); move(e.shiftKey ? -1 : 1); }
    });
    list.addEventListener('mousemove', function (e) {
      var item = e.target.closest('.cmdk-item');
      if (item && +item.dataset.index !== selected) { selected = +item.dataset.index; render(); }
    });
    list.addEventListener('click', function (e) {
      var item = e.target.closest('.cmdk-item');
      if (item) go(+item.dataset.index);
    });
    palette.addEventListener('mousedown', function (e) { if (e.target === palette) closePalette(); });
  }

  document.addEventListener('keydown', function (e) {
    var typing = /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) || e.target.isContentEditable;
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      palette && palette.hidden ? openPalette() : closePalette();
    } else if (e.key === '/' && !typing) {
      e.preventDefault();
      openPalette();
    } else if (e.key === 'Escape') {
      closePalette();
      setDrawer(false);
    }
  });

  /* ── Notifications ── */
  function dismissToast(toast) {
    if (!toast || toast.classList.contains('is-leaving')) return;
    toast.classList.add('is-leaving');
    setTimeout(function () { toast.remove(); }, 200);
  }
  document.querySelectorAll('.toast[data-autohide]').forEach(function (toast) {
    var timer = setTimeout(function () { dismissToast(toast); }, 6000);
    toast.addEventListener('mouseenter', function () { clearTimeout(timer); });
  });

  /* ── Bouton « Fermer » : seulement si la page n'a pas déjà sa propre sortie ── */
  var fermer = document.getElementById('page-fermer');
  var contenu = document.querySelector('.main-inner');
  if (fermer && contenu) {
    var sortieExistante = Array.prototype.some.call(contenu.querySelectorAll('a[href]'), function (a) {
      return /^(←\s*)?(retour|fermer|annuler)\b/i.test(a.textContent.replace(/\s+/g, ' ').trim());
    });
    fermer.hidden = sortieExistante;
  }

  /* ── HTMX : jeton CSRF sur les requêtes non-GET ── */
  document.body.addEventListener('htmx:configRequest', function (evt) {
    if (evt.detail.verb === 'get') return;
    var token = (document.cookie.split(';').map(function (c) { return c.trim(); })
      .find(function (c) { return c.indexOf('csrftoken=') === 0; }) || '').split('=')[1] || '';
    if (token) evt.detail.headers['X-CSRFToken'] = token;
  });
})();
