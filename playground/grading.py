"""The grading pass: one post-round LLM call that turns a transcript into a
failure map. The answer key (rep.KERNEL / RUBRIC / PROBES) is allowed here
and only here -- the same seam where the coach gets it in a sprint session.

Every quote is checked verbatim against the transcript in code, not trusted
from the model: an invented quote on a sales surface is the repo's standing
"never claim what the product does not do" rule broken in the visitor's own
mouth. Failures are dropped, never rendered.
"""

import json
import logging

from playground import rep

logger = logging.getLogger(__name__)

# Hand-curated: the model picks a gap_area key from this table; it does not
# mint URLs. Anchors are the free book's own hash routes (dist/book uses
# #ch/<chapter-id> -- see src/toc.json for ids).
GAP_CHAPTERS = {
    "cache_aside_vs_read_through": "/book/#ch/p1c06",
    "invalidation_race": "/book/#ch/p1c06",
    "ttl_reasoning": "/book/#ch/p1c06",
    "cold_cache_failover": "/book/#ch/p2c07",
    "stampede": "/book/#ch/p2c06",
    "capacity_numbers": "/book/#ch/p1c04",
}


def transcript_text(turns: list) -> str:
    """The candidate's words, in order, and nothing else. Turns come out of a
    live LLMContext, so content may be a string, a parts list, or missing --
    none of those may crash a grading pass."""
    out = []
    for turn in turns:
        if not isinstance(turn, dict) or turn.get("role") != "user":
            continue
        content = turn.get("content")
        if isinstance(content, str):
            out.append(content)
        elif isinstance(content, list):
            out.extend(
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("text")
            )
    return "\n".join(s for s in out if s)


def build_grading_messages(turns: list, board_text: str) -> list[dict]:
    system = (
        "You are grading one short system-design interview round on: "
        f"{rep.REP_TITLE}.\n\n"
        f"The chapter says: {rep.KERNEL}\n\n"
        "A complete answer contains all of these:\n"
        + "\n".join(f"- {label}" for label in rep.RUBRIC_LABELS)
        + "\n\nThe follow-ups a strong candidate can answer:\n"
        + "\n".join(f"- Q: {p['q']}\n  A: {p['a']}" for p in rep.PROBES)
        + "\n\nFind the moments where this candidate would have been cut in a "
        "real loop. Return JSON only: an object with key moments, a list of "
        "at most 3 objects, each with string keys quote, probe, gap, "
        "gap_area.\n\n"
        "Rules:\n"
        "- At most 3 moments, and ONLY moments the transcript actually "
        "supports. Fewer is fine. An empty list is fine.\n"
        "- quote: the candidate's words, copied verbatim from the transcript. "
        "Never paraphrase, never invent.\n"
        "- probe: what was being pressed on, one line.\n"
        "- gap: the miss, named plainly, one line.\n"
        "- gap_area: exactly one of: " + ", ".join(GAP_CHAPTERS) + "."
    )
    user = "Transcript (candidate's words only):\n" + transcript_text(turns)
    if board_text:
        user += "\n\nFinal whiteboard:\n" + board_text
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def parse_and_check(raw: str, transcript: str) -> list[dict] | None:
    """None means the model's output was unusable (caller may retry). A list
    -- possibly empty -- is a valid map: every surviving moment has a
    verbatim quote and a chapter URL resolved from GAP_CHAPTERS."""
    try:
        payload = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(payload, dict) or not isinstance(payload.get("moments"), list):
        return None
    kept = []
    for moment in payload["moments"][:3]:
        if not isinstance(moment, dict):
            continue
        quote = moment.get("quote")
        probe = moment.get("probe")
        gap = moment.get("gap")
        area = moment.get("gap_area")
        if not all(isinstance(v, str) and v.strip() for v in (quote, probe, gap, area)):
            continue
        if quote not in transcript:
            continue  # invented or paraphrased: dropped, never rendered
        chapter = GAP_CHAPTERS.get(area)
        if chapter is None:
            continue  # the model does not mint URLs
        kept.append({"quote": quote, "probe": probe, "gap": gap, "chapter": chapter})
    return kept
