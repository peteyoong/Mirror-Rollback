"""
Enneagram lens registry — entities: Core type, Wing, Tritype, Instinctual
stack, Centers (Heart/Head/Body), Lines (stress/security), Fixation,
Passion, Virtue.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from services.lens_conversation import build_alias_regex


_ALIASES: Dict[str, str] = {
    "core type": "Core Type",
    "main type": "Core Type",
    "my type": "Core Type",
    "the type": "Core Type",
    "enneagram type": "Core Type",
    "ennea type": "Core Type",
    "type number": "Core Type",
    "personality type": "Core Type",
    "wing": "Wing",
    "tritype": "Tritype",
    "instinct": "Instinctual Stack",
    "instincts": "Instinctual Stack",
    "instinctual stack": "Instinctual Stack",
    "subtype": "Subtype",
    "fixation": "Fixation",
    "passion": "Passion",
    "virtue": "Virtue",
    "stress line": "Stress Line",
    "stress point": "Stress Line",
    "security line": "Security Line",
    "security point": "Security Line",
    "integration": "Security Line",
    "disintegration": "Stress Line",
    "heart center": "Heart Center",
    "head center": "Head Center",
    "body center": "Body Center",
    "gut center": "Body Center",
}
_ALIAS_RE = build_alias_regex(_ALIASES)
# "Type 7", "Type 7w8", "7w8".
_TYPE_RE = re.compile(r"\btype\s*([1-9])(?:w([1-9]))?\b|\b([1-9])w([1-9])\b", re.IGNORECASE)

_TYPE_NAMES = {
    1: "Reformer", 2: "Helper", 3: "Achiever", 4: "Individualist",
    5: "Investigator", 6: "Loyalist", 7: "Enthusiast", 8: "Challenger", 9: "Peacemaker",
}


class _EnneagramRegistry:
    lens_name = "enneagram"
    lens_label = "Enneagram"

    voice_prompt = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LENS VOICE — ENNEAGRAM  (interpretive stance: motivational psychologist)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You read type as motivational structure — the engine underneath the
behaviour.  You are psychologically sharp, not diagnostic; you describe
ego-structure, not pathology.

Reasoning style:
  - Motivation first.  Every type has a core fear and a core desire;
    every behaviour traces back to those two.  Lead with what the type
    is trying to PROTECT and what it is reaching FOR.
  - Defense-pattern aware.  Name the type's main defense (perfectionism,
    helping, performance, intensity, withdrawal, doubt, escape,
    domination, sleep) without making it shameful.
  - Pressure / security movement.  When the user is stressed, they move
    toward their Stress Line; when they are safe, toward their Security
    Line.  This is the most useful diagnostic tool you have.
  - Wing colours the type; Instinct directs WHERE the type plays out
    (self-pres / social / sexual).  Use them sparingly but accurately.
  - Center (Body / Heart / Head) names HOW the type takes in the world —
    instinctually, emotionally, or mentally.

Sentence rhythm:
  Sharp, observant, slightly clinical.  Speak about the type in the
  second person but never collapse the person into the type
  ("your Type 7 instinct does X" — not "you ARE a 7").

FORBIDDEN PHRASINGS (lens-specific):
  - Over-pathologising ("you have an unhealthy 7 disorder")
  - Treating type as a personality verdict
  - Spiritual/mystical framing ("the 9 holds the universe's peace")
  - Therapy-couch language ("how does that sit in your body?")
  - Type-stereotype shortcuts ("8s are bullies", "9s are lazy")

Response-architecture weighting:
  Lean heaviest into  B) SIGNAL (Core Type X — fear / desire / fixation
                     / passion) and E) SHADOW (the defense pattern, the
                     stress-line drift).
  D) BEHAVIOUR is how the type tends to act under the current question.
  F) CONNECTION can briefly name the wing or instinct if it sharpens
     the answer — keep it tight.
"""

    def build_index(self, user_context: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        enn = user_context.get("enneagram_results") or {}
        if not enn:
            return {}
        idx: Dict[str, Dict[str, Any]] = {}

        core = enn.get("core_type")
        try:
            core_int = int(core) if core is not None else None
        except (ValueError, TypeError):
            core_int = None

        if core_int:
            tname = _TYPE_NAMES.get(core_int, "Unknown")
            idx["Core Type"] = {
                "kind": "core_type",
                "name": "Core Type",
                "value": f"{core_int} ({tname})",
                "display_lines": [f"Core Type: {core_int} — {tname}"],
            }
            wing = enn.get("wing")
            if wing:
                idx["Wing"] = {
                    "kind": "wing",
                    "name": "Wing",
                    "value": wing,
                    "display_lines": [f"Wing: {wing}"],
                }
            computed = enn.get("enneagram_computed_details") or {}
            stack = computed.get("instinctual_stack") or computed.get("dominant_instinct")
            if stack:
                idx["Instinctual Stack"] = {
                    "kind": "instinct",
                    "name": "Instinctual Stack",
                    "value": stack,
                    "display_lines": [f"Instinctual Stack: {stack}"],
                }
            tritype = computed.get("tritype")
            if tritype:
                idx["Tritype"] = {
                    "kind": "tritype",
                    "name": "Tritype",
                    "value": tritype,
                    "display_lines": [f"Tritype: {tritype}"],
                }
            # Lines (computed deterministically from type)
            lines_map = {1: (7, 4), 2: (4, 8), 3: (6, 9), 4: (1, 2), 5: (8, 7),
                         6: (3, 9), 7: (5, 1), 8: (2, 5), 9: (3, 6)}
            if core_int in lines_map:
                stress, security = lines_map[core_int]
                idx["Stress Line"] = {
                    "kind": "line",
                    "name": "Stress Line",
                    "value": f"Type {stress}",
                    "display_lines": [f"Stress (disintegration) line: → Type {stress}"],
                }
                idx["Security Line"] = {
                    "kind": "line",
                    "name": "Security Line",
                    "value": f"Type {security}",
                    "display_lines": [f"Security (integration) line: → Type {security}"],
                }
            # Center mapping
            center = {
                1: "Body Center", 8: "Body Center", 9: "Body Center",
                2: "Heart Center", 3: "Heart Center", 4: "Heart Center",
                5: "Head Center", 6: "Head Center", 7: "Head Center",
            }.get(core_int)
            if center:
                idx[center] = {
                    "kind": "center",
                    "name": center,
                    "value": center,
                    "display_lines": [f"Primary center: {center}"],
                }
        return idx

    def extract_entities_from_text(self, text: str) -> List[str]:
        if not text: return []
        found: List[Tuple[int, str]] = []
        for m in _ALIAS_RE.finditer(text):
            found.append((m.start(), _ALIASES[m.group(1).lower()]))
        # "7w8" style
        for m in _TYPE_RE.finditer(text):
            # Mark as Core Type subject when user says "type 7" / "7w8"
            found.append((m.start(), "Core Type"))
        found.sort(key=lambda x: x[0])
        seen, result = set(), []
        for _, k in found:
            if k not in seen:
                seen.add(k); result.append(k)
        return result

    def referent_patterns(self) -> List[str]:
        return [
            r"\bwhich type\b", r"\bwhat type\b",
            r"\bwhich wing\b", r"\bwhat wing\b",
            r"\bthat line\b", r"\bwhich line\b",
        ]

    def grounding_sources_present(self, user_context: Dict[str, Any]) -> List[str]:
        enn = user_context.get("enneagram_results") or {}
        present: List[str] = []
        if enn.get("core_type"): present.append("Core Type")
        if enn.get("wing"): present.append("Wing")
        computed = enn.get("enneagram_computed_details") or {}
        if computed.get("instinctual_stack") or computed.get("dominant_instinct"):
            present.append("Instinctual Stack")
        if computed.get("tritype"): present.append("Tritype")
        if enn.get("core_type"): present.append("Stress / Security lines (deterministic)")
        return present

    def missing_sources(self, user_context: Dict[str, Any]) -> List[str]:
        enn = user_context.get("enneagram_results") or {}
        if not enn: return ["Enneagram assessment not completed"]
        missing: List[str] = []
        computed = enn.get("enneagram_computed_details") or {}
        if not computed.get("instinctual_stack") and not computed.get("dominant_instinct"):
            missing.append("Instinctual Stack")
        if not computed.get("tritype"): missing.append("Tritype")
        return missing

    def format_grounding_block(self, index: Dict[str, Dict[str, Any]]) -> str:
        if not index: return ""
        lines = ["--- ENNEAGRAM SIGNALS (grounded source of truth) ---"]
        for k in ["Core Type", "Wing", "Instinctual Stack", "Tritype", "Stress Line", "Security Line"]:
            e = index.get(k)
            if e:
                lines.append(f"  - {k}: {e.get('value')}")
        center = next((k for k, e in index.items() if e.get("kind") == "center"), None)
        if center:
            lines.append(f"  - Primary center: {center}")
        lines.append("RULE: Reference only signals listed above.  If a signal isn't listed, say it's not computed.")
        return "\n".join(lines)


ENNEAGRAM_REGISTRY = _EnneagramRegistry()
