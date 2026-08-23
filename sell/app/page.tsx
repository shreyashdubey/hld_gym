import type { Metadata } from "next";
import Link from "next/link";
import Rep from "@/components/Rep";
import Reels from "@/components/Reels";
import StudyChart from "@/components/StudyChart";
import FreeBookFab from "@/components/FreeBookFab";
import BookButton from "@/components/BookButton";
import { TextSizeToggle, ThemeToggle } from "@/components/Toggles";
import { BOOK_URL, PRICE, RESERVE_URL } from "@/lib/links";

/* Copy rules for this page.

   1. A visitor who reads only the kicker, the h1, the terms strip and the bold
      line under each heading must still know what this is, what it costs, when
      it starts, and why the lock exists. The prose is for the minority who want
      it, never the load-bearing path.
   2. Each disclosure lives in one place, plus the "What exists today" answer,
      which is the summary. "Four reels exist" is the fact line above the reels;
      "the follow-ups are hand-written" and "the score is keyword" are in the
      rep. A fact repeated four times reads as nervousness, and a page asking a
      stranger for money cannot afford to look nervous.
   3. Section order follows the argument: the demo, how it works, why the lock
      works, then the ChatGPT question answered head-on, then the reels as the
      supporting act, then the book, then the offer. The evidence for the lock
      sits next to the lock, and the objection every visitor arrives with gets
      its own section rather than a buried FAQ bullet: research on this exact
      audience (2026-08-23, see ../ROADMAP.md) found "why would I pay when I
      have Claude" is the reflex first objection, and that the sellable layer
      is graded judgment, never the AI interviewer, which reads as a wrapper.
   4. Budget: about 2,000 rendered words. A copy pass wanted 1,300 and a buyer
      pass wanted four more answers (topics, chat window, timeline, trust); the
      answers won because each was a stated bounce point, and the cuts landed
      everywhere else. Add a paragraph here only by taking one out. */

/* The book's four parts, from ../src/toc.json. Chapter counts sum to 51 and
   the topics are the chapter titles, compressed: a Xu or DDIA reader can see
   what is in without leaving the page, and check it against the free book. */
const PARTS = [
  {
    name: "The Meta-Game",
    ch: 2,
    topics: "how the interview is actually scored; company playbooks for Meta, Google, Palantir, Anthropic",
  },
  {
    name: "Foundations",
    ch: 14,
    topics:
      "the request path, API design, data modelling and indexes, estimation, load balancing, caching, CDNs and blobs, replication, sharding and consistent hashing, CAP and quorums, queues, rate limiting, NoSQL, IDs, search indexes and locks",
  },
  {
    name: "Senior Depth",
    ch: 11,
    topics:
      "2PC, sagas and outbox; idempotency and ledgers; consensus, leader election and fencing; CRDTs vs OT; multi-region and cells; hot partitions; backpressure and circuit breakers; SLOs and error budgets; stream processing; probabilistic structures and gossip; zero-downtime migrations",
  },
  {
    name: "The Problem Gauntlet",
    ch: 24,
    topics:
      "URL shortener, typeahead, notifications, WhatsApp, news feed, Uber, Dropbox, Ticketmaster, web crawler, global rate limiter, job scheduler, top-k, ad click aggregation, payments, Google Docs, distributed cache, Kafka, metrics, search, S3, YouTube, stock exchange, LLM inference serving, vector search and RAG",
  },
];

/* Robots directives live here, not in the layout: the layout is shared with the
   404, where Next already emits noindex, and the two together produced a page
   claiming both at once. */
export const metadata: Metadata = {
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true, "max-snippet": -1, "max-image-preview": "large" },
  },
};

export default function Home() {
  return (
    <>
      <a className="skip" href="#rep">
        Skip to the demo
      </a>
      <header className="topbar">
        <div className="topbarInner">
          {/* Link because "/" is a route in this app. Every /book/ link below stays
              a plain <a>: the book is a static file built by a different
              pipeline, not a page Next knows about. */}
          <Link className="brand" href="/">
            <span className="mk">HLD</span>Gym
          </Link>
          <span className="spacer" />
          <a className="mini" href={BOOK_URL}>
            <span className="miniLong">Read the </span>book <span className="freeChip">free</span>
          </a>
          <TextSizeToggle />
          <ThemeToggle />
        </div>
      </header>

      <main className="wrap" id="main">
        <section className="hero">
          <div className="heroGrid">
            <div className="heroCopy">
              <p className="eyebrow">30-day system design sprint · presale</p>
              <h1>You can read system design for months and still freeze at the whiteboard.</h1>
              <p className="lead">
                Reading gets you recognition. Interviews want production under pressure. So a
                diagram from the free HLD Gym book teaches itself, then it is{" "}
                <strong>taken away</strong>. You rebuild it from memory, explain it the way you
                would out loud, an interviewer picks holes in what you said, and you get an honest
                grade: what you missed, named, with your own words as the evidence. Six or seven of
                those a day for thirty days is <strong>197 reps</strong>, one for every diagram in
                all 51 chapters. About an hour a day, set at the senior bar: Meta E5, Google L5 and
                equivalents.
              </p>
            </div>

            {/* A div, not an aside: the price and the primary action are the
                page, not something complementary to it. */}
            <div className="heroCard">
              <div className="termbar termCol">
                <div>
                  <b>{PRICE}</b>
                  <span>one time</span>
                </div>
                <div>
                  <b>197 reps</b>
                  <span>one per diagram</span>
                </div>
                <div>
                  <b>1 Sep</b>
                  <span>start date</span>
                </div>
                <div>
                  <b>~1 hour</b>
                  <span>a day, 30 days</span>
                </div>
              </div>
              <div className="btnRow">
                {/* New tab on every reserve link: the form is someone else's
                    page, and a visitor who backs out of it should land on the
                    offer again rather than on a blank history entry. */}
                <a className="btn" href={RESERVE_URL} target="_blank" rel="noopener">
                  Reserve a seat for {PRICE}
                </a>
                <a className="btn ghost" href="#rep">
                  Try a free rep first, 90 seconds
                </a>
              </div>
              <p className="hint">
                A short form, then the payment link by email. You are charged nothing until you
                click it, and refunded in full if the sprint does not ship on 1 September.
              </p>
              <p className="alt">
                Not ready to buy? <a href={BOOK_URL}>Read all 51 chapters free</a>, no signup, or{" "}
                <a href="#offer">see everything the {PRICE} buys</a>.
              </p>
            </div>
          </div>
        </section>

        <section id="rep">
          <p className="eyebrow">try it right here</p>
          <h2>One real rep, running on this page</h2>
          <p className="key">
            Ninety seconds. It will probably go badly. That is the entire point of showing it to
            you before you pay.
          </p>
          <Rep />
        </section>

        <section>
          <p className="eyebrow">how a rep works</p>
          <h2>Six steps, and the diagram always disappears.</h2>
          <p className="key">
            Watch a diagram once, then rebuild it without it. Six or seven different diagrams a
            day, and the ones you fail come back.
          </p>
          <div className="grid2">
            <div>
              <h3>
                <span className="n">01</span> Watch
              </h3>
              <p>The diagram builds itself, step by step, with the reason for each one.</p>
            </div>
            <div>
              <h3>
                <span className="n">02</span> Lock
              </h3>
              <p>It vanishes. No scrolling back, no peeking. This is the part that works.</p>
            </div>
            <div>
              <h3>
                <span className="n">03</span> Rebuild
              </h3>
              <p>
                You put it back from memory, in words: every step, in order, the way you would say
                it out loud. No drawing canvas. What fails at a whiteboard is the sequence, not the
                pen.
              </p>
            </div>
            <div>
              <h3>
                <span className="n">04</span> Defend
              </h3>
              <p>
                An interviewer attacks the answer. What breaks when this node dies? What is your
                write path at 50k QPS?
              </p>
            </div>
            <div>
              <h3>
                <span className="n">05</span> Score
              </h3>
              <p>Graded against the chapter, not vibes. What you missed is named out loud.</p>
            </div>
            <div>
              <h3>
                <span className="n">06</span> Return
              </h3>
              <p>What you failed comes back in days. What you nailed comes back in weeks.</p>
            </div>
          </div>
        </section>

        <section>
          <p className="eyebrow">why the diagram disappears</p>
          <h2>The part that feels worst is the part that works</h2>
          <div className="split">
            <div>
              <p className="key">
                Re-reading feels smooth. Smooth feels like knowing. That is the most expensive
                illusion in interview prep.
              </p>
              <p>
                In 2006, Roediger and Karpicke gave two groups the same passage and the same total
                time. One group read it four times. The other read it once, then wrote down
                everything they could remember, three times, with no feedback and no looking back.
                Five minutes later the readers were ahead. A week later the readers could produce{" "}
                <strong>40%</strong> of the passage and the recall group <strong>61%</strong>.
              </p>
              <p>
                Before that final test, everyone predicted their own score. The readers predicted
                they would win. Reading it four times had been easy, and easy feels like knowing.
              </p>
              <p>
                That feeling is what the lock removes. While the diagram is on screen you cannot
                tell recognising it apart from being able to build it. Take it away and there is
                nothing left to feel fluent about. You either produce it or you do not.
              </p>
            </div>
            <StudyChart />
          </div>
        </section>

        <section>
          <p className="eyebrow">the obvious question</p>
          <h2>Why not just ChatGPT?</h2>
          <p className="key">
            For explanation, you should. Explanation is free now, which is why the whole book is
            free. What a chat cannot sell you is a grade you can trust.
          </p>
          <p>
            A chat is tuned to be agreeable. Ask it to quiz you and it praises a wrong answer
            delivered confidently, which is worse than no practice at all: it manufactures the
            exact feeling of readiness the lock exists to destroy. People find this out in public,
            every hiring season: flawless AI-assisted practice, then a failed loop.
          </p>
          <p>
            The sprint sells the other layer. The diagram comes off the screen before you answer.
            The grade comes from the chapter the diagram belongs to, not from whatever the model
            improvises that day, and what you missed is quoted back from your own words. The
            schedule remembers which of 197 diagrams you failed twelve days ago; a chat window
            forgets the syllabus by Tuesday. That layer is the product. It is the one layer a free
            model does not offer, because honesty is not what it is tuned for.
          </p>
        </section>

        <section id="reels">
          <p className="eyebrow">15 a day · 450 across the sprint</p>
          <h2>The revision you will actually do</h2>
          <p className="key">
            Ten teach the day&rsquo;s topic. Five bring back one you finished, because nobody
            re&#8209;opens a chapter from three weeks ago and everybody watches one more.
          </p>
          <div className="termbar">
            <div>
              <b>10</b>
              <span>on today&rsquo;s topic</span>
            </div>
            <div>
              <b>5</b>
              <span>on one you finished</span>
            </div>
            <div>
              <b>45s</b>
              <span>each, one idea</span>
            </div>
            <div>
              <b>450</b>
              <span>over 30 days</span>
            </div>
          </div>
          <p className="fact">
            <strong>Four are built and playing below.</strong> The daily fifteen start on
            1 September.
          </p>
          {/* The prose renders under the playlist, beside the reel: the proof
              first, the explanation in the column the 9:16 rail leaves empty. */}
          <Reels>
            <p className="reelProse">
              <strong>Ten reels on the day&rsquo;s topic, five from a topic you already
              finished</strong>, chosen for you and mixed into one feed. Forty-five seconds
              each, one idea, told as something ordinary going wrong: a hotel keycard that still
              opens the door, three flatmates and a moved dinner, a coffee counter in a rush. In
              the last few seconds the same picture is relabelled as your system. Fifteen a day
              is about eleven minutes, the part of the sprint you do on the train.
            </p>
            <p className="reelProse">
              <strong>They go where the book is hardest.</strong> Consensus, quorum overlap,
              isolation levels, clock skew: the chapters people bounce off once and never open
              again. A reel does not make them easy by making them wrong. It takes the one idea
              the chapter turns on and shows it happening to something you already understand.
            </p>
            <p className="fact">
              Not because anyone is a &ldquo;visual learner&rdquo;: that idea has no evidence
              behind it (Pashler, 2008). Because a reel is the picture the interview asks you to
              draw, built one piece at a time, short enough that you finish it.
            </p>
          </Reels>
        </section>

        <section>
          <p className="eyebrow">the source material</p>
          <h2>The book is finished, and it is free</h2>
          <p className="key">
            The sprint is not the book. The book is what the sprint grades you against, and the
            sprint covers all of it.
          </p>
          <div className="termbar">
            <div>
              <b>51</b>
              <span>chapters</span>
            </div>
            <div>
              <b>197</b>
              <span>diagrams</span>
            </div>
            <div>
              <b>125</b>
              <span>war stories</span>
            </div>
            <div>
              <b>1,278</b>
              <span>questions</span>
            </div>
          </div>
          <table className="spec">
            <thead>
              <tr>
                <th>part</th>
                <th>chapters</th>
                <th>covers</th>
              </tr>
            </thead>
            <tbody>
              {PARTS.map((p) => (
                <tr key={p.name}>
                  <td>{p.name}</td>
                  <td className="num">{p.ch}</td>
                  <td className="tag">{p.topics}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p>
            Written for the senior bar: Meta E5, Google L5 and equivalents. No signup, no email, no
            paywall, and no plans for one. Open any chapter and judge the sprint by it.
          </p>

          {/* This described two front doors until 2026-08-23. It described them
              accurately and nobody understood it: readers asked which one to
              read, and the second door was never linked from the built page
              anyway. There is one book now. Every number is counted off the
              built file, not planned: 36 .origin.html, 189 sources across the
              cite.json set, 26 photographs and 46 marks in the 72 shipped
              figures, 150 cards. The 15 chapters that open on a scene instead
              are stated because a reader who hits one after being told "51
              histories" has been misled. */}
          <div className="split2">
            <div>
              <h3>It opens on what actually happened</h3>
              <p className="key">
                <strong>36 of the 51 chapters</strong> start with the real incident that forced the
                mechanism into its shape. The other fifteen open on a scene.
              </p>
              <p>
                Named people, named companies, a date, and a source you can go and read. The
                mechanism arrives as somebody&rsquo;s fix for a bad night, which is what it was.
                Then the chapter teaches it properly.
              </p>
            </div>
            <div>
              <h3>What is in there</h3>
              <p className="key">Counted off the built file, not promised. Open it and check.</p>
              <ul className="plain">
                <li>
                  <strong>36 histories, 189 sources.</strong> Papers, RFCs, postmortems, commits
                  and oral histories, cited inline. Every date and figure is checked against the
                  document, not a search result.
                </li>
                <li>
                  <strong>26 photographs and 46 company logos</strong>, licensed and credited,
                  sitting in the chapter next to the paragraph that names them.
                </li>
                <li>
                  <strong>150 cards, four suits</strong>: person, incident, artifact, ripple. You
                  keep a card by answering it, not by reading it, and the ones you keep join the
                  same review queue as the chapter&rsquo;s questions.
                </li>
              </ul>
            </div>
          </div>

          <div className="btnRow">
            <BookButton>Read the free book, no signup</BookButton>
          </div>
        </section>

        <section id="offer">
          <p className="eyebrow">the offer</p>
          <h2>30-day system design sprint</h2>
          <p className="key">
            Everything you are buying is listed below, and so is everything you are not.
          </p>
          <div className="pricebox">
            <div className="priceH">presale · starts 1 september 2026</div>
            <div className="priceB">
              <div className="amount">
                <span className="cur">$</span>19
                <span className="per">one time · not a subscription</span>
              </div>
              <p style={{ marginTop: 0 }}>
                Thirty days, one topic a day, the whole 51-chapter book.
              </p>
              <ul className="plain">
                <li>
                  <strong>6 or 7 reps a day, 197 across the sprint</strong>: a first sight of every
                  diagram in the book, and what you failed comes back on top of that. Each is the
                  loop on this page: watch, lock, rebuild from memory in words, defend, score,
                  return. About an hour.
                </li>
                <li>
                  <strong>An interviewer that pushes back</strong>: three follow-ups per rep,
                  generated against your actual answer and aimed at what you left out.
                </li>
                <li>
                  <strong>15 reels a day, 450 in total</strong>: ten on that day&rsquo;s topic,
                  five on one you already finished. About eleven minutes.
                </li>
                <li>
                  <strong>A schedule you never manage</strong>: what you could not rebuild comes
                  back in days, what you nailed comes back in weeks. You open the day&rsquo;s reps;
                  you never pick them.
                </li>
                <li>
                  <strong>Lifetime access</strong>: one payment, no renewal, nothing to cancel. It
                  runs in the browser, on a phone or a laptop.
                </li>
              </ul>
              <div className="btnRow">
                <a className="btn" id="buy" href={RESERVE_URL} target="_blank" rel="noopener">
                  Reserve a seat for {PRICE}
                </a>
                <span className="hint">
                  opens a short form · full refund if it does not ship on 1 September
                </span>
              </div>
            </div>
          </div>

          <h3>What happens after you click</h3>
          <p className="key">
            There is no checkout on this page. The button opens a form, and payment is a link I
            send you.
          </p>
          <div className="grid2">
            <div>
              <h4>
                <span className="n">01</span> You answer five questions
              </h4>
              <p>
                Sixty seconds: when you interview, at what level, where it breaks for you, which
                part of this you want most, whether you would pay today, and your email. No
                account, no password, no card.
              </p>
            </div>
            <div>
              <h4>
                <span className="n">02</span> I email you the payment link
              </h4>
              <p>
                Within 24 hours, to the address you gave. {PRICE}, one time. If you change your mind
                you simply do not click it.
              </p>
            </div>
            <div>
              <h4>
                <span className="n">03</span> You pay, and day one lands 1 September
              </h4>
              <p>
                Topic 1, its reps and its fifteen reels, then a new topic every day for thirty
                days. Nothing more is ever charged.
              </p>
            </div>
          </div>

          <div className="split2">
            <div>
              <h3>What you are not buying</h3>
              <p className="key">
                Said plainly, so nobody pays {PRICE} for a thing they thought was included.
              </p>
              <ul className="plain">
                <li>
                  <strong>Not the book.</strong> All 51 chapters are free, now and permanently,
                  with no signup. The sprint is the practice; the book is what it grades you
                  against.
                </li>
                <li>
                  <strong>No videos of anyone talking</strong>, no live calls, no Discord, no
                  one-to-one mentoring, no certificate.
                </li>
                <li>
                  <strong>No mock interview with a human.</strong> The interviewer is software; it
                  grades you against the chapter, not against anyone&rsquo;s mood.
                </li>
                <li>
                  <strong>Not a subscription</strong>, and not a job guarantee. The book rebuilt
                  from memory in thirty days, and an honest score, is the entire promise.
                </li>
              </ul>
            </div>
            <div>
              <h3>Before you pay</h3>
              <p className="key">
                Answered by the person building it, before you spend anything.
              </p>
              <ul className="plain">
                <li>
                  <strong>What exists today?</strong> The book, all 51 chapters, with 36 histories. The rep
                  on this page,
                  hand-built: its follow-ups were written in advance and its score is keyword
                  matching. Model grading is built and running in a diagnostic interview that ends
                  in a failure map quoting your own transcript; it is not hosted on this page yet,
                  so everything you can click here today is the keyword version. Four reels of the
                  450. The sprint itself ships 1 September.
                </li>
                <li>
                  <strong>Why not quiz myself with a chat window?</strong> You should, tonight,
                  for one rep. The difference is answered in its own section above: a chat will
                  not take the diagram away first, will not grade you against a fixed chapter, and
                  will not remember what you failed.
                </li>
                <li>
                  <strong>My interview is in the middle of September.</strong> The form asks when
                  it is. Say so, and the reply that carries the payment link tells you what the
                  first days cover, before you have paid anything.
                </li>
                <li>
                  <strong>What if I fall behind?</strong> Nothing expires. Access is for life, so
                  the thirty days are the pace, not a deadline.
                </li>
                <li>
                  <strong>What if it does not ship on 1 September?</strong> Every dollar back,
                  without emailing me to ask.
                </li>
                <li>
                  <strong>Why trust the sprint?</strong> Judge it by the book, which is by the same
                  person. Open{" "}
                  <a href={`${BOOK_URL}#ch/p2c03`}>Consensus, Leader Election and Fencing</a> or{" "}
                  <a href={`${BOOK_URL}#ch/p3c08`}>Ticketmaster: Booking Under Pressure</a> and
                  read at the depth the reps are set to. If the chapter is below the bar you need,
                  keep your {PRICE}.
                </li>
                <li>
                  <strong>Anything else?</strong> Email{" "}
                  <a href="mailto:shreyashlrn@gmail.com">shreyashlrn@gmail.com</a> or message me
                  on{" "}
                  <a href="https://www.linkedin.com/in/dubeyshreyash/" target="_blank" rel="noopener">
                    LinkedIn
                  </a>
                  . A real person reads these, and it is the same person building it.
                </li>
              </ul>
            </div>
          </div>
        </section>

      </main>
      {/* Outside <main>, so it is the page's contentinfo landmark. */}
      <div className="wrap">
        <footer>
          {/* A plain text route back to the ask: the page ends 1,100px after the
              last button, and a third accent fill is not wanted. */}
          <p className="fact">
            Built by Shreyash Dubey · <a href={BOOK_URL}>the book</a> ·{" "}
            <a href={RESERVE_URL} target="_blank" rel="noopener">reserve a seat for {PRICE}</a> ·
            shipping in public through Project Shipyard S3
          </p>
        </footer>
      </div>

      <FreeBookFab />
    </>
  );
}
