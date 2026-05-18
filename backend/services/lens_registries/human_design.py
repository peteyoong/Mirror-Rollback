"""
Human Design lens registry — entities: Type, Strategy, Authority, Profile,
Centers, Channels, Gates (1-64), Incarnation Cross.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from services.lens_conversation import build_alias_regex, extract_via_aliases


# --- Aliases ---------------------------------------------------------------

_TOP_LEVEL_ALIASES: Dict[str, str] = {
    "type": "Type",
    "energy type": "Type",
    "strategy": "Strategy",
    "authority": "Authority",
    "inner authority": "Authority",
    "profile": "Profile",
    "definition": "Definition",
    "incarnation cross": "Incarnation Cross",
    "cross": "Incarnation Cross",
    "not-self": "Not-Self",
    "not self": "Not-Self",
    "signature": "Signature",
}

_CENTERS: List[str] = [
    "Head", "Ajna", "Throat", "G", "Heart", "Ego", "Spleen", "Sacral",
    "Solar Plexus", "Root",
]
_CENTER_ALIASES: Dict[str, str] = {}
for c in _CENTERS:
    _CENTER_ALIASES[c.lower()] = f"Center: {c}"
    _CENTER_ALIASES[f"{c.lower()} center"] = f"Center: {c}"
_CENTER_ALIASES["g-center"] = "Center: G"
_CENTER_ALIASES["g center"] = "Center: G"
_CENTER_ALIASES["will"] = "Center: Heart"  # Heart/Ego/Will all map to Heart
_CENTER_ALIASES["ego center"] = "Center: Heart"

# Gate regex: "Gate 35", "gate 35", "35th gate". 1..64.
_GATE_RE = re.compile(r"\b(?:gate\s*([1-9]|[1-5][0-9]|6[0-4])|([1-9]|[1-5][0-9]|6[0-4])(?:st|nd|rd|th)?\s*gate)\b", re.IGNORECASE)
# Channel regex: "Channel 34-20", "channel 1-8".
_CHANNEL_RE = re.compile(r"\bchannel\s*([1-9]\d?)\s*[-–]\s*([1-9]\d?)\b", re.IGNORECASE)

_TOP_LEVEL_RE = build_alias_regex(_TOP_LEVEL_ALIASES)
_CENTER_RE = build_alias_regex(_CENTER_ALIASES)


class _HumanDesignRegistry:
    lens_name = "human_design"
    lens_label = "Human Design"

    voice_prompt = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LENS VOICE — HUMAN DESIGN  (interpretive stance: energetic mechanic)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You read the design as a circuit diagram for how this body takes in life
and makes decisions.  You are mechanical, not mystical.

Reasoning style:
  - Energy first.  Where does energy come from, where does it leak, where
    does it amplify, where is it conditioned by other people?
  - Decision-mechanism focused.  Bring every answer back to Strategy +
    Authority — these are not vibes, they are how this body operates.
  - Behavioural, not poetic.  "When you respond from Sacral, the gut
    answers in sound first, language second."  Concrete.
  - Centers as architecture.  Defined centers are reliable; undefined
    centers amplify and distort what they take in from others.
  - Profile + Definition shape HOW the energy moves; gates and channels
    are the specific switches.
  - Not-Self themes (Frustration / Anger / Disappointment / Bitterness)
    are diagnostic, not insults.

Sentence rhythm:
  Direct, declarative, slightly clinical.  Short sentences are fine.
  ("Your Authority is Sacral. That's where the yes/no actually lives.
   The mind is not the decider.")

FORBIDDEN PHRASINGS (lens-specific):
  - Mystical / cosmic framing ("the universe designed you to...")
  - Astrology vocabulary ("your Mars in your Aquarius..." — wrong lens)
  - Vague spiritual language ("trust the flow / lean in")
  - Therapy reframes ("how does that feel for you?")
  - Treating Type/Authority as identity ("you ARE a Generator")
    — say "your body is wired as a Generator" or "you operate as".

Response-architecture weighting:
  Lean heaviest into  B) SIGNAL (Type/Strategy/Authority/Profile/the
                     specific Center/Gate/Channel)
                  and D) BEHAVIOUR (how this energy actually moves
                     through the day — work, decisions, talking, body
                     state).
  E) SHADOW is the not-self theme + conditioning pattern of the
     relevant undefined center.
  F) CONNECTION is allowed to bring in ONE related circuit signal
     (e.g. "this gate is part of the channel of …, which is also defined
     for you") — only when it sharpens the answer.
"""

    def build_index(self, user_context: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        chart = user_context.get("chart") or {}
        hd = chart.get("human_design") or {}
        if not hd:
            return {}

        idx: Dict[str, Dict[str, Any]] = {}

        def add(name: str, kind: str, value: Any, display_lines: List[str] = None):
            if value in (None, "", "Unknown"):
                return
            idx[name] = {
                "kind": kind,
                "name": name,
                "value": value,
                "display_lines": display_lines or [f"{name}: {value}"],
            }

        add("Type", "hd_top", hd.get("type"))
        add("Strategy", "hd_top", hd.get("strategy"))
        add("Authority", "hd_top", hd.get("authority"))
        add("Profile", "hd_top", hd.get("profile"))
        add("Definition", "hd_top", hd.get("definition"))
        ic = hd.get("incarnation_cross")
        if ic:
            extras = []
            icg = hd.get("incarnation_cross_gates")
            if icg:
                extras.append(f"Gates: {icg}")
            idx["Incarnation Cross"] = {
                "kind": "incarnation_cross",
                "name": "Incarnation Cross",
                "value": ic,
                "display_lines": [f"Incarnation Cross: {ic}"] + extras,
            }

        # Centers
        defined_centers = hd.get("defined_centers") or []
        for c in _CENTERS:
            entry = {
                "kind": "center",
                "name": f"Center: {c}",
                "value": ("defined" if c in defined_centers else "undefined"),
                "display_lines": [f"{c} Center: {'defined' if c in defined_centers else 'undefined'}"],
            }
            idx[f"Center: {c}"] = entry

        # Channels
        for ch in (hd.get("defined_channels") or [])[:10]:
            if isinstance(ch, dict):
                g1, g2 = ch.get("gate1"), ch.get("gate2")
            else:
                # parse "34-20"
                m = re.match(r"\s*(\d+)\s*[-]\s*(\d+)\s*", str(ch))
                g1, g2 = (m.group(1), m.group(2)) if m else (None, None)
            if g1 and g2:
                key = f"Channel {g1}-{g2}"
                idx[key] = {
                    "kind": "channel",
                    "name": key,
                    "value": f"{g1}-{g2}",
                    "display_lines": [f"Defined channel: {g1}-{g2}"],
                }
                # Also expose each gate as an entity
                for g in (g1, g2):
                    gname = f"Gate {g}"
                    if gname not in idx:
                        idx[gname] = {
                            "kind": "gate",
                            "name": gname,
                            "value": f"Gate {g}",
                            "display_lines": [f"Defined gate {g} (part of channel {g1}-{g2})"],
                        }

        return idx

    def extract_entities_from_text(self, text: str) -> List[str]:
        if not text:
            return []
        found: List[Tuple[int, str]] = []
        for m in _TOP_LEVEL_RE.finditer(text):
            found.append((m.start(), _TOP_LEVEL_ALIASES[m.group(1).lower()]))
        for m in _CENTER_RE.finditer(text):
            found.append((m.start(), _CENTER_ALIASES[m.group(1).lower()]))
        for m in _GATE_RE.finditer(text):
            g = m.group(1) or m.group(2)
            if g:
                found.append((m.start(), f"Gate {g}"))
        for m in _CHANNEL_RE.finditer(text):
            g1, g2 = m.group(1), m.group(2)
            found.append((m.start(), f"Channel {g1}-{g2}"))
        found.sort(key=lambda x: x[0])
        seen, result = set(), []
        for _, key in found:
            if key not in seen:
                seen.add(key)
                result.append(key)
        return result

    def referent_patterns(self) -> List[str]:
        return [
            r"\bwhich gate\b", r"\bwhat gate\b",
            r"\bwhich channel\b", r"\bwhat channel\b",
            r"\bwhich center\b", r"\bwhat center\b", r"\bthe center\b",
            r"\bwhich type\b", r"\bmy type\b",
            r"\bwhich authority\b", r"\bmy authority\b",
        ]

    def grounding_sources_present(self, user_context: Dict[str, Any]) -> List[str]:
        chart = user_context.get("chart") or {}
        hd = chart.get("human_design") or {}
        present: List[str] = []
        if hd.get("type"): present.append("Type")
        if hd.get("strategy"): present.append("Strategy")
        if hd.get("authority"): present.append("Authority")
        if hd.get("profile"): present.append("Profile")
        if hd.get("definition"): present.append("Definition")
        if hd.get("incarnation_cross"): present.append("Incarnation Cross")
        if hd.get("defined_centers"): present.append("Defined Centers")
        if hd.get("defined_channels"): present.append("Defined Channels")
        return present

    def missing_sources(self, user_context: Dict[str, Any]) -> List[str]:
        chart = user_context.get("chart") or {}
        hd = chart.get("human_design") or {}
        missing: List[str] = []
        if not hd: return ["Human Design chart not computed"]
        if not hd.get("defined_channels"): missing.append("Defined channels (Gates)")
        if not hd.get("incarnation_cross"): missing.append("Incarnation Cross")
        if not hd.get("variables"): missing.append("Variables")
        return missing

    def format_grounding_block(self, index: Dict[str, Dict[str, Any]]) -> str:
        if not index:
            return ""
        lines = ["--- HUMAN DESIGN SIGNALS (grounded source of truth) ---"]
        ordering = ["Type", "Strategy", "Authority", "Profile", "Definition", "Incarnation Cross"]
        for k in ordering:
            e = index.get(k)
            if e:
                lines.append(f"  - {k}: {e.get('value')}")
        defined_centers = [k for k, e in index.items() if e.get("kind") == "center" and e.get("value") == "defined"]
        undefined_centers = [k for k, e in index.items() if e.get("kind") == "center" and e.get("value") == "undefined"]
        if defined_centers:
            lines.append("  - Defined centers: " + ", ".join(c.replace("Center: ", "") for c in defined_centers))
        if undefined_centers:
            lines.append("  - Undefined centers: " + ", ".join(c.replace("Center: ", "") for c in undefined_centers))
        channels = [k for k, e in index.items() if e.get("kind") == "channel"]
        if channels:
            lines.append("  - Defined channels: " + ", ".join(c.replace("Channel ", "") for c in channels))
        lines.append("RULE: Reference only HD signals listed above.  If a signal is not listed, say it's not computed.")
        return "\n".join(lines)


HUMAN_DESIGN_REGISTRY = _HumanDesignRegistry()
