(function(){
  'use strict';
  /* One script for every page of kleooai.com. Nothing here reports anything to anybody: no analytics, no cookies,
     no remote code. Each block looks for its own elements and does nothing on a page that lacks them. */

  /* The address written into the markup. config.json still overrides it at load time, so the server moves by
     editing config.json alone — but a reader whose JavaScript never runs sees an address that actually answers. */
  var SHIPPED = "https://mcp.kleooai.com/mcp";
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- old Italian anchors, kept working ----------
     #come #connetti #prezzi #quinte were the home's section ids until the site went fully English. They are in links
     that have already been shared, so they are translated once on arrival instead of dropping the visitor at the top. */
  var MOVED = { come:'how', connetti:'connect', prezzi:'pricing', quinte:'engine' };
  function followMoved(){
    var was = (location.hash || '').slice(1);
    if (!MOVED[was]) return;
    var el = document.getElementById(MOVED[was]);
    if (!el) return;
    history.replaceState(null, '', '#' + MOVED[was]);
    el.scrollIntoView();
  }
  window.addEventListener('hashchange', followMoved);
  followMoved();

  /* ---------- the menu button, where the links are folded away (phones and narrow tablets) ---------- */
  var nav = document.querySelector('.nav'), navToggle = document.querySelector('.nav-toggle');
  if (nav && navToggle) {
    var setMenu = function(open){
      nav.classList.toggle('open', open);
      navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      navToggle.setAttribute('aria-label', open ? 'Close menu' : 'Menu');
    };
    navToggle.addEventListener('click', function(){ setMenu(!nav.classList.contains('open')); });
    // a link chosen from the menu closes it, and so does a tap anywhere else or the Escape key
    nav.addEventListener('click', function(e){ if (e.target.closest && e.target.closest('a')) setMenu(false); });
    var outside = function(e){ if (nav.classList.contains('open') && !nav.contains(e.target)) setMenu(false); };
    document.addEventListener('click', outside);
    if ('PointerEvent' in window) document.addEventListener('pointerdown', outside);   // iOS fires no click on plain page areas
    document.addEventListener('keydown', function(e){ if (e.key === 'Escape' && nav.classList.contains('open')) { setMenu(false); navToggle.focus(); } });
  }

  /* ---------- copy: the address, a prompt, a config snippet ---------- */
  var toast = document.getElementById('toast'), tt;
  function say(msg){ if (!toast) return; toast.textContent = msg; toast.classList.add('show'); clearTimeout(tt); tt = setTimeout(function(){ toast.classList.remove('show'); }, 1600); }
  // Every button reads "Copy" on its own; each one says what it copies, taken from the block it sits in.
  Array.prototype.forEach.call(document.querySelectorAll('[data-copy]'), function(b){
    if (b.getAttribute('aria-label')) return;
    var host = b.closest && (b.closest('.panel') || b.closest('.step') || b.closest('section'));
    var what = host && host.querySelector('h3, h2') ? host.querySelector('h3, h2').textContent.trim() : 'Kleo';
    var v = b.getAttribute('data-copy') || '';
    b.setAttribute('aria-label', /^https?:/.test(v) ? 'Copy the Kleo server address'
      : /^style:/.test(v) ? 'Copy the argument ' + v
      : b.closest('.style-say') ? 'Copy this prompt'
      : b.closest('.code') ? 'Copy the ' + what + ' snippet'
      : 'Copy the ' + what + ' text');
  });
  document.addEventListener('click', function(e){
    var b = e.target.closest && e.target.closest('[data-copy]'); if(!b) return;
    var txt = b.getAttribute('data-copy');
    function ok(){ say('Copied'); if (b.tagName === 'BUTTON' && !b.dataset.was && !b.classList.contains('style-arg')) { b.dataset.was = b.textContent; b.textContent = 'Copied ✓'; setTimeout(function(){ b.textContent = b.dataset.was; delete b.dataset.was; }, 1500); } }
    try { navigator.clipboard.writeText(txt).then(ok, function(){ say('Copy it by hand: ' + txt); }); }
    catch(err){ say('Copy it by hand: ' + txt); }
  });

  /* ---------- live MCP address from config.json ---------- */
  fetch('/config.json', {cache:'no-store'}).then(function(r){ return r.ok ? r.json() : null; }).then(function(cfg){
    if(!cfg) return;
    var note = document.getElementById('mcpStatus'); if(note){ note.textContent = cfg.note || ''; note.hidden = !cfg.note; }
    if(!cfg.mcp_url || !/^https:\/\/\S+$/.test(cfg.mcp_url)) return;
    var ph = SHIPPED, live = cfg.mcp_url;
    if (ph === live) return;   // the markup already ships the live address: nothing to rewrite
    document.querySelectorAll('[data-copy]').forEach(function(b){ b.setAttribute('data-copy', b.getAttribute('data-copy').split(ph).join(live)); });
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT), n;
    while((n = walker.nextNode())){ if(n.nodeValue.indexOf(ph) !== -1) n.nodeValue = n.nodeValue.split(ph).join(live); }
  }).catch(function(){});

  /* ---------- reveal on scroll ---------- */
  if (!reduce && 'IntersectionObserver' in window) {
    var els = document.querySelectorAll('.sec-head, .step, .card, .plan, .panel, .gantt, .tools, .faq > div, .cta .wrap > div, .style-row, .sample, .defs, .calculator, .prose > h3');
    var rio = new IntersectionObserver(function(entries){
      entries.forEach(function(en){ if (en.isIntersecting) { en.target.classList.add('in'); rio.unobserve(en.target); } });
    }, {rootMargin:'0px 0px -8% 0px', threshold:.08});
    Array.prototype.forEach.call(els, function(el, i){
      // What is already on screen is shown at once: the animation is for what scrolls in, never a gate on reading.
      if (el.getBoundingClientRect().top < window.innerHeight) return;
      el.setAttribute('data-reveal',''); el.style.setProperty('--d', ((i % 4) * 70) + 'ms'); rio.observe(el);
    });
  }

  /* ---------- the small things ---------- */
  // a hairline at the top that fills as you read
  var prog = document.getElementById('progress');
  if (prog) {
    var onScroll = function(){ var h = document.documentElement.scrollHeight - window.innerHeight; prog.style.setProperty('--p', h > 0 ? Math.min(1, window.scrollY / h) : 0); };
    window.addEventListener('scroll', onScroll, {passive:true}); onScroll();
  }
  // the REC line carries a real camera timecode, counting frames at 60 fps since you arrived
  var tcode = document.getElementById('tcode');
  if (tcode && !reduce) {
    var t0 = performance.now();
    var pad = function(n){ return (n < 10 ? '0' : '') + n; };
    var tick = function(now){
      var f = Math.floor((now - t0) / 1000 * 60);
      tcode.textContent = pad(Math.floor(f / 216000) % 24) + ':' + pad(Math.floor(f / 3600) % 60) + ':' + pad(Math.floor(f / 60) % 60) + ':' + pad(f % 60);
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }
  // the chat window shows your clock, like a real one would
  var clock = document.getElementById('demoClock');
  if (clock) {
    var setClock = function(){ var d = new Date(); clock.textContent = (d.getHours() < 10 ? '0' : '') + d.getHours() + ':' + (d.getMinutes() < 10 ? '0' : '') + d.getMinutes(); clock.hidden = false; };
    setClock(); setInterval(setClock, 30000);
  }

  /* ---------- hero: the render loop, with the stages a real job goes through ---------- */
  var tracks = Array.prototype.slice.call(document.querySelectorAll('#tracks .track'));
  if (tracks.length) {
    var stages = [
      {pct:5,   status:'Treatment · logline, angle, acts · look: realistic', track:0},
      {pct:12,  status:'Storyboard · direction, scenes, shots · 23 credits, confirmed', track:1},
      {pct:34,  status:'Generating the shots as footage · 4 of 11 · ~22 min left', track:2},
      {pct:58,  status:'Generating the shots as footage · 8 of 11 · ~12 min left', track:2},
      {pct:76,  status:'Narration · one voice, English · cutting the shots on the words', track:3},
      {pct:93,  status:'Finish · 2160×3840 · 60 fps · quality check', track:4},
      {pct:100, status:'Done · 28 min · link ready for 7 days', done:true}
    ];
    var fill = document.getElementById('renderFill'), pctEl = document.getElementById('renderPct'),
        statusEl = document.getElementById('renderStatus'), result = document.getElementById('result'),
        toolState = document.getElementById('toolState');
    var paint = function(s){
      if (fill) fill.style.width = s.pct + '%'; if (pctEl) pctEl.textContent = s.pct + '%'; if (statusEl) statusEl.textContent = s.status;
      tracks.forEach(function(t,i){
        t.classList.remove('done','active');
        if (s.done || i < s.track) t.classList.add('done'); else if (i === s.track) t.classList.add('active');
      });
      if (result) result.hidden = !s.done;
      if (toolState) { toolState.textContent = s.done ? 'done' : 'running'; toolState.classList.toggle('done', !!s.done); }
    };
    if (reduce) { paint(stages[stages.length-1]); }
    else { var si = 3; paint(stages[si]); setInterval(function(){ si = (si + 1) % stages.length; paint(stages[si]); }, 2400); }
  }

  /* ---------- the credit calculator on /pricing/: the server's own rule, max(10, ceil(seconds / 2)) ---------- */
  var duration = document.getElementById('duration');
  if (duration) {
    var output = document.getElementById('credit-result');
    var update = function(){
      var seconds = Number(duration.value);
      output.textContent = !Number.isInteger(seconds) || seconds < 15 || seconds > 300
        ? 'A whole number from 15 to 300 seconds'
        : seconds + ' s = ' + Math.max(10, Math.ceil(seconds / 2)) + ' credits';
    };
    duration.addEventListener('input', update); update();
  }

  /* ---------- sample films: shown, not handed over ----------
     A film plays by itself while it is in front of you, muted, and is only fetched then; it stops when it is not.
     There is nothing to click: the tag has no controls, the frame takes no pointer, no menu, no drag. The film is
     the content of these pages, not decoration, so it plays under prefers-reduced-motion too — in view only. */
  var medias = Array.prototype.slice.call(document.querySelectorAll('.style-media'));
  medias.forEach(function(m){
    m.addEventListener('contextmenu', function(e){ e.preventDefault(); });
    m.addEventListener('dragstart', function(e){ e.preventDefault(); });
    var v = m.querySelector('video');
    if (!v) return;
    v.addEventListener('play', function(){ m.classList.add('playing'); });
    v.addEventListener('pause', function(){ m.classList.remove('playing'); });
  });
  if ('IntersectionObserver' in window) {
    var vio = new IntersectionObserver(function(entries){
      entries.forEach(function(en){
        var v = en.target.querySelector('video'); if (!v) return;
        if (en.intersectionRatio >= .6) { var p = v.play(); if (p && p.catch) p.catch(function(){}); }
        else v.pause();
      });
    }, {threshold:[0, .6]});
    medias.forEach(function(m){ if (m.querySelector('video')) vio.observe(m); });
  }


  /* ---------- the looks page: the line plays, words light up as they are said, the shots cut on their word ---------- */
  var line = document.getElementById('line');
  if (line) {
    var TEXT = line.getAttribute('aria-label') || '';
    var words = TEXT.split(' '), shots = Array.prototype.slice.call(document.querySelectorAll('#shots .shot'));
    var cuts = shots.map(function(s){ return parseInt(s.getAttribute('data-from'), 10); });
    line.innerHTML = words.map(function(w, i){ return '<span class="w' + (cuts.indexOf(i) > 0 ? ' cut' : '') + '">' + w + '</span>'; }).join(' ');
    var spans = Array.prototype.slice.call(line.querySelectorAll('.w')), lineTimer, at = -1;
    var paintLine = function(i){
      spans.forEach(function(s, k){ s.classList.toggle('said', k < i); s.classList.toggle('now', k === i); });
      var k = 0; cuts.forEach(function(c, n){ if (i >= c) k = n; });
      shots.forEach(function(s, n){ s.classList.toggle('on', i >= 0 && n === k); });
    };
    var playLine = function(){
      clearTimeout(lineTimer); at = -1;
      if (reduce) { paintLine(words.length - 1); return; }   // no motion: the line already said, the last shot on screen
      (function step(){
        at += 1; paintLine(at);
        if (at < words.length) lineTimer = setTimeout(step, /[.,]$/.test(words[at]) ? 720 : 380);
        else lineTimer = setTimeout(function(){ paintLine(-1); shots.forEach(function(s){ s.classList.remove('on'); }); }, 2400);
      })();
    };
    var replay = document.getElementById('replay'); if (replay) replay.addEventListener('click', playLine);
    var scene = document.getElementById('scene'), played = false;
    if (scene && 'IntersectionObserver' in window) {
      new IntersectionObserver(function(en){ if (en[0].isIntersecting && !played) { played = true; playLine(); } }, {threshold:.35}).observe(scene);
    } else playLine();
  }

  /* ---------- the looks page: the hero takes the colour of the look you point at ---------- */
  var shero = document.querySelector('.styles-hero');
  if (shero) Array.prototype.forEach.call(document.querySelectorAll('.look'), function(l){
    l.addEventListener('pointerenter', function(){ shero.setAttribute('data-tint', l.getAttribute('data-look')); });
    l.addEventListener('pointerleave', function(){ shero.removeAttribute('data-tint'); });
  });
})();
