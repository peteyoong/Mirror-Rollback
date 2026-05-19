"""
Longitudinal Pattern Memory
============================

Build marker: pattern-memory-v1

Longitudinal reflective intelligence.  Separate from conversation memory
(short-term continuity) — this layer notices when the SAME theme returns
across days/weeks/months.

What it does NOT do:
    * Store transcripts.  Ever.
    * Store anything in the user's own words.  Ever.
    * Quote past sessions verbatim back to the user.  Ever.

What it DOES do:
    * Tag the current turn with abstracted PATTERN KEYS
      (e.g. "work_exhaustion", "authority_conflict", "child_distance",
      "self_worth_questioning", "avoidance_pattern", "identity_question").
    * Upsert a compact record per (user_id, pattern_key) with first/last
      seen, occurrence count, a small ring buffer of timestamps, the lens
      / intensity / domain contexts it has surfaced in, and peak intensity.
    * Score recency-aware confidence: weak / moderate / strong.
    * Surface moderate / strong patterns to the LLM via a PATTERN MEMORY
      system-prompt block — with explicit instructions to use probabilistic
      language and NEVER quote past sessions.
    * Detect GROWTH SHIFTS: a previously high-intensity pattern returning
      now at SOFT or OBSERVATIONAL with enough history to call it growth.

NB: a different module `services/pattern_memory.py` exists for an unrelated
scene-opening / pattern-exposure system.  Keep them distinct.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 1.  Pattern taxonomy
# ---------------------------------------------------------------------------

_PATTERN_DEFS: Dict[str, Tuple[str, List[str]]] = {
    # --- Work ---
    "work_exhaustion": ("work", [
        r"\bburn(?:ed|t)?\s*out\b", r"\bburnout\b", r"\bexhausted\b",
        r"\boverworked\b", r"\bdrained\b",
        r"\bcan'?t keep up\b", r"\bworked too hard\b",
    ]),
    "career_direction": ("work", [
        r"\bwrong (job|career|path)\b", r"\bwhat (am i|i'?m) (even )?doing\b",
        r"\bmeaning(ful|less) work\b", r"\bsoul-?sucking\b",
        r"\bcareer (crisis|pivot|change)\b",
    ]),
    "authority_conflict": ("work", [
        r"\bmy boss\b.{0,40}\b(annoying|unfair|impossible|controlling|micromanag|dismiss|toxic|cold|harsh)\b",
        r"\b(boss|manager)\s+(?:always|never|keeps|won'?t)\b",
        r"\bmicromanag\w*\b", r"\b(undermined|sidelined|overlooked) at work\b",
    ]),

    # --- Relationships ---
    "relational_distance": ("relationships", [
        r"\bfeel(?:ing)?(?:\s+\w+){0,3}\s+distant\b",
        r"\bdrifting apart\b", r"\bdon'?t connect\b",
        r"\bwe (?:hardly )?talk anymore\b", r"\b(?:emotionally )?disconnected\b",
        r"\bcold and distant\b", r"\bdistant from (?:my |him|her|them|us)\w*\b",
    ]),
    "attachment_anxiety": ("relationships", [
        r"\b(?:abandon(?:ed|ment)|leaving me|will leave me)\b",
        r"\b(?:clingy|needy|too much)\b",
        r"\bafraid (?:of being |to be )?alone\b",
    ]),
    "intimacy_block": ("relationships", [
        r"\bcan'?t open up\b", r"\bcan'?t let (people|anyone) in\b",
        r"\bemotional(?:ly)? unavailable\b", r"\bshut down emotionally\b",
        r"\bvulnerab(?:le|ility) (?:is hard|terrifies)\b",
    ]),

    # --- Family ---
    "parental_pattern": ("family", [
        r"\bmy (mom|mum|dad|mother|father|parents?)\b.{0,60}\b(?:always|never|keeps|won'?t|cold|cri(?:tical|ticise)|harsh|dismiss|absent)\b",
        r"\bdaddy issues?\b", r"\bmommy issues?\b",
        r"\bparental (wound|pattern|dynamic)\b",
    ]),
    "child_distance": ("family", [
        r"\bmy (kid|child|son|daughter)\b.{0,60}\b(?:distant|avoidant|withdrawn|shuts? down|pulled away|won'?t talk)\b",
        r"\bdrifting from my (kid|child|son|daughter)\b",
    ]),
    "sibling_friction": ("family", [
        r"\bmy (sister|brother|sibling)\b.{0,60}\b(?:competitive|cold|distant|jealous|harsh|critical)\b",
    ]),

    # --- Self / Identity ---
    "identity_question": ("self", [
        r"\bwho am i\b", r"\bwhat do i really want\b",
        r"\bdon'?t know who i am\b", r"\blost myself\b",
        r"\bidentity (?:crisis|shift|question)\b",
    ]),
    "self_worth_questioning": ("self", [
        r"\bnot good enough\b", r"\bnot enough\b", r"\bnever enough\b",
        r"\bimposter\b", r"\bdon'?t deserve\b",
        r"\bworthless\b", r"\bhate myself\b",
    ]),
    "avoidance_pattern": ("self", [
        r"\bavoiding\b", r"\bputting (?:it|that|this) off\b",
        r"\bprocrastinat(?:e|ing|ion)\b",
        r"\bcan'?t bring myself to\b",
    ]),
    "people_pleasing": ("self", [
        r"\bpeople[- ]pleas(?:e|er|ing)\b", r"\bcan'?t say no\b",
        r"\balways (?:helping|saying yes|doing for others)\b",
        r"\bover-?giving\b", r"\bover-?functioning\b",
    ]),
    "perfectionism": ("self", [
        r"\bperfectionis(?:m|t)\b", r"\bnever (?:done|finished|enough)\b",
        r"\bgot to be perfect\b",
    ]),
    "control_pattern": ("self", [
        r"\b(?:need to|have to) control\b", r"\bcontrolling\b",
        r"\blet go (?:is hard|of control)\b",
    ]),

    # --- Emotional ---
    "shutdown_pattern": ("emotional", [
        r"\bshut(?:s|ting)? down\b", r"\bgo(?:ing)? numb\b",
        r"\bcheck(?:ed|ing) out\b", r"\bdissociate\b",
    ]),
    "anxiety_loop": ("emotional", [
        r"\banxious\b", r"\banxiety spiral\b",
        r"\bcan'?t stop (worrying|thinking)\b",
        r"\boverthinking\b", r"\bracing thoughts\b",
    ]),
    "grief_processing": ("emotional", [
        r"\bgrief\b", r"\bgrieving\b", r"\bmourning\b",
        r"\bcan'?t stop crying\b",
    ]),
    "anger_pattern": ("emotional", [
        r"\bso angry\b", r"\bfurious\b", r"\bresentful\b", r"\bbitter\b",
    ]),
}

_COMPILED_PATTERNS: Dict[str, Tuple[str, re.Pattern]] = {
    key: (cat, re.compile("|".join(triggers), re.IGNORECASE))
    for key, (cat, triggers) in _PATTERN_DEFS.items()
}


# ---------------------------------------------------------------------------
# 2.  Detection
# ---------------------------------------------------------------------------

def detect_pattern_tags(user_message: str) -> List[Tuple[str, str]]:
    """Return [(pattern_key, category)] for every pattern triggered.  Pure."""
    if not user_message:
        return []
    found: List[Tuple[str, str]] = []
    for key, (cat, regex) in _COMPILED_PATTERNS.items():
        if regex.search(user_message):
            found.append((key, cat))
    return found


# ---------------------------------------------------------------------------
# 3.  Recurrence + growth
# ---------------------------------------------------------------------------

def score_recurrence(record: Dict[str, Any], now: Optional[datetime] = None) -> str:
    """weak (1 in 30d) / moderate (≥2) / strong (≥3).  Only moderate+ are surfaced."""
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)
    recent = record.get("recent_seen_at") or []
    fresh = []
    for t in recent:
        if isinstance(t, datetime):
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            if t >= cutoff:
                fresh.append(t)
    if len(fresh) >= 3:
        return "strong"
    if len(fresh) >= 2:
        return "moderate"
    return "weak"


# narrative-flexibility-v1
def score_fatigue(record: Dict[str, Any], now: Optional[datetime] = None) -> str:
    """
    How many times has THIS pattern been SURFACED to the LLM recently?
    Returns "low" | "med" | "high".
    high  → suppress surfacing this turn (prevents identity locking)
    med   → soften framing ("this thread is known")
    low   → fresh enough to surface normally
    """
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=_FATIGUE_RECENT_SURFACINGS_WINDOW_DAYS)
    surf = record.get("recent_surfaced_at") or []
    fresh = []
    for t in surf:
        if isinstance(t, datetime):
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            if t >= cutoff:
                fresh.append(t)
    if len(fresh) >= _FATIGUE_THRESHOLD_HIGH:
        return "high"
    if len(fresh) >= _FATIGUE_THRESHOLD_MED:
        return "med"
    return "low"


_INTENSITY_RANK = {"SOFT": 0, "OBSERVATIONAL": 1, "DIRECT": 2, "CONFRONTING": 3}


def detect_growth_shift(record: Dict[str, Any], current_intensity: str) -> bool:
    """Pattern previously surfaced DIRECT+ now returning SOFT/OBSERVATIONAL."""
    peak = record.get("peak_intensity") or "OBSERVATIONAL"
    if _INTENSITY_RANK.get(peak, 1) >= _INTENSITY_RANK["DIRECT"]:
        if _INTENSITY_RANK.get(current_intensity, 1) <= _INTENSITY_RANK["OBSERVATIONAL"]:
            if (record.get("occurrence_count") or 0) >= 3:
                return True
    return False


# ---------------------------------------------------------------------------
# 4.  Storage helpers
# ---------------------------------------------------------------------------

PATTERN_MEMORY_COLLECTION = "longitudinal_pattern_memory"
_RECENT_BUFFER_SIZE = 10

# narrative-flexibility-v1 — pattern fatigue thresholds.
# When the same pattern has been SURFACED to the LLM too many times recently,
# we suppress it / soften the framing.  Distinct from `occurrence_count`
# which counts user-mentions; this counts agent-surfacings.
_FATIGUE_RECENT_SURFACINGS_WINDOW_DAYS = 14
_FATIGUE_THRESHOLD_HIGH = 3   # ≥3 surfacings in 14d → SUPPRESS this turn
_FATIGUE_THRESHOLD_MED  = 2   # 2 surfacings → SOFTEN framing ("you know this thread")


async def upsert_pattern_occurrence(
    db,
    user_id: str,
    pattern_key: str,
    category: str,
    lens: Optional[str],
    intensity: Optional[str],
    domain: Optional[str],
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Upsert a single pattern occurrence.  Never stores raw text."""
    now = now or datetime.now(timezone.utc)
    coll = db[PATTERN_MEMORY_COLLECTION]

    existing = await coll.find_one({"user_id": user_id, "pattern_key": pattern_key})

    if existing:
        recent = (existing.get("recent_seen_at") or []) + [now]
        recent = recent[-_RECENT_BUFFER_SIZE:]
        lens_ctx = list(set((existing.get("lens_contexts") or []) + ([lens] if lens else [])))[:6]
        int_ctx = list(set((existing.get("intensity_contexts") or []) + ([intensity] if intensity else [])))[:6]
        dom_ctx = list(set((existing.get("domain_contexts") or []) + ([domain] if domain else [])))[:6]
        old_peak = existing.get("peak_intensity") or intensity or "OBSERVATIONAL"
        peak = old_peak
        if intensity and _INTENSITY_RANK.get(intensity, 1) > _INTENSITY_RANK.get(old_peak, 1):
            peak = intensity
        growth_count = existing.get("growth_shifts_count") or 0
        if detect_growth_shift(existing, intensity or "OBSERVATIONAL"):
            growth_count += 1
        update = {
            "last_seen_at": now,
            "occurrence_count": (existing.get("occurrence_count") or 1) + 1,
            "recent_seen_at": recent,
            "lens_contexts": lens_ctx,
            "intensity_contexts": int_ctx,
            "domain_contexts": dom_ctx,
            "last_observed_intensity": intensity or "OBSERVATIONAL",
            "peak_intensity": peak,
            "growth_shifts_count": growth_count,
            "category": category,
        }
        await coll.update_one({"_id": existing["_id"]}, {"$set": update})
        existing.update(update)
        return existing

    doc = {
        "user_id": user_id,
        "pattern_key": pattern_key,
        "category": category,
        "first_seen_at": now,
        "last_seen_at": now,
        "occurrence_count": 1,
        "recent_seen_at": [now],
        "lens_contexts": [lens] if lens else [],
        "intensity_contexts": [intensity] if intensity else [],
        "domain_contexts": [domain] if domain else [],
        "last_observed_intensity": intensity or "OBSERVATIONAL",
        "peak_intensity": intensity or "OBSERVATIONAL",
        "growth_shifts_count": 0,
    }
    await coll.insert_one(doc)
    return doc


async def record_pattern_surfacing(
    db,
    user_id: str,
    pattern_keys: List[str],
    now: Optional[datetime] = None,
) -> None:
    """
    narrative-flexibility-v1 — record that we SURFACED these patterns to the
    LLM this turn.  Separate from occurrence_count (user-mentions).  Used by
    `score_fatigue()` next turn to prevent identity locking.
    """
    if not pattern_keys:
        return
    now = now or datetime.now(timezone.utc)
    coll = db[PATTERN_MEMORY_COLLECTION]
    for key in pattern_keys:
        try:
            doc = await coll.find_one({"user_id": user_id, "pattern_key": key})
            if not doc:
                continue
            buf = (doc.get("recent_surfaced_at") or []) + [now]
            buf = buf[-_RECENT_BUFFER_SIZE:]
            await coll.update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    "recent_surfaced_at": buf,
                    "last_surfaced_at": now,
                    "surfaced_count": (doc.get("surfaced_count") or 0) + 1,
                }},
            )
        except Exception:
            pass


async def fetch_pattern_records(db, user_id: str, pattern_keys: List[str]) -> List[Dict[str, Any]]:
    if not pattern_keys:
        return []
    cursor = db[PATTERN_MEMORY_COLLECTION].find(
        {"user_id": user_id, "pattern_key": {"$in": pattern_keys}},
        {"_id": 0},
    )
    return await cursor.to_list(length=len(pattern_keys))


# ---------------------------------------------------------------------------
# 5.  Prompt block
# ---------------------------------------------------------------------------

_PATTERN_PHRASING: Dict[str, str] = {
    "work_exhaustion":        "a recurring sense of being depleted by work",
    "career_direction":       "a recurring question about whether the current path is right",
    "authority_conflict":     "a recurring friction with authority / boss figures",
    "relational_distance":    "a recurring sense of distance in close relationships",
    "attachment_anxiety":     "a recurring fear of being left or abandoned",
    "intimacy_block":         "a recurring difficulty opening up emotionally",
    "parental_pattern":       "a recurring dynamic with the parental field",
    "child_distance":         "a recurring distance with the user's child",
    "sibling_friction":       "a recurring friction with a sibling",
    "identity_question":      "a recurring question of identity / who-am-I",
    "self_worth_questioning": "a recurring undercurrent of not-enough-ness",
    "avoidance_pattern":      "a recurring pattern of avoidance / putting things off",
    "people_pleasing":        "a recurring pull to over-give / not say no",
    "perfectionism":          "a recurring pull toward perfectionism",
    "control_pattern":        "a recurring need-to-control pattern",
    "shutdown_pattern":       "a recurring shutdown response under pressure",
    "anxiety_loop":           "a recurring anxiety / overthinking loop",
    "grief_processing":       "a recurring grief layer surfacing again",
    "anger_pattern":          "a recurring anger / resentment thread",
}


def _humanise_recency(dt: Optional[datetime]) -> str:
    if not dt:
        return "unknown"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - dt
    days = delta.days
    if days < 1: return "today"
    if days < 2: return "yesterday"
    if days < 7: return f"{days} days ago"
    if days < 30: return f"{days // 7} week{'s' if days // 7 > 1 else ''} ago"
    if days < 365: return f"{days // 30} month{'s' if days // 30 > 1 else ''} ago"
    return f"{days // 365} year{'s' if days // 365 > 1 else ''} ago"


def format_pattern_memory_block(
    surfaceable: List[Dict[str, Any]],
    growth_shifts: List[Dict[str, Any]],
    softened_keys: Optional[List[str]] = None,
) -> str:
    """Build the PATTERN MEMORY system-prompt block (empty if nothing to surface)."""
    softened_keys = softened_keys or []
    if not surfaceable and not growth_shifts:
        return ""

    lines: List[str] = [
        "--- PATTERN MEMORY (pattern-memory-v1) ---",
        "Longitudinal recurrence — patterns that have surfaced before in",
        "this user's reflection across days/weeks/months.  No transcripts",
        "are stored; only abstracted pattern tags.",
        "",
    ]
    if surfaceable:
        lines.append("Recurring patterns relevant to this turn:")
        for p in surfaceable:
            phrasing = _PATTERN_PHRASING.get(p["pattern_key"], p["pattern_key"].replace("_", " "))
            conf = p.get("confidence", "moderate")
            soften_marker = " [SOFTEN: already named recently — assume the user knows]" if p["pattern_key"] in softened_keys else ""
            lines.append(
                f"  - {phrasing}  (recurrence: {conf}; "
                f"first surfaced ~{_humanise_recency(p.get('first_seen_at'))}, "
                f"last surfaced ~{_humanise_recency(p.get('last_seen_at'))}){soften_marker}"
            )
        lines.append("")
    if growth_shifts:
        lines.append("Possible growth shifts (a previously intense pattern is")
        lines.append("returning at lower charge):")
        for p in growth_shifts:
            phrasing = _PATTERN_PHRASING.get(p["pattern_key"], p["pattern_key"].replace("_", " "))
            lines.append(
                f"  - {phrasing}  (now: {p.get('last_observed_intensity')}, "
                f"peak was: {p.get('peak_intensity')})"
            )
        lines.append("")
        lines.append("If a growth shift is listed above, you MUST gently name it in")
        lines.append("your reply.  One short line is enough: 'something feels less")
        lines.append("charged this time', 'there's a different quality here than")
        lines.append("before', 'this returns with less weight'.  Then continue the")
        lines.append("answer.  Do NOT over-celebrate.  Do NOT skip the recognition.")
        lines.append("")
    lines.extend([
        "RULES — pattern memory surfacing:",
        "  1. NEVER quote past sessions.  NEVER say 'on [date] you said'.",
        "  2. NEVER use absolutist language ('you always', 'you never').",
        "  3. PREFER probabilistic phrasing: 'this seems to return',",
        "     'this resembles an earlier thread', 'there is a recurring",
        "     pull between…', 'this tension has surfaced before'.",
        "  4. ONLY weave a recurrence in when it sharpens the current",
        "     answer.  Do NOT lecture.  Do NOT tour the patterns.",
        "  5. Growth shifts: name gently.  'Something has shifted' is",
        "     enough.  Do not over-celebrate.",
        "  6. Recognisable, not creepy.  Avoid surveillance tone.",
        "  7. (narrative-flexibility-v1) For patterns marked [SOFTEN]:",
        "     do NOT re-explain the pattern.  Assume the user knows it.",
        "     Focus on what is DIFFERENT this time, what is CHANGING, or",
        "     what the current question is asking that the pattern hasn't",
        "     answered before.",
    ])
    return "\n".join(lines)


# narrative-flexibility-v1 — universal anti-locking addendum.
# Injected even when no patterns matched — so the LLM keeps openness as
# a baseline, not just when pattern memory is loud.
_ANTI_LOCKING_BLOCK = """\
--- NARRATIVE FLEXIBILITY (narrative-flexibility-v1) ---
Anti-identity-locking rules (apply at every turn):

  1. PATTERNS, NOT IDENTITY
     Patterns are dynamic, contextual, evolving.  They are not who the
     user IS.  Avoid "you are an X kind of person".  Prefer:
       - "This pattern seems to emerge under these conditions."
       - "Under pressure, this is what tends to surface."
       - "In this kind of relational field, this often shows up."

  2. CONTRADICTION TOLERANCE
     Humans are not internally consistent.  If the user says one thing
     today and the opposite tomorrow — hold both without trying to
     collapse them into one coherent theory.  Phase shifts are real.

  3. CONTEXTUAL FRAMING
     Recurrence does not mean determinism.  Always anchor a pattern in
     the conditions it appears in — not in the person themselves.

  4. GROWTH OVER PATHOLOGY
     Look for adaptation, flexibility, new responses, softened
     reactions, increased awareness.  Do not only re-narrate the
     repeated wound.

  5. ALTERNATIVE FRAMINGS
     Even with strong recurrence, occasionally offer a different angle
     ("another way to read this is…") rather than always confirming the
     same narrative.

  6. RELATIONAL ANTI-LOCKING
     For spouses, children, ex-partners, cofounders: NEVER assign a
     fixed narrative to the other person.  Stay probabilistic, contextual,
     field-aware.  The other person is also changing.

  7. WHAT IS ALIVE NOW
     The highest form of reflection is not "this is who you are."
     It is "this is what seems alive right now."  Bias your interpretation
     toward what is moving / shifting / changing — not toward what is fixed.
"""


def format_anti_locking_block() -> str:
    return _ANTI_LOCKING_BLOCK


# ---------------------------------------------------------------------------
# 6.  Public one-call API
# ---------------------------------------------------------------------------

async def process_pattern_memory(
    db,
    user_id: str,
    user_message: str,
    lens: Optional[str],
    intensity_mode: Optional[str],
    domain: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    1. Detect pattern tags in the current message.
    2. Upsert occurrences (storage is small, no transcripts).
    3. Score recurrence + detect growth.
    4. Format the PATTERN MEMORY system-prompt block.
    Returns (block_text, debug_payload).
    """
    debug: Dict[str, Any] = {
        "marker": "pattern-memory-v1",
        "matched_patterns": [],
        "surfaceable_count": 0,
        "growth_shifts_count": 0,
        "surfaced_keys": [],
        "growth_keys":   [],
    }

    tags = detect_pattern_tags(user_message)
    matched_keys = [k for (k, _) in tags]

    for key, cat in tags:
        try:
            await upsert_pattern_occurrence(
                db=db, user_id=user_id, pattern_key=key, category=cat,
                lens=lens, intensity=intensity_mode, domain=domain,
            )
        except Exception:
            # Pattern memory must NEVER crash the chat.
            pass

    if not matched_keys:
        # narrative-flexibility-v1 — even when no patterns fired, inject
        # the anti-locking universal addendum so the LLM stays open.
        return format_anti_locking_block(), debug

    records = await fetch_pattern_records(db, user_id, matched_keys)

    surfaceable: List[Dict[str, Any]] = []
    growth_shifts: List[Dict[str, Any]] = []
    suppressed_keys: List[str] = []
    softened_keys: List[str] = []
    for rec in records:
        conf = score_recurrence(rec)
        fatigue = score_fatigue(rec)
        rec["confidence"] = conf
        rec["fatigue"] = fatigue
        debug["matched_patterns"].append({
            "pattern_key": rec["pattern_key"],
            "category": rec.get("category"),
            "confidence": conf,
            "fatigue": fatigue,
            "occurrence_count": rec.get("occurrence_count"),
            "surfaced_count": rec.get("surfaced_count", 0),
        })
        # narrative-flexibility-v1 — fatigue filtering.
        # HIGH fatigue → suppress this turn entirely (prevents identity locking).
        # MED fatigue → still surface but with a "soften" flag.
        if conf in ("moderate", "strong"):
            if fatigue == "high":
                suppressed_keys.append(rec["pattern_key"])
            else:
                if fatigue == "med":
                    softened_keys.append(rec["pattern_key"])
                surfaceable.append(rec)
        # Growth shifts bypass fatigue — celebrating change is always OK.
        if detect_growth_shift(rec, intensity_mode or "OBSERVATIONAL"):
            growth_shifts.append(rec)

    debug["surfaceable_count"] = len(surfaceable)
    debug["growth_shifts_count"] = len(growth_shifts)
    debug["surfaced_keys"] = [p["pattern_key"] for p in surfaceable]
    debug["growth_keys"]   = [p["pattern_key"] for p in growth_shifts]
    debug["suppressed_due_to_fatigue"] = suppressed_keys
    debug["softened_due_to_fatigue"] = softened_keys

    # Record surfacings so future turns can fatigue them out.
    surfaced_keys = [p["pattern_key"] for p in surfaceable] + [p["pattern_key"] for p in growth_shifts]
    if surfaced_keys:
        await record_pattern_surfacing(db, user_id, surfaced_keys)

    block = format_pattern_memory_block(surfaceable, growth_shifts, softened_keys=softened_keys)
    # Always append the anti-locking universal addendum.
    block = (block + "\n\n" + format_anti_locking_block()) if block else format_anti_locking_block()
    return block, debug
