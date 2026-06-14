"""relationship_field_v2.py — Slice 1 of the Relationship Field V2 design.

Canonical resolver service to be consumed (in later slices) by:
    - Ask Mirror (generalist + lens)
    - Forum Chat
    - Astrology Chat
    - How This Person Maps To Me
    - Relationship Insight V2

SLICE 1 SCOPE (this file):
    * Build the resolver only. No wiring into any surface.
    * Read-only against existing collections.
    * Layer relationship_stance + directionality + provenance + conflicts
      on top of the existing edges-first ladder in
      `services.relationship_resolver.resolve_relationship`.
    * Preserve relationship_role verbatim (don't rename today's tokens).
    * No DB writes. No prompt changes. No flag flips. No migrations.

DESIGN REFERENCE:
    /app/backend/audit_reports/RELATIONSHIP_FIELD_V2_DESIGN_REFINEMENT.md

USER-APPROVED GUARDRAILS (slice-1 of N):
    G1. Provisional stances must NEVER override an explicit
        `forum_relationship_edges` role. Edges always win.
    G2. Lexicon-only matches may yield `proposed_unresolved` or
        low-confidence target hints — they must NOT bind a high-
        confidence RESOLVED TARGET unless backed by one of:
          - forum_relationship_edges
          - saved_people / relationship_mappings
          - forum topology / last_target_id
          - explicit user phrase naming the role
    G3. self → `self_subject` stance (never null).
    G4. URL `context` mismatches vs edge graph: edges win; conflict is
        recorded in `conflicts[]`. No 409 raised.
    G5. `prior_relational_memory_keys`: pointer-only (no eager-load).
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

ROUTER_VERSION = "relationship_field_v2.0.0-slice1"

# Confidence threshold above which downstream surfaces may treat the
# resolution as HIGH CONFIDENCE (per G2 in the design refinement).
HIGH_CONFIDENCE_THRESHOLD = 0.70


# ════════════════════════════════════════════════════════════════════
# STANCE TAXONOMY
# ════════════════════════════════════════════════════════════════════

# G1 — FROZEN core. Never edit without explicit user approval.
CORE_STANCE_MAP: Dict[str, str] = {
    "spouse":        "covenant_partner",
    "child":         "steward_guardian",
    "parent":        "lineage_source",
    "sibling":       "shared_origin",
    "close_friend":  "chosen_ally",
    "mentor":        "guide",
    "forum_member":  "peer",
    "unknown":       "neutral",
}

# PROVISIONAL — may be revised. Never overrides an explicit edges-derived
# role (G1). Used only when the role string itself maps here AND the
# resolution source is not `forum_relationship_edges`.
PROVISIONAL_STANCE_MAP: Dict[str, str] = {
    "former_partner":   "severed_covenant",
    "ex_partner":       "severed_covenant",
    "mentee":           "apprentice",
    "coach":            "accountable_guide",
    "coachee":          "accountable_apprentice",
    "client":           "accountable_apprentice",
    "cofounder":        "co_architect",
    "business_partner": "co_architect",
    "advisor":          "counsel",
    "investor":         "stakeholder",
    "manager":          "authority_above",
    "boss":             "authority_above",
    "employee":         "authority_below",
    "direct_report":    "authority_below",
    "authority_figure": "power_holder",
    "collaborator":     "peer_in_motion",
    "forum_mate":       "peer",
    "close_circle":     "chosen_ally",   # closeness-leaning provisional
    "friend":           "chosen_ally",
    "colleague":        "peer_in_motion",
    "self":             "self_subject",
}

# G1 enforcement: which stances are FROZEN-core and therefore may not
# be overridden by any provisional mapping.
_FROZEN_STANCES: set = set(CORE_STANCE_MAP.values())


# ════════════════════════════════════════════════════════════════════
# DIRECTIONALITY TAXONOMY (first-class per user disposition #2)
# ════════════════════════════════════════════════════════════════════

# Mapping from canonical role → directionality from the viewer's POV.
# SYMMETRIC      → both give/receive equally (peer, spouse, sibling)
# USER_AS_GIVER  → user is the source of stewardship / responsibility
# USER_AS_RECEIVER → user is the recipient of inheritance / guidance
_DIRECTIONALITY_BY_ROLE: Dict[str, str] = {
    "spouse":         "SYMMETRIC",
    "partner":        "SYMMETRIC",
    "sibling":        "SYMMETRIC",
    "close_friend":   "SYMMETRIC",
    "friend":         "SYMMETRIC",
    "forum_member":   "SYMMETRIC",
    "close_circle":   "SYMMETRIC",
    "collaborator":   "SYMMETRIC",
    "forum_mate":     "SYMMETRIC",
    "cofounder":      "SYMMETRIC",
    "business_partner": "SYMMETRIC",

    "child":          "USER_AS_GIVER",
    "employee":       "USER_AS_GIVER",
    "direct_report":  "USER_AS_GIVER",
    "mentee":         "USER_AS_GIVER",
    "coachee":        "USER_AS_GIVER",
    "client":         "USER_AS_GIVER",

    "parent":         "USER_AS_RECEIVER",
    "mentor":         "USER_AS_RECEIVER",
    "manager":        "USER_AS_RECEIVER",
    "boss":           "USER_AS_RECEIVER",
    "advisor":        "USER_AS_RECEIVER",
    "investor":       "USER_AS_RECEIVER",
    "authority_figure": "USER_AS_RECEIVER",

    "ex_partner":     "SYMMETRIC",
    "former_partner": "SYMMETRIC",
    "coach":          "USER_AS_GIVER",       # user gives to coachee
                                              # NOTE: when role=coach the
                                              # viewer IS the coach, so
                                              # user is giver
}


# ════════════════════════════════════════════════════════════════════
# ENUM CONSTANTS
# ════════════════════════════════════════════════════════════════════

class ActiveFrame:
    SELF         = "SELF"
    MEMBER       = "MEMBER"
    FORUM        = "FORUM"
    PAIRWISE     = "PAIRWISE"        # Slice A — two specific targets
    MULTI_PERSON = "MULTI_PERSON"    # Slice A — scope class
    AMBIGUOUS    = "AMBIGUOUS"       # Slice A — multi-candidate clarification


class Closeness:
    HIGH   = "HIGH"
    MEDIUM = "MEDIUM"
    LOW    = "LOW"


class ResolutionSource:
    EDGES               = "forum_relationship_edges"
    EXPLICIT_MAP        = "explicit_map"
    SAVED_PEOPLE        = "saved_people"
    FORUM_MEMBERS       = "forum_members"
    FORUM_INFERENCE     = "forum_inference"
    MEMBER_ALIAS_LEX    = "member_alias_lexicon"
    PRONOUN_MEMORY      = "pronoun_memory"
    PROPOSED_UNRESOLVED = "proposed_unresolved"
    SELF_NO_TARGET      = "self_no_target"
    AT_MENTION          = "at_mention"           # Slice A
    PAIRWISE_PATTERN    = "pairwise_pattern"     # Slice A
    SCOPE_CLASS         = "scope_class"          # Slice A
    FORUM_INTENT        = "forum_intent"         # Slice A
    AMBIGUITY           = "ambiguity"            # Slice A — multi-candidate
    NONE                = "none"


# Resolution sources that COUNT toward HIGH-CONFIDENCE binding (G2).
_HIGH_CONFIDENCE_SOURCES: set = {
    ResolutionSource.EDGES,
    ResolutionSource.EXPLICIT_MAP,
    ResolutionSource.SAVED_PEOPLE,
    ResolutionSource.FORUM_MEMBERS,
    ResolutionSource.PRONOUN_MEMORY,    # only when last_target_id was edge-bound
}


# ════════════════════════════════════════════════════════════════════
# DATA CLASS
# ════════════════════════════════════════════════════════════════════

@dataclass
class RelationshipField:
    # Identity
    self_user_id: str
    target_user_id: Optional[str] = None
    target_name: Optional[str] = None
    target_aliases: List[str] = field(default_factory=list)

    # Frame & topology
    active_frame: str = ActiveFrame.SELF
    forum_id: Optional[str] = None
    forum_name: Optional[str] = None
    forum_topology: Optional[Dict[str, Any]] = None

    # Role + stance
    relationship_role: Optional[str] = None
    relationship_stance: str = "neutral"
    closeness: str = Closeness.LOW
    emotional_weight: str = Closeness.LOW
    directionality: Optional[str] = None

    # Provenance
    resolution_source: str = ResolutionSource.NONE
    resolution_path: List[str] = field(default_factory=list)
    confidence: float = 0.0
    conflicts: List[str] = field(default_factory=list)
    missing_data: List[str] = field(default_factory=list)
    router_version: str = ROUTER_VERSION

    # ── Slice A — multi-target / scope / ambiguity (additive) ──
    target_user_id_b: Optional[str] = None
    target_name_b:    Optional[str] = None
    scope_class:      Optional[str] = None
    ambiguity_candidates: List[Dict[str, Any]] = field(default_factory=list)

    # Downstream hints — populated for §3 of design ref. In slice-1
    # these are reserved placeholders (None / empty) and will be
    # populated in slice-2 (prompt-block consolidation) and slice-3
    # (lens-priority injection).
    framing_hint: Optional[str] = None
    domain_bias: Optional[str] = None
    lens_priority: List[str] = field(default_factory=list)
    prior_relational_memory_keys: List[str] = field(default_factory=list)

    # Receipt-only proposed action — fires for proposed_unresolved.
    proposed_action: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ════════════════════════════════════════════════════════════════════
# STANCE / DIRECTIONALITY DERIVATION
# ════════════════════════════════════════════════════════════════════

def _derive_stance(role: Optional[str], source: str) -> Tuple[str, List[str]]:
    """Return (stance, applied_rules).

    G1 — frozen core wins.
    G1 — provisional mappings are *not* allowed to override a
    `forum_relationship_edges`-derived role (the edge graph is canonical).

    Resolution order inside this function:
      1. role token matches CORE_STANCE_MAP → return that stance
      2. role token matches PROVISIONAL_STANCE_MAP AND the resolution
         source is not the edge graph → return provisional stance
      3. role token matches PROVISIONAL_STANCE_MAP AND source IS edges
         → still return provisional, but record the guardrail in
           applied_rules so the dashboard can see we let it through
           (edge tokens like `forum_mate` legitimately have only
           provisional stances; the guardrail is against contradiction,
           not against use).
      4. role is None / empty → stance=`neutral`, source-independent.
    """
    rules: List[str] = []
    if not role:
        rules.append("stance:no_role->neutral")
        return CORE_STANCE_MAP["unknown"], rules

    role_lc = role.strip().lower()

    if role_lc in CORE_STANCE_MAP:
        stance = CORE_STANCE_MAP[role_lc]
        rules.append(f"stance:core:{role_lc}->{stance}")
        return stance, rules

    if role_lc in PROVISIONAL_STANCE_MAP:
        stance = PROVISIONAL_STANCE_MAP[role_lc]
        # G1 enforcement check — provisional must NOT be a frozen-core
        # value masquerading. (If a provisional row mapped to a core
        # stance the audit trail would surface it; we don't *drop* the
        # mapping, but we mark it as audit-flagged.)
        if stance in _FROZEN_STANCES and role_lc not in CORE_STANCE_MAP:
            rules.append(
                f"stance:provisional_masquerades_as_core:{role_lc}->{stance}"
            )
        else:
            rules.append(f"stance:provisional:{role_lc}->{stance}")
        return stance, rules

    # Unknown role token — fall back to neutral; record so the dashboard
    # can spot lexicon-coverage drift.
    rules.append(f"stance:unknown_role_token:{role_lc}->neutral")
    return CORE_STANCE_MAP["unknown"], rules


def _derive_directionality(role: Optional[str]) -> Optional[str]:
    if not role:
        return None
    return _DIRECTIONALITY_BY_ROLE.get(role.strip().lower())


def _closeness_to_enum(raw: Optional[str]) -> str:
    """Map the existing `resolve_relationship` lowercased
    closeness/weight tokens to the V2 uppercase enum."""
    if not raw:
        return Closeness.LOW
    raw_lc = str(raw).strip().lower()
    return {
        "high": Closeness.HIGH,
        "medium": Closeness.MEDIUM,
        "low": Closeness.LOW,
    }.get(raw_lc, Closeness.LOW)


# ════════════════════════════════════════════════════════════════════
# PROPER-NAME EXTRACTION (re-used from relationship_router_v2 with
# the same blocklist; kept local to avoid an import cycle).
# ════════════════════════════════════════════════════════════════════

_NAME_TOKEN_RE = re.compile(r"\b([A-Z][a-z]{1,30})\b")

_NAME_BLOCKLIST: set = {
    "How", "What", "Why", "When", "Where", "Who", "Which", "Whose",
    "Tell", "Show", "Can", "Could", "Should", "Would", "Will", "Shall",
    "Am", "Is", "Are", "Was", "Were", "Do", "Does", "Did", "Has", "Have",
    "Had", "May", "Might", "Must", "Let",
    "I", "Me", "My", "Mine", "We", "Us", "Our", "Ours",
    "You", "Your", "Yours", "He", "She", "Him", "Her", "His", "Hers",
    "They", "Them", "Their", "Theirs", "It", "Its",
    "This", "That", "These", "Those", "There", "Here",
    "A", "An", "The", "Any", "All", "Some", "None",
    "But", "And", "Or", "If", "So", "Yet",
    "Yes", "No", "Ok", "Okay", "Hi", "Hey", "Hello",
    "Mirror", "Chat", "Cross", "Lens", "Lenses", "Frame", "Forum",
    # Astro / lens vocabulary (kept identical to the V2 router blocklist
    # so the two resolvers agree on what is NOT a person-name).
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
    "Uranus", "Neptune", "Pluto", "Chiron", "Lilith",
    "Ascendant", "Descendant", "Midheaven", "MC", "IC",
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
    "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    "Human", "Design", "Enneagram", "Astrology", "Numerology",
    "BaZi", "Bazi", "Vedic", "Western",
}

_SELF_PRONOUN_RE = re.compile(
    r"\b(myself|my\s+own|about\s+me|about\s+myself|just\s+me|"
    r"on\s+my\s+own|i\s+want\s+to|i\s+need\s+to|what\s+about\s+me)\b",
    re.IGNORECASE,
)


def _extract_proper_name_candidate(text: str) -> Optional[str]:
    if not text:
        return None
    for tok in _NAME_TOKEN_RE.findall(text):
        if tok in _NAME_BLOCKLIST:
            continue
        return tok
    return None


# ════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ════════════════════════════════════════════════════════════════════

async def resolve_relationship_field(
    *,
    db,
    self_user_id: str,
    message: str = "",
    hints: Optional[Dict[str, Any]] = None,
) -> RelationshipField:
    """Resolve the Relationship Field for a single Mirror turn.

    READ-ONLY. No DB writes anywhere in this path.

    Args:
        db:              The Motor / async MongoDB handle.
        self_user_id:    The viewer (who is asking).
        message:         The verbatim user message.
        hints: {
            about_person_id  : explicit FE-supplied target FK (preferred)
            forum_topology   : {forum_id, active_member_id, members, ...}
            life_domain      : "relationship" | "career" | ...
            last_target_id   : prior-turn target_user_id (pronoun memory)
            url_context      : raw query-param context (e.g.
                               Relationship Insight V2's "context=spouse")
                               — recorded as a *conflict candidate*
                               when it disagrees with the edge graph.
            target_name_hint : explicit FE name when no id is known
        }

    Returns:
        A `RelationshipField` envelope (read-only, no side effects).
    """
    hints = hints or {}
    about_person_id  = hints.get("about_person_id")
    forum_topology   = hints.get("forum_topology")
    last_target_id   = hints.get("last_target_id")
    url_context      = hints.get("url_context")
    target_name_hint = hints.get("target_name_hint")

    # Working envelope — fields populated as we resolve.
    fld = RelationshipField(self_user_id=self_user_id)
    fld.forum_topology = forum_topology

    if forum_topology:
        fld.forum_id = forum_topology.get("forum_id")
        # name resolution is best-effort
        fld.forum_name = forum_topology.get("forum_name")

    # ── Step 0 — self-subject short-circuit ────────────────────────
    # Per G3: if there's no target hint and the message is explicitly
    # self-referencing, return self_subject deterministically.
    has_target_hint = bool(
        about_person_id
        or (forum_topology or {}).get("active_member_id")
        or last_target_id
        or target_name_hint
    )
    self_pronoun_hit = bool(_SELF_PRONOUN_RE.search(message or ""))
    if not has_target_hint and self_pronoun_hit:
        fld.active_frame        = ActiveFrame.SELF
        fld.relationship_role   = "self"
        fld.relationship_stance = PROVISIONAL_STANCE_MAP["self"]   # self_subject
        fld.closeness           = Closeness.LOW
        fld.emotional_weight    = Closeness.LOW
        fld.directionality      = None
        fld.resolution_source   = ResolutionSource.SELF_NO_TARGET
        fld.resolution_path     = ["self:pronoun_match", "stance:self->self_subject"]
        fld.confidence          = 0.95
        return fld

    # ── Step 1a — Pre-declare candidate accumulators ────────────────
    # These must exist BEFORE the Slice A early-return block because the
    # @mention path may set them and pairwise/scope/forum-intent paths
    # gate on `candidate_target_id is None`.  If they were declared only
    # at Step 1 (below) Python would raise NameError on the gates.
    candidate_target_id: Optional[str] = None
    candidate_name: Optional[str] = target_name_hint
    candidate_source_hint: Optional[str] = None

    # ── Slice A — early-return paths (only when no explicit hint) ─────
    # Order: @mention → pairwise → scope (multi-person) → forum-intent
    # All branches are no-ops when explicit hints are provided so that
    # MEMBER resolution via about_person_id/forum_topology remains
    # canonical (per priority order in the audit's §5.3).
    # Bias (per user directive): MEMBER > PAIRWISE > FORUM.  FORUM
    # intent uses an intentionally conservative seed list — better to
    # miss a forum-level question than misclassify a member question.
    if not has_target_hint:
        # 0.5 — @mention extraction (highest priority among message-only paths)
        at_name = _extract_at_mention(message)
        if at_name:
            cands_at = await _resolve_name_to_candidates(db, self_user_id, at_name)
            # @mention is an explicit user gesture; accept the top
            # candidate unless multiple are within 0.10 confidence of each
            # other (per ambiguity rule).
            if cands_at:
                amb = _evaluate_ambiguity(cands_at)
                if amb["ambiguous"]:
                    fld.active_frame         = ActiveFrame.AMBIGUOUS
                    fld.relationship_role    = None
                    fld.relationship_stance  = "neutral"
                    fld.resolution_source    = ResolutionSource.AMBIGUITY
                    fld.confidence           = 0.50
                    fld.ambiguity_candidates = cands_at
                    fld.target_aliases       = [at_name]
                    fld.missing_data.append("target_ambiguous")
                    fld.resolution_path.append(f"at_mention_ambiguous:{at_name}:{len(cands_at)}")
                    return fld
                # Single best candidate — feed into existing MEMBER path
                top = cands_at[0]
                candidate_target_id   = top["user_id"]
                candidate_name        = top["name"]
                candidate_source_hint = "at_mention"
                fld.active_frame      = ActiveFrame.MEMBER
                fld.resolution_path.append(
                    f"at_mention_resolved:{at_name}->{top['name']}"
                )
                # fall through to Step 2 with the resolved candidate
            # else (no candidates) — fall through; later steps handle

        # 0.7 — PAIRWISE pattern ("X and Y", "X & Y")
        if candidate_target_id is None:
            pair = _extract_pairwise_names(message)
            if pair:
                a_name, b_name = pair
                cands_a = await _resolve_name_to_candidates(db, self_user_id, a_name)
                cands_b = await _resolve_name_to_candidates(db, self_user_id, b_name)
                # Only emit PAIRWISE when BOTH names resolve to a single
                # high-confidence candidate.  Otherwise let later steps
                # handle (avoids false positives like "Mel and I").
                if (cands_a and cands_b
                        and not _evaluate_ambiguity(cands_a)["ambiguous"]
                        and not _evaluate_ambiguity(cands_b)["ambiguous"]):
                    a, b = cands_a[0], cands_b[0]
                    fld.active_frame         = ActiveFrame.PAIRWISE
                    fld.target_user_id       = a["user_id"]
                    fld.target_name          = a["name"]
                    fld.target_user_id_b     = b["user_id"]
                    fld.target_name_b        = b["name"]
                    fld.relationship_role    = None    # pairwise = relation between two others
                    fld.relationship_stance  = "neutral"
                    fld.resolution_source    = ResolutionSource.PAIRWISE_PATTERN
                    fld.confidence           = min(a.get("confidence", 0.7),
                                                   b.get("confidence", 0.7))
                    fld.resolution_path.append(
                        f"pairwise:{a_name}+{b_name}->{a['name']}+{b['name']}"
                    )
                    return fld

        # 0.8 — MULTI_PERSON scope ("my children", "all my forum members")
        if candidate_target_id is None:
            scope = _extract_scope_class(message)
            if scope:
                fld.active_frame         = ActiveFrame.MULTI_PERSON
                fld.scope_class          = scope
                fld.relationship_role    = None
                fld.relationship_stance  = "neutral"
                fld.resolution_source    = ResolutionSource.SCOPE_CLASS
                fld.confidence           = 0.85
                fld.resolution_path.append(f"scope_class:{scope}")
                return fld

        # 0.9 — Conservative FORUM intent (only the approved seed list)
        if _has_forum_intent(message) and candidate_target_id is None:
            # Cross-check: viewer must have at least one matching forum.
            # If 0 forums → leave alone; later steps will fall through.
            # If 1 forum → bind it.  If >1 → bind nothing and surface
            # missing_data so the FE can ask which one.
            try:
                viewer_forums: List[Dict[str, Any]] = []
                async for fm in db.forum_members.find(
                    {"user_id": self_user_id, "status": "active"},
                ):
                    viewer_forums.append(fm)
                if len(viewer_forums) >= 1:
                    fld.active_frame      = ActiveFrame.FORUM
                    fld.resolution_source = ResolutionSource.FORUM_INTENT
                    fld.confidence        = 0.85 if len(viewer_forums) == 1 else 0.55
                    if len(viewer_forums) == 1:
                        fld.forum_id      = viewer_forums[0].get("forum_id")
                        # forum_name hydrated below in Step 7 via existing logic
                    else:
                        fld.missing_data.append("forum_intent_multi_match")
                    fld.resolution_path.append(
                        f"forum_intent:viewer_forums={len(viewer_forums)}"
                    )
                    return fld
            except Exception as e:    # pragma: no cover
                logger.debug(f"[RelField] forum-intent probe failed: {e!r}")

    # ── Step 1 — Pick a candidate target_user_id to resolve against ─
    # Priority of hint inputs (does NOT yet say what the role is — that
    # comes from the edges-first resolver below).  candidate_target_id
    # may already be set by the @mention path above.

    if about_person_id:
        candidate_target_id = about_person_id
        candidate_source_hint = "explicit_about_person_id"
        fld.active_frame = ActiveFrame.MEMBER
    elif (forum_topology or {}).get("active_member_id"):
        candidate_target_id = forum_topology["active_member_id"]
        candidate_source_hint = "forum_topology_active_member"
        fld.active_frame = ActiveFrame.FORUM
    elif last_target_id and _has_pronoun(message):
        candidate_target_id = last_target_id
        candidate_source_hint = "pronoun_memory"
        fld.active_frame = ActiveFrame.MEMBER

    fld.resolution_path.append(
        f"hint:{candidate_source_hint or 'none'}"
    )

    # ── Step 2 — Defer to canonical edges-first resolver ────────────
    # `resolve_relationship` already walks:
    #   edges → maps → saved_people → forum_members → forum_inference
    # We just need a target_user_id OR name to ask. If neither is
    # available yet, we fall through to step 3 (lexicon / proper-name).
    role_result: Optional[Dict[str, Any]] = None
    if candidate_target_id or candidate_name:
        try:
            from services.relationship_resolver import resolve_relationship
            role_result = await resolve_relationship(
                db=db,
                asker_user_id=self_user_id,
                target_user_id=candidate_target_id,
                target_name=candidate_name,
                forum_id=fld.forum_id,
            )
        except Exception as e:    # pragma: no cover
            logger.debug(f"[RelField] resolve_relationship failed: {e!r}")
            role_result = None

    # If we got a high-confidence result from the canonical resolver,
    # populate the envelope.
    if role_result and role_result.get("relationship_detected"):
        fld.target_user_id     = candidate_target_id
        fld.target_name        = candidate_name
        fld.relationship_role  = role_result.get("relationship_role")
        fld.closeness          = _closeness_to_enum(role_result.get("closeness"))
        fld.emotional_weight   = _closeness_to_enum(role_result.get("emotional_weight"))
        # Translate the legacy source tag to the V2 enum
        legacy_src = role_result.get("relationship_source")
        fld.resolution_source = {
            "explicit_map":         ResolutionSource.EXPLICIT_MAP,
            "saved_people":         ResolutionSource.SAVED_PEOPLE,
            "forum_relationship":   ResolutionSource.FORUM_MEMBERS,
            "forum_inference":      ResolutionSource.FORUM_INFERENCE,
            # NEW: edges-first explicit tag emitted by resolver L144
            "forum_relationship_edges": ResolutionSource.EDGES,
        }.get(legacy_src, ResolutionSource.NONE)
        fld.resolution_path.append(f"legacy_src:{legacy_src}")
        # Hydrate target name from the users collection if missing
        if fld.target_user_id and not fld.target_name:
            try:
                u = await db.users.find_one({"_id": fld.target_user_id})
                if not u:
                    from bson import ObjectId
                    try:
                        u = await db.users.find_one({"_id": ObjectId(fld.target_user_id)})
                    except Exception:
                        u = None
                if u:
                    fld.target_name = u.get("name") or u.get("first_name")
                    fld.target_aliases = [n for n in [
                        u.get("name"), u.get("first_name"),
                        u.get("display_name"),
                    ] if n]
            except Exception as e:    # pragma: no cover
                logger.debug(f"[RelField] users hydrate failed: {e!r}")
        # forum_id was pre-set from hints; resolver may also have one
        fld.forum_id = fld.forum_id or role_result.get("forum_id")
        fld.forum_name = fld.forum_name or role_result.get("forum_name")
    else:
        # No canonical role — leave role None and fall through to step 3.
        fld.resolution_path.append("canonical_resolver:no_role")
        if candidate_target_id:
            fld.target_user_id = candidate_target_id
            # We have an id but no role: missing_data flag for dashboard.
            fld.missing_data.append("explicit_role_on_edge")

    # ── Step 3 — Proper-name fallback (G2: low-confidence only) ─────
    # Only fires when no target_user_id was hinted AND no role was
    # found.  The fallback never produces a high-confidence binding.
    if not fld.target_user_id and not candidate_target_id:
        name = _extract_proper_name_candidate(message)
        if name:
            # Slice A — check for ambiguity in the candidate pool BEFORE
            # falling through to proposed_unresolved.
            cands_fb = await _resolve_name_to_candidates(db, self_user_id, name)
            if cands_fb:
                amb = _evaluate_ambiguity(cands_fb)
                if amb["ambiguous"]:
                    fld.active_frame         = ActiveFrame.AMBIGUOUS
                    fld.target_aliases       = [name]
                    fld.relationship_role    = None
                    fld.relationship_stance  = "neutral"
                    fld.resolution_source    = ResolutionSource.AMBIGUITY
                    fld.confidence           = 0.50
                    fld.ambiguity_candidates = cands_fb
                    fld.missing_data.append("target_ambiguous")
                    fld.resolution_path.append(
                        f"ambiguity:{name}:{len(cands_fb)}_candidates"
                    )
                    return fld
                # Single best candidate: graceful upgrade to MEMBER
                top = cands_fb[0]
                candidate_target_id = top["user_id"]
                candidate_name      = top["name"]
                fld.resolution_path.append(
                    f"name_match_single:{name}->{top['name']}"
                )
                # Continue below — the canonical resolver fills role/stance
                try:
                    from services.relationship_resolver import resolve_relationship
                    role_result = await resolve_relationship(
                        db=db,
                        asker_user_id=self_user_id,
                        target_user_id=candidate_target_id,
                        target_name=candidate_name,
                        forum_id=fld.forum_id,
                    )
                except Exception:
                    role_result = None
                if role_result and role_result.get("relationship_detected"):
                    fld.target_user_id   = candidate_target_id
                    fld.target_name      = candidate_name
                    fld.relationship_role = role_result.get("relationship_role")
                    fld.closeness        = _closeness_to_enum(role_result.get("closeness"))
                    fld.emotional_weight = _closeness_to_enum(role_result.get("emotional_weight"))
                    legacy_src = role_result.get("relationship_source")
                    fld.resolution_source = {
                        "explicit_map":             ResolutionSource.EXPLICIT_MAP,
                        "saved_people":             ResolutionSource.SAVED_PEOPLE,
                        "forum_relationship":       ResolutionSource.FORUM_MEMBERS,
                        "forum_inference":          ResolutionSource.FORUM_INFERENCE,
                        "forum_relationship_edges": ResolutionSource.EDGES,
                    }.get(legacy_src, ResolutionSource.NONE)
            else:
                # No candidates at all — original proposed_unresolved path
                fld.target_aliases = [name]
                fld.resolution_source = ResolutionSource.PROPOSED_UNRESOLVED
                fld.resolution_path.append(f"proper_name_fallback:{name}")
                fld.missing_data.append("target_unresolved")
                fld.proposed_action = {
                    "type":           "add_to_circle",
                    "suggested_name": name,
                    "reason":         (
                        f"name '{name}' appears in message but is not in "
                        f"user's saved_people OR any of their forums"
                    ),
                    "source_text":    (message or "").strip()[:500],
                    "confidence":     0.55,
                }
                fld.confidence = 0.55
                fld.active_frame = ActiveFrame.SELF

    # ── Step 4 — Derive stance + directionality ────────────────────
    stance, stance_rules = _derive_stance(
        fld.relationship_role, fld.resolution_source,
    )
    fld.relationship_stance = stance
    fld.resolution_path.extend(stance_rules)
    fld.directionality = _derive_directionality(fld.relationship_role)

    # ── Step 5 — Confidence scoring (G2) ───────────────────────────
    # Sources that count toward HIGH-CONFIDENCE binding:
    if fld.confidence == 0.0:
        if fld.resolution_source in _HIGH_CONFIDENCE_SOURCES and fld.relationship_role:
            fld.confidence = 0.95 if fld.resolution_source == ResolutionSource.EDGES else 0.85
        elif fld.resolution_source == ResolutionSource.FORUM_INFERENCE:
            fld.confidence = 0.65
        elif fld.resolution_source == ResolutionSource.PROPOSED_UNRESOLVED:
            fld.confidence = 0.55
        else:
            fld.confidence = 0.30

    # ── Step 6 — Conflict detection (G4: edges override URL context) ─
    # If the caller passed `url_context` and it disagrees with the
    # resolved role, record the conflict but DO NOT overwrite.
    if url_context and fld.relationship_role:
        uc_lc = str(url_context).strip().lower()
        if uc_lc and uc_lc != (fld.relationship_role or "").lower():
            # We allow synonyms — e.g. URL says "partner" but edges say
            # "spouse" → not a conflict.
            _SYNONYMS = {
                ("spouse", "partner"),
                ("partner", "spouse"),
                ("ex_partner", "former_partner"),
                ("former_partner", "ex_partner"),
                ("child", "son"), ("child", "daughter"),
                ("son", "child"), ("daughter", "child"),
                ("parent", "mother"), ("parent", "father"),
                ("mother", "parent"), ("father", "parent"),
            }
            if (uc_lc, fld.relationship_role.lower()) not in _SYNONYMS:
                fld.conflicts.append(
                    f"url_context_vs_edge:url='{uc_lc}' vs "
                    f"resolved_role='{fld.relationship_role}' "
                    f"(source={fld.resolution_source}) — edges override"
                )

    # ── Step 7 — Frame promotion based on resolved target ──────────
    if fld.target_user_id and fld.active_frame == ActiveFrame.SELF:
        fld.active_frame = ActiveFrame.MEMBER
        fld.resolution_path.append("frame_promoted:self->member")

    # Final pass: if we still have no target AND no self-pronoun hit,
    # leave active_frame=SELF and stance=neutral.  This is the
    # "general self-inquiry without any signal" baseline.
    if not fld.target_user_id and fld.resolution_source == ResolutionSource.NONE:
        fld.resolution_source = ResolutionSource.NONE
        fld.relationship_stance = CORE_STANCE_MAP["unknown"]   # neutral
        fld.resolution_path.append("baseline:self_neutral")

    return fld


# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────

_PRONOUN_RE = re.compile(
    r"\b(us|we|he|she|they|them|him|her)\b", re.IGNORECASE,
)


def _has_pronoun(text: str) -> bool:
    return bool(_PRONOUN_RE.search(text or ""))


# ════════════════════════════════════════════════════════════════════
# Slice A — message-pattern helpers
# ════════════════════════════════════════════════════════════════════

# @mention: matches "@Name" tokens.  Accepts letters, digits, and
# underscore.  Restricted to a first letter so we don't pick up
# "@123abc" emoji-style placeholders.
_AT_MENTION_RE = re.compile(r"@([A-Za-z][A-Za-z0-9_]{1,30})\b")


def _extract_at_mention(text: str) -> Optional[str]:
    if not text:
        return None
    m = _AT_MENTION_RE.search(text)
    return m.group(1) if m else None


# PAIRWISE: "X and Y", "X & Y", "X vs Y", "X versus Y".
# Both tokens MUST be capitalised proper-name candidates AND not in the
# global blocklist (otherwise "Mel and I" or "Sun and Moon" would slip
# through).  Per user directive we intentionally bias *narrow* — better
# to miss a pairwise question than treat a member question as pairwise.
_PAIR_RE = re.compile(
    r"\b([A-Z][a-z]{1,30})\s+(?:and|&|vs\.?|versus)\s+([A-Z][a-z]{1,30})\b"
)


def _extract_pairwise_names(text: str) -> Optional[Tuple[str, str]]:
    if not text:
        return None
    m = _PAIR_RE.search(text)
    if not m:
        return None
    a, b = m.group(1), m.group(2)
    if a in _NAME_BLOCKLIST or b in _NAME_BLOCKLIST:
        return None
    if a.lower() == b.lower():
        return None
    return a, b


# MULTI_PERSON scope classes.  Conservative seed list; only common
# scope phrasings are recognised.  Each pattern maps to a stable
# `scope_class` label that downstream surfaces can route on.
_SCOPE_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\b(?:all\s+)?my\s+(?:children|kids)\b", re.IGNORECASE),       "my_children"),
    (re.compile(r"\b(?:all\s+)?my\s+(?:siblings|brothers|sisters)\b", re.IGNORECASE), "my_siblings"),
    (re.compile(r"\b(?:all\s+)?my\s+parents\b", re.IGNORECASE),                 "my_parents"),
    (re.compile(r"\b(?:all\s+)?my\s+(?:forum\s+members?|circle|family)\b", re.IGNORECASE), "my_circle"),
    (re.compile(r"\beveryone\s+in\s+(?:the\s+|my\s+)?forum\b", re.IGNORECASE),  "my_circle"),
    (re.compile(r"\ball\s+forum\s+members?\b", re.IGNORECASE),                  "my_circle"),
]


def _extract_scope_class(text: str) -> Optional[str]:
    if not text:
        return None
    for rx, label in _SCOPE_PATTERNS:
        if rx.search(text):
            return label
    return None


# FORUM intent: deliberately narrow seed list (per user directive
# "do not over-engineer FORUM detection").  Only fires for explicit
# self-referential forum phrasings.
_FORUM_INTENT_RE = re.compile(
    r"\b("
    r"this\s+forum"
    r"|the\s+forum"
    r"|my\s+forum"
    r"|the\s+forum\s+(?:dynamic|energy|theme|field)"
    r"|this\s+(?:family|circle|group)\s+(?:dynamic|energy|theme|field)"
    r"|forum\s+as\s+a\s+whole"
    r")\b",
    re.IGNORECASE,
)


def _has_forum_intent(text: str) -> bool:
    return bool(_FORUM_INTENT_RE.search(text or ""))


# Ambiguity evaluator.  A pool is "ambiguous" iff 2+ candidates sit
# within 0.10 confidence of the top.  Single-candidate pools are NEVER
# ambiguous (per user directive: bias toward MEMBER resolution).
def _evaluate_ambiguity(cands: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not cands or len(cands) < 2:
        return {"ambiguous": False, "competing_count": len(cands or [])}
    top_conf = float(cands[0].get("confidence", 0.0))
    close = [c for c in cands if (top_conf - float(c.get("confidence", 0.0))) <= 0.10]
    return {
        "ambiguous":       len(close) >= 2,
        "competing_count": len(close),
        "top_confidence":  top_conf,
    }


# Name-to-candidates lookup.  Walks the viewer's saved_people and
# forum-co-members for a name prefix-match.  Read-only.  Returns a
# confidence-ranked list of `{user_id, name, role, confidence, source}`.
#
# Per G2 of slice-1: this helper does NOT bind a HIGH-CONFIDENCE target
# on its own; it is *advisory* for the caller (which may demote to
# AMBIGUOUS or feed into the canonical edges-first resolver).
async def _resolve_name_to_candidates(
    db,
    self_user_id: str,
    name: str,
) -> List[Dict[str, Any]]:
    cands: List[Dict[str, Any]] = []
    if not name or not self_user_id:
        return cands
    seen: set = set()
    name_lc = name.strip().lower()
    name_rx_pattern = rf"^{re.escape(name)}"

    # 1. saved_people — names known to the viewer.  Highest signal
    #    because the user explicitly added them.
    try:
        async for sp in db.saved_people.find({
            "user_id": self_user_id,
            "name":    {"$regex": name_rx_pattern, "$options": "i"},
        }):
            uid = (
                sp.get("linked_user_id")
                or sp.get("emergent_user_id")
                or (str(sp.get("_id")) if sp.get("_id") else None)
            )
            if not uid or uid in seen:
                continue
            cands.append({
                "user_id":    uid,
                "name":       sp.get("name") or name,
                "role":       sp.get("relationship_type"),
                "confidence": 0.90,
                "source":     "saved_people",
            })
            seen.add(uid)
    except Exception as e:    # pragma: no cover
        logger.debug(f"[RelField] saved_people scan failed: {e!r}")

    # 2. forum_members → users.  Viewer's forum co-members whose name
    #    starts with the token.
    try:
        viewer_forum_ids: List[str] = []
        async for fm in db.forum_members.find({
            "user_id": self_user_id, "status": "active",
        }):
            fid = fm.get("forum_id")
            if fid:
                viewer_forum_ids.append(fid)
        if viewer_forum_ids:
            async for fm in db.forum_members.find({
                "forum_id": {"$in": viewer_forum_ids},
                "user_id":  {"$ne": self_user_id},
            }):
                co_uid = fm.get("user_id")
                if not co_uid or co_uid in seen:
                    continue
                # Resolve the co-member's name from the users collection
                u_doc = None
                try:
                    u_doc = await db.users.find_one({"_id": co_uid})
                    if not u_doc:
                        from bson import ObjectId
                        try:
                            u_doc = await db.users.find_one({"_id": ObjectId(co_uid)})
                        except Exception:
                            u_doc = None
                except Exception:
                    u_doc = None
                if not u_doc:
                    continue
                u_name = (
                    u_doc.get("name")
                    or u_doc.get("first_name")
                    or u_doc.get("display_name")
                    or ""
                )
                if u_name and u_name.lower().startswith(name_lc):
                    cands.append({
                        "user_id":    co_uid,
                        "name":       u_name,
                        "role":       fm.get("relationship_type"),
                        "confidence": 0.80,
                        "source":     "forum_members",
                    })
                    seen.add(co_uid)
    except Exception as e:    # pragma: no cover
        logger.debug(f"[RelField] forum_members scan failed: {e!r}")

    cands.sort(key=lambda c: float(c.get("confidence", 0.0)), reverse=True)
    return cands
