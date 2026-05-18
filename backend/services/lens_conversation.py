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

    # lens-voice-differentiation-v1 — distinct interpretive stance per lens.
    voice_prompt: str


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
    primary_kinds: Tuple[str, ...] = (
        "planet", "node", "angle",
        "center", "channel", "gate", "hd_top",
        "pillar", "day_master", "luck_pillar",
        "core_type", "tritype", "line",
        "life_path",
    ),
    secondary_kinds: Tuple[str, ...] = (
        "house", "incarnation_cross",
        "ten_god", "element", "animal",
        "personal_cycle", "numerology_number",
        "wing", "instinct",
    ),
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
RESPONSE ARCHITECTURE — available, not mandatory
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You have access to the following components.  Use ONLY the ones the
current turn actually needs.  See the CONVERSATIONAL COMPRESSION block
below for which depth mode you're in and how many components to pull on.

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

DO NOT mechanically include all seven.  A great answer at LIGHT depth is
often A + B + one of D/E/F.  Pulling on all seven every turn is the
"AI completion syndrome" failure mode — avoid it.

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
SIGNAL HIERARCHY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Every reply has ONE dominant signal: the ACTIVE ENTITY.

You MAY pull in one supporting signal — but only if it sharpens the
answer to the user's actual question.  Do not stack 5+ signals.  Do not
"tour" the chart / design / numbers / type / pillars.  When in doubt,
cut the supporting signal entirely.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEAVE INTERPRETIVE SPACE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A world-class interpreter does not explain everything at once.  Trust
the user to ask the next question.  Confident enough to stop is a
feature — not a gap.

Do NOT pre-emptively explain every related mechanism, every adjacent
signal, every possible interpretation.  Answer THIS question with the
strongest signal, then stop.
"""


# ---------------------------------------------------------------------------
# Conversational compression (conversational-compression-v1)
# ---------------------------------------------------------------------------
#
# A great interpreter does not explain everything at once.  This layer
# detects which "depth mode" the current turn wants — LIGHT / NORMAL / DEEP
# — and tells the LLM how compressed the reply should be.
#
# Defaults: NORMAL.  The user can pull us into DEEP by asking "why?",
# "go deeper", "tell me more", "elaborate", "details", "synthesise", etc.
# Very short acknowledgements ("ok", "got it", "yes", "interesting") and
# short clarifying questions pull us into LIGHT.

DEEP_TRIGGER_PATTERNS = [
    r"\bgo deeper\b", r"\bdeep dive\b", r"\bdig deeper\b", r"\bdig in\b",
    r"^why\??\s*$", r"\bbut why\b",
    r"\bin (more |full )?detail\b", r"\bmore detail\b", r"\bdetails\b",
    r"\bexplain\b", r"\belaborate\b", r"\bexpand on\b", r"\bunpack\b",
    r"\btell me everything\b", r"\bfull picture\b", r"\bfull read\b",
    r"\ball of it\b", r"\bcomprehensive\b",
    r"\bsynthes(?:ise|ize|is)\b", r"\bbreak (it|that|this) down\b",
    r"\bwhat does that really mean\b", r"\bwalk me through\b",
    r"\btell me more\b",
]
_DEEP_RE = re.compile("|".join(DEEP_TRIGGER_PATTERNS), re.IGNORECASE)

LIGHT_ACK_PATTERNS = [
    r"^\s*(ok(ay)?|yes|yeah|yep|sure|right|fine|cool|nice|great|thanks?)[\.\!\?\s]*$",
    r"^\s*(got it|makes sense|interesting|hmm+|huh+|i see|fair|fair enough)[\.\!\?\s]*$",
    r"^\s*(true|exactly|same|hmm)[\.\!\?\s]*$",
]
_LIGHT_ACK_RE = re.compile("|".join(LIGHT_ACK_PATTERNS), re.IGNORECASE)

# Imperative / substantive-request patterns — even short, these are real
# questions and should default to NORMAL, not be flattened to LIGHT.
SUBSTANTIVE_REQUEST_PATTERNS = [
    r"\btell me\b", r"\bshow me\b", r"\bdescribe\b", r"\bdefine\b",
    r"\bwhat about\b", r"\bhow about\b",
    r"\bwhat (?:is|are|does)\b", r"\bhow (?:is|are|does)\b",
    r"\bcan you\b", r"\bgive me\b",
]
_SUBSTANTIVE_RE = re.compile("|".join(SUBSTANTIVE_REQUEST_PATTERNS), re.IGNORECASE)


def detect_depth_mode(user_message: str, history: List[Dict[str, str]]) -> str:
    """
    Pick a depth mode for the current turn.  Returns: "LIGHT" | "NORMAL" | "DEEP".

    Heuristics:
      - Explicit DEEP triggers ("why?", "go deeper", "elaborate", "details"…)
        → DEEP.
      - Very short acknowledgement / continuation → LIGHT.
      - Short messages (≤6 words) that aren't questions OR substantive
        requests ("tell me about X", "show me Y") → LIGHT.
      - Everything else → NORMAL.
    """
    msg = (user_message or "").strip()
    if not msg:
        return "NORMAL"
    if _DEEP_RE.search(msg):
        return "DEEP"
    if _LIGHT_ACK_RE.match(msg):
        return "LIGHT"
    word_count = len(msg.split())
    has_q = "?" in msg
    is_substantive = bool(_SUBSTANTIVE_RE.search(msg))
    if word_count <= 6 and not has_q and not is_substantive:
        return "LIGHT"
    return "NORMAL"


_DEPTH_GUIDANCE = {
    "LIGHT": (
        "DEPTH MODE: LIGHT  (fast, conversational, one insight)\n"
        "  - Target length: 2–4 sentences (≈ 30–70 words).\n"
        "  - Use ONLY components A + B (direct answer + signal).\n"
        "    A behaviour line is fine if it is one sentence.\n"
        "  - Do NOT explain mechanism.  Do NOT pull in supporting signals.\n"
        "  - One sharp observation > full architecture.  Stop early."
    ),
    "NORMAL": (
        "DEPTH MODE: NORMAL  (default — observant, not encyclopedic)\n"
        "  - Target length: 90–160 words.  ONE paragraph, or two short ones.\n"
        "  - Use A + B and 2–3 of D / E / F.  Skip the rest.\n"
        "  - Lead with the strongest signal.  At most ONE supporting signal\n"
        "    if it sharpens the answer.\n"
        "  - End when the answer is complete.  Do NOT pad."
    ),
    "DEEP": (
        "DEPTH MODE: DEEP  (user explicitly asked for more — go deeper)\n"
        "  - Target length: 200–360 words.  Layered synthesis allowed.\n"
        "  - You may use A through F generously; G only if useful.\n"
        "  - You MAY pull in one supporting signal AND its interaction\n"
        "    with the active entity.\n"
        "  - Still no therapy-bot prompts.  Still bound to grounded signals."
    ),
}


def format_compression_block(depth_mode: str) -> str:
    """Build the CONVERSATIONAL COMPRESSION system-prompt block."""
    guidance = _DEPTH_GUIDANCE.get(depth_mode, _DEPTH_GUIDANCE["NORMAL"])
    return (
        "--- CONVERSATIONAL COMPRESSION (conversational-compression-v1) ---\n"
        f"{guidance}\n"
        "\n"
        "GLOBAL RULES (apply at every depth):\n"
        "  - One reply = one dominant signal (the ACTIVE ENTITY).\n"
        "  - Do NOT try to fully complete the topic this turn.\n"
        "  - Leave interpretive space — the user is allowed to ask the next\n"
        "    question.  Confident enough to stop is a feature, not a gap.\n"
        "  - Compression must NOT flatten lens voice.  Stay in stance:\n"
        "    Astrology = symbolic · HD = mechanical · Numerology = thematic ·\n"
        "    Enneagram = motivational · BaZi = strategic."
    )



# ---------------------------------------------------------------------------
# Emotional timing (emotional-timing-v1) — conversational intensity
# ---------------------------------------------------------------------------
#
# Separate axis from depth.  Depth controls *how much* we say; intensity
# controls *how hard we land it*.
#
# Four modes (internal only — never shown to users):
#   SOFT          — emotionally safe, gentler wording, low pressure
#   OBSERVATIONAL — neutral descriptive mirror, calm precision  (DEFAULT)
#   DIRECT        — sharper pattern naming, clear consequences, less cushion
#   CONFRONTING   — high-recognition shadow surfacing, only when EARNED
#
# Intensity is NOT harshness.  Even CONFRONTING must feel precise, grounded,
# earned — never judgmental, dramatic, or performatively edgy.

# Markers that pull us DOWN to SOFT (user is vulnerable / shocked / spiralling).
_SOFT_SIGNAL_PATTERNS = [
    # Vulnerability
    r"\bi'?m (lost|scared|terrified|afraid|overwhelmed|broken|drowning|exhausted|so tired)\b",
    r"\bi (?:can'?t|cannot) (?:stop|sleep|breathe|think|cope|handle|do this)\b",
    r"\bi feel (?:so )?(lost|alone|empty|numb|hopeless|broken|stuck|crushed|small)\b",
    r"\bi don'?t know (what to do|who i am|anymore|how to)\b",
    r"\bi'?m falling apart\b", r"\bfalling apart\b",
    r"\bi'?m spirall?ing\b", r"\bspirall?ing\b",
    r"\bi'?m struggling\b", r"\bstruggling so much\b",
    # Grief / shock / loss
    r"\b(died|passed away|funeral|grief|grieving|mourning)\b",
    r"\b(broke up|breakup|divorce|ended (it|things)|left me|leaving me|abandoned me)\b",
    r"\b(miscarriage|lost (the|my) baby)\b",
    r"\bdiagnos(ed|is)\b",
    r"\b(crying|in tears|sobbing|can'?t stop crying)\b",
    r"\b(in shock|i'?m stunned|i can'?t believe)\b",
    # Distress / urgency
    r"\bplease help\b", r"\bi need help\b", r"\bsomething is wrong with me\b",
    r"\bwhy is this happening\b", r"\bwhat is wrong with me\b",
    r"\bi hate myself\b", r"\bi want to give up\b",
]
_SOFT_SIGNAL_RE = re.compile("|".join(_SOFT_SIGNAL_PATTERNS), re.IGNORECASE)

# Markers that ALLOW DIRECT — user invites sharper truth.
_DIRECT_SIGNAL_PATTERNS = [
    r"\bbe honest\b", r"\bbe real (with me)?\b", r"\bbe direct\b",
    r"\btell me the truth\b", r"\bdon'?t sugar-?coat\b", r"\bno sugar-?coating\b",
    r"\bstraight up\b", r"\bjust tell me\b",
    r"\bwhat am i avoiding\b", r"\bwhat am i missing\b",
    r"\bwhat'?s the pattern\b", r"\bwhat'?s underneath\b", r"\bwhat'?s really going on\b",
    r"\bthe real reason\b", r"\bthe truth is\b",
    r"\bcall me out\b", r"\bcall it out\b",
]
_DIRECT_SIGNAL_RE = re.compile("|".join(_DIRECT_SIGNAL_PATTERNS), re.IGNORECASE)

# Markers that explicitly INVITE CONFRONTING.
_CONFRONTING_SIGNAL_PATTERNS = [
    r"\bchallenge me\b", r"\bpush me\b", r"\bdon'?t hold back\b",
    r"\bgive it to me straight\b", r"\bwhat do i need to hear\b",
    r"\bhit me with it\b", r"\bbe brutal\b", r"\bbrutal(ly)? honest\b",
]
_CONFRONTING_SIGNAL_RE = re.compile("|".join(_CONFRONTING_SIGNAL_PATTERNS), re.IGNORECASE)


# Lens bias on the intensity ramp.  Each lens has a default "ceiling" — the
# strongest intensity it will reach when the user invites it.  Astrology
# tops out at DIRECT (stays interpretive, not absolute).  Enneagram and BaZi
# can go up to CONFRONTING when invited.  HD biases toward OBSERVATIONAL
# (mechanical mirror, not psychological confrontation).
_LENS_INTENSITY_CEILING = {
    "astrology": "DIRECT",
    "human_design": "DIRECT",
    "numerology": "DIRECT",
    "enneagram": "CONFRONTING",
    "bazi": "CONFRONTING",
}
# Default starting mode per lens (when nothing in the message moves us).
_LENS_INTENSITY_DEFAULT = {
    "astrology": "OBSERVATIONAL",
    "human_design": "OBSERVATIONAL",
    "numerology": "OBSERVATIONAL",
    "enneagram": "OBSERVATIONAL",
    "bazi": "OBSERVATIONAL",
}

_INTENSITY_RANK = {"SOFT": 0, "OBSERVATIONAL": 1, "DIRECT": 2, "CONFRONTING": 3}


def _count_direct_invitations_in_history(history: List[Dict[str, str]]) -> int:
    """How many times the user has invited a sharper read across recent turns."""
    count = 0
    for turn in (history or []):
        if not isinstance(turn, dict):
            continue
        if turn.get("role") != "user":
            continue
        content = turn.get("content", "") or ""
        if _DIRECT_SIGNAL_RE.search(content) or _CONFRONTING_SIGNAL_RE.search(content):
            count += 1
    return count


def detect_intensity_mode(
    user_message: str,
    history: List[Dict[str, str]],
    lens_name: str,
) -> str:
    """
    Pick the intensity for this turn.  Returns:
        "SOFT" | "OBSERVATIONAL" | "DIRECT" | "CONFRONTING"

    Rules (in order):
      1. SOFT wins everything: if the user is vulnerable / in distress /
         spiralling, we soften regardless of any other signal.
      2. CONFRONTING requires an EXPLICIT invitation in the current message
         AND the lens must allow it (Enneagram, BaZi).  Plus we like at
         least one prior DIRECT-type invitation in history so intensity
         feels earned, not abrupt.
      3. DIRECT triggers if the current message asks for honesty / pattern
         exposure / "what am I avoiding", capped by the lens ceiling.
      4. Conversational momentum: if 2+ prior turns have been probing,
         the floor moves from OBSERVATIONAL → DIRECT.
      5. Otherwise: lens default (OBSERVATIONAL for all 5 lenses today).
    """
    msg = (user_message or "").strip()
    if not msg:
        return _LENS_INTENSITY_DEFAULT.get(lens_name, "OBSERVATIONAL")

    # 1. SOFT always wins.
    if _SOFT_SIGNAL_RE.search(msg):
        return "SOFT"

    ceiling = _LENS_INTENSITY_CEILING.get(lens_name, "DIRECT")
    ceiling_rank = _INTENSITY_RANK[ceiling]

    # 2. Explicit CONFRONTING invitation.
    if _CONFRONTING_SIGNAL_RE.search(msg):
        if ceiling_rank >= _INTENSITY_RANK["CONFRONTING"]:
            # Lens allows CONFRONTING — but require at least one prior
            # probing turn so the confrontation feels earned, not abrupt.
            if _count_direct_invitations_in_history(history) >= 1:
                return "CONFRONTING"
            return "DIRECT"
        # Lens doesn't allow CONFRONTING (astrology / HD / numerology) —
        # step down to the lens ceiling.  The user has clearly invited
        # sharper truth, so we honour the spirit even if we can't go to
        # the top of the ramp.
        return "DIRECT" if ceiling_rank >= _INTENSITY_RANK["DIRECT"] else ceiling

    # 3. DIRECT triggers, capped by lens ceiling.
    if _DIRECT_SIGNAL_RE.search(msg):
        return "DIRECT" if ceiling_rank >= _INTENSITY_RANK["DIRECT"] else ceiling

    # 4. Momentum: 2+ probing turns in history → floor at DIRECT.
    if _count_direct_invitations_in_history(history) >= 2:
        floor = "DIRECT"
        if _INTENSITY_RANK[floor] <= ceiling_rank:
            return floor

    # 5. Lens default.
    return _LENS_INTENSITY_DEFAULT.get(lens_name, "OBSERVATIONAL")


_INTENSITY_GUIDANCE = {
    "SOFT": (
        "INTENSITY: SOFT  (the user is vulnerable / in distress — make it safe)\n"
        "  - Lead with steadiness, not analysis.  Acknowledge the weight\n"
        "    before naming any pattern.\n"
        "  - No sharp pattern exposure this turn.  No shadow language.\n"
        "    No 'here is what you are doing'.  Save those for later.\n"
        "  - Tone: warm, calm, grounded.  Pace slower.\n"
        "  - One observation is enough.  Often the right response is to\n"
        "    name what you see and stop."
    ),
    "OBSERVATIONAL": (
        "INTENSITY: OBSERVATIONAL  (default — calm, precise, neutral mirror)\n"
        "  - Describe the pattern; do not push.  Name what's there without\n"
        "    asserting consequences too strongly.\n"
        "  - Confidence without pressure.  The user gets to decide what\n"
        "    to do with the observation.\n"
        "  - Tone: clear, measured, slightly understated."
    ),
    "DIRECT": (
        "INTENSITY: DIRECT  (user invited sharpness — sharper pattern naming)\n"
        "  - Name the pattern crisply.  Name the consequence honestly.\n"
        "    Less cushioning, less hedging.\n"
        "  - You are allowed to say what the user may be avoiding — but\n"
        "    only if it's specific to THIS signal, not a generic shadow.\n"
        "  - Tone: confident, observant, slightly leaning in.  Still\n"
        "    precise — never aggressive."
    ),
    "CONFRONTING": (
        "INTENSITY: CONFRONTING  (rare — user has explicitly invited this)\n"
        "  - High-recognition shadow surfacing.  Name the defense, the\n"
        "    cost, the pattern the user has been working to not see.\n"
        "  - This is precision, not harshness.  Not judgmental.  Not\n"
        "    dramatic.  Not 'performatively edgy'.\n"
        "  - Tone: grounded, clear, earned.  The intensity comes from\n"
        "    accuracy, not from volume."
    ),
}


def format_intensity_block(intensity: str, lens_name: str) -> str:
    """Build the CONVERSATIONAL INTENSITY system-prompt block."""
    guidance = _INTENSITY_GUIDANCE.get(intensity, _INTENSITY_GUIDANCE["OBSERVATIONAL"])
    ceiling = _LENS_INTENSITY_CEILING.get(lens_name, "DIRECT")
    return (
        "--- CONVERSATIONAL INTENSITY (emotional-timing-v1) ---\n"
        f"{guidance}\n"
        "\n"
        "GLOBAL RULES (every intensity):\n"
        "  - Intensity is precision, NOT harshness.\n"
        "  - Do NOT manufacture drama.  Do NOT force shadow language.\n"
        "    Do NOT overstate consequences.  Do NOT become cryptic.\n"
        "  - Intensity ramps gradually.  Do not jump from OBSERVATIONAL\n"
        "    to CONFRONTING in one turn unless the user explicitly invited.\n"
        f"  - Lens ceiling for {lens_name}: {ceiling}.  Even when the user\n"
        f"    invites more, do not exceed this ceiling."
    )


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
    # lens-voice-differentiation-v1 — lens-specific interpretive stance,
    # injected BEFORE the universal architecture so the voice sets the tone
    # and the architecture provides the spine.
    voice_block = getattr(registry, "voice_prompt", "") or ""
    if voice_block:
        blocks.append(voice_block)
    blocks.append(UNIVERSAL_RESPONSE_ARCHITECTURE)
    # conversational-compression-v1 — depth-aware compression guidance.
    # Detected from the current user message + history.  This is the LAST
    # block so it stays freshest in the LLM's attention.
    depth_mode = detect_depth_mode(user_message, history)
    blocks.append(format_compression_block(depth_mode))
    # emotional-timing-v1 — conversational intensity calibration.
    # Separate axis from depth: depth = how much we say, intensity = how
    # hard we land it.  Goes last so it has the strongest pull on tone.
    intensity_mode = detect_intensity_mode(user_message, history, registry.lens_name)
    blocks.append(format_intensity_block(intensity_mode, registry.lens_name))

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
    # lens-voice-differentiation-v1 — surface the interpretive stance so
    # frontend dev tools can confirm voice is being applied per lens.
    debug["voice_marker"] = "lens-voice-differentiation-v1"
    debug["interpretive_stance"] = {
        "astrology": "symbolic cartographer",
        "human_design": "energetic mechanic",
        "numerology": "life-pattern decoder",
        "enneagram": "motivational psychologist",
        "bazi": "elemental strategist",
    }.get(registry.lens_name)
    # conversational-compression-v1 — surface the depth mode so callers
    # can adapt max_tokens / UX (e.g. show a "deep dive" indicator).
    debug["compression_marker"] = "conversational-compression-v1"
    debug["depth_mode"] = depth_mode
    # emotional-timing-v1 — surface the intensity mode for observability
    # and future relational-intelligence layers.
    debug["intensity_marker"] = "emotional-timing-v1"
    debug["intensity_mode"] = intensity_mode
    debug["lens_intensity_ceiling"] = _LENS_INTENSITY_CEILING.get(registry.lens_name, "DIRECT")

    return memory_block_text, debug
