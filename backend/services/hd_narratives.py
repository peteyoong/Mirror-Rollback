"""hd_narratives.py — Evidence-grounded Human Design narrative registry
========================================================================

Session-3c Phase 4: replace generic HD boilerplate with narratives that
reference the ACTUAL data on the user's chart. Every rendered claim
carries an EvidenceRef so the "How was this derived?" accordion can
show its lineage.

Design invariants (enforced by tests):
--------------------------------------
1. NO cross-lens references. Only HD-domain terms.
2. NO invented / unverifiable claims (e.g. "your PHS wants mountains").
3. Every narrative resolves to at least one EvidenceRef pointing to a
   verifiable field on `hd_data` or `hd_raw`.
4. Centre narratives read differently for defined-vs-undefined and
   reference the specific channels/gates that DEFINE the centre.
5. Channel narratives are per-channel, keyed by canonical `gates` id
   (e.g. "4-63") — no generic template.
6. Gate/line narratives for the four Sun/Earth activations are line-
   sensitive (line 1..6 changes tone).
7. Profile narratives are line-pair specific (5/1 ≠ 5/2).
8. Definition narrative uses the DERIVED topology (from
   hd_definition_topology), not the raw string.
9. Signature/Not-Self already ships from hd_signature_notself.py.

Every function returns a `NarrativeBlock`:
    {
      "text":     str,
      "sub_text": Optional[str],
      "evidence": list[EvidenceRef],
      "content_provenance": "session3c_verified",
    }

build_marker: the-mirror-hd-narratives-v1
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

CONTENT_PROVENANCE_ID = "session3c_verified"


# ---------------------------------------------------------------------------
# 1. CENTRE NARRATIVES — content differentiated by defined-vs-undefined
#    plus the channels flowing through them.
# ---------------------------------------------------------------------------
_CENTER_ROLE = {
    "Head":         ("pressure",   "the seat of inspirational pressure — questions and doubts arriving from outside"),
    "Ajna":         ("awareness",  "the awareness centre that organises concepts and gives shape to what's been questioned"),
    "Throat":       ("expression", "the manifestation centre where inner information becomes speech or action"),
    "G/Identity":   ("identity",   "the seat of direction, love and identity"),
    "Heart/Ego":    ("motor",      "the willpower motor — commitments, promises, self-worth"),
    "Solar Plexus": ("motor",      "the emotional wave motor — feelings that build and release over time"),
    "Sacral":       ("motor",      "the life-force motor — sustainable work, response, sexuality"),
    "Spleen":       ("awareness",  "the intuitive awareness centre — survival, health, in-the-moment knowing"),
    "Root":         ("pressure",   "the adrenal pressure centre — stress, drive, timing"),
}


def _center_definition_via(
    centre: str,
    channels: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Return the subset of the user's defined channels that touch this centre."""
    out: List[Dict[str, Any]] = []
    for ch in channels or []:
        ctrs = ch.get("centers") or ch.get("centres") or []
        if centre in ctrs:
            out.append(ch)
    return out


def center_narrative(
    centre: str,
    is_defined: bool,
    channels: List[Dict[str, Any]],
    hd_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Return an evidence-grounded narrative block for a specific centre."""
    role, role_desc = _CENTER_ROLE.get(centre, ("centre", "one of the nine energy centres"))

    if is_defined:
        via = _center_definition_via(centre, channels)
        via_names = [
            f"{ch.get('gates', '')} · {ch.get('name', '')}".strip(" ·")
            for ch in via
            if ch.get("gates") or ch.get("name")
        ]
        if via_names:
            via_line = " · ".join(via_names)
            text = (
                f"Your {centre} is defined through {via_line}. "
                f"As a defined {role}, this centre carries a consistent "
                f"signal — {role_desc}. It is a fixed way you meet the "
                f"world, not something you're negotiating internally."
            )
        else:
            # Rare: centre is defined but no channel evidence — still call it out.
            text = (
                f"Your {centre} is defined. As a defined {role}, this centre "
                f"carries a consistent signal — {role_desc}. It is a fixed "
                f"way you meet the world."
            )
        sub_text = None
        evidence = [
            {
                "field": "defined_centers",
                "value": centre,
                "source": "chart.human_design.defined_channels",
                "derivation_rule": "hd_center_definition_from_channels_v1",
            }
        ] + [
            {
                "field": "defined_channels",
                "value": ch.get("gates") or ch.get("name"),
                "source": f"chart.human_design.defined_channels[{ch.get('gates', '?')}]",
                "derivation_rule": "hd_channel_intersection_v1",
            }
            for ch in via
        ]
    else:
        text = (
            f"Your {centre} is undefined. As an undefined {role}, this centre "
            f"amplifies whatever is around it — {role_desc}. Not a defect: an "
            f"openness that reads the room. The work is noticing when the "
            f"amplified signal is yours and when it belongs to someone else."
        )
        sub_text = None
        evidence = [
            {
                "field": "undefined_centers",
                "value": centre,
                "source": "chart.human_design.centers",
                "derivation_rule": "hd_center_split_v1",
            }
        ]

    return {
        "centre": centre,
        "is_defined": bool(is_defined),
        "role": role,
        "text": text,
        "sub_text": sub_text,
        "evidence": evidence,
        "content_provenance": CONTENT_PROVENANCE_ID,
    }


# ---------------------------------------------------------------------------
# 2. CHANNEL NARRATIVES — per-channel, evidence-grounded.
#    Keyed by canonical `a-b` id. Contains a compact non-boilerplate
#    interpretation citing the two gates + circuit. Additional channels
#    fall back to a structured template that still cites the actual
#    channel name, circuit, and centre endpoints (never generic text).
# ---------------------------------------------------------------------------
_CHANNEL_SPECIFIC: Dict[str, Dict[str, str]] = {
    "4-63": {
        "headline": "Logic — Doubt that resolves into answers",
        "text": (
            "You carry a mental format that starts with doubt (Gate 63) and "
            "keeps turning it until it arrives at an answer that holds "
            "(Gate 4). This is not indecision; it is how logic works in you. "
            "The pressure to be certain is native — but certainty here is "
            "earned by cycling through the doubt, not by shortcutting it."
        ),
    },
    "35-36": {
        "headline": "Transitoriness — Wanting new experience for the sake of experience",
        "text": (
            "This channel wires progress (Gate 35) to emotional appetite for "
            "change (Gate 36). You are designed to keep moving through "
            "experiences — you get bored when the current one has been "
            "metabolised. The failure mode is calling every ending a mistake; "
            "the design mode is calling it what it is: the experience is done."
        ),
    },
    "37-40": {
        "headline": "Community — Bargains, loyalty, and the terms of belonging",
        "text": (
            "Community is the tribal contract: you offer effort and provision "
            "(Gate 40 · the deliverer) in exchange for the emotional bond of "
            "an agreed community (Gate 37 · the family/friendship). When the "
            "bargain is honoured this channel is deeply nourishing. When it "
            "is broken — implicitly or explicitly — this is where you feel "
            "the rupture most sharply."
        ),
    },
    # Extend here as more real Session-3c narratives are authored.
}


def channel_narrative(channel: Dict[str, Any]) -> Dict[str, Any]:
    """Return an evidence-grounded narrative for one channel."""
    gates_id = channel.get("gates") or ""
    name = channel.get("name") or ""
    circuit = channel.get("circuit") or ""
    theme = channel.get("theme") or ""
    centres = channel.get("centers") or channel.get("centres") or []

    specific = _CHANNEL_SPECIFIC.get(gates_id)
    if specific:
        headline = specific["headline"]
        text = specific["text"]
        variant = "authored"
    else:
        # Compositional strategy — safe, channel-specific content derived
        # from the channel's own theme/circuit/endpoints. No generic
        # boilerplate reaches the user; the copy always references THIS
        # channel's material.
        friendly_theme = theme or "its circuitry theme"
        endpoints = " ↔ ".join(centres) if centres else "two centres"
        circuit_ref = f" in the {circuit} circuit" if circuit else ""
        headline = f"{gates_id} · {name}" if name else gates_id
        text = (
            f"The {name or gates_id} channel connects {endpoints}"
            f"{circuit_ref}. It carries {friendly_theme}. Because both "
            f"gates are activated on your chart, this circuit is a fixed "
            f"part of how you meet the world — not something you're "
            f"negotiating internally."
        )
        variant = "composed_from_structure"

    evidence = [
        {
            "field": "defined_channels",
            "value": gates_id,
            "source": f"chart.human_design.defined_channels[{gates_id}]",
            "derivation_rule": "hd_channel_intersection_v1",
        }
    ]
    return {
        "channel_id": gates_id,
        "name": name,
        "circuit": circuit,
        "centres": list(centres),
        "headline": headline,
        "text": text,
        "variant": variant,
        "evidence": evidence,
        "content_provenance": CONTENT_PROVENANCE_ID,
    }


# ---------------------------------------------------------------------------
# 3. GATE / LINE narratives for the four Sun/Earth activations.
#    Line-sensitive: line changes the tone even for the same gate.
# ---------------------------------------------------------------------------
_LINE_TONE = {
    1: "the foundation line — grounded in study, roots, the base of the pattern",
    2: "the natural line — hermit-genius, brilliant when left alone",
    3: "the experiential line — learns by doing and by what breaks",
    4: "the network line — expresses through relationship and friendship",
    5: "the projected line — attracts expectations, called to lead in crisis",
    6: "the role-model line — three lives: experimenter, retreat, wise witness",
}

_GATE_ONE_LINE: Dict[int, str] = {
    # Compact HD-domain gate summaries. Extend as narratives are verified.
    4: "the answer / the working hypothesis",
    5: "fixed patterns / rhythm",
    6: "conflict / intimacy",
    13: "the listener / the witness",
    21: "control / territory",
    22: "grace / emotional openness",
    25: "the spirit of universal love",
    28: "the game player / struggle",
    29: "commitment / saying yes",
    31: "influence / leadership",
    32: "endurance / recognising what lasts",
    35: "progress / experience",
    36: "the crisis of experience",
    37: "friendship / family agreements",
    40: "aloneness / deliverance",
    41: "imagination / new experience",
    47: "realisation / making sense",
    49: "principles / revolution",
    55: "abundance / mood",
    61: "inner truth / mystery",
    62: "the detail / precision of language",
    63: "doubt / logical questioning",
}


def activation_narrative(
    side: str,               # "personality" | "design"
    planet: str,             # "Sun" | "Earth" | ...
    gate: Optional[int],
    line: Optional[int],
) -> Optional[Dict[str, Any]]:
    """Return a narrative block for one activation. None when insufficient data."""
    if not gate or not line:
        return None
    gate_theme = _GATE_ONE_LINE.get(int(gate), "a specific archetype")
    line_tone = _LINE_TONE.get(int(line), "a specific line-tone")

    side_lens = {
        "personality": ("Personality", "conscious", "how you experience it internally"),
        "design": ("Design", "unconscious", "how it operates without you noticing"),
    }.get(side, (side.title(), side, "one axis of the design"))

    text = (
        f"{side_lens[0]} {planet} — Gate {gate}, Line {line}. "
        f"Gate {gate} carries {gate_theme}; Line {line} is {line_tone}. "
        f"On the {side_lens[1]} side, this is {side_lens[2]}."
    )
    evidence = [
        {
            "field": f"{side}.{planet}.gate",
            "value": f"{gate}.{line}",
            "source": f"chart.human_design.{side}.{planet}.gate",
            "derivation_rule": "hd_gate_line_from_longitude_v1",
        }
    ]
    return {
        "side": side,
        "planet": planet,
        "gate": gate,
        "line": line,
        "gate_theme": gate_theme,
        "line_tone": line_tone,
        "text": text,
        "evidence": evidence,
        "content_provenance": CONTENT_PROVENANCE_ID,
    }


# ---------------------------------------------------------------------------
# 4. PROFILE NARRATIVE — line-pair specific.
# ---------------------------------------------------------------------------
_PROFILE_MAP: Dict[str, Dict[str, str]] = {
    # All 12 canonical profile pairs receive line-pair-specific handling.
    "1/3": {
        "headline": "1/3 — The Investigator Martyr",
        "text": (
            "Line 1 seeks the foundational study; Line 3 learns by making "
            "the mistake and iterating. Together this profile is designed "
            "to hit the wall, find the actual mechanism, and rebuild on it."
        ),
    },
    "1/4": {
        "headline": "1/4 — The Investigator Opportunist",
        "text": (
            "Line 1 needs the depth of study; Line 4 lives through the "
            "network. This profile builds a foundation privately and "
            "expresses it through the friendships that come to it."
        ),
    },
    "2/4": {
        "headline": "2/4 — The Hermit Opportunist",
        "text": (
            "Line 2 is the natural genius that needs solitude; Line 4 is "
            "the network that finds and calls it out. The design is not "
            "'go seek it' — it is 'stay in your work and let the network "
            "recognise you'."
        ),
    },
    "2/5": {
        "headline": "2/5 — The Hermit Heretic",
        "text": (
            "Line 2 is the alone genius; Line 5 attracts projection from "
            "the outside world. This profile is protective of solitude "
            "while carrying an outward-facing role that people impose "
            "before it feels ready."
        ),
    },
    "3/5": {
        "headline": "3/5 — The Martyr Heretic",
        "text": (
            "Line 3 learns experientially — trial, error, iteration. "
            "Line 5 draws people who project solutions onto it. This "
            "profile carries the burden of being seen as the fixer while "
            "still learning by what breaks."
        ),
    },
    "3/6": {
        "headline": "3/6 — The Martyr Role Model",
        "text": (
            "Line 3 iterates through breakage; Line 6 walks a three-life "
            "arc — young experimenter, contemplative roof, wise witness. "
            "The learning of Line 3 becomes the wisdom of Line 6 in the "
            "third stage."
        ),
    },
    "4/6": {
        "headline": "4/6 — The Opportunist Role Model",
        "text": (
            "Line 4 lives through the network; Line 6 walks the three-life "
            "arc. This profile is deeply loyal to relationships and, in "
            "its later stage, becomes the model others quietly study."
        ),
    },
    "4/1": {
        "headline": "4/1 — The Opportunist Investigator (Fixed Fate)",
        "text": (
            "The 4/1 juxtaposition profile has fixed fate — the theme is "
            "not transformational but structural. Line 4 lives through "
            "network; Line 1 needs foundation. This design carries the "
            "same theme through the whole life."
        ),
    },
    "5/1": {
        "headline": "5/1 — The Heretic Investigator",
        "text": (
            "Line 5 is the projected line — people look at you and see "
            "someone who can solve their problem, whether or not you have "
            "the solution ready. Line 1 is the foundation line — you need "
            "depth, study, and time with the material. The 5/1 lives with "
            "constant projection from Line 5 and secures itself against it "
            "by doing the Line-1 work: knowing the material at the root."
        ),
    },
    "5/2": {
        "headline": "5/2 — The Heretic Hermit",
        "text": (
            "Line 5 attracts projection outward; Line 2 protects the "
            "hermit-genius inward. Alone you're brilliant; the challenge "
            "is the pull of Line 5 dragging the Line-2 hermit into public "
            "view before it's ready."
        ),
    },
    "6/2": {
        "headline": "6/2 — The Role Model Hermit",
        "text": (
            "Line 6 runs a three-life arc — experimenter, roof, wise "
            "witness. Line 2 needs solitude to hear what it actually "
            "knows. The two combine into a profile that is naturally "
            "aloof and deeply modelled by others in its later stage."
        ),
    },
    "6/3": {
        "headline": "6/3 — The Role Model Martyr",
        "text": (
            "Line 6's three-life arc combined with Line 3's experiential "
            "iteration. This profile learns very publicly in the early "
            "years, retreats to integrate, and returns as the calibrated "
            "witness."
        ),
    },
}


def profile_narrative(profile_str: Optional[str]) -> Dict[str, Any]:
    key = (profile_str or "").strip()
    entry = _PROFILE_MAP.get(key)
    if entry:
        return {
            "profile": key,
            "headline": entry["headline"],
            "text": entry["text"],
            "variant": "authored",
            "evidence": [
                {
                    "field": "profile",
                    "value": key,
                    "source": "chart.human_design.profile",
                    "derivation_rule": "hd_profile_from_sun_lines_v1",
                }
            ],
            "content_provenance": CONTENT_PROVENANCE_ID,
        }
    # Compositional fallback that still uses the ACTUAL two lines rather
    # than a generic template.  Every profile pair therefore gets
    # line-tone-specific content — no user sees a bare "no interpretation
    # available" string.
    parts = key.split("/") if "/" in key else []
    if len(parts) == 2 and all(p.strip().isdigit() for p in parts):
        a, b = int(parts[0]), int(parts[1])
        a_tone = _LINE_TONE.get(a, "a specific line-tone")
        b_tone = _LINE_TONE.get(b, "a specific line-tone")
        return {
            "profile": key,
            "headline": f"Profile {key}",
            "text": (
                f"Personality Line {a} is {a_tone}. Design Line {b} is "
                f"{b_tone}. Together they form the {key} profile — the "
                f"conscious costume ({a}) worn over the unconscious "
                f"ground ({b})."
            ),
            "variant": "composed_from_lines",
            "evidence": [
                {
                    "field": "profile",
                    "value": key,
                    "source": "chart.human_design.profile",
                    "derivation_rule": "hd_profile_from_sun_lines_v1",
                }
            ],
            "content_provenance": CONTENT_PROVENANCE_ID,
        }
    return {
        "profile": key or None,
        "headline": "Profile — unavailable",
        "text": "Profile lines are not present on this chart.",
        "variant": "unavailable",
        "evidence": [
            {
                "field": "profile",
                "value": key,
                "source": "chart.human_design.profile",
                "derivation_rule": "hd_profile_from_sun_lines_v1",
            }
        ],
        "content_provenance": CONTENT_PROVENANCE_ID,
    }


# ---------------------------------------------------------------------------
# 5. DEFINITION NARRATIVE — uses the DERIVED topology, not the raw label.
# ---------------------------------------------------------------------------
def definition_narrative(topology: Dict[str, Any]) -> Dict[str, Any]:
    derived = topology.get("derived_type") or "Unknown"
    n = topology.get("components_count", 0)
    components = topology.get("components") or []
    is_unverified = topology.get("split_subtype_unverified", False)

    body_map = {
        "Single Definition": (
            "All defined centres form one connected network. Your inner "
            "signal is self-contained: given time, you can access all your "
            "own information without needing another person to bridge it."
        ),
        "Split Definition": (
            "Your defined centres form two separate networks. Bridging "
            "between them happens through relationship, environment, or "
            "the transits — not internally on demand. That is not a defect; "
            "it is how information flows in a Split configuration."
        ),
        "Triple Split Definition": (
            "Your defined centres form three separate networks. Integration "
            "happens across multiple bridges, and your natural pace of "
            "synthesis is slower than a Single Definition."
        ),
        "Quadruple Split Definition": (
            "Your defined centres form four separate networks. This is the "
            "most environmentally-sensitive configuration; the bridges you "
            "meet in relationship or transit have a strong effect on which "
            "pieces you can access at once."
        ),
        "No Definition": (
            "No centres are consistently defined. Your channel of information "
            "is the environment — you sample, absorb, and reflect. This is "
            "the Reflector configuration."
        ),
        "Unknown": (
            "The definition topology could not be verified from the chart. "
            "The upstream label is retained for reference but not interpreted."
        ),
    }
    text = body_map.get(derived, body_map["Unknown"])
    # No consumer-visible diagnostic string for split subtype.  The
    # frontend surfaces this through a discreet "How this was derived"
    # section instead.

    return {
        "definition_type": derived,
        "components_count": n,
        "components": components,
        "headline": derived,
        "text": text,
        "split_subtype_unverified": is_unverified,
        "split_subtype_reason": topology.get("split_subtype_reason"),
        "evidence": [
            {
                "field": "definition",
                "value": derived,
                "source": "hd_definition_topology",
                "derivation_rule": topology.get("derivation_rule"),
            }
        ],
        "content_provenance": CONTENT_PROVENANCE_ID,
    }


# ---------------------------------------------------------------------------
# 6. INCARNATION CROSS NARRATIVE — as an integrated four-activation config.
# ---------------------------------------------------------------------------
def incarnation_cross_narrative(
    cross_label: Optional[str],
    cross_gates: Optional[str],   # "37/40 | 5/35" backend format
    p_sun_gate: Optional[int],
    p_earth_gate: Optional[int],
    d_sun_gate: Optional[int],
    d_earth_gate: Optional[int],
) -> Dict[str, Any]:
    """The Incarnation Cross is not four separate stories — it is one
    configured pattern of four activations (P.Sun / P.Earth / D.Sun /
    D.Earth). Render it as such, always with the four gates cited."""

    quartet = None
    if all(g for g in (p_sun_gate, p_earth_gate, d_sun_gate, d_earth_gate)):
        quartet = f"{p_sun_gate}/{p_earth_gate} | {d_sun_gate}/{d_earth_gate}"
    tag = quartet or cross_gates or "unavailable"

    gate_themes = {
        g: _GATE_ONE_LINE.get(int(g), "a specific archetype")
        for g in (p_sun_gate, p_earth_gate, d_sun_gate, d_earth_gate)
        if isinstance(g, int)
    }

    theme_lines = []
    if p_sun_gate:
        theme_lines.append(
            f"P.Sun {p_sun_gate}: {gate_themes.get(p_sun_gate, '—')} (conscious purpose)"
        )
    if p_earth_gate:
        theme_lines.append(
            f"P.Earth {p_earth_gate}: {gate_themes.get(p_earth_gate, '—')} (conscious ground)"
        )
    if d_sun_gate:
        theme_lines.append(
            f"D.Sun {d_sun_gate}: {gate_themes.get(d_sun_gate, '—')} (unconscious purpose)"
        )
    if d_earth_gate:
        theme_lines.append(
            f"D.Earth {d_earth_gate}: {gate_themes.get(d_earth_gate, '—')} (unconscious ground)"
        )

    text = (
        f"{cross_label or 'Incarnation Cross'} — gates {tag}. This is a "
        f"single configured pattern, not four separate roles. The four "
        f"activations combine into one integrated theme; reading them "
        f"individually loses the configuration."
    )

    evidence = []
    for planet, gate in (
        ("Sun", p_sun_gate),
        ("Earth", p_earth_gate),
    ):
        if gate:
            evidence.append(
                {
                    "field": f"personality.{planet}.gate",
                    "value": gate,
                    "source": f"chart.human_design.personality.{planet}.gate",
                    "derivation_rule": "hd_gate_line_from_longitude_v1",
                }
            )
    for planet, gate in (
        ("Sun", d_sun_gate),
        ("Earth", d_earth_gate),
    ):
        if gate:
            evidence.append(
                {
                    "field": f"design.{planet}.gate",
                    "value": gate,
                    "source": f"chart.human_design.design.{planet}.gate",
                    "derivation_rule": "hd_gate_line_from_longitude_v1",
                }
            )

    return {
        "label": cross_label,
        "cross_gates": tag,
        "quartet": quartet,
        "activation_themes": theme_lines,
        "text": text,
        "evidence": evidence,
        "content_provenance": CONTENT_PROVENANCE_ID,
    }


__all__ = [
    "center_narrative",
    "channel_narrative",
    "activation_narrative",
    "profile_narrative",
    "definition_narrative",
    "incarnation_cross_narrative",
    "CONTENT_PROVENANCE_ID",
]
