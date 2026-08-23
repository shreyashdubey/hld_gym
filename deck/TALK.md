# The talk — script, future plans, and the Q&A you will actually get

Deck: `deck/index.html` in a browser, F11 for fullscreen. Arrow keys or click
to advance, `t` toggles light/dark. Ctrl+P if someone demands a PDF.

Timing for a 5-minute slot: 60s / 75s / 60s / 75s / 45s (plus demo if you
give one). If time is short, cut slide text, never the demo.

---

## Slide 1 — the problem (60 seconds)

Say this, roughly:

> "In 2006 two psychologists ran a brutal little experiment. Two groups,
> same passage, same total study time. One group re-read it four times. The
> other read it once and had to recall it three times, from memory, no
> feedback. Five minutes after studying, the re-readers were ahead, 83 to
> 71. A week later it had reversed: 61 to 40. And here's the cruel part:
> the re-readers had predicted they'd win. Re-reading feels like knowing.
> It isn't.
>
> Now: system design is the round that decides senior engineering offers.
> And almost everyone preps for it by reading and watching. They walk in
> feeling fluent, and the first 'why?' from the interviewer takes the
> whole thing apart. The problem I'm attacking is not that engineers don't
> study. It's that nothing they practice with will tell them they're not
> ready."

Why this framing: it makes the enemy *false confidence*, not lack of
content. Every later answer ("why not ChatGPT", "why pay") hangs off this.

## Slide 2 — the product (75 seconds, demo optional)

> "So I built a gym. A verified diagram teaches itself, then it disappears.
> That lock is the whole trick: while the diagram is on screen you cannot
> tell recognizing it from being able to build it. You rebuild it from
> memory, an interviewer probes your answer, pushing on the weakest edge,
> and then you get graded against a hand-verified rubric, with a failure
> map that quotes your own words back at you.
>
> The book, 51 chapters, 197 hand-verified diagrams, is free, no signup.
> The paid thing is a $19, 30-day sprint of these reps starting September 1."

If you are also giving the demonstration, close the slide with "let me just
show you" and switch to the product.

**Demo path (only if demoing; rehearse once):** the diagnostic round.
Speak briefly, answer imperfectly on purpose, finish, let the grading run,
and show the failure map quoting your own transcript. An honest "here's
where it caught me" lands far better with a technical audience than a
staged perfect run. Fallback if the network or LLM dies on stage: the sell
page's rep (cache-aside) — watch, lock, rebuild, score. It is fully
client-side and cannot fail. Know which one you're falling back to before
you start.

## Slide 3 — the buyer, and the proof (60 seconds)

> "Who buys this: a senior engineer with a system-design onsite dated a few
> weeks out. They fear this round the most, they can't tell if they're
> ready, and they're deciding between my $19 and a $179 human mock. That's
> the whole persona. Someone with no interview date is not my customer, and
> I don't spend a minute on them.
>
> And this market already pays, at every price. interviewing.io sells one
> human mock starting at a hundred and seventy-nine dollars, more if you
> want an interviewer from a specific company, and claims fifty billion
> dollars in job offers won by its users. Hello Interview bootstrapped to
> over a hundred thousand engineers at roughly forty dollars a month.
> NeetCode is one person running what he himself calls a ten-million-dollar
> business. Alex Xu's books are the category's best-sellers and his
> newsletter has a million readers. Notice the pattern in all four: the
> content is free, the money is in judgment and structure on top. And none
> of them sells the graded rebuild-from-memory loop. That open slot is the
> product.
>
> How I reach them: the free book is the funnel. It gets posted, with my
> name on it, where these people already are: r/ExperiencedDevs,
> r/leetcode, Blind, LinkedIn. No ads, no cold launches."

Why the incumbents go ON the slide instead of being hidden: to this
audience, competitors are not a threat to your pitch, they are the
existence proof that money is real. The dangerous position is "no one else
does this" (reads as "no market"). The strong position is "everyone sells
content, nobody sells this loop."

## Slide 4 — "doesn't ChatGPT kill this?" (75 seconds)

Ask the question yourself before the audience does. That's the slide's job.

> "Obvious question: ChatGPT has voice mode, NotebookLM makes study
> podcasts, people build themselves courses with Claude. Doesn't that kill
> this? I researched this properly, hundreds of primary sources, HN and
> Reddit, 2024 to 2026, and the answer has a shape.
>
> Everything whose value is *explanation* is dead as a paid product. Chegg
> sold answers; its stock fell 99%. That's why my book is free. That layer
> is the funnel, not the business.
>
> But the thing DIY-AI learners fail at, publicly, over and over, is that
> the AI is too agreeable to grade them. It's an echo chamber. People pass
> AI-assisted homework at 100% and then fail the real exam. The market
> already prices honest judgment: interviewing.io charges $179 for a single
> mock interview, because a human will tell you you're not ready. What I'm
> selling is that layer: grading against verified ground truth, a schedule
> that doesn't forget the syllabus, and your own calibration curve,
> predicted score versus real score, shrinking over 30 days. When OpenAI
> killed Study Mode this April, the best line on Hacker News was: 'AI study
> modes optimize for knowledge transfer. The harder problem is knowledge
> use, applying it under pressure.' That harder problem is the product.
>
> And that layer is not a slide about the future. It is built: a
> model-graded diagnostic interview that ends in a failure map quoting your
> own transcript, running today. Getting it hosted in front of strangers is
> the last step, and it's the very next one."

## Slide 5 — plan and the bigger machine (45 seconds)

> "Where this goes. Right now the presell is live; the metric I care about
> is three strangers paying before September 9, that's the Shipyard win
> condition, and everything in the next 17 days serves it: the graded
> diagnostic becomes the front door of the site, six minutes, a real grade,
> your failure map, one buy button, and the free book goes to the
> communities where people with onsites actually are.
>
> And the reason I'm more excited than the niche suggests: nothing in the
> machine says 'system design.' Verified ground truth, adversarial grading,
> a calibration record, welded to a dated high-stakes exam. That engine
> transfers: ML design rounds, security certifications, cloud architecture
> orals. Every one of those has people paying hundreds today for the one
> thing AI won't do, which is tell them the truth. That's what I'm
> building: the layer AI can't fake."

---

## Future plans, in the order you should say them

1. **Grader trust, always first.** Real LLM grading, quote-verified against
   the transcript, replacing the demo's keyword score everywhere a stranger
   looks. Every other feature routes its value through whether the score
   can be trusted.
2. **Calibration meter.** Predict your score before the reveal; watch your
   overconfidence curve shrink across 30 days. No competitor has it. It
   turns the Roediger & Karpicke chart into a personal instrument.
3. **Output modes that match the interview:** speaking while drawing,
   defending under interruption. Practice must match the exam's output
   mode; that's a transfer argument, not a preference one.
4. **Failure injection.** You rebuilt the system; now the cache dies, the
   lease expires. Senior loops are decided on "what breaks at 10x."
5. **Exam-date scheduling.** Spaced return compressed toward your actual
   onsite date. Deadline-shaped, like the buyer.
6. **The engine.** Same machine, new verified corpus, next vertical.

## What real value you are building (say it plainly if asked)

"Every learner has a gap between how ready they feel and how ready they
are. For a senior engineer that gap costs a job offer; in other fields it
costs a license or a patient. Free AI made the feeling of readiness cheaper
than ever, you can generate infinite fluent explanation, while making the
measurement of readiness no better at all. I'm building the measurement:
honest, verified, affordable. The book is free because explanation should
be free. The thing worth $19 is the thing that tells you the truth before
the real world charges you a lot more for it."

---

## The Q&A — likely questions, honest answers

**"Why won't OpenAI/Google just ship this?"**
OpenAI shipped free structured learning (Study Mode) and killed it in April
2026; consumer education is a money-losing demographic for them, and the
feature was 'just a system prompt.' What labs don't build is the expensive
part: hand-verified per-domain ground truth, rubrics, and a graded,
scheduled product around one exam. Google is the realer threat (Gemini
guided learning, a JEE-prep vertical in India), which is exactly why my
moat is the verified corpus and the calibration data, not the chat.

**"Why would anyone pay when ChatGPT is free?"**
They already do: interviewing.io from $179 a session, Hello Interview about
$40 a month, and mid-2026 Reddit is full of people splitting premium
accounts.
Nobody pays for explanation anymore; they pay for judgment against ground
truth. ChatGPT is structurally bad at that: it's tuned to be agreeable, and
DIY users publicly bomb real exams because of it.

**"Your moat can be built with AI. So what's the moat?"**
Start by agreeing, it disarms the question: "Yes. AI can draft my content,
and it drafted some of it. What AI cannot do is tell you whether it's
right." Then the three things AI does not produce:

1. **Verification.** In published studies of AI-generated exam questions,
   expert reviewers found error rates from 1% to 60% depending on topic,
   which is why the standard is 100% human review, and why AI drafts skew
   easy while the hard, discriminating items stay human-written. The
   economics say the same thing: drafting a question costs a few dollars,
   a *verified* high-stakes question costs $1,500 to $2,500, and the gap is
   entirely checking, not writing. AI collapsed the cost of writing. It did
   not collapse the cost of being right. I sell being right.
2. **Validation.** Anyone can prompt up a grader in an afternoon. Proving
   the grader agrees with expert humans takes a bench of human-graded
   transcripts and iteration; the literature's own finding is that LLM
   judges are "reliable without being valid," consistent and wrong. My
   grader ships with its agreement statistic, the way ELSA advertises
   93.88% agreement with human raters. The number takes months to earn and
   a prompt cannot fake it.
3. **Outcome data.** Which predicted scores matched real interview results.
   That only accumulates from real users over time, and no model can
   generate it, because nobody reports their onsite result to a generator.

Close with the precedent: "Chegg sold content: down 99%. UWorld sells
verified practice: 90% of US med students. Both existed in the same AI era.
The line between them is exactly the three things I just listed."

If they push once more ("a funded team with an SME could still copy you"):
concede that too, it's true of every seed-stage product, and name the
actual defense: a compounding head start in a niche too small for a lab and
too grubby for a big incumbent, plus the free book as owned distribution.
Moats at this stage are speed and trust, not walls.

**"Isn't this just a ChatGPT wrapper?"**
The interviewer voice is the delivery; anyone can prompt that, and I say so
on the page. The product is what a prompt can't be: 197 hand-verified
diagrams and rubrics, a grading pipeline that must quote your transcript as
evidence for every deduction, 30 days of state, and your calibration
history. When OpenAI's Study Mode died, everything that was 'just a prompt'
died with it. The parts of mine that aren't a prompt are the parts for sale.

**"How is the AI grading trustworthy?"**
Three ways. It grades against a hand-verified rubric, not its own opinion.
Every deduction must cite a quote from your actual transcript, so you can
audit it. And the page never claims more than is true: where a score is
keyword-matched, the page says so, where follow-ups are hand-written, the
page says so. The incumbents' graders get criticized as stubborn black
boxes; mine shows its evidence.

**"What's your traction?"**
Honest answer: presell went live days ago, analytics went live on the 22nd,
zero sales so far, and zero distribution so far, which is the real number.
The next 17 days are distribution. Three paying strangers by September 9 is
the test, and I've set it up so failure is informative: if strangers feel
their own failure map and still don't pay, that tells me what to fix.

**"Why $19? Isn't that too cheap to matter?"**
Deliberately under the market for the presell: it removes price as the
excuse, so a no is a real no. The evidence says the durable price is 2 to
5x higher, shaped like an exam pass (30 days, no auto-renew), which is how
UWorld and Hello Interview price deadlines.

**"What if nobody buys by Sep 9?"**
Then I own the best free system-design book on the internet, a working
graded diagnostic, and data on where strangers drop off, which is the
audience-building position every winner in this market (NeetCode, Alex Xu)
started from. The deadline is Shipyard's, not the product's.

**"Everyone's laid off, does your buyer have money?"**
The buyer isn't the desperate mass-applicant; it's the senior engineer with
a dated onsite, deciding between my $19 and a $179 human mock. Interview
prep spend concentrates exactly when the stakes are a $100k+ comp delta,
and the 2025-26 hiring rebound (Big Tech volume up ~40% YoY) means more
onsites, not fewer.

**"Won't AI change the interviews themselves?"**
The current evidence says no for this round: an Oct 2025 interviewing.io
survey found 0 of 52 FAANG respondents moving away from these formats, and
system design is the round interviewers call most AI-resistant. If formats
do shift, the engine's bet is format-independent: some dated, high-stakes,
synthesis-under-pressure evaluation will exist, and it will need honest
prep.

**"Isn't memorizing diagrams the wrong way to prep?"** (someone will say it)
Agreed, and that's not the mechanic. Memorization is the *input*; the
grading is on synthesis: you defend the design under probing, the probes
follow your answer, and the failure map marks reasoning gaps, not missing
labels. The lock exists because you can't measure what someone can produce
while the answer is on screen. It's the difference between a closed-book
exam and flashcards.

**"Learning styles? I'm an audio learner."** (it has come up before)
Learning-styles matching doesn't replicate (Pashler 2008). The product's
variety is justified by the *output* mode of the exam, you'll speak and
draw and defend, because that's what transfers, not by input preference.

## Three rules for the room

1. Never claim what isn't live. The page discloses hand-written follow-ups
   in the demo rep; disclose the same way on stage. Credibility is the
   product; one overclaim and slide 3 collapses.
2. If the live demo breaks, say "this is the risk of a live LLM demo" and
   switch to the client-side rep without apologizing twice.
3. End every answer on the thesis: measurement of readiness, honestly, at
   a price a person can afford. Repetition is how it sticks.
