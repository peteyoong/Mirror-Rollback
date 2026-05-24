"""
Astrology Chat Intent Router
============================
Build marker: astro-chat-transit-grounding-v1

Tiny pattern-matching layer that runs BEFORE the astrology-lens LLM call.
Classifies the user's question into one of four strict data_modes so the
LLM is constrained to a single answering mode and cannot silently fall
back (e.g., a transit question degrading into a natal answer).

Data modes
----------
  natal_object       — "where is my natal Chiron?", "what sign is my Sun?"
  transit_object     — "where is Chiron now?", "where is Chiron in my transit chart?"
  transit_to_natal   — "is Uranus aspecting my natal Sun?", "is Saturn conjunct my Venus?"
  timeline_summary   — "what's happening this week / this month / year ahead?"

Returns None when the question doesn't match a deterministic-lookup intent
(the regular chat flow handles those).
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional, Tuple

from services.transit_object_engine import resolve_object_name

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Body alias regex — same surface as the engine's resolver but as a
# capturing pattern so we can find a body name inside free-text questions.
# ---------------------------------------------------------------------------
_BODY_PATTERNS = [
    r"\bsun\b", r"\bmoon\b", r"\bluna\b",
    r"\bmercury\b", r"\bvenus\b", r"\bmars\b",
    r"\bjupiter\b", r"\bjove\b", r"\bsaturn\b",
    r"\buranus\b", r"\bneptune\b", r"\bpluto\b",
    r"\bchiron\b",
    r"\bnorth node\b", r"\brahu\b", r"\btrue node\b", r"\bmean node\b",
    r"\bsouth node\b", r"\bketu\b",
    r"\bascendant\b", r"\basc\b", r"\brising( sign)?\b",
    r"\bmc\b", r"\bmidheaven\b",
    # Not-yet-enabled — we still detect so we can return a clean refusal.
    r"\bjuno\b", r"\bvertex\b", r"\blilith\b", r"\bblack moon( lilith)?\b",
    r"\bceres\b", r"\bpallas\b", r"\bvesta\b", r"\beris\b",
]
_BODY_RE = re.compile("|".join(_BODY_PATTERNS), re.IGNORECASE)

# Anything explicitly anchoring to NOW / TODAY / CURRENTLY / TRANSIT.
_TRANSIT_NOW_PATTERNS = [
    r"\bnow\b", r"\btoday\b", r"\bcurrently\b", r"\bright now\b",
    r"\btransit(s|ing)?\b", r"\btransit chart\b",
    r"\bthis week\b", r"\bthis month\b", r"\bthis year\b",
]
_TRANSIT_NOW_RE = re.compile("|".join(_TRANSIT_NOW_PATTERNS), re.IGNORECASE)

# Anything anchoring to NATAL.
_NATAL_PATTERNS = [
    r"\bnatal\b", r"\bmy natal\b",
    r"\bbirth chart\b", r"\bin my chart\b(?!.*transit)",
]
_NATAL_RE = re.compile("|".join(_NATAL_PATTERNS), re.IGNORECASE)

# Aspect query patterns.
_ASPECT_RE = re.compile(
    r"\b(aspect|aspecting|conjunct|conjunction|square|opposition|opposite|trine|sextile|quincunx)\b",
    re.IGNORECASE,
)

# Timeline / week / month broad questions.
_TIMELINE_RE = re.compile(
    r"\b(this week|this month|this year|year ahead|next week|next month|next year|"
    r"what'?s coming|upcoming|timeline|key dates?|important dates?)\b",
    re.IGNORECASE,
)

# Solar return — yearly chart anchored on Sun's tropical return to natal degree.
# astrology-chat-grounding-v2
_SOLAR_RETURN_RE = re.compile(
    r"\b("
    r"solar\s*return|"          # "solar return", "solar-return", "solarreturn"
    r"sr\s*ascendant|"           # "SR ascendant"
    r"sr\s*chart|"
    r"return\s*chart|"
    r"return\s*ascendant|"
    r"birthday\s*chart|"
    r"yearly\s*return|"
    r"annual\s*chart|"
    r"annual\s*return"
    r")\b",
    re.IGNORECASE,
)

# Natal object query — "tell me about my Lilith", "what does my Chiron mean",
# "what house is my Vertex in". Distinct from positional/aspect queries because
# we want a SPECIFIC named natal placement read.   astrology-chat-master-interpreter-v3
_NATAL_OBJECT_BODIES_RE = re.compile(
    r"\b("
    r"lilith|black\s*moon|bml|mean\s*lilith|true\s*lilith|"
    r"chiron|"
    r"vertex|anti.?vertex|"
    r"north\s*node|south\s*node|rahu|ketu|nodes?|"
    r"part\s*of\s*fortune|pars\s*fortuna|fortuna|"
    r"juno|ceres|pallas|vesta|eris"
    r")\b",
    re.IGNORECASE,
)
_NATAL_OBJECT_TRIGGER_RE = re.compile(
    r"\b("
    r"tell\s*me\s*about|what\s*does|what's|whats|what\s*is|where\s*is|"
    r"my|read\s*my|interpret|natal|in\s*my\s*chart"
    r")\b",
    re.IGNORECASE,
)

# Positional question shapes — "where is X", "what sign is X", "what house is X".
_POSITIONAL_RE = re.compile(
    r"\b(where(?:'s| is)|what sign (?:is|does)|what house (?:is|does)|in what (?:sign|house))\b",
    re.IGNORECASE,
)


def _extract_body(text: str) -> Optional[str]:
    """Return the first canonical body name mentioned in the text."""
    m = _BODY_RE.search(text)
    if not m:
        return None
    return resolve_object_name(m.group(0))


def classify_astrology_intent(message: str) -> Optional[Dict[str, Any]]:
    """Classify an incoming astrology-lens message.

    Returns a dict with at minimum:
        { "data_mode": <str>, "object": Optional[str], "natural_form": <str> }
    or None if no deterministic mode matched (caller stays on free-form chat).
    """
    if not message or not isinstance(message, str):
        return None

    text = message.strip()
    body = _extract_body(text)
    has_transit_now = bool(_TRANSIT_NOW_RE.search(text))
    has_natal = bool(_NATAL_RE.search(text))
    has_aspect = bool(_ASPECT_RE.search(text))
    has_positional = bool(_POSITIONAL_RE.search(text))
    has_timeline = bool(_TIMELINE_RE.search(text))
    has_solar_return = bool(_SOLAR_RETURN_RE.search(text))
    natal_obj_body_match = _NATAL_OBJECT_BODIES_RE.search(text)
    has_natal_obj_trigger = bool(_NATAL_OBJECT_TRIGGER_RE.search(text))

    # ── natal_object (specific named body) ─────────────────────────────
    # Catches: "tell me about my Lilith", "what does my Chiron mean",
    # "what house is my Vertex in", "my north node". Must run BEFORE
    # positional/aspect handlers so the LLM doesn't try to free-form it.
    # astrology-chat-master-interpreter-v3
    if natal_obj_body_match and (has_natal_obj_trigger or has_positional or has_natal):
        obj_raw = natal_obj_body_match.group(0)
        return {
            "data_mode":    "natal_object",
            "object":       obj_raw,
            "natural_form": text,
        }

    # ── solar_return ──────────────────────────────────────────────────
    # Catches: "what's my solar return ascendant", "SR chart", "yearly
    # return", "birthday chart". Checked FIRST so "solar return ascendant"
    # doesn't get misrouted to positional/natal handling.
    # astrology-chat-grounding-v2
    if has_solar_return:
        return {
            "data_mode":    "solar_return",
            "object":       None,
            "natural_form": text,
        }

    # ── transit_to_natal ───────────────────────────────────────────────
    # Aspect verb + body → transit-to-natal aspect query.
    # NOTE: when the user writes "my natal Sun" the natal flag turns True,
    # but in aspect queries the "natal" anchor refers to the TARGET body
    # (Sun), not the transiting subject (Uranus). So we ignore has_natal
    # in this branch — the aspect verb itself is the strongest intent
    # signal we can get. astro-chat-transit-grounding-v1
    if has_aspect and body:
        return {
            "data_mode":     "transit_to_natal",
            "object":        body,
            "natural_form":  text,
        }

    # ── transit_object ────────────────────────────────────────────────
    # "where is Chiron now" / "where is Chiron in my transit chart" /
    # "what house is Saturn transiting" / "where is Chiron transiting"
    if body and (
        (has_positional and has_transit_now)
        or (has_positional and "transit" in text.lower())
        or ("transit" in text.lower() and has_positional)
    ):
        return {
            "data_mode":    "transit_object",
            "object":       body,
            "natural_form": text,
        }

    # ── natal_object ──────────────────────────────────────────────────
    # "where is my natal Chiron" / "what sign is my Sun" (no transit verb)
    if has_positional and body and has_natal and not has_transit_now:
        return {
            "data_mode":    "natal_object",
            "object":       body,
            "natural_form": text,
        }

    # ── timeline_summary ──────────────────────────────────────────────
    # Broad period questions — no specific body anchor.
    if has_timeline and not body and not has_positional:
        return {
            "data_mode":    "timeline_summary",
            "object":       None,
            "natural_form": text,
        }

    return None


def build_transit_object_proof_block(envelope: Dict[str, Any]) -> str:
    """Render the deterministic transit envelope into a strict prompt block.

    The LLM consumes this block as ground truth. It is forbidden from
    contradicting or extending the computed numbers.
    """
    if not envelope or not envelope.get("success"):
        reason = (envelope or {}).get("reason", "unknown")
        msg = (envelope or {}).get("message") or ""
        return (
            "=== DETERMINISTIC DATA — data_mode=transit_object ===\n"
            f"COMPUTATION_FAILED · reason={reason}\n"
            f"{msg}\n"
            "ABSOLUTE RULE: Do not answer outside the supplied data_mode. "
            "Do not fall back to natal data. Tell the user the engine could "
            "not compute the requested transit, then stop."
        )

    pos = envelope["transit_position"]
    aspects = envelope.get("aspects_to_natal") or []
    aspect_lines = (
        "\n".join(
            f"  · {a['aspect']} natal {a['natal_body']} · orb {a['orb']}° "
            f"({'applying' if a['applying'] else 'separating'})"
            for a in aspects
        )
        if aspects
        else "  · (no major tight aspects to natal planets right now)"
    )

    return (
        "=== DETERMINISTIC DATA — data_mode=transit_object ===\n"
        f"object:              {envelope['object']}\n"
        f"timestamp:           {envelope['timestamp']}\n"
        f"zodiac_system:       {envelope['zodiac_system']}\n"
        f"ayanamsa:            {envelope['ayanamsa']}\n"
        f"house_system:        {envelope['house_system']}\n"
        f"transit_position:    {pos['formatted']} "
        f"({pos['absolute_longitude']}° abs) "
        f"{'retrograde' if pos['retrograde'] else 'direct'}\n"
        f"natal_house:         {envelope['natal_house']}\n"
        f"aspects_to_natal:\n{aspect_lines}\n"
        "===================================================\n"
        "ABSOLUTE RULES — DO NOT VIOLATE:\n"
        " 1. Do not answer outside the supplied data_mode (transit_object).\n"
        " 2. Do not substitute natal Chiron / natal placement when the user\n"
        "    asked for transit. If you do, you have failed.\n"
        " 3. Lead with the factual placement above, then a short Mirror-style\n"
        "    interpretation grounded ONLY in those numbers.\n"
        " 4. NO therapy-blog phrasing: no 'themes around', 'healing and\n"
        "    vulnerability', 'might be useful to explore', 'what feels tender'.\n"
        " 5. If no aspects are listed, say so calmly — it is not a failure.\n"
    )


def build_transit_object_user_facing_prefix(envelope: Dict[str, Any]) -> Optional[str]:
    """Return a pre-formatted factual prefix the chat layer can prepend.

    Used when we want the answer to be deterministic AT THE PROSE LAYER too
    (e.g., to guarantee the placement string is correct verbatim, even if
    the LLM polish stage misfires).
    """
    if not envelope or not envelope.get("success"):
        return None
    pos = envelope["transit_position"]
    line = (
        f"{envelope['object']} is currently transiting "
        f"{pos['sign']} at {pos['formatted'].replace(pos['sign'], '').strip().lstrip('°').strip() or pos['degree']}°, "
        f"landing in your {_ordinal(envelope['natal_house'])} house."
    )
    aspects = envelope.get("aspects_to_natal") or []
    if aspects:
        line += "\n\nIt is currently making these notable contacts to your natal chart:"
        for a in aspects[:6]:
            line += f"\n• {a['aspect']} natal {a['natal_body']} · orb {a['orb']}°"
    else:
        line += "\n\nNo major tight aspects to your natal planets are active right now."
    return line


def _ordinal(n: int) -> str:
    if not isinstance(n, int):
        return str(n)
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


__all__ = [
    "classify_astrology_intent",
    "build_transit_object_proof_block",
    "build_transit_object_user_facing_prefix",
]
