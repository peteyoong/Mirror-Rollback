"""
Timeline V2 — Stabilization Sprint
===================================
Build marker: timeline-v2-stabilization-sprint-v1

This is NOT a copy-quality test. It is an EXISTENTIAL TOPOLOGY test.

We construct 15 synthetic chart fixtures across 6 archetypal categories
and run them through the deterministic core of the Phase Governor
(extract_signals → build_shortlist) to verify that the engine
distinguishes HOW pressure is metabolized — not merely which traits
are present.

Categories under test:
  1. Emotional permeability  (3 users)
  2. Cognitive recursion     (3 users)
  3. Hybrid                  (3 users)  — the failure-mode-rich zone
  4. Achievement-pressure    (2 users)
  5. Stable / non-dramatic   (2 users)
  6. Avoidant / detached     (2 users)

For each user we compute:
  - signals_extracted (the engine's view of the chart)
  - shortlist (top 3, post-diversity-guard)
  - primary chapter + family
  - adjacent (positions 2, 3)
  - collapse_risk: low / medium / high
  - false_intellectualization: True if the user was routed into
        cognitive_recursion despite missing the discriminator
        (Mercury-Saturn hard).
  - false_emotionalization: True if the user was routed into
        emotional_permeability despite cognitive-recursion mechanics
        being dominant.

Run:
    cd /app/backend && python -m tests.stabilization_sprint

Output:
    /app/backend/tests/STABILIZATION_REPORT.md
    /app/backend/tests/stabilization_results.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure /app/backend is on path so services.* imports work
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services.phase_governor import extract_signals, build_shortlist
from services.chapter_library import get_chapter_by_id


# ===========================================================================
# Fixture builders — construct minimal chart dicts that fire only the
# signals we want to test. Each helper returns a chart dict with the
# shape extract_signals() expects.
# ===========================================================================
def _chart(
    *,
    defined_centers: Optional[List[str]] = None,
    active_gates: Optional[List[int]] = None,
    planets: Optional[Dict[str, Dict[str, Any]]] = None,
    aspects: Optional[List[Dict[str, Any]]] = None,
    life_path: Optional[int] = None,
) -> Dict[str, Any]:
    return {
        "human_design": {
            "defined_centers": defined_centers or [],
            "active_gates":    active_gates    or [],
        },
        "astrology": {
            "planets": planets or {},
            "aspects": aspects or [],
        },
        "numerology": {
            "core": {"life_path": {"number": life_path}} if life_path is not None else {},
        },
    }


def _aspect(a: str, b: str, t: str = "square") -> Dict[str, str]:
    return {"body1": a, "body2": b, "type": t}


def _planet(sign: str = "leo", house: int = 1) -> Dict[str, Any]:
    return {"sign": sign, "house": house}


# ===========================================================================
# Cohort — 15 users
#
# Each entry: { id, label, category, why_we_picked_this_shape, chart }
#
# A user's category is the archetype we expect the engine to land them in.
# A miss is the failure we're testing for.
# ===========================================================================
COHORT: List[Dict[str, Any]] = [
    # =======================================================================
    # 1. EMOTIONAL PERMEABILITY (3) — open emotional center, Saturn heaviness,
    #    suppression. MUST NOT collapse into cognitive_recursion.
    # =======================================================================
    {
        "id":       "E1_pure_permeability",
        "label":    "Pure permeability — open SP, Saturn-Moon, peacekeeping",
        "category": "emotional_permeability",
        "expected_family": "emotional_permeability",
        "why_picked": "Classic open SP + Saturn-Moon hard + Gate 22 — should land squarely in Cost Of Keeping The Peace.",
        "chart": _chart(
            defined_centers=["Heart", "Sacral", "Throat", "G Center"],
            active_gates=[22, 49],
            planets={
                "Sun":     _planet("pisces", 7),
                "Moon":    _planet("cancer", 4),
                "Mercury": _planet("pisces", 7),
                "Venus":   _planet("aquarius", 6),
                "Mars":    _planet("taurus", 8),
                "Saturn":  _planet("libra", 4),
            },
            aspects=[
                _aspect("Saturn", "Moon", "square"),
                _aspect("Saturn", "Venus", "opposition"),
            ],
            life_path=2,
        ),
    },
    {
        "id":       "E2_relational_duty",
        "label":    "Permeability + 7th house Saturn duty",
        "category": "emotional_permeability",
        "expected_family": "emotional_permeability",
        "why_picked": "Saturn in 7th + Saturn-Venus + Open SP — relational duty axis.",
        "chart": _chart(
            defined_centers=["Sacral", "Throat", "Ego"],
            active_gates=[49],
            planets={
                "Sun":     _planet("virgo", 6),
                "Moon":    _planet("scorpio", 8),
                "Mercury": _planet("libra", 7),
                "Venus":   _planet("libra", 7),
                "Mars":    _planet("aries", 1),
                "Saturn":  _planet("libra", 7),
            },
            aspects=[
                _aspect("Saturn", "Venus", "conjunction"),
                _aspect("Mars", "Venus", "opposition"),
            ],
            life_path=6,
        ),
    },
    {
        "id":       "E3_12th_house_moon",
        "label":    "Permeability + 12th house Moon (hidden emotional life)",
        "category": "emotional_permeability",
        "expected_family": "emotional_permeability",
        "why_picked": "Moon in 12th + Open SP + Open Throat — emotional life running underneath.",
        "chart": _chart(
            defined_centers=["Sacral", "G Center"],
            active_gates=[22],
            planets={
                "Sun":     _planet("aquarius", 1),
                "Moon":    _planet("capricorn", 12),
                "Mercury": _planet("aquarius", 1),
                "Venus":   _planet("pisces", 2),
                "Mars":    _planet("scorpio", 10),
                "Saturn":  _planet("taurus", 4),
            },
            aspects=[
                _aspect("Saturn", "Moon", "opposition"),
            ],
            life_path=3,
        ),
    },

    # =======================================================================
    # 2. COGNITIVE RECURSION (3) — defined Ajna + (G63/G4) + Mercury-Saturn.
    #    MUST land in cognitive_recursion family.
    # =======================================================================
    {
        "id":       "C1_full_certainty_loop",
        "label":    "Pure certainty loop — Ajna+G4+G63+MercSat+LP7",
        "category": "cognitive_recursion",
        "expected_family": "cognitive_recursion",
        "why_picked": "Every derived cognitive signal should fire. Expect certainty_that_never_arrives at top.",
        "chart": _chart(
            defined_centers=["Ajna", "Head", "Throat"],
            active_gates=[4, 63, 24, 47],
            planets={
                "Sun":     _planet("virgo", 9),
                "Moon":    _planet("virgo", 9),
                "Mercury": _planet("virgo", 9),
                "Venus":   _planet("libra", 10),
                "Mars":    _planet("gemini", 6),
                "Saturn":  _planet("sagittarius", 12),
                "Neptune": _planet("aquarius", 2),
            },
            aspects=[
                _aspect("Saturn", "Mercury", "square"),
                _aspect("Saturn", "Sun",     "square"),
            ],
            life_path=7,
        ),
    },
    {
        "id":       "C2_recursive_questioning",
        "label":    "Recursive questioning — Ajna+G63+MercSat (no G4)",
        "category": "cognitive_recursion",
        "expected_family": "cognitive_recursion",
        "why_picked": "G63 + Merc-Sat + Ajna only. Expect question_stops_protecting_you or certainty_that_never_arrives.",
        "chart": _chart(
            defined_centers=["Ajna", "Throat", "Sacral"],
            active_gates=[63],
            planets={
                "Sun":     _planet("gemini", 3),
                "Moon":    _planet("virgo", 6),
                "Mercury": _planet("gemini", 3),
                "Venus":   _planet("cancer", 4),
                "Mars":    _planet("leo", 5),
                "Saturn":  _planet("pisces", 12),
            },
            aspects=[
                _aspect("Saturn", "Mercury", "opposition"),
                _aspect("Mercury", "Neptune", "square"),
            ],
            life_path=11,  # not 7
        ),
    },
    {
        "id":       "C3_mental_overcontainment",
        "label":    "Mental overcontainment — Ajna+MercSat+Open Throat",
        "category": "cognitive_recursion",
        "expected_family": "cognitive_recursion",
        "why_picked": "Thinking is structured but can't reach speech. Should still land cognitive (with Open Throat amplifier).",
        "chart": _chart(
            defined_centers=["Ajna", "Head", "Sacral"],  # Throat OPEN
            active_gates=[17, 47, 4],
            planets={
                "Sun":     _planet("capricorn", 10),
                "Moon":    _planet("virgo", 6),
                "Mercury": _planet("capricorn", 10),
                "Venus":   _planet("aquarius", 11),
                "Mars":    _planet("scorpio", 8),
                "Saturn":  _planet("cancer", 4),
            },
            aspects=[
                _aspect("Saturn", "Mercury", "square"),
            ],
            life_path=4,
        ),
    },

    # =======================================================================
    # 3. HYBRID (3) — these are the FAILURE-MODE-RICH zones.
    # =======================================================================
    {
        "id":       "H1_open_sp_plus_ajna_no_mercsat",
        "label":    "Hybrid: Open SP + defined Ajna, NO Mercury-Saturn",
        "category": "hybrid_emotional_dominant",
        "expected_family": "emotional_permeability",  # NOT cognitive
        "why_picked": "FALSE INTELLECTUALIZATION TRAP: defined Ajna without Mercury-Saturn must NOT route into cognitive_recursion.",
        "chart": _chart(
            defined_centers=["Ajna", "Head", "Sacral"],  # SP open
            active_gates=[4, 63],
            planets={
                "Sun":     _planet("cancer", 4),
                "Moon":    _planet("pisces", 12),
                "Mercury": _planet("leo", 5),
                "Venus":   _planet("cancer", 4),
                "Mars":    _planet("taurus", 2),
                "Saturn":  _planet("libra", 7),
            },
            aspects=[
                _aspect("Saturn", "Moon", "square"),
                _aspect("Saturn", "Venus", "opposition"),
            ],
            life_path=7,  # LP7 alone — does NOT trigger certainty loop without MercSat
        ),
    },
    {
        "id":       "H2_ajna_open_sp_open_throat",
        "label":    "Hybrid: Ajna defined + Open SP + Open Throat (smart absorber)",
        "category": "hybrid_emotional_dominant",
        "expected_family": "emotional_permeability",
        "why_picked": "Smart absorptive user. Has thinking pressure but no Mercury-Saturn. Must NOT collapse into cognitive.",
        "chart": _chart(
            defined_centers=["Ajna", "Sacral", "G Center"],  # Throat + SP open
            active_gates=[63, 22],
            planets={
                "Sun":     _planet("libra", 7),
                "Moon":    _planet("cancer", 4),
                "Mercury": _planet("libra", 7),
                "Venus":   _planet("libra", 7),
                "Mars":    _planet("gemini", 3),
                "Saturn":  _planet("libra", 7),
            },
            aspects=[
                _aspect("Saturn", "Moon",  "square"),
                _aspect("Saturn", "Venus", "conjunction"),
            ],
            life_path=2,
        ),
    },
    {
        "id":       "H3_mercsat_no_ajna",
        "label":    "Hybrid: Mercury-Saturn + Open SP, NO Ajna (heavy thinker but no recursion)",
        "category": "hybrid_emotional_dominant",
        "expected_family": "emotional_permeability",
        "why_picked": "Mercury-Saturn alone does NOT make cognitive recursion. Should land permeability with derived_unresolved_cognition amplifier.",
        "chart": _chart(
            defined_centers=["Sacral", "Throat"],  # Ajna NOT defined
            active_gates=[49],
            planets={
                "Sun":     _planet("virgo", 6),
                "Moon":    _planet("scorpio", 8),
                "Mercury": _planet("libra", 7),
                "Venus":   _planet("libra", 7),
                "Mars":    _planet("aries", 1),
                "Saturn":  _planet("libra", 7),
            },
            aspects=[
                _aspect("Saturn", "Mercury", "square"),
                _aspect("Saturn", "Moon",    "square"),
            ],
            life_path=4,
        ),
    },

    # =======================================================================
    # 4. ACHIEVEMENT-PRESSURE (2) — defined Heart + Mars-Saturn / 10th house.
    # =======================================================================
    {
        "id":       "A1_mars_saturn_momentum",
        "label":    "Achievement: Defined Heart + Mars-Saturn + 10th emphasis",
        "category": "achievement_axis",
        "expected_family": "achievement_axis",
        "why_picked": "Classic momentum-as-stabilization. Expect when_momentum_stops_working.",
        "chart": _chart(
            defined_centers=["Heart", "Sacral", "Throat", "G Center", "Solar Plexus"],
            active_gates=[21, 26],
            planets={
                "Sun":     _planet("capricorn", 10),
                "Moon":    _planet("leo", 10),
                "Mercury": _planet("capricorn", 10),
                "Venus":   _planet("aquarius", 11),
                "Mars":    _planet("capricorn", 10),
                "Saturn":  _planet("aries", 1),
            },
            aspects=[
                _aspect("Saturn", "Mars", "opposition"),
            ],
            life_path=8,
        ),
    },
    {
        "id":       "A2_saturn_sun_authority",
        "label":    "Achievement: Defined Heart + Saturn-Sun + Saturn angular",
        "category": "achievement_axis",
        "expected_family": "achievement_axis",
        "why_picked": "Authority-through-pressure. Expect achievement family chapter.",
        "chart": _chart(
            defined_centers=["Heart", "Sacral", "Throat"],
            active_gates=[21],
            planets={
                "Sun":     _planet("aries", 10),
                "Moon":    _planet("taurus", 11),
                "Mercury": _planet("aries", 10),
                "Venus":   _planet("gemini", 12),
                "Mars":    _planet("leo", 1),
                "Saturn":  _planet("cancer", 1),
            },
            aspects=[
                _aspect("Saturn", "Sun", "square"),
            ],
            life_path=1,
        ),
    },

    # =======================================================================
    # 5. STABLE / NON-DRAMATIC (2) — low pressure. Should fall through to
    #    fallback OR very mild chapter. NO chapter should over-fire.
    # =======================================================================
    {
        "id":       "S1_balanced_chart",
        "label":    "Stable: balanced chart, few hard aspects",
        "category": "stable",
        "expected_family": None,  # may fallback
        "why_picked": "Should NOT collapse into any heavy archetype. Expect fallback or very mild.",
        "chart": _chart(
            defined_centers=["Sacral", "G Center", "Throat", "Heart"],
            active_gates=[31, 20],
            planets={
                "Sun":     _planet("taurus", 2),
                "Moon":    _planet("taurus", 2),
                "Mercury": _planet("taurus", 2),
                "Venus":   _planet("gemini", 3),
                "Mars":    _planet("leo", 5),
                "Saturn":  _planet("aquarius", 11),
            },
            aspects=[
                _aspect("Mercury", "Venus", "sextile"),  # not hard
            ],
            life_path=5,
        ),
    },
    {
        "id":       "S2_quiet_chart",
        "label":    "Stable: quiet chart, no major activation",
        "category": "stable",
        "expected_family": None,
        "why_picked": "Even quieter — should land in fallback (Quiet Recalibration) or low-score chapter.",
        "chart": _chart(
            defined_centers=["Sacral", "G Center"],
            active_gates=[],
            planets={
                "Sun":     _planet("leo", 5),
                "Moon":    _planet("aries", 1),
                "Mercury": _planet("leo", 5),
                "Venus":   _planet("virgo", 6),
                "Mars":    _planet("scorpio", 8),
                "Saturn":  _planet("aquarius", 11),
            },
            aspects=[],
            life_path=3,
        ),
    },

    # =======================================================================
    # 6. AVOIDANT / DETACHED (2) — emotional distancing.
    #    These users hide pressure rather than absorbing it (E-perm) or
    #    recursing on it (C-recur). Topology gap candidate.
    # =======================================================================
    {
        "id":       "AV1_12th_moon_no_recursion",
        "label":    "Avoidant: 12th house Moon, Saturn heavy, NO Ajna",
        "category": "avoidant",
        "expected_family": "emotional_permeability_or_closure",  # gray zone — flag if collapse
        "why_picked": "Hidden emotional life + Saturn heaviness but no recursion. Test whether engine over-routes to permeability vs closure.",
        "chart": _chart(
            defined_centers=["Sacral", "Heart"],
            active_gates=[],
            planets={
                "Sun":     _planet("capricorn", 12),
                "Moon":    _planet("scorpio", 12),
                "Mercury": _planet("capricorn", 12),
                "Venus":   _planet("aquarius", 1),
                "Mars":    _planet("taurus", 4),
                "Saturn":  _planet("scorpio", 10),
            },
            aspects=[
                _aspect("Saturn", "Sun", "conjunction"),
            ],
            life_path=4,
        ),
    },
    {
        "id":       "AV2_mercsat_no_ajna_withdrawn",
        "label":    "Avoidant: Mercury-Saturn + 12th Moon, NO Ajna defined",
        "category": "avoidant",
        "expected_family": "emotional_permeability_or_closure",
        "why_picked": "Intellectually withdrawn but cognitively NOT recursive (no Ajna). Should NOT fire certainty loop.",
        "chart": _chart(
            defined_centers=["Throat", "Sacral"],
            active_gates=[],
            planets={
                "Sun":     _planet("scorpio", 12),
                "Moon":    _planet("pisces", 12),
                "Mercury": _planet("scorpio", 12),
                "Venus":   _planet("sagittarius", 1),
                "Mars":    _planet("capricorn", 2),
                "Saturn":  _planet("pisces", 4),
            },
            aspects=[
                _aspect("Saturn", "Mercury", "square"),
                _aspect("Saturn", "Moon",    "conjunction"),
            ],
            life_path=8,
        ),
    },
]


# ===========================================================================
# Diagnostic evaluators
# ===========================================================================
COGNITIVE_FAMILY = "cognitive_recursion"
EMOTIONAL_FAMILY = "emotional_permeability"
ACHIEVEMENT_FAMILY = "achievement_axis"


def _shortlist_for(chart: Dict[str, Any]):
    signals = extract_signals(chart)
    shortlist = build_shortlist(signals)
    return signals, shortlist


def _enrich_shortlist_item(item: Dict[str, Any]) -> Dict[str, Any]:
    ch = get_chapter_by_id(item["chapter_id"])
    return {
        "chapter_id": item["chapter_id"],
        "title":      ch.get("title") if ch else None,
        "family":     ch.get("existential_family") if ch else None,
        "score":      item["score"],
        "matched":    item["matched_signals"],
    }


def evaluate_user(user: Dict[str, Any]) -> Dict[str, Any]:
    signals, shortlist = _shortlist_for(user["chart"])
    enriched = [_enrich_shortlist_item(s) for s in shortlist]
    top = enriched[0] if enriched else None
    adjacent = enriched[1:] if len(enriched) > 1 else []

    primary_family = (top or {}).get("family")
    expected_family = user.get("expected_family")
    category = user["category"]

    # ----- false intellectualization: routed into cognitive when shouldn't be
    false_intellectualization = False
    if primary_family == COGNITIVE_FAMILY:
        # Require the discriminator: BOTH Ajna defined AND Mercury-Saturn hard
        if not ("hd_defined_ajna" in signals and "astro_mercury_saturn_hard" in signals):
            false_intellectualization = True

    # ----- false emotionalization: cognitive user routed into emotional
    false_emotionalization = False
    if category == "cognitive_recursion" and primary_family == EMOTIONAL_FAMILY:
        false_emotionalization = True

    # ----- collapse risk heuristic
    # high: family mismatch on a categorical user
    # medium: family unset / fallback when expected something / over-flat shortlist
    # low: matches expected, has at least one adjacent
    collapse_risk = "low"
    if expected_family is not None and primary_family != expected_family:
        # Allow "or" expressions (e.g. avoidant)
        if "_or_" in str(expected_family):
            opts = expected_family.split("_or_")
            if primary_family not in opts:
                collapse_risk = "high"
        else:
            collapse_risk = "high"
    if not enriched:
        # No shortlist → fallback. For stable/quiet that's fine. For others it's medium.
        if category != "stable":
            collapse_risk = "medium"

    # ----- adjacent quality (gravitational proximity, not roulette)
    adjacent_families = [a["family"] for a in adjacent if a.get("family")]
    adjacent_distinct = len(set(adjacent_families))

    # ----- why_it_fit / why_adjacent_did_not_win
    why_it_fit = (top or {}).get("matched") or []
    why_adjacent_did_not_win = [
        f"{a['chapter_id']} (score={a['score']}, family={a['family']})"
        for a in adjacent
    ]

    # ----- emotional vs cognitive non-substitutability snapshot
    metabolization_style = "unknown"
    if primary_family == COGNITIVE_FAMILY:
        metabolization_style = "cognitive_recursive_delay"
    elif primary_family == EMOTIONAL_FAMILY:
        metabolization_style = "emotional_absorptive_silence"
    elif primary_family == ACHIEVEMENT_FAMILY:
        metabolization_style = "achievement_through_momentum"
    elif top is None:
        metabolization_style = "fallback_quiet_recalibration"
    else:
        metabolization_style = (top or {}).get("family") or "unflagged"

    notes: List[str] = []
    if false_intellectualization:
        notes.append(
            "FALSE INTELLECTUALIZATION: routed cognitive without Mercury-Saturn discriminator."
        )
    if false_emotionalization:
        notes.append(
            "FALSE EMOTIONALIZATION: cognitive-recursion user collapsed into emotional family."
        )
    if expected_family and primary_family and primary_family != expected_family and "_or_" not in str(expected_family):
        notes.append(f"Family mismatch: expected={expected_family} got={primary_family}")
    if adjacent and adjacent_distinct == 0:
        notes.append("Adjacent shortlist all same-family (mono-axis adjacency).")
    if not adjacent and category != "stable":
        notes.append("No adjacent chapters — shortlist is single-entry; thin gravity.")

    return {
        "user":                       user["id"],
        "label":                      user["label"],
        "category":                   category,
        "expected_family":            expected_family,
        "primary_chapter":            (top or {}).get("chapter_id"),
        "primary_chapter_title":      (top or {}).get("title"),
        "family":                     primary_family,
        "adjacent_chapters":          [a["chapter_id"] for a in adjacent],
        "adjacent_families":          adjacent_families,
        "metabolization_style":       metabolization_style,
        "why_it_fit":                 why_it_fit,
        "why_adjacent_did_not_win":   why_adjacent_did_not_win,
        "collapse_risk":              collapse_risk,
        "false_intellectualization":  false_intellectualization,
        "false_emotionalization":     false_emotionalization,
        "signals_extracted":          sorted(signals),
        "shortlist":                  enriched,
        "notes":                      notes,
    }


# ===========================================================================
# Report generation
# ===========================================================================
def _md_row(*cells: str) -> str:
    return "| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |"


def render_markdown(results: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append("# Timeline V2 — Stabilization Sprint Report")
    lines.append("")
    lines.append("**Build marker:** `timeline-v2-stabilization-sprint-v1`")
    lines.append("")
    lines.append("This is an existential topology test, not a copy-quality test.")
    lines.append("We are validating that the engine distinguishes HOW pressure is")
    lines.append("metabolized — not merely whether traits overlap.")
    lines.append("")

    # ----- Aggregate summary
    n = len(results)
    n_false_intel = sum(1 for r in results if r["false_intellectualization"])
    n_false_emo   = sum(1 for r in results if r["false_emotionalization"])
    n_high_risk   = sum(1 for r in results if r["collapse_risk"] == "high")
    n_med_risk    = sum(1 for r in results if r["collapse_risk"] == "medium")
    fam_counts: Dict[str, int] = {}
    for r in results:
        fam = r["family"] or "(unflagged / fallback)"
        fam_counts[fam] = fam_counts.get(fam, 0) + 1

    lines.append("## Aggregate")
    lines.append("")
    lines.append(f"- Users tested: **{n}**")
    lines.append(f"- False intellectualization: **{n_false_intel}**")
    lines.append(f"- False emotionalization: **{n_false_emo}**")
    lines.append(f"- High collapse risk: **{n_high_risk}**")
    lines.append(f"- Medium collapse risk: **{n_med_risk}**")
    lines.append(f"- Family distribution: " + ", ".join(
        f"`{k}`={v}" for k, v in sorted(fam_counts.items())
    ))
    lines.append("")

    # ----- Quick matrix
    lines.append("## Matrix")
    lines.append("")
    lines.append(_md_row("User", "Category", "Top Chapter", "Family", "Risk", "FalseIntel", "FalseEmo"))
    lines.append(_md_row("---", "---", "---", "---", "---", "---", "---"))
    for r in results:
        lines.append(_md_row(
            r["user"],
            r["category"],
            r["primary_chapter"] or "(fallback)",
            r["family"] or "(none)",
            r["collapse_risk"],
            "❌ YES" if r["false_intellectualization"] else "✅ no",
            "❌ YES" if r["false_emotionalization"] else "✅ no",
        ))
    lines.append("")

    # ----- Per-user detail
    lines.append("## Per-user detail")
    lines.append("")
    for r in results:
        lines.append(f"### {r['user']} — {r['label']}")
        lines.append("")
        lines.append(f"- **Category:** {r['category']}")
        lines.append(f"- **Expected family:** {r['expected_family']}")
        lines.append(f"- **Primary chapter:** `{r['primary_chapter']}` ({r['primary_chapter_title']})")
        lines.append(f"- **Family:** {r['family']}")
        lines.append(f"- **Metabolization style:** {r['metabolization_style']}")
        lines.append(f"- **Collapse risk:** {r['collapse_risk']}")
        lines.append(f"- **False intellectualization:** {r['false_intellectualization']}")
        lines.append(f"- **False emotionalization:** {r['false_emotionalization']}")
        lines.append("- **Adjacent:** " + (", ".join(
            f"`{r['adjacent_chapters'][i]}` ({r['adjacent_families'][i] if i < len(r['adjacent_families']) else '?'})"
            for i in range(len(r["adjacent_chapters"]))
        ) or "—"))
        lines.append("- **Why it fit (matched signals):** " + (", ".join(r["why_it_fit"]) or "—"))
        lines.append("- **Signals extracted:** " + (", ".join(r["signals_extracted"]) or "—"))
        if r["notes"]:
            lines.append("- **Notes:**")
            for n in r["notes"]:
                lines.append(f"    - {n}")
        lines.append("")

    # ----- Verdict
    lines.append("## Verdict")
    lines.append("")
    if n_false_intel == 0 and n_false_emo == 0 and n_high_risk == 0:
        lines.append("**STABILIZATION PASS.** Engine distinguishes emotional vs cognitive vs")
        lines.append("achievement metabolization styles. Safe to proceed to Timeline → Today/Home")
        lines.append("modulation (Phase 1B/1C).")
    else:
        lines.append("**STABILIZATION INCOMPLETE.** See notes per affected user. Do NOT proceed")
        lines.append("to Home/Today wiring until the topology issues below are resolved.")
    lines.append("")
    return "\n".join(lines)


# ===========================================================================
# Main
# ===========================================================================
def main() -> int:
    results = [evaluate_user(u) for u in COHORT]

    out_dir = BACKEND_ROOT / "tests"
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "stabilization_results.json"
    md_path   = out_dir / "STABILIZATION_REPORT.md"

    with json_path.open("w") as f:
        json.dump(results, f, indent=2)

    with md_path.open("w") as f:
        f.write(render_markdown(results))

    # Stdout summary
    print(f"[stabilization-sprint] tested {len(results)} users")
    fi = sum(1 for r in results if r["false_intellectualization"])
    fe = sum(1 for r in results if r["false_emotionalization"])
    hr = sum(1 for r in results if r["collapse_risk"] == "high")
    print(f"  false_intellectualization = {fi}")
    print(f"  false_emotionalization    = {fe}")
    print(f"  high_collapse_risk        = {hr}")
    print(f"\nReport: {md_path}")
    print(f"JSON:   {json_path}")
    return 0 if (fi == 0 and fe == 0 and hr == 0) else 2


if __name__ == "__main__":
    raise SystemExit(main())
