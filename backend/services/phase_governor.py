"""
Phase Governor — Timeline V2 / Phase Architecture
=================================================
Build marker: timeline-v2-archetype-differentiation-v1

Resolves the single Governing Life Chapter (3-9 month window) for a user.
The chapter is the gravitational center of the new Timeline V2 — every
existing yearly timeline card eventually becomes a "Pressure Window"
derived FROM the chapter, not parallel to it.

Architecture (load-bearing):
  1. Extract a deterministic SIGNAL VECTOR from the user's natal chart
     + their existing yearly timeline payload.

     v1A signals: raw structural traits (Open SP, Saturn-house, etc.)

     v2 ARCHETYPE DIFFERENTIATION: a second tier of DERIVED SYNTHESIS
     signals encodes HOW the user metabolizes pressure (cognitively
     vs relationally vs through achievement). Chapters that describe
     existential mechanics score AGAINST these derived signals, not
     against raw traits — so two users sharing surface behaviour
     (delay, silence, containment) but different metabolism (cognitive
     recursion vs emotional permeability) get DIFFERENT chapters.

  2. Score every chapter in the library against the signal set.
  3. Top-N candidates form the SHORTLIST. v2 adds a DIVERSITY GUARD:
     when the deterministic top spans only one existential family,
     the shortlist is augmented with the strongest competing-family
     chapter so the LLM always has a real choice.
  4. LLM picks ONE chapter from the shortlist. It MAY NOT invent.
  5. On LLM failure: deterministic top-1.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from services.chapter_library import (
    Chapter,
    FALLBACK_CHAPTER,
    get_chapter_by_id,
    get_library,
)

logger = logging.getLogger(__name__)

BUILD_MARKER = "timeline-v2-archetype-differentiation-v1"

# How many candidates the deterministic stage hands to the LLM.
SHORTLIST_SIZE = 3

# Minimum score threshold for a chapter to be eligible for the shortlist.
# A scored chapter must have at least this much signal evidence to be
# surfaced — otherwise we fall back to the recalibration chapter.
MIN_SHORTLIST_SCORE = 1.0

# Amplifier signals — negative-space evidence (something is permeable /
# absent / open). On their own they describe a baseline disposition but
# do NOT constitute active pressure. A chapter MUST also have at least
# one non-amplifier (positive / active) signal matched before it can
# enter the shortlist. This prevents charts that are simply "open" from
# being read as actively pressured.
_AMPLIFIER_SIGNALS: frozenset = frozenset({
    "hd_open_solar_plexus",
    "hd_open_throat",
})


# ===========================================================================
# Signal extraction — turn the chart + timeline into a vector of booleans.
# ===========================================================================
_HARD_ASPECTS = {"conjunction", "square", "opposition"}


def _safe_lower(s: Any) -> str:
    return str(s).strip().lower() if s is not None else ""


def _find_hard_aspect(astro: Dict[str, Any], a: str, b: str) -> bool:
    a_l, b_l = a.lower(), b.lower()
    pair = {a_l, b_l}
    for asp in (astro.get("aspects") or []):
        if not isinstance(asp, dict):
            continue
        if {_safe_lower(asp.get("body1")), _safe_lower(asp.get("body2"))} != pair:
            continue
        if _safe_lower(asp.get("type")) in _HARD_ASPECTS:
            return True
    return False


def _saturn_house(astro: Dict[str, Any]) -> Optional[int]:
    sat = (astro.get("planets") or {}).get("Saturn") or {}
    try:
        return int(sat.get("house"))
    except (TypeError, ValueError):
        return None


def _moon_house(astro: Dict[str, Any]) -> Optional[int]:
    moon = (astro.get("planets") or {}).get("Moon") or {}
    try:
        return int(moon.get("house"))
    except (TypeError, ValueError):
        return None


def _personal_planets_in_house(astro: Dict[str, Any], house: int) -> int:
    planets = astro.get("planets") or {}
    count = 0
    for p in ("Sun", "Moon", "Mercury", "Venus", "Mars"):
        pd = planets.get(p) or {}
        try:
            if int(pd.get("house")) == house:
                count += 1
        except (TypeError, ValueError):
            continue
    return count


def _has_gate(hd: Dict[str, Any], gate: int) -> bool:
    raw = hd.get("active_gates") or hd.get("all_gates") or []
    for g in raw:
        try:
            if int(g) == gate:
                return True
        except (TypeError, ValueError):
            continue
    return False


def _is_center_defined(hd: Dict[str, Any], names: Tuple[str, ...]) -> bool:
    centers = {_safe_lower(c) for c in (hd.get("defined_centers") or [])}
    return any(n.lower() in centers for n in names)


def _is_center_open(hd: Dict[str, Any], names: Tuple[str, ...]) -> bool:
    """Open = the center is NOT in defined_centers AND the HD payload
    actually contains a defined_centers list. When the HD block is
    missing/empty we have no evidence — return False rather than
    treating every center as 'open' by default. Without this guard a
    chart with no HD data would falsely fire every hd_open_* signal."""
    centers_raw = hd.get("defined_centers")
    if not isinstance(centers_raw, list) or len(centers_raw) == 0:
        return False
    centers = {_safe_lower(c) for c in centers_raw}
    return not any(n.lower() in centers for n in names)


def _timeline_theme_keywords(timeline_payload: Optional[Dict[str, Any]]) -> Set[str]:
    """Pull a flat set of lowercase keywords from the user's yearly timeline.

    We use existing timeline copy as a soft "current pressure" overlay,
    rather than recomputing transits. This keeps V1A surgical."""
    if not isinstance(timeline_payload, dict):
        return set()
    out: List[str] = []
    for field in ("yearTheme", "primaryArc"):
        v = timeline_payload.get(field)
        if isinstance(v, str):
            out.append(v)
    for phase in (timeline_payload.get("phases") or []):
        if not isinstance(phase, dict):
            continue
        for field in ("phaseName", "humanMeaning"):
            v = phase.get(field)
            if isinstance(v, str):
                out.append(v)
        for arr_field in ("whatsHappening", "whatItsAskingOfYou"):
            arr = phase.get(arr_field) or []
            for item in arr:
                if isinstance(item, str):
                    out.append(item)
    blob = " ".join(out).lower()
    keywords: Set[str] = set()
    relational_terms = (
        "communicat", "relationship", "partner", "speak", "say",
        "voice", "express", "boundary", "home", "family",
    )
    boundary_terms = (
        "boundary", "boundar", "absorb", "contain", "say no",
        "protect", "limit", "peace", "harmony",
    )
    if any(t in blob for t in relational_terms):
        keywords.add("timeline_theme_relational")
    if any(t in blob for t in boundary_terms):
        keywords.add("timeline_theme_boundary")
    return keywords


def extract_signals(
    chart: Dict[str, Any],
    *,
    timeline_payload: Optional[Dict[str, Any]] = None,
) -> Set[str]:
    """Return the set of signal IDs the chart + timeline currently fire.

    Signal IDs match the keys used in chapter_library.signal_rules.

    v2 ARCHETYPE DIFFERENTIATION: in addition to raw structural signals
    (Open SP, Saturn-house, etc.), this extractor emits DERIVED SYNTHESIS
    signals that encode existential mechanics:

      * derived_certainty_loop                — defined Ajna + (G4 or G63) + Mercury-Saturn hard
      * derived_recursive_questioning         — G63 + defined Ajna + Mercury-Saturn hard
      * derived_stabilization_through_analysis— defined Ajna + LP 7 + Mercury-Saturn hard
      * derived_proof_before_action           — defined Ajna + Mercury-Saturn + (Saturn-MC OR Mercury-Saturn applying)
      * derived_inability_to_conclude_safely  — defined Ajna + (Mercury-Neptune hard OR G63)
      * derived_mental_overcontainment        — defined Ajna + Mercury-Saturn + Open Throat
      * derived_unresolved_cognition          — Mercury-Neptune hard OR (Mercury-Saturn + Open SP)
      * derived_excessive_air_mentalization   — >=3 personal planets in air signs
      * derived_mutable_mental_overprocessing — >=3 personal planets in mutable signs

    These derived signals are the ones the new cognitive-recursion
    chapters score against — NOT raw traits — so a user with defined
    Ajna alone (no Mercury-Saturn) won't fall into a cognitive-recursion
    chapter just because they have an Ajna.
    """
    if not isinstance(chart, dict):
        return set()
    hd = chart.get("human_design") or {}
    astro = chart.get("astrology") or {}
    num = chart.get("numerology") or {}
    out: Set[str] = set()

    # =================================================================
    # RAW STRUCTURAL SIGNALS — v1A (unchanged for backwards-compat)
    # =================================================================
    if _is_center_open(hd, ("Solar Plexus", "Emotional Solar Plexus")):
        out.add("hd_open_solar_plexus")
    if _is_center_open(hd, ("Throat",)):
        out.add("hd_open_throat")
    if _is_center_defined(hd, ("Ego", "Heart", "Will")):
        out.add("hd_defined_heart")
    if _is_center_defined(hd, ("Sacral", "Splenic", "Ego", "G Center")):
        out.add("hd_defined_authority_center")
    if _has_gate(hd, 22):
        out.add("hd_channel_22")
    if _has_gate(hd, 49):
        out.add("hd_channel_49")

    sat_h = _saturn_house(astro)
    if sat_h in (3, 4, 7):
        out.add("astro_saturn_house_3_4_7")
    if sat_h in (1, 4, 7, 10):
        out.add("astro_saturn_angular")
    if _find_hard_aspect(astro, "Saturn", "Moon"):
        out.add("astro_saturn_hard_to_moon")
    if _find_hard_aspect(astro, "Saturn", "Venus"):
        out.add("astro_saturn_hard_to_venus")
    if _find_hard_aspect(astro, "Saturn", "Mercury"):
        out.add("astro_saturn_hard_to_mercury")
    if _find_hard_aspect(astro, "Saturn", "Mars"):
        out.add("astro_saturn_hard_to_mars")
    if _find_hard_aspect(astro, "Saturn", "Sun"):
        out.add("astro_saturn_hard_to_sun")
    if _find_hard_aspect(astro, "Mars", "Venus"):
        out.add("astro_mars_venus_hard")
    if _moon_house(astro) == 12:
        out.add("astro_12th_house_moon")
    if _personal_planets_in_house(astro, 10) >= 3:
        out.add("astro_10th_house_emphasis")
    if _personal_planets_in_house(astro, 4) >= 3:
        out.add("astro_4th_house_emphasis")
    out.update(_timeline_theme_keywords(timeline_payload))

    # =================================================================
    # v2 RAW SIGNALS — additional structural ground truth
    # =================================================================
    has_ajna = _is_center_defined(hd, ("Ajna",))
    has_g4   = _has_gate(hd, 4)
    has_g63  = _has_gate(hd, 63)
    if has_ajna:
        out.add("hd_defined_ajna")
    if has_g4:
        out.add("hd_gate_4")
    if has_g63:
        out.add("hd_gate_63")
    # Head-Ajna pressure: defined Head + defined Ajna creates the
    # "always thinking" / pressure-to-conclude axis.
    if _is_center_defined(hd, ("Head",)) and has_ajna:
        out.add("hd_head_ajna_pressure")

    has_merc_sat_hard = _find_hard_aspect(astro, "Mercury", "Saturn")
    has_merc_nep_hard = _find_hard_aspect(astro, "Mercury", "Neptune")
    has_merc_plu_hard = _find_hard_aspect(astro, "Mercury", "Pluto")
    if has_merc_sat_hard:
        out.add("astro_mercury_saturn_hard")
    if has_merc_nep_hard:
        out.add("astro_mercury_neptune_uncertainty")
    if has_merc_plu_hard:
        out.add("astro_mercury_pluto_compulsion")

    # Mental over-processing — sign-emphasis without going generic
    # "earth/water/fire". Air = thinking/abstraction; mutable = endless
    # re-evaluation. Each requires >=3 personal planets to fire.
    AIR_SIGNS     = {"gemini", "libra", "aquarius"}
    MUTABLE_SIGNS = {"gemini", "virgo", "sagittarius", "pisces"}
    planets = astro.get("planets") or {}
    personal = ("Sun", "Moon", "Mercury", "Venus", "Mars")
    air_count = sum(
        1 for p in personal
        if _safe_lower(planets.get(p, {}).get("sign")) in AIR_SIGNS
    )
    mutable_count = sum(
        1 for p in personal
        if _safe_lower(planets.get(p, {}).get("sign")) in MUTABLE_SIGNS
    )
    if air_count >= 3:
        out.add("astro_excessive_air_mentalization")
    if mutable_count >= 3:
        out.add("astro_mutable_mental_overprocessing")

    # Numerology Life Path 7 — the introspective / verification path.
    lp_n: Optional[int] = None
    core_num = num.get("core") or {}
    lp_block = core_num.get("life_path") or num.get("life_path") or {}
    try:
        lp_n = int(lp_block.get("number"))
    except (TypeError, ValueError):
        lp_n = None
    if lp_n == 7:
        out.add("num_life_path_7")

    # =================================================================
    # v2 DERIVED SYNTHESIS SIGNALS — existential mechanics
    # These are the load-bearing signals that the new cognitive-
    # recursion chapters score AGAINST. They encode HOW pressure is
    # metabolized, not WHICH traits exist.
    # =================================================================
    if has_ajna and (has_g4 or has_g63) and has_merc_sat_hard:
        out.add("derived_certainty_loop")

    if has_ajna and has_g63 and has_merc_sat_hard:
        out.add("derived_recursive_questioning")

    if has_ajna and lp_n == 7 and has_merc_sat_hard:
        out.add("derived_stabilization_through_analysis")

    # proof_before_action: Ajna defined + Mercury-Saturn + structural
    # ground (Saturn-MC hard OR Saturn-Sun hard — additional weight
    # behind the proof requirement).
    if has_ajna and has_merc_sat_hard and (
        _find_hard_aspect(astro, "Saturn", "MC")
        or _find_hard_aspect(astro, "Saturn", "Sun")
    ):
        out.add("derived_proof_before_action")

    # inability_to_conclude_safely: Ajna + (Merc-Neptune hard OR G63).
    # G63 alone with Ajna creates "every answer triggers a new question";
    # Merc-Neptune adds dissolution / unfinishability.
    if has_ajna and (has_merc_nep_hard or has_g63):
        out.add("derived_inability_to_conclude_safely")

    # mental_overcontainment: defined Ajna + Mercury-Saturn + Open Throat.
    # The thinking is structured (Ajna+MercSat) but can't reach speech
    # (Open Throat).
    if has_ajna and has_merc_sat_hard and "hd_open_throat" in out:
        out.add("derived_mental_overcontainment")

    # unresolved_cognition: cognitive uncertainty entering the system.
    if has_merc_nep_hard or (has_merc_sat_hard and "hd_open_solar_plexus" in out):
        out.add("derived_unresolved_cognition")

    return out


# ===========================================================================
# Scoring + shortlist
# ===========================================================================
def score_chapter(chapter: Chapter, signals: Set[str]) -> Tuple[float, List[str]]:
    """Return (total_score, matched_signal_ids) for a chapter."""
    total = 0.0
    matched: List[str] = []
    for sig_id, rule in (chapter.get("signal_rules") or {}).items():
        if sig_id in signals:
            total += float(rule.get("weight", 1.0))
            matched.append(sig_id)
    return total, matched


def build_shortlist(
    signals: Set[str],
    *,
    size: int = SHORTLIST_SIZE,
    min_score: float = MIN_SHORTLIST_SCORE,
) -> List[Dict[str, Any]]:
    """Rank the library by score against the signal vector.

    A chapter is eligible for the shortlist only when:
      * its score >= min_score, AND
      * it has at least one non-amplifier (active / positive) signal
        matched. Amplifier-only matches describe a baseline disposition,
        not an active phase.

    v2 DIVERSITY GUARD: when the top-N deterministic candidates all come
    from a single existential_family (e.g. all "emotional_permeability"),
    the strongest eligible chapter from a DIFFERENT family is promoted
    into the shortlist by displacing the lowest same-family entry. This
    prevents the LLM from being handed a single-axis shortlist when a
    cross-axis competitor is actually scoring above threshold — exactly
    the failure mode that collapsed certainty-pattern users into
    permeability chapters in QA.
    """
    scored: List[Dict[str, Any]] = []
    for ch in get_library():
        score, matched = score_chapter(ch, signals)
        if score < min_score:
            continue
        positive_matched = [m for m in matched if m not in _AMPLIFIER_SIGNALS]
        if not positive_matched:
            continue
        scored.append({
            "chapter_id":         ch["chapter_id"],
            "title":              ch["title"],
            "existential_family": ch.get("existential_family"),
            "score":              round(score, 3),
            "matched_signals":    matched,
        })
    scored.sort(key=lambda x: (-x["score"], x["chapter_id"]))
    head = scored[:size]

    # Diversity guard — only meaningful when (a) there's a head, (b) we
    # have remaining candidates outside the head, and (c) the head is
    # mono-family (every entry shares the same existential_family).
    if head and len(scored) > len(head):
        head_families = {c.get("existential_family") for c in head}
        if len(head_families) == 1:
            head_family = next(iter(head_families))
            # Find the strongest competitor from a different family in
            # the remainder. Untagged chapters (None family) are NOT
            # treated as competitors — they participate purely on score.
            promoted: Optional[Dict[str, Any]] = None
            for cand in scored[len(head):]:
                fam = cand.get("existential_family")
                if fam and fam != head_family:
                    promoted = cand
                    break
            if promoted is not None:
                # Displace the LOWEST-scoring head entry so the
                # promoted competitor enters at the bottom of the
                # shortlist (deterministic top-1 is still preserved).
                head = head[:-1] + [promoted]
    return head


# ===========================================================================
# LLM-assisted selection (Emergent LLM key)
# ===========================================================================
SELECT_SYSTEM_PROMPT = """You are the Phase Governor for a phase-recognition product called Mirror.
Your job is to pick the SINGLE most resonant Governing Life Chapter for a user, given:
  (a) a deterministic shortlist of candidate chapters (max 3 — you may NOT invent new chapters)
  (b) a brief snapshot of the user's lifeline / current state

ONLY pick from the shortlist. Do NOT add narration, do NOT explain in prose.
Respond with strict JSON ONLY:
{ "chapter_id": "<one of the shortlist chapter_ids>",
  "reason":     "<one short sentence (<= 20 words) describing WHY this resonates more than the others>" }

Tie-break preference (when scores are close):
  * the chapter that aligns with the user's most recent lifeline entries
  * the chapter whose arc_type matches recent journal themes
  * if you truly cannot decide, return the FIRST item in the shortlist."""


def _make_user_context_blob(
    *,
    user_doc: Optional[Dict[str, Any]],
    lifeline_events: Optional[List[Dict[str, Any]]] = None,
    journal_recent: Optional[List[Dict[str, Any]]] = None,
) -> str:
    parts: List[str] = []
    if user_doc:
        name = user_doc.get("name") or user_doc.get("email") or "user"
        parts.append(f"User: {name}")
    if lifeline_events:
        # Just the last 5 entry summaries.
        lines: List[str] = []
        for ev in lifeline_events[-5:]:
            if not isinstance(ev, dict):
                continue
            t = ev.get("title") or ev.get("name") or ev.get("description") or ""
            d = ev.get("date") or ev.get("when") or ""
            if t:
                lines.append(f"- {t}{' (' + str(d) + ')' if d else ''}")
        if lines:
            parts.append("Recent lifeline:\n" + "\n".join(lines))
    if journal_recent:
        lines = []
        for j in journal_recent[-3:]:
            if not isinstance(j, dict):
                continue
            txt = j.get("content") or j.get("text") or ""
            if isinstance(txt, str) and txt.strip():
                lines.append(f"- {txt.strip()[:140]}")
        if lines:
            parts.append("Recent journal snippets:\n" + "\n".join(lines))
    if not parts:
        parts.append("No additional lifeline context available.")
    return "\n\n".join(parts)


async def _select_via_llm(
    shortlist: List[Dict[str, Any]],
    user_context: str,
) -> Optional[Tuple[str, str]]:
    """Returns (chapter_id, reason) or None if LLM fails."""
    if not shortlist:
        return None
    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key:
        logger.info("[PhaseGovernor] EMERGENT_LLM_KEY missing — skipping LLM selection")
        return None
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage  # type: ignore
    except Exception as e:
        logger.warning(f"[PhaseGovernor] emergentintegrations unavailable: {e}")
        return None

    shortlist_payload = [
        {
            "chapter_id":      c["chapter_id"],
            "title":           c["title"],
            "score":           c["score"],
            "matched_signals": c["matched_signals"],
        }
        for c in shortlist
    ]
    user_msg_text = (
        "SHORTLIST (you must pick chapter_id from one of these):\n"
        + json.dumps(shortlist_payload, indent=2)
        + "\n\nUSER CONTEXT:\n"
        + user_context
        + "\n\nReturn JSON only."
    )
    try:
        chat = LlmChat(
            api_key=key,
            session_id=f"phase_governor_{datetime.now(timezone.utc).timestamp()}",
            system_message=SELECT_SYSTEM_PROMPT,
        )
        chat.with_model("openai", "gpt-4o-mini")
        raw = await chat.send_message(UserMessage(text=user_msg_text))
        text = raw if isinstance(raw, str) else str(raw)
        # Strip code fences if present
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
        # Find first { and last }
        i, j = text.find("{"), text.rfind("}")
        if i == -1 or j == -1 or j <= i:
            logger.warning("[PhaseGovernor] LLM returned non-JSON; falling back")
            return None
        parsed = json.loads(text[i:j + 1])
        chapter_id = parsed.get("chapter_id")
        reason = parsed.get("reason") or ""
        allowed = {c["chapter_id"] for c in shortlist}
        if chapter_id not in allowed:
            logger.warning(
                f"[PhaseGovernor] LLM returned chapter_id={chapter_id!r} "
                f"not in shortlist — falling back"
            )
            return None
        return (chapter_id, str(reason)[:240])
    except Exception as e:
        logger.exception(f"[PhaseGovernor] LLM selection failed: {e}")
        return None


# ===========================================================================
# Public resolver
# ===========================================================================
async def resolve_governing_chapter(
    db,
    user_id: str,
    *,
    force_refresh: bool = False,
) -> Optional[Dict[str, Any]]:
    """Top-level entry. Returns a payload ready for the frontend.

    Cache shape (db.governing_chapter_cache):
      { user_id, payload, build_marker, computed_at }

    TTL: 7 days. Force refresh skips the cache.
    """
    if not user_id:
        return None

    cache_coll = db.governing_chapter_cache

    # --- Cache lookup
    if not force_refresh:
        cached = await cache_coll.find_one({"user_id": user_id})
        if cached and cached.get("build_marker") == BUILD_MARKER:
            computed_at = cached.get("computed_at")
            if isinstance(computed_at, datetime):
                age = (datetime.now(timezone.utc) - computed_at.replace(tzinfo=timezone.utc)).total_seconds()
                if age < 7 * 24 * 3600:
                    payload = cached.get("payload") or {}
                    # Force the flag — the stored payload was written with
                    # from_cache=False (fresh compute), so setdefault is a
                    # no-op. Explicit assignment is required.
                    payload["from_cache"] = True
                    return payload

    # --- Chart fetch
    chart = await db.charts.find_one({"user_id": user_id})
    if chart is None:
        return None

    # --- Optional yearly timeline overlay (best-effort)
    timeline_payload: Optional[Dict[str, Any]] = None
    try:
        from services.astrology_timeline_cache import (  # type: ignore
            get_or_build_astrology_timeline,
        )
        timeline_payload = await get_or_build_astrology_timeline(
            db, user_id, chart_doc=chart, force_refresh=False,
        )
    except Exception as e:
        logger.debug(f"[PhaseGovernor] timeline overlay unavailable: {e}")

    # --- Signals + shortlist
    signals = extract_signals(chart, timeline_payload=timeline_payload)
    shortlist = build_shortlist(signals)

    selection_mode = "deterministic_top1"
    selection_reason: Optional[str] = None

    if not shortlist:
        chosen = FALLBACK_CHAPTER
        selection_mode = "fallback_no_score"
    else:
        # --- LLM selects from shortlist
        user_doc = await db.users.find_one({"_id": chart.get("user_id")}) if chart.get("user_id") else None
        # ObjectId lookup fallback
        if user_doc is None:
            try:
                from bson import ObjectId
                if ObjectId.is_valid(user_id):
                    user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
            except Exception:
                user_doc = None
        # Lifeline events (best-effort)
        lifeline_events: List[Dict[str, Any]] = []
        try:
            cursor = db.lifeline_events.find({"user_id": user_id}).sort("date", -1).limit(8)
            lifeline_events = await cursor.to_list(length=8)
        except Exception:
            pass
        # Journal (best-effort)
        journal_recent: List[Dict[str, Any]] = []
        try:
            cursor = db.journal_entries.find({"user_id": user_id}).sort("created_at", -1).limit(3)
            journal_recent = await cursor.to_list(length=3)
        except Exception:
            pass

        user_context = _make_user_context_blob(
            user_doc=user_doc,
            lifeline_events=lifeline_events,
            journal_recent=journal_recent,
        )

        llm_pick = await _select_via_llm(shortlist, user_context)
        if llm_pick is not None:
            chosen_id, selection_reason = llm_pick
            chosen = get_chapter_by_id(chosen_id) or FALLBACK_CHAPTER
            selection_mode = "llm_from_shortlist"
        else:
            chosen = get_chapter_by_id(shortlist[0]["chapter_id"]) or FALLBACK_CHAPTER
            selection_mode = "deterministic_top1"

    # --- Build the response payload
    score_for_chosen: float = 0.0
    matched_for_chosen: List[str] = []
    for c in shortlist:
        if c["chapter_id"] == chosen.get("chapter_id"):
            score_for_chosen = c["score"]
            matched_for_chosen = c["matched_signals"]
            break

    payload: Dict[str, Any] = {
        "build_marker":          BUILD_MARKER,
        "computed_at_iso":       datetime.now(timezone.utc).isoformat(),
        "selection_mode":        selection_mode,
        "selection_reason":      selection_reason,
        "chapter": {
            "chapter_id":   chosen.get("chapter_id"),
            "title":        chosen.get("title"),
            "subtitle":     chosen.get("subtitle"),
            "arc_type":     chosen.get("arc_type"),
            "body_visible": chosen.get("body_visible"),
        },
        "proof": {
            "proof_summary":   chosen.get("proof_summary"),
            "matched_signals": matched_for_chosen,
            "score":           score_for_chosen,
            # NEVER user-facing; only for the proof drawer's
            # "Why this is the chapter we see" technical section.
            "internal_topics": chosen.get("proof_internal_topics", []),
        },
        "shortlist":            shortlist,
        "signals_extracted":    sorted(signals),
        "from_cache":           False,
    }

    # --- Write cache
    try:
        await cache_coll.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id":       user_id,
                    "payload":       payload,
                    "build_marker":  BUILD_MARKER,
                    "computed_at":   datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
    except Exception as e:
        logger.warning(f"[PhaseGovernor] cache write failed: {e}")

    return payload
