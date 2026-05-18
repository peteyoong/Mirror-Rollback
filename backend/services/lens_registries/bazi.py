"""
BaZi lens registry — entities: Day Master, Four Pillars (Year/Month/Day/Hour),
Heavenly Stems, Earthly Branches, Ten Gods, Elements, Animals, Luck Pillars.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from services.lens_conversation import build_alias_regex


_TOP_ALIASES: Dict[str, str] = {
    "day master": "Day Master",
    "day stem": "Day Stem",
    "year pillar": "Year Pillar",
    "month pillar": "Month Pillar",
    "day pillar": "Day Pillar",
    "hour pillar": "Hour Pillar",
    "four pillars": "Four Pillars",
    "luck pillar": "Luck Pillars",
    "luck pillars": "Luck Pillars",
    "ten god": "Ten Gods",
    "ten gods": "Ten Gods",
    "useful god": "Useful God",
    "favorable element": "Favorable Elements",
    "favorable elements": "Favorable Elements",
    "unfavorable element": "Unfavorable Elements",
    "unfavorable elements": "Unfavorable Elements",
    "draining element": "Unfavorable Elements",
    "draining elements": "Unfavorable Elements",
}
_ELEMENTS = ["Wood", "Fire", "Earth", "Metal", "Water"]
_ELEMENT_ALIASES = {e.lower(): f"Element: {e}" for e in _ELEMENTS}

_ANIMALS = ["Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
            "Horse", "Goat", "Sheep", "Monkey", "Rooster", "Dog", "Pig", "Boar"]
_ANIMAL_ALIASES = {a.lower(): f"Animal: {a}" for a in _ANIMALS}

_TEN_GOD_NAMES = [
    "Direct Officer", "Seven Killings", "Direct Resource", "Indirect Resource",
    "Direct Wealth", "Indirect Wealth", "Eating God", "Hurting Officer",
    "Friend", "Rob Wealth",
]
_TEN_GOD_ALIASES = {g.lower(): f"Ten God: {g}" for g in _TEN_GOD_NAMES}

_TOP_RE = build_alias_regex(_TOP_ALIASES)
_ELEMENT_RE = build_alias_regex(_ELEMENT_ALIASES)
_ANIMAL_RE = build_alias_regex(_ANIMAL_ALIASES)
_TEN_GOD_RE = build_alias_regex(_TEN_GOD_ALIASES)


class _BaZiRegistry:
    lens_name = "bazi"
    lens_label = "BaZi"

    def build_index(self, user_context: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        bz = user_context.get("bazi_chart") or {}
        if not bz: return {}
        idx: Dict[str, Dict[str, Any]] = {}

        dm = bz.get("day_master") or {}
        if dm.get("element"):
            idx["Day Master"] = {
                "kind": "day_master",
                "name": "Day Master",
                "value": f"{dm.get('polarity', '')} {dm.get('element', '')}".strip(),
                "display_lines": [
                    f"Day Master: {dm.get('polarity', '')} {dm.get('element', '')}",
                    f"Strength: {dm.get('strength', 'Unknown')}",
                ],
            }
            elem_key = f"Element: {dm.get('element')}"
            idx[elem_key] = {
                "kind": "element",
                "name": elem_key,
                "value": dm.get("element"),
                "display_lines": [f"Day Master element: {dm.get('element')}"],
            }

        pillars = bz.get("pillars") or {}
        for p_name in ("year", "month", "day", "hour"):
            p = pillars.get(p_name) or {}
            if p:
                key = f"{p_name.capitalize()} Pillar"
                stem = p.get("stem_pinyin") or p.get("stem") or "?"
                branch = p.get("branch_pinyin") or p.get("branch") or "?"
                idx[key] = {
                    "kind": "pillar",
                    "name": key,
                    "value": f"{stem} {branch}",
                    "display_lines": [f"{key}: {stem} {branch}"],
                }
                anim = p.get("animal")
                if anim:
                    a_key = f"Animal: {anim}"
                    idx.setdefault(a_key, {
                        "kind": "animal",
                        "name": a_key,
                        "value": anim,
                        "display_lines": [f"{p_name.capitalize()} animal: {anim}"],
                    })

        dd = bz.get("deep_dive") or {}
        tg_list = dd.get("ten_gods_detailed") or []
        if tg_list:
            top = [g.get("label") or g.get("name") for g in tg_list if g.get("strength") in ("high", "moderate")][:5]
            if top:
                idx["Ten Gods"] = {
                    "kind": "ten_god",
                    "name": "Ten Gods",
                    "value": ", ".join(top),
                    "display_lines": ["Dominant Ten Gods: " + ", ".join(top)],
                }
        fav = dd.get("favorable_elements") or []
        if fav:
            idx["Favorable Elements"] = {
                "kind": "element",
                "name": "Favorable Elements",
                "value": ", ".join(fav),
                "display_lines": ["Favorable elements: " + ", ".join(fav)],
            }
        unfav = dd.get("unfavorable_elements") or []
        if unfav:
            idx["Unfavorable Elements"] = {
                "kind": "element",
                "name": "Unfavorable Elements",
                "value": ", ".join(unfav),
                "display_lines": ["Draining elements: " + ", ".join(unfav)],
            }

        luck = (bz.get("luck_pillars") or {}).get("pillars") or []
        if luck:
            idx["Luck Pillars"] = {
                "kind": "luck_pillar",
                "name": "Luck Pillars",
                "value": f"{len(luck)} pillars computed",
                "display_lines": [f"Luck pillars computed: {len(luck)}"],
            }
        return idx

    def extract_entities_from_text(self, text: str) -> List[str]:
        if not text: return []
        found: List[Tuple[int, str]] = []
        for m in _TOP_RE.finditer(text):
            found.append((m.start(), _TOP_ALIASES[m.group(1).lower()]))
        for m in _ELEMENT_RE.finditer(text):
            found.append((m.start(), _ELEMENT_ALIASES[m.group(1).lower()]))
        for m in _ANIMAL_RE.finditer(text):
            found.append((m.start(), _ANIMAL_ALIASES[m.group(1).lower()]))
        for m in _TEN_GOD_RE.finditer(text):
            found.append((m.start(), _TEN_GOD_ALIASES[m.group(1).lower()]))
        found.sort(key=lambda x: x[0])
        seen, result = set(), []
        for _, k in found:
            if k not in seen:
                seen.add(k); result.append(k)
        return result

    def referent_patterns(self) -> List[str]:
        return [
            r"\bwhich pillar\b", r"\bwhat pillar\b", r"\bthe pillar\b",
            r"\bwhich god\b", r"\bwhich ten god\b",
            r"\bwhich element\b", r"\bwhat element\b",
            r"\bwhich animal\b", r"\bmy day master\b",
        ]

    def grounding_sources_present(self, user_context: Dict[str, Any]) -> List[str]:
        bz = user_context.get("bazi_chart") or {}
        if not bz: return []
        present: List[str] = []
        if (bz.get("day_master") or {}).get("element"): present.append("Day Master")
        if bz.get("pillars"): present.append("Four Pillars")
        dd = bz.get("deep_dive") or {}
        if dd.get("ten_gods_detailed"): present.append("Ten Gods")
        if dd.get("favorable_elements"): present.append("Favorable / Unfavorable Elements")
        if (bz.get("luck_pillars") or {}).get("pillars"): present.append("Luck Pillars")
        timing = bz.get("timing")
        if timing: present.append("Current timing layer")
        return present

    def missing_sources(self, user_context: Dict[str, Any]) -> List[str]:
        bz = user_context.get("bazi_chart") or {}
        if not bz: return ["BaZi chart not computed (requires birth date)"]
        missing: List[str] = []
        dd = bz.get("deep_dive") or {}
        if not dd.get("ten_gods_detailed"): missing.append("Ten Gods detail")
        if not dd.get("favorable_elements"): missing.append("Favorable/Unfavorable elements")
        if not (bz.get("luck_pillars") or {}).get("pillars"): missing.append("Luck Pillars")
        if not bz.get("pillars", {}).get("hour"): missing.append("Hour Pillar (requires exact birth time)")
        return missing

    def format_grounding_block(self, index: Dict[str, Dict[str, Any]]) -> str:
        if not index: return ""
        lines = ["--- BAZI SIGNALS (grounded source of truth) ---"]
        for k in ["Day Master", "Year Pillar", "Month Pillar", "Day Pillar", "Hour Pillar",
                  "Ten Gods", "Favorable Elements", "Unfavorable Elements", "Luck Pillars"]:
            e = index.get(k)
            if e:
                lines.append(f"  - {k}: {e.get('value')}")
        lines.append("RULE: Reference only signals listed above.  If a signal isn't listed, say it's not computed.  Do NOT fake BaZi data.")
        return "\n".join(lines)


BAZI_REGISTRY = _BaZiRegistry()
