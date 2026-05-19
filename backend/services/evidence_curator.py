"""
Evidence Curator
================

Build marker: evidence-drawer-v2

This module turns the raw internal debug payloads (master_voice,
pattern_memory, relational, lens, compression, intensity) into a small,
*curated, user-facing* `evidence` object that the Evidence Drawer
("Why this is showing up") can render.

CRITICAL design rules:

    1. The user-facing evidence is ALWAYS in plain language.  Never
       leaks framework jargon (no "Sun in Scorpio", no "Gate 43",
       no "Life Path 7", no "Day Master Wood").  Frameworks appear
       only as lightweight ATTRIBUTION labels — never as data dumps.

    2. The user-facing evidence is SEPARATE from the raw `debug`
       payload.  Frontend dev tools read `debug` for diagnostics.
       Users see `evidence`, which is curated.

    3. Recurrence is shown softly.  "This theme has surfaced a few
       times recently."  NEVER "On March 4th you said…".

    4. Relational moderation is shown when relevant ("This response
       was moderated by a parent/child relational ceiling.").

    5. Contradiction-friendly framing is implicit — recognitions
       are probabilistic ("seems to organise around…"), never
       declarative.

The returned shape is small.  Frontend renders whatever is present
and skips empty fields.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# Human-readable framework labels (lightweight attribution).
_FRAMEWORK_LABEL: Dict[str, str] = {
    "astrology":    "Astrology",
    "human_design": "Human Design",
    "numerology":   "Numerology",
    "enneagram":    "Enneagram",
    "bazi":         "BaZi",
}


# Pattern key → plain-language phrasing for the user-facing drawer.
# Kept compact and behavioural — never absolutist.
_PATTERN_USER_PHRASING: Dict[str, str] = {
    "work_exhaustion":        "a recurring sense of being depleted by work",
    "career_direction":       "a recurring question about the current path",
    "authority_conflict":     "a recurring friction with authority figures",
    "relational_distance":    "a recurring sense of distance in close relationships",
    "attachment_anxiety":     "a recurring fear of being left",
    "intimacy_block":         "a recurring difficulty opening up emotionally",
    "parental_pattern":       "a recurring dynamic with the parental field",
    "child_distance":         "a recurring distance with your child",
    "sibling_friction":       "a recurring friction with a sibling",
    "identity_question":      "a recurring question of identity",
    "self_worth_questioning": "a recurring undercurrent of not-enough-ness",
    "avoidance_pattern":      "a recurring pattern of avoidance",
    "people_pleasing":        "a recurring pull to over-give",
    "perfectionism":          "a recurring pull toward perfectionism",
    "control_pattern":        "a recurring need-to-control pattern",
    "shutdown_pattern":       "a recurring shutdown response under pressure",
    "anxiety_loop":           "a recurring anxiety / overthinking loop",
    "grief_processing":       "a recurring grief layer surfacing again",
    "anger_pattern":          "a recurring anger / resentment thread",
}


_RELATIONSHIP_CLASS_LABEL: Dict[str, str] = {
    "romantic":     "a romantic-partner relational context",
    "former":       "a former-partner relational context",
    "child":        "a parent–child relational context",
    "family_adult": "an adult family-member context",
    "friendship":   "a friendship context",
    "professional": "a professional / colleague context",
    "authority":    "a context where the other person holds authority over you",
    "power_over":   "a context where you hold authority over the other person",
    "mentorship":   "a mentor / mentee context",
    "other":        "a one-to-one relational context",
}


def _pattern_phrase(pattern_key: str) -> str:
    return _PATTERN_USER_PHRASING.get(
        pattern_key,
        pattern_key.replace("_", " "),
    )


def _curate_recurrence(pm: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Soft, surveillance-free recurrence line.
    Returns None when there is nothing useful to say.
    """
    if not pm or not isinstance(pm, dict):
        return None
    matched = pm.get("matched_patterns") or []
    if not matched:
        return None
    # Find at least one moderate+ pattern (others are too weak to mention).
    moderate_or_strong = [
        p for p in matched
        if isinstance(p, dict) and p.get("confidence") in ("moderate", "strong")
    ]
    if not moderate_or_strong:
        return None
    # Lead with the strongest, named in plain language.
    p0 = moderate_or_strong[0]
    phrase = _pattern_phrase(p0.get("pattern_key", "") or "")
    # If there are 2+ moderate/strong patterns, keep the line gentle.
    if len(moderate_or_strong) >= 2:
        return f"{phrase} — this thread has surfaced a few times recently"
    return f"{phrase} — this has surfaced before"


def _curate_relational(rel: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Curated relational moderation summary for the drawer.
    Returns None when no relational layer fired.
    """
    if not rel or not isinstance(rel, dict):
        return None
    cls = (rel.get("relationship_class") or "").strip().lower()
    if not cls:
        return None
    ceiling = rel.get("relationship_intensity_ceiling")
    applied = rel.get("intensity_applied") or rel.get("applied_intensity")
    projection = rel.get("projection_risk")

    moderation: List[str] = []
    label = _RELATIONSHIP_CLASS_LABEL.get(cls, "a relational context")
    moderation.append(label)
    if ceiling:
        moderation.append(f"intensity ceiling {ceiling.lower()}")
    # Surface projection safeguards softly.
    pr = (projection or "").strip().lower() if isinstance(projection, str) else None
    if pr in ("moderate", "high", "elevated"):
        moderation.append("projection safeguards engaged")

    return {
        "moderated_by": moderation,
        "applied_intensity": applied,
    }


def _curate_master_voice(mv: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    For Life Tab Master Voice replies — pull out the dominant signal in
    plain language, plus the framework attribution.  No jargon dump.
    """
    if not mv or not isinstance(mv, dict):
        return None
    dom = mv.get("dominant_signal") or None
    contributing = mv.get("contributing_frameworks") or []
    attribution: List[str] = []
    for f in contributing:
        lbl = _FRAMEWORK_LABEL.get(f)
        if lbl and lbl not in attribution:
            attribution.append(lbl)

    out: Dict[str, Any] = {"domain": mv.get("domain")}
    if dom and isinstance(dom, dict):
        sig = (dom.get("signal") or "").strip()
        if sig:
            out["dominant_pattern"] = sig
    if attribution:
        out["frameworks"] = attribution
    return out if (out.get("dominant_pattern") or out.get("frameworks")) else None


def _curate_lens(lens_dbg: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    For single-lens chats, pull out the active entity name and the lens
    label so the drawer can show e.g. "Astrology · Sun".
    """
    if not lens_dbg or not isinstance(lens_dbg, dict):
        return None
    lens_name = lens_dbg.get("lens")
    active = lens_dbg.get("active_entity") or None
    if not lens_name:
        return None
    out: Dict[str, Any] = {
        "framework": _FRAMEWORK_LABEL.get(lens_name, lens_name.title()),
    }
    if active and isinstance(active, dict):
        nm = active.get("name")
        kind = active.get("kind")
        if nm:
            out["focus"] = nm
        if kind:
            out["focus_kind"] = kind
    return out


def curate_evidence(debug: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Public entry-point.  Given the FULL `debug` payload returned by
    /api/mirror/chat, produce a small user-facing `evidence` object.

    Returns None when there is genuinely nothing curated to show (very
    rare — usually at least compression / intensity exist).
    """
    if not debug or not isinstance(debug, dict):
        return None

    evidence: Dict[str, Any] = {"marker": "evidence-drawer-v2"}

    # --- Master voice (Life Tab) ------------------------------------------
    mv_curated = _curate_master_voice(debug.get("master_voice"))
    if mv_curated:
        evidence["master_voice"] = mv_curated

    # --- Single-lens active entity ----------------------------------------
    # The dispatcher writes lens fields at the top level (active_entity,
    # active_entity_source, lens, depth_mode, intensity_mode) — same
    # object as lens_debug_payload.  We curate from `debug` directly.
    if debug.get("lens") and debug.get("active_entity"):
        lens_curated = _curate_lens(debug)
        if lens_curated:
            evidence["lens"] = lens_curated

    # --- Relational moderation (Ask About Person) -------------------------
    rel_curated = _curate_relational(debug.get("relational"))
    if rel_curated:
        evidence["relational"] = rel_curated

    # --- Recurrence (longitudinal pattern memory) -------------------------
    rec = _curate_recurrence(debug.get("pattern_memory"))
    if rec:
        evidence["recurrence"] = rec

    # --- Conversational calibration (depth + intensity) -------------------
    # Surface these as tiny labels — the drawer can show "Reflective ·
    # Observational" rather than the raw mode strings.  Different code
    # paths write the modes at different locations:
    #   - lens dispatcher writes them at top level
    #     (debug.depth_mode / debug.intensity_mode OR debug.compression_mode)
    #   - life-tab master voice nests them under debug.master_voice.*
    #   - relational (Ask About Person) writes intensity at
    #     debug.relational.intensity_applied
    # Accept any of the above.
    mv_dbg = debug.get("master_voice") if isinstance(debug.get("master_voice"), dict) else {}
    rel_dbg = debug.get("relational") if isinstance(debug.get("relational"), dict) else {}
    depth = (
        debug.get("depth_mode")
        or debug.get("compression_mode")
        or (mv_dbg.get("depth_mode") if mv_dbg else None)
        or ""
    ).upper()
    intensity = (
        debug.get("intensity_mode")
        or (mv_dbg.get("intensity_mode") if mv_dbg else None)
        or (rel_dbg.get("intensity_applied") if rel_dbg else None)
        or (rel_dbg.get("applied_intensity") if rel_dbg else None)
        or ""
    ).upper()
    # If we have no calibration signals at all (rare — generic chat with
    # no lens / no person / no life-domain), default to the most common
    # baseline so the drawer always has SOMETHING calm to show.  This
    # keeps the user-facing experience consistent across surfaces while
    # still being honest (these are the platform defaults).
    if not depth and not intensity:
        depth = "NORMAL"
        intensity = "OBSERVATIONAL"
    calibration: List[str] = []
    if depth:
        calibration.append({
            "LIGHT":  "light touch",
            "NORMAL": "reflective",
            "DEEP":   "deep dive",
        }.get(depth, depth.lower()))
    if intensity:
        calibration.append({
            "SOFT":          "softened",
            "OBSERVATIONAL": "observational",
            "DIRECT":        "direct",
            "CONFRONTING":   "confronting",
        }.get(intensity, intensity.lower()))
    if calibration:
        evidence["calibration"] = calibration

    # If the only thing in evidence is the marker, return None (nothing
    # interesting to show).
    if list(evidence.keys()) == ["marker"]:
        return None
    return evidence
