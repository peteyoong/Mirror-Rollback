"""
Astrology Timeline Interpreter — Lightweight Layer
==================================================

Converts the existing True Sidereal Astrology Timeline content into a
COMPACT, STRUCTURED decision/timing context that the Life Interpreter
("Ask About My Life") can reason with.

Design notes
------------
- This service does NOT recompute astrology. It interprets whatever
  timeline payload is provided.
- Robust to multiple payload shapes — the existing astrology timeline
  is largely LLM prose today; if a structured payload is missing, the
  interpreter falls back to a deterministic 4-phase scaffold using
  the user's birth-quarter (Recognition → Confrontation → Crossroads
  → Integration).
- Returns ONLY structured data. No user-facing prose generation.
- All output is astrology-jargon-free: no planets, houses, transits,
  decans, or chart mechanics.

Public API
----------
    build_timeline_context(
        user_id, astrology_timeline_payload,
        current_date=None, domain=None,
    ) -> dict
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Canonical 4-phase scaffold
# ---------------------------------------------------------------------------
#
# Year-quarter → canonical phase. This is the deterministic fallback used
# when the upstream astrology timeline payload doesn't carry phase data.
# These phase names were chosen to map cleanly onto the user-facing
# pressure_type vocabulary that the Life Interpreter already understands
# (no astrology jargon).
#
_QUARTER_PHASES: List[Dict[str, str]] = [
    {
        "name":           "Recognition",
        "period_label":   "Q1",
        "pressure_type":  "clarity emerging",
        "description":    (
            "Patterns that have been quietly building become visible. "
            "What you've been ignoring starts to ask for attention."
        ),
    },
    {
        "name":           "Confrontation",
        "period_label":   "Q2",
        "pressure_type":  "avoidance becoming costly",
        "description":    (
            "What you've been avoiding starts to cost you something real. "
            "The longer you delay, the higher the price."
        ),
    },
    {
        "name":           "Crossroads",
        "period_label":   "Q3",
        "pressure_type":  "choice point",
        "description":    (
            "A genuine decision window opens. Both paths are real; "
            "neither is free. The body knows which one is correct."
        ),
    },
    {
        "name":           "Integration",
        "period_label":   "Q4",
        "pressure_type":  "settling into form",
        "description":    (
            "Whatever you chose at the crossroads begins to take "
            "concrete shape. The pace slows; the stakes feel earned."
        ),
    },
]

# ---------------------------------------------------------------------------
# Pressure-type classification
# ---------------------------------------------------------------------------
#
# When a payload provides a phase name we don't recognise, we infer the
# pressure_type via lightweight keyword scanning over the phase name +
# description. Order matters: more specific patterns should be checked
# first.
#
_PRESSURE_RULES: List[Tuple[str, List[str]]] = [
    ("avoidance becoming costly", [
        "confront", "avoid", "ignored", "reckon", "cost", "consequence",
        "boil", "head-on", "force",
    ]),
    ("choice point", [
        "crossroad", "decide", "decision", "choose", "fork", "either/or",
        "commit", "pick a side", "act or wait",
    ]),
    ("settling into form", [
        "integrat", "consolidat", "land", "form", "settle", "anchor",
        "name it", "stabili", "grounding",
    ]),
    ("clarity emerging", [
        "recogn", "surface", "emerg", "reveal", "becoming visible",
        "naming", "see clearly", "wake up", "notice",
    ]),
    ("trigger", [
        "trigger", "activat", "spark", "catalys",
    ]),
    ("release", [
        "release", "let go", "shed", "close out", "finish",
    ]),
]


def _classify_pressure(text: str) -> str:
    """Return a canonical pressure_type by scanning text for keyword cues."""
    t = (text or "").lower()
    for label, kws in _PRESSURE_RULES:
        if any(kw in t for kw in kws):
            return label
    return "clarity emerging"


# ---------------------------------------------------------------------------
# Turning-point type classification
# ---------------------------------------------------------------------------
_TURNING_TYPE_RULES: List[Tuple[str, List[str]]] = [
    ("confrontation", [
        "confront", "head-on", "no longer ignore", "reckon",
        "avoid", "impossible to keep", "stops being optional",
        "comes due", "due", "stops being",
    ]),
    ("decision",      ["decide", "decision", "choose", "fork", "crossroad", "choice", "must choose"]),
    ("integration",   ["integrat", "name it", "name what", "settle", "consolidat", "land", "starts to land"]),
    ("release",       ["release", "let go", "close out", "shed", "end"]),
    ("trigger",       ["trigger", "spark", "set off", "catalys"]),
]


def _classify_turning_type(text: str) -> str:
    t = (text or "").lower()
    for label, kws in _TURNING_TYPE_RULES:
        if any(kw in t for kw in kws):
            return label
    return "trigger"


# ---------------------------------------------------------------------------
# Domain relevance keyword maps
# ---------------------------------------------------------------------------
#
# Each domain has a list of (regex, weight) pairs. Higher weight = stronger
# evidence. We scan all timeline content (year theme, phases, turning
# points) and accumulate per-domain hits. A short human-readable note is
# returned for each domain that scored above zero.
#
_DOMAIN_KEYWORDS: Dict[str, List[Tuple[str, int]]] = {
    "relationships": [
        (r"\brelationship", 3),
        (r"\bintimacy", 3),
        (r"\bpartner", 3),
        (r"\bconnection", 2),
        (r"\bbond(ing|s)?\b", 2),
        (r"\bmarriage|\bdivorce", 3),
        (r"\bdating|\bromance", 2),
        (r"\bshared resources?\b", 2),
        (r"\btrust\b", 1),
    ],
    "work": [
        (r"\bwork\b", 3),
        (r"\bcareer", 3),
        (r"\bjob\b", 2),
        (r"\bresponsibilit", 2),
        (r"\bvisibility", 2),
        (r"\boutput\b", 2),
        (r"\bachievement", 2),
        (r"\bambition", 2),
        (r"\bpurpose\b", 1),
        (r"\bproject", 1),
    ],
    "money": [
        (r"\bmoney\b", 3),
        (r"\bfinanc", 3),
        (r"\bincome", 3),
        (r"\bwealth", 2),
        (r"\bsalary|\bcompensation", 2),
        (r"\bdebt|\bsavings", 2),
        (r"\bshared resources?\b", 3),  # canonical Pluto-in-2nd-house style
        (r"\bvalue\b", 1),
    ],
    "self": [
        (r"\bidentity", 3),
        (r"\bauthentic", 3),
        (r"\bbecoming\b", 2),
        (r"\bself\b", 2),
        (r"\binner\b", 1),
        (r"\bgrowth\b", 1),
        (r"\bcharacter", 1),
        (r"\bvalues\b", 1),
    ],
    "health": [
        (r"\bhealth", 3),
        (r"\bbody\b", 3),
        (r"\bvitality", 2),
        (r"\brest\b", 2),
        (r"\bsleep\b", 2),
        (r"\benergy\b", 1),
        (r"\bnervous system", 2),
        (r"\bburnout", 2),
        (r"\bstress\b", 1),
    ],
    "family": [
        (r"\bfamily\b", 3),
        (r"\bparent", 2),
        (r"\bsibling", 2),
        (r"\bchild(ren)?\b", 2),
        (r"\bhome\b", 2),
        (r"\bbelonging", 2),
        (r"\binheritance", 2),
        (r"\broots?\b", 1),
    ],
    "friends": [
        (r"\bfriend", 3),
        (r"\bcommunity", 3),
        (r"\bnetwork", 2),
        (r"\bsocial\b", 1),
        (r"\bcircle\b", 1),
        (r"\bgroup\b", 1),
    ],
}


_DOMAIN_NOTE_TEMPLATES: Dict[str, str] = {
    "relationships": (
        "intimacy and connection are under pressure to refine, "
        "not just expand"
    ),
    "work": (
        "responsibility and visibility are being raised — the bar "
        "for what counts as 'real output' is moving up"
    ),
    "money": (
        "shared resources and value exchange are surfacing — what "
        "you give versus what you receive is being reweighed"
    ),
    "self": (
        "identity is shifting — what you used to call 'me' may not "
        "fit what is now becoming"
    ),
    "health": (
        "the body is asking for a different pace — pressure here "
        "tends to surface as fatigue, not crisis"
    ),
    "family": (
        "family ties and belonging are being renegotiated — old "
        "roles no longer hold the same shape"
    ),
    "friends": (
        "community and network composition are shifting — who is "
        "actually with you may be revealed"
    ),
}


def _scan_domain_relevance(text: str) -> Dict[str, str]:
    """
    Scan free text for domain keyword hits and return a dict of
    domain → short human note. Only domains that scored above zero are
    included.
    """
    if not text:
        return {}
    t = text.lower()
    relevance: Dict[str, str] = {}
    for domain, rules in _DOMAIN_KEYWORDS.items():
        score = 0
        for pattern, weight in rules:
            hits = len(re.findall(pattern, t))
            score += hits * weight
        if score > 0:
            relevance[domain] = _DOMAIN_NOTE_TEMPLATES[domain]
    return relevance


# ---------------------------------------------------------------------------
# Date → quarter helper
# ---------------------------------------------------------------------------

def _resolve_current_date(current_date: Any) -> datetime:
    """Coerce a wide variety of date inputs into a datetime."""
    if isinstance(current_date, datetime):
        return current_date
    if isinstance(current_date, date):
        return datetime(current_date.year, current_date.month, current_date.day)
    if isinstance(current_date, str):
        # Accept ISO date or datetime
        s = current_date.strip()
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(s.replace("Z", ""))
        except (ValueError, AttributeError):
            pass
    return datetime.utcnow()


def _quarter_index(dt: datetime) -> int:
    """Return 0..3 for Q1..Q4."""
    m = dt.month
    if m <= 3:
        return 0
    if m <= 6:
        return 1
    if m <= 9:
        return 2
    return 3


# ---------------------------------------------------------------------------
# Payload parsing
# ---------------------------------------------------------------------------
#
# Different upstream sources use slightly different field names. We
# normalise them gracefully here. Recognised aliases:
#
#   year_theme        ← year_theme | year_question | theme
#   arc               ← arc | year_arc | primary_arc
#   phases            ← phases | quarterly_phases | key_phases
#   turning_points    ← turning_points | primary_turning_points | windows

def _extract_year_theme(payload: Optional[Dict[str, Any]]) -> Optional[str]:
    if not payload:
        return None
    for key in ("year_theme", "year_question", "theme", "year_summary"):
        v = payload.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _extract_arc(payload: Optional[Dict[str, Any]]) -> Optional[str]:
    if not payload:
        return None
    for key in ("arc", "year_arc", "primary_arc", "summary"):
        v = payload.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _extract_phases(payload: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return a list of phase dicts. Empty list if none found."""
    if not payload:
        return []
    for key in ("phases", "quarterly_phases", "key_phases"):
        v = payload.get(key)
        if isinstance(v, list) and v:
            return [p for p in v if isinstance(p, dict)]
    return []


def _extract_turning_points(payload: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not payload:
        return []
    for key in ("turning_points", "primary_turning_points", "windows", "decision_windows"):
        v = payload.get(key)
        if isinstance(v, list) and v:
            return [tp for tp in v if isinstance(tp, dict)]
    return []


# ---------------------------------------------------------------------------
# Phase normalisation
# ---------------------------------------------------------------------------

def _normalise_phase(p: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise a single phase dict to the {name, period, pressure_type, description} shape."""
    name = (
        p.get("name") or p.get("label") or p.get("phase_name") or p.get("title") or ""
    ).strip() or "Unnamed phase"

    period = (
        p.get("period")
        or p.get("date_range")
        or p.get("dates")
        or p.get("when")
        or p.get("period_label")
        or ""
    )
    period = str(period).strip()

    description = (
        p.get("description")
        or p.get("summary")
        or p.get("what_happens")
        or p.get("what_actually_happening")
        or p.get("body")
        or ""
    )
    description = str(description).strip()

    pressure_type = (p.get("pressure_type") or "").strip()
    if not pressure_type:
        pressure_type = _classify_pressure(f"{name} {description}")

    return {
        "name":          name,
        "period":        period or None,
        "pressure_type": pressure_type,
        "description":   description or None,
    }


def _normalise_turning_point(tp: Dict[str, Any]) -> Dict[str, Any]:
    timing = (
        tp.get("timing")
        or tp.get("date")
        or tp.get("when")
        or tp.get("period")
        or ""
    )
    timing = str(timing).strip()

    what_activates = (
        tp.get("what_activates")
        or tp.get("trigger")
        or tp.get("why_this_matters")
        or tp.get("description")
        or ""
    )
    what_activates = str(what_activates).strip()

    what_becomes_clear = (
        tp.get("what_becomes_clear")
        or tp.get("clarity")
        or tp.get("realization")
        or ""
    )
    what_becomes_clear = str(what_becomes_clear).strip()

    if_avoided = (
        tp.get("if_avoided")
        or tp.get("what_happens_if_avoided")
        or tp.get("consequence")
        or ""
    )
    if_avoided = str(if_avoided).strip()

    tp_type = (tp.get("type") or "").strip()
    if tp_type not in {"trigger", "decision", "integration", "release", "confrontation"}:
        tp_type = _classify_turning_type(
            f"{what_activates} {what_becomes_clear} {if_avoided}"
        )

    return {
        "timing":             timing or None,
        "type":               tp_type,
        "what_activates":     what_activates or None,
        "what_becomes_clear": what_becomes_clear or None,
        "if_avoided":         if_avoided or None,
    }


# ---------------------------------------------------------------------------
# Current/next phase resolution
# ---------------------------------------------------------------------------

_PHASE_NAME_QUARTER_HINTS: List[Tuple[str, int]] = [
    ("recognition",   0),
    ("confrontation", 1),
    ("crossroads",    2),
    ("integration",   3),
]


def _phase_quarter_hint(phase_name: str, period_label: str) -> Optional[int]:
    """Try to infer which quarter a phase belongs to."""
    n = (phase_name or "").lower()
    for stem, q in _PHASE_NAME_QUARTER_HINTS:
        if stem in n:
            return q

    pl = (period_label or "").lower()
    if "q1" in pl or "first quarter" in pl:
        return 0
    if "q2" in pl or "second quarter" in pl:
        return 1
    if "q3" in pl or "third quarter" in pl:
        return 2
    if "q4" in pl or "fourth quarter" in pl:
        return 3

    # Month name lookups
    months = [
        ("january", 0),  ("february", 0), ("march", 0),
        ("april", 1),    ("may", 1),      ("june", 1),
        ("july", 2),     ("august", 2),   ("september", 2),
        ("october", 3),  ("november", 3), ("december", 3),
    ]
    for m, q in months:
        if m in pl:
            return q
    return None


def _resolve_current_and_next(
    phases: List[Dict[str, Any]],
    current_dt: datetime,
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """
    Resolve which phase is current and which is next, given a list of
    normalised phases and the current date.

    Strategy
    --------
    1. If any phase is explicitly tagged is_current, honour it.
    2. Else, use the quarter inferred from each phase's name / period
       label. Pick the phase whose quarter matches the current quarter.
    3. If no match, fall back to the first phase (covers "before first
       phase" case).
    """
    if not phases:
        # Synthesise from the canonical scaffold
        q = _quarter_index(current_dt)
        scaffold = _QUARTER_PHASES
        cur = {
            "name":          scaffold[q]["name"],
            "period":        scaffold[q]["period_label"],
            "pressure_type": scaffold[q]["pressure_type"],
            "description":   scaffold[q]["description"],
        }
        nxt_idx = (q + 1) % 4
        nxt = {
            "name":          scaffold[nxt_idx]["name"],
            "period":        scaffold[nxt_idx]["period_label"],
            "pressure_type": scaffold[nxt_idx]["pressure_type"],
            "description":   scaffold[nxt_idx]["description"],
        }
        return cur, nxt

    # 1. Honour explicit is_current tag
    for i, p in enumerate(phases):
        if p.get("is_current"):
            cur = phases[i]
            nxt = phases[i + 1] if i + 1 < len(phases) else None
            return cur, nxt

    # 2. Quarter match
    cur_q = _quarter_index(current_dt)
    for i, p in enumerate(phases):
        q = _phase_quarter_hint(p.get("name", ""), p.get("period") or "")
        if q == cur_q:
            cur = phases[i]
            nxt = phases[i + 1] if i + 1 < len(phases) else None
            return cur, nxt

    # 3. Before any matching quarter — use first phase
    cur = phases[0]
    nxt = phases[1] if len(phases) > 1 else None
    return cur, nxt


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_timeline_context(
    user_id: str,
    astrology_timeline_payload: Optional[Dict[str, Any]] = None,
    current_date: Any = None,
    domain: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convert an astrology timeline payload into the structured
    decision/timing context the Life Interpreter consumes.

    Parameters
    ----------
    user_id
        Used only for logging / cache-key hooks.
    astrology_timeline_payload
        The upstream timeline content. Tolerant to multiple shapes:
        see _extract_* functions for recognised aliases. Pass `None`
        or `{}` to use the deterministic 4-phase scaffold.
    current_date
        Optional `datetime`, `date` or ISO string. Defaults to "now".
    domain
        Optional Ask-chip domain (e.g. "relationships"). When provided,
        the returned `domain_relevance` will still include all domains
        that scored above zero, but a future caller can use this hint
        to highlight the chip-relevant note.

    Returns
    -------
    dict with the keys spec'd in the task brief:
        year_theme, current_phase, next_phase, key_turning_points,
        domain_relevance, failure_mode, confidence
    """
    dt = _resolve_current_date(current_date)
    payload = astrology_timeline_payload or {}

    # 1. Year theme + arc -----------------------------------------------------
    year_theme = _extract_year_theme(payload)
    arc = _extract_arc(payload)

    # 2. Phases ---------------------------------------------------------------
    raw_phases = _extract_phases(payload)
    phases = [_normalise_phase(p) for p in raw_phases]
    current_phase, next_phase = _resolve_current_and_next(phases, dt)

    # 3. Turning points -------------------------------------------------------
    raw_tps = _extract_turning_points(payload)
    key_turning_points = [_normalise_turning_point(tp) for tp in raw_tps]

    # 4. Domain relevance -----------------------------------------------------
    # Aggregate text for keyword scanning.
    scan_parts: List[str] = []
    if year_theme:
        scan_parts.append(year_theme)
    if arc:
        scan_parts.append(arc)
    for p in phases:
        if p.get("name"):
            scan_parts.append(p["name"])
        if p.get("description"):
            scan_parts.append(p["description"])
    for tp in key_turning_points:
        for k in ("what_activates", "what_becomes_clear", "if_avoided"):
            if tp.get(k):
                scan_parts.append(tp[k])
    full_scan = " \n ".join(scan_parts)
    domain_relevance = _scan_domain_relevance(full_scan)

    # 5. Failure mode ---------------------------------------------------------
    # Extract from explicit field; else aggregate from turning points'
    # "if_avoided" content; else leave None.
    failure_mode: Optional[str] = None
    for k in ("failure_mode", "what_happens_if_avoided", "drift_pattern"):
        v = payload.get(k)
        if isinstance(v, str) and v.strip():
            failure_mode = v.strip()
            break
    if not failure_mode:
        avoidances = [
            tp["if_avoided"] for tp in key_turning_points
            if tp.get("if_avoided")
        ]
        if avoidances:
            # Aggregate into a single sentence — keep concise.
            failure_mode = (
                "If the choice points are skipped: "
                + "; ".join(avoidances[:2])
            ).strip()

    # 6. Confidence -----------------------------------------------------------
    # Heuristic:
    #   - high   if year_theme + arc + ≥3 phases + ≥1 turning point
    #   - medium if year_theme OR arc, plus phases or turning points
    #   - low    otherwise (using deterministic scaffold)
    confidence = "low"
    has_theme_or_arc = bool(year_theme or arc)
    has_rich_phases = len(phases) >= 3
    has_tp = bool(key_turning_points)
    if has_theme_or_arc and has_rich_phases and has_tp:
        confidence = "high"
    elif has_theme_or_arc and (phases or key_turning_points):
        confidence = "medium"
    elif phases or key_turning_points:
        confidence = "medium"

    # Track which upstream produced this — payload's explicit `source`
    # wins; otherwise we infer from whether we got real phases parsed
    # out of the payload (real) or fell back to the canonical scaffold.
    inferred_source = (payload or {}).get("source")
    if not inferred_source:
        inferred_source = "real_astrology_timeline" if phases else "deterministic_scaffold"

    result: Dict[str, Any] = {
        "year_theme":          year_theme,
        "current_phase":       current_phase,
        "next_phase":          next_phase,
        "key_turning_points":  key_turning_points,
        "domain_relevance":    domain_relevance,
        "failure_mode":        failure_mode,
        "confidence":          confidence,
        "source":              inferred_source,
    }

    # Optional: surface the chip-relevant note for caller convenience.
    if domain and domain in domain_relevance:
        result["chip_domain_note"] = domain_relevance[domain]

    logger.debug(
        "[AstrologyTimelineInterpreter] user=%s confidence=%s phase=%s next=%s",
        user_id,
        confidence,
        (current_phase or {}).get("name"),
        (next_phase or {}).get("name"),
    )
    return result


__all__ = ["build_timeline_context"]
