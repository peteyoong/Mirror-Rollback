"""
Member Summary Card — quick orientation of a single forum member across
all computed lenses. Shown inline directly below the members row.

Returns a scannable structure (each field is None if the lens is missing
so the UI can hide the row entirely):

    {
        "name": "Pete",
        "is_host": true,
        "astrology":    "Pisces Sun · Aries Moon · Sagittarius Rising",
        "human_design": "Manifestor · Emotional Authority · 5/1",
        "bazi":         "Dragon · Ding Fire Day Master · strong Fire / Wood",
        "enneagram":    "7w8",
        "numerology":   "11/2",
        "how_they_read":"Warm, fast-moving, emotionally direct — tends to energise the room.",
        "chart_version":"v:midpoint13_variant_a_v1:ts:1718387310479",
    }

No LLM calls. Everything is derived deterministically from the cached
chart + user doc.

Build marker: mel-rising-fix-member-summary-v1 (2026-06-16) — adds
5-fallback Ascendant resolution + longitude-derived fallback so a
stale/missing `astro.angles.asc.sign` cannot silently surface as a
wrong Rising in the member-summary card. Also adds `chart_version`
to the response so client caches can invalidate when the underlying
chart is recomputed.
"""
from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Optional

from bson import ObjectId

logger = logging.getLogger(__name__)


_CHINESE_ZODIAC: List[str] = [
    "Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
    "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig",
]


def _title(s: Optional[str]) -> Optional[str]:
    if not isinstance(s, str) or not s.strip():
        return None
    return s.strip().title()


def _chinese_zodiac_from_year(year: Optional[int]) -> Optional[str]:
    """Reference: 2020 = Rat. Anchor for all years via modulo 12."""
    if not isinstance(year, int):
        return None
    idx = (year - 2020) % 12
    return _CHINESE_ZODIAC[idx]


# ------------------------------------------------------------------ formatters


def _format_astrology(chart: Dict[str, Any]) -> Optional[str]:
    """Render the astrology summary string.

    Sun/Moon: `astro.planets.{Sun,Moon}.sign` (case-insensitive).

    Rising sign — 5-fallback resolution (matches the canonical order used by
    `services.forum_lens_helpers.get_member_lens_data`, build marker
    `astrology-lens-summary-rising-fix-v1`):

      1. `astro.angles.asc.sign`            (canonical, post-Variant-A migration)
      2. `astro.angles.ascendant.sign`      (legacy alias)
      3. `astro.houses.ascendant_sign`      (legacy intake forms)
      4. derive from `astro.angles.asc.longitude` via
         `calculations.astrology.longitude_to_sign_degree` (honours the
         active True Sidereal-M Midpoint mode)
      5. derive from `astro.houses.ascendant` (legacy float)

    Until this build (`mel-rising-fix-member-summary-v1`) only #1 and #2
    were consulted. A chart that stored only the longitude — or that had
    been recomputed but never wrote a `sign` token under `angles.asc` —
    would silently drop the Rising row, OR keep echoing a previously-bad
    `houses.ascendant_sign`. That was the root surface of the live Mel
    "Gemini Rising" regression.
    """
    astro = (chart or {}).get("astrology") or {}
    planets = astro.get("planets") or {}
    angles = astro.get("angles") or {}
    houses = astro.get("houses") or {}

    # Sun / Moon — case-insensitive planet lookup
    def _planet_sign(key: str) -> Optional[str]:
        p = planets.get(key) or planets.get(key.lower()) or planets.get(key.title())
        if isinstance(p, dict):
            return p.get("sign")
        if isinstance(p, str):
            return p
        return None

    sun = _planet_sign("Sun")
    moon = _planet_sign("Moon")

    # Rising — 5-fallback resolution
    asc_node = angles.get("asc") or angles.get("ascendant") or {}
    asc: Optional[str] = None

    if isinstance(asc_node, dict) and asc_node.get("sign"):
        asc = asc_node.get("sign")                                     # (1)

    if not asc and houses.get("ascendant_sign"):
        asc = houses.get("ascendant_sign")                             # (3) legacy intake

    if not asc:
        asc_lon = None
        trop_lon = None
        if isinstance(asc_node, dict):
            asc_lon = asc_node.get("longitude")
            trop_lon = asc_node.get("tropical_longitude")
        if asc_lon is None:
            asc_lon = houses.get("ascendant")                          # (5) legacy float
        if isinstance(asc_lon, (int, float)):
            try:
                from calculations.astrology import longitude_to_sign_degree as _lts
                resolved = _lts(float(asc_lon) % 360,
                                tropical_longitude=trop_lon)
                if isinstance(resolved, dict) and resolved.get("sign"):
                    asc = resolved["sign"]                             # (4)
            except Exception as _e:  # pragma: no cover — defensive
                logger.warning(
                    "[MemberSummary] longitude_to_sign_degree failed for "
                    "asc_lon=%s: %s (chart will surface without Rising)",
                    asc_lon, _e,
                )

    parts: List[str] = []
    if _title(sun):
        parts.append(f"{_title(sun)} Sun")
    if _title(moon):
        parts.append(f"{_title(moon)} Moon")
    if _title(asc):
        parts.append(f"{_title(asc)} Rising")
    return " · ".join(parts) if parts else None


def _format_hd(chart: Dict[str, Any]) -> Optional[str]:
    hd = (chart or {}).get("human_design") or {}
    t = hd.get("type")
    auth = hd.get("authority") or hd.get("inner_authority")
    profile = hd.get("profile")

    parts: List[str] = []
    if isinstance(t, str) and t.strip():
        parts.append(t.strip())
    if isinstance(auth, str) and auth.strip():
        auth_s = auth.strip()
        if "authority" not in auth_s.lower():
            auth_s = f"{auth_s} Authority"
        parts.append(auth_s)
    if isinstance(profile, str) and profile.strip():
        parts.append(profile.strip())
    return " · ".join(parts) if parts else None


def _format_bazi(chart: Dict[str, Any], user: Dict[str, Any]) -> Optional[str]:
    """
    Format: [Animal Sign] · [Day Master] · [Element Balance]
    Animal sign is always first when available — the Asian-user anchor.
    """
    bazi = (chart or {}).get("bazi") or {}

    # 1. Animal sign — prefer explicit bazi.pillars.year.animal_name (the
    #    Asian-user anchor), falling back to various legacy fields, finally
    #    computing from birth year as last resort.
    pillars = bazi.get("pillars") or {}
    year_pillar = pillars.get("year") or bazi.get("year_pillar") or {}
    animal = None
    if isinstance(year_pillar, dict):
        animal = (
            year_pillar.get("animal_name")
            or year_pillar.get("animal")
        )
        # strip emoji prefix from "🐒 Monkey"
        if isinstance(animal, str):
            animal = animal.strip()
            # keep only trailing latin word (skip emoji/chars)
            parts = [p for p in animal.split() if p[:1].isalpha()]
            animal = parts[-1] if parts else animal
    if not animal:
        animal = (
            bazi.get("year_animal")
            or bazi.get("animal_sign")
            or (chart.get("chinese_zodiac") or {}).get("animal")
        )
    if not animal:
        year = None
        bd = user.get("birth_date") or user.get("birthdate")
        if hasattr(bd, "year"):
            year = bd.year
        elif isinstance(bd, str) and len(bd) >= 4 and bd[:4].isdigit():
            year = int(bd[:4])
        animal = _chinese_zodiac_from_year(year)

    # 2. Day Master — prefer Pinyin ("Ding Fire") over Chinese characters.
    dm = bazi.get("day_master") or {}
    dm_stem = dm.get("stem_pinyin") or dm.get("pinyin") or dm.get("stem")
    dm_element = dm.get("element")
    day_master_str = None
    if dm_stem and dm_element:
        day_master_str = f"{str(dm_stem).strip().title()} {str(dm_element).strip().title()} Day Master"
    elif dm_element:
        day_master_str = f"{str(dm_element).strip().title()} Day Master"
    elif isinstance(dm, str) and dm.strip():
        day_master_str = f"{dm.strip().title()} Day Master"

    # 3. Element balance — strong elements first, then supporting if distinct
    elements = bazi.get("elements") or {}
    dom = [e for e in (elements.get("dominant") or []) if isinstance(e, str)]
    strength = None
    if isinstance(dm, dict):
        s = dm.get("strength")
        if isinstance(s, str) and s.strip():
            strength = s.strip().lower()
    balance = None
    if dom:
        dom_str = " / ".join(e.title() for e in dom[:2])
        balance = f"{strength} {dom_str}" if strength else dom_str
    elif strength:
        balance = f"{strength} day master"

    parts = [p for p in (
        _title(animal) if animal else None,
        day_master_str,
        balance,
    ) if p]
    return " · ".join(parts) if parts else None


def _format_enneagram(user: Dict[str, Any]) -> Optional[str]:
    primary = (
        user.get("enneagram_type")
        or user.get("primary_enneagram_type")
        or (user.get("enneagram") or {}).get("primary_type")
        or (user.get("enneagram_result") or {}).get("primary_type")
    )
    try:
        p = int(primary) if primary is not None else None
        if p is None or not (1 <= p <= 9):
            return None
    except (TypeError, ValueError):
        return None

    wing = (
        user.get("enneagram_wing")
        or (user.get("enneagram") or {}).get("wing")
        or (user.get("enneagram_result") or {}).get("wing")
    )
    if wing is not None:
        try:
            w = int(wing)
            if 1 <= w <= 9 and w != p:
                return f"{p}w{w}"
        except (TypeError, ValueError):
            pass
    return f"Type {p}"


def _format_numerology(chart: Dict[str, Any]) -> Optional[str]:
    num = (chart or {}).get("numerology") or {}

    def _get(block):
        if isinstance(block, dict):
            return block.get("number") or block.get("master_number")
        if isinstance(block, int):
            return block
        return None

    lp = _get(num.get("life_path")) or _get(num.get("life_path_number"))
    # Master-number reveal (11/2, 22/4, 33/6)
    master_map = {11: "11/2", 22: "22/4", 33: "33/6"}
    if isinstance(lp, int):
        return master_map.get(lp, str(lp))
    return None


# ---------------------------------------------------------------------- synthesis


def _how_they_read(chart: Dict[str, Any], user: Dict[str, Any]) -> str:
    """
    A single short synthesis sentence. Plain English, no jargon.
    Derived deterministically from HD type, BaZi day-master element,
    and Enneagram type.
    """
    hd_type = ((chart or {}).get("human_design") or {}).get("type") or ""
    hd_type = hd_type.strip().lower()

    bazi_element = (((chart or {}).get("bazi") or {}).get("day_master") or {}).get("element") or ""
    bazi_element = bazi_element.strip().lower()

    enn = None
    try:
        enn = int(user.get("enneagram_type") or (user.get("enneagram") or {}).get("primary_type") or 0) or None
    except Exception:
        enn = None

    # Base flavour from HD type
    if "manifesting" in hd_type and "generator" in hd_type:
        base = "Fast-moving and multi-tracked"
    elif "manifestor" in hd_type:
        base = "Direct and initiating"
    elif "projector" in hd_type:
        base = "Perceptive and system-seeing"
    elif "reflector" in hd_type:
        base = "Quietly perceptive"
    elif "generator" in hd_type:
        base = "Grounded and steady"
    else:
        base = "Quietly present"

    # Warmth layer from BaZi
    warmth = {
        "fire":  "warm",
        "wood":  "expansive",
        "earth": "grounded",
        "metal": "precise",
        "water": "emotionally attuned",
    }.get(bazi_element)
    if warmth and warmth not in base.lower():
        base = f"{warmth.capitalize()}, {base.lower()}"

    # Room-effect tail from HD type
    effect = {
        "manifestor":           "tends to move the room into action.",
        "manifesting generator": "tends to energise and shape the work.",
        "projector":            "people feel seen before they know why.",
        "reflector":            "absorbs and reflects the tone of the room.",
        "generator":            "brings things back to what actually matters.",
    }
    tail = None
    for k, v in effect.items():
        if k in hd_type:
            tail = v
            break
    tail = tail or "adds depth without dominating."

    # Enneagram nudge softens / sharpens the ending
    if enn in (7, 8, 3):
        tail = tail.replace("adds depth", "pushes the pace").replace("actually matters", "actually moves forward")
    elif enn in (4, 2, 9):
        tail = tail.replace("move the room into action", "shift the emotional temperature") \
                   .replace("pushes the pace", "deepens the emotional layer")
    elif enn in (5, 1):
        tail = tail.replace("tends to energise and shape the work", "brings precision and refines the thinking")

    return f"{base} — {tail}"


# ======================================================================== API


def _compute_chart_version(chart: Dict[str, Any]) -> str:
    """Stable cache-busting token derived from the chart's compute metadata.

    Combines (in order of preference):
      • `astrology.metadata.computation_version`  or  `astrology.metadata.astrology_engine_version`
      • the most recent of `chart.chart_updated_at` / `chart.astrology_updated_at`
        / `chart.updated_at` / `chart.created_at`
      • the chart `_id`

    Falls back to a short SHA-1 of whatever string-coerced subset is available
    so that **a recompute → write to db.charts always produces a different
    token**. The frontend uses this as part of its cache key (see
    `app/forums/[id].tsx` memberSummaries) so that a corrected chart is never
    masked by a previously-rendered stale summary.

    Format: `v:<engine>|t:<ts>|c:<id8>` — opaque to the client; the only
    contract is that the token CHANGES when the underlying chart changes.
    """
    if not chart:
        return "v:none"
    astro = chart.get("astrology") or {}
    meta = astro.get("metadata") or {}
    engine = (
        meta.get("computation_version")
        or meta.get("astrology_engine_version")
        or astro.get("astrology_engine_version")
        or "unknown"
    )
    # Pick the freshest timestamp we can find on the chart envelope.
    ts_candidates = [
        chart.get("chart_updated_at"),
        chart.get("astrology_updated_at"),
        chart.get("updated_at"),
        chart.get("created_at"),
    ]
    ts_str = ""
    for c in ts_candidates:
        if c is None:
            continue
        try:
            ts_str = c.isoformat() if hasattr(c, "isoformat") else str(c)
            break
        except Exception:
            continue
    cid = chart.get("_id")
    cid_str = str(cid)[-8:] if cid is not None else ""
    raw = f"v:{engine}|t:{ts_str}|c:{cid_str}"
    # Keep the human-meaningful prefix but append a short hash for safety so
    # cosmetic field reorders never produce identical tokens.
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8]
    return f"{raw}|h:{digest}"


async def get_member_summary(db, forum_id: str, member_id: str) -> Optional[Dict[str, Any]]:
    if not ObjectId.is_valid(forum_id) or not ObjectId.is_valid(member_id):
        return None

    # Confirm this member is actually in this forum
    membership = await db.forum_members.find_one({
        "forum_id": forum_id, "user_id": member_id, "status": "active",
    })
    if not membership:
        return None

    forum = await db.forums.find_one({"_id": ObjectId(forum_id)})
    creator_id = forum.get("created_by") if forum else None

    user = await db.users.find_one({"_id": ObjectId(member_id)})
    if not user:
        return None

    chart = await db.charts.find_one({"user_id": member_id}) or {}

    name = (user.get("name") or "").strip() or "Member"

    payload = {
        "member_id": member_id,
        "name": name,
        "is_host": member_id == creator_id,
        "astrology":    _format_astrology(chart),
        "human_design": _format_hd(chart),
        "bazi":         _format_bazi(chart, user),
        "enneagram":    _format_enneagram(user),
        "numerology":   _format_numerology(chart),
        "how_they_read": _how_they_read(chart, user),
        # mel-rising-fix-member-summary-v1: opaque cache token. Changes
        # whenever the chart is recomputed/rewritten so the client's
        # member-summary cache cannot pin a previously-bad payload across
        # a chart correction.
        "chart_version": _compute_chart_version(chart),
    }
    return payload
