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
    }

No LLM calls. Everything is derived deterministically from the cached
chart + user doc.
"""
from __future__ import annotations

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
    astro = (chart or {}).get("astrology") or {}
    planets = astro.get("planets") or {}
    angles = astro.get("angles") or {}

    sun = (planets.get("Sun") or planets.get("sun") or {}).get("sign")
    moon = (planets.get("Moon") or planets.get("moon") or {}).get("sign")
    asc = (angles.get("asc") or {}).get("sign") or (angles.get("ascendant") or {}).get("sign")

    parts: List[str] = []
    if _title(sun):  parts.append(f"{_title(sun)} Sun")
    if _title(moon): parts.append(f"{_title(moon)} Moon")
    if _title(asc):  parts.append(f"{_title(asc)} Rising")
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
    }
    return payload
