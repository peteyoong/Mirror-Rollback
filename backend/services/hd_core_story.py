"""hd_core_story.py — Evidence-ranked hierarchical HD Core Story
========================================================================

Session-3c Decision 5: replace the single-dominant-theme HD Core Story
("acting before emotional clarity", etc.) with a hierarchical story
built from evidence-ranked threads.

Ranking philosophy
------------------
The Core Story is not a fixed script. Each user's HD payload surfaces
different threads; the story is the ordered SUBSET of threads that
resolve to actual evidence on their chart. Threads are scored by:

    (a) evidence strength   — does the chart show explicit structural
                              support for this thread?
    (b) domain weight       — Type & Authority carry more structural
                              weight than a single line-tone;
    (c) integration reach   — does the thread anchor into multiple
                              other structures?

Weights are conservative and fixed in this module (no runtime tuning),
so the same chart always renders the same ranked story. This mirrors
the ranking-required regime required by Session-3c Decision 5.

Output
------
{
    "primary":     NarrativeThread,      # top-1
    "secondary":   list[NarrativeThread],# ranks 2..N (max 4)
    "hierarchy":   [thread_id, ...],     # explicit order
    "score_table": [{thread_id, score, weight, evidence_count}],
    "content_provenance": "session3c_verified",
    "algorithm":   "hd_core_story_ranked_v1"
}

Each NarrativeThread carries:
    thread_id, headline, text, evidence[]

build_marker: the-mirror-hd-core-story-v1
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

CONTENT_PROVENANCE_ID = "session3c_verified"
ALGORITHM_ID = "hd_core_story_ranked_v1"


def _thread(thread_id: str, headline: str, text: str, evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "thread_id": thread_id,
        "headline": headline,
        "text": text,
        "evidence": evidence,
        "content_provenance": CONTENT_PROVENANCE_ID,
    }


def build_core_story(
    *,
    hd_type: Optional[str],
    strategy: Optional[str],
    authority: Optional[str],
    profile: Optional[str],
    topology: Dict[str, Any],
    channels: List[Dict[str, Any]],
    defined_centers: List[str],
    undefined_centers: List[str],
    p_sun_gate: Optional[int],
    d_sun_gate: Optional[int],
    signature: Optional[str],
    not_self: Optional[str],
) -> Dict[str, Any]:
    """Build the evidence-ranked hierarchical Core Story."""

    threads: List[Dict[str, Any]] = []
    score_table: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Thread A — TYPE + STRATEGY  (weight 100)
    # ------------------------------------------------------------------
    if hd_type:
        threads.append(_thread(
            thread_id="type_and_strategy",
            headline=f"{hd_type}" + (f" — {strategy}" if strategy else ""),
            text=(
                f"Your operating mechanism is {hd_type}. The strategy for a "
                f"{hd_type} — {strategy or 'the standard strategy for this Type'} "
                f"— is not advice, it is how this configuration is designed to "
                f"engage the world. The signature that appears when this is "
                f"honoured is {signature or '—'}; the not-self theme that "
                f"appears when it is not is {not_self or '—'}."
            ),
            evidence=[
                {"field": "type", "value": hd_type,
                 "source": "chart.human_design.type",
                 "derivation_rule": "hd_type_from_definition_v1"},
                {"field": "strategy", "value": strategy,
                 "source": "hd_strategy_map_by_type",
                 "derivation_rule": "hd_strategy_from_type_v1"},
            ],
        ))
        score_table.append({"thread_id": "type_and_strategy", "score": 100,
                             "weight": 100, "evidence_count": 2})

    # ------------------------------------------------------------------
    # Thread B — AUTHORITY  (weight 90)
    # ------------------------------------------------------------------
    if authority and authority != "None":
        threads.append(_thread(
            thread_id="authority",
            headline=f"Authority — {authority}",
            text=(
                f"Your inner authority is {authority}. This is the mechanism "
                f"through which your body confirms a decision; the mind is "
                f"designed to observe, not to decide. Reading through this "
                f"authority — rather than the mind — is what returns you to "
                f"correct timing."
            ),
            evidence=[
                {"field": "authority", "value": authority,
                 "source": "chart.human_design.authority",
                 "derivation_rule": "hd_authority_from_defined_centers_v1"},
            ],
        ))
        score_table.append({"thread_id": "authority", "score": 90,
                             "weight": 90, "evidence_count": 1})

    # ------------------------------------------------------------------
    # Thread C — DEFINITION TOPOLOGY  (weight 80)
    # ------------------------------------------------------------------
    derived_def = topology.get("derived_type") if topology else None
    if derived_def:
        n_comp = topology.get("components_count", 0)
        text = (
            f"Definition topology: {derived_def} "
            f"({n_comp} connected component{'s' if n_comp != 1 else ''} on "
            f"the defined-centre graph). This shapes how you integrate "
            f"information internally and how much your environment fills "
            f"in the bridges."
        )
        # Split-subtype detail is intentionally not surfaced in the
        # consumer-facing text; it remains available on the topology
        # payload for methodology inspection.
        threads.append(_thread(
            thread_id="definition_topology",
            headline=derived_def,
            text=text,
            evidence=[
                {"field": "definition", "value": derived_def,
                 "source": "hd_definition_topology",
                 "derivation_rule": topology.get("derivation_rule")},
            ],
        ))
        score_table.append({"thread_id": "definition_topology", "score": 80,
                             "weight": 80, "evidence_count": 1})

    # ------------------------------------------------------------------
    # Thread D — CHANNELS  (weight 60 + reach bonus per channel)
    # ------------------------------------------------------------------
    if channels:
        channel_names = [
            f"{ch.get('gates', '')} · {ch.get('name', '')}".strip(" ·")
            for ch in channels
        ]
        reach_bonus = min(len(channels) * 5, 20)
        threads.append(_thread(
            thread_id="channels",
            headline=f"{len(channels)} defined channel"
            + ("s" if len(channels) != 1 else ""),
            text=(
                "Your defined channels are the fixed circuitry — the parts "
                "of the design that speak the same way every day: "
                + ", ".join(channel_names)
                + ". These are the sentences of your design; centres are "
                "the paragraphs."
            ),
            evidence=[
                {"field": "defined_channels",
                 "value": ch.get("gates") or ch.get("name"),
                 "source": f"chart.human_design.defined_channels[{ch.get('gates', '?')}]",
                 "derivation_rule": "hd_channel_intersection_v1"}
                for ch in channels
            ],
        ))
        score_table.append({"thread_id": "channels", "score": 60 + reach_bonus,
                             "weight": 60, "evidence_count": len(channels)})

    # ------------------------------------------------------------------
    # Thread E — PROFILE  (weight 55)
    # ------------------------------------------------------------------
    if profile and profile != "Unknown":
        threads.append(_thread(
            thread_id="profile",
            headline=f"Profile {profile}",
            text=(
                f"Your profile is {profile}. Profile is the costume the design "
                f"wears — how the mechanism gets seen and how it learns."
            ),
            evidence=[
                {"field": "profile", "value": profile,
                 "source": "chart.human_design.profile",
                 "derivation_rule": "hd_profile_from_sun_lines_v1"},
            ],
        ))
        score_table.append({"thread_id": "profile", "score": 55,
                             "weight": 55, "evidence_count": 1})

    # ------------------------------------------------------------------
    # Thread F — SUN INCARNATION (P/D)  (weight 50)
    # ------------------------------------------------------------------
    if p_sun_gate or d_sun_gate:
        text = (
            "Conscious Sun (Personality) sits at Gate "
            f"{p_sun_gate if p_sun_gate else '—'}; Unconscious Sun (Design) "
            f"sits at Gate {d_sun_gate if d_sun_gate else '—'}. These are the "
            "two distinct purposes of the design — the conscious voice and "
            "the biological / unconscious one — and they are meant to be "
            "carried together, not merged."
        )
        threads.append(_thread(
            thread_id="sun_incarnation",
            headline=(
                f"P.Sun {p_sun_gate or '—'} · D.Sun {d_sun_gate or '—'}"
            ),
            text=text,
            evidence=[
                {"field": "personality.Sun.gate", "value": p_sun_gate,
                 "source": "chart.human_design.personality.Sun.gate",
                 "derivation_rule": "hd_gate_line_from_longitude_v1"},
                {"field": "design.Sun.gate", "value": d_sun_gate,
                 "source": "chart.human_design.design.Sun.gate",
                 "derivation_rule": "hd_gate_line_from_longitude_v1"},
            ],
        ))
        score_table.append({"thread_id": "sun_incarnation", "score": 50,
                             "weight": 50, "evidence_count": 2})

    # ------------------------------------------------------------------
    # Thread G — UNDEFINED CENTRE OPENNESS  (weight 40)
    # ------------------------------------------------------------------
    if undefined_centers:
        threads.append(_thread(
            thread_id="undefined_openness",
            headline=f"Openness: {len(undefined_centers)} undefined centre"
            + ("s" if len(undefined_centers) != 1 else ""),
            text=(
                "Your undefined centres — " + ", ".join(undefined_centers) +
                " — amplify what's around you. This is where you're most "
                "receptive to other people's signals and most likely to "
                "confuse borrowed pressure for your own."
            ),
            evidence=[
                {"field": "undefined_centers", "value": c,
                 "source": "chart.human_design.centers",
                 "derivation_rule": "hd_center_split_v1"}
                for c in undefined_centers
            ],
        ))
        score_table.append({"thread_id": "undefined_openness",
                             "score": 40,
                             "weight": 40,
                             "evidence_count": len(undefined_centers)})

    # ------------------------------------------------------------------
    # Sort by score desc, then thread order for tiebreak
    # ------------------------------------------------------------------
    order_ids = [t["thread_id"] for t in threads]
    score_by_id = {s["thread_id"]: s["score"] for s in score_table}
    threads.sort(
        key=lambda t: (-score_by_id.get(t["thread_id"], 0),
                       order_ids.index(t["thread_id"]))
    )
    hierarchy = [t["thread_id"] for t in threads]

    primary = threads[0] if threads else None
    secondary = threads[1:5] if len(threads) > 1 else []

    return {
        "primary": primary,
        "secondary": secondary,
        "hierarchy": hierarchy,
        "score_table": sorted(
            score_table, key=lambda s: -s["score"]
        ),
        "content_provenance": CONTENT_PROVENANCE_ID,
        "algorithm": ALGORITHM_ID,
    }


__all__ = ["build_core_story", "CONTENT_PROVENANCE_ID", "ALGORITHM_ID"]
