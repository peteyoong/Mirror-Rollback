"""
Lens Conversation — Shared Memory + Entity Tracking Service for ALL Mirror lens chats.

Build marker: multi-lens-chat-memory-v1

This module replaces the per-lens "single-turn stateless retrieval" failure
mode that affected every lens chat (not just astrology).  Each lens chat
(Astrology / Human Design / Numerology / Enneagram / BaZi) now plugs into
this service to gain:

    1. Active-entity resolution across recent turns.
       Referents like "that / it / this / which one / what about that"
       resolve to the most recently-named entity from history.

    2. Recent conversation history injection.
       The last 6 turns are formatted into the system prompt so the LLM
       stops asking "what were we talking about?" between turns.

    3. Lens grounding + missing-data honesty.
       Each lens reports `grounding_sources_present` and `missing_sources`
       so the LLM can say "I don't have that signal computed yet" instead
       of inventing.

    4. Consistent debug payload returned on every lens chat response.

Each lens supplies a registry conforming to LensRegistry — see
services.lens_registries.* — that knows:
    * how to build its entity index from user data
    * which aliases identify its entities in free text
    * which referent words trigger lookback ("which gate", "that center",
      "which pillar", etc.)
    * what sources are present vs missing for this user
    * how to format a grounding signals block

The service then composes ACTIVE ENTITY + GROUNDING SIGNALS + CONVERSATION
HISTORY blocks for the LLM system prompt — identical structure across all
lenses so the LLM behaviour stays consistent.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Protocol, Tuple


# ---------------------------------------------------------------------------
# Universal referent words (shared by every lens).
# Lens-specific referents (e.g. "which gate", "which pillar") are added on
# top of these by each registry.
# ---------------------------------------------------------------------------

UNIVERSAL_REFERENT_PATTERNS = [
    r"\bthat\b", r"\bthis\b", r"\bit\b", r"\bthey\b", r"\bthese\b", r"\bthose\b",
    r"\bwhich (?:one|of these|of those)\b",
    r"\bwhat about (?:that|this|it)\b",
    r"\bhow does (?:that|this|it)\b",
    r"\bwhere does (?:that|this|it)\b",
    r"\bis that why\b", r"\bso that\b",
    r"\bwhat does that mean\b",
]


# ---------------------------------------------------------------------------
# LensRegistry protocol — each lens implements this shape.
# ---------------------------------------------------------------------------

class LensRegistry(Protocol):
    """Each lens implements this Protocol to plug into the shared service."""

    # Stable lens id, e.g. "astrology", "human_design", "numerology", ...
    lens_name: str

    # Human-readable label used inside prompts, e.g. "Human Design"
    lens_label: str

    def build_index(self, user_context: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Build the entity index from whatever user-specific data this lens
        has access to.  Keys are canonical entity names; values must include
        at minimum: kind, name, and any lens-specific descriptive fields.
        Return {} when there is no data (e.g. lens not computed for user).
        """
        ...

    def extract_entities_from_text(self, text: str) -> List[str]:
        """
        Return canonical entity keys mentioned in `text`, in left-to-right
        order of appearance, deduplicated.
        """
        ...

    def referent_patterns(self) -> List[str]:
        """
        Lens-specific referent phrases, e.g. ["\\bwhich gate\\b",
        "\\bwhich pillar\\b"].  Combined with UNIVERSAL_REFERENT_PATTERNS
        by the resolver.
        """
        ...

    def grounding_sources_present(self, user_context: Dict[str, Any]) -> List[str]:
        """Which data sources for this lens are currently computed."""
        ...

    def missing_sources(self, user_context: Dict[str, Any]) -> List[str]:
        """Which data sources are missing (will trigger honest fallback)."""
        ...

    def format_grounding_block(self, index: Dict[str, Dict[str, Any]]) -> str:
        """Format the grounded source-of-truth block for the system prompt."""
        ...


# ---------------------------------------------------------------------------
# Helpers shared by every registry
# ---------------------------------------------------------------------------

def build_alias_regex(aliases: Dict[str, str]) -> re.Pattern:
    """
    Build a single case-insensitive regex matching any alias (longest first).
    `aliases` maps lowercase alias → canonical key.
    """
    if not aliases:
        return re.compile(r"(?!)")  # never matches
    keys = sorted(aliases.keys(), key=len, reverse=True)
    escaped = [re.escape(k) for k in keys]
    return re.compile(r"\b(" + "|".join(escaped) + r")\b", re.IGNORECASE)


def extract_via_aliases(text: str, alias_regex: re.Pattern, alias_to_canonical: Dict[str, str]) -> List[str]:
    """
    Generic extraction helper.  Returns canonical entity keys in
    left-to-right first-mention order, deduplicated.
    """
    if not text:
        return []
    found: List[Tuple[int, str]] = []
    for m in alias_regex.finditer(text):
        canonical = alias_to_canonical.get(m.group(1).lower())
        if canonical:
            found.append((m.start(), canonical))
    found.sort(key=lambda x: x[0])
    seen, result = set(), []
    for _, key in found:
        if key not in seen:
            seen.add(key)
            result.append(key)
    return result


# ---------------------------------------------------------------------------
# Active-entity resolver (lens-agnostic)
# ---------------------------------------------------------------------------

def has_referent(message: str, lens_referents: List[str]) -> bool:
    if not message:
        return False
    patterns = UNIVERSAL_REFERENT_PATTERNS + (lens_referents or [])
    combined = re.compile("|".join(patterns), re.IGNORECASE)
    return bool(combined.search(message))


def resolve_active_entity(
    user_message: str,
    history: List[Dict[str, str]],
    registry: LensRegistry,
    index: Dict[str, Dict[str, Any]],
    primary_kinds: Tuple[str, ...] = ("planet", "node", "angle", "center", "channel", "gate", "pillar", "core_type", "life_path"),
    secondary_kinds: Tuple[str, ...] = ("house", "incarnation_cross", "ten_god", "element", "personal_cycle", "wing", "instinct"),
) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Resolve which entity the user is currently asking about.

    Precedence:
      1. Explicit PRIMARY entity in the current message wins
         (planet/gate/center/pillar/etc.).
      2. Referent + only-SECONDARY entity in current message → look back
         for the most recent PRIMARY entity in history.
      3. Referent only → look back for any most recent entity in history.
      4. No referent, no entity → carryover from most recent turn (if any).
      5. Nothing found → ("none") so the LLM is forced to ask.

    Returns: (entity_or_None, source_label)
        source_label ∈ {"current", "referent", "carryover", "none"}
    """
    current_keys = registry.extract_entities_from_text(user_message or "")
    current_entities = [(k, index[k]) for k in current_keys if k in index]

    has_ref = has_referent(user_message or "", registry.referent_patterns())

    current_primary = [e for e in current_entities if e[1].get("kind") in primary_kinds]
    current_secondary = [e for e in current_entities if e[1].get("kind") in secondary_kinds]

    # 1. Explicit primary entity in current message → it wins.
    if current_primary:
        return current_primary[0][1], "current"

    # 2. Referent + only-secondary in current message → resolve from history.
    if has_ref and current_secondary and not current_primary:
        prior = _scan_history_for_kind(history, registry, index, kinds=primary_kinds)
        if prior:
            return prior, "referent"
        # Fall through to using the secondary as subject
        return current_secondary[0][1], "current"

    # If only secondary was named and no referent — treat as subject.
    if current_secondary and not has_ref:
        return current_secondary[0][1], "current"

    # 3. Pure referent → look back for any entity.
    if has_ref:
        prior = _scan_history_for_kind(history, registry, index, kinds=primary_kinds + secondary_kinds)
        if prior:
            return prior, "referent"

    # 4. Carryover: no referent, no entity → use most recent from history.
    prior = _scan_history_for_kind(history, registry, index, kinds=primary_kinds + secondary_kinds)
    if prior:
        return prior, "carryover"

    return None, "none"


def _scan_history_for_kind(
    history: List[Dict[str, str]],
    registry: LensRegistry,
    index: Dict[str, Dict[str, Any]],
    kinds: Tuple[str, ...],
) -> Optional[Dict[str, Any]]:
    """Walk history in reverse, return first entity whose kind ∈ kinds."""
    for turn in reversed(history or []):
        content = turn.get("content", "") if isinstance(turn, dict) else ""
        for k in registry.extract_entities_from_text(content):
            e = index.get(k)
            if e and e.get("kind") in kinds:
                return e
    return None


# ---------------------------------------------------------------------------
# Prompt block formatters
# ---------------------------------------------------------------------------

def format_history_block(history: List[Dict[str, str]], max_turns: int = 6) -> str:
    """Format the last N user/assistant pairs as a clean prompt block."""
    if not history:
        return ""
    recent = history[-(max_turns * 2):]
    lines = ["--- CONVERSATION HISTORY (most recent last) ---"]
    for msg in recent:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role", "user")
        content = (msg.get("content") or "").strip()
        if len(content) > 800:
            content = content[:800] + "…"
        lines.append(f"{'User' if role == 'user' else 'Mirror'}: {content}")
    return "\n".join(lines)


def format_active_entity_block(
    entity: Optional[Dict[str, Any]],
    source: str,
    lens_label: str,
) -> str:
    """
    Build the ACTIVE ENTITY block — the single most important fix.
    Each registry can also include `display_lines` on the entity dict for
    richer per-lens grounding (e.g. "Sign: Cancer · House 4" for astrology,
    "Energy Type: Manifesting Generator · Channel 34-20" for HD).
    """
    if not entity:
        return (
            "--- ACTIVE ENTITY (conversational focus) ---\n"
            f"Lens: {lens_label}\n"
            "No specific entity is in active focus.\n"
            "If the user references 'that' / 'it' / 'this' / 'which one' without\n"
            "naming a new entity, ASK which signal they mean.  DO NOT guess and\n"
            "DO NOT drift to an unrelated entity within this lens."
        )

    name = entity.get("name", "")
    placement_line = name
    display_lines: List[str] = entity.get("display_lines", []) or []

    source_explainer = {
        "current": "named in the current user message",
        "referent": "RESOLVED from prior turns (user used a referent like 'that' / 'it' / 'which one')",
        "carryover": "carried over from the most recent turn (user did not name a new entity)",
        "none": "none",
    }.get(source, source)

    lines = [
        "--- ACTIVE ENTITY (conversational focus) ---",
        f"Lens: {lens_label}",
        f"Active focus: {placement_line}",
        f"How resolved: {source_explainer}",
    ]
    if display_lines:
        lines.append("Details:")
        for d in display_lines[:6]:
            lines.append(f"  - {d}")

    lines.append(
        "RULE: Answer the user's question about THIS entity.  Do NOT pivot to a\n"
        "different entity in this lens unless the user explicitly asks."
    )
    return "\n".join(lines)


def format_grounding_status_block(
    lens_label: str,
    present: List[str],
    missing: List[str],
) -> str:
    """
    A short block telling the LLM which sources are computed and which aren't.
    The LLM is required to honour `missing` and say so plainly rather than
    inventing data.
    """
    lines = [
        "--- LENS GROUNDING STATUS ---",
        f"Lens: {lens_label}",
    ]
    if present:
        lines.append("Computed and available:")
        for p in present:
            lines.append(f"  - {p}")
    if missing:
        lines.append("Missing / not computed for this user:")
        for m in missing:
            lines.append(f"  - {m}")
        lines.append(
            f"RULE: If the user asks about any of the missing signals above,"
            f" say plainly: \"I don't have that {lens_label} signal computed yet.\""
            f" Do NOT invent values.  Do NOT substitute a different signal."
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Universal response-architecture prompt block (shared across all lens chats).
# Each lens supplies its lens-specific anti-drift / anti-therapy rules on top
# of this.
# ---------------------------------------------------------------------------

UNIVERSAL_RESPONSE_ARCHITECTURE = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSE ARCHITECTURE — every substantive answer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hold the ACTIVE ENTITY for the entire reply.  Use this structure
(present in substance — labels are not required to be visible):

A) DIRECT ANSWER     — answer the EXACT question the user asked, up front.
B) SIGNAL / FACT     — name the precise signal from THIS user's data.
                       (e.g. "Your Saturn is in Capricorn, in House 10."
                              "Your Authority is Sacral."
                              "Your Life Path is 7.")
C) MEANING           — translate that signal into plain English.
D) BEHAVIOUR         — where this shows up in real life: specific domain
                       (family, work, visibility, intimacy, decision-making,
                       belonging, etc.) and concrete behaviours.
E) TENSION / SHADOW  — where this becomes distorted under pressure.  Be
                       honest about the cost.  No sugar-coating.
F) CONNECTION        — one short line tying this to the active question
                       the user is actually asking.
G) (OPTIONAL) one sharp reflective close — only if it adds something
                       specific to THIS entity.  Skip otherwise.

Length: 120–240 words for a full answer; 1–2 sentences for a clarification.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VOICE — observant interpreter, NOT therapy bot
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You sound:  observant · interpretive · precise · grounded · intelligent.
You do NOT sound: like a journaling coach · like a wellness pamphlet.

FORBIDDEN PHRASINGS (these make us sound generic — avoid them):
  - "How does that make you feel?"
  - "What's been capturing your curiosity lately?"
  - "How do you balance X with Y?"
  - "What's alive for you right now?"
  - "Where in your body do you feel this?"
  - "What's coming up for you?"
  - Any generic open-ended reflection prompt that doesn't reference the
    active signal by name.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONVERSATIONAL MEMORY — NON-NEGOTIABLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The ACTIVE ENTITY and CONVERSATION HISTORY blocks above are authoritative.

  - "that / it / this / which one / what about that" refers to the ACTIVE
    ENTITY.  Period.  Do not pivot.
  - If you already stated a signal in a prior turn, that fact is a shared
    premise.  Build on it, do not contradict it, do not pretend it wasn't
    said.
  - If the user corrects you ("I was asking about X"), acknowledge briefly
    and switch focus to X.  No defensive prelude.
  - If the active entity is "none" AND the user uses a referent, ASK which
    signal they mean.  Do NOT guess.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GROUNDING — USE ONLY WHAT'S COMPUTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The LENS GROUNDING STATUS block tells you which signals are computed and
which are missing for THIS user.

  - Use ONLY signals listed as computed.
  - For any signal listed as missing, say "I don't have that {lens} signal
    computed yet."  Do NOT fabricate.  Do NOT substitute a different signal.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANTI-DRIFT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

One reply = one focus.  Do not tour the chart / design / numbers / type /
pillars.  Introduce a second signal only if it is directly relevant to the
active entity, and keep it to ONE connection line.
"""


# ---------------------------------------------------------------------------
# Debug payload
# ---------------------------------------------------------------------------

def build_debug_payload(
    lens: str,
    active_entity: Optional[Dict[str, Any]],
    source: str,
    history_entities: List[str],
    grounding_sources: List[str],
    missing_sources: List[str],
    conversation_turns_used: int,
) -> Dict[str, Any]:
    """Consistent debug payload returned on every lens chat."""
    return {
        "marker": "multi-lens-chat-memory-v1",
        "lens": lens,
        "active_entity": (
            {
                "name": active_entity.get("name"),
                "kind": active_entity.get("kind"),
            } if active_entity else None
        ),
        "active_entity_source": source,
        "recent_history_entities": history_entities[:12],
        "grounding_sources": grounding_sources,
        "missing_sources": missing_sources,
        "conversation_turns_used": conversation_turns_used,
    }


# ---------------------------------------------------------------------------
# Orchestrator: one call that does everything for a given lens.
# ---------------------------------------------------------------------------

def compose_lens_memory_blocks(
    registry: LensRegistry,
    user_context: Dict[str, Any],
    user_message: str,
    history: List[Dict[str, str]],
    max_history_turns: int = 6,
) -> Tuple[str, Dict[str, Any]]:
    """
    One-stop call.  Returns:
        (memory_block_text, debug_payload)

    The text block is meant to be appended to the lens's system prompt.
    The debug payload is meant to be surfaced on the API response.

    Caller is responsible for catching exceptions if they care; this
    function is defensive and will degrade gracefully when data is
    partial — but a TypeError in a registry would still bubble up.
    """
    index = registry.build_index(user_context) or {}

    active_entity, source = resolve_active_entity(
        user_message=user_message,
        history=history,
        registry=registry,
        index=index,
    )

    # Collect entities mentioned anywhere in recent history (debug only)
    history_entities: List[str] = []
    for turn in (history[-(max_history_turns * 2):] if history else []):
        content = turn.get("content", "") if isinstance(turn, dict) else ""
        for ent in registry.extract_entities_from_text(content):
            if ent not in history_entities:
                history_entities.append(ent)

    present = registry.grounding_sources_present(user_context)
    missing = registry.missing_sources(user_context)

    blocks: List[str] = []
    blocks.append(format_active_entity_block(active_entity, source, registry.lens_label))
    grounding_block = registry.format_grounding_block(index)
    if grounding_block:
        blocks.append(grounding_block)
    blocks.append(format_grounding_status_block(registry.lens_label, present, missing))
    history_block = format_history_block(history, max_turns=max_history_turns)
    if history_block:
        blocks.append(history_block)
    blocks.append(UNIVERSAL_RESPONSE_ARCHITECTURE)

    memory_block_text = "\n\n".join(b for b in blocks if b)

    debug = build_debug_payload(
        lens=registry.lens_name,
        active_entity=active_entity,
        source=source,
        history_entities=history_entities,
        grounding_sources=present,
        missing_sources=missing,
        conversation_turns_used=min(len(history), max_history_turns * 2),
    )

    return memory_block_text, debug
