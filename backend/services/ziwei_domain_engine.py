"""
Zi Wei Domain Pattern Engine — invisible domain-origin layer.

Architectural role
==================
Each life domain (self / work / money / relationships / health / friends /
family) gets its OWN causal origin instead of being a re-projection of a
single global pattern. We use Zi Wei Dou Shu's palace structure as the
internal mapping ONLY — the user never sees the term, the palace name,
or any Chinese terminology.

Why a placeholder
=================
Full Zi Wei chart computation (palace placement, 14 main stars, 4 化 transformations,
etc.) requires a different ephemeris and chart engine than what is currently
hooked up. This module ships a STRUCTURED PLACEHOLDER that:

  1. Maps each domain to its canonical palace identifier (internally).
  2. Returns a domain-origin contract: {domain_pattern_origin, domain_tension,
     domain_failure_mode, domain_evolution_hint, confidence, source}.
  3. Lightly colours the seed using whatever chart data is already
     available (BaZi element, astrology house posture, lifeline evidence)
     so two users with the same domain do not get the same wording.
  4. Has the same OUTPUT CONTRACT as a future fully-computed Zi Wei layer
     would, so we can swap in real palace/star derivation later without
     changing callers.

The output is fed into Life Synthesis as the DOMAIN-CAUSAL SEED, and
into Ask About My Life when the user picks money / family / health /
friends so those chips no longer feel like reused Self/Work/Relationships
copy.

NEVER expose to UI
==================
Banned in user-facing copy (the synthesis prompt scrubs these too):
  zi wei · ziwei · zi wei dou shu · purple star · 命宫 · 官禄宫 · 财帛宫 ·
  夫妻宫 · 疾厄宫 · 交友宫 · 父母宫 · palace · stars · chart · destiny
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain → palace map (internal use only — never surface these names)
# ---------------------------------------------------------------------------

DOMAIN_TO_PALACE: Dict[str, Dict[str, str]] = {
    "self":          {"id": "life",     "cn": "命宫",   "en": "Life Palace"},
    "work":          {"id": "career",   "cn": "官禄宫", "en": "Career Palace"},
    "money":         {"id": "wealth",   "cn": "财帛宫", "en": "Wealth Palace"},
    "relationships": {"id": "spouse",   "cn": "夫妻宫", "en": "Spouse Palace"},
    "health":        {"id": "health",   "cn": "疾厄宫", "en": "Health Palace"},
    "friends":       {"id": "friends",  "cn": "交友宫", "en": "Friends Palace"},
    "family":        {"id": "parents",  "cn": "父母宫", "en": "Parents Palace"},
}


# ---------------------------------------------------------------------------
# Per-palace base frames.
#
# These describe what the domain is REALLY ABOUT in plain behavioural
# language. They are intentionally not personality-language and not fate
# language. They give the LLM a domain-causal axis instead of the engine
# defaulting to "global pattern projected into N domains".
# ---------------------------------------------------------------------------

_PALACE_FRAMES: Dict[str, Dict[str, str]] = {
    # SELF — Life Palace (命宫)
    "life": {
        "domain_pattern_origin":
            "the way you have come to occupy your own life — the inner posture you take "
            "before anyone else has had a say",
        "domain_tension":
            "internal pressure — the standard you carry for yourself before any external "
            "demand has even arrived",
        "domain_failure_mode":
            "self-trust gets replaced by self-correction; you start treating yourself the "
            "way the pattern treats everything else",
        "domain_evolution_hint":
            "shifts when you stop performing identity and begin inhabiting it — when there "
            "is room to exist without proving",
    },
    # WORK — Career Palace (官禄宫)
    "career": {
        "domain_pattern_origin":
            "how responsibility accumulates around you — the way work finds its way to "
            "your shoulders, often before you have agreed to it",
        "domain_tension":
            "weight that arrives faster than the structure to hold it — output outpaces "
            "the system that was supposed to carry the output",
        "domain_failure_mode":
            "the work begins routing through your presence rather than through the system; "
            "leverage erodes into ownership",
        "domain_evolution_hint":
            "evolves when leverage replaces ownership — when a clear handoff exists that is "
            "not conditional on you staying in the loop",
    },
    # MONEY — Wealth Palace (财帛宫)
    "wealth": {
        "domain_pattern_origin":
            "the way value enters your life and the container you have built to hold it — "
            "earning, spending, keeping, and what you allow yourself to receive",
        "domain_tension":
            "what comes in is shaped by what you believe you can keep; income tracks the "
            "size of the container rather than the size of the effort",
        "domain_failure_mode":
            "earnings move faster than the container; what arrives gets converted into "
            "obligation, not capacity, and the felt-sense of money stays scarce",
        "domain_evolution_hint":
            "evolves when accumulation becomes a deliberate decision rather than a residual "
            "one — when keeping becomes its own action, not what's left over",
    },
    # RELATIONSHIPS — Spouse Palace (夫妻宫)
    "spouse": {
        "domain_pattern_origin":
            "the rhythm of how you let someone close — the pacing between reaching toward "
            "and being met",
        "domain_tension":
            "your pace and the other person's response do not always meet in time; the "
            "signal arrives before the reply has had room to form",
        "domain_failure_mode":
            "distance forms before either side names it; the other person stops reaching "
            "the real you and reaches the version that is already moving",
        "domain_evolution_hint":
            "deepens when staying becomes louder than reaching — when the pause is long "
            "enough for the other person to actually arrive",
    },
    # HEALTH — Health Palace (疾厄宫)
    "health": {
        "domain_pattern_origin":
            "where strain finds the body before the mind notices — the somatic ledger of "
            "what hasn't been put down yet",
        "domain_tension":
            "the body carries what the calendar refuses to drop; energy is treated as "
            "renewable when in this season it is finite",
        "domain_failure_mode":
            "the body becomes the only signal loud enough to interrupt the pattern; rest "
            "gets earned instead of allowed",
        "domain_evolution_hint":
            "shifts when rest is allowed to be a signal, not a reward — when the body's "
            "early language is heard before it has to escalate",
    },
    # FRIENDS — Friends Palace (交友宫)
    "friends": {
        "domain_pattern_origin":
            "who shows up around you and on what terms — the field of people the pattern "
            "selects for and selects against",
        "domain_tension":
            "the field around you is shaped by what you let in and what you don't; the "
            "people who can keep up are the ones who stay close",
        "domain_failure_mode":
            "the circle narrows by exhaustion rather than by choice; reciprocity quietly "
            "drifts out of balance",
        "domain_evolution_hint":
            "evolves when the circle is curated rather than inherited — when proximity is a "
            "decision rather than a default",
    },
    # FAMILY — Parents Palace (父母宫)
    "family": {
        "domain_pattern_origin":
            "the inheritance you did not ask for and cannot fully refuse — the family "
            "voice that often answers before yours does",
        "domain_tension":
            "where the family default still routes the response; the loyalty patterns "
            "answer in your name",
        "domain_failure_mode":
            "what you actually want gets shaped around keeping the peace; the cost of the "
            "inheritance compounds quietly across years",
        "domain_evolution_hint":
            "shifts when you decide what to keep, not just what to leave — when the inheritance "
            "is sorted instead of inherited whole",
    },
}


# ---------------------------------------------------------------------------
# Light personalisation hooks — uses already-available chart / lifeline data
# to colour the seed without doing real palace/star math yet.
# ---------------------------------------------------------------------------

# Element flavour for each palace's tension language. Keeps two users with
# the same domain from receiving identical seeds.
_ELEMENT_FLAVOUR: Dict[str, str] = {
    "wood":  "the pattern leans toward expansion that outgrows the room it has",
    "fire":  "the pattern leans toward intensity that burns hotter than its surface",
    "earth": "the pattern leans toward holding more weight than the structure was built for",
    "metal": "the pattern leans toward refining past the point where the result still helps",
    "water": "the pattern leans toward absorbing the field until self and field stop being separate",
}


def _bazi_element(chart: Optional[Dict[str, Any]]) -> Optional[str]:
    if not isinstance(chart, dict):
        return None
    bazi = chart.get("bazi") or {}
    dm = bazi.get("day_master") or {}
    el = (dm.get("element") or "").strip().lower() or None
    return el if el in _ELEMENT_FLAVOUR else None


def _lifeline_colour(lifeline_summary: Optional[Dict[str, Any]], domain: str) -> Optional[str]:
    """Return a short lifeline-evidence echo string for this domain, or None."""
    if not isinstance(lifeline_summary, dict):
        return None
    domains = lifeline_summary.get("domains") or {}
    block = domains.get(domain) or {}
    titles = block.get("recent_titles") or block.get("titles") or []
    if titles:
        # Up to 2 titles, just to anchor the seed in lived material — no quoting.
        return "this domain has shown up in the lived ledger more than once"
    themes = block.get("themes") or []
    if themes:
        return "this domain leans on themes the user has already lived"
    return None


def _confidence(chart: Optional[Dict[str, Any]], lifeline_summary: Optional[Dict[str, Any]]) -> str:
    """Confidence we can express on this domain origin given current inputs."""
    has_chart = isinstance(chart, dict) and bool(chart.get("bazi") or chart.get("astrology"))
    has_ll = isinstance(lifeline_summary, dict) and bool(lifeline_summary.get("domains"))
    if has_chart and has_ll:
        return "medium"
    if has_chart or has_ll:
        return "low-medium"
    return "low"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

SUPPORTED_DOMAINS: List[str] = list(DOMAIN_TO_PALACE.keys())


def generate_ziwei_domain_pattern(
    domain: str,
    *,
    chart: Optional[Dict[str, Any]] = None,
    lifeline_summary: Optional[Dict[str, Any]] = None,
    pattern_memory: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Return a domain-origin contract for the requested domain.

    The output is consumed by Life Synthesis and Ask About My Life as the
    PRIMARY domain-causal seed. It must NOT contain palace names, Chinese
    terms, or Zi Wei terminology — those are scrubbed before reaching the
    LLM render step.

    Returns
    -------
    {
      "domain":                "self|work|money|relationships|health|friends|family",
      "palace":                "life|career|wealth|spouse|health|friends|parents",
      "domain_pattern_origin": str,
      "domain_tension":        str,
      "domain_failure_mode":   str,
      "domain_evolution_hint": str,
      "confidence":            "high|medium|low-medium|low",
      "source":                "ziwei_placeholder" | "ziwei_computed",
    }
    """
    domain_norm = (domain or "").strip().lower()
    if domain_norm not in DOMAIN_TO_PALACE:
        logger.warning("[ZiWei] unsupported domain=%r — returning empty contract", domain)
        return {
            "domain": domain_norm,
            "palace": None,
            "domain_pattern_origin": "",
            "domain_tension": "",
            "domain_failure_mode": "",
            "domain_evolution_hint": "",
            "confidence": "low",
            "source": "ziwei_placeholder",
        }

    palace_id = DOMAIN_TO_PALACE[domain_norm]["id"]
    frame = dict(_PALACE_FRAMES[palace_id])  # copy so we can colour without mutating

    # Element-based colouring on tension (one extra clause, semicolon-joined,
    # so the LLM receives a slightly different starting point per user).
    element = _bazi_element(chart)
    if element and _ELEMENT_FLAVOUR.get(element):
        frame["domain_tension"] = (
            frame["domain_tension"] + "; " + _ELEMENT_FLAVOUR[element]
        )

    # Lifeline echo on origin — anchors the seed in lived evidence when present.
    ll_echo = _lifeline_colour(lifeline_summary, domain_norm)
    if ll_echo:
        frame["domain_pattern_origin"] = (
            frame["domain_pattern_origin"] + "; " + ll_echo
        )

    # Pattern memory recurrence — adds repetition awareness on the failure mode.
    if isinstance(pattern_memory, dict):
        match_count = pattern_memory.get("match_count") or 0
        if isinstance(match_count, int) and match_count >= 3:
            frame["domain_failure_mode"] = (
                frame["domain_failure_mode"]
                + "; this exact shape has shown up multiple times before — write it as a loop, not a first-time event"
            )

    return {
        "domain":                domain_norm,
        "palace":                palace_id,
        "domain_pattern_origin": frame["domain_pattern_origin"],
        "domain_tension":        frame["domain_tension"],
        "domain_failure_mode":   frame["domain_failure_mode"],
        "domain_evolution_hint": frame["domain_evolution_hint"],
        "confidence":            _confidence(chart, lifeline_summary),
        "source":                "ziwei_placeholder",
    }
