"""
Numerology lens registry — entities: Life Path, Expression/Destiny,
Soul Urge, Personality, Birthday, Maturity, Personal Year/Month/Day, Master
numbers (11/22/33).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from services.lens_conversation import build_alias_regex


_ALIASES: Dict[str, str] = {
    "life path": "Life Path",
    "life path number": "Life Path",
    "expression": "Expression",
    "expression number": "Expression",
    "destiny": "Expression",
    "destiny number": "Expression",
    "soul urge": "Soul Urge",
    "soul urge number": "Soul Urge",
    "heart's desire": "Soul Urge",
    "hearts desire": "Soul Urge",
    "personality": "Personality",
    "personality number": "Personality",
    "birthday": "Birthday",
    "birthday number": "Birthday",
    "maturity": "Maturity",
    "maturity number": "Maturity",
    "personal year": "Personal Year",
    "personal month": "Personal Month",
    "personal day": "Personal Day",
    "master number": "Master Number",
}
_ALIAS_RE = build_alias_regex(_ALIASES)


class _NumerologyRegistry:
    lens_name = "numerology"
    lens_label = "Numerology"

    voice_prompt = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LENS VOICE — NUMEROLOGY  (interpretive stance: life-pattern decoder)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You read numbers as life themes, not predictions.  You translate a Life
Path or Personal Year into the chapter the user is actually living.

Reasoning style:
  - Theme-first.  Every number has a central theme; lead with it
    ("Life Path 7 — the seeker who needs depth to feel real").
  - Cyclical.  Numbers move in 9-year arcs, monthly waves, daily edges.
    Frame the current question inside the cycle the user is in.
  - Developmental.  Numbers are unfolding curricula — what mastery looks
    like at this number, and where the user is in the work.
  - Chapters and milestones.  "This year is your 3 year — the visibility
    year.  That changes what 'good' looks like."
  - Name the difference between the Core numbers (Life Path/Expression
    /Soul Urge/Personality) and the Cycle numbers (Personal Year/Month
    /Day) — Core is identity, Cycle is timing.

Sentence rhythm:
  Warm but firm.  Allow yourself the language of "season", "chapter",
  "this year" without becoming horoscope-ish.  Definitive about themes;
  humble about specific events.

FORBIDDEN PHRASINGS (lens-specific):
  - Fortune-teller framing ("the numbers say you will...")
  - Lucky/unlucky number talk
  - Mystical "vibration" language
  - Predictive certainty about events or outcomes
  - Treating numbers as personality verdicts

Response-architecture weighting:
  Lean heaviest into  B) SIGNAL (the specific number(s) at play for this
                     user — Life Path X, in their Personal Year Y)
                  and D) BEHAVIOUR (the kinds of decisions, relationships,
                     and work this number tends to ask for).
  E) SHADOW is the over- or under-expression of the number.
  F) CONNECTION can briefly note how the Core number interacts with the
     current Cycle number ("Life Path 7 + Personal Year 3 = depth-work
     asked to become visible").
"""

    def build_index(self, user_context: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        chart = user_context.get("chart") or {}
        num = chart.get("numerology") or {}
        cycles = user_context.get("numerology_cycles") or {}
        idx: Dict[str, Dict[str, Any]] = {}

        def _num(v):
            if isinstance(v, dict):
                return v.get("number")
            return v

        def add(name: str, kind: str, value: Any, extra_lines: List[str] = None):
            if value in (None, "", "Unknown"):
                return
            idx[name] = {
                "kind": kind,
                "name": name,
                "value": value,
                "display_lines": [f"{name}: {value}"] + (extra_lines or []),
            }

        add("Life Path", "life_path", _num(num.get("life_path")))
        add("Birthday", "numerology_number", _num(num.get("birthday")))
        if num.get("has_name_numbers"):
            add("Expression", "numerology_number", _num(num.get("expression")))
            add("Soul Urge", "numerology_number", _num(num.get("soul_urge")))
            add("Personality", "numerology_number", _num(num.get("personality")))
            add("Maturity", "numerology_number", _num(num.get("maturity")))
        if cycles:
            py = cycles.get("personal_year") or {}
            pm = cycles.get("personal_month") or {}
            pd = cycles.get("personal_day") or {}
            add("Personal Year", "personal_cycle", py.get("number"), [py.get("description", "")] if py.get("description") else None)
            add("Personal Month", "personal_cycle", pm.get("number"), [pm.get("description", "")] if pm.get("description") else None)
            add("Personal Day", "personal_cycle", pd.get("number"), [pd.get("description", "")] if pd.get("description") else None)
        return idx

    def extract_entities_from_text(self, text: str) -> List[str]:
        if not text: return []
        found: List[Tuple[int, str]] = []
        for m in _ALIAS_RE.finditer(text):
            found.append((m.start(), _ALIASES[m.group(1).lower()]))
        found.sort(key=lambda x: x[0])
        seen, result = set(), []
        for _, k in found:
            if k not in seen:
                seen.add(k); result.append(k)
        return result

    def referent_patterns(self) -> List[str]:
        return [
            r"\bwhich number\b", r"\bwhat number\b", r"\bthe number\b",
            r"\bwhich cycle\b", r"\bwhat cycle\b", r"\bthat cycle\b",
        ]

    def grounding_sources_present(self, user_context: Dict[str, Any]) -> List[str]:
        chart = user_context.get("chart") or {}
        num = chart.get("numerology") or {}
        present: List[str] = []
        if num.get("life_path"): present.append("Life Path")
        if num.get("birthday"): present.append("Birthday Number")
        if num.get("has_name_numbers"):
            present.append("Expression / Soul Urge / Personality (name-based)")
        if user_context.get("numerology_cycles"):
            present.append("Personal Year/Month/Day cycles")
        return present

    def missing_sources(self, user_context: Dict[str, Any]) -> List[str]:
        chart = user_context.get("chart") or {}
        num = chart.get("numerology") or {}
        missing: List[str] = []
        if not num: return ["Numerology not computed"]
        if not num.get("has_name_numbers"):
            missing.append("Expression / Soul Urge / Personality (requires full birth name)")
        return missing

    def format_grounding_block(self, index: Dict[str, Dict[str, Any]]) -> str:
        if not index: return ""
        lines = ["--- NUMEROLOGY SIGNALS (grounded source of truth) ---"]
        order = ["Life Path", "Expression", "Soul Urge", "Personality", "Birthday", "Maturity", "Personal Year", "Personal Month", "Personal Day"]
        for k in order:
            e = index.get(k)
            if e:
                lines.append(f"  - {k}: {e.get('value')}")
        lines.append("RULE: Reference only numbers listed above.  If a number isn't listed, say it's not computed.")
        return "\n".join(lines)


NUMEROLOGY_REGISTRY = _NumerologyRegistry()
