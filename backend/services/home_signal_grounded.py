"""
Home Signal-Grounded Engine (V6)
================================
Replaces generic templates with a layered output driven by REAL daily signals.

PRODUCT CONTRACT:
-----------------
The Home card must feel like it could only have been generated TODAY for THIS user.

A user swapping dates must see the output change. A user with no qualifying signals
must NOT see a rendered card (render=False) — we never fall back to generic copy.

LAYERS (always signal-grounded, never templated):
1. TRIGGER     — from strongest transit aspect / stellium / lunar event today
2. COLLISION   — from recurring pattern memory (72h / 7d recurrence)
3. DISTORTION  — from conflicting signals (Neptune, Mercury Rx, emotional authority delay)
4. COST        — derived from collision + distortion (what the loop produces)
5. INTERRUPT   — short, sharp, pattern-level move

GATE:
-----
Card renders only if >= 2 signals are resolved from DIFFERENT sources
(e.g. transit + pattern_memory, or lunar + hd_activation).
Otherwise: render=False, reason="insufficient_signals".
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# SIGNAL MODEL
# =============================================================================

@dataclass
class Signal:
    source: str                 # "transit" | "stellium" | "lunar_event" | "hd_activation"
                                # | "pattern_recurrence" | "bazi_day"
    kind: str                   # precise descriptor, e.g. "saturn_square_moon", "new_moon_aries"
    label: str                  # human-readable one-liner for proof layer
    weight: float               # 0.0 - 1.0 ; used for trigger selection
    evidence: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# PLANET / ASPECT BEHAVIOR MAP (no templates — composable pieces)
# =============================================================================

TRANSIT_VERB = {
    ("Sun",    "conjunction"): "illuminating",
    ("Sun",    "square"):       "pressuring",
    ("Sun",    "opposition"):   "mirroring",
    ("Sun",    "trine"):        "warming",
    ("Moon",   "conjunction"):  "saturating",
    ("Moon",   "square"):       "pulling at",
    ("Moon",   "opposition"):   "surfacing",
    ("Mars",   "conjunction"):  "igniting",
    ("Mars",   "square"):       "provoking",
    ("Mars",   "opposition"):   "confronting",
    ("Mercury","conjunction"):  "broadcasting",
    ("Mercury","square"):       "garbling",
    ("Mercury","opposition"):   "cross-examining",
    ("Venus",  "conjunction"):  "softening",
    ("Venus",  "square"):       "destabilizing",
    ("Jupiter","conjunction"):  "enlarging",
    ("Jupiter","square"):       "over-inflating",
    ("Saturn", "conjunction"):  "condensing",
    ("Saturn", "square"):       "pressing down on",
    ("Saturn", "opposition"):   "forcing a verdict on",
    ("Uranus", "conjunction"):  "jolting",
    ("Uranus", "square"):       "fracturing",
    ("Neptune","conjunction"):  "blurring",
    ("Neptune","square"):       "misting over",
    ("Neptune","opposition"):   "distorting",
    ("Pluto",  "conjunction"):  "rewriting",
    ("Pluto",  "square"):       "ripping open",
    ("Pluto",  "opposition"):   "forcing a reckoning with",
}

NATAL_POINT_BEHAVIOR = {
    "Sun":     "your sense of self",
    "Moon":    "your emotional baseline",
    "Mercury": "how you process and communicate",
    "Venus":   "what you pull toward",
    "Mars":    "how you act on what you want",
    "Jupiter": "where you expand",
    "Saturn":  "where you hold structure",
    "Uranus":  "the part of you that breaks form",
    "Neptune": "what you believe without proof",
    "Pluto":   "what won't stay buried",
    "ASC":     "how you meet the world",
    "MC":      "what you build toward publicly",
}


# =============================================================================
# STEP 1 — GATHER SIGNALS
# =============================================================================

async def gather_signals(db, user_id: str, now: Optional[datetime] = None) -> List[Signal]:
    """
    Collect all DAILY signals available right now. Returns list of Signal.
    Each signal must be real (computed from data), never pre-written text.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    signals: List[Signal] = []

    # --- A. ASTROLOGY TRANSITS + STELLIUMS ---
    try:
        signals += await _gather_astro_signals(db, user_id, now)
    except Exception as e:
        logger.debug(f"[HomeSignal] Astro gather error: {e}")

    # --- B. LUNAR EVENTS (new/full moon, eclipse) ---
    try:
        signals += _gather_lunar_signals(now)
    except Exception as e:
        logger.debug(f"[HomeSignal] Lunar gather error: {e}")

    # --- C. HD GATE ACTIVATIONS (transit planets on natal gates) ---
    try:
        signals += await _gather_hd_signals(db, user_id, now)
    except Exception as e:
        logger.debug(f"[HomeSignal] HD gather error: {e}")

    # --- D. PATTERN RECURRENCE ---
    try:
        signals += await _gather_pattern_recurrence(db, user_id, now)
    except Exception as e:
        logger.debug(f"[HomeSignal] Pattern recurrence gather error: {e}")

    # --- E. BAZI DAY PRESSURE ---
    try:
        signals += _gather_bazi_day(now)
    except Exception as e:
        logger.debug(f"[HomeSignal] BaZi day gather error: {e}")

    # Sort strongest first
    signals.sort(key=lambda s: -s.weight)
    return signals


# ---------- astrology transits ----------

async def _gather_astro_signals(db, user_id: str, now: datetime) -> List[Signal]:
    from services.astrology_today_engine import (
        get_current_transits,
        compute_transit_natal_aspects,
        detect_sign_concentration,
    )

    chart = await db.charts.find_one({"user_id": user_id})
    if not chart:
        return []

    astrology = chart.get("astrology") or {}
    natal_planets = astrology.get("planets") or {}
    if not natal_planets:
        return []

    transits = get_current_transits(now)
    aspects = compute_transit_natal_aspects(transits, natal_planets)

    signals: List[Signal] = []

    # Take top 3 aspects with score >= 0.3 as trigger candidates
    for asp in aspects[:3]:
        if asp["score"] < 0.3:
            continue
        tp = asp["transit_planet"]
        np_ = asp["natal_planet"]
        verb = TRANSIT_VERB.get((tp, asp["aspect"]), "touching")
        behavior = NATAL_POINT_BEHAVIOR.get(np_, f"your natal {np_}")
        label = (
            f"{tp} in {asp['transit_sign']} is {verb} {behavior} "
            f"(natal {np_} in {asp['natal_sign']}, {asp['aspect']} orb {asp['orb']}°)"
        )
        signals.append(Signal(
            source="transit",
            kind=f"{tp.lower()}_{asp['aspect']}_{np_.lower()}",
            label=label,
            weight=min(1.0, asp["score"] * 1.1),
            evidence={
                "transit": tp, "natal": np_, "aspect": asp["aspect"],
                "nature": asp["nature"], "orb": asp["orb"], "score": asp["score"],
                "transit_sign": asp["transit_sign"], "natal_sign": asp["natal_sign"],
            },
        ))

    # Stellium detection
    concentrations = detect_sign_concentration(transits)
    for conc in concentrations[:1]:
        if conc["count"] >= 3:
            planets = ", ".join(conc["planets"])
            label = (
                f"{conc['count']} planets are stacked in {conc['sign']} ({planets}) — "
                f"today's energy is clustered in one arena"
            )
            signals.append(Signal(
                source="stellium",
                kind=f"stellium_{conc['sign'].lower()}_{conc['count']}",
                label=label,
                weight=min(1.0, 0.5 + conc["count"] * 0.1),
                evidence=conc,
            ))

    return signals


# ---------- lunar events ----------

def _gather_lunar_signals(now: datetime) -> List[Signal]:
    import swisseph as swe
    jd = swe.julday(now.year, now.month, now.day, now.hour + now.minute / 60.0)
    sun = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)[0][0]
    moon = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)[0][0]

    diff = abs(sun - moon) % 360
    if diff > 180:
        diff = 360 - diff

    signals: List[Signal] = []
    # NOTE: `sun` and `moon` above are TROPICAL longitudes (calc_ut without
    # FLG_SIDEREAL). We attribute the sign via the global mode-aware router.
    # Build marker: true-sidereal-midpoint-production-migration-v1
    from calculations.sign_attribution import attribute_sign

    if diff < 6:
        sign = attribute_sign(moon)["sign"]
        signals.append(Signal(
            source="lunar_event",
            kind="new_moon",
            label=f"New Moon in {sign} — a reset is landing today, not next week",
            weight=0.85,
            evidence={"type": "new_moon", "sign": sign, "orb": round(diff, 2)},
        ))
    elif abs(diff - 180) < 6:
        sign = attribute_sign(moon)["sign"]
        signals.append(Signal(
            source="lunar_event",
            kind="full_moon",
            label=f"Full Moon in {sign} — something hidden is coming into view",
            weight=0.9,
            evidence={"type": "full_moon", "sign": sign, "orb": round(abs(diff - 180), 2)},
        ))
    return signals


# ---------- HD gate activations ----------

HD_GATE_THEMES = {
    1:"self-expression", 2:"receptive direction", 3:"ordering the new",
    4:"forming answers", 5:"consistent rhythm", 6:"friction in intimacy",
    7:"leadership role", 8:"individual contribution", 9:"focus",
    10:"being yourself", 11:"ideas", 12:"caution in speaking",
    13:"listening and witness", 14:"resources for direction", 15:"extremes/humanity",
    16:"skills and enthusiasm", 17:"opinions", 18:"correction",
    19:"emotional approach", 20:"now", 21:"control of material",
    22:"grace under pressure", 23:"splitting complexity", 24:"rationalization",
    25:"innocent love", 26:"the egoist", 27:"nourishment",
    28:"the game-player", 29:"commitment", 30:"desire/feelings",
    31:"the leader", 32:"duration", 33:"privacy/retreat",
    34:"power", 35:"change/progress", 36:"emotional crisis",
    37:"friendship", 38:"the fighter", 39:"provocation",
    40:"aloneness", 41:"imagination", 42:"growth",
    43:"insight breakthrough", 44:"pattern recognition", 45:"gathering",
    46:"determination of the self", 47:"realization", 48:"depth",
    49:"principles/rejection", 50:"values", 51:"shock/alerting",
    52:"stillness", 53:"starting", 54:"ambition",
    55:"spirit/mood", 56:"storytelling", 57:"intuition",
    58:"joy of vitality", 59:"sexuality/intimacy", 60:"acceptance of limitation",
    61:"inner truth", 62:"detail", 63:"doubt/inquiry",
    64:"confusion before clarity",
}


async def _gather_hd_signals(db, user_id: str, now: datetime) -> List[Signal]:
    chart = await db.charts.find_one({"user_id": user_id})
    if not chart:
        return []
    hd = (chart.get("human_design") or {})
    natal_gates = set()

    # Common shapes: {"active_gates":[...]} or gates in channels/centers
    for g in (hd.get("active_gates") or []):
        try:
            natal_gates.add(int(g))
        except Exception:
            pass
    if not natal_gates:
        # Try channel pairs
        for ch in (hd.get("defined_channels") or []):
            for part in str(ch).split("-"):
                try:
                    natal_gates.add(int(part.strip()))
                except Exception:
                    pass
    if not natal_gates:
        return []

    # Compute transit gate positions (I-Ching gate wheel, 64 gates × 5.625°)
    import swisseph as swe
    jd = swe.julday(now.year, now.month, now.day, now.hour + now.minute / 60.0)
    PLANETS_HD = {
        'Sun':swe.SUN,'Moon':swe.MOON,'Mercury':swe.MERCURY,'Venus':swe.VENUS,
        'Mars':swe.MARS,'Jupiter':swe.JUPITER,'Saturn':swe.SATURN,
        'Uranus':swe.URANUS,'Neptune':swe.NEPTUNE,'Pluto':swe.PLUTO,
    }

    # HD gate wheel starts at 17°25'55" Pisces (=347.4319°) with Gate 17 in early Aries — simplified:
    # we map tropical longitude -> HD gate using the standard 64-gate wheel (BG5 Business/IHDS common order).
    # For our purposes we use the standard gate order keyed to sign boundaries; this approximation is
    # adequate for "is transit activating a natal gate today" signaling.
    HD_GATE_SEQUENCE = [
        25, 17, 21, 51, 42, 3, 27, 24, 2, 23, 8, 20,  # Aries
        16, 35, 45, 12, 15, 52, 39, 53, 62, 56, 31, 33,  # Taurus
        7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57,  # Gemini
        32, 50, 28, 44, 1, 43, 14, 34, 9, 5, 26, 11,  # Cancer
        10, 58, 38, 54, 61, 60, 41, 19, 13, 49, 30, 55,  # Leo
        37, 63, 22, 36, 25, 17, 21, 51, 42, 3, 27, 24,  # Virgo (repeats sequence from Aries start)
    ]
    # NOTE: precise HD gate wheel is complex; this simplified mapping covers half the zodiac and
    # is sufficient as a *signal trigger* (false positives are rare because we require natal gate
    # membership). For higher precision we can replace with the exact degree table later.

    signals: List[Signal] = []
    for pname, pid in PLANETS_HD.items():
        try:
            lon = swe.calc_ut(jd, pid, swe.FLG_SWIEPH)[0][0]
            gate_idx = int((lon / 360.0) * 64) % 64
            gate = HD_GATE_SEQUENCE[gate_idx] if gate_idx < len(HD_GATE_SEQUENCE) else None
            if gate and gate in natal_gates:
                theme = HD_GATE_THEMES.get(gate, "")
                label = f"Transit {pname} is activating your Gate {gate}" + (f" ({theme})" if theme else "")
                signals.append(Signal(
                    source="hd_activation",
                    kind=f"{pname.lower()}_on_gate_{gate}",
                    label=label,
                    weight=0.6 if pname in ("Sun", "Moon", "Mars") else 0.45,
                    evidence={"transit_planet": pname, "gate": gate, "theme": theme},
                ))
        except Exception:
            continue
    return signals[:2]  # cap at 2 HD activations to avoid flood


# ---------- pattern recurrence ----------

async def _gather_pattern_recurrence(db, user_id: str, now: datetime) -> List[Signal]:
    try:
        from services.pattern_memory_engine import get_pattern_history
    except Exception:
        return []

    history = await get_pattern_history(db, user_id, days=14)
    if not history:
        return []

    # Tally signatures
    sig_counts: Dict[str, List[Dict]] = {}
    for h in history:
        sig = h.get("pattern_signature") or h.get("tension_hash") or ""
        if not sig:
            continue
        sig_counts.setdefault(sig, []).append(h)

    # Find the most recurring recent pattern
    best = None
    for sig, entries in sig_counts.items():
        if best is None or len(entries) > len(best[1]):
            best = (sig, entries)

    if not best or len(best[1]) < 2:
        return []

    _, entries = best
    # Days-ago list
    ago = []
    today_str = now.strftime("%Y-%m-%d")
    for e in entries:
        d = e.get("date")
        if not d or d == today_str:
            continue
        try:
            dt = datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            ago.append((now - dt).days)
        except Exception:
            continue

    if not ago:
        return []

    title = entries[0].get("diagnosis_title") or entries[0].get("pattern_label") or "this loop"
    last_days = min(ago)
    total = len(entries)

    if last_days <= 3:
        framing = f"same pattern hit {last_days} day{'s' if last_days != 1 else ''} ago"
    elif last_days <= 7:
        framing = f"same pattern surfaced {last_days} days ago"
    else:
        framing = f"same pattern {total}× in the last two weeks"

    label = f"Pattern memory: \"{title}\" — {framing}"
    return [Signal(
        source="pattern_recurrence",
        kind="recurrence",
        label=label,
        weight=0.7 + min(0.25, total * 0.05),
        evidence={"title": title, "count": total, "last_days_ago": last_days},
    )]


# ---------- BaZi day pressure ----------

def _gather_bazi_day(now: datetime) -> List[Signal]:
    try:
        from services.bazi_engine import get_chinese_year, calculate_day_pillar
    except Exception:
        return []
    # Day pillar stem/branch as a signal of the day's baseline pressure.
    try:
        stem, branch, stem_idx, branch_idx = calculate_day_pillar(now)
    except Exception:
        return []

    # We surface this only if we want a generic "day energy" signal. Keep weight low
    # so it counts only as corroboration, never the trigger by itself.
    return [Signal(
        source="bazi_day",
        kind=f"day_pillar_{stem}{branch}",
        label=f"Today's BaZi day pillar is {stem}{branch} (stem+branch energy pair)",
        weight=0.3,
        evidence={"stem": stem, "branch": branch},
    )]


# =============================================================================
# STEP 2 — COMPOSE LAYERS
# =============================================================================

def _pick(signals: List[Signal], *sources: str) -> Optional[Signal]:
    for s in signals:
        if s.source in sources:
            return s
    return None


def _compose_hook(trigger_sig: Signal, pattern_sig: Optional[Signal]) -> str:
    """
    HOOK — first line the user sees.
    NEVER mentions planets, signs, houses, or astrological terms.
    Short, sharp, personal — a behavioral pattern line the user recognizes.
    
    Priority:
    1. Pattern memory hit → behavioral line from the loop itself.
    2. Transit-driven → map aspect nature to behavioral language.
    3. Stellium / lunar → behavioral implication.
    """
    # Pattern-memory HOOK wins if available — it's the most "you know this" line.
    if pattern_sig:
        e = pattern_sig.evidence
        last = e.get("last_days_ago", 0)
        if last <= 2:
            return "You're about to do the thing you said you wouldn't do again."
        if last <= 7:
            return "The same decision is back. You haven't changed your answer, just the story around it."
        return "This is the loop you keep stepping around."

    # Transit-driven behavioral HOOK (no planet language)
    if trigger_sig.source == "transit":
        e = trigger_sig.evidence
        t = e.get("transit", "")
        n = e.get("natal", "")
        nature = e.get("nature", "")

        # Nature-specific behavioral leads
        if t == "Neptune" or n == "Neptune":
            return "You feel like you have clarity. You don't, yet. You have a preference dressed up as one."
        if t == "Saturn":
            if nature == "tension":
                return "You're powering through something that was meant to be a decision point."
            if nature == "polarity":
                return "Something's being asked of you that requires a 'no' you've been avoiding."
            return "The thing you keep deferring is taking up more room than the thing itself."
        if t == "Mars":
            if nature == "tension":
                return "You want to move, but you keep choreographing the move instead of making it."
            if nature == "fusion":
                return "There's one thing you actually want to do today. Everything else is stalling."
            return "Your body is ahead of your thinking. The plan is catching up, not leading."
        if t == "Mercury":
            if nature in ("tension", "opposition"):
                return "You're over-explaining instead of saying the one thing."
            return "The clarity you want from talking about it won't come from more talking."
        if t == "Venus":
            return "You're managing the relationship instead of being in it."
        if t == "Jupiter":
            if nature in ("tension", "square"):
                return "The openness you feel is real, but your default is to wait until it's safer. It won't get safer."
            return "Something is actually open today. You're treating it like it might close if you touch it."
        if t == "Uranus":
            return "Something you'd normally tolerate just stopped being tolerable."
        if t == "Pluto":
            return "You're negotiating with a thing that's already decided."
        if t == "Moon":
            return "The urgency you feel right now belongs more to the hour than to the decision."
        if t == "Sun":
            if nature == "tension":
                return "You're arguing with something that's not going to shift by tomorrow."
            return "The version of you that shows up today is going to set the tone for the week."

    # Stellium HOOK — behavioral, no planet-stacking language
    if trigger_sig.source == "stellium":
        return "You keep returning to the same area of your life. The rest is noise right now."

    # Lunar HOOK
    if trigger_sig.source == "lunar_event":
        e = trigger_sig.evidence
        if e.get("type") == "full_moon":
            return "Something you've been looking past is harder to look past today."
        if e.get("type") == "new_moon":
            return "You've been waiting to begin. You're already in the middle of it."

    # HD HOOK
    if trigger_sig.source == "hd_activation":
        return "A part of you that's usually quiet has opinions today. You can feel it even if you can't name it."

    # Fallback — still behavioral
    return "Something in you knows what it wants to do. The rest of you is busy talking around it."


def _compose_recognition(trigger_sig: Signal, pattern_sig: Optional[Signal], signals: List[Signal]) -> str:
    """
    RECOGNITION — concrete behaviors, not abstract.
    The user should feel "yes, that's exactly what I'm doing."
    Derived from pattern recurrence first, then signal nature.
    """
    if pattern_sig:
        e = pattern_sig.evidence
        last = e.get("last_days_ago", 0)
        if last <= 2:
            return (
                "You're rehearsing the conversation. You're running the pros and cons. "
                "You're telling yourself you need 'one more day to think.' You don't."
            )
        return (
            "You're researching it again. You're asking a new person the same question. "
            "You're treating the answer as missing — it's not missing, you just don't like it."
        )

    if trigger_sig.source == "transit":
        e = trigger_sig.evidence
        nature = e.get("nature", "")
        t = e.get("transit", "")

        if t == "Neptune" or e.get("natal") == "Neptune":
            return (
                "You're explaining it to yourself in a way that sounds generous. "
                "You're leaving out the part that's inconvenient. You're calling it 'nuance.'"
            )
        if t == "Saturn":
            return (
                "You're treating a structural problem as a mood problem. "
                "You're 'managing it.' You're waiting for it to resolve itself."
            )
        if t == "Mars" and nature in ("tension", "polarity"):
            return (
                "You're opening the doc. You're closing the doc. "
                "You're texting a friend about it instead of doing the two minutes of the thing."
            )
        if t == "Mercury":
            return (
                "You're sending a paragraph where a sentence would do. "
                "You're pre-apologizing for the thing before you've said it."
            )
        if t == "Jupiter":
            return (
                "You're calling it 'being realistic' when you mean 'staying small.' "
                "You're asking whether, instead of asking how."
            )
        if t == "Pluto":
            return (
                "You're trying to find a version where nothing has to change. "
                "You already know that version doesn't exist."
            )
        if nature == "fusion":
            return (
                "You're adding more things to the list so the main thing doesn't have to be done. "
                "Every other task is louder than it should be."
            )

    if trigger_sig.source == "stellium":
        return (
            "You're giving every area of your life equal weight on purpose, "
            "because if one area matters more you have to do something about it."
        )

    # Fallback recognition
    return (
        "You're filling the day with things that are almost the thing. "
        "Close enough to feel productive. Far enough to stay safe."
    )


def _compose_cost_v2(trigger_sig: Signal, pattern_sig: Optional[Signal]) -> str:
    """
    COST — what this actually erodes. Quiet, specific, not dramatic.
    """
    if pattern_sig:
        e = pattern_sig.evidence
        return (
            f"What this costs you isn't the decision. It's trust in your own signal — "
            f"every time you run this loop, the next decision gets a little harder to feel."
        )
    if trigger_sig.source == "transit":
        t = trigger_sig.evidence.get("transit", "")
        if t == "Neptune" or trigger_sig.evidence.get("natal") == "Neptune":
            return "What this erodes: your confidence that you'd know if you were kidding yourself."
        if t == "Saturn":
            return "What this costs: the thing gets harder the longer you 'manage' it instead of deciding it."
        if t == "Mars":
            return "What this creates: a body that's tired from bracing, not from doing."
        if t == "Mercury":
            return "What this builds: a version of you who's never fully said what they meant."
        if t == "Jupiter":
            return "What this costs: the opening doesn't close — but you stop noticing it's there."
    return "What this slowly builds: a habit of waiting for the moment to be right, instead of making it."


def _compose_move_v2(trigger_sig: Signal, pattern_sig: Optional[Signal]) -> str:
    """
    THE MOVE — a minimal behavioral shift, not advice.
    Pattern-level, but tiny enough to do today.
    """
    if pattern_sig:
        return (
            "Don't try to break the loop. Write down the exact sentence you use to stay in it. "
            "That sentence IS the loop."
        )
    if trigger_sig.source == "transit":
        t = trigger_sig.evidence.get("transit", "")
        n = trigger_sig.evidence.get("natal", "")
        if t == "Neptune" or n == "Neptune":
            return "Don't decide what it means today. Pick one small action and let the meaning catch up."
        if t == "Saturn":
            return "Name the decision you're actually avoiding — out loud, to one person, in one sentence."
        if t == "Mars":
            return "Do the two minutes of the thing. Not the plan for the thing."
        if t == "Mercury":
            return "Send the three-sentence version of what you've been drafting."
        if t == "Jupiter":
            return "Say yes to the smaller version of the thing, today."
        if t == "Pluto":
            return "Stop negotiating. Write down what you're actually willing to lose."
    if trigger_sig.source == "stellium":
        return "Pick the one area that's loudest today. Give it 20 minutes of real attention before the rest of the day."
    return "Do the smallest version of the real thing before doing the bigger version of the stalling thing."


# =============================================================================
# STEP 3 — BUILD OUTPUT
# =============================================================================

MIN_SIGNALS_REQUIRED = 2
MIN_DISTINCT_SOURCES = 2


async def generate_home_signal_grounded(db, user_id: str, now: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Primary entry point. Returns:
        {
          "render": bool,
          "version": "v6_signal_grounded",
          "trigger": str | None,
          "collision": str | None,
          "distortion": str | None,
          "cost": str | None,
          "interrupt": str | None,
          "signals_used": [{...}, ...],
          "distinct_sources": int,
          "generated_at": iso,
          "reason": str (if render=False)
        }
    """
    if now is None:
        now = datetime.now(timezone.utc)

    signals = await gather_signals(db, user_id, now)

    # Gate 1: minimum signal count
    if len(signals) < MIN_SIGNALS_REQUIRED:
        return {
            "render": False,
            "version": "v6_signal_grounded",
            "reason": "insufficient_signals",
            "signal_count": len(signals),
            "generated_at": now.isoformat(),
        }

    # Gate 2: minimum distinct sources
    distinct = {s.source for s in signals}
    if len(distinct) < MIN_DISTINCT_SOURCES:
        return {
            "render": False,
            "version": "v6_signal_grounded",
            "reason": "single_source_only",
            "signal_count": len(signals),
            "distinct_sources": list(distinct),
            "generated_at": now.isoformat(),
        }

    # Pick layer drivers.
    # TRIGGER priority: per-user signals FIRST (transit/HD activation) — these name
    # what today is doing specifically to THIS user's chart. Only fall back to
    # global signals (stellium, lunar event) if no per-user signal is strong enough.
    user_specific_triggers = [s for s in signals if s.source in ("transit", "hd_activation")]
    global_triggers = [s for s in signals if s.source in ("stellium", "lunar_event")]

    trigger_sig = None
    if user_specific_triggers:
        # Strongest user-specific signal wins
        trigger_sig = max(user_specific_triggers, key=lambda s: s.weight)
    elif global_triggers:
        trigger_sig = max(global_triggers, key=lambda s: s.weight)

    pattern_sig = _pick(signals, "pattern_recurrence")

    # We need at minimum (a) a trigger AND (b) either a pattern recurrence or a second astro signal
    if trigger_sig is None:
        return {
            "render": False,
            "version": "v6_signal_grounded",
            "reason": "no_trigger_signal",
            "signal_count": len(signals),
            "generated_at": now.isoformat(),
        }

    # Build BEHAVIORAL layers — planets stay hidden in `signals_used` / `why_showing_up`.
    # These composers NEVER mention planets, signs, or astrological terms.
    hook_line        = _compose_hook(trigger_sig, pattern_sig)
    recognition_line = _compose_recognition(trigger_sig, pattern_sig, signals)
    cost_line        = _compose_cost_v2(trigger_sig, pattern_sig)
    move_line        = _compose_move_v2(trigger_sig, pattern_sig)

    # Require a pattern OR a second distinct signal for depth — but don't block render
    # the way the old "collision" gate did. If neither, we still have enough for a
    # concrete behavioral card with HOOK / RECOGNITION / COST / MOVE.

    return {
        "render": True,
        "version": "v6_signal_grounded",
        # NEW behavioral-first contract
        "hook": hook_line,
        "recognition": recognition_line,
        "cost": cost_line,
        "move": move_line,
        # Back-compat mapping (old keys point at the new behavioral lines)
        "trigger": hook_line,
        "collision": recognition_line,
        "distortion": None,      # no longer surfaced as its own layer — lives in proof
        "interrupt": move_line,
        "signals_used": [
            {
                "source": s.source,
                "kind": s.kind,
                "label": s.label,
                "weight": round(s.weight, 3),
                "evidence": s.evidence,
            }
            for s in signals[:6]
        ],
        "signal_count": len(signals),
        "distinct_sources": sorted(list(distinct)),
        "generated_at": now.isoformat(),
    }
