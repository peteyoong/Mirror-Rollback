"""
Forum Mirror Relational Orchestrator V1
========================================
Build marker: forum-mirror-relational-orchestrator-v1

The Ask Mirror surface inside a forum (Me / Member / Forum tabs) was
routing user messages directly into a generic LLM with a flat
context dump. As a result, a query like
    "Tell me about Mel's 4th house and how does that map to me?"
from the "Me" tab returned a textbook answer ("the 4th house is about
home and family...") because:
  - the LLM had no orchestrated knowledge that "Mel" referred to a
    specific forum member with a stored chart,
  - the deterministic V7/V8/V10 engines that already exist for
    /api/mirror/chat were never invoked here,
  - the system prompt told the model "the user is asking about
    themselves" — which silently overrode the relational pivot the
    user actually wanted.

This orchestrator runs BEFORE the LLM call and produces a strongly-
worded, deterministic addendum that the system prompt can include.
It chains three resolvers and one synthesis builder:

  Phase 1 — Member resolver:
      Extract candidate target names + relationship aliases (spouse,
      wife, husband, partner) from the message. Cross-reference
      forum_members, relationship_mappings, and saved_people.

  Phase 2 — Intent classifier:
      Decide whether the question is ASTROLOGY / RELATIONSHIP_FIELD
      / HD / ENNEAGRAM / BAZI / NUMEROLOGY / FORUM_DYNAMICS /
      PERSON_PATTERN / GENERAL.

  Phase 3 — Relationship resolver:
      If a target was found, resolve relationship_role + closeness
      via the existing V10 relationship_resolver (explicit_map first,
      then saved_people, then forum inference).

  Phase 4 — Context synthesizer:
      Build a deterministic, mirror-voice ADDENDUM block:
        - resolved-target identity assertion
        - relationship-field framing
        - if ASTROLOGY+target+house → V8 field synthesis proof block
          (computed against the target's chart, not the asker's)
        - mirror-voice rules: never refuse data that exists, never
          speak generic astrology, prioritise relational reflection.

Caller (forums_chat.py) appends the addendum to the existing system
prompt right before invoking the LLM.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from bson import ObjectId

logger = logging.getLogger(__name__)

BUILD_MARKER = "forum-mirror-relational-orchestrator-v1"

# ---------------------------------------------------------------------------
# Phase 1 — Member resolution helpers
# ---------------------------------------------------------------------------

# Relationship-alias tokens that resolve a target without requiring the
# member's literal name in the message ("spouse", "my wife", etc.).
_ALIAS_TO_ROLES: Dict[str, List[str]] = {
    "spouse":   ["spouse", "husband", "wife"],
    "husband":  ["spouse", "husband"],
    "wife":     ["spouse", "wife"],
    "partner":  ["partner", "spouse"],
    "ex":       ["ex_partner", "ex"],
    "boyfriend": ["partner", "spouse"],
    "girlfriend": ["partner", "spouse"],
}

# These pronouns mean "the asker" — NOT a member.
_SELF_PRONOUNS = {"i", "me", "my", "mine", "myself"}

_ALIAS_RE = re.compile(
    r"\bmy\s+(spouse|husband|wife|partner|ex|boyfriend|girlfriend)\b",
    re.IGNORECASE,
)


async def _resolve_target_via_alias(
    *,
    db,
    asker_user_id: str,
    message: str,
) -> Optional[Dict[str, Any]]:
    """If the message contains 'my spouse / wife / husband / partner',
    look up `relationship_mappings` for the asker and return that
    target. Returns None if no alias is present or no mapping exists.
    """
    m = _ALIAS_RE.search(message or "")
    if not m:
        return None
    alias = m.group(1).lower()
    candidate_roles = _ALIAS_TO_ROLES.get(alias, [alias])

    # Search relationship_mappings for asker → target with matching role
    cursor = db.relationship_mappings.find({
        "asker_user_id":      asker_user_id,
        "relationship_type":  {"$in": candidate_roles},
    })
    docs = await cursor.to_list(length=10)
    if not docs:
        return None
    doc = docs[0]
    target_uid = doc.get("target_user_id")
    if not target_uid:
        return None
    target_user = await db.users.find_one({"_id": ObjectId(target_uid)})
    target_name = (target_user or {}).get("name", alias.title())
    return {
        "target_user_id": target_uid,
        "target_name":    target_name,
        "source":         "relationship_alias",
        "alias_matched":  alias,
        "role_hint":      doc.get("relationship_type"),
    }


async def _resolve_target_via_forum_members(
    *,
    db,
    forum_id: str,
    asker_user_id: str,
    message: str,
) -> Optional[Dict[str, Any]]:
    """Find any forum member whose first name appears in the message.

    This is the workhorse resolver. It picks up "Mel", "Isaac",
    "Thaddeus", "Jakob", etc. and returns the first match. Skips the
    asker themselves.
    """
    if not message:
        return None
    msg_words = set(re.findall(r"[A-Za-z]+", message))
    msg_words_lower = {w.lower() for w in msg_words}
    msg_words_lower -= _SELF_PRONOUNS

    # Hydrate all forum members
    cursor = db.forum_members.find({
        "forum_id": forum_id,
        "status":   "active",
    })
    members = await cursor.to_list(length=50)
    for mem in members:
        mem_uid = mem.get("user_id")
        if not mem_uid or mem_uid == asker_user_id:
            continue
        user_doc = await db.users.find_one({"_id": ObjectId(mem_uid)})
        if not user_doc:
            continue
        full_name = (user_doc.get("name") or "").strip()
        if not full_name:
            continue
        # Match either full name or first-name token
        first = full_name.split()[0].lower()
        if first in msg_words_lower or full_name.lower() in (message or "").lower():
            return {
                "target_user_id": mem_uid,
                "target_name":    full_name,
                "source":         "forum_member",
            }
    return None


# ---------------------------------------------------------------------------
# Slice A — Spouse auto-promotion when the life-domain is relationship
# ---------------------------------------------------------------------------
# When the asker has a stored spouse / wife / husband / partner mapping
# AND the question is in the relationship life-domain ("marriage",
# "partnership", "soulmate"…), we promote that target automatically —
# even if the asker never typed the spouse's name or the word "spouse".
# This is what makes "Tell me about what my chart says about marriage"
# become a Pete↔Mel reading instead of a solo Pete reading.
# ---------------------------------------------------------------------------

_SPOUSE_ROLES = {"spouse", "husband", "wife", "partner"}


async def _resolve_spouse_when_relationship_domain(
    *,
    db,
    asker_user_id: str,
) -> Optional[Dict[str, Any]]:
    """Return the asker's stored spouse mapping when one exists, else None.

    Caller is responsible for gating this behind a relationship-domain check.
    """
    cursor = db.relationship_mappings.find({
        "asker_user_id":     asker_user_id,
        "relationship_type": {"$in": list(_SPOUSE_ROLES)},
    })
    docs = await cursor.to_list(length=5)
    if not docs:
        return None
    doc = docs[0]
    target_uid = doc.get("target_user_id")
    if not target_uid:
        return None
    target_user = await db.users.find_one({"_id": ObjectId(target_uid)})
    target_name = (
        doc.get("target_name")
        or (target_user or {}).get("name")
        or "your partner"
    )
    return {
        "target_user_id": target_uid,
        "target_name":    target_name,
        "source":         "spouse_auto_promote",
        "role_hint":      doc.get("relationship_type") or "spouse",
    }


# ---------------------------------------------------------------------------
# Phase 2 — Intent classification
# ---------------------------------------------------------------------------

_HOUSE_RE = re.compile(
    r"\b(?:(1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th|11th|12th)|"
    r"(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth))\s+house\b",
    re.IGNORECASE,
)
_HOUSE_WORDS = {
    "first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3,
    "fourth": 4, "4th": 4, "fifth": 5, "5th": 5, "sixth": 6, "6th": 6,
    "seventh": 7, "7th": 7, "eighth": 8, "8th": 8, "ninth": 9, "9th": 9,
    "tenth": 10, "10th": 10, "eleventh": 11, "11th": 11, "twelfth": 12, "12th": 12,
}

_ASTROLOGY_TOKENS = re.compile(
    r"\b(house|chart|natal|sun|moon|rising|ascendant|mercury|venus|mars|"
    r"jupiter|saturn|uranus|neptune|pluto|chiron|north node|midheaven|"
    r"IC|MC|stellium|aspect|conjunction|opposition|square|trine|sextile|"
    r"placement|sign|transit|retrograde|astrology|astrological)\b",
    re.IGNORECASE,
)
_RELATIONSHIP_FIELD_TOKENS = re.compile(
    r"\b(fight|fights|argue|conflict|tension|why do (?:we|you)|"
    r"how does\b.+\b(?:process|handle|cope|react)|"
    r"what does\b.+\bneed|between us|between you and me|our dynamic|"
    r"the field between|how (?:do|does) (?:he|she|they)\b)\b",
    re.IGNORECASE,
)
_HD_TOKENS = re.compile(
    r"\b(channel|gate|human design|hd type|projector|generator|"
    r"manifestor|reflector|profile line|authority|defined|undefined|"
    r"split definition|cross|incarnation)\b",
    re.IGNORECASE,
)
_ENNEAGRAM_TOKENS = re.compile(
    r"\b(enneagram|core type|wing|tritype|stress arrow|growth arrow|"
    r"type [1-9]\b)\b",
    re.IGNORECASE,
)
_BAZI_TOKENS = re.compile(
    r"\b(bazi|day master|four pillars|chinese astrology|element clash)\b",
    re.IGNORECASE,
)
_NUMEROLOGY_TOKENS = re.compile(
    r"\b(life path|destiny number|expression number|numerology|"
    r"personal year|master number)\b",
    re.IGNORECASE,
)
_FORUM_TOKENS = re.compile(
    r"\b(forum|group|circle|the team|everyone in|all of us|group dynamic)\b",
    re.IGNORECASE,
)


def classify_query_intent(message: str) -> Dict[str, Any]:
    """Return {'intent': str, 'house_number': Optional[int]}.

    intent ∈ {ASTROLOGY, RELATIONSHIP_FIELD, HD, ENNEAGRAM, BAZI,
              NUMEROLOGY, FORUM_DYNAMICS, PERSON_PATTERN, GENERAL}
    """
    if not message:
        return {"intent": "GENERAL", "house_number": None}
    house_n = None
    m = _HOUSE_RE.search(message)
    if m:
        token = (m.group(1) or m.group(2) or "").lower()
        house_n = _HOUSE_WORDS.get(token)

    # Priority order: relationship_field > astrology > HD > enneagram > others
    if _RELATIONSHIP_FIELD_TOKENS.search(message):
        return {"intent": "RELATIONSHIP_FIELD", "house_number": house_n}
    if house_n is not None or _ASTROLOGY_TOKENS.search(message):
        return {"intent": "ASTROLOGY", "house_number": house_n}
    if _HD_TOKENS.search(message):
        return {"intent": "HD", "house_number": None}
    if _ENNEAGRAM_TOKENS.search(message):
        return {"intent": "ENNEAGRAM", "house_number": None}
    if _BAZI_TOKENS.search(message):
        return {"intent": "BAZI", "house_number": None}
    if _NUMEROLOGY_TOKENS.search(message):
        return {"intent": "NUMEROLOGY", "house_number": None}
    if _FORUM_TOKENS.search(message):
        return {"intent": "FORUM_DYNAMICS", "house_number": None}
    return {"intent": "GENERAL", "house_number": None}


# ---------------------------------------------------------------------------
# Phase 3 + 4 — Synthesis builder
# ---------------------------------------------------------------------------

_MIRROR_VOICE_RULES = """
MIRROR VOICE RULES (NON-NEGOTIABLE):

1. NEVER claim you "can't provide specifics" about a member when their
   chart is loaded above. The data is in this prompt. Use it.

2. NEVER write generic astrology definitions ("the 4th house represents
   home and family"). Always speak from the SPECIFIC placement on the
   target's chart.

3. ALWAYS answer from the RELATIONSHIP FIELD when a relationship is
   resolved. Bad: "The 4th house represents home." Good: "{TARGET}'s
   emotional foundation is shaped by {SIGN} on the IC and {PLANET} in
   the {HOUSE}. What this touches in you is..."

4. ANSWER PRIORITY (never invert this order):
     1. Relationship field
     2. Astrology / HD / Enneagram evidence on the specific person
     3. Forum context
     4. General interpretation (ONLY if nothing above applies)

5. Forum Mirror is a RELATIONSHIP-AWARE REFLECTION SYSTEM. Not a
   therapist, not a chatbot, not an astrologer.

6. Assume data above is correct. Do not hedge with "without their
   chart..." — the chart IS in this prompt.

7. End with a reflection that lands in the field between asker and
   target, not a generic open question.
"""


async def build_relational_orchestrator_payload(
    *,
    db,
    forum_id: str,
    asker_user_id: str,
    message: str,
    mode: str,                       # "self" | "member" | "forum"
    target_member_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Top-level entry point. Returns the addendum block + debug dict.

    Caller (forums_chat.py) appends `system_prompt_addendum` to the
    existing system prompt right before the LLM call.
    """
    debug: Dict[str, Any] = {
        "marker":        BUILD_MARKER,
        "frame":         mode,
        "intent":        None,
        "house_number":  None,
        "resolved_target":   None,
        "relationship_role": None,
        "role_source":       None,
        "context_blocks":    [],
        "life_domain":       None,
        "spouse_auto_promoted": False,
        "layered_block_emitted": False,
    }

    # ── Slice A — life-domain classification (question-intent-router-v1) ──
    #   This runs the lightweight life-domain classifier so we know if
    #   the question is about marriage / partnership / career / family /
    #   spiritual purpose.  This signal is INDEPENDENT of the existing
    #   astrology-intent classifier below — both fire.
    try:
        from services.question_intent_router import classify_question_intent
        _life_intent = classify_question_intent(message or "")
        life_domain = _life_intent.get("domain", "general")
    except Exception as _li_err:  # noqa: BLE001
        logger.debug(f"[ForumMirrorOrchestrator] life-domain skipped: {_li_err}")
        life_domain = "general"
    debug["life_domain"] = life_domain

    # ── Phase 1 — Resolve target ──────────────────────────────────────
    resolved: Optional[Dict[str, Any]] = None
    if mode == "member" and target_member_id:
        # Explicit Member-mode selection — trust it.
        user_doc = await db.users.find_one({"_id": ObjectId(target_member_id)})
        if user_doc:
            resolved = {
                "target_user_id": target_member_id,
                "target_name":    (user_doc.get("name") or "Unknown").strip(),
                "source":         "explicit_mode_member",
            }

    # Even in Member mode we still try alias resolution in case the
    # message references a different member (e.g. selected Mel but
    # asked about "my wife who is also Mel" — alias wins as a sanity
    # check; otherwise alias confirms the selection).
    alias_match = await _resolve_target_via_alias(
        db=db, asker_user_id=asker_user_id, message=message
    )

    # Bare forum-member-name extraction (regardless of mode). This is
    # the key fix for "Me" tab queries that mention another member's
    # name. If alias already matched, we still run this to capture an
    # additional explicit-name reference, but prefer alias if mode==me.
    name_match = await _resolve_target_via_forum_members(
        db=db, forum_id=forum_id, asker_user_id=asker_user_id, message=message
    )

    # Priority: explicit_mode_member > alias > name_match
    if not resolved:
        resolved = alias_match or name_match

    # ── Slice A — Spouse auto-promotion ───────────────────────────────
    #   If the question is in the relationship life-domain AND nothing
    #   else resolved a target, promote the asker's stored spouse.
    #   This makes "Tell me about what my chart says about marriage"
    #   become a layered Pete↔Mel reading instead of a solo Pete read.
    if not resolved and life_domain == "relationship":
        try:
            spouse_match = await _resolve_spouse_when_relationship_domain(
                db=db, asker_user_id=asker_user_id,
            )
            if spouse_match:
                resolved = spouse_match
                debug["spouse_auto_promoted"] = True
        except Exception as _sp_err:  # noqa: BLE001
            logger.debug(
                f"[ForumMirrorOrchestrator] spouse auto-promote skipped: {_sp_err}"
            )

    debug["resolved_target"] = resolved

    # ── Phase 2 — Intent classification ───────────────────────────────
    intent_data = classify_query_intent(message)
    debug["intent"] = intent_data["intent"]
    debug["house_number"] = intent_data["house_number"]

    # ── Phase 3 — Relationship role ───────────────────────────────────
    rel_info: Dict[str, Any] = {}
    if resolved and resolved.get("target_user_id"):
        try:
            from services.relationship_resolver import resolve_relationship
            rel_info = await resolve_relationship(
                db=db,
                asker_user_id=asker_user_id,
                target_user_id=resolved["target_user_id"],
                target_name=resolved.get("target_name"),
                forum_id=forum_id,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(
                f"[ForumMirrorOrchestrator] relationship_resolver failed: {e}"
            )
            rel_info = {}
        debug["relationship_role"] = rel_info.get("relationship_role")
        debug["role_source"]      = rel_info.get("relationship_source")

    # ── Phase 4 — Build context block stack ───────────────────────────
    parts: List[str] = []
    parts.append(
        f"\n=========================================================\n"
        f"FORUM MIRROR RELATIONAL ORCHESTRATOR ({BUILD_MARKER})\n"
        f"=========================================================\n"
    )

    # 4.0 — Slice A: LAYERED RELATIONSHIP BLOCK (leads when domain=relationship)
    #   This is the marriage/partnership fix.  When the life-domain is
    #   relationship we open the addendum with a strict, layered block
    #   that names Descendant / 7th house / 7th ruler / Venus / Juno
    #   BEFORE anything else, and bans opening with Sun / HD / Numerology.
    if life_domain == "relationship":
        try:
            from services.astrology_domain_context import (
                build_layered_relationship_block,
            )
            # Always load asker's chart
            asker_chart = await db.charts.find_one({"user_id": asker_user_id})
            asker_user_doc = await db.users.find_one({"_id": ObjectId(asker_user_id)})
            asker_name = (asker_user_doc or {}).get("name") or "you"

            # Spouse chart (when promoted or otherwise resolved)
            spouse_chart = None
            spouse_name = None
            spouse_role = None
            if resolved and resolved.get("target_user_id"):
                spouse_chart = await db.charts.find_one({
                    "user_id": resolved["target_user_id"],
                })
                spouse_name = resolved.get("target_name")
                spouse_role = resolved.get("role_hint") or "spouse"

            layered = build_layered_relationship_block(
                asker_chart=asker_chart or {},
                asker_name=asker_name,
                spouse_chart=spouse_chart,
                spouse_name=spouse_name,
                relationship_role=spouse_role,
            )
            if layered:
                parts.append(layered)
                debug["layered_block_emitted"] = True
                debug["context_blocks"].append("layered_relationship_block")
                logger.info(
                    f"[ForumMirrorOrchestrator] layered_relationship_block "
                    f"asker={asker_name!r} spouse={spouse_name!r} "
                    f"role={spouse_role!r} chars={len(layered)}"
                )
        except Exception as _lr_err:  # noqa: BLE001
            logger.warning(
                f"[ForumMirrorOrchestrator] layered relationship block failed: {_lr_err}"
            )

    # 4a — resolved-target identity assertion
    if resolved and resolved.get("target_user_id"):
        parts.append(
            f"RESOLVED TARGET: {resolved.get('target_name')} "
            f"(user_id={resolved.get('target_user_id')[:8]}…, "
            f"resolution_source={resolved.get('source')})\n"
        )
        debug["context_blocks"].append("resolved_target")
    else:
        parts.append(
            "RESOLVED TARGET: none — speaker is reflecting on themselves "
            "or asking a general forum question.\n"
        )

    # 4b — relationship framing
    if rel_info and rel_info.get("relationship_detected"):
        parts.append(
            f"RELATIONSHIP CONTEXT:\n"
            f"  speaker → target relationship role: "
            f"{rel_info.get('relationship_role')}\n"
            f"  closeness: {rel_info.get('closeness')}\n"
            f"  emotional_weight: {rel_info.get('emotional_weight')}\n"
            f"  source: {rel_info.get('relationship_source')}\n"
            f"  forum_id: {rel_info.get('forum_id') or forum_id}\n"
        )
        debug["context_blocks"].append("relationship_context")

    # 4c — V8 field synthesis when ASTROLOGY + target + house
    v8_proof_block_added = False
    if (
        resolved
        and resolved.get("target_user_id")
        and intent_data["intent"] == "ASTROLOGY"
        and intent_data["house_number"] is not None
    ):
        try:
            from services.field_synthesis_engine import (
                build_field_synthesis,
                build_field_synthesis_proof_block,
            )
            # Load target's chart
            chart_doc = await db.charts.find_one({
                "user_id": resolved["target_user_id"],
            })
            if chart_doc:
                synth = build_field_synthesis(
                    chart=chart_doc,
                    house_number=intent_data["house_number"],
                )
                if synth.get("success"):
                    proof = build_field_synthesis_proof_block(synth)
                    parts.append(
                        f"\nDETERMINISTIC ASTROLOGY EVIDENCE FOR "
                        f"{resolved.get('target_name')}'s "
                        f"{intent_data['house_number']} HOUSE:\n"
                        f"(computed from {resolved.get('target_name')}'s "
                        f"natal chart — not the asker's)\n"
                    )
                    parts.append(proof)
                    debug["context_blocks"].append("v8_field_synthesis")
                    debug["v8_synth_summary"] = {
                        "house_sign": synth.get("house_sign"),
                        "ruler": synth.get("ruler"),
                        "ruler_sign": synth.get("ruler_sign"),
                        "ruler_house": synth.get("ruler_house"),
                        "destabilizing_planet": synth.get("destabilizing_planet"),
                    }
                    # Stash the full synth for the V8 token anchor
                    # post-processor (run by the caller).
                    debug["_v8_synth_full"] = synth
                    v8_proof_block_added = True
        except Exception as e:  # noqa: BLE001
            logger.warning(
                f"[ForumMirrorOrchestrator] V8 synthesis failed: {e}"
            )

    # 4d — relationship-mapping summary (when target + non-astrology
    #      intent, or when astrology fell through). Tries to fetch
    #      pair-level synthesis from forum_hd_mapping if available.
    if resolved and resolved.get("target_user_id") and not v8_proof_block_added:
        # We won't reach for the full forum_hd_mapping run here (heavy)
        # — instead we point the LLM at the relationship-mapping
        # context fields that are already loaded into the forum chat
        # context dump above. This nudge keeps the LLM from defaulting
        # to generic answers.
        parts.append(
            f"\nFIELD-LEVEL FRAMING:\n"
            f"  The user is in {('MEMBER' if mode=='member' else 'ME')} mode "
            f"but the message references {resolved.get('target_name')}. "
            f"Pivot the answer to the {resolved.get('target_name')}↔"
            f"speaker field, NOT a generic explanation about "
            f"{resolved.get('target_name')} or the abstract concept.\n"
        )
        debug["context_blocks"].append("field_framing_pivot")

    # 4e — intent-specific directive
    if intent_data["intent"] == "ASTROLOGY":
        parts.append(
            "\nINTENT: ASTROLOGY.\n"
            "Answer from the SPECIFIC placement on the target's natal "
            "chart loaded above. NEVER write the textbook definition "
            "of a house or planet. If a placement is unavailable, say "
            "so explicitly — do not invent.\n"
        )
    elif intent_data["intent"] == "RELATIONSHIP_FIELD":
        parts.append(
            "\nINTENT: RELATIONSHIP_FIELD.\n"
            "Answer from the active field between speaker and target. "
            "Use the relationship_mapping context loaded above. Avoid "
            "psychoanalysing the target in isolation.\n"
        )
    elif intent_data["intent"] in ("HD", "ENNEAGRAM", "BAZI", "NUMEROLOGY"):
        parts.append(
            f"\nINTENT: {intent_data['intent']}.\n"
            f"Answer from the target's specific lens data above (NOT "
            f"the generic type description). When a relationship "
            f"exists, frame the answer as how this lens shows up "
            f"BETWEEN speaker and target.\n"
        )
    elif intent_data["intent"] == "FORUM_DYNAMICS":
        parts.append(
            "\nINTENT: FORUM_DYNAMICS.\n"
            "Answer from the FORUM DYNAMICS SUMMARY block above.\n"
        )

    # 4f — universal mirror voice rules
    parts.append(_MIRROR_VOICE_RULES)

    addendum = "".join(parts)
    return {
        "marker":               BUILD_MARKER,
        "frame":                mode,
        "resolved_target":      resolved,
        "relationship_role":    rel_info.get("relationship_role") if rel_info else None,
        "role_source":          rel_info.get("relationship_source") if rel_info else None,
        "intent":               intent_data["intent"],
        "house_number":         intent_data["house_number"],
        "life_domain":          life_domain,
        "spouse_auto_promoted": debug.get("spouse_auto_promoted", False),
        "layered_block_emitted": debug.get("layered_block_emitted", False),
        "system_prompt_addendum": addendum,
        "debug":                debug,
    }
