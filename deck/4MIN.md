# The 4-minute demo (Shipyard demo day, Sat 5 Sep, 16:00)

Files: `deck/mocks/interviewer-round.html`, `deck/mocks/failure-map.html`. Keys on both: Space next · ArrowLeft back · r reset · t theme · f fullscreen · c compare overlay (on the map) · digits on the predict and reflection screens.

Tabs, in this order, all loaded before the slot:
1. https://hld-gym.vercel.app/#rep, scrolled so the rep panel fills the screen, idle, F11.
2. deck/mocks/interviewer-round.html on step 0 (one more Space after 'That's time' turns it into failure-map.html; the theme carries over).
3. deck/index.html on slide 5, F11.
4. deck/launch-demo.mp4 paused at 0:00. Backup only.
Start on tab 1. Two Ctrl+Tabs in the whole talk. Notifications off. Open both mocks once while online so the fonts cache; after that nothing in the talk needs the network (the rep is client-side once loaded).

Timing: 32 hook · 9 caught · 31 story · 37 rebuild · 11 honesty · 25 probes · 24 failure · 33 map · 24 thirty days · 29 category · 13 GTM · 14 CTA = 282s. That is 12s over a hard 270. Pay it back on the map: read only moment 2 aloud (−5s), and skip pressing c only if the clock says so (−6s).

The typed line, verbatim, never improvised. It scores exactly 4 of 6, missing 'rows return to the app' and 'a TTL on the write', and every screen after it is built on that result. One extra word like data, result, response, expires or evict changes the score in front of the room.

```
The app checks the cache first. Miss, so the app queries the database and writes the value back into the cache.
```

---

## 1. Hook (32s) · tab 1, live

> Machines got good at thinking, so we stopped doing it ourselves. No code by hand, nothing built from scratch, no struggle. Here is what that does to your head. Watch this diagram. It's about to disappear, and then I'm going to ask you about it.

[CLICK 'watch the rep · 12s']

> Cache-aside. The read path. Five steps. Don't take notes.

[Silence while it draws. It locks: 'That's it. It's gone.' Hold one beat.]

> Gone. Step four: what came back, and to whom?

## 2. Caught (9s)

[Do not wait for an answer. Say it yourself.]

> Rows, to the app. Some of you had it. All of you felt like you had it while it was on the screen. That feeling is the company.

## 3. Story (31s) · still the lock panel, no slide

> In 2006, two groups, same passage. One re-read it four times, one had to recall it. A week later: re-readers 40 percent, recallers 61. And the re-readers had predicted they'd win. That was books. Now the answer is always on screen. We're the last generation that built systems by hand before a model could. The next generation may never build anything by hand. So I built the place where the answer disappears, you have to think, and something honest tells you whether you did.

## 4. Rebuild, call it, submit (37s)

> Now I rebuild it, the way I'd say it to an interviewer.

[TYPE the line. Do not talk while typing.]

> Before I submit, I'll call my score. Five out of six.

[CLICK 'submit, no going back'. Two seconds of silence while the rows tick in.]

> Four. I never said what comes back to the app. I never said TTL. I wrote the chapter, and I called five. That one point is the product.

## 5. The honesty line (11s) · said once, to the room, before any mock

> Everything up to that score is live today. From here, this is the sprint as it ships: the graded round and the map run on my laptop, not yet on the site.

[CTRL+TAB to the mock.]

## 6. The interviewer comes for what you left out (25s)

> The round doesn't stop at a score. An interviewer takes over and comes for exactly what I left out.

[SPACE · timer 1:04, the rows arrow draws in orange]

> 'What did the database send back, and to whom?' I say the cache. 'So the cache talks to the database.' No. The app does.

[SPACE · timer 2:37]

> 'Another server deletes that key between your miss and your write. What's in your cache?' Stale. 'For how long?' I never set a TTL. Forever.

## 7. Failure injection (24s)

> Then it breaks my design. Senior loops are decided on what breaks.

[SPACE · timer 4:12, the red strip, the Cache node struck through]

> 'Busiest hour of the year, ten times normal. Your cache is gone. Hit rate was 99 percent. What does the database see?' Ten x. It should hold. 'It served one percent of reads. Now it serves all of them, at ten x. A thousand times what it was sized for.'

[SPACE · timer 6:00]

> That's time.

## 8. Predict, the map, the compare (33s)

[SPACE · failure-map.html loads on the predict screen]

> Before the grade, it asks me to call it.

[PRESS 5]

> Five. Same as before.

[The grading bar runs two seconds. Say nothing.]

> Then it grades me. Not a number. A map. Three moments where I would have been cut. Each one my own words, the probe that exposed it, the gap in one line, and the free chapter that closes it. Every quote is checked against the transcript in code. If it can't quote you, it can't cut you.

[PRESS c]

> Same words into ChatGPT this morning: 'Great explanation. Nice work.' It says that to everyone.

[PRESS c]

## 9. Thirty days (24s)

[SPACE]

> And it remembers. I called five, I scored four. Plus one. Day one of thirty. Which miss did I think I'd said?

[PRESS 2]

> The TTL. This diagram comes back day 3, day 8, day 17. Its next return would have been day 33, after my onsite. The date pulls it in. By the onsite, that plus one is the number I walk in with.

## 10. The category (29s) · CTRL+TAB to the deck, slide 5

> Nothing in that machine says system design. A verified answer key. A grader that has to quote you. A schedule welded to a date. A calibration record nobody else keeps. System design is the first subject. The framework is the product. Next: ML design rounds, staff loops, any subject where understanding matters more than the answer. interviewing.io charges 179 dollars for one human to say you're not ready. I sell that honesty at 19.

[Only if someone from flo101 is in the room, paid for by reading only moment 2 on the map:]

> If you're building the path across every skill, this is the verified answer key for one. They fit.

## 11. GTM and the ask (13s) · PRESS 6

> Who first: senior engineers with a system design onsite in the next six weeks. The free book is the funnel. The ask: if you have that interview, sit one round with me and tell me where the grade lied.

## 12. CTA (14s)

> hld-gym dot vercel dot app. The book is free, no signup. The rep is on the front page. The sprint is nineteen dollars, presale. Built for the next ten years, when the answer is always on screen and understanding isn't. Find me after.

[Stop. Add nothing.]

---

## If over time, cut in this order

1. On the map, read only moment 2 aloud (−5s).
2. Skip pressing c (−6s).
3. Hook: drop 'No code by hand, nothing built from scratch, no struggle.' (−4s).

Never cut: the honesty line, the typed rep, 'Forever.', the +1 screen, the last line of the CTA.

## If it breaks

- Product tab dead: play tab 4 fullscreen and say beats 1 to 4 over it; the lock is at about 0:14 in the recording. 'Tech being tech, here's the recorded run.'
- The rep is fully client-side. Once loaded, wifi can die and it still works. Load it before the slot, not during.
- A mock on the wrong screen: r resets it, ArrowLeft steps back, keep talking.
- A judge asks which screens are live: the honesty line, verbatim, then stop. No softer second admission.
- Never say 'this is still rough'. Never say 'ignore the UI'.

## Before the slot, in order

1. git push at the repo root (the live page still says '1 September' in seven places until you do).
2. Ask ChatGPT the 21 typed words in a fresh session; paste its reply into CHATGPT_REPLY at the top of deck/mocks/failure-map.html.
3. Open the four tabs in order, the mocks once while online. F11 everywhere. Notifications off.
4. Type the line twice with a timer so your hands know it.
5. Walk both Ctrl+Tabs and every Space with a timer, twice. Reset: r on each mock, Alt+Left from failure-map back to interviewer-round.
6. Three slow breaths. In for 4, hold 4, out 6. Twice.
