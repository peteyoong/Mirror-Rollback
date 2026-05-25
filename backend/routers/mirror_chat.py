"""
Mirror Chat route  (server-router-refactor-v8)
==============================================

Behaviour-preserving extraction of the primary `/api/mirror/chat`
endpoint from server.py.  All paths, request/response schemas,
prompts, debug payloads, log lines, and persistence ordering are
byte-identical to the inline implementation.

Endpoint attached here:

    POST   /api/mirror/chat        (response_model=MirrorChatResponse)

NOT moved in v8 (left in server.py because it shares the in-memory
`chat_sessions` dict which lives at server.py module scope):

    DELETE /api/mirror/chat/{session_id}

Pipeline stages (lens / life-domain / relational / pattern-memory /
micro-reflection / contradiction) continue to be served from
`services.mirror_chat_pipeline` — this router does NOT duplicate any
of that logic.

Call signature:

    mirror_chat.register(api_router, db, logger, emergent_llm_key)

All other dependencies (models, prompt constants, rate-limit helpers,
chart migration helper, sign/cross helpers, the shared chat_sessions
dict) are imported late from `server` inside `register()`.  This is
safe because `register()` is invoked by server.py AFTER those
module-level symbols are defined — same pattern used implicitly by
the rest of the refactor (no circular-import risk).
"""

# NOTE: deliberately NOT using `from __future__ import annotations` here.
# The route handler signature uses `MirrorChatRequest` which is imported
# inside register() (late-binding from server.py to avoid circular import).
# PEP 563 string-annotations would turn the type hint into a literal
# string that typing.get_type_hints() then can't resolve, because the
# router module's globals don't contain `MirrorChatRequest`.  FastAPI
# would silently downgrade the body param to a query param and every
# request would 422 with loc=["query","request"].  Keeping eager
# annotation evaluation ensures FastAPI sees the actual Pydantic model
# at function-definition time (inside register(), where the late import
# has just put `MirrorChatRequest` in scope).

import asyncio
import json
import re
import time
import traceback
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException

from emergentintegrations.llm.chat import LlmChat, UserMessage
from llm_model_config import get_primary_model


# ---------------------------------------------------------------------------
# register() — attach the /mirror/chat POST route onto api_router.
# ---------------------------------------------------------------------------

def register(
    api_router: APIRouter,
    db,
    logger,
    emergent_llm_key: Optional[str],
) -> None:
    # Late-bind server-level symbols.  Done inside register() so this
    # module can be imported by server.py without a circular import
    # at module-load time.  By the time server.py calls .register(),
    # every name below is already defined at server.py module scope.
    from server import (
        MirrorChatRequest,
        MirrorChatResponse,
        MemoryUpdate,
        MIRROR_SYSTEM_PROMPT,
        LENS_PROMPTS,
        KEYSTONE_CONTINUATION_INSERT,
        THREAD_ANCHOR_INSERT,
        MEMORY_UPDATE_PROMPT,
        MAX_JOURNAL_ENTRIES,
        MAX_CHAT_HISTORY,
        check_rate_limit,
        get_rate_limit_remaining,
        check_and_migrate_astrology_chart,
        get_opposite_sign,
        get_incarnation_cross_label,
        chat_sessions,
    )

    # Allow the local `EMERGENT_LLM_KEY` name to mirror the in-line
    # version so the function body below remains byte-identical.
    EMERGENT_LLM_KEY = emergent_llm_key

    # ──────────────────────────────────────────────────────────────────
    # POST /api/mirror/chat
    # ──────────────────────────────────────────────────────────────────

    @api_router.post("/mirror/chat", response_model=MirrorChatResponse)
    async def mirror_chat(request: MirrorChatRequest):
        """
        Mirror Chat - The reflective companion AI.

        - lens=None: Generalist mode (integrates all lenses)
        - lens="astrology": Constrained to astrology lens
        - lens="human_design": Constrained to Human Design lens
        - lens="numerology": Constrained to numerology lens
        """
        import time
        request_start = time.time()
        logger.info(f"[MIRROR_CHAT] === REQUEST RECEIVED === user_id={request.user_id}, lens={request.lens}, message_length={len(request.message) if request.message else 0}")

        is_lens = request.lens is not None

        # ===== RATE LIMITING =====
        if not check_rate_limit(request.user_id, is_lens):
            remaining = get_rate_limit_remaining(request.user_id, is_lens)
            limit_type = "lens" if is_lens else "mirror"
            logger.warning(f"[MIRROR_CHAT] Rate limit exceeded for user {request.user_id}, type={limit_type}")
            raise HTTPException(
                status_code=429,
                detail="Mirror needs a pause. Try again in a little while."
            )

        try:
            if not EMERGENT_LLM_KEY:
                logger.error("[MIRROR_CHAT] EMERGENT_LLM_KEY not configured!")
                raise HTTPException(status_code=500, detail="AI service not configured")

            logger.info(f"[MIRROR_CHAT] EMERGENT_LLM_KEY present: {bool(EMERGENT_LLM_KEY)}, length: {len(EMERGENT_LLM_KEY) if EMERGENT_LLM_KEY else 0}")

            # Generate or use existing session ID
            session_id = request.session_id or str(uuid.uuid4())

            # Get user's chart data for context
            logger.info("[MIRROR_CHAT] Fetching user and chart data...")
            user = await db.users.find_one({"_id": ObjectId(request.user_id)})
            chart = await db.charts.find_one({"user_id": request.user_id})

            if not user:
                logger.error(f"[MIRROR_CHAT] User not found: {request.user_id}")
                raise HTTPException(status_code=404, detail="User not found")

            logger.info(f"[MIRROR_CHAT] User found: {user.get('name', 'Unknown')}, chart exists: {chart is not None}")

            # Auto-migrate chart if needed (e.g., missing nodes)
            if chart and (request.lens == "astrology" or request.lens is None):
                try:
                    migration_performed, migration_status, migrated_chart = await check_and_migrate_astrology_chart(request.user_id)
                    if migration_performed:
                        logger.info(f"[MIRROR_CHAT] Auto-migrated chart for user {request.user_id}: {migration_status}")
                        chart = migrated_chart
                except Exception as e:
                    logger.error(f"[MIRROR_CHAT] Migration check failed for user {request.user_id}: {e}")

            # Build context from chart data
            context_parts = []

            # User basics
            context_parts.append(f"User's name: {user.get('name', 'Unknown')}")
            context_parts.append(f"Birth date: {user.get('birth_date')}")

            if chart:
                # Astrology context
                astro = chart.get('astrology', {})
                if astro and (request.lens is None or request.lens == "astrology"):
                    planets = astro.get('planets', {})
                    sun = planets.get('Sun', {})
                    moon = planets.get('Moon', {})
                    houses = astro.get('houses', {})
                    rising = houses.get('formatted_cusps', [{}])[0] if houses.get('formatted_cusps') else {}

                    context_parts.append("\n--- ASTROLOGY (True Sidereal) ---")
                    context_parts.append(f"Sun: {sun.get('formatted', 'Unknown')} ({sun.get('sign', 'Unknown')})")
                    context_parts.append(f"Moon: {moon.get('formatted', 'Unknown')} ({moon.get('sign', 'Unknown')})")
                    context_parts.append(f"Rising: {rising.get('formatted', 'Unknown')} ({rising.get('sign', 'Unknown')})")

                    # Add other planets if in astrology lens
                    if request.lens == "astrology":
                        for planet_name in ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']:
                            planet = planets.get(planet_name, {})
                            if planet:
                                context_parts.append(f"{planet_name}: {planet.get('formatted', 'Unknown')}")

                        # DEBUG: Log Neptune source for data integrity verification
                        neptune_data = planets.get('Neptune', {})
                        svp_used = chart.get('debug_stamp', {}).get('sidereal_settings_used', {}).get('svp_degrees', 'unknown')
                        logger.info(f"[MIRROR_CHAT] Neptune source=stored_chart, sign={neptune_data.get('sign')}, degree={neptune_data.get('degree', 0):.2f}, lon={neptune_data.get('longitude', 0):.2f}, SVP={svp_used}")

                        # Add Lunar Nodes - CRITICAL for complete astrology readings
                        nodes = astro.get('nodes', {})
                        north_node = nodes.get('north', {})
                        south_node = nodes.get('south', {})

                        if north_node and north_node.get('sign'):
                            context_parts.append(f"North Node: {north_node.get('formatted', north_node.get('sign', 'Unknown'))} (House {north_node.get('house', 'Unknown')})")
                        if south_node and south_node.get('sign'):
                            context_parts.append(f"South Node: {south_node.get('formatted', south_node.get('sign', 'Unknown'))} (House {south_node.get('house', 'Unknown')})")

                        # If nodes not in new format, check legacy formats
                        if not north_node.get('sign'):
                            # Check lunar_nodes format
                            lunar_nodes = astro.get('lunar_nodes', {})
                            if lunar_nodes:
                                nn = lunar_nodes.get('north_node', {}) or lunar_nodes.get('north', {})
                                sn = lunar_nodes.get('south_node', {}) or lunar_nodes.get('south', {})
                                if nn.get('sign'):
                                    context_parts.append(f"North Node: {nn.get('sign')} ({nn.get('degree', 0):.0f}°)")
                                if sn.get('sign'):
                                    context_parts.append(f"South Node: {sn.get('sign')} ({sn.get('degree', 0):.0f}°)")
                            else:
                                # Check if North Node is in planets
                                nn_planet = planets.get('North Node', {}) or planets.get('True Node', {}) or planets.get('GC', {})
                                if nn_planet.get('sign'):
                                    context_parts.append(f"North Node: {nn_planet.get('formatted', nn_planet.get('sign', 'Unknown'))}")
                                    # Calculate South Node
                                    south_sign = get_opposite_sign(nn_planet.get('sign', ''))
                                    if south_sign:
                                        context_parts.append(f"South Node: {south_sign}")

                # Human Design context
                hd = chart.get('human_design', {})
                if hd and (request.lens is None or request.lens == "human_design"):
                    context_parts.append("\n--- HUMAN DESIGN ---")
                    context_parts.append(f"Type: {hd.get('type', 'Unknown')}")
                    context_parts.append(f"Strategy: {hd.get('strategy', 'Unknown')}")
                    context_parts.append(f"Authority: {hd.get('authority', 'Unknown')}")
                    context_parts.append(f"Profile: {hd.get('profile', 'Unknown')}")
                    context_parts.append(f"Definition: {hd.get('definition', 'Unknown')}")

                    # Incarnation Cross - IMPORTANT: Include full details
                    inc_cross = hd.get('incarnation_cross', 'Unknown')
                    inc_cross_gates = hd.get('incarnation_cross_gates', '')
                    if inc_cross and inc_cross != 'Unknown':
                        # Get the named cross using the helper function
                        named_cross = get_incarnation_cross_label(inc_cross)
                        context_parts.append(f"Incarnation Cross: {named_cross}")
                        if inc_cross_gates:
                            context_parts.append(f"Incarnation Cross Gates: {inc_cross_gates}")

                    # Defined Centers if available
                    defined_centers = hd.get('defined_centers', [])
                    if defined_centers:
                        context_parts.append(f"Defined Centers: {', '.join(defined_centers)}")

                    # Defined Channels if available
                    defined_channels = hd.get('defined_channels', [])
                    if defined_channels:
                        # Handle both string and dict formats for channels
                        channel_strs = []
                        for channel in defined_channels[:5]:  # Limit to first 5
                            if isinstance(channel, dict):
                                gate1 = channel.get('gate1', '')
                                gate2 = channel.get('gate2', '')
                                channel_strs.append(f"{gate1}-{gate2}")
                            else:
                                channel_strs.append(str(channel))
                        context_parts.append(f"Defined Channels: {', '.join(channel_strs)}")

                # Numerology context
                numerology = chart.get('numerology', {})
                if numerology and (request.lens is None or request.lens == "numerology"):
                    # Extract life path (handle both old and new format)
                    life_path_data = numerology.get('life_path')
                    if isinstance(life_path_data, int):
                        life_path = life_path_data
                    elif isinstance(life_path_data, dict):
                        life_path = life_path_data.get('number', 'Unknown')
                    else:
                        life_path = 'Unknown'

                    context_parts.append("\n--- NUMEROLOGY ---")
                    context_parts.append(f"Life Path: {life_path}")

                    # Birthday number if available
                    birthday = numerology.get('birthday')
                    if birthday:
                        if isinstance(birthday, dict):
                            context_parts.append(f"Birthday Number: {birthday.get('number', 'Unknown')}")
                        else:
                            context_parts.append(f"Birthday Number: {birthday}")

                    # Name-based numbers (only if available)
                    has_name_numbers = numerology.get('has_name_numbers', False)
                    if has_name_numbers:
                        expression = numerology.get('expression')
                        soul_urge = numerology.get('soul_urge')
                        personality = numerology.get('personality')

                        if expression:
                            exp_num = expression.get('number') if isinstance(expression, dict) else expression
                            context_parts.append(f"Expression: {exp_num}")
                        if soul_urge:
                            su_num = soul_urge.get('number') if isinstance(soul_urge, dict) else soul_urge
                            context_parts.append(f"Soul Urge: {su_num}")
                        if personality:
                            pers_num = personality.get('number') if isinstance(personality, dict) else personality
                            context_parts.append(f"Personality: {pers_num}")
                    else:
                        context_parts.append("Expression/Soul Urge/Personality: Not provided (requires full birth name)")

                    # Calculate current cycles for numerology lens
                    if request.lens == "numerology":
                        birth_date = user.get('birth_date')
                        if birth_date:
                            from calculations.numerology import get_numerology_cycles
                            today = datetime.now()
                            cycles = get_numerology_cycles(birth_date, today)

                            context_parts.append("\n--- CURRENT CYCLES ---")
                            context_parts.append(f"Personal Year: {cycles['personal_year']['number']} ({cycles['personal_year']['description']})")
                            context_parts.append(f"Personal Month: {cycles['personal_month']['number']} ({cycles['personal_month']['description']})")
                            context_parts.append(f"Personal Day: {cycles['personal_day']['number']} ({cycles['personal_day']['description']})")

                # Enneagram context
                enneagram_results = await db.enneagram_results.find_one({"user_id": request.user_id})
                if enneagram_results and (request.lens is None or request.lens == "enneagram"):
                    context_parts.append("\n--- ENNEAGRAM ---")
                    core_type = enneagram_results.get('core_type', 'Unknown')
                    wing = enneagram_results.get('wing', '')
                    confidence = enneagram_results.get('confidence', 0)
                    computed = enneagram_results.get('enneagram_computed_details', {})

                    # Type names for readability
                    type_names = {
                        "1": "Reformer", "2": "Helper", "3": "Achiever", "4": "Individualist",
                        "5": "Investigator", "6": "Loyalist", "7": "Enthusiast", "8": "Challenger", "9": "Peacemaker"
                    }
                    type_name = type_names.get(str(core_type), "Unknown")

                    context_parts.append(f"Core Type: {core_type} ({type_name})")
                    if wing:
                        context_parts.append(f"Wing: {wing}")
                    context_parts.append(f"Confidence: {confidence:.0%}" if isinstance(confidence, float) else f"Confidence: {confidence}")

                    # Add instinctual variants if available
                    instincts = computed.get('instinctual_stack', computed.get('dominant_instinct', ''))
                    if instincts:
                        context_parts.append(f"Instinctual Stack: {instincts}")

                    # Add tritype if available
                    tritype = computed.get('tritype', '')
                    if tritype:
                        context_parts.append(f"Tritype: {tritype}")

                # ===== BAZI CONTEXT =====
                # Load computed BaZi chart for BaZi lens or generalist mode
                if request.lens is None or request.lens == "bazi":
                    try:
                        birth_date = user.get("birth_date")
                        birth_time = user.get("birth_time")
                        user_tz = user.get("timezone")

                        if birth_date:
                            from services.bazi_engine_v2 import compute_bazi_chart_v2
                            from services.bazi_insight_layer import transform_bazi_to_insight_first

                            bazi_chart = compute_bazi_chart_v2(
                                birth_date=birth_date,
                                birth_time=birth_time,
                                timezone=user_tz,
                                include_timing=True
                            )

                            if bazi_chart:
                                context_parts.append("\n--- BAZI (Chinese Astrology) ---")
                                context_parts.append("[CHART ALREADY COMPUTED - DO NOT ASK FOR BIRTH DATA]")

                                # Day Master info
                                dm = bazi_chart.get('day_master', {})
                                dm_element = dm.get('element', 'Unknown')
                                dm_polarity = dm.get('polarity', 'Unknown')
                                dm_strength = dm.get('strength', 'Unknown')
                                dm_chinese = dm.get('chinese_name', '')

                                context_parts.append(f"Day Master: {dm_polarity} {dm_element} ({dm_chinese})")
                                context_parts.append(f"Day Master Strength: {dm_strength}")

                                # Four Pillars
                                pillars = bazi_chart.get('pillars', {})
                                if pillars:
                                    context_parts.append("\nFour Pillars:")
                                    for pillar_name in ['year', 'month', 'day', 'hour']:
                                        p = pillars.get(pillar_name, {})
                                        if p:
                                            stem = p.get('stem_pinyin', '')
                                            branch = p.get('branch_pinyin', '')
                                            context_parts.append(f"  {pillar_name.capitalize()}: {stem} {branch}")

                                # Deep dive structures
                                deep_dive = bazi_chart.get('deep_dive', {})
                                if deep_dive:
                                    # Ten Gods
                                    ten_gods = deep_dive.get('ten_gods_detailed', [])
                                    if ten_gods:
                                        high_strength = [g.get('label', g.get('name', '')) for g in ten_gods if g.get('strength') in ['high', 'moderate']][:3]
                                        if high_strength:
                                            context_parts.append(f"\nDominant Ten Gods: {', '.join(high_strength)}")

                                    # Favorable/Unfavorable elements
                                    favorable = deep_dive.get('favorable_elements', [])
                                    unfavorable = deep_dive.get('unfavorable_elements', [])
                                    if favorable:
                                        context_parts.append(f"Favorable Elements: {', '.join(favorable)}")
                                    if unfavorable:
                                        context_parts.append(f"Draining Elements: {', '.join(unfavorable)}")

                                # Current timing (if available)
                                timing = bazi_chart.get('timing', {})
                                if timing:
                                    today = timing.get('today', {})
                                    if today:
                                        context_parts.append("\nCurrent Timing:")
                                        today_element = today.get('element', '')
                                        today_interaction = today.get('interaction', '')
                                        today_ten_god = today.get('ten_god_name', '')
                                        if today_element:
                                            context_parts.append(f"  Today's Energy: {today_element} ({today_interaction})")
                                        if today_ten_god:
                                            context_parts.append(f"  Today's Ten God: {today_ten_god}")

                                # Add insight summary if in bazi lens
                                if request.lens == "bazi":
                                    try:
                                        insight = transform_bazi_to_insight_first(
                                            day_master_element=dm_element,
                                            day_master_polarity=dm_polarity,
                                            day_master_strength=dm_strength,
                                            life_pattern=deep_dive.get('life_pattern', {}),
                                            ten_gods_detailed=deep_dive.get('ten_gods_detailed', []),
                                            timing=timing,
                                            pillars=pillars,
                                            favorable_elements=deep_dive.get('favorable_elements', []),
                                            unfavorable_elements=deep_dive.get('unfavorable_elements', []),
                                        )

                                        core_truth = insight.get('core_truth', {})
                                        if core_truth:
                                            context_parts.append(f"\nCore Pattern: {core_truth.get('line1', '')} {core_truth.get('line2', '')}")

                                        genius = insight.get('genius', {})
                                        if genius:
                                            context_parts.append(f"Genius: {genius.get('line1', '')}")
                                    except Exception as insight_err:
                                        logger.debug(f"[BAZI_CHAT] Could not generate insight: {insight_err}")

                                logger.info(f"[BAZI_CHAT] Loaded BaZi context for user {request.user_id}: DM={dm_polarity} {dm_element}, strength={dm_strength}")
                            else:
                                context_parts.append("\n--- BAZI ---")
                                context_parts.append("[BaZi chart computation incomplete - birth date available but chart not computed]")
                        else:
                            if request.lens == "bazi":
                                context_parts.append("\n--- BAZI ---")
                                context_parts.append("[No birth date available - BaZi chart cannot be computed]")

                    except Exception as bazi_err:
                        logger.error(f"[BAZI_CHAT] Error loading BaZi context: {bazi_err}")
                        if request.lens == "bazi":
                            context_parts.append("\n--- BAZI ---")
                            context_parts.append(f"[BaZi context loading error]")

            # Add recent journal entries if requested (LIMITED to MAX_JOURNAL_ENTRIES)
            if request.include_journal:
                journal_entries = await db.journal.find(
                    {"user_id": request.user_id}
                ).sort("timestamp", -1).limit(MAX_JOURNAL_ENTRIES).to_list(MAX_JOURNAL_ENTRIES)

                if journal_entries:
                    context_parts.append("\n--- RECENT JOURNAL ENTRIES ---")
                    for entry in reversed(journal_entries):  # Show oldest first
                        timestamp = entry.get('timestamp', datetime.now())
                        if isinstance(timestamp, str):
                            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        date_str = timestamp.strftime("%Y-%m-%d %H:%M")
                        content = entry.get('content', '')[:300]  # Truncate long entries
                        context_parts.append(f"[{date_str}] {content}")

            # ===== GENE KEYS PATTERN MATCHING =====
            # Load Gene Keys profile and match against user's message for subtle context awareness
            gene_keys_context = ""
            try:
                from services.gene_keys_matcher import (
                    match_gene_keys_to_message,
                    build_gene_keys_chat_context,
                    log_gene_keys_match_debug
                )

                # Only run matching for generalist mode or human_design lens
                if request.lens is None or request.lens == "human_design":
                    # Try to load Gene Keys profile (reuse the profile endpoint logic)
                    gk_profile = None
                    try:
                        birth_date = user.get("birth_date")
                        birth_time = user.get("birth_time")
                        gk_timezone = user.get("timezone", "UTC")
                        birth_location = user.get("birth_location", {})

                        if isinstance(birth_location, dict):
                            gk_lat = birth_location.get("latitude")
                            gk_lon = birth_location.get("longitude")
                        else:
                            gk_lat = user.get("latitude") or user.get("birth_lat")
                            gk_lon = user.get("longitude") or user.get("birth_lon")

                        if all([birth_date, birth_time, gk_lat, gk_lon]):
                            from calculations.timezone_utils import resolve_birth_utc_with_debug
                            from calculations.human_design import get_human_design_chart
                            from services.gene_keys_interpreter import build_gene_keys_profile

                            if hasattr(birth_date, 'strftime'):
                                gk_birth_date_str = birth_date.strftime("%Y-%m-%d")
                            else:
                                gk_birth_date_str = str(birth_date).split(' ')[0]

                            gk_result = resolve_birth_utc_with_debug(gk_birth_date_str, birth_time, gk_timezone)
                            gk_birth_utc = gk_result.get('birth_utc')

                            if gk_birth_utc:
                                # Compute HD chart for Gene Keys
                                gk_hd = get_human_design_chart(
                                    birth_datetime=gk_birth_utc,
                                    lat=float(gk_lat),
                                    lon=float(gk_lon)
                                )

                                personality = gk_hd.get('personality', {})
                                design = gk_hd.get('design', {})

                                def gk_extract(planet_data):
                                    gate_data = planet_data.get('gate', {})
                                    if isinstance(gate_data, dict):
                                        return gate_data.get('gate', 1), gate_data.get('line', 1)
                                    return 1, 1

                                # Build profile
                                gk_profile = build_gene_keys_profile(
                                    personality_sun_gate=gk_extract(personality.get('Sun', {}))[0],
                                    personality_sun_line=gk_extract(personality.get('Sun', {}))[1],
                                    personality_earth_gate=gk_extract(personality.get('Earth', {}))[0],
                                    personality_earth_line=gk_extract(personality.get('Earth', {}))[1],
                                    design_sun_gate=gk_extract(design.get('Sun', {}))[0],
                                    design_sun_line=gk_extract(design.get('Sun', {}))[1],
                                    design_earth_gate=gk_extract(design.get('Earth', {}))[0],
                                    design_earth_line=gk_extract(design.get('Earth', {}))[1],
                                    design_moon_gate=gk_extract(design.get('Moon', {}))[0],
                                    design_moon_line=gk_extract(design.get('Moon', {}))[1],
                                    personality_mercury_gate=gk_extract(personality.get('Mercury', {}))[0],
                                    personality_mercury_line=gk_extract(personality.get('Mercury', {}))[1],
                                    design_mercury_gate=gk_extract(design.get('Mercury', {}))[0],
                                    design_mercury_line=gk_extract(design.get('Mercury', {}))[1],
                                    design_venus_gate=gk_extract(design.get('Venus', {}))[0],
                                    design_venus_line=gk_extract(design.get('Venus', {}))[1],
                                    personality_mars_gate=gk_extract(personality.get('Mars', {}))[0],
                                    personality_mars_line=gk_extract(personality.get('Mars', {}))[1],
                                    design_mars_gate=gk_extract(design.get('Mars', {}))[0],
                                    design_mars_line=gk_extract(design.get('Mars', {}))[1],
                                    personality_jupiter_gate=gk_extract(personality.get('Jupiter', {}))[0],
                                    personality_jupiter_line=gk_extract(personality.get('Jupiter', {}))[1],
                                    design_jupiter_gate=gk_extract(design.get('Jupiter', {}))[0],
                                    design_jupiter_line=gk_extract(design.get('Jupiter', {}))[1],
                                )
                    except Exception as gk_load_err:
                        logger.debug(f"[GK_MATCH] Could not load Gene Keys profile: {gk_load_err}")

                    # Run matching if we have a profile
                    if gk_profile and gk_profile.get('all_spheres'):
                        match_result = match_gene_keys_to_message(
                            user_message=request.message,
                            all_spheres=gk_profile['all_spheres'],
                            min_keyword_matches=1,
                            max_results=2
                        )

                        # Log debug info (dev-only)
                        log_gene_keys_match_debug(
                            user_id=request.user_id,
                            message_preview=request.message,
                            match_result=match_result
                        )

                        # Build context if match found
                        if match_result['has_match']:
                            gene_keys_context = build_gene_keys_chat_context(match_result)
                            logger.info(f"[GK_MATCH] Added Gene Keys context for user {request.user_id}")

            except Exception as gk_err:
                logger.debug(f"[GK_MATCH] Gene Keys matching skipped: {gk_err}")

            # Build system prompt
            system_prompt = MIRROR_SYSTEM_PROMPT

            # ===== V1: PREFERENCE FEEDBACK LOOP =====
            # Apply user's experience preferences to chat immediately
            if user:
                v1_tone = user.get('v1_tone', 'calm')
                v1_depth = user.get('v1_depth', 'balanced')
                v1_support = user.get('v1_support_style', 'work_with')

                preference_insert = f"""
--- EXPERIENCE PREFERENCES (V1) ---

The user has configured their experience preferences. Apply these IMMEDIATELY:

TONE: {v1_tone}
"""
                if v1_tone == 'direct':
                    preference_insert += """- Be clear, no padding
- Shorter sentences
- Get to the point quickly
- Example: "You already know what's off here."
"""
                elif v1_tone == 'calm':
                    preference_insert += """- Steady, less intense
- More space between ideas
- Soft but clear
- Example: "Take a breath. Something here still doesn't feel settled."
"""
                elif v1_tone == 'grounded':
                    preference_insert += """- Practical phrasing
- Less emotional
- Action-oriented
- Example: "This isn't ready yet. Slow it down."
"""
                elif v1_tone == 'confronting':
                    preference_insert += """- Sharper pattern exposure
- More direct about consequences
- Don't soften the truth
- Example: "You're about to do the thing that keeps costing you."
"""

                preference_insert += f"""
DEPTH: {v1_depth}
"""
                if v1_depth == 'light':
                    preference_insert += """- Shorter responses
- Just enough to notice
- Get in and out quickly
"""
                elif v1_depth == 'balanced':
                    preference_insert += """- Enough to work with
- Not overwhelming
- Standard depth
"""
                elif v1_depth == 'deep':
                    preference_insert += """- More pattern exploration
- More reflection prompts
- Allow multi-turn deepening
"""

                preference_insert += f"""
SUPPORT STYLE: {v1_support}
"""
                if v1_support == 'interrupt':
                    preference_insert += """- Catch patterns quickly
- More interception
- Don't let them loop
"""
                elif v1_support == 'work_with':
                    preference_insert += """- More actionable guidance
- Practical support
- Help them move through it
"""
                elif v1_support == 'explore':
                    preference_insert += """- Deeper engagement
- More reflection
- More space to explore
"""

                system_prompt += "\n" + preference_insert
                logger.debug(f"[MIRROR_CHAT] Applied V1 preferences for user {request.user_id}: tone={v1_tone}, depth={v1_depth}, support={v1_support}")

            # Add lens-specific prompt if constrained
            if request.lens and request.lens in LENS_PROMPTS:
                system_prompt += "\n" + LENS_PROMPTS[request.lens]

            # ===== KEYSTONE THREAD MODE =====
            is_keystone_followup = request.keystone_context is not None
            thread_state = None
            current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

            if is_keystone_followup:
                # Starting or restarting a keystone thread
                kc = request.keystone_context
                keystone_insert = KEYSTONE_CONTINUATION_INSERT.format(
                    title=kc.title,
                    keystone=kc.keystone,
                    reflect_question=kc.reflect_question,
                    micro_affirmation=kc.micro_affirmation,
                    tone=kc.tone
                )
                system_prompt += "\n" + keystone_insert
                logger.info(f"[Mirror Chat] Keystone continuation mode for user {request.user_id}, date={kc.date}")

                # Create/overwrite thread state with remaining_turns=3
                thread_state = {
                    "user_id": request.user_id,
                    "thread_type": "daily_keystone",
                    "thread_date": kc.date,
                    "daily_seed": kc.daily_seed,
                    "tone": kc.tone,
                    "title": kc.title,
                    "keystone": kc.keystone,
                    "reflect_question": kc.reflect_question,
                    "micro_affirmation": kc.micro_affirmation,
                    "remaining_turns": 3,  # Will be decremented after reply
                    "created_at_iso": datetime.now(timezone.utc).isoformat(),
                    "updated_at_iso": datetime.now(timezone.utc).isoformat()
                }

                await db.user_thread_state.update_one(
                    {"user_id": request.user_id},
                    {"$set": thread_state},
                    upsert=True
                )
                logger.info(f"[Thread] Created keystone thread for user {request.user_id}, remaining_turns=3")

            elif request.lens is None:
                # Check for active thread state (only for generalist chat, not lens chats)
                existing_thread = await db.user_thread_state.find_one({"user_id": request.user_id})

                if existing_thread and existing_thread.get("remaining_turns", 0) > 0:
                    # Verify it's for today's date
                    if existing_thread.get("thread_date") == current_date:
                        thread_state = existing_thread
                        turn_number = 4 - thread_state["remaining_turns"]  # 1, 2, or 3

                        # Inject thread anchor prompt
                        thread_anchor = THREAD_ANCHOR_INSERT.format(
                            tone=thread_state.get("tone", "unclear"),
                            turn_number=turn_number
                        )
                        system_prompt += "\n" + thread_anchor
                        logger.info(f"[Thread] Active thread for user {request.user_id}, turn={turn_number}, remaining={thread_state['remaining_turns']}")
                    else:
                        # Thread is from a different day, clear it
                        await db.user_thread_state.delete_one({"user_id": request.user_id})
                        logger.info(f"[Thread] Cleared stale thread for user {request.user_id} (date mismatch)")

            # Add context
            system_prompt += "\n\n--- USER CONTEXT ---\n" + "\n".join(context_parts)

            # ===== V1: PATTERN THREAD CONTEXT FOR LENS → CHAT CONTINUITY =====
            if request.pattern_thread_context:
                ptc = request.pattern_thread_context
                thread_context_parts = []

                # Build continuity context
                source = ptc.get('source_surface', 'lens')
                thread_context_parts.append(f"User just came from: {source}")

                if ptc.get('core_truth'):
                    thread_context_parts.append(f"Active pattern (core truth): {ptc['core_truth']}")

                if ptc.get('echo'):
                    thread_context_parts.append(f"Recurrence signal: {ptc['echo']}")

                if ptc.get('cross_link'):
                    thread_context_parts.append(f"Cross-lens link: {ptc['cross_link']}")

                if ptc.get('memory_line'):
                    thread_context_parts.append(f"Memory: {ptc['memory_line']}")

                if ptc.get('current_shift'):
                    thread_context_parts.append(f"Suggested shift: {ptc['current_shift']}")

                if ptc.get('genius'):
                    thread_context_parts.append(f"Genius insight: {ptc['genius']}")

                # Add continuity instruction
                pattern_thread_insert = """
--- PATTERN THREAD CONTINUITY (V1) ---

The user has arrived from a lens view where they were already seeing a specific pattern.

{context}

CONTINUITY RULES:
1. Acknowledge continuity in your first response: "You've already seen this pattern once today." or "This same thing is showing up here too." or "Alright. Let's stay with the same thread."
2. Do NOT restart from a generic assistant mode
3. Do NOT ask broad opening questions
4. Continue the same pattern thread, not a new conversation
5. After the continuity acknowledgment, proceed with Mirror Chat mode (interrupt or support)

The user should feel: "Mirror is continuing the same conversation"
NOT: "I opened a generic chat"
""".format(context="\n".join(thread_context_parts))

                system_prompt += "\n" + pattern_thread_insert
                logger.info(f"[MIRROR_CHAT] Pattern thread context injected from {source} for user {request.user_id}")

            # Add Gene Keys pattern awareness context (if match found)
            if gene_keys_context:
                system_prompt += "\n" + gene_keys_context

            # Get or create chat history for session
            if session_id not in chat_sessions:
                chat_sessions[session_id] = []

            history = chat_sessions[session_id]

            # =====================================================================
            # MULTI-LENS CONVERSATIONAL MEMORY (multi-lens-chat-memory-v1)
            # ---------------------------------------------------------------------
            # v7: hoisted into services.mirror_chat_pipeline.build_lens_context.
            # Behaviour unchanged — same registry resolution, same prompt block,
            # same debug payload.
            # =====================================================================
            from services.mirror_chat_pipeline import (
                build_lens_context as _build_lens_context,
                build_life_domain_context as _build_life_domain_context,
                build_relational_context as _build_relational_context,
                build_pattern_memory_context as _build_pattern_memory_context,
                build_micro_reflection_context as _build_micro_reflection_context,
                build_contradiction_context as _build_contradiction_context,
            )

            _locals = locals()
            # Numerology cycles are computed inline above only when lens=numerology.
            _numerology_cycles = None
            if request.lens == "numerology":
                try:
                    _bd = user.get('birth_date') if user else None
                    if _bd:
                        from calculations.numerology import get_numerology_cycles
                        _numerology_cycles = get_numerology_cycles(_bd, datetime.now())
                except Exception:
                    pass

            memory_block, lens_debug_payload = await _build_lens_context(
                lens=request.lens,
                user=user,
                chart=chart,
                enneagram_results=_locals.get("enneagram_results"),
                bazi_chart=_locals.get("bazi_chart"),
                numerology_cycles=_numerology_cycles,
                user_message=request.message,
                history=history,
                user_id=request.user_id,
            )
            if memory_block:
                system_prompt += "\n\n" + memory_block

            # =====================================================================
            # LIFE TAB MASTER VOICE (life-tab-master-voice-v1)
            # ---------------------------------------------------------------------
            # v7: hoisted into services.mirror_chat_pipeline.build_life_domain_context.
            # =====================================================================
            mv_block, master_voice_debug_payload = await _build_life_domain_context(
                life_domain=request.life_domain,
                lens=request.lens,
                user=user,
                chart=chart,
                enneagram_results=_locals.get("enneagram_results"),
                bazi_chart=_locals.get("bazi_chart"),
                user_message=request.message,
                history=history,
            )
            if mv_block:
                system_prompt += "\n\n" + mv_block

            # =====================================================================
            # RELATIONAL AWARENESS (relational-awareness-v1)
            # ---------------------------------------------------------------------
            # v7: hoisted into services.mirror_chat_pipeline.build_relational_context.
            # NOTE: this stage may MUTATE lens_debug_payload in place to reflect
            # an intensity cap — same behaviour as the inline version.
            # =====================================================================
            rel_block, relational_debug_payload = await _build_relational_context(
                db=db,
                user_id=request.user_id,
                about_person_id=request.about_person_id,
                user_message=request.message,
                history=history,
                lens_debug_payload=lens_debug_payload,
            )
            if rel_block:
                system_prompt += "\n\n" + rel_block

            # =====================================================================
            # LONGITUDINAL PATTERN MEMORY (pattern-memory-v1)
            # ---------------------------------------------------------------------
            # v7: hoisted into services.mirror_chat_pipeline.build_pattern_memory_context.
            # =====================================================================
            pattern_block, pattern_debug_payload = await _build_pattern_memory_context(
                db=db,
                user_id=request.user_id,
                user_message=request.message,
                lens=request.lens,
                lens_debug_payload=lens_debug_payload,
            )
            if pattern_block:
                system_prompt += "\n\n" + pattern_block

            # =====================================================================
            # MICRO-REFLECTION v2  (micro-reflection-v2)
            # ---------------------------------------------------------------------
            # v7: hoisted into services.mirror_chat_pipeline.build_micro_reflection_context.
            # =====================================================================
            r_block, reflection_debug_payload = await _build_micro_reflection_context(
                db=db, user_id=request.user_id,
            )
            if r_block:
                system_prompt += "\n\n" + r_block

            # =====================================================================
            # CONTRADICTION INTELLIGENCE v1 (contradiction-intelligence-v1)
            # ---------------------------------------------------------------------
            # v7: hoisted into services.mirror_chat_pipeline.build_contradiction_context.
            # =====================================================================
            _c_block, contradiction_debug_payload = await _build_contradiction_context(
                db=db,
                user_id=request.user_id,
                user_message=request.message,
            )
            if _c_block:
                system_prompt += "\n\n" + _c_block



            # ===== LLM CALL VIA EMERGENT CONTRACT =====
            from emergent_contract import emergent_generate, validate_emergent_output, log_contract_event
            import asyncio
            import re

            response_text = None
            llm_start = time.time()
            try:
                # =================================================================
                # ASTROLOGY TRANSIT GROUNDING — astro-chat-transit-grounding-v1
                # Runs BEFORE the looser "transit question" heuristic below.
                # If the user asks where a body IS (transit) or whether a
                # transit is aspecting natal, we compute the answer
                # deterministically and pin the LLM to interpret-only mode.
                # =================================================================
                grounded_transit_envelope = None
                grounded_intent = None
                # astrology-chat-grounding-v2 — debug payload for dev verification
                astro_chat_debug: Dict[str, Any] = {
                    "marker": "astrology-chat-grounding-v2",
                    "intent_detected": None,
                    "solar_return_used": False,
                    "solar_return_success": False,
                    "transit_object_used": False,
                    "transit_to_natal_used": False,
                    "natal_object_used": False,
                    "timeline_summary_used": False,
                    "fallback_triggered": False,
                    "astro_sources_used": [],
                }
                if request.lens == "astrology" and chart is not None:
                    try:
                        from services.astrology_chat_router import (
                            classify_astrology_intent,
                            build_transit_object_proof_block,
                            build_transit_object_user_facing_prefix,
                        )
                        from services.transit_object_engine import (
                            compute_transit_object,
                            NOT_YET_ENABLED,
                            resolve_object_name,
                        )
                        from services.solar_return_engine import (
                            compute_solar_return,
                            build_solar_return_proof_block,
                        )
                        from services.natal_object_engine import (
                            compute_natal_object,
                            build_natal_object_proof_block,
                        )
                        from services.house_inventory_engine import (
                            build_house_inventory,
                            build_house_inventory_proof_block,
                        )

                        grounded_intent = classify_astrology_intent(request.message)
                        if grounded_intent:
                            mode_label = grounded_intent["data_mode"]
                            obj_name = grounded_intent.get("object")
                            astro_chat_debug["intent_detected"] = mode_label
                            astro_chat_debug[f"{mode_label}_used"] = True
                            logger.info(
                                f"[TransitRouter] intent={mode_label} "
                                f"object={obj_name} user={request.user_id[:8]}..."
                            )

                            # ── house_inventory branch ─────────────────────────
                            # astrology-chat-house-hierarchy-v5
                            # Multi-body house synthesis. Must aggregate the
                            # FULL object registry (Chiron, Lilith, Lots,
                            # asteroids) so the LLM never omits a body.
                            if mode_label == "house_inventory":
                                h_num = grounded_intent.get("house_number")
                                h_env = build_house_inventory(chart, h_num)
                                astro_chat_debug["house_number"] = h_num
                                astro_chat_debug["objects_in_house"] = [
                                    o["name"] for o in (h_env.get("objects_in_house") or [])
                                ]
                                astro_chat_debug["dominant_body"] = h_env.get("dominant_body")
                                astro_chat_debug["tension_body"] = h_env.get("tension_body")
                                astro_chat_debug["house_field_type"] = h_env.get("house_field_type")
                                astro_chat_debug["inventory_complete_for_computed_objects"] = h_env.get(
                                    "inventory_complete_for_computed_objects", True)
                                astro_chat_debug["object_classes_included"] = h_env.get(
                                    "object_classes_included", [])
                                astro_chat_debug["object_classes_unsupported"] = h_env.get(
                                    "object_classes_unsupported", [])
                                astro_chat_debug["astro_sources_used"].append(
                                    f"house_inventory:H{h_num}"
                                )
                                logger.info(
                                    f"[HouseInventory] house={h_num} objects="
                                    f"{[o['name'] for o in h_env.get('objects_in_house') or []]} "
                                    f"dominant={h_env.get('dominant_body')} "
                                    f"tension={h_env.get('tension_body')}"
                                )
                                system_prompt += "\n\n" + build_house_inventory_proof_block(h_env)
                                # let the LLM synthesize from the proof block

                            # ── solar_return branch ────────────────────────────
                            # astrology-chat-grounding-v2
                            elif mode_label == "solar_return":
                                user_doc = await db.users.find_one({"_id": ObjectId(request.user_id)})
                                sr_env = compute_solar_return(chart=chart, user=user_doc or {})
                                astro_chat_debug["solar_return_success"] = bool(sr_env.get("success"))
                                astro_chat_debug["solar_return_target_year"] = sr_env.get("target_year")
                                if sr_env.get("success"):
                                    astro_chat_debug["astro_sources_used"].append("solar_return_engine")
                                logger.info(
                                    f"[SolarReturn] success={sr_env.get('success')} "
                                    f"reason={sr_env.get('reason')} "
                                    f"target_year={sr_env.get('target_year')}"
                                )
                                system_prompt += "\n\n" + build_solar_return_proof_block(sr_env)
                                if not sr_env.get("success"):
                                    # Engine refused → use its message verbatim
                                    astro_chat_debug["fallback_triggered"] = True
                                    response_text = sr_env.get("message") or (
                                        "Solar return engine isn't wired into "
                                        "Astrology Chat yet."
                                    )
                                # else: let the LLM read the proof block and answer

                            # ── natal_object branch ─────────────────────────────
                            # astrology-chat-master-interpreter-v3
                            # Handles: Lilith, Chiron, Vertex, Nodes, Juno, etc.
                            # CRITICAL: if engine returns not-wired, the proof
                            # block forbids substitution with another body
                            # (no Lilith→Moon swap).
                            elif mode_label == "natal_object" and grounded_intent.get("object"):
                                obj_q = grounded_intent["object"]
                                no_env = compute_natal_object(chart=chart, object_name=obj_q)
                                astro_chat_debug["natal_object_success"] = bool(no_env.get("success"))
                                astro_chat_debug["natal_object_canonical"] = no_env.get("object")
                                astro_chat_debug["natal_object_reason"] = no_env.get("reason")
                                astro_chat_debug["natal_object_source"] = no_env.get("source")
                                if no_env.get("success"):
                                    astro_chat_debug["astro_sources_used"].append(
                                        f"natal_object:{no_env.get('object')}"
                                    )
                                logger.info(
                                    f"[NatalObject] query={obj_q!r} canonical={no_env.get('object')} "
                                    f"success={no_env.get('success')} reason={no_env.get('reason')} "
                                    f"source={no_env.get('source')}"
                                )
                                system_prompt += "\n\n" + build_natal_object_proof_block(no_env)
                                if not no_env.get("success"):
                                    astro_chat_debug["fallback_triggered"] = True
                                    response_text = no_env.get("message")

                            # transit_object + transit_to_natal both need
                            # the deterministic transit position envelope.
                            elif mode_label in ("transit_object", "transit_to_natal") and obj_name:
                                canonical = resolve_object_name(obj_name)
                                if canonical in NOT_YET_ENABLED:
                                    logger.info(
                                        f"[TransitRouter] object={canonical} "
                                        "not_yet_enabled — short-circuit response"
                                    )
                                    response_text = (
                                        f"{canonical} is not yet enabled in the "
                                        "transit lookup engine. I can compute the "
                                        "Sun, Moon, Mercury through Pluto, Chiron, "
                                        "and the Lunar Nodes — ask about any of "
                                        "those and I'll pull the current placement."
                                    )
                                else:
                                    grounded_transit_envelope = compute_transit_object(
                                        chart=chart,
                                        object_name=obj_name,
                                    )
                                    logger.info(
                                        f"[TransitRouter] endpoint_called=compute_transit_object "
                                        f"success={grounded_transit_envelope.get('success')} "
                                        f"reason={grounded_transit_envelope.get('reason')}"
                                    )
                                    # Inject deterministic block at the END of
                                    # the system prompt so it overrides any
                                    # earlier looser context.
                                    system_prompt += "\n\n" + build_transit_object_proof_block(
                                        grounded_transit_envelope
                                    )
                                    # If computation failed, refuse to interpret.
                                    if not grounded_transit_envelope.get("success"):
                                        logger.warning(
                                            "[TransitRouterFallbackBlocked] "
                                            f"attempted_fallback=natal_object "
                                            f"reason=transit_intent_requires_transit_payload "
                                            f"engine_reason={grounded_transit_envelope.get('reason')}"
                                        )
                                        # Prefer the engine-supplied message (e.g.,
                                        # Vertex explanation, ephemeris-missing
                                        # diagnostic) when present.
                                        eng_msg = grounded_transit_envelope.get("message")
                                        eng_reason = grounded_transit_envelope.get("reason")
                                        if eng_msg:
                                            response_text = eng_msg
                                        else:
                                            response_text = (
                                                "I couldn't compute the current "
                                                f"transit placement for "
                                                f"{canonical or obj_name} from the "
                                                f"chart engine yet. (reason: {eng_reason})"
                                            )
                    except Exception as router_exc:
                        # Intent router failure is non-fatal — fall through
                        # to the regular astrology chat path. We log loudly
                        # so this never silently degrades.
                        logger.exception(
                            f"[TransitRouter] classifier/compute crashed: {router_exc}"
                        )

                # ===== TRANSIT/TIMING QUESTION DETECTION =====
                # Detect if user is asking about timing, transits, or "what the stars say"
                transit_keywords = [
                    r'\bstars?\b', r'\bastrology\b', r'\btransit[s]?\b', r'\bplanetary\b',
                    r'\balignment[s]?\b', r'\bthis week\b', r'\bthis month\b', r'\bnext week\b',
                    r'\bnext month\b', r'\bcoming up\b', r'\bright now\b', r'\bcurrently\b',
                    r'\bwhat.*lenses? say\b', r'\bwhat do.*stars\b', r'\bcelestial\b',
                    r'\bretrograde\b', r'\beclipse\b', r'\bnew moon\b', r'\bfull moon\b'
                ]
                message_lower = request.message.lower()
                is_transit_question = any(re.search(kw, message_lower) for kw in transit_keywords)

                if is_transit_question:
                    logger.info(f"[MIRROR_CHAT] Detected transit/timing question for user {request.user_id}")

                # ===== ANALYST MODE DETECTION =====
                # Detect if user wants structured, analytical output (not reflective)
                analyst_keywords = [
                    r'\bdate breakdown\b', r'\bpoint form\b', r'\bbullet points?\b',
                    r'\bbullets?\b', r'\bbig events?\b', r'\btimeline\b', r'\bwhat\'?s coming\b',
                    r'\btransits?\b', r'\bsummary\b', r'\blist\b', r'\boverview\b',
                    r'\bkey dates?\b', r'\bkey moments?\b', r'\bwhen.*happen\b',
                    r'\bstructured\b', r'\bbreak.*down\b', r'\bclarity\b'
                ]
                is_analyst_mode = any(re.search(kw, message_lower) for kw in analyst_keywords)

                if is_analyst_mode:
                    logger.info(f"[MIRROR_CHAT] ANALYST MODE triggered for user {request.user_id}")

                # ===== TIMELINE MODE DETECTION (for Astrology Lens) =====
                timeline_keywords = [
                    r'\btimeline\b', r'\byear ahead\b', r'\bthis year\b', r'\bnext year\b',
                    r'\b2026\b', r'\b2027\b', r'\bkey dates\b', r'\bkey periods?\b',
                    r'\bwhen.*happen\b', r'\bwhat\'?s coming\b', r'\bupcoming\b',
                    r'\bimportant dates?\b', r'\bmajor events?\b', r'\bchronolog\b',
                    r'\bmap.*year\b', r'\byear overview\b', r'\bcalendar\b',
                    r'\bwindows?\b', r'\bpeaks?\b', r'\bturning points?\b'
                ]
                is_timeline_request = any(re.search(kw, message_lower) for kw in timeline_keywords)

                if is_timeline_request:
                    logger.info(f"[MIRROR_CHAT] TIMELINE MODE detected for user {request.user_id}")

                # Determine mode based on lens and question type
                if request.lens == "astrology" and is_timeline_request:
                    mode = "astrology_timeline"  # NEW: Dedicated timeline mode for astrology
                elif request.lens == "astrology" and is_analyst_mode:
                    mode = "astrology_analyst"  # Analyst mode within astrology lens
                elif request.lens == "astrology":
                    mode = "deep_dive"  # Default astrology mode
                elif request.lens == "human_design":
                    mode = "deep_dive"
                elif request.lens == "numerology":
                    mode = "deep_dive"
                elif is_keystone_followup:
                    mode = "daily_insight"
                elif is_analyst_mode:
                    mode = "analyst"  # Analyst mode for structured output
                elif is_transit_question:
                    mode = "timeline"  # Use timeline mode for transit questions
                else:
                    mode = "reflection_chat"

                # ===== ADD CURRENT TRANSIT CONTEXT FOR TIMING QUESTIONS =====
                if is_transit_question or request.lens == "astrology":
                    # Add user's timezone and current timing context
                    user_timezone = user.get('timezone', 'UTC')
                    tz_minutes = user.get('timezone_minutes', 0)
                    current_date = datetime.now().strftime("%Y-%m-%d")
                    current_month = datetime.now().strftime("%B %Y")

                    transit_context = f"""
--- CURRENT TIMING CONTEXT ---
Current Date: {current_date}
Current Month: {current_month}
User's Timezone: {user_timezone} (offset: {tz_minutes} minutes)
User's Location: {user.get('birth_location', {}).get('city', 'Not specified')}

IMPORTANT INSTRUCTION FOR TRANSIT/TIMING QUESTIONS:
When the user asks about "what the stars say", "this month", "this week", "planetary alignments", 
or any timing-related question:

1. ANSWER FIRST with the available context - do NOT immediately ask clarifying questions
2. Use the current date/month provided above as the default timeframe
3. Use the user's stored timezone as the default location context
4. Structure your response as:
   - FIRST: Share 1-3 strongest themes/signals relevant to the timeframe
   - THEN: Explain what this might feel like in lived experience
   - OPTIONAL: End with ONE reflective question (not a clarifying question)
5. Only ask for clarification if you truly cannot proceed (e.g., if birth data is completely missing)
6. DO NOT ask "what city are you in" or "which month do you mean" - use app context
7. If you need to make an assumption, state it lightly: "Reading this for {current_month}..."

RESPONSE TONE:
- Reflective and grounded, not generic assistant-like
- Specific without being absolute
- NO "I need one detail to do it cleanly" helper language
- Mirror holds space for exploration, not administrative questions
"""
                    system_prompt += transit_context
                    logger.info(f"[MIRROR_CHAT] Added transit context: timezone={user_timezone}, date={current_date}")

                # ===== ANALYST MODE PROMPT =====
                # When user wants structured, analytical output
                if is_analyst_mode:
                    user_timezone = user.get('timezone', 'UTC')
                    current_date = datetime.now().strftime("%Y-%m-%d")
                    current_month = datetime.now().strftime("%B %Y")

                    analyst_prompt = f"""
--- ANALYST MODE ACTIVATED ---
Current Date: {current_date}
Current Month: {current_month}

YOU ARE NOW IN ANALYST MODE. The user has requested structured, clear information.

OUTPUT FORMAT (STRICT):
Use this exact structure for your response:

### [DATE RANGE or PERIOD]
**Theme:** [2-5 word summary]

- [specific transit or signal]
- [specific transit or signal]

**What this means:**
- [clear bullet point - what they might feel/experience]
- [clear bullet point - behavioral pattern to watch]
- [clear bullet point - practical awareness]

---

(Repeat for 3-5 strongest windows/themes only)

RULES:
1. DO NOT ask clarifying questions first - answer with what you have
2. DO NOT explain astrology theory - just name the transit and its effect
3. DO NOT hedge excessively - be clear and direct
4. DO NOT use long paragraphs - bullets only
5. PRIORITIZE: Show only top 3-5 transit windows, strongest signals only
6. DATE RANGES: Use actual date ranges (e.g., "March 22-28" or "Late March")
7. THEMES: Name them clearly (e.g., "Career Pressure", "Relationship Reset", "Inner Conflict")

OPTIONAL MIRROR LAYER:
At the end, add ONE short reflective line. Examples:
- "You'll recognize this when the same tension shows up in different situations."
- "Watch for the moment when clarity comes—it'll be quieter than you expect."
- "The choice you're avoiding will show up again around [date]."

USER SHOULD FEEL:
- "This is clear"
- "I know what to expect"
- "I can orient myself"

NOT:
- "What is this saying?"
- "This is vague"
"""
                    system_prompt += analyst_prompt
                    logger.info(f"[MIRROR_CHAT] ANALYST MODE prompt injected for user {request.user_id}")

                # ===== ASTROLOGY TIMELINE MODE PROMPT =====
                # Master Astrologer Timeline - Year as a Story
                if mode == "astrology_timeline":
                    current_year = datetime.now().year
                    next_year = current_year + 1
                    current_date = datetime.now().strftime("%Y-%m-%d")

                    timeline_prompt = f"""
--- MASTER ASTROLOGER TIMELINE MODE ---
Current Date: {current_date}
Year Focus: {current_year} (or {next_year} if user specified)

YOU ARE A MASTER ASTROLOGER. Map the YEAR AS A STORY — not a calendar.
This is a narrative timeline of pressure, change, and decision windows.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## THE YEAR AS IT UNFOLDS
*Where things build, break, and shift*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### YEAR THEME (MANDATORY - 1-2 lines)
Must reflect dominant pattern + life chapter. Be specific, not generic.

Example:
"This is a year where moving too fast stops working. Growth comes from timing, not force."

---

### PRIMARY ARC (MANDATORY - short paragraph)
Describe:
- What is building across the year
- What keeps repeating
- What the year is trying to correct

Example:
"Across the year, you'll feel the tension between urgency and readiness. The pattern is consistent—acting early, then managing consequences. This year doesn't block you. It teaches you timing."

---

### KEY PHASES (MAX 6 - each must feel like a CHAPTER, not an event)

For each phase use this format:

━━━━━━━━━━━━━━━━━━━━━━
**[DATE RANGE]**
### [PHASE NAME] (2-4 words)

**What's actually happening:**
- Real-world description (NO astrology jargon)

**What this tends to create:**
- Behavioral / emotional pattern

**Where people get it wrong:**
- Common mistake pattern

**What this phase is asking of you:**
- Clear growth edge
━━━━━━━━━━━━━━━━━━━━━━

---

### ⭐ PRIMARY TURNING POINTS (MAX 3)
These are NOT just dates. These are IRREVERSIBLE SHIFTS.

For each:

⭐ **[DATE]**

**Why this matters:**
- What changes here (internal or external)

**What becomes clear:**
- What you can no longer ignore

**What happens if avoided:**
- Consequence of not engaging

---

### DECISION WINDOWS (CRITICAL - the "GURU" layer)
Add 2-4 windows where CHOICE matters:

**[DATE RANGE]**

*"You can push here. Or you can wait."*

- **If you act →** [likely outcome]
- **If you wait →** [likely outcome]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CRITICAL RULES:
1. DO NOT list more than 6 phases - be selective
2. DO NOT make every moment important - prioritize ruthlessly
3. NO vague spiritual phrasing ("cosmic energy", "universe guiding you")
4. NO astrology jargon without behavioral translation
5. EVERYTHING must be BEHAVIORAL + REAL - what will they DO or FEEL
6. EVERY section must connect to the SAME underlying pattern
7. Use the user's dominant truth, life chapter, and aspect patterns as the thread

DATA TO USE:
- Dominant truth (what keeps showing up)
- Life chapter (where they are in their arc)
- Aspect patterns (internal tensions)
- Transit priority (which transits actually matter)

USER SHOULD FEEL:
❌ NOT: "Here are some dates"
✅ BUT: "I understand how my year is unfolding"

❌ NOT: "Interesting"
✅ BUT: "I know when to act and when to wait"
"""
                    system_prompt += timeline_prompt
                    logger.info(f"[MIRROR_CHAT] MASTER ASTROLOGER TIMELINE prompt injected for user {request.user_id}")

                logger.info(f"[MIRROR_CHAT] Starting LLM call: mode={mode}, user={request.user_id}, is_transit_question={is_transit_question}")

                # Build context for emergent_generate
                emit_context = {
                    "lens": request.lens or "generalist",
                    "is_keystone_followup": is_keystone_followup,
                    "has_thread": thread_state is not None
                }
                if thread_state:
                    emit_context["thread_tone"] = thread_state.get("tone", "unclear")
                    emit_context["thread_remaining"] = thread_state.get("remaining_turns", 0)

                # Use centralized contract-enforced generation with timeout.
                # SKIP LLM CALL entirely if the deterministic transit router
                # already produced a final answer (e.g., object_not_yet_enabled
                # or computation failed) — astro-chat-transit-grounding-v1.
                try:
                    if response_text is None:
                        response_text = await asyncio.wait_for(
                            emergent_generate(
                                mode=mode,
                                user_message=request.message,
                                endpoint="mirror_chat",
                                user_id=request.user_id,
                                context=emit_context,
                                additional_system_prompt=system_prompt,
                                model=get_primary_model()
                            ),
                            timeout=90.0  # 90 second timeout for LLM call
                        )
                    else:
                        logger.info(
                            "[TransitRouter] response_text pre-populated by "
                            "deterministic router — skipping LLM call"
                        )
                    llm_duration = time.time() - llm_start
                    logger.info(f"[MIRROR_CHAT] LLM call completed: duration={llm_duration:.2f}s, response_length={len(response_text) if response_text else 0}")
                except asyncio.TimeoutError:
                    llm_duration = time.time() - llm_start
                    logger.error(f"[MIRROR_CHAT] LLM call TIMEOUT after {llm_duration:.2f}s for user {request.user_id}")
                    raise HTTPException(status_code=504, detail="Mirror is taking too long to respond. Please try again.")

                # Log request (no user text)
                logger.info(f"Mirror chat via emergent_generate: user={request.user_id}, lens={request.lens or 'generalist'}, mode={mode}")

            except HTTPException:
                raise  # Re-raise HTTP exceptions (like timeout)
            except Exception as llm_error:
                llm_duration = time.time() - llm_start
                logger.error(f"[MIRROR_CHAT] LLM call FAILED after {llm_duration:.2f}s for user {request.user_id}: {type(llm_error).__name__}: {str(llm_error)}")
                from emergent_contract import get_safe_fallback
                response_text = get_safe_fallback(mode if 'mode' in dir() else "reflection_chat")

            # Note: Guardrail enforcement is now handled INSIDE emergent_generate()
            # The contract module does validation, rewriting, and regeneration automatically

            # Store in history
            history.append({"role": "user", "content": request.message})
            history.append({"role": "assistant", "content": response_text})

            # Limit history size to MAX_CHAT_HISTORY messages
            if len(history) > MAX_CHAT_HISTORY * 2:  # *2 for user+assistant pairs
                chat_sessions[session_id] = history[-(MAX_CHAT_HISTORY * 2):]

            # Generate Memory Update (asynchronously, in parallel with response)
            memory_update = None
            try:
                # Build context for memory analysis
                memory_context_parts = []

                # Add recent conversation history
                memory_context_parts.append("--- RECENT CONVERSATION ---")
                for msg in history[-10:]:  # Last 10 messages
                    role = "User" if msg['role'] == 'user' else "Mirror"
                    memory_context_parts.append(f"{role}: {msg['content'][:500]}")

                # Add journal entries if available (LIMITED to MAX_JOURNAL_ENTRIES)
                if request.include_journal:
                    journal_entries = await db.journal.find(
                        {"user_id": request.user_id}
                    ).sort("timestamp", -1).limit(MAX_JOURNAL_ENTRIES).to_list(MAX_JOURNAL_ENTRIES)

                    if journal_entries:
                        memory_context_parts.append("\n--- RECENT JOURNAL ENTRIES ---")
                        for entry in reversed(journal_entries):
                            content = entry.get('content', '')[:300]
                            memory_context_parts.append(f"- {content}")

                # Build memory analysis prompt
                memory_prompt = MEMORY_UPDATE_PROMPT + "\n\n" + "\n".join(memory_context_parts)

                # Create separate LLM call for memory update
                memory_chat = LlmChat(
                    api_key=EMERGENT_LLM_KEY,
                    session_id=f"memory_{session_id}",
                    system_message=memory_prompt
                )
                memory_chat.with_model("openai", get_primary_model())

                # Request structured memory update
                memory_message = UserMessage(text="Analyze the above and generate a memory_update JSON object.")
                memory_response = await memory_chat.send_message(memory_message)

                # Parse JSON response
                import json
                import re

                # Handle case where memory_response is a dict (API response) or string
                if isinstance(memory_response, dict):
                    # Extract text from response dict
                    memory_response_text = memory_response.get('text', memory_response.get('content', str(memory_response)))
                else:
                    memory_response_text = str(memory_response)

                # Extract JSON from response (handle markdown code blocks)
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', memory_response_text)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = memory_response_text.strip()

                memory_data = json.loads(json_str)

                # Validate and sanitize
                memory_update = MemoryUpdate(
                    themes=memory_data.get('themes', [])[:5],
                    recurring_tensions=memory_data.get('recurring_tensions', [])[:5],
                    supportive_moves=memory_data.get('supportive_moves', [])[:5],
                    drainers=memory_data.get('drainers', [])[:5],
                    inferred_state=memory_data.get('inferred_state', 'unclear'),
                    confidence=min(1.0, max(0.0, float(memory_data.get('confidence', 0.5)))),
                    evidence=memory_data.get('evidence', [])[:3],
                    updated_at_iso=datetime.now(timezone.utc).isoformat()
                )

                # Validate inferred_state
                valid_states = ['grounding', 'stabilizing', 'exploring', 'integrating', 'unclear']
                if memory_update.inferred_state not in valid_states:
                    memory_update.inferred_state = 'unclear'

                # Store memory update in database (overwrite previous)
                await db.user_memory.update_one(
                    {"user_id": request.user_id},
                    {"$set": {
                        "user_id": request.user_id,
                        "memory_update": memory_update.dict(),
                        "updated_at": datetime.now(timezone.utc)
                    }},
                    upsert=True
                )

                logger.info(f"Memory update stored for user {request.user_id}: state={memory_update.inferred_state}, confidence={memory_update.confidence}")

                # Write timeline event for consciousness tracking (privacy-safe, no raw text)
                try:
                    timeline_event = {
                        "user_id": request.user_id,
                        "session_id": session_id,
                        "created_at_iso": datetime.now(timezone.utc).isoformat(),
                        "event_type": "keystone_followup" if is_keystone_followup else "mirror_chat_turn",
                        "inferred_state": memory_update.inferred_state,
                        "confidence": memory_update.confidence,
                        "themes": memory_update.themes[:2],  # max 2 themes
                        "tension": memory_update.recurring_tensions[0] if memory_update.recurring_tensions else None,
                        "source": "keystone_continuation" if is_keystone_followup else "mirror_chat",
                        "keystone_date": request.keystone_context.date if is_keystone_followup else None,
                        "version": "v1"
                    }

                    await db.user_timeline.insert_one(timeline_event)
                    logger.info(f"Timeline event recorded for user {request.user_id}: type={timeline_event['event_type']}, state={memory_update.inferred_state}")

                except Exception as timeline_error:
                    logger.warning(f"Timeline event write failed: {timeline_error}")
                    # Continue without timeline - don't fail the request

            except Exception as mem_error:
                logger.warning(f"Memory update generation failed: {mem_error}")
                # Continue without memory update - don't fail the whole request

            # ===== THREAD STATE UPDATE =====
            # Decrement remaining_turns after successful reply
            thread_metadata = None
            if thread_state and thread_state.get("remaining_turns", 0) > 0:
                new_remaining = thread_state["remaining_turns"] - 1

                await db.user_thread_state.update_one(
                    {"user_id": request.user_id},
                    {"$set": {
                        "remaining_turns": new_remaining,
                        "updated_at_iso": datetime.now(timezone.utc).isoformat()
                    }}
                )

                thread_metadata = {
                    "active": new_remaining > 0,
                    "thread_type": thread_state.get("thread_type", "daily_keystone"),
                    "thread_date": thread_state.get("thread_date"),
                    "remaining_turns": new_remaining,
                    "title": thread_state.get("title"),
                    "keystone": thread_state.get("keystone"),
                    "reflect_question": thread_state.get("reflect_question"),
                    "micro_affirmation": thread_state.get("micro_affirmation"),
                    "tone": thread_state.get("tone")
                }

                logger.info(f"[Thread] Decremented remaining_turns for user {request.user_id}: {thread_state['remaining_turns']} -> {new_remaining}")

                if new_remaining == 0:
                    logger.info(f"[Thread] Thread completed for user {request.user_id}")

            request_duration = time.time() - request_start
            logger.info(f"[MIRROR_CHAT] === REQUEST COMPLETED === user_id={request.user_id}, duration={request_duration:.2f}s, response_length={len(response_text) if response_text else 0}")

            # Compose final debug payload — fold relational debug under
            # `relational` key so frontend can read both lens + relational layers.
            final_debug: Optional[dict] = None
            if request.lens in ("astrology", "human_design", "numerology", "enneagram", "bazi", "zi_wei"):
                # Spread top-level fields (preserved for backwards-compat with
                # any consumer reading `debug.marker` / `debug.lens` directly),
                # AND ALSO mirror the full payload under `debug.lens_chat` so
                # the documented T1b/T1c contract holds:
                #   debug.lens_chat.marker == "multi-lens-chat-memory-v1"
                #   debug.lens_chat.lens   == "<lens>"
                final_debug = dict(lens_debug_payload or {})
                if lens_debug_payload:
                    final_debug["lens_chat"] = dict(lens_debug_payload)
            if relational_debug_payload:
                if final_debug is None:
                    final_debug = {}
                final_debug["relational"] = relational_debug_payload
            # pattern-memory-v1 — surface longitudinal recurrence debug data.
            # Always include when the pattern-memory module ran (even on
            # no-trigger turns) so the frontend can verify the dispatcher is
            # active.  Frontend uses `pattern_memory.marker` for dev tooling.
            if pattern_debug_payload:
                if final_debug is None:
                    final_debug = {}
                final_debug["pattern_memory"] = pattern_debug_payload
            # life-tab-master-voice-v1 — surface the master-voice provenance
            # so the frontend dev pill can confirm it fired and inspect which
            # frameworks contributed.
            if master_voice_debug_payload:
                if final_debug is None:
                    final_debug = {}
                final_debug["master_voice"] = master_voice_debug_payload

            # evidence-drawer-v2 — build the small, curated, user-facing
            # `evidence` object that the Evidence Drawer renders.  This is
            # SEPARATE from `debug`: `debug` is for diagnostics, `evidence`
            # is for the user.  Curator failure NEVER breaks the response.
            if reflection_debug_payload:
                if final_debug is None:
                    final_debug = {}
                final_debug["micro_reflection"] = reflection_debug_payload

            # contradiction-intelligence-v1 — fold soft contradiction payload
            # into final debug.  Even at LOW level (not surfaced) we expose
            # it so frontend can confirm the dispatcher ran.
            if contradiction_debug_payload:
                if final_debug is None:
                    final_debug = {}
                final_debug["contradictions"] = contradiction_debug_payload

            # astrology-chat-grounding-v2 — surface intent classifier +
            # solar return engine usage so the dev pill can confirm
            # which deterministic source the chat was grounded against.
            try:
                if astro_chat_debug and astro_chat_debug.get("intent_detected"):
                    if final_debug is None:
                        final_debug = {}
                    final_debug["astro_chat"] = astro_chat_debug
            except NameError:
                # astro_chat_debug only exists when lens == "astrology"
                pass

            evidence_payload: Optional[dict] = None
            try:
                from services.evidence_curator import curate_evidence
                evidence_payload = curate_evidence(final_debug)
                if evidence_payload:
                    logger.info(
                        f"[MIRROR_CHAT][evidence-drawer-v2] evidence_emitted=True "
                        f"keys={list(evidence_payload.keys())}"
                    )
            except Exception as ev_err:
                logger.error(
                    f"[MIRROR_CHAT][evidence-drawer-v2] curator error: "
                    f"{type(ev_err).__name__}: {ev_err}"
                )
                evidence_payload = None

            return MirrorChatResponse(
                response=response_text,
                session_id=session_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                memory_update=memory_update,
                thread=thread_metadata,
                debug=final_debug,
                evidence=evidence_payload,
            )

        except HTTPException as http_exc:
            # Re-raise HTTP exceptions (like rate limiting, timeouts)
            request_duration = time.time() - request_start
            logger.error(f"[MIRROR_CHAT] === REQUEST FAILED (HTTPException) === user_id={request.user_id}, duration={request_duration:.2f}s, status={http_exc.status_code}, detail={http_exc.detail}")
            raise
        except Exception as e:
            request_duration = time.time() - request_start
            error_type = type(e).__name__
            error_msg = str(e)
            logger.error(f"[MIRROR_CHAT] === REQUEST FAILED (Exception) === user_id={request.user_id}, duration={request_duration:.2f}s, type={error_type}, message={error_msg}")
            logger.error(f"[MIRROR_CHAT] traceback: {traceback.format_exc()}")

            # Return structured error instead of exposing raw exception
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error_code": "mirror_interpret_failed",
                    "message": "Mirror hit an internal formatting issue while preparing the reflection."
                }
            )
