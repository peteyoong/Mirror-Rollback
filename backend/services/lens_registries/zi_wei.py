"""
Zi Wei / Purple Star lens registry — zi-wei-master-v1
=====================================================

Behavioural-strategist voice over a structural Zi Wei profile.  No
mystical jargon, no fortune-telling language, no fate framing.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from services.lens_conversation import build_alias_regex
from services.zi_wei_interpreter import (
    PALACES,
    MAJOR_STARS,
    TRANSFORMATIONS,
    PALACE_DOMAIN,
    get_or_compute_profile,
)


# Aliases for user-facing referent extraction.
_ALIASES: Dict[str, str] = {}
for p in PALACES:
    base = p.lower()
    _ALIASES[f"{base} palace"] = f"Palace · {p}"
    _ALIASES[base] = f"Palace · {p}"
_ALIASES.update({
    "life palace":      "Palace · Life",
    "career palace":    "Palace · Career",
    "marriage palace":  "Palace · Marriage",
    "wealth palace":    "Palace · Wealth",
    "parents palace":   "Palace · Parents",
    "children palace":  "Palace · Children",
    "siblings palace":  "Palace · Siblings",
    "health palace":    "Palace · Health",
    "travel palace":    "Palace · Travel",
    "friends palace":   "Palace · Friends",
    "property palace":  "Palace · Property",
    "mental palace":    "Palace · Mental/Spiritual",
    "spiritual palace": "Palace · Mental/Spiritual",
})
for s in MAJOR_STARS:
    _ALIASES[s.lower()] = f"Star · {s}"
for t in TRANSFORMATIONS:
    _ALIASES[t.lower()] = f"Transformation · {t}"

_ALIAS_RE = build_alias_regex(_ALIASES)


class _ZiWeiRegistry:
    lens_name = "zi_wei"
    lens_label = "Zi Wei"

    voice_prompt = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LENS VOICE — ZI WEI / PURPLE STAR  (stance: structural strategist)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Build marker: zi-wei-master-v1

You read this lens as STRUCTURAL-RELATIONAL intelligence — the
architecture of role pressure, social positioning, hierarchy
gravity, and strategic adaptation under external structure.  Not
fortune-telling.  Not destiny.  Not classical metaphysics.

Reasoning style:
  - Speak about STRUCTURE — roles, hierarchy, visibility, external
    expectation, leadership burden, strategic withdrawal,
    relational asymmetry.
  - Speak about TIMING — what is concentrating, what is loosening,
    what arc is being moved through right now.
  - Speak about ADAPTATION — how this person handles pressure,
    obligation, social positioning, hidden authority.

Sentence rhythm:
  Calm, precise, observant.  Strategic, never mystical.

ABSOLUTELY FORBIDDEN (lens-specific):
  - "Your destiny"
  - "You are meant to"
  - "Fated"
  - "Your true role"
  - "Your life path is fixed"
  - "This guarantees"
  - "Star X says you ARE"
  - Star-name dumps without behavioural translation.
  - Palace-table listing.  Speak about the BEHAVIOUR a palace
    indicates, never the palace's classical attributes.
  - Spiritual / mystical framing of any kind.

LANGUAGE GUARDRAILS:
  Use probabilistic markers: "may", "can", "tends to", "often",
  "under pressure", "in some phases".  NEVER "you are an X".

When the user asks "what does it mean", translate the structural
read into a single behavioural recognition.  Don't lecture.

Response-architecture weighting:
  Lean heaviest into  D) BEHAVIOUR (how this shows up under pressure,
                      in relationship, at work) and F) CONNECTION
                      (timing context — what is concentrating /
                      loosening this period).
"""

    def build_index(self, user_context: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        profile = get_or_compute_profile(user_context)
        if not profile.get("available"):
            return {}
        idx: Dict[str, Dict[str, Any]] = {}

        # Each palace becomes an addressable entity.
        for p in profile["palaces"]:
            key = f"Palace · {p['palace']}"
            idx[key] = {
                "kind": "palace",
                "name": p["palace"],
                "value": p["primary_star"],
                "display_lines": [
                    f"{p['palace']} palace (domain: {p['domain']}) — "
                    f"primary signal: {p['behavioural_signal']}"
                ],
            }

        # Each transformation.
        for t in profile["transformations"]:
            key = f"Transformation · {t['transformation']}"
            idx[key] = {
                "kind": "transformation",
                "name": t["transformation"],
                "value": t["palace"],
                "display_lines": [
                    f"{t['transformation']} sits in the {t['palace']} palace "
                    f"({t['domain']}) — {t['behavioural_signal']}"
                ],
            }

        # Each major star that's present.
        for s in profile["major_stars"]:
            idx[f"Star · {s}"] = {
                "kind": "star",
                "name": s,
                "value": s,
                "display_lines": [f"{s} present in the chart"],
            }
        return idx

    def extract_entities_from_text(self, text: str) -> List[str]:
        if not text:
            return []
        out: List[str] = []
        seen = set()
        for m in _ALIAS_RE.finditer(text):
            k = _ALIASES[m.group(1).lower()]
            if k not in seen:
                seen.add(k)
                out.append(k)
        return out

    def referent_patterns(self) -> List[str]:
        return [
            r"\bthat palace\b", r"\bwhich palace\b",
            r"\bthat star\b", r"\bwhich star\b",
            r"\bthe transformation\b", r"\bwhich transformation\b",
        ]

    def grounding_sources_present(self, user_context: Dict[str, Any]) -> List[str]:
        profile = get_or_compute_profile(user_context)
        if not profile.get("available"):
            return []
        present = ["12-palace anchor map", "Major-star anchors", "Transformations"]
        if profile.get("current_cycle"):
            present.append("Current decade anchor")
        if profile.get("current_year_overlay"):
            present.append("Current year overlay")
        return present

    def missing_sources(self, user_context: Dict[str, Any]) -> List[str]:
        profile = get_or_compute_profile(user_context)
        if not profile.get("available"):
            return ["birth date missing — cannot build profile"]
        missing: List[str] = []
        if profile.get("confidence") == "low":
            missing.append("exact birth time (profile downgraded to date-only)")
        return missing

    def format_grounding_block(self, index: Dict[str, Dict[str, Any]]) -> str:
        # Inject the FULL behavioural profile so the LLM can ground responses.
        if not index:
            return ""
        lines = [
            "--- ZI WEI STRUCTURAL PROFILE (grounded behavioural source) ---",
            "Treat the following as the user's structural posture.  TRANSLATE",
            "any palace / star / transformation reference into behavioural",
            "language for the user.  Never quote palace/star names as the",
            "answer.  Always say what the user TENDS to do under conditions.",
            "",
        ]
        for k, v in index.items():
            if v.get("display_lines"):
                lines.append(f"  - {k}: {v['display_lines'][0]}")
        lines.append("")
        lines.append(
            "RULE: Forbidden tokens in your reply: 'destiny', 'fated', "
            "'guarantees', 'you are meant to', 'your true role'.  Use "
            "probabilistic markers throughout."
        )
        return "\n".join(lines)


ZI_WEI_REGISTRY = _ZiWeiRegistry()
