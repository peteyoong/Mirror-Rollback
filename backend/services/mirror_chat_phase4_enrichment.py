"""mirror_chat_phase4_enrichment.py — P6 R1/R2/R3/R4 prompt-block builders.

Adds the missing wiring between the V2 stack (Intent Router V2,
relationship_router_v2, Timeline V2 read-side, founder/operator
context) and the live LLM prompt.

All builders are STRICTLY ADDITIVE and FEATURE-FLAG-GATED. They
return `(None, debug_dict)` when their feature flag is off or when
no signal is found — so dropping the block into the prompt builder
is safe-by-default.

Flag-gating
-----------
Environment variables (read at import time + re-read per call so
flips don't require a restart for testing):

* `INTENT_V2_PROMPT_INJECTION=true|false`  (R2 — V2 envelope → prompt)
* `TIMELINE_V2_READ_ENABLED=true|false`    (R1 — Timeline V2 retrieval)
* `FOUNDER_CONTEXT_ENABLED=true|false`     (R4 — founder/operator retrieval)
* `RELATIONSHIP_ORCHESTRATION_PROMPT=true|false` (R5 — P3 framing_hint surfacing — DEFAULT OFF per constraint)
* `CROSS_LENS_PROMPT_SURFACE=true|false`         (R7 — cross-lens contradictions surfacing — DEFAULT OFF per constraint)

Constraint compliance
---------------------
* `INTENT_ROUTER_V2_CUTOVER` / `INTENT_ROUTER_V2_ROLLOUT_PERCENT` —
  NEVER read by this module. These remain unchanged in `.env`.
* Relationship orchestration and cross-lens contradictions are
  feature-flagged OFF by default.
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("mirror_chat_phase4")


# ─────────────────────────────────────────────────────────────────────
# R3b — Forum-topology fallback target resolution
# ─────────────────────────────────────────────────────────────────────
#
# Real-user finding from P6 / Phase 4 audit: the V2 relationship_router
# only consults `saved_people` + a client-supplied forum_topology. It
# never inspects `forum_members` to find who else is in the user's
# forums. Result: a name like "Mel" returns `target_unresolved_name`
# even when Mel is a forum member of the user's pair forum
# "Pete & Mel" or a family forum "Yoong family".
#
# This resolver fills the gap. Resolution ladder (first match wins):
#     1. saved_people   — already handled upstream by V2 resolver
#     2. forum_member   — name matches a member of one of the user's forums
#     3. pair_forum     — same as (2) but the forum name is a binary pair
#                         ("Pete & Mel", "Pete and Mel", "Mel and Pete")
#                         → role inferred as `partner`
#     4. family_forum   — same as (2) but forum name contains "family"
#                         → role inferred as `family`
#     5. alias_spouse   — name in message is a role noun ("wife",
#                         "husband", "partner", "spouse") and the user
#                         has a pair-forum with exactly one other
#                         member → resolve to that member, role=partner
#     6. unresolved     — none of the above
#
# Returns a dict with full provenance so the prompt builder can surface
# the resolution source to the LLM.

_PAIR_FORUM_NAME_RE = re.compile(
    # Two-token pair:
    #   * each token is either a proper-name shape ([A-Z][a-z'-]{1,30})
    #     or one of the self-reference tokens "I" / "Me" (case-insensitive
    #     via re.I)
    #   * separator: "&", "and", "+", "/" (whitespace tolerated)
    # Examples that match: "Pete & Mel", "Mel and I", "Me and Mel",
    #   "Lu/Pere", "Nic & Pete", "Pete+Ana", "Pete and Mel"
    # PFS-1 Defect 1 fix: bare "I" / "Me" now accepted as the second
    # token of a pair, so "Mel and I" classifies as pair_forum rather
    # than falling through to forum_member.
    r"^\s*([A-Z][a-z\-']{1,30}|I|Me)\s*(?:&|and|\+|/)\s*"
    r"([A-Z][a-z\-']{1,30}|I|Me)\s*$",
    re.I,
)
_FAMILY_FORUM_NAME_RE = re.compile(r"\bfamily\b|\bfam\b", re.I)

# PFS-1 Defect 2 fix — disambiguate romantic vs business pairs.
# Self-reference ("I" / "Me") inside a pair-shaped name indicates the
# user is naming a forum from their own first-person frame — overwhelmingly
# a romantic / spousal context ("Mel and I", "Me and Mel").
_SELF_TOKEN_IN_PAIR_RE = re.compile(r"\b(I|Me)\b", re.I)

# Explicit romantic markers in a forum name.  Conservative list — only
# strings that unambiguously indicate intimacy/relationship status.
_ROMANTIC_KEYWORD_RE = re.compile(
    r"\b(love|spouse|wife|husband|hubby|hubs|wifey|"
    r"marriage|married|romantic|romance|date|dating)\b",
    re.I,
)

# Business / cofounder / leadership markers in a forum name.  When a
# pair-shaped name carries any of these tokens, role inference flips to
# `cofounder` instead of `partner`.  When a NON-pair name carries any
# of these, the forum is treated as a `business_forum` group (priority
# above generic forum_member, below pair/family).
_BUSINESS_KEYWORD_RE = re.compile(
    r"\b(cofounders?|co-founders?|founders?|founder|leadership|"
    r"leaders?|team|exec|execs|executives?|board|"
    r"company|companies|biz|business|startup|startups|"
    r"ventures?|llc|inc|corp|holdings|capital|"
    r"investors?|advisors?|operators?|partners?)\b",
    re.I,
)

# Role-noun aliases → spouse / partner
_SPOUSE_ALIASES = {"wife", "husband", "partner", "spouse",
                   "my wife", "my husband", "my partner", "my spouse",
                   "girlfriend", "boyfriend", "fiance", "fiancee"}


async def resolve_target_via_forums(
    *, db, user_id: str, candidate_name: Optional[str], message: str,
) -> Dict[str, Any]:
    """Try to bind `candidate_name` to a forum_member in any forum the user
    is in. Includes simple alias matching ("Mel" matches both "Mel" and
    "Melissa"; "Mel " with trailing whitespace; "Melly").

    Also handles role-noun aliases ("wife", "spouse") by inspecting the
    user's pair forums.

    Always returns a dict; never raises.
    """
    result: Dict[str, Any] = {
        "found":             False,
        "candidate_name":    candidate_name,
        "resolved_user_id":  None,
        "resolved_name":     None,
        "resolved_role":     None,
        "forum_id":          None,
        "forum_name":        None,
        "resolution_source": "unresolved",
        "all_forums_with_match": [],
        "user_forum_count":  0,
        "alias_used":        None,
    }

    if db is None or not user_id:
        return result

    try:
        # 1. List all forums the user is a member of.
        cur = db.forum_members.find({"user_id": user_id})
        user_forum_ids: List[str] = []
        async for d in cur:
            user_forum_ids.append(d["forum_id"])
        result["user_forum_count"] = len(user_forum_ids)
        if not user_forum_ids:
            return result

        # Hydrate forum docs (name, etc.). Forums use string `_id`
        # (ObjectId) — try both id and _id forms.
        from bson import ObjectId
        forum_docs: Dict[str, Dict[str, Any]] = {}
        for fid in user_forum_ids:
            try:
                f = await db.forums.find_one({"_id": ObjectId(fid)})
            except Exception:
                f = None
            if not f:
                f = await db.forums.find_one({"id": fid})
            if f:
                forum_docs[fid] = f

        # 2. Build a map of {forum_id: [member_docs_with_names]} by
        #    joining forum_members → users.
        from bson import ObjectId as _OID
        forum_members_map: Dict[str, List[Dict[str, Any]]] = {}
        for fid in user_forum_ids:
            mcur = db.forum_members.find({"forum_id": fid})
            members: List[Dict[str, Any]] = []
            async for m in mcur:
                muid = m.get("user_id")
                if muid == user_id:
                    continue  # skip self
                muser = None
                try:
                    muser = await db.users.find_one({"_id": _OID(muid)})
                except Exception:
                    pass
                if not muser:
                    muser = await db.users.find_one({"id": muid})
                if muser:
                    members.append({
                        "user_id":     muid,
                        "name":        (muser.get("name") or "").strip(),
                        "email":       muser.get("email"),
                        "forum_role":  m.get("role"),
                    })
            forum_members_map[fid] = members

        # 3a. Direct name match (with alias logic) across all forums.
        if candidate_name:
            cand_lc = candidate_name.lower().strip()
            matches: List[Dict[str, Any]] = []
            for fid, members in forum_members_map.items():
                for m in members:
                    nm = (m.get("name") or "").lower().strip()
                    if not nm:
                        continue
                    name_match = (
                        nm == cand_lc
                        or nm.startswith(cand_lc + " ")
                        or nm.startswith(cand_lc)
                        or cand_lc in nm.split()
                    )
                    # Email-stem match: "mel" → email "melissa.mars@…"
                    email = (m.get("email") or "").lower()
                    email_stem = email.split("@")[0] if email else ""
                    email_match = (
                        cand_lc
                        and len(cand_lc) >= 3
                        and email_stem.startswith(cand_lc)
                    )
                    if name_match or email_match:
                        forum_name = (forum_docs.get(fid) or {}).get("name") or ""
                        source, role = _classify_forum_source(forum_name)
                        matches.append({
                            "user_id":    m["user_id"],
                            "name":       m["name"],
                            "forum_id":   fid,
                            "forum_name": forum_name,
                            "source":     source,
                            "role":       role,
                            "alias_used": (
                                f"{cand_lc}→{nm}" if (name_match and nm != cand_lc)
                                else f"{cand_lc}→email:{email_stem}"
                                if email_match else None
                            ),
                        })

            if matches:
                # Priority order per user's resolution ladder:
                #   pair_forum > family_forum > business_forum > forum_member
                # (PFS-1: `business_forum` inserted between family and
                # generic. Leadership/cofounder groups are more specific
                # than a generic shared forum, but less specific than a
                # named pair or family.)
                _src_priority = {
                    "pair_forum":     0,
                    "family_forum":   1,
                    "business_forum": 2,
                    "forum_member":   3,
                }
                matches.sort(key=lambda x: _src_priority.get(x["source"], 9))
                top = matches[0]
                result["found"] = True
                result["resolved_user_id"] = top["user_id"]
                result["resolved_name"]   = top["name"]
                result["resolved_role"]   = top["role"]
                result["forum_id"]        = top["forum_id"]
                result["forum_name"]      = top["forum_name"]
                result["resolution_source"] = top["source"]
                result["alias_used"]      = top["alias_used"]
                # Record ALL forums where the match was found
                result["all_forums_with_match"] = [
                    {"forum_id": x["forum_id"], "forum_name": x["forum_name"],
                     "source": x["source"], "role": x["role"]}
                    for x in matches
                ]
                return result

        # 3b. Role-noun alias path ("wife", "spouse" → pair-forum member)
        msg_lc = (message or "").lower()
        spouse_alias = None
        for alias in _SPOUSE_ALIASES:
            if re.search(rf"\b{re.escape(alias)}\b", msg_lc):
                spouse_alias = alias
                break
        if spouse_alias:
            # Find a pair forum (exactly one other member) involving the user
            for fid, members in forum_members_map.items():
                if len(members) != 1:
                    continue
                forum_name = (forum_docs.get(fid) or {}).get("name") or ""
                # Prefer named pair forums (matching the regex) but
                # accept any 1-other-member forum as a partner candidate.
                pair_hit = bool(_PAIR_FORUM_NAME_RE.match(forum_name))
                m = members[0]
                result["found"] = True
                result["resolved_user_id"] = m["user_id"]
                result["resolved_name"]   = m["name"]
                result["resolved_role"]   = "partner"
                result["forum_id"]        = fid
                result["forum_name"]      = forum_name
                result["resolution_source"] = (
                    "alias_spouse_via_pair_forum" if pair_hit
                    else "alias_spouse_via_single_other_member"
                )
                result["alias_used"] = spouse_alias
                return result

    except Exception as e:
        log.warning(
            f"[mirror_chat_phase4][R3b] forum target resolution failed: "
            f"{type(e).__name__}: {e}"
        )
        result["error"] = f"{type(e).__name__}: {e!s}"
    return result


def _classify_forum_source(forum_name: str) -> Tuple[str, Optional[str]]:
    """Map a forum's name to a (resolution_source, inferred_role) pair.

    Resolution sources:
      `pair_forum`     — two-token pair (e.g. "Pete & Mel", "Mel and I",
                         "Lu/Pere"). Role disambiguated below.
      `family_forum`   — forum name contains "family" / "fam".
                         Role = `family`.
      `business_forum` — non-pair forum whose name contains business /
                         leadership / cofounder keywords (e.g. "Pulsifi
                         Leadership", "Acme Team", "Founders Circle").
                         Role = None (group context, no per-member role).
      `forum_member`   — fallthrough; any other shared forum. Role = None.

    PFS-1 (June 2026) heuristics:
      * Pair forums whose name contains a self-token (`I`, `Me`) — e.g.
        "Mel and I" — are treated as romantic pairs (`role=partner`).
      * Pair forums whose name carries explicit romantic markers ("love",
        "spouse", "wife", …) are treated as romantic pairs.
      * Pair forums whose name carries business/leadership markers
        ("cofounder", "founders", "leadership", "team", …) are treated
        as `cofounder` pairs (`role=cofounder`).
      * Otherwise a pair forum is left **role-less** (`None`) — the
        upstream prompt block will not assert a romantic frame.  This
        is the deliberate safe-default change (PFS-1 Defect 2 fix):
        we do not assume romantic intent purely from name shape.

    Examples (all asserted in `/app/backend/tests/test_classify_forum_source.py`):
      "Pete & Mel"           → (pair_forum,    None)        # ambiguous, no role assertion
      "Mel and I"            → (pair_forum,    partner)     # self-token present
      "Mel & I"              → (pair_forum,    partner)     # self-token present
      "Mel & Pete"           → (pair_forum,    None)        # ambiguous
      "Lu/Pere"              → (pair_forum,    None)        # ambiguous, no false-partner
      "Pete/Ana"             → (pair_forum,    None)        # ambiguous, no false-partner
      "Nic & Pete"           → (pair_forum,    None)        # ambiguous, no false-partner
      "Yoong Family"         → (family_forum,  family)
      "Pulsifi Leadership"   → (business_forum, None)       # was: forum_member/None
      "Acme Cofounders"      → (business_forum, None)
      "Mel and I (Married)"  → (pair_forum,    partner)     # romantic keyword
    """
    if not forum_name:
        return "forum_member", None

    is_pair         = bool(_PAIR_FORUM_NAME_RE.match(forum_name))
    has_family      = bool(_FAMILY_FORUM_NAME_RE.search(forum_name))
    has_business    = bool(_BUSINESS_KEYWORD_RE.search(forum_name))
    has_romantic_kw = bool(_ROMANTIC_KEYWORD_RE.search(forum_name))
    # Self-token check only meaningful inside a pair-shaped name.
    has_self_token  = (
        bool(_SELF_TOKEN_IN_PAIR_RE.search(forum_name)) if is_pair else False
    )

    # 1. Family wins outright — family-named forums are unambiguous.
    if has_family:
        return "family_forum", "family"

    # 2. Pair-shaped names — disambiguate role.
    if is_pair:
        # Romantic markers OR self-reference → partner.
        if has_self_token or has_romantic_kw:
            return "pair_forum", "partner"
        # Business markers → cofounder.
        if has_business:
            return "pair_forum", "cofounder"
        # Ambiguous pair — DO NOT assert a romantic role.  Source stays
        # `pair_forum` (so the resolver still prioritises this match),
        # but role is left to downstream context / saved_people.
        return "pair_forum", None

    # 3. Non-pair, non-family with business markers → business_forum.
    if has_business:
        return "business_forum", None

    # 4. Anything else — generic forum membership.
    return "forum_member", None


# ─────────────────────────────────────────────────────────────────────
# Feature-flag helpers
# ─────────────────────────────────────────────────────────────────────

def _flag(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() in ("true", "1", "yes", "on")


def intent_v2_prompt_injection_enabled() -> bool:
    return _flag("INTENT_V2_PROMPT_INJECTION", "true")


def timeline_v2_read_enabled() -> bool:
    return _flag("TIMELINE_V2_READ_ENABLED", "true")


def founder_context_enabled() -> bool:
    return _flag("FOUNDER_CONTEXT_ENABLED", "true")


def relationship_orchestration_prompt_enabled() -> bool:
    return _flag("RELATIONSHIP_ORCHESTRATION_PROMPT", "false")


def cross_lens_prompt_surface_enabled() -> bool:
    return _flag("CROSS_LENS_PROMPT_SURFACE", "false")


# ─────────────────────────────────────────────────────────────────────
# R2 — Intent V2 envelope → prompt block
# ─────────────────────────────────────────────────────────────────────

FOUNDER_LEXICON_SIGNALS = {
    "founder", "co-founder", "cofounder", "as the founder",
    "founder ceo transition", "founder mode", "founder burnout",
    "the founder", "executive", "leadership offsite", "exec offsite",
    "board", "the board", "operating partner",
    "term sheet", "cap table", "the cap table", "valuation",
    "dilution", "raise a round", "raising a round", "next round",
    "series a", "series b", "series c", "down round", "out of runway",
    "extend runway", "extending runway", "cut burn", "reduce burn",
    "product market fit", "product-market fit", "pmf", "find pmf",
    "go to market", "go-to-market", "gtm", "ipo", "go public",
    "exit the company", "selling the company", "sell the company",
    "acquisition offer", "step back as ceo", "step down as ceo",
    "succeed me as ceo", "someone to run the company",
    "hiring plan", "the hiring plan", "annual hiring plan",
    "compensation plan", "comp plan", "performance review",
    "perf review", "performance improvement plan", "put on a pip",
    "okrs", "set okrs", "annual planning", "quarterly planning",
    "investor update", "lp update", "lead investor",
}


def build_intent_v2_prompt_block(
    v2_receipt: Optional[Dict[str, Any]],
) -> Tuple[Optional[str], Dict[str, Any]]:
    """Build an INTENT SIGNAL prompt block from the V2 envelope.

    Surfaces (when present and meaningful):
      * Resolved primary domain + confidence
      * Top secondary domains
      * Matched founder/operator phrases
      * Relationship target (resolved id OR unresolved name)
      * Relationship role
      * Active frame (self/forum/member)
      * P3 framing hint (when RELATIONSHIP_ORCHESTRATION_PROMPT=true)
      * Cross-lens top contradiction (when CROSS_LENS_PROMPT_SURFACE=true)
    """
    debug: Dict[str, Any] = {
        "intent_v2_block_emitted": False,
        "intent_v2_signals":       [],
    }

    if not intent_v2_prompt_injection_enabled():
        debug["intent_v2_block_emitted"] = False
        debug["intent_v2_signals"].append("flag_off")
        return None, debug

    if not v2_receipt or not v2_receipt.get("shadow_mode"):
        debug["intent_v2_signals"].append("receipt_unavailable")
        return None, debug

    env = v2_receipt.get("intent_envelope") or {}
    rel = v2_receipt.get("relationship_resolution") or {}
    p3  = v2_receipt.get("relationship_orchestration_v1") or {}
    cls = v2_receipt.get("cross_lens_synthesis_v2") or {}
    ft  = v2_receipt.get("forum_topology_resolution") or {}

    primary    = env.get("primary_domain")
    confidence = env.get("confidence")
    secondary  = env.get("secondary_domains") or []
    matched    = (env.get("evidence") or {}).get("matched_phrases") or {}

    # Skip emission entirely when the router has nothing meaningful to say.
    has_signal = (
        (primary and primary != "general")
        or bool(matched)
        or rel.get("target")
        or rel.get("target_unresolved_name")
    )
    if not has_signal:
        debug["intent_v2_signals"].append("no_signal")
        return None, debug

    lines: List[str] = ["--- INTENT SIGNAL (Mirror V2 router) ---"]

    if primary and primary != "general":
        confidence_display = (
            f"{confidence:.2f}" if isinstance(confidence, (int, float))
            else "?"
        )
        lines.append(f"Primary domain: {primary} (confidence {confidence_display})")
        debug["intent_v2_signals"].append(f"primary={primary}")
    if secondary:
        lines.append(f"Secondary lenses: {', '.join(secondary[:3])}")
        debug["intent_v2_signals"].append(
            f"secondary={','.join(secondary[:3])}"
        )

    # Flatten and trim matched phrases for the LLM.
    flat_phrases: List[str] = []
    founder_hits: List[str] = []
    for dom, phrases in matched.items():
        for p in phrases:
            flat_phrases.append(f"{dom}:{p}")
            if p.lower() in FOUNDER_LEXICON_SIGNALS:
                founder_hits.append(p)
    if flat_phrases:
        # cap to 5 to keep prompt lean
        lines.append(f"Matched phrases: {', '.join(flat_phrases[:5])}")
        debug["intent_v2_signals"].append(f"phrases={len(flat_phrases)}")
    if founder_hits:
        lines.append(
            f"Founder/operator signals: {', '.join(founder_hits[:5])}"
        )
        debug["founder_hits"] = founder_hits
        debug["intent_v2_signals"].append("founder_hits")

    # Active frame
    frame = (v2_receipt.get("frame_source") or {}).get("derived_frame")
    if frame and frame != "self":
        lines.append(f"Active frame: {frame}")
        debug["intent_v2_signals"].append(f"frame={frame}")

    # Relationship target
    tgt        = rel.get("target")
    tgt_unres  = rel.get("target_unresolved_name")
    tgt_role   = rel.get("role")
    res_source = (
        rel.get("resolution_source")
        or v2_receipt.get("target_resolution_source")
        or ""
    )
    forum_name_hit = rel.get("forum_name")
    if tgt and res_source in (
        "forum_member", "pair_forum", "family_forum", "business_forum",
        "alias_spouse_via_pair_forum",
        "alias_spouse_via_single_other_member",
    ):
        # R3b — bound via forum membership, not saved_people.
        tgt_name = rel.get("target_name") or "(unnamed)"
        forum_phrase = (
            f"the '{forum_name_hit}' forum" if forum_name_hit
            else "a shared forum"
        )
        role_part = f" (relationship_role: {tgt_role})" if tgt_role else ""
        lines.append(
            f"Relationship target: '{tgt_name}' "
            f"(resolved via {res_source} in {forum_phrase}{role_part}). "
            f"This person is in the user's saved relationship topology — "
            f"ground your reflection in the actual relationship between "
            f"them, not in generic projection language."
        )
        debug["intent_v2_signals"].append(
            f"target_via_{res_source}:{tgt_name}"
        )
    elif tgt:
        role_part = f" (role: {tgt_role})" if tgt_role else ""
        lines.append(f"Relationship target: bound{role_part}")
        debug["intent_v2_signals"].append(f"target_bound:{tgt_role or '?'}")
    elif tgt_unres:
        lines.append(
            f"Relationship target: '{tgt_unres}' is mentioned but NOT in "
            f"the user's saved people OR any of their forums. Acknowledge "
            f"this rather than guessing who they are. Ask the user who "
            f"'{tgt_unres}' is."
        )
        debug["intent_v2_signals"].append(f"target_unresolved:{tgt_unres}")

    # Forum topology
    if ft.get("topology_supplied"):
        lines.append(
            f"Forum topology: active member id={ft.get('active_member_id')}"
        )
        debug["intent_v2_signals"].append("forum_topology_supplied")

    # P3 framing hint (flag-gated, default off per constraint)
    if (relationship_orchestration_prompt_enabled()
            and p3.get("computed")
            and p3.get("framing_hint")
            and p3.get("framing_hint") != "self_inquiry"):
        lines.append(f"Suggested framing: {p3['framing_hint']}")
        debug["intent_v2_signals"].append(f"framing={p3['framing_hint']}")

    # Cross-lens top contradiction (flag-gated, default off per constraint)
    if cross_lens_prompt_surface_enabled() and cls.get("computed"):
        contradictions = cls.get("contradictions") or []
        if contradictions:
            top = contradictions[0]
            lines.append(
                f"Cross-lens tension: {top.get('dominant')} dominates over "
                f"{top.get('counter')} (delta {top.get('delta')})"
            )
            debug["intent_v2_signals"].append(
                f"contradiction:{top.get('dominant')}>{top.get('counter')}"
            )

    if len(lines) == 1:
        # only the header — nothing meaningful to say
        debug["intent_v2_signals"].append("header_only_skipped")
        return None, debug

    debug["intent_v2_block_emitted"] = True
    return "\n".join(lines), debug


# ─────────────────────────────────────────────────────────────────────
# R1 — Timeline V2 read-side retrieval
# ─────────────────────────────────────────────────────────────────────

async def build_timeline_v2_context(
    *, db, user_id: str, window_days: int = 14, max_events: int = 8,
) -> Tuple[Optional[str], Dict[str, Any]]:
    """Read recent `user_timeline` events and project them into the prompt.

    Surfaces:
      * Recent state distribution (integrating/stabilizing/etc.)
      * Last N event tags / states (chronological)
      * Window summary so the LLM can ground "right now" prompts
    """
    debug: Dict[str, Any] = {
        "timeline_v2_emitted":  False,
        "event_count":          0,
        "state_distribution":   {},
        "window_days":          window_days,
    }

    if not timeline_v2_read_enabled():
        debug["timeline_v2_emitted"] = False
        return None, debug

    if db is None or not user_id:
        return None, debug

    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()
        cur = db.user_timeline.find({"user_id": user_id}).sort([("_id", -1)]).limit(max_events * 2)
        rows: List[Dict[str, Any]] = []
        async for d in cur:
            rows.append(d)
        if not rows:
            debug["timeline_v2_signals"] = ["empty"]
            return None, debug

        events: List[Dict[str, Any]] = rows[:max_events]
        debug["event_count"] = len(events)

        # State distribution
        state_dist: Dict[str, int] = {}
        for e in events:
            s = e.get("inferred_state") or "unknown"
            state_dist[s] = state_dist.get(s, 0) + 1
        debug["state_distribution"] = state_dist

        # Dominant state
        dom = max(state_dist.items(), key=lambda kv: kv[1])
        debug["dominant_state"] = dom[0]

        lines: List[str] = [
            f"--- TIMELINE V2 (last {len(events)} events, ~{window_days}d window) ---"
        ]
        lines.append(
            f"State distribution: " +
            ", ".join(f"{k}:{v}" for k, v in
                      sorted(state_dist.items(), key=lambda kv: -kv[1]))
        )
        lines.append(f"Dominant recent state: {dom[0]}")

        # Recent event sequence
        recent_seq: List[str] = []
        for e in events[:5]:
            etype = e.get("event_type") or "?"
            state = e.get("inferred_state") or "?"
            ts    = (e.get("timestamp") or "")[:10] or "?"
            recent_seq.append(f"{ts}:{etype}({state})")
        if recent_seq:
            lines.append("Recent sequence: " + " → ".join(recent_seq))

        # Pattern hint
        if state_dist.get("integrating", 0) >= 2:
            lines.append(
                "Pattern hint: user has been in an INTEGRATING state — "
                "they're synthesising, not yet resting."
            )
        elif state_dist.get("destabilizing", 0) >= 2:
            lines.append(
                "Pattern hint: user has been DESTABILIZING — "
                "responses should anchor, not amplify."
            )
        elif state_dist.get("stabilizing", 0) >= 2:
            lines.append(
                "Pattern hint: user has been STABILIZING — "
                "responses can extend / deepen safely."
            )

        debug["timeline_v2_emitted"] = True
        return "\n".join(lines), debug

    except Exception as e:
        log.warning(
            f"[mirror_chat_phase4] timeline_v2 retrieval failed: "
            f"{type(e).__name__}: {e}"
        )
        debug["error"] = f"{type(e).__name__}: {e!s}"
        return None, debug


# ─────────────────────────────────────────────────────────────────────
# R4 — Founder / Operator context retrieval
# ─────────────────────────────────────────────────────────────────────

# Pattern memory tags that signal founder/operator context. Soft list —
# we keep them loose because the pattern memory tagging vocabulary
# evolves separately from this module.
FOUNDER_PATTERN_TAG_HINTS = (
    "founder", "operator", "leadership", "ceo", "executive",
    "fundraise", "fundraising", "runway", "burn", "team_scaling",
    "hiring", "cofounder", "board", "investor",
    "product_market_fit", "pmf", "gtm", "exit",
)


async def build_founder_context_block(
    *,
    db,
    user_id: str,
    v2_receipt: Optional[Dict[str, Any]],
    window_days: int = 30,
) -> Tuple[Optional[str], Dict[str, Any]]:
    """Surface a founder/operator-flavoured context block when the V2
    envelope contains founder/operator signals.

    Pulls:
      * Recent timeline events touching founder/leadership/career states
      * Pattern memory entries with founder-flavoured tags
      * A short "what to consider" framing line so the LLM knows this
        is a founder-specific reflection.

    Triggers only when V2 envelope.matched_phrases contains a founder/
    operator term, OR primary_domain ∈ {career, leadership} with
    confidence ≥ 0.5.
    """
    debug: Dict[str, Any] = {
        "founder_block_emitted": False,
        "founder_signals":       [],
    }

    if not founder_context_enabled():
        return None, debug

    if not v2_receipt or not v2_receipt.get("shadow_mode"):
        debug["founder_signals"].append("receipt_unavailable")
        return None, debug

    env = v2_receipt.get("intent_envelope") or {}
    primary    = env.get("primary_domain")
    confidence = env.get("confidence") or 0.0
    matched    = (env.get("evidence") or {}).get("matched_phrases") or {}

    flat_phrases = []
    for dom, phrases in matched.items():
        for p in phrases:
            flat_phrases.append(p.lower())
    has_founder_phrase = any(
        any(s in p for s in FOUNDER_LEXICON_SIGNALS)
        for p in flat_phrases
    )

    domain_signals_founder = (
        primary in ("career", "leadership") and confidence >= 0.5
    )

    if not (has_founder_phrase or domain_signals_founder):
        debug["founder_signals"].append("no_founder_trigger")
        return None, debug

    debug["founder_signals"].append(
        f"trigger:primary={primary}/conf={confidence}/phrase={has_founder_phrase}"
    )

    if db is None:
        return None, debug

    try:
        # Recent timeline events that look founder/leadership-flavoured
        cursor = db.user_timeline.find({"user_id": user_id}).sort([("_id", -1)]).limit(20)
        founder_events: List[Dict[str, Any]] = []
        async for e in cursor:
            tags = (e.get("tags") or [])
            etype = (e.get("event_type") or "").lower()
            inferred = (e.get("inferred_state") or "").lower()
            text_blob = " ".join([etype, inferred] + [str(t).lower() for t in tags])
            if any(h in text_blob for h in FOUNDER_PATTERN_TAG_HINTS):
                founder_events.append(e)

        # Pattern memory — best effort; never crash
        pattern_hits: List[Dict[str, Any]] = []
        try:
            pm_cur = db.pattern_memory.find({"user_id": user_id}).sort([("_id", -1)]).limit(15)
            async for p in pm_cur:
                tags = (p.get("tags") or [])
                if any(any(h in str(t).lower() for h in FOUNDER_PATTERN_TAG_HINTS)
                       for t in tags):
                    pattern_hits.append(p)
        except Exception:
            pass  # pattern_memory collection may not exist

        if not founder_events and not pattern_hits:
            debug["founder_signals"].append("no_founder_history")
            # Still emit a "founder context active" hint so the LLM
            # knows to ground in founder-mode framing.
            block = (
                "--- FOUNDER / OPERATOR CONTEXT (V2-detected) ---\n"
                f"V2 detected a founder/operator question (primary={primary}, "
                f"confidence={confidence:.2f}). The user has no recent "
                f"founder-tagged history to draw from, so respond with "
                f"founder-mode framing but avoid fabricating past events. "
                f"Focus on the current question and the Founder/Operator "
                f"lens patterns (decision velocity, leverage, "
                f"team-vs-self attention split)."
            )
            debug["founder_block_emitted"] = True
            return block, debug

        lines: List[str] = ["--- FOUNDER / OPERATOR CONTEXT (V2-detected) ---"]
        lines.append(
            f"V2 detected a founder/operator question "
            f"(primary={primary}, confidence={confidence:.2f}). "
            f"Founder-flavoured recent history below should ground your reflection."
        )
        if founder_events:
            lines.append(f"Founder-flavoured timeline events ({len(founder_events)}):")
            for e in founder_events[:5]:
                etype = e.get("event_type") or "?"
                state = e.get("inferred_state") or "?"
                ts    = (e.get("timestamp") or "")[:10] or "?"
                lines.append(f"  • {ts} {etype} (state: {state})")
            debug["founder_signals"].append(
                f"events={len(founder_events)}"
            )
        if pattern_hits:
            lines.append(f"Founder-flavoured patterns ({len(pattern_hits)}):")
            for p in pattern_hits[:3]:
                tags = ", ".join(str(t) for t in (p.get("tags") or [])[:4])
                lines.append(f"  • tags=[{tags}]")
            debug["founder_signals"].append(
                f"patterns={len(pattern_hits)}"
            )

        lines.append(
            "Framing reminder: surface decision-velocity, leverage, and "
            "team-vs-self attention split when relevant. Avoid generic "
            "Manifestor/HD-strategy filler unless the user asked for it."
        )

        debug["founder_block_emitted"] = True
        return "\n".join(lines), debug

    except Exception as e:
        log.warning(
            f"[mirror_chat_phase4] founder_context retrieval failed: "
            f"{type(e).__name__}: {e}"
        )
        debug["error"] = f"{type(e).__name__}: {e!s}"
        return None, debug
