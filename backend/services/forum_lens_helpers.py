"""
Forum Lens Helpers  (server-router-refactor-v6)
================================================

Shared lens helpers used by:
  • forum chat        (routers/forums_chat.py)
  • forum mirror-chat (server.py — pending extraction)
  • forum intelligence routes
      - member-lens
      - relationship-map
      - pattern-map
      - dynamics-context
      - pairwise-dynamics
      - contributions
    (routers/forums_intelligence.py)
  • future forum field routes (forum_field, live_field)

These helpers were previously defined inline in server.py
(~700 combined lines).  Hoisting them here lets the router layer
import them directly rather than receiving them as register()
arguments, and keeps the implementation a single source of truth.

Behaviour is identical to the inline server.py version — same
field names, same fallbacks, same logging.  Nothing about the
shape returned to the API surface changes.

Usage:

    from services import forum_lens_helpers
    forum_lens_helpers.init(db, logger)   # once, at app start
    lens = await forum_lens_helpers.get_member_lens_data(user_id)
    ctx  = forum_lens_helpers.build_forum_dynamics_context([lens, ...])

The astrology auto-migration callback is resolved lazily on first
call (via a deferred import from server) to avoid a circular import
at module load time.  If the import fails we skip migration silently
and continue with whatever chart data the user already has — same
graceful behaviour as the original inline code.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from bson import ObjectId


# ---------------------------------------------------------------------------
# Module-level state set via init().  Keeping these as module globals lets
# callers invoke helpers with the original single-arg signature
# (`get_member_lens_data(user_id)`), preserving existing call sites in
# server.py and routers without changes.
# ---------------------------------------------------------------------------

_db = None
_logger: logging.Logger = logging.getLogger(__name__)
_astrology_migrator: Optional[Callable] = None


def init(
    db,
    logger: Optional[logging.Logger] = None,
    astrology_migrator: Optional[Callable] = None,
) -> None:
    """
    Bind the Motor database handle, logger, and the optional astrology
    auto-migration callback to this module.  Should be called once at
    application startup (server.py).

    `astrology_migrator` is the async function
    `check_and_migrate_astrology_chart(user_id)` from server.py.  It is
    optional — if not provided, the helper performs a lazy `from server
    import ...` on first use to maintain backwards compatibility.
    """
    global _db, _logger, _astrology_migrator
    _db = db
    if logger is not None:
        _logger = logger
    if astrology_migrator is not None:
        _astrology_migrator = astrology_migrator


def _resolve_astrology_migrator() -> Optional[Callable]:
    """Lazy lookup so we don't trigger a circular import at module load."""
    global _astrology_migrator
    if _astrology_migrator is not None:
        return _astrology_migrator
    try:
        # Deferred import — by request-time server.py is fully loaded.
        from server import check_and_migrate_astrology_chart  # type: ignore
        _astrology_migrator = check_and_migrate_astrology_chart
        return _astrology_migrator
    except Exception:  # pragma: no cover — defensive
        return None


# ===========================================================================
# get_member_lens_data
# ===========================================================================

async def get_member_lens_data(user_id: str) -> dict:
    """
    Build the full forum_member_lens_data object for a user.
    Aggregates data from existing user profile sources (charts, enneagram, patterns).
    Returns None values for missing fields - never fails.
    """
    db = _db
    logger = _logger

    lens_data = {
        "user_id": user_id,
        "name": None,
        "human_design": {
            "type": None,
            "strategy": None,
            "authority": None,
            "profile": None,
            "definition": None,
            "incarnation_cross": None,
            "centers_defined": [],
            "centers_undefined": [],
            "active_gates": [],
            "active_channels": []  # Will be formatted as strings like "37-40"
        },
        "enneagram": {
            "core_type": None,
            "wing": None,
            "center": None,
            "hornevian_group": None,
            "harmonic_group": None,
            "growth_direction": None,
            "stress_direction": None
        },
        "astrology": {
            "sun": None,
            "moon": None,
            "rising": None,
            "dominant_element": None,
            "dominant_modality": None
        },
        "bazi": {
            "day_master_element": None,      # e.g. "Metal"
            "day_master_polarity": None,     # e.g. "Yin"
            "day_master_stem": None,         # e.g. "Xin"
            "day_master_strength": None,     # e.g. "strong"
            "structure": None,               # top-level structure label
            "year_animal": None,
            "month_animal": None,
            "day_animal": None,
            "hour_animal": None,
            "elements": None                 # dict of element counts
        },
        "numerology": {
            "life_path": None,
            "expression": None,
            "soul_urge": None,
            "personality": None
        },
        "patterns": {
            "active_domains": [],
            "recurring_domains": []
        },
        # Compute status — frontend can use this to surface "missing birth data"
        # vs "compute failed" vs "ok" clearly instead of showing empty lenses.
        "compute_status": {
            "has_birth_data": False,
            "astrology_ok": False,
            "bazi_ok": False,
            "astrology_recomputed": False,
            "bazi_recomputed": False,
            "errors": []
        }
    }

    try:
        # Get user basic info
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if user:
            lens_data["name"] = user.get("name", "Anonymous")
            # Detect birth data presence for compute_status
            has_birth_data = bool(
                user.get("birth_date")
                and user.get("birth_time")
                and (user.get("birth_location", {}).get("latitude") is not None
                     or user.get("birth_location", {}).get("lat") is not None)
            )
            lens_data["compute_status"]["has_birth_data"] = has_birth_data

        # If user has birth data, ensure astrology chart is fresh (auto-migrates
        # legacy / corrupted chart with empty planets).
        if user and lens_data["compute_status"]["has_birth_data"]:
            migrator = _resolve_astrology_migrator()
            if migrator is not None:
                try:
                    migrated, status_msg, updated = await migrator(user_id)
                    if migrated:
                        logger.info(f"[MemberLens] Astrology migration performed for {user_id[:8]}: {status_msg}")
                        lens_data["compute_status"]["astrology_recomputed"] = True
                except Exception as _mig_e:
                    logger.warning(f"[MemberLens] Astrology auto-migration skipped for {user_id[:8]}: {_mig_e}")
                    lens_data["compute_status"]["errors"].append(f"astrology_migration: {_mig_e}")

        # Get chart data (contains astrology, human_design, numerology)
        chart = await db.charts.find_one({"user_id": user_id})
        if chart:
            # === Human Design ===
            hd = chart.get("human_design", {})
            if hd:
                lens_data["human_design"]["type"] = hd.get("type") if hd.get("type") != "Unknown" else None
                lens_data["human_design"]["strategy"] = hd.get("strategy") if hd.get("strategy") != "Unknown" else None
                lens_data["human_design"]["authority"] = hd.get("authority") if hd.get("authority") != "Unknown" else None
                lens_data["human_design"]["profile"] = hd.get("profile") if hd.get("profile") != "Unknown" else None
                lens_data["human_design"]["definition"] = hd.get("definition") if hd.get("definition") != "Unknown" else None

                # Incarnation cross - handle both dict and string formats
                ic = hd.get("incarnation_cross")
                if isinstance(ic, dict):
                    lens_data["human_design"]["incarnation_cross"] = ic.get("name", str(ic))
                elif ic and ic != "Unknown":
                    lens_data["human_design"]["incarnation_cross"] = str(ic)

                # Centers
                lens_data["human_design"]["centers_defined"] = hd.get("defined_centers", [])
                # Calculate undefined centers
                all_centers = ["Head", "Ajna", "Throat", "G", "Heart", "Sacral", "Solar Plexus", "Spleen", "Root"]
                defined = set(hd.get("defined_centers", []))
                lens_data["human_design"]["centers_undefined"] = [c for c in all_centers if c not in defined]

                # Gates and channels
                lens_data["human_design"]["active_gates"] = hd.get("all_gates", hd.get("gates", []))

                # Format channels as readable strings (e.g., "37-40")
                raw_channels = hd.get("defined_channels", [])
                formatted_channels = []
                for ch in raw_channels:
                    if isinstance(ch, dict):
                        # Channel is an object with gate1, gate2
                        g1 = ch.get("gate1")
                        g2 = ch.get("gate2")
                        if g1 and g2:
                            formatted_channels.append(f"{g1}-{g2}")
                    elif isinstance(ch, str):
                        formatted_channels.append(ch)
                    elif isinstance(ch, (list, tuple)) and len(ch) >= 2:
                        formatted_channels.append(f"{ch[0]}-{ch[1]}")
                lens_data["human_design"]["active_channels"] = formatted_channels

            # === Astrology ===
            astro = chart.get("astrology", {})
            if astro:
                planets = astro.get("planets", {}) or {}

                def _get_planet(pk: str):
                    """Fetch planet entry by name, case-insensitive. Supports
                    legacy lowercase ('sun') and canonical title-case ('Sun')."""
                    if not isinstance(planets, dict):
                        return {}
                    if pk in planets:
                        return planets[pk]
                    # Try title-case and lower-case variants
                    for candidate in (pk.title(), pk.lower(), pk.upper()):
                        if candidate in planets:
                            return planets[candidate]
                    return {}

                # Sun
                sun = _get_planet("sun")
                if isinstance(sun, dict):
                    lens_data["astrology"]["sun"] = sun.get("sign")
                elif isinstance(sun, str):
                    lens_data["astrology"]["sun"] = sun

                # Moon
                moon = _get_planet("moon")
                if isinstance(moon, dict):
                    lens_data["astrology"]["moon"] = moon.get("sign")
                elif isinstance(moon, str):
                    lens_data["astrology"]["moon"] = moon

                # Rising (Ascendant)
                # ── FORENSIC FIX (astrology-lens-summary-rising-fix-v1) ──
                # Mirror's astrology engine writes the Ascendant to
                # astro.angles.asc.{sign,longitude} (since the True
                # Sidereal-M migration). The earlier code path only
                # looked at astro.houses.ascendant_sign /
                # astro.houses.ascendant — which the current engine
                # does NOT populate — so `rising_sign` always
                # silently fell through to None, and the lens summary
                # surface picked up a stale or fallback value.
                #
                # Source-of-truth order (most authoritative first):
                #   1. astro.angles.asc.sign            ← canonical
                #   2. astro.angles.ascendant.sign      ← legacy alias
                #   3. astro.houses.ascendant_sign      ← legacy intake forms
                #   4. derive from astro.angles.asc.longitude
                #   5. derive from astro.houses.ascendant (legacy float)
                rising_sign = None
                rising_source = None
                rising_asc_longitude = None

                angles = (astro.get("angles") or {})
                asc_node = angles.get("asc") or angles.get("ascendant") or {}
                if isinstance(asc_node, dict) and asc_node.get("sign"):
                    rising_sign   = asc_node.get("sign")
                    rising_source = "astro.angles.asc.sign"
                    rising_asc_longitude = asc_node.get("longitude")

                houses = astro.get("houses", {}) or {}
                if not rising_sign and houses.get("ascendant_sign"):
                    rising_sign   = houses.get("ascendant_sign")
                    rising_source = "astro.houses.ascendant_sign (legacy)"

                if not rising_sign:
                    asc_deg = (
                        (asc_node.get("longitude") if isinstance(asc_node, dict) else None)
                        or houses.get("ascendant")
                    )
                    if isinstance(asc_deg, (int, float)):
                        from calculations.astrology import longitude_to_sign_degree as _lts
                        rising_sign = _lts(float(asc_deg) % 360)["sign"]
                        rising_source = "derived from longitude"
                        rising_asc_longitude = float(asc_deg)

                lens_data["astrology"]["rising"] = rising_sign

                # ── Forensic debug payload (always populated) ───────
                # astrology-lens-summary-debug-v1
                from datetime import datetime, timezone as _tz
                lens_data["astrology"]["_debug"] = {
                    "summary_string": " · ".join(
                        f"{(lens_data['astrology'].get(k) or '?').title()} {label}"
                        for k, label in (("sun", "Sun"), ("moon", "Moon"), ("rising", "Rising"))
                        if lens_data["astrology"].get(k)
                    ),
                    "summary_sun_source":     "astro.planets.Sun.sign",
                    "summary_moon_source":    "astro.planets.Moon.sign",
                    "summary_rising_source":  rising_source,
                    "asc_from_angles":        (asc_node.get("sign") if isinstance(asc_node, dict) else None),
                    "asc_longitude":          rising_asc_longitude,
                    "stored_houses_ascendant_sign":  houses.get("ascendant_sign"),
                    "stored_houses_ascendant_deg":   houses.get("ascendant"),
                    "stored_angles_keys":     list(angles.keys()) if isinstance(angles, dict) else [],
                    "stored_houses_keys":     list(houses.keys()) if isinstance(houses, dict) else [],
                    "chart_engine_version":   (astro.get("metadata") or {}).get("computation_version"),
                    "chart_sidereal_mode":    (astro.get("metadata") or {}).get("sidereal_mode"),
                    "chart_house_system":     (astro.get("metadata") or {}).get("house_system"),
                    "birth_input_used": {
                        "utc":  (astro.get("metadata") or {}).get("input_datetime_utc"),
                        "lat":  ((astro.get("metadata") or {}).get("coordinates") or {}).get("lat"),
                        "lon":  ((astro.get("metadata") or {}).get("coordinates") or {}).get("lon"),
                    },
                    "summary_generated_at":   datetime.now(_tz.utc).isoformat(),
                    "fix_build_marker":       "astrology-lens-summary-rising-fix-v1",
                }

                # Calculate dominant element and modality from planets
                element_counts = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
                modality_counts = {"Cardinal": 0, "Fixed": 0, "Mutable": 0}

                sign_elements = {
                    "Aries": "Fire", "Taurus": "Earth", "Gemini": "Air", "Cancer": "Water",
                    "Leo": "Fire", "Virgo": "Earth", "Libra": "Air", "Scorpio": "Water",
                    "Sagittarius": "Fire", "Capricorn": "Earth", "Aquarius": "Air", "Pisces": "Water"
                }
                sign_modalities = {
                    "Aries": "Cardinal", "Taurus": "Fixed", "Gemini": "Mutable", "Cancer": "Cardinal",
                    "Leo": "Fixed", "Virgo": "Mutable", "Libra": "Cardinal", "Scorpio": "Fixed",
                    "Sagittarius": "Mutable", "Capricorn": "Cardinal", "Aquarius": "Fixed", "Pisces": "Mutable"
                }

                for planet_name, planet_data in planets.items():
                    sign = planet_data.get("sign") if isinstance(planet_data, dict) else planet_data
                    if sign and sign in sign_elements:
                        element_counts[sign_elements[sign]] += 1
                        modality_counts[sign_modalities[sign]] += 1

                if any(element_counts.values()):
                    lens_data["astrology"]["dominant_element"] = max(element_counts.items(), key=lambda x: x[1])[0]
                if any(modality_counts.values()):
                    lens_data["astrology"]["dominant_modality"] = max(modality_counts.items(), key=lambda x: x[1])[0]

                # Mark astrology as OK if we ended up with any of sun/moon/rising
                if any([lens_data["astrology"]["sun"], lens_data["astrology"]["moon"], lens_data["astrology"]["rising"]]):
                    lens_data["compute_status"]["astrology_ok"] = True
                else:
                    logger.warning(
                        f"[MemberLens] Astrology yielded no sun/moon/rising for {user_id[:8]} "
                        f"(planets populated={bool(planets)}). Chart may still be corrupted."
                    )
                    lens_data["compute_status"]["errors"].append("astrology_empty_after_extract")

            # === BaZi ===
            # Prefer persisted chart.bazi. If missing but user has birth data,
            # compute on-demand via bazi_engine_v2 and persist.
            bazi = chart.get("bazi") or {}
            if not bazi and lens_data["compute_status"]["has_birth_data"]:
                try:
                    from services.bazi_engine_v2 import compute_bazi_chart_v2
                    bl = user.get("birth_location", {})
                    lat = bl.get("latitude", bl.get("lat"))
                    lon = bl.get("longitude", bl.get("lng", bl.get("lon")))
                    bazi = compute_bazi_chart_v2(
                        birth_date=str(user.get("birth_date")),
                        birth_time=str(user.get("birth_time") or "12:00"),
                        birth_place=bl.get("city", "Unknown"),
                        latitude=lat,
                        longitude=lon,
                        timezone_str=user.get("timezone") or bl.get("timezone") or "UTC",
                    ) or {}
                    if bazi:
                        await db.charts.update_one(
                            {"user_id": user_id},
                            {"$set": {"bazi": bazi, "bazi_updated_at": datetime.now(timezone.utc)}},
                            upsert=True,
                        )
                        lens_data["compute_status"]["bazi_recomputed"] = True
                        logger.info(f"[MemberLens] BaZi computed on-demand for {user_id[:8]}")
                except Exception as _bazi_e:
                    logger.warning(f"[MemberLens] BaZi compute failed for {user_id[:8]}: {_bazi_e}")
                    lens_data["compute_status"]["errors"].append(f"bazi_compute_failed: {_bazi_e}")

            if bazi:
                dm = bazi.get("day_master", {}) or {}
                pillars = bazi.get("pillars", {}) or {}

                lens_data["bazi"]["day_master_element"] = dm.get("element")
                lens_data["bazi"]["day_master_polarity"] = dm.get("polarity")
                lens_data["bazi"]["day_master_stem"] = dm.get("stem_pinyin") or dm.get("stem")
                lens_data["bazi"]["day_master_strength"] = dm.get("strength")
                lens_data["bazi"]["structure"] = (bazi.get("structure_summary") or {}).get("label") or bazi.get("structure")
                lens_data["bazi"]["year_animal"] = (pillars.get("year") or {}).get("animal_name")
                lens_data["bazi"]["month_animal"] = (pillars.get("month") or {}).get("animal_name")
                lens_data["bazi"]["day_animal"] = (pillars.get("day") or {}).get("animal_name")
                lens_data["bazi"]["hour_animal"] = (pillars.get("hour") or {}).get("animal_name")
                lens_data["bazi"]["elements"] = bazi.get("elements")

                if lens_data["bazi"]["day_master_element"]:
                    lens_data["compute_status"]["bazi_ok"] = True
                else:
                    logger.warning(f"[MemberLens] BaZi present but day_master.element missing for {user_id[:8]}")
                    lens_data["compute_status"]["errors"].append("bazi_day_master_missing")
            elif lens_data["compute_status"]["has_birth_data"]:
                # Birth data present but BaZi still empty after attempted compute
                logger.warning(f"[MemberLens] BaZi unavailable for {user_id[:8]} despite birth data")
                lens_data["compute_status"]["errors"].append("bazi_unavailable")

            # === Numerology ===
            numerology = chart.get("numerology", {})
            if numerology:
                lens_data["numerology"]["life_path"] = numerology.get("life_path")
                lens_data["numerology"]["expression"] = numerology.get("expression")
                lens_data["numerology"]["soul_urge"] = numerology.get("soul_urge")
                lens_data["numerology"]["personality"] = numerology.get("personality")

        # === Enneagram ===
        # CANONICAL RESOLUTION ORDER (see services/enneagram_source.py):
        #   1. user.enneagram_type          (single source of truth going forward)
        #   2. user.enneagram.inferred_core
        #   3. user.enneagram.core
        #   4. legacy scalar user.enneagram
        #   5. enneagram_results collection (wing + assessment metadata only
        #      when the user doc has nothing)
        #
        # Previously this block read ONLY from `db.enneagram_results`, which
        # caused Forum Dynamics → Enneagram Diversity to drift whenever the
        # user doc was updated but the collection wasn't. That drift is the
        # root cause of the reported mismatch.
        from services.enneagram_source import get_user_enneagram
        core_type = get_user_enneagram(user) if user else None
        wing_value = None

        enneagram_data = await db.enneagram_results.find_one({"user_id": user_id})
        if enneagram_data:
            # Prefer user-doc canonical core when present; otherwise fall
            # back to the stored assessment result.
            if core_type is None:
                from services.enneagram_source import _normalize_core
                core_type = _normalize_core(
                    enneagram_data.get("core_type") or enneagram_data.get("inferred_core")
                )
            # Wing always comes from the assessment result (we don't store
            # a canonical wing on the user doc yet).
            wing_value = enneagram_data.get("wing") or enneagram_data.get("inferred_wing")

            # Convert wing to int if it's not "balanced"
            if isinstance(wing_value, str) and wing_value != "balanced":
                try:
                    wing_value = int(wing_value)
                except ValueError:
                    wing_value = None
            elif wing_value == "balanced":
                wing_value = None

        if core_type is not None:
            lens_data["enneagram"]["core_type"] = core_type
            lens_data["enneagram"]["wing"] = wing_value

            # Add Enneagram metadata based on core type
            if core_type:
                # Centers (Body/Heart/Head)
                centers_map = {
                    8: "Body", 9: "Body", 1: "Body",
                    2: "Heart", 3: "Heart", 4: "Heart",
                    5: "Head", 6: "Head", 7: "Head"
                }
                # Hornevian Groups (Assertive/Compliant/Withdrawn)
                hornevian_map = {
                    3: "Assertive", 7: "Assertive", 8: "Assertive",
                    1: "Compliant", 2: "Compliant", 6: "Compliant",
                    4: "Withdrawn", 5: "Withdrawn", 9: "Withdrawn"
                }
                # Harmonic Groups (Positive/Competency/Reactive)
                harmonic_map = {
                    2: "Positive", 7: "Positive", 9: "Positive",
                    1: "Competency", 3: "Competency", 5: "Competency",
                    4: "Reactive", 6: "Reactive", 8: "Reactive"
                }
                # Growth and Stress directions
                growth_map = {1: 7, 2: 4, 3: 6, 4: 1, 5: 8, 6: 9, 7: 5, 8: 2, 9: 3}
                stress_map = {1: 4, 2: 8, 3: 9, 4: 2, 5: 7, 6: 3, 7: 1, 8: 5, 9: 6}

                lens_data["enneagram"]["center"] = centers_map.get(core_type)
                lens_data["enneagram"]["hornevian_group"] = hornevian_map.get(core_type)
                lens_data["enneagram"]["harmonic_group"] = harmonic_map.get(core_type)
                lens_data["enneagram"]["growth_direction"] = growth_map.get(core_type)
                lens_data["enneagram"]["stress_direction"] = stress_map.get(core_type)

        # === Patterns ===
        pattern_cache = await db.pattern_cache.find_one({
            "user_id": user_id,
            "cache_type": "pattern_graph"
        })
        if pattern_cache and pattern_cache.get("categories"):
            categories = pattern_cache.get("categories", [])
            active_domains = []
            recurring_domains = []

            for cat in categories:
                signal = cat.get("signal_strength", "")
                domain_name = cat.get("category_name")
                if domain_name:
                    if signal == "active":
                        active_domains.append(domain_name)
                    elif signal in ["emerging", "recurring"]:
                        recurring_domains.append(domain_name)

            lens_data["patterns"]["active_domains"] = active_domains
            lens_data["patterns"]["recurring_domains"] = recurring_domains

    except Exception as e:
        logger.warning(f"[MemberLensData] Error building lens data for {user_id}: {e}")

    return lens_data


# ===========================================================================
# build_forum_dynamics_context
# ===========================================================================

def build_forum_dynamics_context(members_lens_data: List[dict]) -> dict:
    """
    Build a structured context object for Forum Chat and Forum Dynamics.
    Aggregates member lens data into distributions and summaries.

    Args:
        members_lens_data: List of forum_member_lens_data objects

    Returns:
        Structured context object for AI interpretation
    """
    context = {
        "forum_members": members_lens_data,
        "member_count": len(members_lens_data),

        # Distributions
        "hd_type_distribution": {},
        "hd_authority_distribution": {},
        "hd_profile_distribution": {},
        "enneagram_distribution": {},
        "astrology_elements": {},
        "astrology_modalities": {},
        "numerology_life_paths": {},

        # Active patterns across forum
        "active_pattern_domains": [],

        # Center coverage (for channel/gate dynamics later)
        "defined_centers_coverage": {},
        "undefined_centers_coverage": {}
    }

    pattern_domain_counts: Dict[str, int] = {}

    for member in members_lens_data:
        # HD Type distribution
        hd = member.get("human_design", {})
        if hd.get("type"):
            hd_type = hd["type"]
            context["hd_type_distribution"][hd_type] = context["hd_type_distribution"].get(hd_type, 0) + 1

        # HD Authority distribution
        if hd.get("authority"):
            auth = hd["authority"]
            context["hd_authority_distribution"][auth] = context["hd_authority_distribution"].get(auth, 0) + 1

        # HD Profile distribution
        if hd.get("profile"):
            profile = hd["profile"]
            context["hd_profile_distribution"][profile] = context["hd_profile_distribution"].get(profile, 0) + 1

        # Center coverage
        for center in hd.get("centers_defined", []):
            context["defined_centers_coverage"][center] = context["defined_centers_coverage"].get(center, 0) + 1
        for center in hd.get("centers_undefined", []):
            context["undefined_centers_coverage"][center] = context["undefined_centers_coverage"].get(center, 0) + 1

        # Enneagram distribution
        enneagram = member.get("enneagram", {})
        if enneagram.get("core_type"):
            etype = enneagram["core_type"]
            context["enneagram_distribution"][etype] = context["enneagram_distribution"].get(etype, 0) + 1

        # Astrology elements
        astro = member.get("astrology", {})
        if astro.get("dominant_element"):
            elem = astro["dominant_element"]
            context["astrology_elements"][elem] = context["astrology_elements"].get(elem, 0) + 1
        if astro.get("dominant_modality"):
            mod = astro["dominant_modality"]
            context["astrology_modalities"][mod] = context["astrology_modalities"].get(mod, 0) + 1

        # Numerology life paths - handle both simple numbers and dict format
        numerology = member.get("numerology", {})
        if numerology.get("life_path"):
            lp = numerology["life_path"]
            # Handle dict format (e.g., {"number": 11, "description": "..."})
            if isinstance(lp, dict):
                lp = lp.get("number")
            if lp:
                context["numerology_life_paths"][lp] = context["numerology_life_paths"].get(lp, 0) + 1

        # Pattern domains
        patterns = member.get("patterns", {})
        for domain in patterns.get("active_domains", []):
            pattern_domain_counts[domain] = pattern_domain_counts.get(domain, 0) + 1

    # Sort pattern domains by count
    context["active_pattern_domains"] = sorted(
        [{"domain": k, "count": v} for k, v in pattern_domain_counts.items()],
        key=lambda x: -x["count"]
    )

    return context


# ===========================================================================
# Prompt formatters — pure helpers, shared by forum chat, forum mirror chat,
# pairwise-dynamics and forum story.  No DB access.
# ===========================================================================

def format_lens_for_prompt(lens_data: dict) -> str:
    """Render a single member's lens data as a compact prompt block."""
    parts: List[str] = []

    name = lens_data.get("name", "Anonymous")
    parts.append(f"Name: {name}")

    hd = lens_data.get("human_design", {})
    if hd.get("type"):
        hd_line = f"Human Design: {hd.get('type')}"
        if hd.get("profile"):
            hd_line += f" • {hd.get('profile')}"
        if hd.get("authority"):
            hd_line += f" • {hd.get('authority')} Authority"
        parts.append(hd_line)

        if hd.get("definition"):
            parts.append(f"  Definition: {hd.get('definition')}")
        if hd.get("centers_defined"):
            parts.append(f"  Defined Centers: {', '.join(hd.get('centers_defined', []))}")
        if hd.get("centers_undefined"):
            parts.append(f"  Open Centers: {', '.join(hd.get('centers_undefined', []))}")

    enneagram = lens_data.get("enneagram", {})
    if enneagram.get("core_type"):
        enne_line = f"Enneagram: Type {enneagram.get('core_type')}"
        if enneagram.get("wing"):
            enne_line += f"w{enneagram.get('wing')}"
        parts.append(enne_line)

    astro = lens_data.get("astrology", {})
    if astro.get("sun") or astro.get("moon"):
        astro_line = "Astrology:"
        if astro.get("sun"):
            astro_line += f" Sun in {astro.get('sun')}"
        if astro.get("moon"):
            astro_line += f", Moon in {astro.get('moon')}"
        if astro.get("rising"):
            astro_line += f", {astro.get('rising')} Rising"
        parts.append(astro_line)

    numerology = lens_data.get("numerology", {})
    if numerology.get("life_path"):
        lp = numerology.get("life_path")
        if isinstance(lp, dict):
            lp = lp.get("number")
        parts.append(f"Numerology: Life Path {lp}")

    patterns = lens_data.get("patterns", {})
    if patterns.get("active_domains"):
        parts.append(f"Active Pattern Domains: {', '.join(patterns.get('active_domains', []))}")
    if patterns.get("recurring_domains"):
        parts.append(f"Recurring Domains: {', '.join(patterns.get('recurring_domains', []))}")

    return "\n".join(parts)


def format_dynamics_for_prompt(dynamics: dict) -> str:
    """Render the aggregated forum dynamics context as a compact prompt block."""
    parts: List[str] = []

    member_count = dynamics.get("member_count", 0)
    parts.append(f"Forum has {member_count} active member(s)")

    hd_dist = dynamics.get("hd_type_distribution", {})
    if hd_dist:
        hd_summary = ", ".join([f"{k}: {v}" for k, v in hd_dist.items()])
        parts.append(f"Human Design Types: {hd_summary}")

    auth_dist = dynamics.get("hd_authority_distribution", {})
    if auth_dist:
        auth_summary = ", ".join([f"{k}: {v}" for k, v in auth_dist.items()])
        parts.append(f"Authorities: {auth_summary}")

    enne_dist = dynamics.get("enneagram_distribution", {})
    if enne_dist:
        enne_summary = ", ".join([f"Type {k}: {v}" for k, v in enne_dist.items()])
        parts.append(f"Enneagram Types: {enne_summary}")

    elem_dist = dynamics.get("astrology_elements", {})
    if elem_dist:
        elem_summary = ", ".join([f"{k}: {v}" for k, v in elem_dist.items()])
        parts.append(f"Dominant Elements: {elem_summary}")

    pattern_domains = dynamics.get("active_pattern_domains", [])
    if pattern_domains:
        domain_names = [d.get("domain", "") for d in pattern_domains[:5]]
        parts.append(f"Active Pattern Domains: {', '.join(domain_names)}")

    defined_centers = dynamics.get("defined_centers_coverage", {})
    if defined_centers:
        coverage = ", ".join([f"{k}({v})" for k, v in list(defined_centers.items())[:5]])
        parts.append(f"Center Coverage (defined): {coverage}")

    return "\n".join(parts)
