'use strict';
/* ===== HLD Gym engine ===== */

const TOC = JSON.parse(document.getElementById('toc-data').textContent);
const QUIZ = JSON.parse(document.getElementById('quiz-data').textContent); // {chapterId: [items]}
const CARDS = JSON.parse(document.getElementById('cards-data').textContent); // {chapterId: [cards]}
/* One engine, two compiled outputs. build.py stamps the mode onto <body>; the
   book output ships an empty CARDS and no data-origin templates, so every
   origins branch below is dead code there rather than a second code path. */
const ORIGINS = document.body.dataset.mode === 'origins';

/* ---------- state ---------- */
const KEY = 'hldgym_v1';
const DAY = 86400000;
const INTERVALS = [0, 1, 3, 7, 14, 30]; // days per Leitner box 1..5 (index 1..5)
const RANKS = [
  ['Intern', 0], ['Junior', 500], ['Mid-level', 1500],
  ['Senior', 3500], ['Staff', 7000], ['Distinguished', 12000],
];

function blank() {
  return {
    theme: null, gym: false, fontSize: 0, xp: 0,
    streak: 0, lastDay: null, freezesUsed: 0, freezeWeek: null,
    items: {},      // itemId -> {box, due, right, wrong}
    levels: {},     // chapterId -> {1: best%, 2: best%, 3: best%}
    feynman: {},    // key -> text
    boss: {},       // part -> {best, passed}
    heat: {},       // 'YYYY-MM-DD' -> count
    lastCh: null,
  };
}
let S = blank();
try { S = Object.assign(blank(), JSON.parse(localStorage.getItem(KEY) || '{}')); } catch (e) {}
const save = () => localStorage.setItem(KEY, JSON.stringify(S));

/* save() writes the whole of S, so two tabs on the same browser would each
   overwrite the other's last write — and /book and /origins share this key on
   purpose, which makes two tabs the normal case rather than the odd one. Re-read
   on any write from another tab. Last writer still wins within a single action;
   what this stops is a whole session being lost to a tab nobody looked at. */
window.addEventListener('storage', e => {
  if (e.key !== KEY || !e.newValue) return;
  try { S = Object.assign(blank(), JSON.parse(e.newValue)); } catch (err) { return; }
  renderChrome();
});

/* The gym layer — streak, xp, rank, stamps, boss battles, the review queue — is
   off for anyone who arrives just to read. Visiting #gym toggles it on for this
   browser and it stays on; nothing is deleted while it is off, so turning it
   back on restores whatever that browser had already earned. While it is off
   nothing is graded or recorded, so a public reader accumulates no progress at
   all. Feynman answers and the theme choice save either way — those are the
   reader's own words, not a score. */
const GYM = () => !!S.gym;

const today = () => new Date().toISOString().slice(0, 10);
const dayNum = iso => Math.floor(Date.parse(iso) / DAY);

/* ---------- toc helpers ---------- */
const CHAPTERS = [];
TOC.parts.forEach(p => p.chapters.forEach((c, i) => CHAPTERS.push({ ...c, part: p.n, idx: i + 1, partTitle: p.title })));
const chById = id => CHAPTERS.find(c => c.id === id);
const isReady = id => !!document.querySelector(`template[data-ch="${id}"]`);
const chQuiz = id => QUIZ[id] || [];
const chCards = id => (ORIGINS && CARDS[id]) || [];
const mastered = id => (S.levels[id] || {})[3] >= 80;

/* ---------- xp, rank, streak ---------- */
function rank() {
  let r = RANKS[0][0], next = null;
  for (let i = 0; i < RANKS.length; i++) {
    if (S.xp >= RANKS[i][1]) r = RANKS[i][0];
    else { next = RANKS[i]; break; }
  }
  return { name: r, next };
}
function addXP(n, label) {
  if (!GYM()) return;
  S.xp += n; save();
  toast(`+${n} XP${label ? ' · ' + label : ''}`);
  renderChrome();
}
function touchStreak() {
  if (!GYM()) return;
  const t = today();
  if (S.lastDay === t) return;
  // weekly freeze reset (ISO week key)
  const wk = (d => { const dt = new Date(d); dt.setDate(dt.getDate() - ((dt.getDay() + 6) % 7)); return dt.toISOString().slice(0, 10); })(t);
  if (S.freezeWeek !== wk) { S.freezeWeek = wk; S.freezesUsed = 0; }
  if (S.lastDay) {
    const gap = dayNum(t) - dayNum(S.lastDay) - 1; // fully missed days
    if (gap > 0) {
      const freezes = Math.min(gap, 2 - S.freezesUsed);
      if (freezes >= gap) { S.freezesUsed += gap; toast(`🧊 streak freeze used (${gap})`); }
      else S.streak = 0;
    }
  }
  S.streak += 1; S.lastDay = t;
  S.heat[t] = S.heat[t] || 0;
  save(); renderChrome();
}
function bumpHeat() { const t = today(); S.heat[t] = (S.heat[t] || 0) + 1; }

/* ---------- leitner ---------- */
function gradeItem(itemId, correct) {
  if (!GYM()) return;
  const it = S.items[itemId] || { box: 0, due: null, right: 0, wrong: 0 };
  if (correct) { it.right++; it.box = Math.min(5, (it.box || 0) + 1); }
  else { it.wrong++; it.box = 1; }
  /* box cannot carry this: from box 0 a right and a wrong answer both land on 1.
     Quiz items get the field too and ignore it. No migration — blank() does not
     enumerate item fields, so a saved state reads undefined as not-earned until
     the card is next answered. */
  it.ok = !!correct;   // last outcome, so a card can grey again after a miss
  it.due = new Date(Date.now() + INTERVALS[it.box] * DAY).toISOString().slice(0, 10);
  S.items[itemId] = it;
  bumpHeat(); touchStreak(); save();
}
function dueItems() {
  const t = today(), out = [];
  for (const [chId, items] of Object.entries(QUIZ)) {
    if (!isReady(chId)) continue;
    for (const q of items) {
      const st = S.items[q.id];
      if (st && st.due && st.due <= t) out.push({ ...q, chapter: chId });
    }
  }
  for (const c of allCards()) {
    const st = S.items[c.id];
    if (st && st.due && st.due <= t) out.push(c);
  }
  return out.sort(() => Math.random() - 0.5);
}

/* ---------- chrome ---------- */
const $ = sel => document.querySelector(sel);
function toast(msg) {
  const el = document.createElement('div');
  el.className = 'toast'; el.textContent = msg;
  $('#toast-root').appendChild(el);
  setTimeout(() => el.remove(), 2800);
}
function renderChrome() {
  const pill = $('#streak-pill');
  pill.hidden = !GYM();
  if (GYM()) pill.innerHTML = `🔥 <b>${S.streak}</b>d · ${S.xp} XP`;
  renderSidebar();
}
// Only the part you are working through is expanded. 51 chapters in one flat
// scroll is a wall; one part at a time is a place.
let openPart = null, sidebarFor = null;

function renderSidebar() {
  const cur = location.hash.replace('#ch/', '');
  if (cur !== sidebarFor) {
    sidebarFor = cur;
    const p = TOC.parts.find(p => p.chapters.some(c => c.id === cur));
    if (p) openPart = p.n;
  }
  if (openPart === null) openPart = TOC.parts[0].n;

  const gym = GYM();
  /* The brand in the header leaves for the sell page, so this is now the only
     route back to the book's own home — progress, streak, review. */
  const atHome = !location.hash || location.hash === '#home';
  let html = `<a class="side-ch side-home${atHome ? ' active' : ''}" href="#home">
    <span class="n">◆</span><span>home</span></a>`;
  for (const p of TOC.parts) {
    const done = p.chapters.filter(c => mastered(c.id)).length;
    const pct = Math.round(done / p.chapters.length * 100);
    const open = p.n === openPart ? 1 : 0;
    html += `<div class="side-part" data-part="${p.n}" data-open="${open}">
      <button class="side-part-btn" aria-expanded="${open ? 'true' : 'false'}">
        <span class="pn">Part ${p.n}${gym ? `<span class="frac">${done}/${p.chapters.length}</span>` : ''}</span>
        <span class="pt">${p.title}</span>
        ${gym ? `<span class="pbar"><i style="width:${pct}%"></i></span>` : ''}
      </button>
      <div class="side-list">`;
    p.chapters.forEach((c, i) => {
      const ready = isReady(c.id);
      const cls = ['side-ch', ready ? '' : 'soon', cur === c.id ? 'active' : ''].join(' ');
      const mark = gym && mastered(c.id) ? '<span class="m done">✔</span>' : '';
      html += `<a class="${cls}" href="#ch/${c.id}"><span class="n">${p.n}.${i + 1}</span><span>${c.title}</span>${mark}</a>`;
    });
    html += `</div></div>`;
  }
  const sb = $('#sidebar');
  sb.innerHTML = html;
  sb.querySelectorAll('.side-part-btn').forEach(b => b.addEventListener('click', () => {
    const n = +b.parentElement.dataset.part;
    openPart = openPart === n ? -1 : n;
    renderSidebar();
  }));
  // Scroll the sidebar by hand rather than with scrollIntoView: that call also
  // moves the sequential focus navigation starting point, so the first Tab on
  // a chapter landed in the middle of the chapter list and the skip link was
  // unreachable. Setting scrollTop moves the rail without touching focus.
  const active = sb.querySelector('.side-ch.active');
  if (active) {
    const top = active.offsetTop - sb.offsetTop;
    if (top < sb.scrollTop || top + active.offsetHeight > sb.scrollTop + sb.clientHeight) {
      sb.scrollTop = Math.max(0, top - sb.clientHeight / 2);
    }
  }
}

/* ---------- right rail: where you are inside the chapter ---------- */
let railSpy = null;

function clearRail() {
  if (railSpy) { removeEventListener('scroll', railSpy); railSpy = null; }
  $('#rail').innerHTML = '';
  $('.shell').classList.add('no-rail');
}

function renderRail(id) {
  clearRail();
  const rail = $('#rail');
  const heads = [...VIEW.querySelectorAll('.ch-body h2')];
  const levels = GYM() ? (S.levels[id] || {}) : {};
  // spelled out, not "L1" — lowercase chrome turns that into an unreadable "l1"
  const names = { 1: 'Level 1 · Recall', 2: 'Level 2 · Apply', 3: 'Level 3 · Senior bar' };

  let html = '';
  if (heads.length) {
    html += `<div class="rail-title">On this page</div><nav class="rail-toc">`;
    heads.forEach((h, i) => { html += `<button class="rail-link" data-i="${i}">${h.textContent}</button>`; });
    html += `</nav><div class="rail-sep"></div>`;
  }
  html += `<div class="rail-title">Quiz</div>`;
  [1, 2, 3].forEach(lv => {
    const b = levels[lv];
    const cls = b === undefined ? 'none' : (b >= 80 ? 'pass' : '');
    // with the gym off nothing is ever scored, so don't hang an empty score on it
    const score = GYM() ? `<b class="${cls}">${b === undefined ? '—' : b + '%'}</b>` : '';
    html += `<button class="rq" data-lv="${lv}">${names[lv]}${score}</button>`;
  });
  rail.innerHTML = html;
  $('.shell').classList.remove('no-rail');

  const how = { behavior: REDUCED ? 'auto' : 'smooth', block: 'start' };
  rail.querySelectorAll('.rail-link').forEach(b =>
    b.addEventListener('click', () => heads[+b.dataset.i].scrollIntoView(how)));
  rail.querySelectorAll('.rq').forEach(b => b.addEventListener('click', () => {
    VIEW.querySelector('.quiz-wrap').scrollIntoView(how);
    const tab = VIEW.querySelector(`.q-level-tab[data-lv="${b.dataset.lv}"]`);
    if (tab) tab.click();
  }));

  const links = [...rail.querySelectorAll('.rail-link')];
  if (!links.length) return;
  let queued = false;
  railSpy = () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      let idx = 0;
      heads.forEach((h, i) => { if (h.getBoundingClientRect().top <= 130) idx = i; });
      links.forEach((l, i) => l.classList.toggle('here', i === idx));
    });
  };
  addEventListener('scroll', railSpy, { passive: true });
  railSpy();
}

/* ---------- quiz rendering ---------- */
function renderQuizItem(q, onAnswer, num) {
  q = { ...q, options: [...q.options].sort(() => Math.random() - 0.5) }; // authors write correct-first; never show it that way
  const wrap = document.createElement('div');
  wrap.className = 'q-item';
  wrap.innerHTML = `<div class="q-num">${num || ''}${q.tag ? ' · ' + q.tag : ''} · level ${q.level}</div>
    <div class="q-text"></div>`;
  wrap.querySelector('.q-text').textContent = q.q;
  const multi = q.type === 'multi';
  const chosen = new Set();
  const correctSet = new Set(q.options.map((o, i) => o.correct ? i : -1).filter(i => i >= 0));

  const buttons = q.options.map((o, i) => {
    const b = document.createElement('button');
    b.className = 'q-opt'; b.type = 'button'; b.textContent = o.t;
    b.addEventListener('click', () => {
      if (multi) {
        // multi: toggle until submit
        if (chosen.has(i)) { chosen.delete(i); b.style.borderColor = ''; }
        else { chosen.add(i); b.style.borderColor = 'var(--accent)'; }
        return;
      }
      finish(new Set([i]));
    });
    wrap.appendChild(b);
    return b;
  });

  let submit = null;
  if (multi) {
    submit = document.createElement('button');
    submit.className = 'btn ghost'; submit.type = 'button'; submit.textContent = 'Check my picks';
    submit.addEventListener('click', () => { if (chosen.size) finish(chosen); });
    wrap.appendChild(submit);
  }

  function whyPanel(opt, ok, picked) {
    const d = document.createElement('div');
    d.className = 'q-why ' + (ok ? 'right' : 'wrong');
    d.innerHTML = `<b class="verdict">${ok ? (picked ? '✔ Correct' : 'The right answer') : '✘ Not this one'}</b>`;
    const p = document.createElement('span'); p.textContent = opt.why; d.appendChild(p);
    return d;
  }

  function finish(picks) {
    const correct = picks.size === correctSet.size && [...picks].every(i => correctSet.has(i));
    buttons.forEach(b => b.disabled = true);
    if (submit) submit.remove();
    q.options.forEach((o, i) => {
      const b = buttons[i];
      if (picks.has(i)) {
        b.classList.add(o.correct ? 'picked-right' : 'picked-wrong');
        b.insertAdjacentElement('afterend', whyPanel(o, o.correct, true));
      } else if (o.correct) {
        b.classList.add('reveal-right');
        b.insertAdjacentElement('afterend', whyPanel(o, true, false));
      }
    });
    onAnswer(correct);
  }
  return wrap;
}

/* ---------- cards ---------- */
const cardEarned = id => !!(S.items[id] || {}).ok;

/* Free text, then self-grade. Weaker than a graded MCQ and chosen anyway: it is
   production rather than recognition, which is the thing learning-and-retention.md
   says the book has none of. It is also how every spaced-repetition tool works.
   The card face is hidden until the reader commits, or the prompt would be
   answerable by reading the answer. */
function renderCard(card, onAnswer) {
  const wrap = document.createElement('div');
  const earned = cardEarned(card.id);
  wrap.className = 'card card-' + card.suit + (earned ? ' earned' : '');
  wrap.innerHTML = `<div class="card-suit">${card.suit}</div>
    <div class="card-prompt"></div>
    <div class="card-face" hidden>
      <div class="card-title"></div>
      <div class="card-sub"></div>
      <div class="card-body"></div>
    </div>`;
  wrap.querySelector('.card-prompt').textContent = card.prompt;
  wrap.querySelector('.card-title').textContent = card.title;
  wrap.querySelector('.card-sub').textContent = card.sub || '';
  wrap.querySelector('.card-body').textContent = card.body;
  if (card.asset) {
    /* setAttribute, not interpolation into innerHTML: a stray quote in an
       authored asset path would close the src attribute and inject a handler. */
    const face = wrap.querySelector('.card-face');
    const img = document.createElement('img');
    img.className = 'card-art';
    img.setAttribute('src', card.asset);
    img.alt = card.title;
    face.insertBefore(img, face.firstChild);
  }

  const ta = document.createElement('textarea');
  ta.className = 'card-answer';
  ta.setAttribute('aria-label', card.prompt);
  ta.placeholder = 'Say it before you look. A wrong guess still beats reading the answer cold.';
  wrap.insertBefore(ta, wrap.querySelector('.card-face'));

  const reveal = document.createElement('button');
  reveal.className = 'btn ghost'; reveal.type = 'button';
  reveal.textContent = 'Show the card';
  wrap.appendChild(reveal);

  reveal.addEventListener('click', () => {
    reveal.remove();
    ta.disabled = true;
    wrap.querySelector('.card-face').hidden = false;
    const model = document.createElement('div');
    model.className = 'card-model';
    model.textContent = card.answer;
    wrap.appendChild(model);
    const grade = document.createElement('div');
    grade.className = 'card-grade';
    [['Got it', true], ['Missed it', false]].forEach(([label, ok]) => {
      const b = document.createElement('button');
      b.className = 'btn' + (ok ? '' : ' ghost'); b.type = 'button'; b.textContent = label;
      b.addEventListener('click', () => {
        grade.remove();
        wrap.classList.toggle('earned', ok);
        wrap.classList.toggle('missed', !ok);
        onAnswer(ok);
      });
      grade.appendChild(b);
    });
    wrap.appendChild(grade);
  });
  return wrap;
}

function allCards() {
  const out = [];
  for (const [chId, cards] of Object.entries(CARDS)) {
    if (!isReady(chId)) continue;
    for (const c of cards) out.push({ ...c, chapter: chId, kind: 'card' });
  }
  return out;
}

/* ---------- views ---------- */
const VIEW = $('#view');

function renderHome() {
  const gym = GYM();
  const due = gym ? dueItems().length : 0;
  const done = CHAPTERS.filter(c => mastered(c.id)).length;
  const readyCount = CHAPTERS.filter(c => isReady(c.id)).length;
  const r = rank();
  const resumed = !!(S.lastCh && isReady(S.lastCh));
  const cont = resumed ? chById(S.lastCh) : CHAPTERS.find(c => isReady(c.id) && !mastered(c.id));
  let html = `<div class="content">
    <p class="eyebrow">${gym ? 'Training floor' : 'Senior system design'}</p>
    <h1 class="ch-title">${gym ? 'Welcome back.' : 'HLD Gym'}</h1>`;

  if (gym) {
    html += `<div class="tiles">
      <div class="tile accent"><div class="tile-label">Rank</div><div class="tile-value">${r.name}</div>
        <div class="tile-label">${r.next ? (r.next[1] - S.xp) + ' xp to ' + r.next[0] : 'max rank'}</div></div>
      <div class="tile"><div class="tile-label">XP</div><div class="tile-value">${S.xp}</div></div>
      <div class="tile warm"><div class="tile-label">Streak</div><div class="tile-value">${S.streak}<small> days</small></div></div>
      <div class="tile"><div class="tile-label">Mastered</div><div class="tile-value">${done}<small> / ${CHAPTERS.length}</small></div></div>
    </div>`;
  } else {
    html += `<p>${readyCount} chapters on designing systems at the level a senior interview actually probes. Every idea starts with the problem that forces it, carries an analogy and a real company's incident, and ends with a quiz that explains every option — including the ones you didn't pick.</p>`;
  }

  html += `<p>
      ${cont ? `<a class="btn" href="#ch/${cont.id}">${gym || resumed ? 'Continue' : 'Start reading'}: ${cont.title}</a>` : ''}
      ${gym ? `<a class="btn ghost" href="#review">Review due · ${due}</a>` : ''}
      ${ORIGINS ? `<a class="btn ghost" href="#cards">The collection · ${allCards().filter(c => cardEarned(c.id)).length}/${allCards().length}</a>` : ''}
      ${ORIGINS ? `<a class="btn ghost" href="#timeline">The timeline</a>` : ''}
    </p>`;

  if (gym) {
    html += `<h2 style="margin-top:2em">Review activity</h2>
    <div class="heat" aria-label="review activity heatmap">${heatCells()}</div>
    <div class="heat-cap">last 15 weeks · darker = more answers</div>`;
  }

  for (const p of TOC.parts) {
    const boss = S.boss[p.n];
    const partReady = p.chapters.some(c => isReady(c.id));
    html += `<div class="part-block">
      <div class="part-head"><h2>Part ${p.n} — ${p.title}</h2><span class="tagline">${p.tagline}</span>
      ${gym && partReady ? `<a class="btn ghost bossbtn" href="#boss/${p.n}">${boss?.passed ? '👑 Boss cleared' : 'Boss battle'}</a>` : ''}</div>
      <div class="ch-grid">`;
    p.chapters.forEach((c, i) => {
      const ready = isReady(c.id);
      const st = !gym ? ''
        : mastered(c.id) ? '<span class="st done">✔</span>'
        : (S.levels[c.id] ? '<span class="st part">◐</span>' : '');
      html += `<a class="ch-cell ${ready ? '' : 'soon'}" href="#ch/${c.id}"><span class="n">${p.n}.${i + 1}</span><span>${c.title}${ready ? '' : ' <small>(soon)</small>'}</span>${st}</a>`;
    });
    html += `</div></div>`;
  }
  if (gym) {
    html += `<div class="part-block"><h2>Backup</h2>
      <p style="font-size:.9rem;color:var(--ink-2)">Progress lives in this browser. Copy the blob to move it to another device.</p>
      <p><button class="btn ghost" id="exp">Export progress</button> <button class="btn ghost" id="imp">Import</button></p>
      <textarea id="expbox" style="width:100%;min-height:70px;display:none;font-size:.75rem"></textarea></div>`;
  }
  html += `</div>`;
  VIEW.innerHTML = html;
  if (!gym) return;
  $('#exp').onclick = () => { const b = $('#expbox'); b.style.display = 'block'; b.value = JSON.stringify(S); b.select(); };
  $('#imp').onclick = () => {
    const b = $('#expbox'); b.style.display = 'block';
    if (!b.value.trim()) { b.placeholder = 'Paste your exported blob here, then press Import again.'; b.focus(); return; }
    try { S = Object.assign(blank(), JSON.parse(b.value)); save(); toast('Progress imported'); route(); }
    catch (e) { toast('That blob did not parse'); }
  };
}

function heatCells() {
  const cells = [];
  const now = new Date();
  const start = new Date(now - 104 * DAY);
  start.setDate(start.getDate() - ((start.getDay() + 6) % 7)); // align Monday
  for (let d = new Date(start); d <= now; d.setDate(d.getDate() + 1)) {
    const k = d.toISOString().slice(0, 10);
    const v = S.heat[k] || 0;
    const l = v === 0 ? '' : v < 5 ? 'l1' : v < 15 ? 'l2' : v < 30 ? 'l3' : 'l4';
    cells.push(`<i class="${l}" title="${k}: ${v}"></i>`);
  }
  return cells.join('');
}

/* ---------- diagram animation ----------
   Edges draw themselves, nodes fade in left-to-right as a diagram scrolls into
   view. Diagrams that mark parts with data-step="N" also get a stepper.
   Everything degrades to a plain static diagram: no JS, no motion preference,
   or an unmeasurable SVG all leave the markup untouched. */
const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;
const DRAW_MS = 550;
let dgObserver = null;
let dgPrepared = [];

// The CSS @media print rule cannot reach marker-end, which is an attribute, so
// the arrowheads have to come back here.
addEventListener('beforeprint', () => dgPrepared.forEach(svg => svg._dgEls.forEach(el => {
  el.style.transitionDelay = '0ms';
  el.style.opacity = '1';
  if (el._dgLen) {
    el.style.strokeDashoffset = '0';
    if (el._dgMarker) { clearTimeout(el._dgTimer); el.setAttribute('marker-end', el._dgMarker); }
  }
})));

function dgPrep(el) {
  const drawable = /^(line|path|polyline)$/i.test(el.tagName)
    && !el.hasAttribute('stroke-dasharray')
    && !el.classList.contains('dg-zone');
  if (drawable) {
    let len = 0;
    try { len = el.getTotalLength(); } catch (e) { }
    if (len > 0) {
      el._dgLen = len;
      el.style.strokeDasharray = len;
      el.style.strokeDashoffset = len;
      // markers paint at full opacity regardless of the dash pattern, so an
      // arrowhead would hang in mid-air while its line is still drawing
      const mk = el.getAttribute('marker-end');
      if (mk) { el._dgMarker = mk; el.setAttribute('marker-end', 'none'); }
    }
  }
  el.style.opacity = '0';
}

function dgShow(el, delay) {
  el.style.transitionDelay = delay + 'ms';
  el.style.opacity = '1';
  if (el._dgLen) {
    el.style.strokeDashoffset = '0';
    if (el._dgMarker) {
      clearTimeout(el._dgTimer);
      el._dgTimer = setTimeout(() => el.setAttribute('marker-end', el._dgMarker), delay + DRAW_MS - 60);
    }
  }
  if (el._dgFlow) {
    clearTimeout(el._dgFlowTimer);
    el._dgFlowTimer = setTimeout(() => { el._dgFlow.style.display = ''; }, delay + DRAW_MS);
  }
}

function dgHide(el) {
  el.style.transitionDelay = '0ms';
  el.style.opacity = '0';
  if (el._dgLen) {
    el.style.strokeDashoffset = el._dgLen;
    if (el._dgMarker) { clearTimeout(el._dgTimer); el.setAttribute('marker-end', 'none'); }
  }
  if (el._dgFlow) { clearTimeout(el._dgFlowTimer); el._dgFlow.style.display = 'none'; }
}

// A pulse that keeps travelling along each arrow after the draw finishes. This
// is what stops a diagram going dead the moment it has finished appearing.
// Only directional edges get one — lifelines and grouping boxes stay quiet.
function dgAddFlow(svg) {
  svg.querySelectorAll('.dg-flow').forEach(f => f.remove());
  svg._dgEls.forEach((el, i) => {
    if (!el._dgLen || !el._dgMarker) return;
    const f = el.cloneNode(false);
    f.removeAttribute('marker-end');
    f.removeAttribute('stroke-dasharray');
    // the source already carries the hidden inline state from dgPrep, and an
    // inline opacity:0 would outrank the stylesheet rule that lights the pulse
    f.removeAttribute('style');
    f.setAttribute('class', 'dg-flow');
    f.style.strokeDasharray = `12 ${el._dgLen}`;
    f.style.setProperty('--flow-from', el._dgLen + 12);
    f.style.animationDelay = `-${(i % 7) * 0.4}s`;
    f.style.display = 'none';
    el.after(f);
    el._dgFlow = f;
  });
}

function dgRun(svg, upto) {
  const els = svg._dgEls;
  els.forEach(el => { if (el._dgStep > upto && el._dgVisible) { el._dgVisible = false; dgHide(el); } });
  const fresh = els.filter(el => el._dgStep <= upto && !el._dgVisible);
  const gap = Math.min(45, 900 / Math.max(1, fresh.length));
  fresh.forEach((el, i) => { el._dgVisible = true; dgShow(el, Math.round(i * gap)); });
}

function dgPrepare(svg) {
  const els = [...svg.querySelectorAll('rect, circle, ellipse, line, path, polyline, polygon, text')]
    .filter(el => !el.closest('defs') && !el.classList.contains('dg-flow'));
  if (!els.length) return false;
  els.forEach(el => {
    try { const b = el.getBBox(); el._dgx = b.x; el._dgy = b.y; }
    catch (e) { el._dgx = 0; el._dgy = 0; }
    const holder = el.closest('[data-step]');
    el._dgStep = holder ? +holder.dataset.step : 0;
    el._dgVisible = false;
  });
  els.sort((a, b) => (a._dgStep - b._dgStep) || (a._dgx - b._dgx) || (a._dgy - b._dgy));
  els.forEach(dgPrep);
  svg._dgEls = els;
  svg._dgMax = els.reduce((m, el) => Math.max(m, el._dgStep), 0);
  svg._dgCur = 1;
  dgAddFlow(svg);
  return true;
}

function dgReplay(svg) {
  svg._dgEls.forEach(el => { el._dgVisible = false; dgHide(el); });
  svg._dgCur = 1;
  svg.classList.add('dg-anim');
  dgRun(svg, 1);
  if (svg._dgSync) svg._dgSync();
}

// One control row per diagram. Every diagram gets replay and expand; only the
// ones authored with data-step get the step controls and narration.
function dgControls(svg, { expandable }) {
  const stepped = svg._dgMax > 1;
  const bar = document.createElement('div');
  bar.className = 'dg-steps';
  bar.innerHTML =
    (stepped ? `<button class="dg-prev" aria-label="Previous step">◀</button>` +
      `<button class="dg-next" aria-label="Next step">▶</button>` : '') +
    `<button class="dg-replay" aria-label="Replay the animation">↻</button>` +
    (expandable ? `<button class="dg-expand" aria-label="Open this diagram full screen">⤢</button>` : '') +
    `<span class="dg-count"></span><span class="dg-label"></span>`;

  const labels = {};
  svg.querySelectorAll('[data-step][data-step-label]')
    .forEach(g => { labels[+g.dataset.step] = g.dataset.stepLabel; });
  const sync = () => {
    if (!stepped) return;
    bar.querySelector('.dg-prev').disabled = svg._dgCur <= 1;
    bar.querySelector('.dg-next').disabled = svg._dgCur >= svg._dgMax;
    bar.querySelector('.dg-count').textContent = `${svg._dgCur} / ${svg._dgMax}`;
    bar.querySelector('.dg-label').textContent = labels[svg._dgCur] || '';
  };
  const go = n => {
    svg._dgCur = Math.min(svg._dgMax, Math.max(1, n));
    dgRun(svg, svg._dgCur);
    sync();
  };
  if (stepped) {
    bar.querySelector('.dg-prev').addEventListener('click', () => go(svg._dgCur - 1));
    bar.querySelector('.dg-next').addEventListener('click', () => go(svg._dgCur + 1));
  }
  bar.querySelector('.dg-replay').addEventListener('click', () => dgReplay(svg));
  if (expandable) bar.querySelector('.dg-expand').addEventListener('click', () => dgOpen(svg));
  svg._dgGo = go;
  svg._dgSync = sync;
  // the first reveal belongs to the observer, so the diagram animates when the
  // reader reaches it rather than while it is still off-screen
  sync();
  return bar;
}

function dgOpen(source) {
  const fig = source.closest('figure');
  const caption = fig && fig.querySelector('figcaption');
  const svg = source.cloneNode(true);
  svg.querySelectorAll('.dg-flow').forEach(f => f.remove());
  svg.classList.remove('dg-anim');

  const overlay = document.createElement('div');
  overlay.className = 'dg-overlay';
  overlay.innerHTML = `<button class="dg-close" aria-label="Close">✕ close</button>`;
  const stage = document.createElement('div');
  stage.className = 'dg-stage';
  stage.appendChild(svg);
  overlay.appendChild(stage);
  if (caption) {
    const cap = document.createElement('p');
    cap.className = 'dg-cap';
    cap.textContent = caption.textContent;
    overlay.appendChild(cap);
  }
  document.body.appendChild(overlay);
  document.body.style.overflow = 'hidden';

  const close = () => {
    document.body.style.overflow = '';
    removeEventListener('keydown', onKey);
    overlay.remove();
    if (document.fullscreenElement) document.exitFullscreen().catch(() => { });
  };
  const onKey = e => {
    if (e.key === 'Escape') close();
    else if (svg._dgMax > 1 && e.key === 'ArrowRight') svg._dgGo(svg._dgCur + 1);
    else if (svg._dgMax > 1 && e.key === 'ArrowLeft') svg._dgGo(svg._dgCur - 1);
  };
  overlay.querySelector('.dg-close').addEventListener('click', close);
  overlay.addEventListener('click', e => { if (e.target === overlay) close(); });
  addEventListener('keydown', onKey);

  // measurable only once it is in the document and laid out
  if (dgPrepare(svg)) {
    stage.appendChild(dgControls(svg, { expandable: false }));
    svg.classList.add('dg-anim');
    dgRun(svg, 1);
    setTimeout(() => svg.classList.add('dg-live'), 1500);
  }
  overlay.requestFullscreen && overlay.requestFullscreen().catch(() => { });
}

function initDiagrams(root) {
  if (dgObserver) { dgObserver.disconnect(); dgObserver = null; }
  dgPrepared = [];
  if (REDUCED || !('IntersectionObserver' in window)) return;

  const svgs = [...root.querySelectorAll('svg')]
    .filter(s => s.querySelector('[class^="dg-"], [class*=" dg-"]'))
    .filter(s => s.getBoundingClientRect().width > 0);
  if (!svgs.length) return;

  dgObserver = new IntersectionObserver(entries => {
    entries.forEach(e => {
      const svg = e.target;
      if (e.isIntersecting) {
        // class added here, not at prep time: the hidden state must already be
        // painted or the transition would run backwards from visible
        svg.classList.add('dg-anim');
        dgRun(svg, svg._dgCur);
        clearTimeout(svg._dgLiveTimer);
        svg._dgLiveTimer = setTimeout(() => svg.classList.add('dg-live'), 1500);
      } else if (e.intersectionRatio === 0) {
        // fully gone: stop the pulses, and rearm the reveal so scrolling back
        // replays it instead of finding a diagram that already happened
        clearTimeout(svg._dgLiveTimer);
        svg.classList.remove('dg-live');
        if (svg._dgMax <= 1) svg._dgEls.forEach(el => { el._dgVisible = false; dgHide(el); });
      }
    });
  }, { threshold: [0, 0.12], rootMargin: '0px 0px -6% 0px' });

  svgs.forEach(svg => {
    if (!dgPrepare(svg)) return;
    dgPrepared.push(svg);
    svg.classList.add('dg-zoomable');
    svg.parentElement.insertBefore(dgControls(svg, { expandable: true }), svg);
    svg.addEventListener('click', () => dgOpen(svg));
    dgObserver.observe(svg);
  });
}

/* The style guide defines a cold open as the paragraphs before the first <h2>.
   That makes the swap mechanical: drop everything up to the first heading, put
   the origin story there instead. A chapter with no .origin.html is untouched,
   which is why partial coverage is always shippable. */
function swapColdOpen(body, id) {
  const tpl = document.querySelector(`template[data-origin="${id}"]`);
  if (!tpl) return;
  const first = body.querySelector('h2');
  while (body.firstChild && body.firstChild !== first) body.removeChild(body.firstChild);
  body.insertBefore(tpl.content.cloneNode(true), first);
}

function renderChapter(id) {
  const c = chById(id);
  const tpl = document.querySelector(`template[data-ch="${id}"]`);
  if (!c || !tpl) { VIEW.innerHTML = `<div class="content"><h1 class="ch-title">Coming soon</h1><p>This chapter isn't written yet.</p></div>`; clearRail(); return; }
  S.lastCh = id; save();
  const gym = GYM();

  const words = tpl.content.textContent.split(/\s+/).length;
  VIEW.innerHTML = `<div class="content">
    <p class="eyebrow">Part ${c.part} — ${c.partTitle}</p>
    <h1 class="ch-title">${c.title} ${gym && mastered(id) ? '<span class="stamp">Mastered</span>' : ''}</h1>
    <div class="ch-meta">${c.part}.${c.idx} · ~${Math.max(1, Math.round(words / 220))} min read · ${chQuiz(id).length} quiz questions</div>
    <div class="ch-body"></div>
    <div class="quiz-wrap"><h2>Quiz</h2><p style="font-size:.9rem;color:var(--ink-2)">${gym ? 'Three levels. Pass Level 3 with 80% to earn the stamp. Answers go into your review queue.' : 'Three levels, hardest last. Every option explains itself once you pick — including the ones that are wrong.'}</p>
    <div class="q-level-tabs"></div><div class="q-zone"></div></div>
    <div class="deck-wrap"></div>
    <div class="ch-nav"></div>
  </div>`;
  const body = VIEW.querySelector('.ch-body');
  body.appendChild(tpl.content.cloneNode(true));
  if (ORIGINS) swapColdOpen(body, id);
  initDiagrams(body);

  // feynman blocks
  VIEW.querySelectorAll('.feynman').forEach(f => {
    const key = f.dataset.key;
    const ta = document.createElement('textarea');
    ta.placeholder = 'Write it in your own words. Out loud is even better.';
    // a placeholder is not an accessible name — it disappears the moment you type
    ta.setAttribute('aria-label', f.querySelector('.fey-prompt')?.textContent.trim() || 'Explain it yourself');
    ta.value = S.feynman[key] || '';
    ta.addEventListener('input', () => { S.feynman[key] = ta.value; save(); });
    const hint = document.createElement('div');
    hint.className = 'fey-hint';
    hint.textContent = 'Saved automatically. Jargon you can’t avoid = a gap you just found.';
    const model = f.querySelector('.fey-model');
    f.insertBefore(ta, model); f.insertBefore(hint, model);
  });

  // quiz levels
  const items = chQuiz(id);
  const tabs = VIEW.querySelector('.q-level-tabs');
  const zone = VIEW.querySelector('.q-zone');
  const levels = [1, 2, 3];
  const names = { 1: 'Level 1 · Recall', 2: 'Level 2 · Apply', 3: 'Level 3 · Senior bar' };
  function openLevel(lv) {
    tabs.querySelectorAll('.q-level-tab').forEach(t => t.classList.toggle('active', +t.dataset.lv === lv));
    zone.innerHTML = '';
    const qs = items.filter(q => q.level === lv);
    if (!qs.length) { zone.innerHTML = '<p>No questions at this level yet.</p>'; return; }
    let answered = 0, correct = 0;
    const firstTry = {};
    qs.forEach((q, i) => {
      zone.appendChild(renderQuizItem(q, ok => {
        answered++; if (ok) correct++;
        if (firstTry[q.id] === undefined) {
          firstTry[q.id] = ok;
          if (ok) addXP(lv === 1 ? 10 : lv === 2 ? 15 : 20);
        }
        gradeItem(q.id, ok);
        if (answered === qs.length) levelDone();
      }, `Q${i + 1}/${qs.length}`));
    });
    function levelDone() {
      const pct = Math.round(100 * correct / qs.length);
      const sum = document.createElement('div');
      sum.className = 'q-summary' + (pct >= 80 ? ' pass' : '');
      if (!gym) {
        // no stamp, no best-ever, nothing recorded — just the score for this run
        sum.innerHTML = `<b>${pct}%</b> (${correct}/${qs.length}). ` +
          (pct >= 80 ? 'Strong.' : 'Below 80 — worth rereading the sections you missed.');
        zone.appendChild(sum);
        sum.scrollIntoView({ behavior: 'smooth', block: 'center' });
        return;
      }
      const best = (S.levels[id] = S.levels[id] || {});
      const prev = best[lv] || 0;
      best[lv] = Math.max(prev, pct); save();
      const pass = lv === 3 && pct >= 80;
      sum.innerHTML = `<b>${pct}%</b> (${correct}/${qs.length}) — best ${best[lv]}%. ` +
        (pass && prev < 80 ? '<span class="stamp big">Mastered</span> Chapter stamped. It’s yours now — reviews will keep it that way.'
          : pct >= 80 ? 'Strong.' : 'Below 80 — reread the sections you missed, the queue will bring these back.');
      zone.appendChild(sum);
      if (pass && prev < 80) { addXP(50, 'chapter mastered'); renderChrome(); }
      sum.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }
  levels.forEach(lv => {
    const b = document.createElement('button');
    b.className = 'q-level-tab'; b.dataset.lv = lv;
    const best = gym ? (S.levels[id] || {})[lv] : undefined;
    b.innerHTML = names[lv] + (best !== undefined ? ` <span class="score">${best}%</span>` : '');
    b.onclick = () => openLevel(lv);
    tabs.appendChild(b);
  });
  openLevel(1);

  // the deck
  const cards = chCards(id);
  const deck = VIEW.querySelector('.deck-wrap');
  if (cards.length) {
    deck.innerHTML = `<h2>The deck</h2><p class="deck-note">${cards.length} cards from this chapter's story. Answer to keep one — unanswered cards stay grey and never enter your review queue.</p><div class="deck"></div>`;
    const zone = deck.querySelector('.deck');
    cards.forEach(c => zone.appendChild(renderCard(c, ok => {
      if (ok && !cardEarned(c.id)) addXP(15, 'card earned');
      gradeItem(c.id, ok);
    })));
  }

  // prev/next
  const i = CHAPTERS.indexOf(chById(id));
  const prev = CHAPTERS.slice(0, i).reverse().find(c2 => isReady(c2.id));
  const next = CHAPTERS.slice(i + 1).find(c2 => isReady(c2.id));
  VIEW.querySelector('.ch-nav').innerHTML =
    (prev ? `<a class="btn ghost" href="#ch/${prev.id}">← ${prev.title}</a>` : '<span></span>') +
    (next ? `<a class="btn" href="#ch/${next.id}">${next.title} →</a>` : '');
  window.scrollTo(0, 0);
  renderRail(id);
}

function renderReview() {
  const due = dueItems();
  VIEW.innerHTML = `<div class="content"><p class="eyebrow">Spaced review</p>
    <h1 class="ch-title">Review queue</h1>
    <p>${due.length ? due.length + ' answers are due. Old chapters, mixed together on purpose — that’s what makes it stick.' : 'Nothing due. Go learn something new, or come back tomorrow.'}</p>
    <div class="q-zone"></div></div>`;
  const zone = VIEW.querySelector('.q-zone');
  let i = 0, right = 0;
  function nextItem() {
    zone.innerHTML = '';
    if (i >= due.length) {
      if (due.length) zone.innerHTML = `<div class="q-summary pass"><b>${right}/${due.length}</b> — queue cleared. See you when the next batch is due.</div>`;
      return;
    }
    const q = due[i];
    const ch = chById(q.chapter);
    const head = document.createElement('div');
    head.className = 'review-item-tag';
    head.textContent = `${i + 1}/${due.length} · from ${ch ? ch.title : q.chapter}`;
    zone.appendChild(head);
    const cb = ok => {
      gradeItem(q.id, ok);
      if (ok) { right++; addXP(5); }
      i++;
      setTimeout(nextItem, ok ? 900 : 2600);
    };
    zone.appendChild(q.kind === 'card' ? renderCard(q, cb) : renderQuizItem(q, cb));
  }
  nextItem();
}

function renderCollection() {
  const cards = allCards();
  const earned = cards.filter(c => cardEarned(c.id));
  const suits = ['person', 'incident', 'artifact', 'ripple'];
  const pct = cards.length ? Math.round(100 * earned.length / cards.length) : 0;
  VIEW.innerHTML = `<div class="content"><p class="eyebrow">The collection</p>
    <h1 class="ch-title">${earned.length} of ${cards.length}</h1>
    <p>Every card here came out of a real, dated, sourced event. You keep one by answering it, not by reading it.</p>
    <div class="coll-bar"><span style="width:${pct}%"></span></div>
    <div class="coll-suits">${suits.map(s => {
      const all = cards.filter(c => c.suit === s);
      const got = all.filter(c => cardEarned(c.id));
      return `<div class="coll-suit"><b>${s}</b><span>${got.length}/${all.length}</span></div>`;
    }).join('')}</div>
    <div class="coll-grid"></div></div>`;
  const grid = VIEW.querySelector('.coll-grid');
  if (!cards.length) {
    grid.innerHTML = '<p>No cards yet. They arrive with the chapters that have an origin story.</p>';
    return;
  }
  cards.forEach(c => {
    const got = cardEarned(c.id);
    const a = document.createElement('a');
    a.className = 'coll-card card-' + c.suit + (got ? ' earned' : '');
    a.href = `#ch/${c.chapter}`;
    a.innerHTML = `<span class="coll-year">${c.year}</span><span class="coll-title"></span><span class="coll-suit-tag">${c.suit}</span>`;
    // an unearned card must not leak its own answer from the collection page
    a.querySelector('.coll-title').textContent = got ? c.title : '— locked —';
    a.title = got ? c.title : 'Answer this card in its chapter to keep it';
    grid.appendChild(a);
  });
}

/* The one thing 51 separate chapters cannot teach: these ideas arrived in an
   order, and each was a reaction to the one before. No new content — the spine
   is just every card's year, sorted. */
function renderTimeline() {
  const cards = allCards().slice().sort((a, b) => a.year - b.year || a.id.localeCompare(b.id));
  const got = cards.filter(c => cardEarned(c.id)).length;
  VIEW.innerHTML = `<div class="content"><p class="eyebrow">One history</p>
    <h1 class="ch-title">The timeline</h1>
    <p>${got} of ${cards.length} moments lit. Every idea in this book was a reaction to the one before it.</p>
    <ol class="tl"></ol></div>`;
  const ol = VIEW.querySelector('.tl');
  let lastYear = null;
  cards.forEach(c => {
    const earned = cardEarned(c.id);
    const li = document.createElement('li');
    li.className = 'tl-node card-' + c.suit + (earned ? ' earned' : '');
    li.innerHTML = `<span class="tl-year">${c.year === lastYear ? '' : c.year}</span>
      <a class="tl-label" href="#ch/${c.chapter}"></a>`;
    li.querySelector('.tl-label').textContent = earned ? c.title : '— not yet earned —';
    ol.appendChild(li);
    lastYear = c.year;
  });
  if (!cards.length) ol.innerHTML = '<li>The timeline fills as chapters get their stories.</li>';
}

function renderBoss(part) {
  const p = TOC.parts.find(x => x.n === +part);
  if (!p) { location.hash = '#home'; return; }
  const pool = p.chapters.filter(c => isReady(c.id)).flatMap(c => chQuiz(c.id));
  const hard = pool.filter(q => q.level >= 2);
  const tech = (hard.length >= 20 ? hard : pool).sort(() => Math.random() - 0.5);
  /* Only cards the reader has already earned. A boss round is a test of what you
     hold, not a first meeting — and an unearned card here would hand over its
     answer outside the gate. */
  const chIds = new Set(p.chapters.map(c => c.id));
  const hist = allCards().filter(c => chIds.has(c.chapter) && cardEarned(c.id))
    .sort(() => Math.random() - 0.5).slice(0, 6);
  const qs = [...tech.slice(0, 20 - hist.length), ...hist].sort(() => Math.random() - 0.5);
  const best = S.boss[part]?.best;
  VIEW.innerHTML = `<div class="content"><p class="eyebrow">Part ${p.n} — ${p.title}</p>
    <h1 class="ch-title">Boss battle</h1>
    <p>${qs.length} questions sampled from the whole part${hist.length ? `, including ${hist.length} history card${hist.length > 1 ? 's' : ''} you have earned` : ''}. 25 minutes on the clock (it won’t stop you — it’s telling you the truth about interview pace). Pass at 80%.${best !== undefined ? ` Best so far: <b>${best}%</b>.` : ''}</p>
    <p><button class="btn" id="start">Enter the arena</button></p>
    <div class="timer" id="timer" hidden></div><div class="q-zone"></div></div>`;
  const zone = VIEW.querySelector('.q-zone');
  $('#start').onclick = () => {
    $('#start').remove();
    const t0 = Date.now(); const timerEl = $('#timer'); timerEl.hidden = false;
    const tick = setInterval(() => {
      const left = 25 * 60 - Math.floor((Date.now() - t0) / 1000);
      timerEl.textContent = `⏱ ${left >= 0 ? Math.floor(left / 60) + ':' + String(left % 60).padStart(2, '0') : 'over time — keep going'}`;
      if (left < 0) timerEl.style.color = 'var(--bad)';
    }, 1000);
    let answered = 0, right = 0;
    qs.forEach((q, i) => {
      const cb = ok => {
        answered++; if (ok) right++;
        gradeItem(q.id, ok);
        if (answered === qs.length) {
          clearInterval(tick);
          const pct = Math.round(100 * right / qs.length);
          const rec = S.boss[part] = S.boss[part] || {};
          const firstPass = pct >= 80 && !rec.passed;
          rec.best = Math.max(rec.best || 0, pct); if (pct >= 80) rec.passed = true; save();
          const sum = document.createElement('div');
          sum.className = 'q-summary' + (pct >= 80 ? ' pass' : '');
          sum.innerHTML = pct >= 80 ? `<b>${pct}%</b> — boss down. <span class="stamp big">Part ${p.n} cleared</span>` : `<b>${pct}%</b> — the boss wins this round. Check the review queue and come back.`;
          zone.appendChild(sum);
          if (firstPass) addXP(200, `Part ${p.n} boss`);
          sum.scrollIntoView({ behavior: 'smooth' });
        }
      };
      zone.appendChild(q.kind === 'card'
        ? renderCard(q, cb)
        : renderQuizItem(q, cb, `Q${i + 1}/${qs.length}`));
    });
  };
}

/* ---------- router + boot ---------- */
function route() {
  const h = location.hash || '#home';
  // the one door into the gym: visit #gym to turn it on for this browser, again
  // to turn it off. Nothing is cleared either way.
  if (h === '#gym') {
    S.gym = !S.gym; save();
    toast(S.gym ? 'Gym mode on — streak, xp and reviews are back' : 'Gym mode off — reading only');
    location.replace('#home');
    renderChrome();
    return;
  }
  $('#sidebar').classList.remove('open'); $('#scrim').hidden = true;
  clearRail(); // renderChapter puts it back; every other view runs full width
  if (h.startsWith('#ch/')) renderChapter(h.slice(4));
  else if (!GYM() && (h === '#review' || h.startsWith('#boss/'))) { location.replace('#home'); return; }
  else if (h === '#review') renderReview();
  else if (h === '#cards') renderCollection();
  else if (h === '#timeline') renderTimeline();
  else if (h.startsWith('#boss/')) renderBoss(h.slice(6));
  else renderHome();
  renderSidebar();
}
window.addEventListener('hashchange', route);

const THEMES = ['light', 'dark', 'manim', 'phosphor'];
const THEME_GLYPH = { light: '◐', dark: '◑', manim: 'π', phosphor: '◒' };
const THEME_NAME = { light: 'Paper', dark: 'Blueprint', manim: 'Manim', phosphor: 'Phosphor' };
function applyTheme(t) {
  document.documentElement.dataset.theme = t;
  const b = $('#theme-toggle');
  b.querySelector('.ib-g').textContent = THEME_GLYPH[t];
  b.querySelector('.ib-n').textContent = THEME_NAME[t].toLowerCase();
  b.setAttribute('aria-label', `Theme: ${THEME_NAME[t]}. Switch theme`);
}
applyTheme(document.documentElement.dataset.theme);
$('#theme-toggle').addEventListener('click', () => {
  const i = THEMES.indexOf(document.documentElement.dataset.theme);
  const next = THEMES[(i + 1) % THEMES.length];
  applyTheme(next);
  S.theme = next; save();
});
/* ---------- text size ----------
   Three steps, cycling. The multiplier lands on the root element, so prose,
   headings and chrome scale together. Saved next to the theme. */
const FS = [
  { scale: 1,    name: 'Normal' },
  { scale: 1.15, name: 'Large' },
  { scale: 1.3,  name: 'Larger' },
];
function applyFontSize(i) {
  const step = FS[i] || FS[0];
  document.documentElement.style.setProperty('--fs', step.scale);
  const b = $('#text-size');
  b.dataset.level = i;
  b.querySelector('.ib-n').textContent = step.name.toLowerCase();
  b.setAttribute('aria-label', `Text size: ${step.name}, level ${i + 1} of ${FS.length}. Change text size`);
  b.title = `Text size: ${step.name.toLowerCase()}`;
}
applyFontSize(S.fontSize || 0);
$('#text-size').addEventListener('click', () => {
  S.fontSize = ((S.fontSize || 0) + 1) % FS.length;
  save();
  applyFontSize(S.fontSize);
  toast(`text size · ${FS[S.fontSize].name.toLowerCase()}`);
});

$('#nav-toggle').addEventListener('click', () => {
  const sb = $('#sidebar');
  sb.classList.toggle('open');
  $('#scrim').hidden = !sb.classList.contains('open');
});
$('#scrim').addEventListener('click', () => { $('#sidebar').classList.remove('open'); $('#scrim').hidden = true; });

/* The skip link moves focus itself instead of letting the browser follow
   href="#view". The router owns the hash, and "#view" matches no route, so
   navigating to it would fall through to the home page — skipping the sidebar
   by leaving the chapter entirely. #view already carries tabindex="-1". */
document.querySelector('.skip-link').addEventListener('click', e => {
  e.preventDefault();
  VIEW.focus();
  VIEW.scrollIntoView({ block: 'start' });
});

renderChrome();
route();
