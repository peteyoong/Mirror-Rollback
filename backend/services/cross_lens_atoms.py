"""
Cross-Lens Synthesis Atoms — V1
================================
Build marker: cross-lens-atoms-v1

Detects small, deterministic "atoms" of convergence across multiple
symbolic systems (Human Design, Astrology, Numerology). An atom is
surfaced ONLY when ALL required signals match — never partial fits,
never LLM-generated. The first atom shipped is the "Certainty Pattern".

Tone rules (enforced):
  * Recognition-first ("You tend to..."), not framework-first
    ("Your Ajna is defined so...").
  * No pathologizing of Open centers, no fortune-telling, no
    grand "master synthesis" prose.
  * Each signal carries a short, lived sentence describing how it
    shows up — not a definition of the framework.

Public surface:
  compute_atoms(chart: dict) -> List[dict]
      Runs every registered detector and returns the matched atoms.
      Live computation only — no caching at this layer.

Each atom dict:
  {
    "atom_id":      "certainty_pattern",
    "name":         "Certainty Pattern",
    "recognition":  "<one-line lived statement>",
    "framing":      "<short subtitle for the card>",
    "signals":      [ {lens, label, evidence}, ... ],   # ordered HD, HD, Astro, Numerology
    "matched":      4,
    "required":     4,
    "match_mode":   "strict_all"
  }
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

BUILD_MARKER = "cross-lens-atoms-v1"

# Aspects considered "hard contacts" between Mercury and Saturn for the
# Certainty Pattern. Trines and sextiles are intentionally excluded —
# the pattern hinges on the *friction* between thought and weight.
_MERCURY_SATURN_HARD_ASPECTS = {"conjunction", "square", "opposition"}

# Hard aspect set re-used by Emotional Permeability (Moon to Neptune/Pluto).
# Same logic: hard contacts mark permeability/friction, not the soft trines.
_LUNAR_HARD_ASPECTS = {"conjunction", "square", "opposition"}

# Personal planets considered for "strong Pisces emphasis" — outer planets
# in Pisces apply generationally and would create false positives.
_PERSONAL_PLANETS_FOR_SIGN_EMPHASIS = ("Sun", "Moon", "Mercury", "Venus", "Mars")

# Angular houses for Neptune-angular check.
_ANGULAR_HOUSES = {1, 4, 7, 10}

# Tribal/emotional HD circuitry that, paired with Open Solar Plexus,
# qualifies as the HD-secondary signal for Emotional Permeability.
# Channel pairs are stored as frozensets so order does not matter.
_PERMEABILITY_CHANNELS = (
    frozenset({6, 59}),     # 6-59  Mating  (intimacy / bond)
    frozenset({39, 55}),    # 39-55 Emoting (provocation / mood)
)
_PERMEABILITY_GATES = {22, 49}  # Gate 22 Grace; Gate 49 Principles (tribal-emotional)


# ---------------------------------------------------------------------------
# Achievement-as-Stabilization configuration
# ---------------------------------------------------------------------------
# HD channels & gates that route inner uncertainty into outward building.
_ACHIEVEMENT_CHANNELS = (
    frozenset({21, 45}),    # 21-45 Authority / Money line
    frozenset({32, 54}),    # 32-54 Drive / Transformation
)
_ACHIEVEMENT_GATES = {21, 45, 54, 32}

# Saturn-to-personal-planet orb for THIS atom only.
# Standard ASPECT_TYPES orb is 8°; we tighten to 5° here to avoid the
# atom over-firing on widely-shared Saturn aspects (calibration call:
# preserves Pete @ 3.72°, Thaddeus @ 0.37°; drops Mel @ 4.08° who sits
# at the edge of conceptual drift for this specific pattern).
_SATURN_PERSONAL_TIGHT_ORB = 5.0

# Saturn-Mercury is the *fallback* astro signal — it leans toward the
# Certainty Pattern's cognitive-pressure axis rather than achievement.
# It gets an even tighter orb (3°) so it only emits when the contact is
# unambiguous. This is what cuts the Mel @ 4.08° edge-case while
# preserving truly tight Mercury-Saturn structures.
_SATURN_MERCURY_TIGHT_ORB = 3.0

# Personal points that Saturn must hit for an achievement-axis flag.
# Mercury is intentionally LAST — Mercury-Saturn alone leans toward the
# Certainty Pattern's cognitive-pressure axis rather than achievement-as-
# stabilization, so we only emit it if no stronger Saturn contact exists.
_SATURN_PERSONAL_TARGETS_PRIMARY = ("Sun", "Moon", "Mars", "Venus", "Ascendant")
_SATURN_PERSONAL_TARGETS_FALLBACK = ("Mercury",)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _safe_lower(s: Any) -> str:
    return str(s).strip().lower() if s is not None else ""


def _has_defined_ajna(hd: Dict[str, Any]) -> bool:
    centers = hd.get("defined_centers") or []
    return any(_safe_lower(c) == "ajna" for c in centers)


def _active_gates(hd: Dict[str, Any]) -> set:
    raw = hd.get("active_gates") or hd.get("all_gates") or []
    out = set()
    for g in raw:
        try:
            out.add(int(g))
        except (TypeError, ValueError):
            continue
    return out


def _mercury_saturn_aspect(astro: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return the tightest Mercury<->Saturn hard aspect, or None."""
    aspects = astro.get("aspects") or []
    best: Optional[Dict[str, Any]] = None
    for asp in aspects:
        if not isinstance(asp, dict):
            continue
        b1 = _safe_lower(asp.get("body1"))
        b2 = _safe_lower(asp.get("body2"))
        pair = {b1, b2}
        if pair != {"mercury", "saturn"}:
            continue
        atype = _safe_lower(asp.get("type"))
        if atype not in _MERCURY_SATURN_HARD_ASPECTS:
            continue
        if best is None or asp.get("orb", 99) < best.get("orb", 99):
            best = asp
    return best


def _life_path_number(numerology: Dict[str, Any]) -> Optional[int]:
    """Pulls the Life Path number from the canonical numerology payload."""
    if not numerology:
        return None
    # Canonical path: numerology.core.life_path.number
    core = numerology.get("core") or {}
    lp = core.get("life_path") or {}
    n = lp.get("number")
    if n is None:
        # Legacy: numerology.life_path.number
        lp_legacy = numerology.get("life_path") or {}
        n = lp_legacy.get("number")
    if n is None:
        return None
    try:
        return int(n)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Emotional Permeability helpers
# ---------------------------------------------------------------------------
def _has_open_solar_plexus(hd: Dict[str, Any]) -> bool:
    """Open = NOT in defined_centers. Treat 'Emotional Solar Plexus' and
    'Solar Plexus' as synonyms; the canonical HD payload uses 'Solar Plexus'."""
    centers = [_safe_lower(c) for c in (hd.get("defined_centers") or [])]
    return "solar plexus" not in centers and "emotional solar plexus" not in centers


def _defined_channels(hd: Dict[str, Any]) -> List[frozenset]:
    """Returns each defined channel as an unordered {gate1, gate2} frozenset."""
    out: List[frozenset] = []
    for ch in (hd.get("defined_channels") or []):
        if not isinstance(ch, dict):
            continue
        g1, g2 = ch.get("gate1"), ch.get("gate2")
        try:
            out.append(frozenset({int(g1), int(g2)}))
        except (TypeError, ValueError):
            continue
    return out


def _matching_permeability_channel(hd: Dict[str, Any]) -> Optional[frozenset]:
    """Return the first defined channel from the permeability set, or None."""
    defined = _defined_channels(hd)
    for ch in _PERMEABILITY_CHANNELS:
        if ch in defined:
            return ch
    return None


def _matching_permeability_gate(hd: Dict[str, Any]) -> Optional[int]:
    """Return the first active gate from the permeability gate set, or None.
    NOTE: Only used if no permeability channel is already defined."""
    gates = _active_gates(hd)
    for g in sorted(_PERMEABILITY_GATES):
        if g in gates:
            return g
    return None


def _moon_neptune_or_pluto_aspect(astro: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return the tightest Moon<->Neptune or Moon<->Pluto hard aspect, or None.
    A Moon-Neptune contact is preferred over Moon-Pluto when both exist at the
    same orb (Neptune is the more direct permeability signal)."""
    aspects = astro.get("aspects") or []
    best: Optional[Dict[str, Any]] = None
    for asp in aspects:
        if not isinstance(asp, dict):
            continue
        bodies = {_safe_lower(asp.get("body1")), _safe_lower(asp.get("body2"))}
        if "moon" not in bodies:
            continue
        if not (bodies & {"neptune", "pluto"}):
            continue
        atype = _safe_lower(asp.get("type"))
        if atype not in _LUNAR_HARD_ASPECTS:
            continue
        if best is None or asp.get("orb", 99) < best.get("orb", 99):
            best = asp
    return best


def _neptune_angular(astro: Dict[str, Any]) -> Optional[int]:
    """Return Neptune's house if angular (1/4/7/10), else None."""
    planets = astro.get("planets") or {}
    nep = planets.get("Neptune") or {}
    try:
        house = int(nep.get("house"))
    except (TypeError, ValueError):
        return None
    return house if house in _ANGULAR_HOUSES else None


def _moon_in_12th(astro: Dict[str, Any]) -> bool:
    planets = astro.get("planets") or {}
    moon = planets.get("Moon") or {}
    try:
        return int(moon.get("house")) == 12
    except (TypeError, ValueError):
        return False


def _strong_pisces_emphasis(astro: Dict[str, Any]) -> int:
    """Count of personal planets in Pisces (>= 3 = 'strong')."""
    planets = astro.get("planets") or {}
    return sum(
        1 for p in _PERSONAL_PLANETS_FOR_SIGN_EMPHASIS
        if _safe_lower(planets.get(p, {}).get("sign")) == "pisces"
    )


def _strong_ophiuchus_emphasis(astro: Dict[str, Any]) -> int:
    """Count of personal planets in Ophiuchus (>= 3 = 'strong').

    ophiuchus-first-class-content-v1. Ophiuchus is NOT a Scorpio cousin —
    its emphasis reads as integration / threshold-crossing / repair, not
    Scorpio intensity. Voice deliberately avoids 'chosen one', '13th sign
    mystery', or 'healer savior' language.
    """
    planets = astro.get("planets") or {}
    return sum(
        1 for p in _PERSONAL_PLANETS_FOR_SIGN_EMPHASIS
        if _safe_lower(planets.get(p, {}).get("sign")) == "ophiuchus"
    )


# ---------------------------------------------------------------------------
# Achievement-as-Stabilization helpers
# ---------------------------------------------------------------------------
def _has_defined_heart(hd: Dict[str, Any]) -> bool:
    """The Heart center is also called 'Ego' or 'Will' in HD literature.
    The canonical payload uses 'Ego' but we accept any of the three."""
    centers = [_safe_lower(c) for c in (hd.get("defined_centers") or [])]
    return any(c in {"ego", "heart", "will"} for c in centers)


def _matching_achievement_channel(hd: Dict[str, Any]) -> Optional[frozenset]:
    defined = _defined_channels(hd)
    for ch in _ACHIEVEMENT_CHANNELS:
        if ch in defined:
            return ch
    return None


def _matching_achievement_gate(hd: Dict[str, Any]) -> Optional[int]:
    """Return the first active gate from the achievement gate set, or None.
    Only used if no achievement channel is already defined."""
    gates = _active_gates(hd)
    for g in sorted(_ACHIEVEMENT_GATES):
        if g in gates:
            return g
    return None


def _find_saturn_personal_aspect(
    astro: Dict[str, Any],
    targets: Tuple[str, ...],
    max_orb: float = _SATURN_PERSONAL_TIGHT_ORB,
) -> Optional[Dict[str, Any]]:
    """Tightest Saturn<->{target} hard aspect within max_orb degrees."""
    targets_lower = {t.lower() for t in targets}
    # 'Ascendant' is sometimes stored as 'Asc' in aspect tables.
    if "ascendant" in targets_lower:
        targets_lower.add("asc")
    aspects = astro.get("aspects") or []
    best: Optional[Dict[str, Any]] = None
    for asp in aspects:
        if not isinstance(asp, dict):
            continue
        bodies = {_safe_lower(asp.get("body1")), _safe_lower(asp.get("body2"))}
        if "saturn" not in bodies:
            continue
        other = (bodies - {"saturn"}).pop() if (bodies - {"saturn"}) else ""
        if other not in targets_lower:
            continue
        atype = _safe_lower(asp.get("type"))
        if atype not in _LUNAR_HARD_ASPECTS:  # conj/sq/opp set reused
            continue
        try:
            orb = float(asp.get("orb"))
        except (TypeError, ValueError):
            orb = 99.0
        if orb > max_orb:
            continue
        if best is None or orb < float(best.get("orb", 99)):
            best = asp
    return best


def _find_aspect(
    astro: Dict[str, Any],
    body_a: str,
    body_b: str,
    types: set,
) -> Optional[Dict[str, Any]]:
    """Tightest aspect of any qualifying type between body_a and body_b."""
    a_l, b_l = body_a.lower(), body_b.lower()
    pair = {a_l, b_l}
    best: Optional[Dict[str, Any]] = None
    for asp in (astro.get("aspects") or []):
        if not isinstance(asp, dict):
            continue
        if {_safe_lower(asp.get("body1")), _safe_lower(asp.get("body2"))} != pair:
            continue
        if _safe_lower(asp.get("type")) not in types:
            continue
        if best is None or asp.get("orb", 99) < best.get("orb", 99):
            best = asp
    return best


def _saturn_angular(astro: Dict[str, Any]) -> Optional[int]:
    sat = (astro.get("planets") or {}).get("Saturn") or {}
    try:
        h = int(sat.get("house"))
    except (TypeError, ValueError):
        return None
    return h if h in _ANGULAR_HOUSES else None


def _personal_planet_count_by(
    astro: Dict[str, Any],
    *,
    sign: Optional[str] = None,
    house: Optional[int] = None,
) -> int:
    """Count of personal planets matching the given sign OR house."""
    planets = astro.get("planets") or {}
    count = 0
    for p in _PERSONAL_PLANETS_FOR_SIGN_EMPHASIS:
        pd = planets.get(p) or {}
        if sign is not None and _safe_lower(pd.get("sign")) != sign.lower():
            continue
        if house is not None:
            try:
                if int(pd.get("house")) != house:
                    continue
            except (TypeError, ValueError):
                continue
        count += 1
    return count


def _expression_number(numerology: Dict[str, Any]) -> Optional[int]:
    """Pulls Expression number from canonical numerology payload, if present."""
    if not numerology:
        return None
    core = numerology.get("core") or {}
    expr = core.get("expression") or numerology.get("expression") or {}
    n = expr.get("number") if isinstance(expr, dict) else None
    if n is None:
        return None
    try:
        return int(n)
    except (TypeError, ValueError):
        return None


def _format_orb(orb: Any) -> str:
    try:
        return f"{float(orb):.1f}°"
    except (TypeError, ValueError):
        return "tight"


# ---------------------------------------------------------------------------
# Detector: Certainty Pattern
# ---------------------------------------------------------------------------
def detect_certainty_pattern(chart: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Strict ALL-4 detector for the 'Certainty Pattern' atom.

    Required signals:
      1. HD: Defined Ajna
      2. HD: Gate 4 (Answers) OR Gate 63 (Doubt) in active gates
      3. Astro: Mercury <-> Saturn conjunction/square/opposition
      4. Numerology: Life Path 7
    """
    if not isinstance(chart, dict):
        return None

    hd = chart.get("human_design") or {}
    astro = chart.get("astrology") or {}
    num = chart.get("numerology") or {}

    if not _has_defined_ajna(hd):
        return None

    gates = _active_gates(hd)
    has_g4 = 4 in gates
    has_g63 = 63 in gates
    if not (has_g4 or has_g63):
        return None

    aspect = _mercury_saturn_aspect(astro)
    if aspect is None:
        return None

    lp = _life_path_number(num)
    if lp != 7:
        return None

    # All 4 matched — build signals (HD center, HD gate(s), Astro, Numerology).
    if has_g4 and has_g63:
        gate_label = "Gates 4 & 63 — Answers & Doubt"
        gate_evidence = (
            "You carry both the drive to give an answer and the instinct to "
            "doubt it. They argue with each other inside the same thought."
        )
    elif has_g4:
        gate_label = "Gate 4 — Answers"
        gate_evidence = (
            "You're the one who reaches for an answer when things feel "
            "uncertain — even before you've fully worked it out."
        )
    else:
        gate_label = "Gate 63 — Doubt"
        gate_evidence = (
            "You question the answer the moment it lands. Doubt is the way "
            "your mind double-checks reality."
        )

    aspect_type = _safe_lower(aspect.get("type")).capitalize()
    orb = aspect.get("orb")
    try:
        orb_txt = f"{float(orb):.1f}°"
    except (TypeError, ValueError):
        orb_txt = "tight"

    astro_label = f"Mercury {aspect_type} Saturn ({orb_txt})"
    astro_evidence = (
        "How you think is shaped by patience and weight. Answers don't come "
        "fast for you — but the ones that hold, hold for a long time."
    )

    signals: List[Dict[str, str]] = [
        {
            "lens": "Human Design",
            "label": "Defined Ajna",
            "evidence": (
                "Your Ajna is consistent — once you land on a way of seeing "
                "something, it stays. Others borrow that certainty from you, "
                "which can quietly raise the stakes on getting it right."
            ),
        },
        {
            "lens": "Human Design",
            "label": gate_label,
            "evidence": gate_evidence,
        },
        {
            "lens": "Astrology",
            "label": astro_label,
            "evidence": astro_evidence,
        },
        {
            "lens": "Numerology",
            "label": "Life Path 7",
            "evidence": (
                "Your path leans toward analysis and inner verification. "
                "Easy answers don't satisfy — you want the one that survives "
                "your own scrutiny."
            ),
        },
    ]

    return {
        "atom_id": "certainty_pattern",
        "name": "Certainty Pattern",
        "framing": "Where different systems point to the same thing.",
        "recognition": (
            "You tend to look for certainty under pressure — and to doubt "
            "the answer the moment you've found one."
        ),
        "signals": signals,
        "matched": 4,
        "required": 4,
        "match_mode": "strict_all",
    }


# ---------------------------------------------------------------------------
# Detector: Emotional Permeability
# ---------------------------------------------------------------------------
def detect_emotional_permeability(chart: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Strict detector for the 'Emotional Permeability' atom.

    This atom is NOT emotionality, empathy, spirituality or "deep feeling".
    It IS: lower emotional separation thresholds, faster relational
    absorption, environments entering the system before the person
    decides whether to carry them.

    Required signals (strict, all 3 must match):
      1. HD-primary:   Open Solar Plexus
      2. HD-secondary: at least ONE of —
           * defined channel 6-59 (Mating)
           * defined channel 39-55 (Emoting)
           * active gate 22 (Grace)
           * active gate 49 (Principles / tribal-emotional)
      3. Astrology:    at least ONE of —
           * Moon-Neptune hard aspect (conj/sq/opp)
           * Moon-Pluto hard aspect (conj/sq/opp)
           * Neptune in an angular house (1/4/7/10)
           * Moon in 12th house
           * Strong Pisces emphasis (>= 3 personal planets in Pisces)

    Supporting (NEVER required, NEVER triggers alone):
      4. Numerology Life Path 2, 6, or 11 — added to the signals list
         when present, but the atom can fire without it.
    """
    if not isinstance(chart, dict):
        return None

    hd = chart.get("human_design") or {}
    astro = chart.get("astrology") or {}
    num = chart.get("numerology") or {}

    # --- Required: HD primary
    if not _has_open_solar_plexus(hd):
        return None

    # --- Required: HD secondary (channels preferred over gates)
    hd_channel = _matching_permeability_channel(hd)
    hd_gate: Optional[int] = None
    if hd_channel is None:
        hd_gate = _matching_permeability_gate(hd)
        if hd_gate is None:
            return None

    # --- Required: Astrology (find the *strongest* available marker)
    astro_signal_label: Optional[str] = None
    astro_signal_evidence: Optional[str] = None

    lunar_aspect = _moon_neptune_or_pluto_aspect(astro)
    if lunar_aspect is not None:
        bodies = {_safe_lower(lunar_aspect.get("body1")), _safe_lower(lunar_aspect.get("body2"))}
        other = "Neptune" if "neptune" in bodies else "Pluto"
        atype = _safe_lower(lunar_aspect.get("type")).capitalize()
        try:
            orb_txt = f"{float(lunar_aspect.get('orb')):.1f}°"
        except (TypeError, ValueError):
            orb_txt = "tight"
        astro_signal_label = f"Moon {atype} {other} ({orb_txt})"
        if other == "Neptune":
            astro_signal_evidence = (
                "Your Moon meets Neptune at a hard angle. Emotional boundaries "
                "blur — feelings nearby become hard to label as 'mine' versus "
                "'theirs' until you slow down."
            )
        else:
            astro_signal_evidence = (
                "Your Moon contacts Pluto. Emotional undercurrents aren't "
                "filtered — you feel the pressure under what's said before "
                "it's said."
            )
    else:
        neptune_house = _neptune_angular(astro)
        if neptune_house is not None:
            astro_signal_label = f"Neptune angular (house {neptune_house})"
            astro_signal_evidence = (
                "Neptune is angular in your chart, which keeps emotional "
                "permeability close to the visible parts of you — body, home, "
                "relationships, or the role you play in public."
            )
        elif _moon_in_12th(astro):
            astro_signal_label = "Moon in the 12th house"
            astro_signal_evidence = (
                "Your Moon is in the 12th. Your emotional life often runs "
                "underneath — picking up what's in the collective field before "
                "it becomes conscious to anyone in the room."
            )
        else:
            pisces_count = _strong_pisces_emphasis(astro)
            if pisces_count >= 3:
                astro_signal_label = f"{pisces_count} personal planets in Pisces"
                astro_signal_evidence = (
                    "Multiple personal planets in Pisces — emotional and "
                    "energetic absorption is built into how you process most "
                    "things, not a mood you switch on."
                )

    if astro_signal_label is None:
        return None

    # All required signals matched — assemble the atom.
    sp_evidence = (
        "Your Solar Plexus is open. Emotional waves don't have a fixed shape "
        "inside you — what's in the room can pass through and start to feel "
        "like yours without a clear seam."
    )

    if hd_channel is not None:
        if hd_channel == frozenset({6, 59}):
            hd_secondary_label = "Channel 6-59 — Intimacy"
            hd_secondary_evidence = (
                "You're wired for close bonding. The closer the contact, the "
                "harder it is to tell where your emotion stops and the other "
                "person's starts."
            )
        else:  # 39-55
            hd_secondary_label = "Channel 39-55 — Moodiness"
            hd_secondary_evidence = (
                "You carry the wave that provokes feeling in others — and the "
                "wave they're already in lands on you just as fast."
            )
    else:
        # Single gate fallback
        if hd_gate == 22:
            hd_secondary_label = "Gate 22 — Grace"
            hd_secondary_evidence = (
                "Gate 22 leans you toward emotional openness — receiving the "
                "room — which can quietly turn into carrying it."
            )
        else:  # 49
            hd_secondary_label = "Gate 49 — Principles"
            hd_secondary_evidence = (
                "Gate 49 keeps your emotional radar tuned to the people "
                "around you. You read the room before deciding whether you "
                "want to be in it."
            )

    signals: List[Dict[str, str]] = [
        {"lens": "Human Design", "label": "Open Solar Plexus",   "evidence": sp_evidence},
        {"lens": "Human Design", "label": hd_secondary_label,    "evidence": hd_secondary_evidence},
        {"lens": "Astrology",    "label": astro_signal_label,    "evidence": astro_signal_evidence},
    ]

    # Optional supporting numerology — adds, never triggers alone.
    lp = _life_path_number(num)
    if lp in (2, 6, 11):
        if lp == 2:
            num_evidence = (
                "Your path leans toward attunement and partnership — which "
                "compounds the absorption rather than countering it."
            )
        elif lp == 6:
            num_evidence = (
                "Your path leans toward caretaking and harmony — which biases "
                "you to absorb the room and tend it before locating yourself."
            )
        else:  # 11
            num_evidence = (
                "Your path runs on heightened sensitivity. The dial is "
                "already turned up before anyone else touches it."
            )
        signals.append({
            "lens":       "Numerology",
            "label":      f"Life Path {lp} (supporting)",
            "evidence":   num_evidence,
        })

    return {
        "atom_id":      "emotional_permeability",
        "name":         "Emotional Permeability",
        "framing":      "Where different systems point to the same thing.",
        "recognition": (
            "Emotional environments enter you quickly. You often adapt to "
            "what others are feeling before deciding whether you actually "
            "want to carry it."
        ),
        "signals":      signals,
        "matched":      len(signals),
        "required":     len(signals),
        "match_mode":   "strict_all",
        # Internal fields — not load-bearing for the UI, useful for analytics.
        "core_signals_required": 3,
        "has_supporting":        len(signals) > 3,
    }


# ---------------------------------------------------------------------------
# Detector: Achievement-as-Stabilization
# ---------------------------------------------------------------------------
def detect_achievement_as_stabilization(chart: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Strict detector for the 'Achievement-as-Stabilization' atom.

    This atom is NOT ambition, success orientation, founder energy,
    productivity or hustle identity.
    This atom IS: accomplishment regulating inner instability, movement
    replacing emotional uncertainty, building as a way to find solid
    ground when the inside feels unresolved.

    Required (strict AND):
      1. HD primary: at least ONE of —
           * defined channel 21-45 (Authority)
           * defined channel 32-54 (Drive)
           * active gate 21 (Control)
           * active gate 45 (Gatherer)
           * active gate 54 (Ambition)
           * active gate 32 (Continuity)

      2. Astrology: at least ONE of (priority order, tightest wins per group):
           * Mars-Saturn hard aspect (conj/sq/opp)
           * Saturn-MC hard aspect
           * Mars-MC hard aspect
           * Saturn-to-personal hard aspect (Sun/Moon/Mars/Venus/Asc)
             — capped at 5.0° orb (tighter than the default 8°)
           * Saturn-to-Mercury hard aspect (fallback ONLY; Mercury-Saturn
             leans toward the Certainty Pattern's cognitive-pressure axis
             so it never dominates)
           * Saturn angular (house 1/4/7/10)
           * Capricorn emphasis (>=3 personal planets in Capricorn)
           * 10th-house emphasis (>=3 personal planets in house 10)

    Supporting (NEVER required, NEVER triggers alone):
      3. Defined Heart center (Ego/Will) — adds a 2nd HD signal when present
      4. Numerology Life Path or Expression 4 or 8 — adds a Numerology
         supporting signal when present
    """
    if not isinstance(chart, dict):
        return None

    hd = chart.get("human_design") or {}
    astro = chart.get("astrology") or {}
    num = chart.get("numerology") or {}

    # --- Required HD primary
    hd_channel = _matching_achievement_channel(hd)
    hd_gate: Optional[int] = None
    if hd_channel is None:
        hd_gate = _matching_achievement_gate(hd)
        if hd_gate is None:
            return None

    # --- Required Astro (priority-ordered, deterministic)
    astro_label: Optional[str] = None
    astro_evidence: Optional[str] = None
    astro_kind: Optional[str] = None  # internal: used for confidence scoring

    # 1) Mars-Saturn hard (strongest)
    asp = _find_aspect(astro, "Mars", "Saturn", _LUNAR_HARD_ASPECTS)
    if asp:
        astro_label = f"Mars {_safe_lower(asp['type']).capitalize()} Saturn ({_format_orb(asp.get('orb'))})"
        astro_evidence = (
            "Mars and Saturn meet at a hard angle in you — desire and "
            "discipline argue inside the same impulse. Effort doesn't "
            "relax; it converts to output."
        )
        astro_kind = "mars_saturn"

    # 2) Saturn-MC hard
    if astro_label is None:
        asp = _find_aspect(astro, "Saturn", "MC", _LUNAR_HARD_ASPECTS)
        if asp:
            astro_label = f"Saturn {_safe_lower(asp['type']).capitalize()} MC ({_format_orb(asp.get('orb'))})"
            astro_evidence = (
                "Saturn presses directly on the achievement axis of your "
                "chart. Public progress becomes one of the ways you feel "
                "real."
            )
            astro_kind = "saturn_mc"

    # 3) Mars-MC hard
    if astro_label is None:
        asp = _find_aspect(astro, "Mars", "MC", _LUNAR_HARD_ASPECTS)
        if asp:
            astro_label = f"Mars {_safe_lower(asp['type']).capitalize()} MC ({_format_orb(asp.get('orb'))})"
            astro_evidence = (
                "Mars sits on the achievement axis of your chart. The drive "
                "to make something happen wires close to your visible "
                "direction."
            )
            astro_kind = "mars_mc"

    # 4) Saturn-to-personal-primary (Sun/Moon/Mars/Venus/Asc), tight orb (≤5°)
    if astro_label is None:
        asp = _find_saturn_personal_aspect(astro, _SATURN_PERSONAL_TARGETS_PRIMARY)
        if asp:
            bodies = {_safe_lower(asp.get("body1")), _safe_lower(asp.get("body2"))}
            other_raw = (bodies - {"saturn"}).pop()
            other = "Ascendant" if other_raw == "asc" else other_raw.capitalize()
            astro_label = f"Saturn {_safe_lower(asp['type']).capitalize()} {other} ({_format_orb(asp.get('orb'))})"
            # Mechanism-only phrasing — earlier "you build where others rest"
            # phrasing introduced a comparative-trait framing ("where most
            # people just live") that drifted toward exceptionalism / founder
            # flattery when surfaced on real operators. The atom's core rule
            # is movement-as-regulation, NOT achievement-as-identity.
            astro_evidence = (
                "Saturn presses on a personal point in your chart. Structure "
                "and weight attach close to who you are — so making something "
                "real becomes a way of steadying that part."
            )
            astro_kind = "saturn_personal"

    # 5) Saturn-Mercury (fallback only — demoted to prevent over-firing,
    #    AND tightened to 3.0° orb since Mercury-Saturn at wider orbs
    #    leans into the Certainty Pattern's cognitive-pressure axis
    #    rather than achievement-as-stabilization)
    if astro_label is None:
        asp = _find_saturn_personal_aspect(
            astro,
            _SATURN_PERSONAL_TARGETS_FALLBACK,
            max_orb=_SATURN_MERCURY_TIGHT_ORB,
        )
        if asp:
            astro_label = f"Saturn {_safe_lower(asp['type']).capitalize()} Mercury ({_format_orb(asp.get('orb'))})"
            astro_evidence = (
                "Your thinking carries Saturn's weight — you organise and "
                "build with thought, and unresolved questions push you "
                "toward making something measurable."
            )
            astro_kind = "saturn_mercury"

    # 6) Saturn angular
    if astro_label is None:
        h = _saturn_angular(astro)
        if h is not None:
            astro_label = f"Saturn angular (house {h})"
            astro_evidence = (
                "Saturn is angular — duty, structure and 'must build' "
                "pressure sit close to the visible parts of your life: "
                "body, home, partnerships, or public role."
            )
            astro_kind = "saturn_angular"

    # 7) Capricorn stellium (>=3 personal)
    if astro_label is None:
        cap_n = _personal_planet_count_by(astro, sign="Capricorn")
        if cap_n >= 3:
            astro_label = f"{cap_n} personal planets in Capricorn"
            astro_evidence = (
                "Multiple personal planets in Capricorn. Building, climbing "
                "and earning ground is baked into how you process most "
                "things — not a mode you switch into."
            )
            astro_kind = "capricorn_stellium"

    # 8) 10th-house stellium
    if astro_label is None:
        h10_n = _personal_planet_count_by(astro, house=10)
        if h10_n >= 3:
            astro_label = f"{h10_n} personal planets in 10th house"
            astro_evidence = (
                "Multiple personal planets in your 10th. The pull to make "
                "yourself legible in the world isn't a phase, it's wiring."
            )
            astro_kind = "tenth_house_stellium"

    if astro_label is None:
        return None

    # --- Assemble signals
    signals: List[Dict[str, str]] = []

    # HD primary
    if hd_channel is not None:
        if hd_channel == frozenset({21, 45}):
            signals.append({
                "lens":     "Human Design",
                "label":    "Channel 21-45 — Authority",
                "evidence": (
                    "You're wired to take charge of what's around you. "
                    "When the field gets uncertain, you reach for what you "
                    "can govern — including yourself."
                ),
            })
        else:  # 32-54
            signals.append({
                "lens":     "Human Design",
                "label":    "Channel 32-54 — Drive",
                "evidence": (
                    "You carry a striving wave — pressure converts to "
                    "ambition fast. Moving up and forward is how the "
                    "system discharges uncertainty."
                ),
            })
    else:
        gate_labels = {
            21: ("Gate 21 — Control",
                 "Gate 21 turns unease into the move to handle what's in "
                 "front of you. You manage when you can't yet rest."),
            45: ("Gate 45 — Gatherer",
                 "Gate 45 leans you toward holding ground for others. "
                 "Building something legible becomes the way you provide "
                 "— and steady yourself."),
            54: ("Gate 54 — Ambition",
                 "Gate 54 is straight-line upward pressure. Striving "
                 "doesn't feel optional — it feels like the floor."),
            32: ("Gate 32 — Continuity",
                 "Gate 32 watches what survives. Endurance becomes proof "
                 "— keeping something alive is how the system knows "
                 "it's stable."),
        }
        lbl, ev = gate_labels[hd_gate]
        signals.append({"lens": "Human Design", "label": lbl, "evidence": ev})

    # HD supporting: Defined Heart center
    heart_defined = _has_defined_heart(hd)
    if heart_defined:
        signals.append({
            "lens":     "Human Design",
            "label":    "Defined Heart (Ego)",
            "evidence": (
                "Your Heart is defined — willpower runs on a consistent "
                "supply. That makes building something measurable a "
                "viable steadying move, not just an aspiration."
            ),
        })

    # Astro
    signals.append({"lens": "Astrology", "label": astro_label, "evidence": astro_evidence})

    # Numerology supporting (LP or Expression 4/8)
    lp = _life_path_number(num)
    expr = _expression_number(num)
    num_match: Optional[Tuple[str, int]] = None
    if lp in (4, 8):
        num_match = ("Life Path", lp)
    elif expr in (4, 8):
        num_match = ("Expression", expr)

    if num_match is not None:
        kind, n = num_match
        if n == 4:
            ev = (
                "Your path leans toward structure and steady effort — "
                "work and order are the materials your system uses to "
                "feel safe."
            )
        else:  # 8
            ev = (
                "Your path is wired around mastery and material outcomes. "
                "Building something tangible is part of how you metabolize "
                "being alive."
            )
        signals.append({
            "lens":     "Numerology",
            "label":    f"{kind} {n} (supporting)",
            "evidence": ev,
        })

    # Internal confidence scoring (not load-bearing for UI; useful for
    # telemetry / future weighting work). Bigger = more recognitional.
    confidence = 1.0
    if astro_kind in {"mars_saturn", "saturn_mc", "mars_mc"}:
        confidence += 0.6
    elif astro_kind == "saturn_personal":
        confidence += 0.4
    elif astro_kind in {"capricorn_stellium", "tenth_house_stellium"}:
        confidence += 0.3
    elif astro_kind == "saturn_angular":
        confidence += 0.2
    elif astro_kind == "saturn_mercury":
        confidence += 0.1  # Lowest — also caps total ceiling for this fallback
    if heart_defined:
        confidence += 0.4
    if hd_channel is not None:
        confidence += 0.3
    if num_match is not None:
        confidence += 0.2

    return {
        "atom_id":      "achievement_as_stabilization",
        "name":         "Achievement as Stabilization",
        "framing":      "Where different systems point to the same thing.",
        "recognition": (
            "When the inside feels unresolved, you look for something to "
            "build, fix, win, or move forward. Achievement becomes less "
            "about status and more about finding solid ground."
        ),
        "signals":      signals,
        "matched":      len(signals),
        "required":     len(signals),
        "match_mode":   "strict_all",
        # Internal fields — not used by the UI.
        "core_signals_required": 2,    # HD primary + astro
        "has_supporting":        len(signals) > 2,
        "confidence":            round(confidence, 2),
        "astro_kind":            astro_kind,
    }


# ---------------------------------------------------------------------------
# Registry + public entry point
# ---------------------------------------------------------------------------
# Order matters for display: first match in this list is shown first.
_DETECTORS = [
    detect_certainty_pattern,
    detect_emotional_permeability,
    detect_achievement_as_stabilization,
]


def compute_atoms(chart: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run every registered atom detector against the user's chart.

    Returns an ordered list of matched atoms. Atoms that fail any required
    signal are silently omitted — there is no "partial" surface yet.
    """
    if not chart:
        return []

    matched: List[Dict[str, Any]] = []
    for detector in _DETECTORS:
        try:
            atom = detector(chart)
        except Exception as e:  # noqa: BLE001 - never let one bad detector kill the rest
            logger.warning(
                f"[CrossLensAtoms] detector {detector.__name__} raised: {e}"
            )
            continue
        if atom:
            matched.append(atom)
    return matched
