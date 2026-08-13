'use strict';
/* ===== HLD Gym engine ===== */

const TOC = JSON.parse(document.getElementById('toc-data').textContent);
const QUIZ = JSON.parse(document.getElementById('quiz-data').textContent); // {chapterId: [items]}

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
    theme: null, xp: 0,
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

const today = () => new Date().toISOString().slice(0, 10);
const dayNum = iso => Math.floor(Date.parse(iso) / DAY);

/* ---------- toc helpers ---------- */
const CHAPTERS = [];
TOC.parts.forEach(p => p.chapters.forEach((c, i) => CHAPTERS.push({ ...c, part: p.n, idx: i + 1, partTitle: p.title })));
const chById = id => CHAPTERS.find(c => c.id === id);
const isReady = id => !!document.querySelector(`template[data-ch="${id}"]`);
const chQuiz = id => QUIZ[id] || [];
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
  S.xp += n; save();
  toast(`+${n} XP${label ? ' · ' + label : ''}`);
  renderChrome();
}
function touchStreak() {
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
  const it = S.items[itemId] || { box: 0, due: null, right: 0, wrong: 0 };
  if (correct) { it.right++; it.box = Math.min(5, (it.box || 0) + 1); }
  else { it.wrong++; it.box = 1; }
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
  $('#streak-pill').innerHTML = `🔥 <b>${S.streak}</b>d · ${S.xp} XP`;
  renderSidebar();
}
function renderSidebar() {
  const cur = location.hash.replace('#ch/', '');
  let html = '';
  for (const p of TOC.parts) {
    const done = p.chapters.filter(c => mastered(c.id)).length;
    html += `<div class="side-part"><div class="side-part-title">Part ${p.n} — ${p.title}<span class="prog">${done}/${p.chapters.length}</span></div>`;
    p.chapters.forEach((c, i) => {
      const ready = isReady(c.id);
      const cls = ['side-ch', ready ? '' : 'soon', cur === c.id ? 'active' : ''].join(' ');
      const mark = mastered(c.id) ? '<span class="m done">✔</span>' : '';
      html += `<a class="${cls}" href="#ch/${c.id}"><span class="n">${p.n}.${i + 1}</span><span>${c.title}</span>${mark}</a>`;
    });
    html += `</div>`;
  }
  $('#sidebar').innerHTML = html;
}

/* ---------- quiz rendering ---------- */
function renderQuizItem(q, onAnswer, num) {
  const wrap = document.createElement('div');
  wrap.className = 'q-item';
  wrap.innerHTML = `<div class="q-num">${num || ''}${q.tag ? ' · ' + q.tag : ''} · L${q.level}</div>
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

/* ---------- views ---------- */
const VIEW = $('#view');

function renderHome() {
  const due = dueItems().length;
  const done = CHAPTERS.filter(c => mastered(c.id)).length;
  const readyCount = CHAPTERS.filter(c => isReady(c.id)).length;
  const r = rank();
  const cont = S.lastCh && isReady(S.lastCh) ? chById(S.lastCh) : CHAPTERS.find(c => isReady(c.id) && !mastered(c.id));
  let html = `<div class="content">
    <p class="eyebrow">Training floor</p>
    <h1 class="ch-title">Welcome back.</h1>
    <div class="tiles">
      <div class="tile accent"><div class="tile-label">Rank</div><div class="tile-value">${r.name}</div>
        <div class="tile-label">${r.next ? (r.next[1] - S.xp) + ' xp to ' + r.next[0] : 'max rank'}</div></div>
      <div class="tile"><div class="tile-label">XP</div><div class="tile-value">${S.xp}</div></div>
      <div class="tile warm"><div class="tile-label">Streak</div><div class="tile-value">${S.streak}<small> days</small></div></div>
      <div class="tile"><div class="tile-label">Mastered</div><div class="tile-value">${done}<small> / ${CHAPTERS.length}</small></div></div>
    </div>
    <p>
      ${cont ? `<a class="btn" href="#ch/${cont.id}">Continue: ${cont.title}</a>` : ''}
      <a class="btn ghost" href="#review">Review due · ${due}</a>
    </p>
    <h2 style="margin-top:2em">Review activity</h2>
    <div class="heat" aria-label="review activity heatmap">${heatCells()}</div>
    <div class="heat-cap">last 15 weeks · darker = more answers</div>`;

  for (const p of TOC.parts) {
    const boss = S.boss[p.n];
    const partReady = p.chapters.some(c => isReady(c.id));
    html += `<div class="part-block">
      <div class="part-head"><h2>Part ${p.n} — ${p.title}</h2><span class="tagline">${p.tagline}</span>
      ${partReady ? `<a class="btn ghost bossbtn" href="#boss/${p.n}">${boss?.passed ? '👑 Boss cleared' : 'Boss battle'}</a>` : ''}</div>
      <div class="ch-grid">`;
    p.chapters.forEach((c, i) => {
      const ready = isReady(c.id);
      const st = mastered(c.id) ? '<span class="st done">✔</span>'
        : (S.levels[c.id] ? '<span class="st part">◐</span>' : '');
      html += `<a class="ch-cell ${ready ? '' : 'soon'}" href="#ch/${c.id}"><span class="n">${p.n}.${i + 1}</span><span>${c.title}${ready ? '' : ' <small>(soon)</small>'}</span>${st}</a>`;
    });
    html += `</div></div>`;
  }
  html += `<div class="part-block"><h2>Backup</h2>
    <p style="font-size:.9rem;color:var(--ink-2)">Progress lives in this browser. Copy the blob to move it to another device.</p>
    <p><button class="btn ghost" id="exp">Export progress</button> <button class="btn ghost" id="imp">Import</button></p>
    <textarea id="expbox" style="width:100%;min-height:70px;display:none;font-size:.75rem"></textarea></div></div>`;
  VIEW.innerHTML = html;
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

function renderChapter(id) {
  const c = chById(id);
  const tpl = document.querySelector(`template[data-ch="${id}"]`);
  if (!c || !tpl) { VIEW.innerHTML = `<div class="content"><h1 class="ch-title">Coming soon</h1><p>This chapter isn't written yet.</p></div>`; return; }
  S.lastCh = id; save();

  const words = tpl.content.textContent.split(/\s+/).length;
  VIEW.innerHTML = `<div class="content">
    <p class="eyebrow">Part ${c.part} — ${c.partTitle}</p>
    <h1 class="ch-title">${c.title} ${mastered(id) ? '<span class="stamp">Mastered</span>' : ''}</h1>
    <div class="ch-meta">${c.part}.${c.idx} · ~${Math.max(1, Math.round(words / 220))} min read · ${chQuiz(id).length} quiz questions</div>
    <div class="ch-body"></div>
    <div class="quiz-wrap"><h2>Quiz</h2><p style="font-size:.9rem;color:var(--ink-2)">Three levels. Pass Level 3 with 80% to earn the stamp. Answers go into your review queue.</p>
    <div class="q-level-tabs"></div><div class="q-zone"></div></div>
    <div class="ch-nav"></div>
  </div>`;
  VIEW.querySelector('.ch-body').appendChild(tpl.content.cloneNode(true));

  // feynman blocks
  VIEW.querySelectorAll('.feynman').forEach(f => {
    const key = f.dataset.key;
    const ta = document.createElement('textarea');
    ta.placeholder = 'Write it in your own words. Out loud is even better.';
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
      const best = (S.levels[id] = S.levels[id] || {});
      const prev = best[lv] || 0;
      best[lv] = Math.max(prev, pct); save();
      const pass = lv === 3 && pct >= 80;
      const sum = document.createElement('div');
      sum.className = 'q-summary' + (pct >= 80 ? ' pass' : '');
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
    const best = (S.levels[id] || {})[lv];
    b.innerHTML = names[lv] + (best !== undefined ? ` <span class="score">${best}%</span>` : '');
    b.onclick = () => openLevel(lv);
    tabs.appendChild(b);
  });
  openLevel(1);

  // prev/next
  const i = CHAPTERS.indexOf(chById(id));
  const prev = CHAPTERS.slice(0, i).reverse().find(c2 => isReady(c2.id));
  const next = CHAPTERS.slice(i + 1).find(c2 => isReady(c2.id));
  VIEW.querySelector('.ch-nav').innerHTML =
    (prev ? `<a class="btn ghost" href="#ch/${prev.id}">← ${prev.title}</a>` : '<span></span>') +
    (next ? `<a class="btn" href="#ch/${next.id}">${next.title} →</a>` : '');
  window.scrollTo(0, 0);
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
    zone.appendChild(renderQuizItem(q, ok => {
      gradeItem(q.id, ok);
      if (ok) { right++; addXP(5); }
      i++;
      setTimeout(nextItem, ok ? 900 : 2600);
    }));
  }
  nextItem();
}

function renderBoss(part) {
  const p = TOC.parts.find(x => x.n === +part);
  if (!p) { location.hash = '#home'; return; }
  const pool = p.chapters.filter(c => isReady(c.id)).flatMap(c => chQuiz(c.id));
  const hard = pool.filter(q => q.level >= 2);
  const qs = (hard.length >= 20 ? hard : pool).sort(() => Math.random() - 0.5).slice(0, 20);
  const best = S.boss[part]?.best;
  VIEW.innerHTML = `<div class="content"><p class="eyebrow">Part ${p.n} — ${p.title}</p>
    <h1 class="ch-title">Boss battle</h1>
    <p>${qs.length} questions sampled from the whole part. 25 minutes on the clock (it won’t stop you — it’s telling you the truth about interview pace). Pass at 80%.${best !== undefined ? ` Best so far: <b>${best}%</b>.` : ''}</p>
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
    qs.forEach((q, i) => zone.appendChild(renderQuizItem(q, ok => {
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
    }, `Q${i + 1}/${qs.length}`)));
  };
}

/* ---------- router + boot ---------- */
function route() {
  const h = location.hash || '#home';
  $('#sidebar').classList.remove('open'); $('#scrim').hidden = true;
  if (h.startsWith('#ch/')) renderChapter(h.slice(4));
  else if (h === '#review') renderReview();
  else if (h.startsWith('#boss/')) renderBoss(h.slice(6));
  else renderHome();
  renderSidebar();
}
window.addEventListener('hashchange', route);

$('#theme-toggle').addEventListener('click', () => {
  const cur = document.documentElement.dataset.theme;
  const next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  S.theme = next; save();
});
$('#nav-toggle').addEventListener('click', () => {
  const sb = $('#sidebar');
  sb.classList.toggle('open');
  $('#scrim').hidden = !sb.classList.contains('open');
});
$('#scrim').addEventListener('click', () => { $('#sidebar').classList.remove('open'); $('#scrim').hidden = true; });

renderChrome();
route();
