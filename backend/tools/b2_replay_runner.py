"""b2_replay_runner.py — Mirror Chat V2 Slice B2 shadow telemetry replay.

Pulls real user messages from `chat_history`, `forum_chat_messages`, and
`forum_mirror_chat_messages` over the last N days, optionally
supplements with synthetic cases from
`tests/intent_router_v2/golden_set_pete_mel_historical.yaml` (only the
`source: synth` rows), then runs every message through the V2 shadow
stack (`intent_router_v2` + `relationship_router_v2` +
`retrieval_validation_v1.build_receipt`).

Produces:
  * /app/backend/audit_reports/B2_REPLAY_RESULTS.json — full per-case
    rows + aggregate metrics, sliced by source(real/synth) and category.
  * /app/backend/audit_reports/B2_REPLAY_SAMPLES.md  — representative
    success cases + representative failure cases for the readiness
    report appendix.

NOTE: shadow only.  Never writes to mirror_chat_retrieval_receipts here
(this is a *replay* of historical messages, not a live ingest).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone as dt_tz
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(BACKEND_DIR / ".env")

import yaml  # noqa: E402
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from services.intent_router_v2 import classify_intent_v2, ROUTER_VERSION as INTENT_VER  # noqa: E402
from services.relationship_router_v2 import (  # noqa: E402
    resolve_relationship_context,
    ROUTER_VERSION as REL_VER,
)
from services.retrieval_validation_v1 import (  # noqa: E402
    build_receipt,
    mandatory_modules,
    VALIDATOR_VERSION,
)

OUT_DIR = BACKEND_DIR / "audit_reports"
RESULTS_JSON = OUT_DIR / "B2_REPLAY_RESULTS.json"
SAMPLES_MD = OUT_DIR / "B2_REPLAY_SAMPLES.md"
SYNTH_YAML = BACKEND_DIR / "tests" / "intent_router_v2" / "golden_set_pete_mel_historical.yaml"

DEFAULT_WINDOW_DAYS = 90
TARGET_TOTAL_LOW = 100
TARGET_TOTAL_HIGH = 150


CATEGORY_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("relationship",     re.compile(r"\b(mel|wife|husband|partner|spouse|marriage|us|we|relationship|relating)\b", re.I)),
    ("forum_member",     re.compile(r"\b(forum|group|member|room|cohort|circle)\b", re.I)),
    ("career_founder",   re.compile(r"\b(ceo|founder|board|team|fundraise|runway|role|vp|company|leader|product|engineering)\b", re.I)),
    ("lens_jargon",      re.compile(r"\b(saturn|venus|mars|jupiter|pluto|mercury|node|house|chart|gate|channel|profile|authority|enneagram|human design|astrology|numerology|bazi)\b", re.I)),
    ("identity_growth",  re.compile(r"\b(show up|naturally|am i|who am i|patterns?|growth|stuck|cycle|season)\b", re.I)),
]

# Heuristic patterns used by the sub-bucket classifiers below.
_RELATIONSHIP_KW_RE = re.compile(
    r"\b(mel|wife|husband|partner|spouse|marriage|us|we|her|him|relationship|"
    r"between\s+\w+\s+and|together|fight|distant|connection|conflict)\b", re.I)
_FORUM_KW_RE = re.compile(
    r"\b(forum|group|room|cohort|circle|members?|together|we|us|our|this room|"
    r"this group|this forum|the team)\b", re.I)
_SELF_ONLY_RE = re.compile(
    r"^\s*(how\s+(do|am|can)\s+i|am\s+i|why\s+(do|am)\s+i|what'?s\s+my|tell\s+me\s+about\s+my)",
    re.I)


def _classify_forum_member_unresolved(row: Dict[str, Any]) -> str:
    """Classify why a forum/member-frame message did NOT resolve a target.

    Mutually exclusive; first-match-wins priority order:
      1. wrong_person_selected  — explicit_target_id was set but the
                                  resolver couldn't match it in saved_people
                                  (mis-binding / stale id)
      2. forum_to_member_misroute — frame=forum, message names a specific
                                  person, but no member binding emerged
                                  (router should have picked a member)
      3. relationship_to_self_downgrade — frame=forum/member AND clear
                                  relational keywords present, but the
                                  intent envelope's primary_domain is
                                  NOT relationship/family/parenting (the
                                  relational signal was lost downstream)
      4. wrong_frame_selected   — frame=forum/member but the message is
                                  self-oriented (1P singular phrasing,
                                  no forum/group/member keywords, no
                                  proper-name candidate).  Frame was
                                  probably mis-derived upstream.
      5. unclassified_unresolved — catch-all.
    """
    msg = row.get("message") or ""
    frame = row.get("active_frame")
    predicted = row.get("predicted_domain")
    explicit_target = row.get("explicit_target_id")
    has_proper_name = bool(row.get("rel_target_unresolved_name"))
    has_rel_kw = bool(_RELATIONSHIP_KW_RE.search(msg))
    has_forum_kw = bool(_FORUM_KW_RE.search(msg))
    looks_self_only = bool(_SELF_ONLY_RE.search(msg))

    if explicit_target and not row.get("rel_target_resolved"):
        return "wrong_person_selected"
    if frame == "forum" and has_proper_name:
        return "forum_to_member_misroute"
    if has_rel_kw and predicted not in ("relationship", "family", "parenting"):
        return "relationship_to_self_downgrade"
    if not has_rel_kw and not has_forum_kw and not has_proper_name and looks_self_only:
        return "wrong_frame_selected"
    return "unclassified_unresolved"


def _classify_unresolved_named(row: Dict[str, Any]) -> str:
    """Classify why an UNRESOLVED_NAMED row didn't bind to a saved person.

    Mutually exclusive; first-match-wins:
      1. resolver_miss        — saved_people loaded BUT a similar name
                                exists (substring or shared 4+ char prefix).
                                Signals fuzzy/typo failure in the resolver.
      2. ambiguous_match      — multiple proper-name candidates in the
                                message (router picked one arbitrarily).
      3. forum_only_member    — frame=forum/member AND a proper name was
                                detected; the named person is likely a
                                forum-only member not in saved_people.
      4. true_missing_person  — name truly not present anywhere
                                (saved_people was empty in this replay
                                row, OR the name is a brand-new mention).
      5. other                — catch-all.

    NOTE: in this OFFLINE replay the saved_people list is always empty
    (we deliberately don't hydrate it so the missing-target path has a
    fair chance to fire).  Live-shadow telemetry on
    `mirror_chat_retrieval_receipts` is the place where `resolver_miss`
    and `ambiguous_match` become populated meaningfully.  We surface the
    classifier shape here for parity.
    """
    name = (row.get("rel_target_unresolved_name") or "").strip()
    msg = row.get("message") or ""
    frame = row.get("active_frame")
    if not name:
        return "other"

    # Count distinct proper-name candidates in the message itself.
    candidates = _NAME_CANDIDATE_RE.findall(msg)
    distinct = {c for c in candidates if c.lower() not in _NAME_FILTER_LC}
    if len(distinct) >= 2:
        return "ambiguous_match"

    # In live mode we would also check fuzzy match against saved_people
    # here; in offline replay saved_people=[] so we skip resolver_miss.

    if frame in ("forum", "member"):
        return "forum_only_member"
    return "true_missing_person"


# Lightweight re-use of the router's filtering, without importing private
# helpers (keeps the runner self-contained).
_NAME_CANDIDATE_RE = re.compile(r"\b([A-Z][a-z]{1,30})\b")
_NAME_FILTER_LC = {
    "how", "what", "why", "when", "where", "who", "tell", "show", "can",
    "should", "would", "am", "is", "are", "do", "does", "has", "have",
    "i", "me", "my", "we", "us", "our", "you", "your", "they",
    "saturn", "venus", "mars", "jupiter", "pluto", "mercury", "sun",
    "moon", "uranus", "neptune", "chiron", "lilith", "node", "nodes",
    "aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra",
    "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    "human", "design", "enneagram", "astrology", "numerology", "bazi",
    "mirror", "chat", "cross", "lens", "lenses", "forum", "reflection",
    "rl", "probe", "test", "today", "yes", "no", "ok", "okay", "hi",
    "hey", "hello",
}

# ---------------------------------------------------------------------------
# B2 Delta-Review Regression Classifiers (June 14 operator focus list).
#
# These helpers annotate each replay row with the regression buckets the
# operator asked us to track on top of the existing FP/forum/unresolved
# gates.  They are mutually-orthogonal labels (a row can hit several).
#
# Buckets (operator spec):
#   1. domain_drift_kind          (gate <5%, per-domain >10% review)
#   2. lens_jargon_override       (gate <3%)
#   3. relationship_context_loss  (gate <2%)
#   4. wrong_target_selected      (gate = 0)
#   5. payload_completeness       (alert if >25% shrink vs baseline)
#   6. multi_lens_coverage        (gate >=90% of multi-lens prompts get >=2 lenses)
#   7. high_confidence_wrong_route (gate <1%)
#   8. is_founder_query           (tracked separately)
#   9. couple_forum_bleed_kind    (gate = 0)
#  10. decision_not_explainable   (tracked)
# ---------------------------------------------------------------------------

# Lens families used by the "multi-lens coverage" classifier.
_LENS_FAMILY_PATTERNS: Dict[str, re.Pattern] = {
    "astrology":    re.compile(
        r"\b(saturn|venus|mars|jupiter|pluto|mercury|sun|moon|uranus|neptune|"
        r"chiron|north\s+node|south\s+node|7th\s+house|10th\s+house|5th\s+house|"
        r"natal|transit|return|aries|taurus|gemini|cancer|leo|virgo|libra|"
        r"scorpio|sagittarius|capricorn|aquarius|pisces|chart|ascendant)\b", re.I),
    "human_design": re.compile(
        r"\b(manifestor|generator|projector|reflector|sacral|splenic|emotional\s+"
        r"authority|gate\s+\d+|channel\s+\d+|profile\s+\d|3/5|5/1|6/2|defined|"
        r"undefined|open\s+center|strategy|inner\s+authority|human\s+design)\b",
        re.I),
    "enneagram":    re.compile(
        r"\b(type\s+[1-9]\b|enneagram|integration|disintegration|wing\s+[1-9]|"
        r"sp/so|so/sp|sx/sp|tritype)\b", re.I),
    "numerology":   re.compile(
        r"\b(life\s+path|expression\s+number|soul\s+urge|personality\s+number|"
        r"numerolog|destiny\s+number|birthday\s+number|year\s+\d{4}\s+vibration)\b",
        re.I),
    "bazi":         re.compile(
        r"\b(bazi|day\s+master|four\s+pillars|five\s+elements|metal\s+rat|"
        r"wood\s+ox|fire\s+horse|water\s+dragon|earth\s+goat|heavenly\s+stem|"
        r"earthly\s+branch)\b", re.I),
}

# Heuristic lens-jargon override patterns (operator examples).
# Each entry: (lens-term-regex, "wrong" predicted domain it tends to land in,
#              short note for the report).
_LENS_OVERRIDE_PATTERNS: List[Tuple[re.Pattern, str, str]] = [
    (re.compile(r"\bsaturn\s+return\b", re.I), "identity",
     "saturn return collapsed to identity (should weight life_direction)"),
    (re.compile(r"\b7th\s+house\b", re.I), "relationship",
     "7th house auto-routed to relationship without relational kw"),
    (re.compile(r"\bmanifestor\b", re.I), "leadership",
     "manifestor auto-routed to leadership without leadership context"),
    (re.compile(r"\b10th\s+house\b", re.I), "career",
     "10th house auto-routed to career without career context"),
]

# Heuristic ground-truth labels for domain drift on REAL rows (where we
# have no synth `expected_primary`).  Each tuple: (regex, expected_domain).
# Pattern order matters — first match wins.
_DRIFT_GROUND_TRUTH: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bsaturn\s+return\b", re.I),                 "life_direction"),
    (re.compile(r"\bshould\s+i\s+leave\s+(my|the)\s+(company|job|role|firm)\b", re.I),
                                                                "life_direction"),
    (re.compile(r"\bshould\s+i\s+(quit|leave|exit)\b", re.I),  "life_direction"),
    (re.compile(r"\bwhat\s+does\s+\w+\s+trigger\s+in\s+me\b", re.I),
                                                                "relationship"),
    (re.compile(r"\bbetween\s+\w+\s+and\s+(me|us)\b", re.I),   "relationship"),
    (re.compile(r"\bmy\s+(career|next\s+role|next\s+chapter)\s+(direction|path)?\b", re.I),
                                                                "life_direction"),
    (re.compile(r"\b(life\s+direction|next\s+chapter|where\s+i'?m\s+headed)\b", re.I),
                                                                "life_direction"),
]

# Founder / operator regression suite triggers.
_FOUNDER_RE = re.compile(
    r"\b(founder|co-?founder|ceo|cto|coo|chief\s+\w+\s+officer|board\b|investor|"
    r"fundrais\w*|runway|hiring|hire\b|delegat\w*|cofound|company[- ]building|"
    r"team\s+dynamics|leadership|operator|exec\b|executive)\b", re.I)

# ----- Stage-1 rollout focused telemetry categories -----
# Operator-tracked buckets during the 10% rollout observation window.
# These are PURELY ANALYTICAL — they classify rows for stratified
# reporting, they do NOT influence routing.

# Educational astrology: lens-term present WITHOUT contextual cue.
# Examples: "Tell me about my Saturn return", "What's my 7th house about?",
# "Explain my Pluto in the 8th".  Distinct from the lens-jargon override
# bucket: this is the SAFE pattern when routed to identity/general, not
# a failure mode per se — but B3.1 will move these to a dedicated
# "educational" lane.
_EDU_ASTRO_LENS_RE = re.compile(
    r"\b(saturn|venus|mars|jupiter|pluto|mercury|sun|moon|uranus|neptune|"
    r"chiron|north\s+node|south\s+node|\d+(st|nd|rd|th)\s+house|"
    r"natal|transit|return|ascendant|midheaven|descendant|ic\b)\b", re.I)
_EDU_CONTEXTUAL_CUE_RE = re.compile(
    r"\b(mel|wife|husband|partner|spouse|cofounder|team|board|company|"
    r"feeling|right\s+now|today|this\s+week|happening|tension|conflict|"
    r"between\s+(me|us|them))\b", re.I)


def _is_educational_astrology(row: Dict[str, Any]) -> bool:
    """Lens-term present in a chart-explanation framing, with no
    relational/career/temporal contextual cue.  These are the prompts
    B3.1's 'educational-mode disambiguation' lane will absorb."""
    msg = row.get("message") or ""
    if not _EDU_ASTRO_LENS_RE.search(msg):
        return False
    if _EDU_CONTEXTUAL_CUE_RE.search(msg):
        return False
    return True


def _is_forum_topology_dependent(row: Dict[str, Any]) -> bool:
    """Prompt that REQUIRES forum_topology.active_member_id to resolve
    correctly: frame=forum AND no explicit_target_id AND no name in the
    message.  These are the prompts P4 will fix."""
    if row.get("active_frame") != "forum":
        return False
    if row.get("explicit_target_id"):
        return False
    if row.get("rel_target_resolved"):
        return False
    return True

# Couple-only signals (relational dyad).
_COUPLE_RE = re.compile(
    r"\b(mel|wife|husband|partner|spouse|marriage|between\s+(mel|me|us|him|her)\s+and|"
    r"my\s+(wife|husband|partner|spouse))\b", re.I)
# Forum-only signals (multi-party / room / group).  Intentionally
# excludes the bare word "member(s)" — probe messages and member-frame
# diagnostic strings frequently contain it without implying group framing.
_FORUM_ONLY_RE = re.compile(
    r"\b(the\s+forum|our\s+forum|this\s+room|this\s+group|the\s+group|"
    r"the\s+team|cohort|circle)\b", re.I)

# Diagnostic-probe filter — messages this short are operator/QA probes
# (e.g. "Reflection test (member)."), not real user inputs, so we skip
# them for content-quality classifiers that depend on semantic intent.
_PROBE_MIN_CHARS = 25
_PROBE_RE = re.compile(
    r"^(reflection\s+test|probe|ping|test\b|hi\b|hey\b|hello\b)", re.I)


def _is_probe(msg: str) -> bool:
    if not msg:
        return True
    msg_s = msg.strip()
    if len(msg_s) < _PROBE_MIN_CHARS:
        return True
    if _PROBE_RE.match(msg_s):
        return True
    return False


def _domain_drift_kind(row: Dict[str, Any]) -> Optional[str]:
    """Return a 'expected→predicted' label if there's a domain drift.

    Uses:
      * `expected_domain` if present (synth golden rows).
      * Heuristic ground-truth regex for known REAL drift patterns.
    Returns None if no drift detected or no ground truth available.
    """
    predicted = row.get("predicted_domain")
    expected = row.get("expected_domain")
    if expected and predicted and predicted != expected:
        return f"{expected}->{predicted}"
    msg = row.get("message") or ""
    for pat, exp in _DRIFT_GROUND_TRUTH:
        if pat.search(msg):
            if predicted and predicted != exp:
                return f"{exp}->{predicted}"
            return None  # heuristic matched but predicted is correct
    return None


def _lens_jargon_override(row: Dict[str, Any]) -> Optional[str]:
    """Return a short error tag if a lens term auto-overrode the route.

    Heuristic: the message contains a lens term, the predicted domain
    matches the "collapse" pattern for that term, AND the message lacks
    independent relational/career/leadership keywords supporting the
    predicted domain.
    """
    msg = row.get("message") or ""
    predicted = row.get("predicted_domain")
    if not predicted:
        return None
    for pat, wrong_dom, note in _LENS_OVERRIDE_PATTERNS:
        if pat.search(msg) and predicted == wrong_dom:
            # Make sure there's NO independent context that would
            # legitimately push the route to that domain.
            if wrong_dom == "relationship" and _COUPLE_RE.search(msg):
                continue
            if wrong_dom == "leadership" and re.search(
                    r"\b(lead|leading|team|founder|ceo|board|delegat)\b", msg, re.I):
                continue
            if wrong_dom == "career" and re.search(
                    r"\b(job|role|career|firm|company|promotion)\b", msg, re.I):
                continue
            if wrong_dom == "identity" and re.search(
                    r"\b(who\s+am\s+i|my\s+core|am\s+i\s+really|identity)\b", msg, re.I):
                continue
            return note
    return None


def _relationship_context_loss(row: Dict[str, Any]) -> bool:
    """Target resolved + relationship_relevant=true, but predicted is
    NOT relationship/family/parenting → synthesis will likely treat as
    solo self-analysis even though the user is asking about someone.

    Skips diagnostic probe messages (operator/QA shorthand) since those
    do not exercise the synthesis path meaningfully.
    """
    if _is_probe(row.get("message") or ""):
        return False
    if not row.get("rel_target_resolved"):
        return False
    if not row.get("relationship_relevant"):
        return False
    return row.get("predicted_domain") not in ("relationship", "family", "parenting")


def _wrong_target_selected(row: Dict[str, Any]) -> bool:
    """explicit_target_id given but resolver returned a different target
    (mis-binding or stale-memory bleed-through)."""
    explicit = row.get("explicit_target_id")
    resolved = row.get("rel_target_resolved")
    if not explicit:
        return False
    if resolved is None:
        return False  # captured by wrong_person_selected sub-bucket
    return str(explicit) != str(resolved)


def _multi_lens_signature(msg: str) -> List[str]:
    """List of lens families detected in the message."""
    return [lens for lens, pat in _LENS_FAMILY_PATTERNS.items() if pat.search(msg or "")]


def _high_confidence_wrong_route(row: Dict[str, Any]) -> bool:
    """confidence >= 0.6 AND predicted != expected (only meaningful where
    we have ground truth — synth rows OR heuristic-drift-detected rows)."""
    conf = row.get("confidence") or 0.0
    if conf < 0.6:
        return False
    drift = row.get("domain_drift_kind")
    return bool(drift)


def _couple_forum_bleed(row: Dict[str, Any]) -> Optional[str]:
    """Detect cross-contamination between couple and forum framing.

    Skips diagnostic probe messages (e.g. "Reflection test (member).")
    to avoid false positives from operator-internal QA strings.
    """
    msg = row.get("message") or ""
    if _is_probe(msg):
        return None
    frame = row.get("active_frame")
    has_couple = bool(_COUPLE_RE.search(msg))
    has_forum = bool(_FORUM_ONLY_RE.search(msg))
    if has_couple and frame == "forum" and not has_forum:
        return "couple_to_forum_bleed"
    if has_forum and frame == "member" and not has_couple:
        return "forum_to_couple_bleed"
    return None


def _is_decision_explainable(envelope: Dict[str, Any]) -> bool:
    """A routing decision is explainable if:
      * its primary_domain has at least one matched phrase, OR
      * a strong frame/role/target bias contributed to the top score, OR
      * the envelope is an intentional 'general' fallback (those are
        explainable by definition via `fallback_reason`).
    """
    domain = envelope.get("primary_domain")
    ev = envelope.get("evidence") or {}
    if domain == "general":
        return bool(ev.get("fallback_reason"))
    matched = (ev.get("matched_phrases") or {}).get(domain) or []
    if matched:
        return True
    # Bias-only decisions are explainable iff bias clearly contributed.
    frame_bias = ev.get("frame_bias_applied") or {}
    role_bias = ev.get("role_bias_applied") or {}
    target_bonus = ev.get("target_active_bonus") or 0.0
    contributed = (
        domain in frame_bias and frame_bias.get(domain, 0) >= 0.20
    ) or (
        domain in role_bias and role_bias.get(domain, 0) >= 0.20
    ) or (
        target_bonus and domain in ("relationship", "family", "parenting", "work", "career")
    )
    return bool(contributed)


def categorise(message: str, frame: str, has_target: bool) -> str:
    if frame in ("forum",):
        return "forum_member"
    if has_target or frame == "member":
        return "forum_member"
    for name, pat in CATEGORY_PATTERNS:
        if pat.search(message or ""):
            return name
    return "other"


async def _pull_real(db, window_days: int) -> List[Dict[str, Any]]:
    """Pull real user messages from the three chat collections.

    chat_history.messages: array on a user doc → each {role:user} item is a
                            replay case
    forum_chat_messages: 1 doc per user turn with {message, target_member_*,
                          mode}
    forum_mirror_chat_messages: 1 doc per turn with {content, role}
    """
    rows: List[Dict[str, Any]] = []
    cutoff = datetime.now(dt_tz.utc) - timedelta(days=window_days)

    # 1. chat_history — wraps an array of {role, content, timestamp}.
    async for doc in db["chat_history"].find({}):
        user_id = str(doc.get("user_id") or "")
        for m in (doc.get("messages") or []):
            if (m.get("role") or "").lower() != "user":
                continue
            content = (m.get("content") or "").strip()
            if not content:
                continue
            ts = m.get("timestamp")
            try:
                ts_dt = ts if isinstance(ts, datetime) else datetime.fromisoformat(str(ts).split(".")[0])
                if ts_dt.tzinfo is None:
                    ts_dt = ts_dt.replace(tzinfo=dt_tz.utc)
            except Exception:
                ts_dt = datetime.now(dt_tz.utc)
            if ts_dt < cutoff:
                continue
            rows.append({
                "source": "real",
                "collection": "chat_history",
                "user_id": user_id,
                "message": content,
                "active_frame": "self",
                "current_target_id": None,
                "relationship_role": None,
                "ts": ts_dt.isoformat(),
            })

    # 2. forum_chat_messages — has mode + target_member info.
    async for doc in db["forum_chat_messages"].find({}):
        content = (doc.get("message") or "").strip()
        if not content:
            continue
        ts = doc.get("timestamp")
        try:
            ts_dt = ts if isinstance(ts, datetime) else datetime.fromisoformat(str(ts).split(".")[0])
            if ts_dt.tzinfo is None:
                ts_dt = ts_dt.replace(tzinfo=dt_tz.utc)
        except Exception:
            ts_dt = datetime.now(dt_tz.utc)
        if ts_dt < cutoff:
            continue
        mode = (doc.get("mode") or "").lower()
        target = doc.get("target_member_id")
        frame = "member" if target else ("forum" if mode == "forum" else "self")
        rows.append({
            "source": "real",
            "collection": "forum_chat_messages",
            "user_id": str(doc.get("user_id") or ""),
            "message": content,
            "active_frame": frame,
            "current_target_id": str(target) if target else None,
            "relationship_role": None,
            "target_member_name": doc.get("target_member_name"),
            "ts": ts_dt.isoformat(),
        })

    # 3. forum_mirror_chat_messages — turn-based.
    async for doc in db["forum_mirror_chat_messages"].find({"role": "user"}):
        content = (doc.get("content") or "").strip()
        if not content:
            continue
        ts = doc.get("ts")
        try:
            ts_dt = ts if isinstance(ts, datetime) else datetime.fromisoformat(str(ts).split(".")[0])
            if ts_dt.tzinfo is None:
                ts_dt = ts_dt.replace(tzinfo=dt_tz.utc)
        except Exception:
            ts_dt = datetime.now(dt_tz.utc)
        if ts_dt < cutoff:
            continue
        rows.append({
            "source": "real",
            "collection": "forum_mirror_chat_messages",
            "user_id": str(doc.get("user_id") or ""),
            "message": content,
            "active_frame": "forum",
            "current_target_id": None,
            "relationship_role": None,
            "ts": ts_dt.isoformat(),
        })

    return rows


def _load_synth_supplement(target_min: int) -> List[Dict[str, Any]]:
    if not SYNTH_YAML.exists():
        return []
    with open(SYNTH_YAML) as f:
        cases = yaml.safe_load(f) or []
    synth_rows: List[Dict[str, Any]] = []
    for c in cases:
        if c.get("source") != "synth":
            continue
        synth_rows.append({
            "source": "synth",
            "collection": "golden_set_pete_mel_historical",
            "user_id": "synth-pete",
            "message": c.get("message", ""),
            "active_frame": c.get("active_frame", "self"),
            "current_target_id": c.get("current_target_id"),
            "relationship_role": c.get("relationship_role"),
            "expected_primary": c.get("expected_primary"),
            "category_hint": c.get("category"),
            "ts": None,
        })
    return synth_rows[:target_min]


def _saved_people_for(user_id: str) -> List[Dict[str, Any]]:
    """Replay uses a minimal stub.  In live mode the router would pull
    the user's saved_people; here we keep it empty so the missing-target
    fallback gets a fair chance to fire."""
    return []


def _run_one(row: Dict[str, Any]) -> Dict[str, Any]:
    t0 = time.perf_counter()
    frame = row["active_frame"]
    target_id = row.get("current_target_id")
    role = row.get("relationship_role")
    rel = resolve_relationship_context(
        self_user_id=row.get("user_id") or "",
        user_message=row["message"],
        active_frame=frame,
        target_id=target_id,
        saved_people=_saved_people_for(row.get("user_id") or ""),
    )
    env = classify_intent_v2(
        message=row["message"],
        active_frame=frame,
        current_target_id=rel.target or target_id,
        relationship_role=rel.role or role,
    )
    envd = env.to_dict()
    modules = mandatory_modules(envd["primary_domain"])
    receipt = build_receipt(
        request_id=f"replay-{row.get('user_id', 'unknown')[:8]}-{time.time_ns()}",
        intent_envelope=envd,
        relationship_resolution=rel.to_dict(),
        modules_invoked=modules,
        payloads={m: {"sim": True} for m in modules},
    )
    latency_ms = round((time.perf_counter() - t0) * 1000, 3)

    predicted = envd["primary_domain"]
    expected = row.get("expected_primary")
    top1_hit = (expected is None) or (predicted == expected)
    category = row.get("category_hint") or categorise(row["message"], frame, bool(target_id or rel.target))

    out = {
        "source": row["source"],
        "collection": row["collection"],
        "user_id_short": (row.get("user_id") or "")[:10],
        "message": row["message"],
        "active_frame": frame,
        "explicit_target_id": target_id,
        "category": category,
        "predicted_domain": predicted,
        "expected_domain": expected,
        "top1_hit": top1_hit if expected else None,
        "signal_strength": envd.get("signal_strength"),
        "margin": envd.get("margin"),
        "confidence": envd.get("confidence"),
        "fallback_reason": (envd.get("evidence") or {}).get("fallback_reason"),
        "relationship_relevant": envd.get("relationship_relevant"),
        "secondary_domains": envd.get("secondary_domains"),
        "rel_target_resolved": rel.target,
        "rel_target_unresolved_name": rel.target_unresolved_name,
        "rel_missing_data": rel.missing_data,
        "rel_proposed_action": rel.proposed_action,
        "rel_context_mode": rel.context_mode,
        "retrieval_status": receipt["retrieval_status"],
        "routing_status": receipt["routing_status"],
        "target_resolution_status": receipt["target_resolution_status"],
        "latency_ms": latency_ms,
    }
    # Attach sub-bucket classifiers (used by the readiness report to
    # split forum/member ambiguity and unresolved-named into categories).
    if frame in ("forum", "member") and not out["rel_target_resolved"]:
        out["fm_subbucket"] = _classify_forum_member_unresolved(out)
    else:
        out["fm_subbucket"] = None
    if out["target_resolution_status"] == "UNRESOLVED_NAMED":
        out["un_subbucket"] = _classify_unresolved_named(out)
    else:
        out["un_subbucket"] = None

    # ----- B2 Delta-Review Regression Classifiers (operator focus list) -----
    out["domain_drift_kind"] = _domain_drift_kind(out)
    out["lens_jargon_override"] = _lens_jargon_override(out)
    out["relationship_context_loss"] = _relationship_context_loss(out)
    out["wrong_target_selected"] = _wrong_target_selected(out)
    out["multi_lens_signature"] = _multi_lens_signature(row["message"])
    out["multi_lens_prompt"] = len(out["multi_lens_signature"]) >= 2
    # Coverage: in the offline shadow stack, the "retrieved" lens family
    # set == lens_priority entries that map to a known lens family.
    lens_priority = envd.get("lens_priority") or []
    out["lens_priority"] = lens_priority
    out["multi_lens_covered_count"] = sum(
        1 for fam in out["multi_lens_signature"]
        if fam in lens_priority
        or (fam == "human_design" and "human_design" in lens_priority)
    )
    out["high_confidence_wrong_route"] = _high_confidence_wrong_route(out)
    out["is_founder_query"] = bool(_FOUNDER_RE.search(row["message"] or ""))
    out["is_educational_astrology"] = _is_educational_astrology(out)
    out["is_forum_topology_dependent"] = _is_forum_topology_dependent(out)
    out["couple_forum_bleed_kind"] = _couple_forum_bleed(out)
    out["decision_not_explainable"] = not _is_decision_explainable(envd)
    # Payload completeness — in offline replay payloads are stubbed,
    # but we still capture the *expected* mandatory module list size so
    # the delta-detector can flag baseline-shrinkage in live mode.
    out["mandatory_modules_count"] = len(modules)
    return out


def _aggregate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute the readiness metrics the user asked for."""
    n = len(rows)
    n_real = sum(1 for r in rows if r["source"] == "real")
    n_synth = sum(1 for r in rows if r["source"] == "synth")

    domain_counts = Counter(r["predicted_domain"] for r in rows)
    routing_counts = Counter(r["routing_status"] for r in rows)
    retrieval_counts = Counter(r["retrieval_status"] for r in rows)
    target_status_counts = Counter(r["target_resolution_status"] for r in rows)
    by_source: Dict[str, Counter] = {"real": Counter(), "synth": Counter()}
    for r in rows:
        by_source[r["source"]][r["predicted_domain"]] += 1
    cat_counts = Counter(r["category"] for r in rows)

    # False-positive relationship routing.  Two flavours:
    #  * "frame_aware" — TRUE false positive: predicted=relationship in
    #    `self` frame with no target_id and no relationship keyword.  The
    #    forum/member frames *intentionally* bias toward relationship via
    #    FRAME_BIAS, so we exclude them.
    #  * "broad"       — pre-bias view: predicted=relationship without
    #    target/keyword regardless of frame.  Useful when reasoning about
    #    the FRAME_BIAS contribution itself.
    rel_keyword_re = re.compile(
        r"\b(mel|wife|husband|partner|spouse|marriage|us|we|her|him|relationship|"
        r"between\s+\w+\s+and|together|fight|distant|connection|conflict)\b", re.I)
    fp_rel = [
        r for r in rows
        if r["predicted_domain"] == "relationship"
        and r["active_frame"] == "self"
        and not r["rel_target_resolved"]
        and not rel_keyword_re.search(r["message"])
        and r["explicit_target_id"] is None
    ]
    fp_rel_broad = [
        r for r in rows
        if r["predicted_domain"] == "relationship"
        and not r["rel_target_resolved"]
        and not rel_keyword_re.search(r["message"])
        and r["explicit_target_id"] is None
    ]

    # False-negative relationship routing: explicit target or relationship
    # keyword present but predicted is NOT relationship/family/parenting.
    fn_rel = [
        r for r in rows
        if r["predicted_domain"] not in ("relationship", "family", "parenting")
        and (r["explicit_target_id"] or r["rel_target_resolved"]
             or rel_keyword_re.search(r["message"]))
    ]

    # Forum/member ambiguity: frame is forum/member but the resolver
    # produced no target.  We now classify each unresolved row into a
    # sub-bucket so the rollout review can separate resolver failures
    # from acceptable data gaps.
    forum_member_unresolved = [
        r for r in rows
        if r["active_frame"] in ("forum", "member")
        and not r["rel_target_resolved"]
    ]
    forum_member_total = [r for r in rows if r["active_frame"] in ("forum", "member")]
    fm_sub_counts = Counter(r.get("fm_subbucket") for r in forum_member_unresolved)
    fm_sub_examples: Dict[str, List[Dict[str, Any]]] = {}
    for r in forum_member_unresolved:
        b = r.get("fm_subbucket") or "unclassified_unresolved"
        if len(fm_sub_examples.get(b, [])) < 3:
            fm_sub_examples.setdefault(b, []).append({
                "message": r["message"],
                "frame": r["active_frame"],
                "predicted_domain": r["predicted_domain"],
                "explicit_target_id": r.get("explicit_target_id"),
                "unresolved_name": r.get("rel_target_unresolved_name"),
            })
    # "Resolver-failure" sub-buckets that block cutover; the others are
    # acceptable data-gap categories we surface but don't gate on.
    fm_resolver_failure_buckets = {
        "wrong_person_selected",
        "wrong_frame_selected",
        "relationship_to_self_downgrade",
    }
    fm_resolver_failures = sum(v for k, v in fm_sub_counts.items()
                               if k in fm_resolver_failure_buckets)
    fm_data_gap_buckets = {"forum_to_member_misroute", "unclassified_unresolved", None}
    fm_data_gaps = sum(v for k, v in fm_sub_counts.items() if k in fm_data_gap_buckets)

    # Unresolved-named-target rate: rows where a proper name was detected
    # but no saved-people match.
    unresolved_named = [r for r in rows if r["target_resolution_status"] == "UNRESOLVED_NAMED"]
    un_sub_counts = Counter(r.get("un_subbucket") for r in unresolved_named)
    un_sub_examples: Dict[str, List[Dict[str, Any]]] = {}
    for r in unresolved_named:
        b = r.get("un_subbucket") or "other"
        if len(un_sub_examples.get(b, [])) < 3:
            un_sub_examples.setdefault(b, []).append({
                "message": r["message"],
                "frame": r["active_frame"],
                "suggested_name": r.get("rel_target_unresolved_name"),
            })

    # General-bucket rate.
    general = [r for r in rows if r["predicted_domain"] == "general"]

    # Fallback (low/no_signal) rate.
    fallbacks = [r for r in rows if r["fallback_reason"] in ("low_signal", "no_signal", "weak_ambiguous")]

    # Real-only golden-set accuracy: only meaningful where expected is
    # provided (synth rows).  For real rows we don't have ground truth.
    expected_rows = [r for r in rows if r["expected_domain"]]
    expected_top1 = [r for r in expected_rows if r["top1_hit"]]

    lat = [r["latency_ms"] for r in rows]

    return {
        "totals": {
            "n": n,
            "n_real": n_real,
            "n_synth": n_synth,
            "in_window_target": (TARGET_TOTAL_LOW <= n <= TARGET_TOTAL_HIGH),
        },
        "stratification": {
            "by_category": dict(cat_counts),
            "by_source": {k: dict(v) for k, v in by_source.items()},
            "domain_counts": dict(domain_counts),
        },
        "routing": {
            "status_counts": dict(routing_counts),
            "pass_rate": round(routing_counts.get("PASS", 0) / max(n, 1), 4),
        },
        "retrieval": {
            "status_counts": dict(retrieval_counts),
            "pass_rate": round(retrieval_counts.get("PASS", 0) / max(n, 1), 4),
        },
        "target_resolution": {
            "status_counts": dict(target_status_counts),
            "unresolved_named_rate": round(len(unresolved_named) / max(n, 1), 4),
            "unresolved_named_count": len(unresolved_named),
            "unresolved_named_subbuckets": dict(un_sub_counts),
            "unresolved_named_subbucket_examples": un_sub_examples,
        },
        "false_positive_relationship": {
            "count": len(fp_rel),
            "rate": round(len(fp_rel) / max(n, 1), 4),
            "broad_count": len(fp_rel_broad),
            "broad_rate": round(len(fp_rel_broad) / max(n, 1), 4),
            "examples": [{"message": r["message"], "frame": r["active_frame"],
                          "category": r["category"]} for r in fp_rel[:10]],
        },
        "false_negative_relationship": {
            "count": len(fn_rel),
            "rate": round(len(fn_rel) / max(n, 1), 4),
            "examples": [{"message": r["message"], "predicted": r["predicted_domain"],
                          "frame": r["active_frame"]} for r in fn_rel[:10]],
        },
        "forum_member_ambiguity": {
            "total": len(forum_member_total),
            "unresolved": len(forum_member_unresolved),
            "rate": round(
                len(forum_member_unresolved) / max(len(forum_member_total), 1), 4),
            "subbuckets": dict(fm_sub_counts),
            "subbucket_examples": fm_sub_examples,
            "resolver_failure_buckets": sorted(fm_resolver_failure_buckets),
            "resolver_failure_count": fm_resolver_failures,
            "resolver_failure_rate_of_unresolved": round(
                fm_resolver_failures / max(len(forum_member_unresolved), 1), 4),
            "resolver_failure_rate_of_total": round(
                fm_resolver_failures / max(len(forum_member_total), 1), 4),
            "data_gap_count": fm_data_gaps,
            "data_gap_rate_of_unresolved": round(
                fm_data_gaps / max(len(forum_member_unresolved), 1), 4),
            # "correctly handled" = resolved OR classified as acceptable data gap
            "correctly_handled_rate": round(
                ((len(forum_member_total) - fm_resolver_failures))
                / max(len(forum_member_total), 1), 4),
        },
        "general_bucket": {
            "count": len(general),
            "rate": round(len(general) / max(n, 1), 4),
        },
        "fallback": {
            "count": len(fallbacks),
            "rate": round(len(fallbacks) / max(n, 1), 4),
        },
        "expected_top1_synth_only": {
            "n_with_expected": len(expected_rows),
            "n_top1": len(expected_top1),
            "accuracy": round(len(expected_top1) / max(len(expected_rows), 1), 4),
        },
        "latency_ms": {
            "mean": round(statistics.mean(lat), 3) if lat else 0,
            "p50": round(statistics.median(lat), 3) if lat else 0,
            "p95": round(sorted(lat)[int(0.95 * (len(lat) - 1))], 3) if lat else 0,
            "max": round(max(lat), 3) if lat else 0,
        },
        "versions": {
            "intent_router": INTENT_VER,
            "relationship_router": REL_VER,
            "validator": VALIDATOR_VERSION,
        },
        # ----- B2 Delta-Review Regression Buckets (operator focus list) -----
        "regression_buckets": _aggregate_regression_buckets(rows),
    }


def _aggregate_regression_buckets(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute the 10 operator-requested regression buckets.

    Each sub-dict carries:
      * count        — # rows that hit the bucket
      * rate         — share of the denominator (whole corpus by default)
      * gate         — the operator-specified threshold (informational)
      * status       — PASS / FAIL / WATCH
      * examples     — up to 5 representative rows
    """
    n = max(len(rows), 1)

    def _examples(predicate, limit=5, fields=("message", "active_frame",
                                              "predicted_domain")):
        out = []
        for r in rows:
            if predicate(r):
                out.append({f: r.get(f) for f in fields})
                if len(out) >= limit:
                    break
        return out

    def _status(rate: float, gate: float, cmp: str) -> str:
        if cmp == "<=":
            return "PASS" if rate <= gate else "FAIL"
        if cmp == "<":
            return "PASS" if rate < gate else "FAIL"
        if cmp == ">=":
            return "PASS" if rate >= gate else "FAIL"
        if cmp == "==0":
            return "PASS" if rate == 0 else "FAIL"
        return "WATCH"

    # 1. Domain drift
    drift_rows = [r for r in rows if r.get("domain_drift_kind")]
    drift_kinds = Counter(r["domain_drift_kind"] for r in drift_rows)
    drift_per_domain: Dict[str, int] = defaultdict(int)
    for kind, cnt in drift_kinds.items():
        if "->" in kind:
            expected, _ = kind.split("->", 1)
            drift_per_domain[expected] += cnt
    # Per-domain drift rate is normalised against rows that had a
    # heuristic/synth ground truth (where drift was *possible*).
    ground_truth_rows = sum(
        1 for r in rows
        if r.get("expected_domain")
        or any(pat.search(r.get("message") or "") for pat, _ in _DRIFT_GROUND_TRUTH)
    )
    drift_denom = max(ground_truth_rows, 1)
    drift_rate = len(drift_rows) / drift_denom
    per_domain_rate = {k: round(v / drift_denom, 4) for k, v in drift_per_domain.items()}
    domain_review = [d for d, rate in per_domain_rate.items() if rate > 0.10]
    # Small-sample guard: < 5 ground-truth rows isn't enough signal to
    # gate cutover on drift rate alone.
    if ground_truth_rows < 5:
        drift_status = "INSUFFICIENT_SAMPLE"
    elif drift_rate >= 0.05 or domain_review:
        drift_status = "FAIL"
    else:
        drift_status = "PASS"
    domain_drift = {
        "count": len(drift_rows),
        "denominator": drift_denom,
        "ground_truth_rows": ground_truth_rows,
        "rate": round(drift_rate, 4),
        "kinds": dict(drift_kinds),
        "per_expected_domain": dict(drift_per_domain),
        "per_expected_domain_rate": per_domain_rate,
        "domains_above_10pct": sorted(domain_review),
        "gate": "< 5% overall AND no expected_domain > 10%",
        "status": drift_status,
        "examples": _examples(lambda r: bool(r.get("domain_drift_kind")),
                              fields=("message", "active_frame",
                                      "predicted_domain", "domain_drift_kind")),
    }

    # 2. Lens-jargon override
    lj_rows = [r for r in rows if r.get("lens_jargon_override")]
    lj_rate = len(lj_rows) / n
    lens_jargon = {
        "count": len(lj_rows),
        "rate": round(lj_rate, 4),
        "kinds": dict(Counter(r["lens_jargon_override"] for r in lj_rows)),
        "gate": "< 3%",
        "status": _status(lj_rate, 0.03, "<"),
        "examples": _examples(lambda r: bool(r.get("lens_jargon_override")),
                              fields=("message", "predicted_domain",
                                      "lens_jargon_override")),
    }

    # 3. Relationship-context loss
    rcl_rows = [r for r in rows if r.get("relationship_context_loss")]
    rcl_rate = len(rcl_rows) / n
    rel_ctx_loss = {
        "count": len(rcl_rows),
        "rate": round(rcl_rate, 4),
        "gate": "< 2%",
        "status": _status(rcl_rate, 0.02, "<"),
        "examples": _examples(lambda r: bool(r.get("relationship_context_loss")),
                              fields=("message", "predicted_domain",
                                      "rel_target_resolved")),
    }

    # 4. Wrong-target selection
    wts_rows = [r for r in rows if r.get("wrong_target_selected")]
    wrong_target = {
        "count": len(wts_rows),
        "rate": round(len(wts_rows) / n, 4),
        "gate": "= 0 in review sample",
        "status": "PASS" if not wts_rows else "FAIL",
        "examples": _examples(lambda r: bool(r.get("wrong_target_selected")),
                              fields=("message", "explicit_target_id",
                                      "rel_target_resolved")),
    }

    # 5. Payload completeness (offline-stubbed; live-delta-only).
    mandatory_counts = [r.get("mandatory_modules_count") or 0 for r in rows]
    payload_completeness = {
        "mandatory_modules_mean": round(
            sum(mandatory_counts) / max(len(mandatory_counts), 1), 3),
        "mandatory_modules_min": min(mandatory_counts) if mandatory_counts else 0,
        "mandatory_modules_max": max(mandatory_counts) if mandatory_counts else 0,
        "gate": "no mandatory payload shrinks >25% vs baseline",
        "status": "BASELINE_ONLY",
        "note": ("Offline replay stubs payloads to {'sim': true}; the >25% "
                 "shrinkage alert fires only in the delta-detector when a "
                 "live-shadow run is diffed against the frozen baseline."),
    }

    # 6. Multi-lens coverage loss
    multi = [r for r in rows if r.get("multi_lens_prompt")]
    multi_covered = [r for r in multi if (r.get("multi_lens_covered_count") or 0) >= 2]
    multi_rate = (len(multi_covered) / max(len(multi), 1)) if multi else 1.0
    cross_lens = {
        "multi_lens_prompts": len(multi),
        "covered_2plus": len(multi_covered),
        "coverage_rate": round(multi_rate, 4),
        "gate": ">= 90% of multi-lens prompts retrieve >= 2 lens families",
        "status": "PASS" if (not multi or multi_rate >= 0.90) else "FAIL",
        "examples": _examples(
            lambda r: r.get("multi_lens_prompt")
            and (r.get("multi_lens_covered_count") or 0) < 2,
            fields=("message", "multi_lens_signature", "lens_priority")),
    }

    # 7. High-confidence wrong route
    hcwr = [r for r in rows if r.get("high_confidence_wrong_route")]
    hcwr_rate = len(hcwr) / n
    # Small-sample guard: HCWR depends on having a ground-truth signal;
    # if drift sample is too small to be meaningful, downgrade to WATCH.
    if ground_truth_rows < 5:
        hcwr_status = "WATCH" if hcwr else "INSUFFICIENT_SAMPLE"
    else:
        hcwr_status = _status(hcwr_rate, 0.01, "<")
    false_confidence = {
        "count": len(hcwr),
        "rate": round(hcwr_rate, 4),
        "ground_truth_rows": ground_truth_rows,
        "gate": "< 1%",
        "status": hcwr_status,
        "examples": _examples(lambda r: bool(r.get("high_confidence_wrong_route")),
                              fields=("message", "predicted_domain",
                                      "domain_drift_kind", "confidence")),
    }

    # 8. Founder/operator regression suite
    fnd = [r for r in rows if r.get("is_founder_query")]
    fnd_dom = Counter(r["predicted_domain"] for r in fnd)
    fnd_pass = sum(1 for r in fnd if r["routing_status"] == "PASS")
    founder_suite = {
        "count": len(fnd),
        "predicted_domain_mix": dict(fnd_dom),
        "routing_pass_rate": round(fnd_pass / max(len(fnd), 1), 4),
        "gate": "informational (no hard threshold)",
        "status": "WATCH",
        "examples": _examples(lambda r: r.get("is_founder_query"),
                              fields=("message", "predicted_domain",
                                      "routing_status", "confidence")),
    }

    # 9. Couple/Forum bleed
    bleed = [r for r in rows if r.get("couple_forum_bleed_kind")]
    bleed_kinds = Counter(r["couple_forum_bleed_kind"] for r in bleed)
    couple_forum = {
        "count": len(bleed),
        "kinds": dict(bleed_kinds),
        "gate": "= 0 in reviewed samples",
        "status": "PASS" if not bleed else "FAIL",
        "examples": _examples(lambda r: bool(r.get("couple_forum_bleed_kind")),
                              fields=("message", "active_frame",
                                      "couple_forum_bleed_kind",
                                      "predicted_domain")),
    }

    # 10. Explainability
    not_expl = [r for r in rows if r.get("decision_not_explainable")]
    explainability = {
        "decision_not_explainable_count": len(not_expl),
        "rate": round(len(not_expl) / n, 4),
        "gate": "informational; track for future bug clusters",
        "status": "WATCH" if not_expl else "PASS",
        "examples": _examples(lambda r: r.get("decision_not_explainable"),
                              fields=("message", "predicted_domain",
                                      "signal_strength", "margin",
                                      "confidence")),
    }

    return {
        "domain_drift":            domain_drift,
        "lens_jargon_override":    lens_jargon,
        "relationship_context_loss": rel_ctx_loss,
        "wrong_target_selected":   wrong_target,
        "payload_completeness":    payload_completeness,
        "cross_lens_coverage":     cross_lens,
        "high_confidence_wrong_route": false_confidence,
        "founder_operator_suite":  founder_suite,
        "couple_forum_separation": couple_forum,
        "explainability":          explainability,
        # ----- Stage-1 rollout focused telemetry categories -----
        "stage1_focused": _aggregate_stage1_focused(rows),
    }


def _aggregate_stage1_focused(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Stage-1 rollout focused telemetry: stratified counters operator
    asked us to track separately during the 10% rollout window.

    Three categories:
      * founder/operator queries        — B3.2 target lane
      * educational astrology queries   — B3.1 target lane
      * forum-topology-dependent queries — P4 target lane

    Each section reports volume, routing PASS rate, predicted-domain
    mix, and a small sample of representative cases.
    """
    def _slice(predicate, label: str):
        items = [r for r in rows if predicate(r)]
        n = len(items)
        pass_rate = (sum(1 for r in items if r.get("routing_status") == "PASS")
                     / max(n, 1))
        dom_mix = Counter(r.get("predicted_domain") for r in items)
        frame_mix = Counter(r.get("active_frame") for r in items)
        ex = [{"message": r.get("message"),
               "frame":   r.get("active_frame"),
               "predicted_domain": r.get("predicted_domain"),
               "routing_status":   r.get("routing_status"),
               "confidence":       r.get("confidence")}
              for r in items[:5]]
        return {
            "label": label,
            "count": n,
            "share_of_corpus": round(n / max(len(rows), 1), 4),
            "routing_pass_rate": round(pass_rate, 4),
            "predicted_domain_mix": dict(dom_mix),
            "frame_mix": dict(frame_mix),
            "examples": ex,
        }
    return {
        "founder_operator":          _slice(
            lambda r: r.get("is_founder_query"),         "B3.2 — founder/operator"),
        "educational_astrology":     _slice(
            lambda r: r.get("is_educational_astrology"), "B3.1 — educational astrology"),
        "forum_topology_dependent":  _slice(
            lambda r: r.get("is_forum_topology_dependent"), "P4 — forum topology dependent"),
    }


def _write_samples_md(rows: List[Dict[str, Any]], path: Path) -> None:
    """Pick representative success + failure cases for the appendix."""
    successes_real = [r for r in rows if r["source"] == "real"
                      and r["routing_status"] == "PASS"
                      and r["confidence"] and r["confidence"] >= 0.6][:8]
    failures_real = [r for r in rows if r["source"] == "real"
                     and (r["routing_status"] == "FAIL"
                          or r["predicted_domain"] == "general")][:8]
    fp_rel = [r for r in rows if r["predicted_domain"] == "relationship"
              and not r["rel_target_resolved"]
              and r["explicit_target_id"] is None][:5]
    unresolved = [r for r in rows if r["target_resolution_status"] == "UNRESOLVED_NAMED"][:5]

    def fmt(r):
        rp = r.get("rel_proposed_action")
        rp_str = f"  - proposed_action: `{rp}`" if rp else ""
        return (
            f"- `{r['source']}` / `{r['collection']}` / frame=`{r['active_frame']}`"
            f"\n  - **msg**: {r['message'][:200]}"
            f"\n  - predicted=`{r['predicted_domain']}`  conf={r['confidence']}  "
            f"signal={r['signal_strength']}  margin={r['margin']}"
            f"\n  - routing=`{r['routing_status']}`  retrieval=`{r['retrieval_status']}`  "
            f"target=`{r['target_resolution_status']}`"
            + (rp_str if rp_str else "")
        )

    parts = ["# B2 Replay Samples\n",
             "_Companion to `B2_READINESS_REPORT.md`._\n",
             "## Representative success cases (REAL)\n"]
    parts.append("\n".join(fmt(r) for r in successes_real) or "_(none)_")
    parts.append("\n\n## Representative failure cases (REAL)\n")
    parts.append("\n".join(fmt(r) for r in failures_real) or "_(none)_")
    parts.append("\n\n## False-positive relationship routing samples\n")
    parts.append("\n".join(fmt(r) for r in fp_rel) or "_(none)_")
    parts.append("\n\n## Unresolved-named-target samples (with proposed_action)\n")
    parts.append("\n".join(fmt(r) for r in unresolved) or "_(none)_")
    path.write_text("\n".join(parts))


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--window-days", type=int, default=DEFAULT_WINDOW_DAYS)
    ap.add_argument("--target-total", type=int, default=120,
                    help="Target replay corpus size (real first, synth fills the gap)")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = cli[os.environ["DB_NAME"]]

    real_rows = await _pull_real(db, args.window_days)
    print(f"Pulled {len(real_rows)} real rows from the last {args.window_days} days.")

    needed = max(0, args.target_total - len(real_rows))
    synth_rows = _load_synth_supplement(target_min=needed) if needed > 0 else []
    print(f"Supplementing with {len(synth_rows)} synthetic rows to reach target ~{args.target_total}.")

    corpus = real_rows + synth_rows
    print(f"Total replay corpus: {len(corpus)} cases "
          f"({len(real_rows)} real / {len(synth_rows)} synth)")

    # Run every case.
    t0 = time.perf_counter()
    results = [_run_one(r) for r in corpus]
    dt = time.perf_counter() - t0
    print(f"Replay complete in {dt*1000:.1f} ms.")

    agg = _aggregate(results)

    # Aggregates per source (so the readiness report can ground in REAL only)
    real_results = [r for r in results if r["source"] == "real"]
    synth_results = [r for r in results if r["source"] == "synth"]
    agg["aggregates_by_source"] = {
        "real": _aggregate(real_results),
        "synth": _aggregate(synth_results),
    }

    out_doc = {
        "generated_at": datetime.now(dt_tz.utc).isoformat(),
        "window_days": args.window_days,
        "target_total": args.target_total,
        "aggregate": agg,
        "rows": results,
    }
    RESULTS_JSON.write_text(json.dumps(out_doc, indent=2, default=str))
    print(f"Wrote {RESULTS_JSON}")

    _write_samples_md(results, SAMPLES_MD)
    print(f"Wrote {SAMPLES_MD}")

    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
