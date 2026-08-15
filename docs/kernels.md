# Kernels — one causal core per topic

Status: **draft, unvalidated.** 25 candidates, one per concept chapter.
Date: 2026-08-16. Source for the reel scripts in `../../hld-sprint/reel/`.

---

## What a kernel is

The compressed core of a topic that lets you regenerate the rest. Not a fact to
recite — a mechanism to run forward.

> "An odd-length cycle means the graph isn't bipartite" is the **result**.
> "2-colour it; every edge flips the colour; an odd walk lands you back on
> yourself wearing the wrong colour" is the **kernel** — and it regenerates the
> theorem, the proof, and the BFS-colouring algorithm.

Three gates. A candidate that misses any of them is a slogan.

1. **Mechanical, not declarative.** You can run it forward from a blank page.
2. **Derives 3+ facts** the learner never separately stored.
3. **Has a named boundary** where it stops being true.

## The risk to hold onto

A kernel is memorisable *without* its substrate. Handed over as the teaching
unit, this becomes a system-design Twitter thread — recitable, and worth
nothing. It has to be the thing the learner **produces** after the rep, as a
compression check, not the thing handed to them before it.

See `learning-and-retention.md` for why (chunking, Chase & Simon 1973): the
kernel is the index, the derivation is the knowledge.

---

## Part 1 — Foundations

### p1c01 · How a request travels
**Latency is round trips, not bandwidth. Count the round trips before the first byte.**

- Cold connection: DNS 1 + TCP 1 + TLS 2 + request 1 = 5 RTT. At 150ms
  cross-continent that is 750ms before a single byte of content.
- Keep-alive, connection pools, HTTP/2 multiplexing and TLS session resumption
  all exist to delete round trips, and nothing else.
- A CDN wins by terminating TLS near you, not by being a faster computer.

Breaks: bulk transfer (video, backups) is bandwidth-bound. Counting RTT there
tells you nothing.

### p1c02 · API design
**Every endpoint is a contract about who retries. Ask: if the client sends this twice, what is true after?**

- PUT is idempotent by construction; POST needs an idempotency key; DELETE
  should succeed on an already-deleted resource.
- Offset pagination shifts under concurrent writes, which is why cursors exist.
- Versioning exists because you cannot change a contract under a caller you do
  not control.

Breaks: internal APIs where you own both sides and deploy atomically.
Versioning there is ceremony.

### p1c03 · Data modeling and indexes
**An index is a sorted copy of some columns. Ask what it is sorted by, and whether your query matches that sort from the left.**

- An index on `(a, b)` serves `a = ?` and `a = ? AND b = ?`, never `b = ?`.
- A range predicate on `a` kills the use of `b`.
- `ORDER BY` is free when it matches the sort; a covering index skips the heap
  fetch entirely.
- Every index is another sorted copy to maintain, so writes pay per index.
- A low-cardinality index loses to a sequential scan.

Breaks: hash indexes (no order, equality only), and LSM trees, where "sorted"
means sorted-in-levels and the write path is a different animal.

### p1c04 · Estimation
**Daily count divided by 100,000 is your QPS. Then multiply by size.**

- 86,400 seconds ≈ 10⁵. 1M DAU × 10 actions = 100 QPS average, peak 2–5×.
- 100 QPS is one box; 100k QPS is a fleet. The number picks the architecture,
  and that is the only reason to compute it.
- Same move gives storage (× bytes × retention) and cache size (80/20).

Breaks: bursty correlated traffic. A ticket drop or a notification storm has
peak-to-average near 1000×; estimate the burst, not the mean.

### p1c05 · Scaling out
**You can only add machines to work that does not need to agree. Find the thing that must agree — that is your real capacity.**

- A stateless web tier scales linearly; sessions must move out; the database is
  the ceiling; sticky sessions are a scaling bug you introduced yourself.
- L7 can route on content because it terminates the connection and reads it.
- Past a point, coordination makes throughput go *down*, not flat.

Breaks: embarrassingly parallel work behind a rate-limited third party. More
machines make it strictly worse.

### p1c06 · Caching
**The cache is a suggestion. The database is the truth.**

- Any entry may vanish at any moment and the system must stay correct, so no
  write lands only in the cache.
- TTL is your staleness bound, stated in seconds.
- A miss storm hits everyone at once because the suggestion expired for everyone
  at once — hence stampede locks and early recompute.
- Invalidation is hard because it is two systems disagreeing about one fact.

Breaks: when the cache **is** the truth — Redis as a lock, a rate-limit counter,
a session store. Then an eviction is data loss, not a slow path.

### p1c07 · CDN and blob storage
**Move the bytes closer than the logic. Anything identical for everyone should never touch a machine that thinks.**

- Upload straight to S3 with a signed URL: auth stays at the origin, bytes never
  proxy through your app.
- Cache key design is just "what makes this response different per user".
- Video is chunked so ranges cache independently.

Breaks: per-byte authorization and personalised content. Logic has to run at the
edge or the win disappears.

### p1c08 · Replication
**A replica is a copy that is always behind. The lag is a real number of milliseconds, and someone will read inside it.**

- Write to primary, read from replica, see nothing: read-your-own-writes broken.
  Every fix is "route back to the primary for a window" or carry a version token.
- Failover during lag is data loss, so RPO *is* the lag.
- Synchronous replication buys RPO=0 and charges latency on every write.

Breaks: leaderless quorum systems, where "behind" is per-key rather than one
global timeline.

### p1c09 · Sharding
**Pick a key. Every query that does not carry that key becomes a scatter-gather across all shards.**

- The shard key follows the dominant read.
- Cross-shard joins become a distributed query you now own; transactions stop
  crossing shards cheaply.
- Resharding is the expensive part, which is the entire reason consistent
  hashing exists — move 1/N of the keys instead of all of them.
- Virtual nodes exist because N arcs on a ring come out uneven.

Breaks: skew. Consistent hashing balances **key count**, not **load**. One
celebrity key ruins one shard however good the ring is.

### p1c10 · Consistency and quorums
**R + W > N forces the read set and the write set to share at least one node. That overlap is the whole guarantee.**

- N=3, W=2, R=2 survives one node down on both paths. W=N is fast reads and
  fragile writes.
- A partition forces one choice: answer with maybe-stale data, or refuse to
  answer.
- Partitions are rare; the trade you pay *every millisecond* is latency against
  consistency — the "else" half of PACELC.

Breaks: the overlap proves you **saw** the newest write, not that you can
**identify** it. You still need versioning to pick, and last-write-wins silently
drops concurrent writes.

### p1c11 · Queues
**A queue converts "do it now or fail" into "do it eventually". You bought a buffer, and a buffer has a length you must watch.**

- Queue depth is the leading indicator, not CPU.
- If consumers are slower than producers *on average*, the queue only delays the
  collapse.
- At-least-once is the default, so consumers must be idempotent.
- One poison message blocks the buffer, which is what dead-letter queues are for.
- Ordering holds only inside a partition.

Breaks: work where the user is waiting. There a queue adds latency and hides the
failure.

### p1c12 · Rate limiting
**A limiter is a counter and a clock. Decide what resets the counter and you have already picked the algorithm.**

- Reset on a wall-clock boundary: fixed window, and a 2× burst at the seam.
- Keep every timestamp: sliding log, exact and expensive.
- Refill continuously: token bucket, which permits bursts up to bucket size —
  why it is the default for public APIs.
- Constant drain: leaky bucket, which smooths.

Breaks: distributed limiting. The counter becomes shared state, so every check
is a network hop — accept N× overshoot with local counters, or pay the latency.

### p1c13 · Picking a database
**A database makes one access pattern cheap and everything else expensive. Name the query you will run a million times a second, then pick the engine that made exactly that cheap.**

- KV gets by key and does nothing else.
- Wide-column is partition key plus sort-key range, so you model a table per
  query and duplicate data on purpose.
- Document fetches a whole aggregate by id; search is an inverted index.
- "NoSQL scales better" is the wrong sentence: it scales because it deleted the
  joins and transactions that were expensive to distribute.

Breaks: when the access pattern changes after launch. Relational tolerates
unknown future queries, and that flexibility is precisely what the others sold.

### p1c14 · IDs
**Uniqueness without coordination costs you either bits or ordering. Pick which one you are paying.**

- UUIDv4 buys zero coordination and pays 128 bits plus random B-tree inserts.
- Auto-increment buys perfect ordering and pays a single coordinator.
- Snowflake is time + machine id + sequence: coordinate once, at machine-id
  assignment, and sort by time for free.
- UUIDv7 / ULID put the timestamp in front to restore index locality.

Breaks: clock skew. Snowflake's ordering is only as good as NTP, and a backwards
clock issues duplicates — real implementations refuse to issue during a
backwards jump.

*(This chapter also carries search indexes and locks. Their kernels live at
p3c19 and p2c03.)*

---

## Part 2 — Senior depth

### p2c01 · Distributed transactions
**You cannot write two systems atomically. You can only pick one as truth and make the second write retryable until it lands.**

- Outbox: the row and the event in one local transaction, relayed with retries.
- Dual-writing to a database and a queue is a bug wearing a pattern's name.
- A saga is local transactions plus compensations, because there is no
  cross-service rollback.
- 2PC works and blocks: a coordinator that dies after prepare leaves locks held
  indefinitely.
- A compensation is not a rollback. You cannot un-send the email; you send an
  apology.

Breaks: when both systems are actually one database. People build sagas where a
transaction would have done.

### p2c02 · Idempotency
**Exactly-once delivery does not exist. Exactly-once effect does, and you get it by making the receiver remember what it already did.**

- Store the idempotency key with the **result**, so a retry replays the response
  instead of the work.
- Store it in the same transaction as the effect, or you get the effect without
  the record.
- The dedup retention window is literally how late a retry may safely arrive.
- Ledgers are append-only because inserts replay and mutations do not;
  double-entry makes the invariant checkable after the fact.

Breaks: effects outside your database. Money and email need the remote system to
accept your key (Stripe does). Otherwise the guarantee is not for sale.

### p2c03 · Consensus and fencing
**Consensus is a majority agreeing on an ordered log. A leader, a lock and a config are all just reads of that log.**

- 2f+1 tolerates f failures, so 5 nodes survive 2 and even counts buy nothing.
- Every write costs a round trip to a majority, which caps throughput — hence
  metadata in etcd and data somewhere else.
- Leases expire, which smuggles a clock assumption into leader election.

Breaks: **a lock is a statement about the past.** Between grant and use you may
have been paused for 30 seconds. Only a monotonic fencing token, checked at the
resource, closes that gap.

> Rendered as reel 01.

### p2c04 · CRDT vs OT
**Two people edit offline. Either you rewrite one person's operations against the other's, or you designed the data so order never mattered.**

- Rewriting needs a server to sequence: OT, Google Docs.
- Order-free needs per-character identities that are never reused, so tombstones
  accumulate and documents grow and never shrink: CRDT, offline-first,
  peer-to-peer.

Breaks: neither solves *semantic* conflict. Both converge on the same document;
neither notices the merged sentence is nonsense. Convergence is not intent
preservation.

### p2c05 · Multi-region and cells
**Cross-region is 100ms+ and the link will split. Decide per datum: one home region (everyone far pays), or all regions (they will disagree).**

- Pin user data to a home region and latency plus residency both fall out.
- Read-mostly data (catalog, config) replicates everywhere safely.
- Anything needing a global uniqueness check needs a global coordinator or a
  conflict rule.
- Companion: **a cell is a blast radius. If the failure cannot cross the
  boundary, the outage is 1/N.**

Breaks: a shared global control plane un-cells you. Most large outages are
exactly that — the one component everybody depended on.

### p2c06 · Hot partitions
**Sharding balances keys, not traffic. One key can outgrow one machine, and no hash function fixes that.**

- Discord's Cassandra hot partition, split by time bucket.
- Celebrity fanout-on-write is O(followers), so it goes hybrid: push for normal
  accounts, pull for celebrities.
- Salting (`key#1..N`, read all N) trades read amplification for write spread.

Breaks: salting is a **write**-side fix. If the key is read-hot, cache it —
salting there just multiplies the work. And splitting a key destroys whatever
ordering or atomicity you had inside it.

### p2c07 · Backpressure
**An overloaded system has one honest move: refuse work. Queueing it is refusing it slowly, with the customer still waiting.**

- Unbounded queues turn overload into timeout storms, where every task you
  complete was already abandoned.
- Little's Law: arrival above service rate grows latency without bound.
- Shed at the edge where it is cheapest, and shed by priority — drop the retries
  and the bots, keep the checkouts.
- Breakers stop you tying up threads on a dying dependency and let it recover.
- Retries without jitter and a budget are a DDoS you wrote yourself.

Breaks: work that must not be lost. Payments cannot be shed, so you persist and
process later — and there the queue is correct. The dividing question is always
*is the customer waiting.*

### p2c08 · SLOs
**Pick the number the user feels, promise it, and spend the gap.**

- 99.9% is 43 minutes a month, and that is a **budget you are supposed to
  spend** on releases.
- Burning it fast means freeze; never burning it means you are shipping too
  slowly.
- Alert on burn rate, not on instantaneous errors.
- Percentiles, not averages: a page makes 50 calls, so every user meets your
  tail.

Breaks: rare-catastrophic events. "We corrupted every record" is not a budget
line, and availability arithmetic says nothing about it.

### p2c09 · Stream processing
**Events arrive late and out of order. A watermark is you declaring "I am no longer waiting for anything older than T." Everything else follows from that declaration.**

- Windows close only when the watermark passes them; late data goes to a side
  output or forces a retraction.
- Watermark lag *is* the latency-against-completeness dial.
- Exactly-once sinks need idempotent writes, or a commit tied to the checkpoint.
- Lambda architecture existed because nobody trusted the stream; kappa because
  eventually they did.

Breaks: window on processing time and watermarks become trivial while your
results become wrong on every network hiccup. Also, one idle partition freezes
the watermark for everybody.

### p2c10 · Probabilistic structures
**Trade exactness for space, then check which direction the error runs.**

- Bloom never false-negatives, so it is a pre-filter: "definitely not here, skip
  the disk read" — which is why every LSM engine ships one.
- Count-min only overestimates, so it is safe for "is this over threshold".
- HyperLogLog counts distinct values in kilobytes at ~2% error: fine for a
  dashboard, illegal for billing.
- The **direction** of the error decides where the structure is allowed.
- Companion: **gossip — tell a few random nodes what you know, everyone knows in
  O(log N) rounds, nobody is in charge.**

Breaks: no deletion from a plain Bloom filter, and no probabilistic answer may
ever feed a money or security decision.

### p2c11 · Zero-downtime migrations
**Reader and writer can never change in the same instant. So every migration is: write both, read old, backfill, read new, stop writing old. Four deploys, never two.**

- That is why you cannot rename a column in one deploy.
- The backfill gets throttled because it competes with production.
- Shadow reads compare old against new before you switch.
- Every step reverts independently, which is the entire point.

Breaks: when the two writes span different systems and cannot be atomic. Then it
is CDC/outbox plus reconciliation, not dual write.

---

## Part 0 — the meta-game

### p0c01 · How the interview works
**You are not being graded on the design. You are being graded on whether they would hand you an ambiguous project on Monday.**

- Option-listing reads junior because it hands the decision back to the
  interviewer.
- Find the crux early and spend the time there; breadth-first everywhere is a
  down-level.
- "What breaks at 10×", unprompted, is the senior tell.

Breaks: formats where the arithmetic *is* the grade (Google L5 / NALSD).
Driving without numbers fails there.

---

## Part 3 — cruxes, not kernels

Problem chapters are **compositions**. Their nugget is which constraint
dominates, and each one is really an application of a Part 1/2 kernel:

| chapter | the crux |
|---|---|
| p3c01 URL shortener | the ID scheme (p1c14) |
| p3c02 typeahead | precompute the trie; the read path is a lookup |
| p3c05 news feed | fanout on write against fanout on read (p2c06) |
| p3c06 Uber | geospatial index plus a matching lock (p2c03) |
| p3c08 Ticketmaster | a hold is a distributed lock with an expiry (p2c03) |
| p3c10 global rate limiter | the counter is shared state (p1c12) |
| p3c14 payments | idempotency and the ledger (p2c02) |
| p3c15 Google Docs | OT against CRDT (p2c04) |
| p3c17 build Kafka | the log is the truth |
| p3c19 search | the inverted index is a map from term to posting list |
| p3c22 stock exchange | single-threaded matching, because ordering is the product |
| p3c23 LLM serving | the KV cache is the memory bottleneck; continuous batching is the throughput fix |

Different altitude. Worth writing out properly once the 25 above are validated.

---

## Weakest three, attack first

- **p1c14** bundles IDs, search indexes and locks; the kernel only covers IDs.
- **p2c05** is two kernels wearing one coat (regions, and blast radius).
- **p2c10** pairs Bloom filters with gossip, which have nothing to do with each
  other. The chapter is a junk drawer and the kernel inherits it.
