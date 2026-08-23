# Roadmap — the researched reality, the positioning, and the plan

Rewritten 2026-08-23. This replaces the 2026-08-23 morning version wholesale.
That version was written from one conversation; this one is written from three
multi-agent research passes over primary sources (HN Algolia comment archive,
Reddit threads, Blind, live pricing pages, SEC filings, ~500 web fetches,
2024–2026 recency window) plus a three-lens adversarial judge panel. Every
load-bearing claim below carries its source. Quotes are verbatim.

The old roadmap's frame — "will this sell given free websites and LLMs?" —
was the right question with a half-researched answer. The full answer changes
the positioning, the distribution plan, and what gets built first. It does
not change the product's thesis. It sharpens it.

---

## Part 1 — the market reality, August 2026

### The layer map: what free AI killed, and what it verifiably did not

The product is not one thing. It is layers, and the market has already priced
each layer separately. Getting this map wrong is the difference between
selling a commodity and selling the one thing buyers still pay for.

**Layer 1 — explanation and content: fully commoditized. Worth $0 as a paid
good.** Chegg's stock fell 99% to ChatGPT and HN cites it as settled fact
(news.ycombinator.com/item?id=48370862). NotebookLM ships quizzes and
flashcards natively and people pass real exams with it. "Knowledge gate
keeping is officially dead" took 90 upvotes on r/leetcode (2025-08-29).
Consequence: **the free book is correctly free.** It competes with NotebookLM
and wins only as distribution, never as revenue.

**Layer 2 — the voice interviewer, as a feature: fully commoditized.** An
895-upvote r/interviews offer story ran on free ChatGPT voice alone,
including a simulated three-persona panel. interviewing.io gives its AI
interviewer away free. A census of Show HN 2024–2026 found ~30 AI
mock-interviewer launches; top score 9 points, median 2, most with zero
comments. A Feb 2026 solo voice-interviewer launch nearly identical to our
feature set drew exactly one reply: "Can tell me your tech stack?"
(news.ycombinator.com/item?id=47176043). Consequence: **"an AI interviewer
probes you" may never again be the pitch.** It is delivery, not product.

**Layer 3 — raw LLM grading: commoditized as folk practice.** 2026
offer-winners describe screenshotting Excalidraw diagrams into ChatGPT "to
assess me" (r/cscareerquestionsOCE, 2026-05-21). Anything that is a prompt
is replicable by a prompt: when OpenAI killed Study Mode in April 2026, HN's
epitaph was "this mode was just a system prompt"
(news.ycombinator.com/item?id=47739305).

**Layer 4 — honest graded judgment against verified ground truth: NOT
commoditized, and buyers name it as the thing they pay for.** The evidence
is consistent across every source:

- The documented failure of DIY-AI study is sycophancy-inflated confidence.
  A Study Mode user got one pushback in 90 minutes and bombed his final. An
  instructor reports 100% AI-assisted homework alongside C-minus exams.
  "Self-practice out loud is stupid because it can be an echo chamber —
  there's no pushback" (r/InterviewStories, 2026-08-16). DIYers hand-engineer
  anti-flattery guardrail prompts to get honesty an LLM won't volunteer
  (r/leetcode, 2025-05-15).
- People who pass high-stakes evaluations in 2025–26 (CISM, PMP, FAANG
  loops) pair free AI-as-explainer with a **paid graded question bank**.
  "It may be worth buying leetcode premium... I cannot overstate how
  important this is" — from the same person who used ChatGPT daily.
- The category's pure painkiller is paid judgment: interviewing.io charges
  $179–339 per single mock; "you pay for the feedback"; "calibrated
  signal... worth it once you're close to ready"; "I paid for a mock
  interview from a FAANG engineer... he told me he would fail me and gave me
  every reason. It was eye opening" (news.ycombinator.com/item?id=43151623).
- Buyers of Hello Interview premium (the closest incumbent) name LLM-graded
  practice against curated answer keys as the difference-maker: "Yeah AI
  feedback, but it was really good. It sounds gimmicky but it made a huge
  difference for me" (r/leetcode, 2025-01-15). Graded practice called "10x
  more efficient than reading or watching videos."

**Layer 5 — the multi-session spine: NOT commoditized, and users ask for it
by name.** Free chat verifiably fails at holding a curriculum: "It typically
started off like a structured lesson but as I chatted with it, it would
forget the syllabus... we never completed the thing we set out to learn"
(HN, 2026-04-12). r/notebooklm's most consistent complaint is that the tool
is "built for understanding, not retention," with users literally requesting
weak/solid tracking plus spaced review tied to an exam date. That request is
this product's spaced-return feature, described by strangers, unbuilt by
anyone free.

The sharpest positioning sentence found in any primary source, HN April
2026, unprompted:

> "The problem with most AI study modes is that they optimize for knowledge
> transfer. The harder problem is knowledge use — being able to actually
> apply something under pressure."

That is the product in one line. The market wrote our copy.

### The demand side: the pain is real, paid, and deadline-shaped

- FAANG has not moved away from these rounds: interviewing.io survey (Oct
  2025), 0 of 52 FAANG respondents moving off algorithmic/design questions;
  Big Tech hiring volume up ~40% YoY (Pragmatic Engineer, 2025).
- The category monetizes at every rung: Alex Xu ~1M books; NeetCode ~$10M/yr
  solo; Hello Interview bootstrapped to 100k+ engineers at ~$47/mo
  equivalent; Interview Kickstart $2,400–12,000 per program; Formation
  $5,000 up front plus success fee.
- Deadline pricing proves the painkiller: UWorld charges ~6x more per day
  for its 30-day plan than its annual. Hello Interview's one-month pass
  costs 60–80% of its full year, and does not auto-renew — the incumbent
  already sells deadline-shaped passes, not subscriptions. **$19/30 days is
  2–10x below every working comparable.** Underpriced is the current risk,
  not overpriced.
- Mid-2026 demand is visible and desperate: r/leetcode threads of people
  begging for Hello Interview referral codes and organizing account-splits.

### The three hard warnings the research surfaced

**1. The real competitor is Hello Interview, not ChatGPT.** They killed
their human-mock marketplace in May 2026 and went all-in on AI-graded guided
practice — the market leader converged on this product's shape, which
validates the shape and occupies the shelf. Their known weakness, from their
own buyers: the grader is "very stubborn," rejecting valid alternative
designs. Our transcript-quoting failure map and hand-verified rubrics are
the credible wedge against that specific, documented complaint. Note their
Guided Practice contains **no spaced repetition and no recall-from-memory
mechanic** (verified on their own pages): our LOCK loop is differentiated —
and therefore also unvalidated by any incumbent.

**2. Conversion, not substitution, is the binding risk.** The research found
**zero instances, ever, of an audience-less solo dev converting cold traffic
on paid interview prep.** Every observed winner had a pre-built audience
(Xu: LinkedIn; NeetCode: YouTube) or a credential (Hello Interview: ex-Meta
interviewers) before charging. Cold Show HN is a graveyard. Astroturf
suspicion poisons every Reddit review thread. A competing founder's own
words: "The hardest part has not been the model. It has been reducing the
trust gap" (r/SaaS, 2026-06-30). HN's first question to a prep launch is
whether laid-off buyers have disposable income at all.

**3. Two framings are banned by the audience itself.** "Accountability"
("no reason for paid bootcamps to exist other than the illusion of added
accountability" — 92 upvotes, r/leetcode) and "memorization" (community
folk theory: memorization doesn't transfer; only synthesis under live
pressure counts). The mechanic can BE forced recall; it must be SOLD as
graded synthesis under interviewer pressure. Same loop, opposite reception.
This retires the old roadmap's instinct to lead with the LOCK mechanic and
the spaced-return promise as headline features.

### What this retires from the previous vision

- **"An AI interviewer probes you" as a selling point.** Table stakes;
  actively harmful as a headline (reads as ChatGPT wrapper; the documented
  HN reflex is "I already pay for Claude — why would I pay more for this?").
- **The one-good-HN-post distribution plan.** Even Hello Interview's own
  flagship free guide flopped on HN, twice, at 1–2 points. Winners built on
  LinkedIn, YouTube, Reddit/Blind word of mouth. HN is where this audience's
  builders are, not where its buyers are.
- **The regex-graded rep as the public face of the product.** A grader that
  scores 6/6 on a reversed read path manufactures the exact illusion of
  competence the product exists to destroy. It was honest scaffolding for a
  presell; it is now the weakest thing a stranger can find, positioned where
  every stranger looks. The diagnostic round (real LLM grading, failure map
  quoting the candidate's own transcript, built 2026-08-22/23) replaces it.
- **Gamification/surface as a value axis.** Four themes shipped to zero
  users. Duolingo's lesson from the research: gamified discipline monetizes
  only on enormous free traffic. Not our model. (Already a non-goal; now
  it is an evidenced one.)

---

## Part 2 — what the product is, restated in the market's own language

**For:** a senior engineer with a system-design onsite dated weeks away.
No date, no buyer — every research lens independently flipped the
no-deadline segment to vitamin.

**The pain:** reading feels like knowing. You cannot see yourself the way
the interviewer will, and the free tools you practice with are structurally
incapable of telling you you're wrong — sycophancy is load-bearing in their
product design. The result, documented in public repeatedly: candidates who
studied everything, felt ready, and got taken apart.

**The product:** a graded diagnostic and a 30-day sprint that force you to
produce designs under interviewer pressure and grade them against
hand-verified ground truth, then show you a failure map in your own words —
before the onsite does it for real.

**The moat, ranked by durability (from the frontier-lab risk analysis):**
1. **Hand-verified ground truth** (197 diagrams, rubrics, war stories,
   kernels) — the layer LLMs improvise per-session and get wrong; the layer
   buyers name as un-DIY-able.
2. **The grading pipeline** — rubric-anchored, transcript-quoting,
   adversarially checked. Everything that is "just a prompt" is commodity;
   this is a pipeline, not a prompt.
3. **The multi-session spine** — schedule, state, spaced return, exam-date
   compression. Free chat forgets the syllabus; this doesn't.
4. **The calibration record** — predicted vs actual over 30 days. A chat
   has no memory of your miscalibration. Nobody else has this. It converts
   the sales argument (Roediger & Karpicke's overconfident restudiers) into
   a personal instrument.

The voice loop and the teaching diagrams are delivery. Excellent, necessary,
not the moat, never the headline.

**Price:** $19 stands for the presell (it undercuts the wrapper-skepticism
objection and the goal is 3 payments, not revenue). The evidence says the
sustainable price is 2–5x higher, deadline-shaped, non-renewing — the
Hello Interview / UWorld pass model, not a subscription.

---

## Part 3 — the plan to 9 September

Goal unchanged: **3 paying strangers.** Deadline math unchanged: at 0.5–2%
cold presell conversion, a few hundred targeted visitors. What changed is
where they come from and what they see when they arrive.

**1. The diagnostic round becomes the front door.** (Build item, first.)
A stranger sits the ~6-minute interviewer-only round, gets graded for real,
sees the failure map quoting their own words, then sees one $19 CTA. The
pain goes from claimed to felt. The regex rep demo comes off the front page.
Stop rule, from the buyer lens of the judge panel: do not build anything
else for the sprint until someone who felt their own failure map still
won't pay.

**2. The copy repositions.** Headline space sells graded judgment under
pressure and verified ground truth. A "why not just ChatGPT?" section
answers the documented first objection head-on: ChatGPT is a superb
explainer and a structurally dishonest grader; here is the same wrong answer
graded by both, side by side. Banned words stay banned. Honesty rules stay:
every claim checkable, every limitation disclosed where the belief forms.

**3. Distribution goes where the buyers are, with a name on it.** The free
book and the free diagnostic posted to r/ExperiencedDevs, r/leetcode,
LinkedIn — as genuine value, author identified, no growth-hack tricks
(astroturf suspicion is the ambient failure mode; being visibly a person is
the counter). The shareable unit is the failure map: "I got taken apart in
six minutes" travels. Not Show HN.

**4. Trust decisions get made and stated** (unchanged from the old roadmap,
still open, still costing sales while undecided): refund mechanics after
1 September; access mechanism after payment; days gated or open. Decide and
say, in that order.

---

## Part 4 — learner-value build order, evidence-annotated

The organizing principle survives the research intact and comes out
stronger: **the product's thesis is calibration — the gap between
feeling-of-knowing and actual knowing. Every hour makes that promise true,
not the surface bigger.** What changed is the confidence level: this is no
longer a design instinct, it is the one layer of the market free AI has
verifiably failed to eat.

1. **Grader first. Still first. Everything routes through trust in the
   score.** The diagnostic round's LLM grading (quote-verified against the
   transcript) is built; the sprint's rep grading inherits it. The regex
   rubric stays as fallback only. The research adds urgency: incumbent
   graders are publicly criticized as "very stubborn" — grading that shows
   its evidence (quotes, rubric line, why) is the wedge.
2. **Calibration meter.** Predict your score before the reveal; watch the
   overconfidence curve shrink over 30 days. Novel (verified: no incumbent
   has it), cheap, and it is the thesis made visible. The restudiers in
   Roediger & Karpicke predicted they would win and lost; the product shows
   each user their own version of that graph.
3. **Output modes matching the interview** (speak while drawing, defend
   under interruption). Justified by transfer-appropriate processing, never
   input preference (standing rule). The voice loop exists; point it at reps.
4. **Failure-injection reps.** The kernel rule already demands "a named
   place it breaks." Senior loops are decided on what breaks at 10x. The 125
   war stories are pre-written failure scenarios.
5. **Spaced return as a real scheduler + exam-date mode.** FSRS over the
   197 reps, seeded by grade and calibration error, compressed toward the
   buyer's onsite date. The r/notebooklm users asked for exactly this.
6. **Mock gauntlet** (45-minute full mock, graded, unlimited retries) — the
   interviewing.io $179 product inside a $19-tier one. End state.
7. **Narrow diagrams for the book** (136 of 197 unreadable on phones; the
   book is the funnel; grind work, pure value).
8. **Close the loop from real interviews** (post-onsite debrief → tune
   probes and weighting). Ten users in, the product trains on the real
   interview distribution.

## Non-goals, re-evidenced

More themes. Gamification expansion. Social features. Reel polish before
reels are posted. "AI interviewer" as identity. HN launches. Subscriptions.
Anything whose value is explanation (that layer is free, everywhere,
forever).

---

## Part 5 — the engine: making the machine subject-agnostic

Researched 2026-08-23, second fleet: five sweeps (learning science, vertical
teardowns, subject selection, engine spec, moat durability) plus an
adversarial critic pass that verified case law and primary papers. The
question: if this exact machine were rebuilt for a different subject, what
transfers, what gets re-authored, and where does the machine break?

### 5.1 The science backbone, with effect sizes and honest edges

The loop is not a metaphor; each stage has a literature, and the literature
has boundary conditions that are now design requirements.

- **Retrieval beats restudy: g = 0.50** across 61 studies (Rowland 2014,
  Psych Bulletin), **g = 0.61** across 217 (Adesope 2017), holds in
  classrooms, and transfer (g = 0.53) is nearly as large as retention.
  Caveat kept on the record: published studies show g = 0.58 vs unpublished
  0.25, so some inflation exists.
- **The hardest boundary condition in the whole literature:** when initial
  retrieval success is at or below ~50% AND there is no feedback, the
  testing effect **vanishes** (g = 0.03). With feedback it is the largest
  cell of the meta-analysis (g = 0.73). **Design law: no rep exists without
  feedback, and the teach-then-lock sequence must keep first-attempt
  success above ~50%.** The grade plus failure map is not a feature on top
  of the mechanic; it is the condition under which the mechanic works
  at all.
- **The mechanic is not diagram-bound.** Verified by the critic pass:
  free-recall writing beats elaborative concept mapping even when the final
  test is itself a concept map (Karpicke & Blunt, Science 2011); the
  retrieval format is interchangeable (Blunt & Karpicke 2014); the effect
  holds for oral clinical performance at six months (Larsen 2013) and for
  procedural skill at effect size 0.93 with zero extra time (Kromann 2009).
  **The LOCK-rebuild loop transfers to essays, oral cases, procedures. The
  rebuild artifact is the per-subject skin.**
- **Transfer is fragile and congruency is worth +0.30.** Pan & Rickard
  (2018): transfer averages d = 0.40, response congruency between practice
  and final test adds d = +0.30, and bias-corrected estimates approach zero
  when no moderators are present. Larsen 2013 is the applied version:
  standardized-patient practice beat written practice on the
  standardized-patient final, only. **Output modes matching the evaluation
  (speak, draw, defend) are not nice-to-haves; they are where the transfer
  effect lives.** The standing "output mode, never input preference" rule
  is now quantitative.
- **Complexity is the honest open fight.** Van Gog & Sweller argue the
  testing effect shrinks as material complexity rises; Karpicke, Aue and
  Rawson rebut; Adesope found larger effects for complex material. Spacing
  gains do shrink with complexity (r = −.25, Donovan & Radosevich). So:
  spaced return stays, sold as scheduling honesty (exam-date compression),
  not as a magic multiplier for whole-system rebuilds.
- **Calibration is trainable but not by a score alone.** Delayed
  judgments-of-learning improve which-items-do-I-know accuracy; but showing
  predicted-vs-actual by itself often fails to fix absolute calibration,
  improvement needs structured reflection on the discrepancy across
  repeated cycles, and the worst performers' overconfidence is stickiest.
  **The calibration meter must ship with a guided one-line reflection
  ("where did the 2 points go?"), not just the graph.**

### 5.2 The machine every winner runs

The vertical teardowns (UWorld, AMBOSS, Themis, ELSA, Math Academy,
Sheppard Air, AnKing, Duolingo Max) converge on one four-part machine:

1. **A bank of verified items authored by credentialed people who passed
   the target evaluation themselves.** UWorld: licensed practicing
   physicians; its CFA launch: a 17-step per-question process, 10 hires,
   9 charterholders. AMBOSS: 150+ clinician editors, an "8-eyes"
   review principle. The credential is the marketing, not a hidden cost.
2. **A grader whose credibility is itself a published statistic.** ELSA
   sells 93.88% agreement with expert human raters. UWorld sells a
   self-assessment that correlates r ≈ 0.85–0.89 with the real exam score.
   **The grader's trustworthiness is a number on the pricing page.**
3. **Scheduled structure whose compliance visibly moves the pass rate.**
   Themis publishes, per jurisdiction, the pass rate of everyone, of its
   students, and of its students who completed 75% of the coursework
   (e.g. Virginia 85 / 89 / 99). Structure is sold with receipts.
4. **Time-boxed, stakes-priced passes.** Pass-and-leave churn is designed
   in, not fought: UWorld prices a 30-day window at ~6x the per-day annual
   rate; prices track the exam's stakes across a 75x range ($40 FAA to
   $2,995 bar), never content volume.

We already run a small version of all four. The engine work is
instrumenting them: the grader needs its agreement statistic, the schedule
needs its compliance-vs-outcome receipts, the price needs to move to
stakes-shaped passes after the presell.

### 5.3 Authoring economics and the LLM boundary

- A verified high-stakes exam item costs **$1,500–2,500** (GMAT
  psychometrician figure); freelance drafting costs $3–15. The 100x gap is
  verification. That gap is the moat, and it is why AI-generated banks
  don't displace incumbents.
- LLM drafting with expert verification is the one proven shortcut: in a
  real high-stakes exam, GPT-4o item drafting cut person-hours 71.5% with
  no loss of discrimination — but expert-flagged error rates in AI-drafted
  items range 1–60% by topic, so **100% human review is the boundary, and
  the hard, discriminating items stay human-authored** (AI drafts skew easy
  and recall-heavy).
- LLM-as-judge, current state: rubric-anchored grading reaches
  kappa ≈ 0.65–0.75 against experts; judges are **reliable without being
  valid** (test-retest >0.95 coexisting with position bias; exact-match
  agreement overstates quality by 33–41 points vs kappa). The working
  mitigation stack is exactly what the grader already half-does:
  anchored rubric levels, reasoning-before-score, order randomization,
  quote-grounding to the transcript, ensembles for high stakes.
- **Engine component most builders miss, adopted here as a requirement: a
  judge-validation harness.** Before any vertical's scores are trusted or
  marketed: ~50–100 transcripts graded by a credentialed human, judge
  agreement measured as kappa (target >0.6), re-run on every rubric or
  model change. This is also where our grader's public credibility
  statistic comes from (see 5.2.2).

### 5.4 What survives the frontier labs

One line decides shelf life: **everything that explains dies; everything
that verifies against a real outcome lives.**

- Died or dying: Chegg (revenue −39%, subscribers −31%, CEO naming Google
  AI Overviews as material); 200+ funded GPT-wrapper startups; OpenAI's
  Study Mode (killed April 2026, "it was just a system prompt");
  Duolingo's engagement-only layer (stock −75% from May 2025 peak,
  "Explain My Answer" given away free — gamification without a welded bar
  defended nothing).
- Survives: verified rubrics for evaluations with **no public corpus a lab
  can license** (avoid JEE/SAT/MCAT, where Gemini already gives away full
  verified mocks); the schedule welded to a dated bar; an owned
  distribution list (ByteByteGo's 1M-reader funnel still converts, 2026);
  and the outcome-linked data loop: UWorld's readiness prediction is a
  regression on thousands of predicted-vs-real-outcome pairs, **a dataset
  frontier labs structurally cannot collect because nobody reports their
  onsite result to ChatGPT.**
- Critic's correction, kept: the UWorld analogy flatters us. USMLE outcomes
  are standardized scores; interview outcomes are binary, private,
  self-reported, confounded by company bars. Outcome capture starts on day
  one ("did you pass? consented self-report") with realistic noise
  expectations — a moat seed, not a UWSA clone.
- Exam boards are moving toward MORE adversarial, hands-on, AI-banned
  formats (OSCP's 24-hour proctored gauntlet; proctoring fraud response).
  This grows prep demand; it does not shrink it.

**The legal wall, verified in case law by the critic pass:** verified
ground truth is a moat only when it means credentialed authors writing
ORIGINAL items against a public blueprint. The moment a product ingests
learner-recalled secure exam content it becomes NBME v. Optima (bankrupt
one month after filing) or NCBE v. PMBR (a quarter-century of litigation),
and USMLE sanctions the *learners* too. Sheppard Air's crowdsourced-recall
model is a licensing artifact of the FAA's published bank, not a
transferable pattern. **Consequence: a compliance boundary is a first-class
engine component in secure-bank verticals — and system design is quietly
the safest vertical of all, because no exam board owns interview
questions.**

### 5.5 The split: subject-blind runtime, per-subject content pack

**The runtime (build once, owns no domain facts):**
lock-rebuild player and scheduler; realtime voice probe harness; the
rubric-anchored judge with its bias-control stack; the failure map
renderer; spaced return + exam-date compression; the calibration meter
with guided reflection; the judge-validation harness (5.3); the outcome
capture pipeline (5.4); and the funnel machinery this repo already has —
the single-file textbook builder and the reel renderer are distribution
tooling any vertical reuses.

**The content pack (re-authored per subject, the only thing a new vertical
ships):** diagrams (or the subject's rebuild artifact), kernels, rubrics,
war stories, probe bank, exam-blueprint mapping, plus a named credentialed
verifier and the 50–100 human-graded validation transcripts. Scale floor
from the pattern: ~2,500–4,000 verified MCQ-equivalents for an MCQ-shaped
exam, or on the order of 150–300 deep graded reps for a rubric-graded one.
(Flagged by the critic: the rep-to-MCQ exchange rate is our inference, not
literature; treat the floor as a hypothesis the first vertical tests.)

### 5.6 The subject filter, and the ranked next verticals

A subject fits the engine only if all four hold: **(1)** a dated,
high-stakes evaluation; **(2)** constructed-response synthesis under
pressure (never MCQ recall); **(3)** an artifact worth locking and
rebuilding; **(4)** incumbents selling explanation rather than honest
grading. Plus two vetoes from 5.4: no mass public corpus a lab can license,
and no secure-bank IP regime without a compliance design.

**Ranked (evidence in the research files):**
1. **GenAI/ML system-design rounds.** No canon exists — interview content
   shifted 60%+ to RAG, evals, agent design, categories that didn't exist
   two years ago; candidates are prepping 2023 material. Same buyer, same
   diagram grammar, same funnel; the incumbent just exited human mocks.
   This is a content pack, not a new company.
2. **Staff/principal architecture loops.** Highest proven willingness to
   pay in the sweep ($179–339/session, $2,000 for three); largely a
   re-rubric of existing assets at a higher bar.
3. **Medical OSCEs (PLAB 2 class).** The realtime voice probe IS the exam
   being simulated; incumbents are seat-limited live academies. But:
   heaviest re-authoring, requires a clinical SME as verifier, and the
   secure-bank compliance wall applies. This vertical is the *test of the
   pack format*, not a near-term move.

**Fails the filter** (recorded so it isn't re-litigated): USMLE Step 1
(saturated, MCQ), IELTS/TOEFL speaking (fifteen AI scorers already, no
synthesis), CKA/CKS (killer.sh owns it), AWS SA Pro (MCQ), PM interviews
(Exponent ships rubric-graded AI mocks at $12/mo), actuarial (Coaching
Actuaries' ADAPT already is this engine), FE/PE (MCQ), EM loops
(behavioral-weighted). Borderline, parked: CCIE lab, CFA L3 essays (real
self-grading pain, partial mechanic fit), pilot checkride orals
(fragmented, price-sensitive).

### 5.7 Sequencing, and the solo-capacity truth

UWorld dominated one vertical for ~12 years before its second, then
*bought* culturally distant ones (Roger CPA, Themis) rather than
transplant content. 2U spent $1.55B on the thesis that platform and brand
transfer across verticals; audiences don't transfer, and it went
Chapter 11. And the critic found **no existence proof anywhere of a
one-person company running verified-ground-truth prep in a vertical whose
credential the founder doesn't hold.**

So the meta-plan, honestly sized: **one engine, one owned vertical, and a
pack format deliberately built for transfer.** Verticals 1 and 2 are
adjacent (same buyer, same credibility, same funnel) and can be shipped by
this builder. Vertical 3 happens only as a deliberate experiment in
handing the authoring pipeline to a recruited, credentialed SME — the
17-step-style authoring doc plus the validation harness ARE the product at
that point. The builder's role per new subject shrinks to recruiting the
verifier and running the validation, and that claim gets tested before it
gets believed.

### 5.8 What this changes in the current build, immediately

1. Every rep grades with feedback, no exceptions (5.1: without it the
   mechanic measurably does nothing).
2. Teach-then-lock stays tuned so first recall lands above ~50% success.
3. The grader earns a public agreement statistic via the validation
   harness (50–100 human-graded transcripts, kappa >0.6) — then the
   number goes on the page, ELSA-style.
4. The calibration meter ships with guided discrepancy reflection.
5. Outcome capture ("did you pass?") ships with the first paying cohort.
6. Voice/draw output modes are transfer infrastructure (+0.30 d), built
   before any new content surface.
7. Post-presell pricing moves to stakes-priced, non-renewing passes.
