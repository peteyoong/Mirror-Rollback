"""hd_relationship_narrative.py — narrative blocks for HD drill-down
=====================================================================
Build marker: hd-relationship-narrative-v1

Reads the deterministic `field_v3` + `diagnostics` payload produced by
`relationship_hd_field_engine.compute_hd_relationship_field` and turns
it into a structured set of narrative BLOCKS designed for the
relationship-page "What Drives This → Human Design" drill-down.

Blocks produced:

    1.  type_pair_engagement   — how the two TYPES meet
    2.  authority_rhythm       — how decisions land between you
    3.  profile_interaction    — how the profiles cross
    4.  definition_dynamics    — how the definitions weave / split
    5.  centers_conditioning   — defined ↔ open conditioning summary
    6.  electromagnetic_gifts  — channels you complete in each other
    7.  compromise_dominance   — half-channels & whose energy fills the field
    8.  practical_guidance     — how to engage *this* specific person

Strict rules:
  • Everything deterministic. No LLM calls.
  • Reads `field_v3` strings as authoritative; only adds STRUCTURE.
  • Inlines names where the engine emitted name_a / name_b placeholders.
  • Safe to call when field_v3 is None — returns None.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

NARRATIVE_VERSION = "hd-relationship-narrative-v1"

# Profile interaction matrix — Pythagorean line crossings.
PROFILE_INTERACTION_MAP: Dict[str, Dict[str, str]] = {
    # Each entry keyed by sorted profile pair "a/b|c/d"
    "default": {
        "summary": "Your profile lines cross in ways that ask each of you to be exactly who you are — neither one has to bend to fit the other.",
        "watch": "When one of you starts running on borrowed strategy, the field flattens.",
    },
}


def _profile_block(prof_a: str, prof_b: str, name_a: str, name_b: str) -> Dict[str, str]:
    if not prof_a or not prof_b:
        return {
            "summary": "Profile data is incomplete for one or both charts — this block reads more clearly once both profiles are confirmed.",
            "watch": "Until then, lean on the type and authority blocks above.",
        }
    # Extract lines (e.g. "5/1" -> "5","1")
    def _lines(p):
        try:
            parts = [int(x) for x in p.split("/")[:2]]
            return parts
        except Exception:
            return []
    la = _lines(prof_a); lb = _lines(prof_b)
    if not la or not lb:
        return PROFILE_INTERACTION_MAP["default"]
    set_lines = set(la) | set(lb)
    # Heuristic narrative based on line presence
    summary_parts: List[str] = [f"{name_a} runs a {prof_a} profile; {name_b} runs {prof_b}."]
    if 1 in set_lines and 4 in set_lines:
        summary_parts.append("One of you investigates, the other influences — research deepens what gets shared in the network.")
    if 2 in set_lines and 5 in set_lines:
        summary_parts.append("One of you needs hermit time to recharge; the other carries projections from the outside world. Protecting both is the work.")
    if 3 in set_lines and 6 in set_lines:
        summary_parts.append("Experimentation meets role-model — trial-and-error finds its way into something the other can stand behind.")
    if not summary_parts[1:]:
        summary_parts.append("Different lines, different ways of meeting the world — your shared map gets richer when each is respected.")
    watch_parts: List[str] = []
    if 1 in set_lines:
        watch_parts.append("The 1-line needs solid ground; if it doesn't get to investigate, anxiety leaks into the connection.")
    if 2 in set_lines:
        watch_parts.append("The 2-line needs unscheduled time; pulling them out of the hermitage too often drains the field.")
    if 5 in set_lines:
        watch_parts.append("The 5-line carries projections both ways — what gets imagined onto them isn't always real.")
    if 6 in set_lines:
        watch_parts.append("The 6-line moves through life phases; if you're together long-term, expect that the role-model line will shift visibly between roof-on and roof-off phases.")
    if not watch_parts:
        watch_parts.append("Let each profile do its own work; the synthesis emerges over time, not on demand.")
    return {
        "summary": " ".join(summary_parts),
        "watch":   " ".join(watch_parts[:2]),
    }


def _definition_block(def_a: str, def_b: str, name_a: str, name_b: str) -> Dict[str, str]:
    if not def_a or not def_b:
        return {
            "summary": "Definition data is incomplete — this block reads more clearly once both definitions are confirmed.",
            "watch": "",
        }
    def_a_l = def_a.lower(); def_b_l = def_b.lower()
    summary: str
    watch: str
    if def_a_l.startswith("single") and def_b_l.startswith("single"):
        summary = (f"Both {name_a} and {name_b} run on Single Definition — each of you carries a self-contained inner logic. "
                   "When you connect, two whole systems meet rather than completing each other.")
        watch = "Don't expect the other to fill a missing piece — that's not the dynamic. Connection here is about resonance, not completion."
    elif def_a_l.startswith("split") and def_b_l.startswith("split"):
        summary = (f"Both of you carry Split Definition — each of you already feels the bridge between two parts of yourselves. "
                   "Together you can either deepen the gap or build the bridge faster.")
        watch = "If you each rely on the other to bridge what's actually internal, the relationship becomes the patch over your own seams."
    elif def_a_l.startswith("single") and def_b_l.startswith("split"):
        summary = f"{name_a}'s Single Definition completes what {name_b} carries across a Split — your presence makes their internal bridge easier to feel."
        watch = f"{name_b} may unconsciously seek out {name_a} for completion; if that becomes a need, the relationship carries weight that should sit internally."
    elif def_a_l.startswith("split") and def_b_l.startswith("single"):
        summary = f"{name_b}'s Single Definition completes what {name_a} carries across a Split — their presence makes your internal bridge easier to feel."
        watch = f"{name_a} may unconsciously seek out {name_b} for completion; if that becomes a need, the relationship carries weight that should sit internally."
    elif "no definition" in def_a_l or "no definition" in def_b_l or "reflector" in def_a_l or "reflector" in def_b_l:
        summary = ("One of you carries No Definition — you sample the room, and the room samples you back. "
                   "Together your field has both a centre and a mirror.")
        watch = "The mirror needs time and space to settle; rushing them for clarity collapses the read."
    elif def_a_l.startswith("triple") or def_b_l.startswith("triple"):
        summary = ("One of you carries Triple Split — three separate bodies of definition. "
                   "Together you bridge them one by one; this connection is patient by nature.")
        watch = "Forcing decisions before all three areas have weighed in produces decisions that don't hold."
    else:
        summary = f"Definitions: {def_a} × {def_b} — two distinct internal architectures meeting."
        watch = "Each definition has its own way of arriving at certainty; the work is letting both arrive in their own time."
    return {"summary": summary, "watch": watch}


def _centers_block(diagnostics: Dict[str, Any],
                   field_v3: Dict[str, Any],
                   name_a: str, name_b: str) -> Dict[str, Any]:
    cc = (diagnostics or {}).get("center_conditioning") or {}
    a_amplifies = cc.get("a_amplifies_b_via") or []
    b_amplifies = cc.get("b_amplifies_a_via") or []
    both_def    = cc.get("both_defined") or []
    both_open   = cc.get("both_open") or []
    lines: List[str] = []
    if a_amplifies:
        lines.append(
            f"{name_a}'s defined {', '.join(a_amplifies)} amplifies {name_b}'s open {('one' if len(a_amplifies)==1 else 'these')} "
            f"— what passes between you in {('this area' if len(a_amplifies)==1 else 'these areas')} is mostly {name_a}'s frequency."
        )
    if b_amplifies:
        lines.append(
            f"{name_b}'s defined {', '.join(b_amplifies)} amplifies {name_a}'s open "
            f"— in {('that area' if len(b_amplifies)==1 else 'those areas')} you tend to take on {name_b}'s tone."
        )
    if both_def:
        lines.append(
            f"Both of you are defined in {', '.join(both_def)} — these areas run in parallel; neither of you conditions the other here."
        )
    if both_open:
        lines.append(
            f"Both of you are open in {', '.join(both_open)} — these areas are most influenced by whoever else is in the room."
        )
    # Pull `centre_conditioning` lines from field_v3 verbatim as supporting evidence
    cond_lines = (field_v3 or {}).get("centre_conditioning") or []
    return {
        "summary": " ".join(lines) if lines else "Center conditioning data is incomplete for this pairing.",
        "details": cond_lines[:3],
        "watch":   "Open centers are amplifiers, not lacks; what comes through them is data, not identity.",
    }


def _channels_block(field_v3: Dict[str, Any],
                    diagnostics: Dict[str, Any],
                    name_a: str, name_b: str) -> Dict[str, Any]:
    em_count   = diagnostics.get("electromagnetic_count", 0)
    comp_count = diagnostics.get("compromise_count", 0)
    dom_a      = diagnostics.get("dominance_a_count", 0)
    dom_b      = diagnostics.get("dominance_b_count", 0)
    comp_pairs = diagnostics.get("companion_count", 0)
    em_narr   = field_v3.get("electromagnetic_gifts") or ""
    comp_narr = field_v3.get("compromise_dynamics") or ""
    dom_narr  = field_v3.get("dominance_dynamics") or ""
    return {
        "electromagnetic": {
            "count": em_count,
            "summary": em_narr,
            "headline": (f"{em_count} electromagnetic completion{'s' if em_count != 1 else ''} "
                         f"between {name_a} and {name_b}" if em_count else "No electromagnetic completions"),
        },
        "compromise": {
            "count": comp_count,
            "summary": comp_narr,
        },
        "dominance": {
            "a_count": dom_a,
            "b_count": dom_b,
            "summary": dom_narr,
        },
        "companion": {
            "count": comp_pairs,
            "summary": (
                f"{comp_pairs} companion channel{'s' if comp_pairs != 1 else ''} — same gate active on both sides. "
                f"This is shared reinforcement, not new completion."
                if comp_pairs else
                "No companion channels — neither of you has the same gate as the other."
            ),
        },
    }


def _practical_guidance(field_v3: Dict[str, Any], name_b: str) -> Dict[str, Any]:
    """Return a digestible 'how to engage them' block from repair/growth/friction."""
    repair = field_v3.get("repair_pathway") or []
    growth = field_v3.get("growth_edge") or ""
    friction = field_v3.get("friction_patterns") or []
    return {
        "summary": f"How to engage {name_b} on purpose — drawn from your shared mechanics, not personality guesses.",
        "repair_first": repair[:3] if isinstance(repair, list) else [repair][:3],
        "growth_edge": growth if isinstance(growth, str) else "",
        "friction_to_watch": friction[:3] if isinstance(friction, list) else [],
    }


def compute_hd_narrative_blocks(
    field_v3: Optional[Dict[str, Any]],
    diagnostics: Optional[Dict[str, Any]],
    name_a: str = "You",
    name_b: str = "them",
) -> Optional[Dict[str, Any]]:
    """Build the HD-drill-down narrative blocks. Returns None when the
    underlying engine returned nothing.

    SAFE: never raises on partial data; emits skeleton blocks with empty
    strings instead.
    """
    if not field_v3 or not diagnostics:
        return None

    prof_pair = diagnostics.get("profile_pair", "")
    type_pair = diagnostics.get("type_pair", "")
    def_pair  = diagnostics.get("definition_pair", "")
    auth_pair = diagnostics.get("authority_pair", "")

    def _split_pair(s: str):
        """Split 'A × B' or 'A x B' (case-insensitive) -> ('A','B')."""
        if not isinstance(s, str) or not s.strip():
            return ("", "")
        for sep in (" × ", " x ", " X ", " ✕ "):
            if sep in s:
                parts = s.split(sep)
                if len(parts) >= 2:
                    return (parts[0].strip(), parts[1].strip())
        return ("", "")

    prof_a, prof_b = _split_pair(prof_pair)
    def_a,  def_b  = _split_pair(def_pair)

    blocks = {
        "version": NARRATIVE_VERSION,
        "type_pair_engagement": {
            "summary": field_v3.get("aura_dynamics", "") or field_v3.get("energy_signature", ""),
            "field_overview": field_v3.get("field_overview", ""),
            "headline": type_pair,
        },
        "authority_rhythm": {
            "summary": field_v3.get("decision_dynamics", ""),
            "headline": auth_pair,
        },
        "profile_interaction": {
            **_profile_block(prof_a, prof_b, name_a, name_b),
            "headline": prof_pair,
        },
        "definition_dynamics": {
            **_definition_block(def_a, def_b, name_a, name_b),
            "headline": def_pair,
        },
        "centers_conditioning": _centers_block(diagnostics, field_v3, name_a, name_b),
        "channels": _channels_block(field_v3, diagnostics, name_a, name_b),
        "practical_guidance": _practical_guidance(field_v3, name_b),
        "energy_weather": field_v3.get("energy_weather", ""),
    }
    return blocks


__all__ = ["compute_hd_narrative_blocks", "NARRATIVE_VERSION"]
