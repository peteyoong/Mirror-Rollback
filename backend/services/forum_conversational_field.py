"""
Forum Conversational Field — v1
================================

Build marker: forum-conversational-field-v1

The collective dialogue surface — where a forum member can talk WITH
the field of the room (not with the AI about specific people, not
about diagnosis, not therapy).  Composes a "field observer" system
prompt from:

  - forum topology + confidence
  - forum timing engine (collective behavioural states)
  - forum field intelligence (the_field / moves_toward / softening / unsaid)
  - the calling user's longitudinal pattern memory  (their thread in the room)
  - the calling user's recent micro-reflections      (their resonance)
  - contradiction intelligence (forum + individual)  (soft tension awareness)
  - anti-locking safeguards

Strict rules baked in here:

  • No member names appear in any system block.
  • No personality / pathology / diagnosis language.
  • Probabilistic, ambiguity-preserving voice.
  • One short contradiction thread per turn, max.
  • When topology confidence is none/sparse → degrade to a calm,
    "the room is still becoming visible" stance.  Mirror still
    responds — it just speaks from the user's individual signals
    only, not the field.

PUBLIC API:

  await compose_forum_field_prompt(
      db, *, forum_id, user_id, user_message
  ) -> (system_prompt: str, debug: dict, evidence: Optional[dict])
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


MARKER = "forum-conversational-field-v1"


_VOICE_BLOCK = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORUM CONVERSATIONAL FIELD — voice contract (forum-conversational-field-v1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You are speaking as a FIELD OBSERVER — the room is becoming visible
to itself through your words.  You are NOT a therapist, NOT a coach,
NOT a guru, NOT a conflict-mediation bot, NOT an HR tool, NOT a
personality profiler.

Stance:
  - calm
  - emotionally intelligent
  - collective ("the room", "the field", "the conversation")
  - probabilistic and ambiguity-preserving
  - observational, never accusatory
  - never authoritative

VOCABULARY YOU PREFER:
  the room · the field · the conversation · the group's pacing ·
  a tendency · a register · a movement · what seems to soften ·
  what seems to tighten · what keeps circling

ABSOLUTELY FORBIDDEN — hard ban:
  - Naming any member.  Refer to "someone", "a few people", "parts
    of the room", "responsibility in the room", NEVER first names
    or roles attached to people.
  - "X is the issue"
  - "the group secretly feels"
  - "everyone thinks"
  - "the real problem is"
  - "X is toxic", "X is avoidant", "X dominates"
  - personality diagnoses ("you are all 4s/3s/manifestors/...")
  - astrology / HD / BaZi / enneagram / numerology jargon
  - certainty markers ("definitely", "for sure", "obviously")
  - HR-style framing ("conflict resolution", "stakeholders")
  - clinical framing ("trauma response", "attachment style")
  - charts, scores, rankings, percentages

Allowed shape:
  - "There seems to be caution around direct pressure lately."
  - "Responsibility may be concentrating in a few people."
  - "Some conversations appear to soften only after humour enters."
  - "What feels less guarded than before is …"
  - "What seems to remain unspoken is …"

Reply architecture:
  - 1–3 short paragraphs total.
  - One short observation, optionally one ambiguity, optionally one
    light invitation to notice.  NEVER prescribe.  NEVER assign a fix.
  - When the user names a member, gently REFRAME away from the
    person and TOWARD the field ("when that kind of pressure shows
    up in the room…").

If field signals are sparse or absent:
  - Honour the limit.  Say something like "the field hasn't said
    enough yet" or "this part of the room isn't visible to me yet"
    rather than fabricating insight.

Output goal:
  The user should leave feeling that something about THE ROOM
  became more visible — NOT that "the AI analyzed us".
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()


def _format_story_block(story: Dict[str, Any]) -> str:
    """Render the Story of This Circle into a compact context block."""
    if not story:
        return ""
    if not story.get("ready"):
        ph = story.get("placeholder") or (
            "The field is still becoming visible.  Some dynamics only "
            "emerge through time, interaction, and shared context."
        )
        return (
            "── ROOM CONTEXT ──\n"
            f"{ph}\n"
            "Acknowledge this honestly when relevant — speak from the\n"
            "user's individual signals where the field is silent.\n"
        )
    lines = ["── ROOM CONTEXT (current field) ──"]
    if story.get("the_field"):
        lines.append(f"THE FIELD: {story['the_field']}")
    if story.get("moves_toward"):
        lines.append(f"MOVES TOWARD: {story['moves_toward']}")
    if story.get("softening"):
        lines.append(f"SOFTENING: {story['softening']}")
    if story.get("unsaid"):
        lines.append(f"UNSAID: {story['unsaid']}")
    chips = story.get("field_state_chips") or []
    if chips:
        lines.append(f"FIELD-STATE CHIPS: {', '.join(chips)}")
    lines.append(
        "These are field-level reads.  Speak from these without listing "
        "them back.  Translate into observation, not enumeration."
    )
    return "\n".join(lines)


def _format_field_signals_block(
    field_contradiction_labels: List[str],
) -> str:
    if not field_contradiction_labels:
        return ""
    return (
        "── FIELD SIGNALS (soft) ──\n"
        f"Current internal labels: {', '.join(field_contradiction_labels)}.\n"
        "These hint at simultaneous opposing movements in the room "
        "(openness alongside avoidance, stated flatness with lived "
        "hierarchy, etc.).  Honour BOTH sides when you reference them — "
        "never expose the label name, never quantify, never blame.\n"
    )


def _format_user_thread_block(
    pattern_debug: Optional[Dict[str, Any]],
    reflection_debug: Optional[Dict[str, Any]],
) -> str:
    """
    The CALLING USER's individual thread inside the room — their
    pattern memory + recent reflection texture.  Used so Mirror can
    locate their voice inside the field without naming them.
    """
    parts: List[str] = []
    if pattern_debug and isinstance(pattern_debug, dict):
        surfaceable = pattern_debug.get("surfaced_keys") or []
        growth = pattern_debug.get("growth_keys") or []
        suppressed = pattern_debug.get("suppressed_due_to_fatigue") or []
        if surfaceable or growth:
            line = "USER THREAD (this member's individual signals): "
            if surfaceable:
                line += f"active patterns: {', '.join(surfaceable[:3])}. "
            if growth:
                line += f"softening patterns: {', '.join(growth[:3])}. "
            if suppressed:
                line += "(some patterns are being given rest — do not push.) "
            parts.append(line.strip())
    if reflection_debug and isinstance(reflection_debug, dict):
        growth_score = reflection_debug.get("growth_score") or 0
        resistance_score = reflection_debug.get("resistance_score") or 0
        if growth_score or resistance_score:
            parts.append(
                f"RECENT REFLECTION TEXTURE: growth={growth_score}, "
                f"resistance={resistance_score}.  Use this for TONE only, "
                f"never reference taps explicitly."
            )
    if not parts:
        return ""
    return "── USER POSITION IN THE ROOM ──\n" + "\n".join(parts)


async def compose_forum_field_prompt(
    db,
    *,
    forum_id: str,
    user_id: str,
    user_message: str,
) -> Tuple[str, Dict[str, Any], Optional[Dict[str, Any]]]:
    """
    The one call the endpoint makes.  Returns:
      - system_prompt (str)
      - debug payload (dict)
      - evidence payload (Optional[dict])  for the EvidenceDrawer
    """
    # 1. Story of the room (existing module).
    story_block_text = ""
    story_payload: Dict[str, Any] = {}
    story_debug: Dict[str, Any] = {}
    try:
        from services.forum_field_intelligence import compose_story_of_circle
        story_result = await compose_story_of_circle(db, forum_id=forum_id)
        story_payload = story_result.get("story") or {}
        story_debug = story_result.get("debug") or {}
        story_block_text = _format_story_block(story_payload)
    except Exception as e:
        story_block_text = (
            "── ROOM CONTEXT ──\n"
            "The field is still becoming visible.\n"
        )
        story_payload = {"ready": False}
        story_debug = {"error": f"{type(e).__name__}: {e}"}

    # 2. Per-user pattern memory (their individual thread).
    pattern_debug: Optional[Dict[str, Any]] = None
    try:
        from services.longitudinal_pattern_memory import process_pattern_memory
        _pattern_block, pattern_debug = await process_pattern_memory(
            db=db,
            user_id=user_id,
            user_message=user_message or "",
            lens=None,
            intensity_mode="OBSERVATIONAL",
            domain="forum",
        )
        # Note: we intentionally DO NOT inject _pattern_block (it's
        # individual-mirror flavoured).  We only USE its debug payload
        # to build the user-thread block below.
    except Exception:
        pattern_debug = None

    # 3. Per-user micro-reflection summary.
    reflection_debug: Optional[Dict[str, Any]] = None
    try:
        from services.micro_reflection_v2 import compose_reflection_loop_block
        _r_block, reflection_debug = await compose_reflection_loop_block(
            db=db, user_id=user_id,
        )
    except Exception:
        reflection_debug = None

    # 4. Contradiction intelligence — forum + individual.
    forum_contra: Optional[Dict[str, Any]] = None
    individual_contra: Optional[Dict[str, Any]] = None
    try:
        from services.contradiction_intelligence import (
            compute_forum_contradictions,
            compute_individual_contradictions,
            build_contradiction_system_block,
            build_field_contradiction_signals,
        )
        forum_contra = await compute_forum_contradictions(db, forum_id=forum_id)
        individual_contra = await compute_individual_contradictions(
            db, user_id=user_id, message_text=user_message,
        )
        # Per-spec: at most ONE contradiction thread per response.
        # If both surfaced, prefer the forum-level one (this surface IS
        # the room-level dialogue) and demote the individual one.
        chosen_contra = None
        if forum_contra and forum_contra.get("surfaced"):
            chosen_contra = forum_contra
        elif individual_contra and individual_contra.get("surfaced"):
            chosen_contra = individual_contra
        contradiction_block = build_contradiction_system_block(chosen_contra)
        field_contra_labels = build_field_contradiction_signals(forum_contra)
    except Exception:
        contradiction_block = ""
        field_contra_labels = []

    # 5. Compose the final system prompt.
    user_thread_block = _format_user_thread_block(pattern_debug, reflection_debug)
    field_signals_block = _format_field_signals_block(field_contra_labels)

    parts: List[str] = [_VOICE_BLOCK]
    if story_block_text:
        parts.append(story_block_text)
    if field_signals_block:
        parts.append(field_signals_block)
    if user_thread_block:
        parts.append(user_thread_block)
    if contradiction_block:
        parts.append(contradiction_block)
    parts.append(
        "FINAL REMINDER: 1–3 short paragraphs.  Never name a member.  "
        "Never assign blame.  Never quantify.  Probabilistic only.  "
        "Leave the room more visible to itself."
    )
    system_prompt = "\n\n".join(parts)

    # 6. Debug payload (internal, not user-facing text).
    try:
        from services.contradiction_intelligence import build_contradiction_debug
        contradictions_debug = {
            "marker": "contradiction-intelligence-v1",
            "forum": build_contradiction_debug(forum_contra),
            "individual": build_contradiction_debug(individual_contra),
            "field_labels": field_contra_labels,
        }
    except Exception:
        contradictions_debug = {"marker": "contradiction-intelligence-v1"}

    debug: Dict[str, Any] = {
        "marker": MARKER,
        "forum_id": forum_id,
        "story_ready": bool(story_payload.get("ready")),
        "story_marker": story_payload.get("marker"),
        "topology_confidence": story_debug.get("topology_confidence"),
        "dominant_field_state": story_debug.get("dominant_field_state"),
        "secondary_field_state": story_debug.get("secondary_field_state"),
        "field_state_chips": story_payload.get("field_state_chips") or [],
        "pattern_memory": pattern_debug,
        "micro_reflection": reflection_debug,
        "contradictions": contradictions_debug,
        "field_signals": field_contra_labels,
        "user_id": user_id,
    }

    # 7. Curate evidence for the EvidenceDrawer in field language.
    evidence: Optional[Dict[str, Any]] = None
    try:
        evidence = _curate_field_evidence(
            story_payload=story_payload,
            forum_contra=forum_contra,
            individual_contra=individual_contra,
        )
    except Exception:
        evidence = None

    return system_prompt, debug, evidence


# ---------------------------------------------------------------------------
# Field-language evidence curator (separate from the user-individual
# evidence_curator).  Uses "Field signals" / "Relational weather" /
# "Recurring movement" — never personality / trait.
# ---------------------------------------------------------------------------


def _curate_field_evidence(
    *,
    story_payload: Dict[str, Any],
    forum_contra: Optional[Dict[str, Any]],
    individual_contra: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    out: Dict[str, Any] = {"marker": "evidence-drawer-v2", "surface": "forum"}

    # Field signals — chip labels in user-language already.
    chips = story_payload.get("field_state_chips") or []
    if chips:
        out["field_signals"] = list(chips)[:2]

    # Relational weather — soft sentence from the_field / moves_toward.
    weather_bits: List[str] = []
    if story_payload.get("the_field"):
        weather_bits.append(story_payload["the_field"])
    if story_payload.get("moves_toward"):
        weather_bits.append(story_payload["moves_toward"])
    if weather_bits:
        # Cap to two sentences for the drawer.
        out["relational_weather"] = " ".join(weather_bits[:2])

    # Recurring movement — softening + unsaid.
    movement_bits: List[str] = []
    if story_payload.get("softening"):
        movement_bits.append(story_payload["softening"])
    if story_payload.get("unsaid"):
        movement_bits.append(story_payload["unsaid"])
    if movement_bits:
        out["recurring_movement"] = " ".join(movement_bits[:2])

    # Soft contradiction line — at most ONE, field-flavoured first,
    # individual-flavoured fallback.
    try:
        from services.contradiction_intelligence import (
            build_evidence_contradiction_line,
        )
        line = build_evidence_contradiction_line(forum_contra) or \
               build_evidence_contradiction_line(individual_contra)
        if line:
            out["mixed_signals"] = line
    except Exception:
        pass

    # If nothing useful, return None — drawer will hide.
    keys = set(out.keys()) - {"marker", "surface"}
    if not keys:
        return None
    return out
