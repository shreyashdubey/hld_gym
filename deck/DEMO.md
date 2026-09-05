# The demo deck (Shipyard demo day, Sat 5 Sep, 16:00)

One file: `deck/demo/index.html`, hosted at **https://hld-gym.vercel.app/demo/**. Ten slides. Works from any PC, fullscreen with F11 (or `f`). No login, nothing to install. The three experience slides play themselves the moment you land on them.

Keys: `→` / Space next · `←` back · `1`–`9` jump · End = slide 10 · `r` replay the experience on the current slide · `t` paper/dark · `f` fullscreen. `?slide=5` opens on a slide.

Two names are placeholders until you tell me the real ones: **Rohit Deshmukh** (person B) and **Ananya Iyer** (person C). Each is one string at the top of its `<script>` plus the markup.

Timing for 4 minutes: 20 · 25 · 15 · 15 · 60 · 15 · 30 · 15 · 30 · 15 = 240 s. Person A's experience runs to the end; B and C you leave early at the moment named below. Six minutes: let all three run out.

---

## 1 · Hook + the idea (20 s)

> Machines got good at thinking, so we stopped doing it ourselves. No code by hand, nothing built from scratch, no struggle. If the answer is always on screen, what happens to understanding?
> We're the last generation that built things by hand before a model could. The next one may never have to.
> So I've been building the opposite of an answer machine: a book compiled for one person, from how that person learns. Extract the person. Compile the book. And the book fights back.

## 2 · The method (25 s)

> By hand, today. I sit with a person and find out five things: what they already know, a prior-knowledge map and a pretest with confidence ratings. How they think, a think-aloud on one real problem. How they learn fast, what stuck in their life and what didn't, and why. How the knowledge has to come out, because practice has to match the exam: a whiteboard, a bench and code, or papers and math. And what makes it stick for them, calibration: how sure they were, against what they actually recalled a week later.
> The book then does the things the research says work: retrieval, spacing, worked examples that fade, dual coding, the lock. Not learning styles. That doesn't replicate. What they don't know, and how it has to come out.

## 3 · What is built (15 s)

> The first person was me. Fifty-one chapters, one hundred ninety-seven verified diagrams, four reels, checkpoints, and the lock: the diagram disappears, you rebuild it, an interviewer probes what you left out. Live, free, no signup.

## 4 · Person A, Shreyash: extracted → generated (15 s)

> Me. I want to know who got hurt before I want the mechanism. I read a diagram faster than a paragraph and forget both unless I have to redraw them. So every chapter has an origin, told from the person who hit the wall, then a drawing that draws itself, then the lock.

## 5 · Shreyash's experience (60 s, plays itself) · say this over it

> You tapped Pay. Your signal died. The app retried. Why weren't you charged twice?
> [origin card] Dalmellington, 2015. One pouch scanned once, recorded four times. The retry was honest. People were prosecuted over ledgers that agreed with themselves.
> [diagram draws] The key travels with the request. Stored with the result, in the same transaction. The OK gets lost. The retry carries the same key, and the server replays the response instead of the work.
> [lock] Gone. Now I rebuild it. [typing] I call five of six. [grade] Four. I never said how long a retry may arrive, and I never said why the ledger only inserts.
> [probe] And then it asks the question the chapter knows I'll miss: the retry that arrives *during* the transaction.
> [reveal] Where it breaks: effects outside your database.

## 6 · Person B, Rohit: extracted → generated (15 s)

> Rohit tests software by hand and wants to build hardware for space. History first: he won't read a mechanism until he knows which mission it broke. He learns by breaking it himself and believes it only when his own test passes. So his book opens every chapter with a failed mission, runs the mechanism on a simulated board, and makes him write the test before the code.

## 7 · Rohit's experience (leave at RESET, ~30 s)

> A cosmic ray flips one bit in a satellite's memory. Why doesn't the mission end?
> [history] Apollo 11 rebooted on the way down and kept flying. One flipped bit gave a Belgian candidate 4,096 votes. Voyager, 2022.
> [mechanism] Eight bits of data carry four bits of proof. One flip: the reader computes which bit lied and fixes it.
> [simulation] Two flips: it can't. The core hangs. The watchdog counts down. Reset. State restored. Mission continues.
> [move on at RESET, or stay for the test and the code if there is time]

## 8 · Person C, Ananya: extracted → generated (15 s)

> Ananya builds front-ends and wants to work on exoskeletons. She thinks in state machines and sixteen-millisecond frames; an equation lands only after she has seen what it moves. So her book is the gait cycle as a state machine, a knee she can tune until it oscillates, and the derivation that disappears until she can write it back.

## 9 · Ananya's experience (leave after "catches you", ~30 s)

> You step off a curb. Your knee catches you before you decide to. How does a powered exoskeleton do that in ten milliseconds without throwing you?
> [state] Heel strike, loading, mid-stance, toe-off, swing. She knows this shape.
> [derive] Torque is a spring minus a damper. K is how hard the joint argues back. B is how fast it stops arguing.
> [simulate] Too little damping: overshoot, it throws you. Enough: it settles in fifty-eight milliseconds. The exo gets there before your reflex does, so it must never be wrong.
> [move on after "catches you"; the lock, the grade and the stale-sample probe run if there is time]

## 10 · How it is built, and where it goes (15 s)

> One repo. The interviews and the profile are manual. The compile, the reels, the lock and the grader are automated. Most of the learning still arrives when I sit with someone and ask how the last thing they truly learned got in.
> Three people. Three books. Built for the next ten years, when the answer is always on screen and understanding isn't.

---

## If asked

- **"Is it learning styles?"** No. Style-matching doesn't replicate (Pashler 2008). It's what you don't know, how you think, and the output mode of the thing you're preparing for.
- **"How much is automated?"** The compile, the diagrams that draw themselves, the reels pipeline, the lock, the rubric grader, the voice interviewer with verbatim-quote checking. The extraction and the verification of every chapter are by hand.
- **"Are B and C real books?"** Real people, real profiles, first chapters. The experiences on slides 7 and 9 are the books' design, scripted for this demo; the system-design book is the fully built one.
- **"Which parts can I try?"** hld-gym.vercel.app/book, free, no signup. The rep on the front page is the lock-and-ask loop.

## If it breaks

- Wrong slide: a digit key. Experience stuck: `r`. Page dead: reload, `?slide=N`.
- Fonts missing on a strange PC: the deck still runs on system fonts; nothing else is fetched.
