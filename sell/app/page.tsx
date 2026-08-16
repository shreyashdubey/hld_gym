import Link from "next/link";
import Rep from "@/components/Rep";
import Reels from "@/components/Reels";
import StudyChart from "@/components/StudyChart";
import FreeBookFab from "@/components/FreeBookFab";
import BookButton from "@/components/BookButton";
import { TextSizeToggle, ThemeToggle } from "@/components/Toggles";

/* Swap this for the real Gumroad link once the product is created.
   Until then it is deliberately obvious that it is unset. */
const BUY_URL = process.env.NEXT_PUBLIC_BUY_URL ?? "#buy";
/* Same origin now: the sprint owns the site root, the book sits at /book. */
const BOOK_URL = "/book/";

/* Copy rule for this page: a visitor who reads only the kicker, the h1, the
   terms strip and the bold line under each heading must still know what this
   is, what it costs, when it starts, and why the lock exists. The prose is for
   the minority who want it, never the load-bearing path. */

export default function Home() {
  return (
    <>
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
            Read the book <span className="freeChip">free</span>
          </a>
          <TextSizeToggle />
          <ThemeToggle />
        </div>
      </header>

      <div className="wrap">
        <section className="hero">
          <div className="heroGrid">
            <div className="heroCopy">
              <p className="eyebrow">30-day system design sprint · presale</p>
              <h1>You can read system design for months and still freeze at the whiteboard.</h1>
              <p className="lead">
                Thirty days, one system a day. You learn it, it is{" "}
                <strong>taken away</strong>, and you rebuild it from memory while an interviewer
                picks holes in what you said. A rep takes as long as it takes. The ones you get
                wrong take longest, and that is where the work is.
              </p>
            </div>

            <aside className="heroCard">
              <div className="termbar termCol">
                <div>
                  <b>$39</b>
                  <span>one time</span>
                </div>
                <div>
                  <b>30 reps</b>
                  <span>one a day</span>
                </div>
                <div>
                  <b>1 Sep</b>
                  <span>start date</span>
                </div>
                <div>
                  <b>100%</b>
                  <span>refund if late</span>
                </div>
              </div>
              <div className="btnRow">
                <a className="btn" href={BUY_URL}>
                  Reserve a seat for $39
                </a>
                <a className="btn ghost" href="#rep">
                  Try a free rep first, 90 seconds
                </a>
              </div>
              <p className="alt">
                Not ready to buy? <a href={BOOK_URL}>Read all 51 chapters free</a>, no signup.
              </p>
            </aside>
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
          <h2>Six steps, every day, and it always disappears.</h2>
          <p className="key">
            Reading gets you recognition. Interviews want recall. Reading harder does not turn one
            into the other.
          </p>
          <div className="grid2">
            <div>
              <h4>
                <span className="n">01</span> Watch
              </h4>
              <p>The diagram builds itself, step by step, with the reason for each one.</p>
            </div>
            <div>
              <h4>
                <span className="n">02</span> Lock
              </h4>
              <p>It vanishes. No scrolling back, no peeking. This is the part that works.</p>
            </div>
            <div>
              <h4>
                <span className="n">03</span> Rebuild
              </h4>
              <p>You put it back from memory and explain it the way you would say it out loud.</p>
            </div>
            <div>
              <h4>
                <span className="n">04</span> Defend
              </h4>
              <p>
                An interviewer attacks the answer. What breaks when this node dies? What is your
                write path at 50k QPS?
              </p>
            </div>
            <div>
              <h4>
                <span className="n">05</span> Score
              </h4>
              <p>Graded against the chapter, not vibes. What you missed is named out loud.</p>
            </div>
            <div>
              <h4>
                <span className="n">06</span> Return
              </h4>
              <p>
                What you failed comes back in days. What you nailed comes back in weeks. You never
                manage the schedule.
              </p>
            </div>
          </div>
        </section>

        <section id="reels">
          <p className="eyebrow">ten a day, on the topic you are on</p>
          <h2>The revision you will actually do</h2>
          <p className="key">
            Nobody re-opens a chapter they finished three weeks ago. Everybody watches one more.
          </p>
          <p>
            Every topic you study ships with <strong>ten reels</strong>. Fifteen seconds each,
            one idea, told as something ordinary going wrong: a hotel keycard, a coffee queue, a
            cleared desk. In the last two seconds the same picture is relabelled as your system.
            Watch them on the train. That is the whole ask.
          </p>
          <p>
            Then the topics you already finished come back. Not all of them, and not on a day you
            choose: whatever you got wrong returns in days, whatever you nailed returns in weeks,
            mixed into the same feed. Revision stops being a thing you schedule and starts being a
            thing you scroll.
          </p>
          <p className="fact">
            <strong>Four of these are built and playing below.</strong> They ship at ten a day from
            1 September; today there are four. Everything on this page that exists, you can touch,
            and everything that does not says so.
          </p>
          <Reels />
          <p className="fact">
            Why the format works, and it is not because anyone is a “visual learner”. That idea
            has no evidence behind it (Pashler, 2008). It works because the thing you are practising
            is drawing a system while talking through it, which is the thing the interview asks for.
            The reel is that same picture, built one piece at a time, short enough that you finish it.
          </p>
        </section>

        <section>
          <p className="eyebrow">why the diagram disappears</p>
          <h2>The part that feels worst is the part that works</h2>
          <div className="split">
            <div>
          <p className="key">
            Re-reading feels smooth. Smooth feels like knowing. That is the most expensive illusion
            in interview prep.
          </p>
          <p>
            In 2006, Roediger and Karpicke ran this. Same passage, same total time, two groups. One
            group read it four times. The other read it once, then three times wrote down everything
            they could remember, with no feedback and no looking back.
          </p>
          <p>
            Tested five minutes later, the readers were ahead. Tested a week later, the readers
            could produce <strong>40%</strong> of the passage and the recall group produced{" "}
            <strong>61%</strong>. Completely reversed.
          </p>
          <p>
            Before that final test, everyone predicted their own score. The readers predicted they
            would win. Reading it four times had been easy, and easy feels like knowing.
          </p>
          <p>
            That feeling is exactly what the lock removes. While the diagram is on screen you cannot
            tell recognising it apart from being able to build it, because it is right there in
            front of you. Take it away and there is nothing left to feel fluent about. You either
            produce it or you do not.
          </p>
            </div>
            <StudyChart />
          </div>
          <p className="fact">
            Chase &amp; Simon, 1973: chess masters rebuild a real board far better than novices, and
            lose the whole advantage on a random one. Their memory is not bigger; their chunks are. A
            junior holds “load balancer, cache, primary, replica” as four things. A senior holds
            “standard read path” as one. Chunks come from rebuilding with feedback, never from
            reading a description.
          </p>
        </section>

        <section>
          <p className="eyebrow">the source material</p>
          <h2>The book is finished, and it is free</h2>
          <p className="key">
            The sprint is not the book. The book is what the sprint grades you against.
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
              <span>real outages</span>
            </div>
            <div>
              <b>1,278</b>
              <span>questions</span>
            </div>
          </div>
          <p style={{ marginTop: 18 }}>
            Written for the senior bar: Meta E5, Google L5 and equivalents. No signup, no email, no
            paywall, and no plans for one.
          </p>
          <div className="btnRow">
            <BookButton>Read the free book, no signup</BookButton>
          </div>
        </section>

        <section>
          <p className="eyebrow">the offer</p>
          <h2>30-day system design sprint</h2>
          <div className="pricebox">
            <div className="priceH">presale · starts 1 september 2026</div>
            <div className="priceB">
              <div className="amount">
                <span className="cur">$</span>39
                <span className="per">one time · not a subscription</span>
              </div>
              <ul className="plain">
                <li>
                  <strong>30 reps</strong>, one a day, drawn from the book’s 197 diagrams.
                </li>
                <li>
                  <strong>An interviewer that pushes back</strong>, with three follow-ups per rep
                  aimed at what you left out.
                </li>
                <li>
                  <strong>10 reels a day</strong> on the topic you are on, plus reels from topics
                  you already finished, mixed back in as revision.
                </li>
                <li>
                  <strong>A schedule you never manage</strong>, so failures return in days and wins
                  in weeks.
                </li>
                <li>
                  <strong>A record of what you actually know</strong>, not what you have read.
                </li>
              </ul>
              <div className="btnRow">
                <a className="btn" id="buy" href={BUY_URL}>
                  Reserve a seat for $39
                </a>
                <span className="hint">full refund if it does not ship on 1 September</span>
              </div>
            </div>
          </div>

          <h3>Straight about what exists today</h3>
          <p className="key">The book is done and live. The sprint ships 1 September.</p>
          <p>
            The rep on this page is real, and hand-built. In the product, the follow-ups are
            generated against your actual answer instead of written in advance. Four reels are
            built and playing above; the daily ten start on 1 September. If it is not live on
            1 September you get every rupee back, without emailing me to ask.
          </p>
        </section>

        <footer>
          <p className="fact">
            Built by Shreyash Dubey · <a href={BOOK_URL}>the book</a> · shipping in public through
            Project Shipyard S3
          </p>
        </footer>
      </div>

      <FreeBookFab />
    </>
  );
}
