# HLD Gym — Design Spec
Date: 2026-08-13 · Status: approved by user (chat) · Owners: two engineers, 3 YOE, targeting senior loops (Meta E5 / Google L5 / Anthropic / Palantir)

## What this is
A single self-contained HTML file (`dist/index.html`): an interactive, gamified system-design textbook in the spirit of e-maxx/cp-algorithms, written to the senior interview bar. Works offline from `file://`, desktop + mobile, all progress in localStorage (each reader keeps their own copy; solo play — no duo mechanics).

## Non-negotiable user requirements
1. Two color themes with toggle.
2. Inviting font + design; engaging, "can't put it down".
3. Quiz: selecting an answer instantly shows right/wrong AND explains the answer.
4. Simple language everywhere — experienced teacher/friend voice, no hard words, every term explained on first use.
5. Simple analogies for concepts.
6. Real-world company case studies ("war stories") in detail for most concepts — how the company hit the problem, what they did.
7. Very comprehensive and detailed; senior (E5/L5) depth.

## Research grounding (see chat research sweeps 1 & 2)
- Senior bar: candidate drives, 2–3 proactive deep dives, commit-with-justification (option-listing = downlevel), find the crux early, ops maturity (monitoring/SLO/rollout/rollback), "what breaks at 10x" unprompted, quantified estimates that drive decisions.
- Company formats: Meta System Design vs Product Architecture; Google L5 vague prompts + NALSD math; Palantir Decomp; Anthropic infra/LLM-serving flavor (KV cache, continuous batching, token rate limiting).
- Learning science: retrieval practice + spaced repetition (top-2 evidence), streaks with freezes, XP as informational mastery feedback, boss battle = milestone exam skin, Feynman self-explanation (g≈0.66), ≥8-week program.

## Content structure (~51 chapters)
- **Part 0 — The meta-game (2):** p0c01 interview framework + senior grading rubric; p0c02 company playbooks (Meta SD vs PA, Google L5/NALSD, Palantir Decomp, Anthropic).
- **Part 1 — Foundations (14):** p1c01 networking/web basics; p1c02 API design; p1c03 data modeling + SQL + indexing; p1c04 back-of-envelope estimation; p1c05 scaling + load balancing; p1c06 caching; p1c07 CDN + blob storage; p1c08 replication; p1c09 sharding + consistent hashing; p1c10 consistency + CAP/PACELC + quorums; p1c11 message queues; p1c12 rate limiting + API gateway; p1c13 NoSQL landscape + picking a DB; p1c14 unique IDs, search indexes, distributed locks intro.
- **Part 2 — Senior depth (11):** p2c01 distributed transactions (2PC/saga/outbox); p2c02 idempotency + exactly-once + ledgers; p2c03 consensus as primitive + leader election + fencing tokens; p2c04 CRDTs vs OT; p2c05 multi-region + cell-based; p2c06 hot partitions/celebrity; p2c07 backpressure + load shedding + circuit breakers; p2c08 observability + SLOs + error budgets; p2c09 stream processing (watermarks, lambda/kappa, exactly-once sinks); p2c10 probabilistic structures (Bloom/HLL/count-min) + gossip/SWIM; p2c11 zero-downtime migrations.
- **Part 3 — Problem gauntlet (24, easy→brutal, all senior bar):** p3c01 URL shortener; p3c02 typeahead; p3c03 notification system; p3c04 chat (WhatsApp); p3c05 news feed at Meta scale; p3c06 Uber ride matching; p3c07 Dropbox; p3c08 Ticketmaster; p3c09 web crawler; p3c10 global rate limiter; p3c11 distributed job scheduler; p3c12 top-K/trending; p3c13 ad click aggregation; p3c14 payment system; p3c15 Google Docs (OT/CRDT); p3c16 build a distributed cache; p3c17 build Kafka; p3c18 metrics/monitoring (Datadog); p3c19 search + inverted index; p3c20 S3-like object store; p3c21 YouTube/Netflix; p3c22 stock exchange; p3c23 LLM inference serving; p3c24 vector search/RAG.
- Problem-chapter skeleton: requirements → estimation → API → high-level design → 2–3 deep dives (the CRUX) → failure modes + ops → "what the interviewer probes next" → trade-off table.

## Visual design ("Paper & Blueprint")
- Light theme **Paper**: graph-paper white `#F7F9FB` (faint grid), ink `#1B2A41`, accent blueprint blue `#2F6DE0`, correct `#1F9D63`, wrong `#D64545`, warm highlight `#B97A24`.
- Dark theme **Blueprint**: ground `#0E1C2E`, panel `#152A44`, line/text `#D9E4F1`, accent `#6EA8FF`, same status hues re-stepped for dark.
- Type: Literata (variable, serif — long-form body + display weights) + IBM Plex Mono (labels, numbers, code, eyebrows). Embedded as woff2 data URIs; fallback Charter/Georgia + system mono.
- Signature: engineering-stamp system — rotated stamp-look badges: red **CRUX** on each problem's hardest part, green **MASTERED** across cleared chapters in TOC/dashboard.
- Boxes: `.analogy` (Analogy), `.story` (War story — {Company}), `.lens` (At the whiteboard), `.crux` (The crux), `.feynman` (Explain it yourself). Diagrams: inline SVG using CSS variables so both themes work.
- Dashboard follows dataviz rules: heatmap = single-hue blue sequential; mastery states = status colors + stamp icon (never color alone); XP/streak = stat tiles.

## Engine (vanilla JS, no deps)
- Hash router: `#home` (dashboard + continue), `#ch/<id>`, `#review`, `#boss/<part>`. Sidebar TOC (collapses to hamburger on mobile).
- Theme toggle: localStorage override, default `prefers-color-scheme`.
- Quiz engine: renders from embedded JSON; click option → instant correct/incorrect styling + that option's `why` + the correct answer's `why`; L1/L2/L3 per chapter; best scores stored; chapter mastered at L3 ≥ 80% (earns MASTERED stamp).
- Spaced review (Leitner): boxes 1–5, intervals 1/3/7/14/30 days; wrong → box 1; `#review` serves due items interleaved across chapters; home shows due count.
- XP: L1 +10, L2 +15, L3 +20 (first-try correct), review +5, boss pass +200. Ranks: Intern 0 → Junior 500 → Mid-level 1500 → Senior 3500 → Staff 7000 → Distinguished 12000.
- Streak: any scored activity counts for the day; 2 auto freezes/week.
- Boss exam per part: 20 questions sampled (L2/L3-weighted) across the part, 25 min soft timer, pass ≥ 80%. Soft gate only — nothing locked.
- Progress export/import: JSON blob copy-paste (move progress between devices).
- State: one localStorage key `hldgym_v1`.

## Build pipeline
- `src/template.html` + `src/style.css` + `src/app.js` + `src/fonts/*.woff2` + `src/toc.json` + `src/chapters/<id>.html` + `src/chapters/<id>.quiz.json` → `python3 build.py` → `dist/index.html`.
- Chapters not yet written (`status:"soon"` in toc.json) render as "coming soon" — file stays shippable at every stage.
- build.py validates: quiz schema (every option has `why`, exactly-one/≥1 correct, level counts), no external http(s) refs, unknown component classes, size report. Build fails loudly on violations.
- Content authored by parallel agents against STYLE_GUIDE.md (voice + component contract + quiz schema), verified by fact/voice-check agents before merge.

## Out of scope
Duo/social features, servers/accounts, LLD/coding-round prep, search-in-book, PDF export.
