'use strict';
// One script for every page. No analytics, no cookies, no remote script: nothing here reports anything to anybody.
(function () {
  // ---- the server address ships IN the markup; config.json can move it without a rebuild (see README) ----
  var SHIPPED = 'https://mcp.kleooai.com/mcp';
  var note = document.getElementById('server-note');
  try {
    fetch('/config.json', { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (cfg) {
      if (!cfg) return;
      var url = typeof cfg.mcp_url === 'string' && /^https:\/\/\S+$/.test(cfg.mcp_url) ? cfg.mcp_url : SHIPPED;
      if (url !== SHIPPED) {
        document.querySelectorAll('code, [data-copy]').forEach(function (el) {
          if (el.dataset && el.dataset.copy && el.dataset.copy.indexOf(SHIPPED) >= 0) el.dataset.copy = el.dataset.copy.split(SHIPPED).join(url);
          if (el.tagName === 'CODE' && el.textContent.indexOf(SHIPPED) >= 0 && el.children.length === 0) el.textContent = el.textContent.split(SHIPPED).join(url);
        });
      }
      if (note && typeof cfg.note === 'string' && cfg.note.trim()) note.textContent = cfg.note.trim();
    }).catch(function () {});
  } catch (_) {}

  // ---- copy buttons: the address, a prompt, a config snippet ----
  var status = document.getElementById('copy-status');
  var statusTimer;
  function say(text) {
    if (!status) return;
    status.textContent = text;
    clearTimeout(statusTimer);
    statusTimer = setTimeout(function () { status.textContent = ''; }, 5000);
  }
  document.querySelectorAll('[data-copy]').forEach(function (button) {
    button.addEventListener('click', function () {
      var text = button.dataset.copy;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () { say('Copied. Paste it into your assistant.'); },
          function () { say('Select the text and copy it manually.'); });
      } else say('Select the text and copy it manually.');
    });
  });

  // ---- the credit calculator on /pricing/: same rule as the server, max(10, ceil(seconds / 2)) ----
  var duration = document.getElementById('duration');
  if (duration) {
    var output = document.getElementById('credit-result');
    var update = function () {
      var seconds = Number(duration.value);
      output.textContent = !Number.isInteger(seconds) || seconds < 15 || seconds > 300
        ? 'Enter a whole number from 15 to 300 seconds.'
        : seconds + ' seconds = ' + Math.max(10, Math.ceil(seconds / 2)) + ' credits';
    };
    duration.addEventListener('input', update);
    update();
  }

  // ---- sample films: shown, not handed over. A film plays by itself while it is in front of you, muted, and is
  //      only fetched then; no controls, no menu, no drag. ----
  var watches = Array.prototype.slice.call(document.querySelectorAll('.watch'));
  watches.forEach(function (w) {
    w.addEventListener('contextmenu', function (e) { e.preventDefault(); });
    w.addEventListener('dragstart', function (e) { e.preventDefault(); });
  });
  watches.forEach(function (w) {
    var v = w.querySelector('video');
    if (!v) return;
    v.addEventListener('play', function () { w.classList.add('playing'); });
    v.addEventListener('pause', function () { w.classList.remove('playing'); });
  });
  // The film is the content of these pages, not decoration, so it also plays under prefers-reduced-motion — muted,
  // only while it is in front of you, and it stops the moment you scroll on (the stylesheet still stops every
  // transition and animation for that preference).
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var v = en.target.querySelector('video');
        if (!v) return;
        if (en.intersectionRatio >= 0.6) { var p = v.play(); if (p && p.catch) p.catch(function () {}); }
        else v.pause();
      });
    }, { threshold: [0, 0.6] });
    watches.forEach(function (w) { if (w.querySelector('video')) io.observe(w); });
  }

  // ---- section URLs shared from the first landing page (Italian ids) still land on their section ----
  var moved = { '#come': '#how', '#connetti': '#connect', '#prezzi': '#pricing', '#quinte': '#engine' };
  if (location.pathname === '/' || location.pathname === '/index.html') {
    var target = moved[location.hash];
    if (target) {
      history.replaceState(null, '', target);
      var el = document.querySelector(target);
      if (el) el.scrollIntoView();
    }
  }
})();
