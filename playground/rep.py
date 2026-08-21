"""The one rep this service knows, ported from sell/lib/rep.ts.

Python cannot import TypeScript, so this is a second copy. test_personas.py
parses rep.ts and fails if the two ever disagree. Change one, change both.
"""

REP_TITLE = "p1c06 · cache-aside read path"

KERNEL = (
    "Cache-aside: the app asks the cache first. On a miss the cache does not "
    "fetch anything — it just says no. The app queries the database itself, the "
    "rows come back to the app rather than to the cache, and the app writes the "
    "cache with a TTL. That is what 'aside' means: the cache is a dumb box the "
    "application manages, not a layer that sits in front of the database."
)

# Verbatim from RUBRIC in sell/lib/rep.ts, in order. The drift test compares
# these character for character.
RUBRIC_LABELS = [
    "GET from the cache first",
    "the miss comes back to the app",
    "the app queries the database",
    "rows return to the app, not the cache",
    "the app writes the cache itself",
    "a TTL on the write",
]

# Verbatim from PROBES in sell/lib/rep.ts. Curly apostrophes and quotes are
# intentional — they are what the file contains, and the coach's credibility is
# that it says what the book says.
PROBES = [
    {
        "q": "Step 2 was a miss. Why didn’t the cache go and fetch it for you?",
        "a": "Because cache-aside puts the app in charge, not the cache. The cache is a dumb key-value box that answers hit or miss and nothing else. That is exactly why it is resilient: when the cache dies, reads get slower but they still work, because the fallback path is already the normal path. A read-through cache would have fetched it for you, and taken the database down with it when it failed.",
    },
    {
        "q": "Between step 2 and step 5, another server updates that product and deletes the key. What is in your cache after step 5?",
        "a": "Stale data, and it sits there wrong until the TTL expires. Your step 5 writes rows that were true at step 2. The delete happened in between, so it deleted nothing, and then you refilled the key with the old value. This is the race at the heart of cache invalidation, and it is why the TTL is not optional decoration: it is the only thing that eventually saves you.",
    },
    {
        "q": "Your hit rate is 99%. The cache dies. What happens to the database?",
        "a": "It takes 100× its normal read load, instantly, and almost certainly falls over. The better your hit rate, the more catastrophic losing the cache becomes. Success is what created the fragility. A 99% hit rate means the database was only ever sized for 1% of real traffic. This is why you load-test with the cache cold, and why “the cache is just an optimisation” stops being true the moment you depend on it.",
    },
]
