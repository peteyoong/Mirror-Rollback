"""services/advanced_object_resolver.py — Option C shared resolver.

ONE canonical resolver consumed by every chat surface so that
'Tell me about my Juno' (and any other advanced-object query)
returns the same placement-aware answer regardless of whether the
user is on:

  * POST /api/mirror/chat
  * POST /api/forums/{id}/chat
  * POST /api/forums/{id}/mirror-chat

Encapsulates:
  • classify_astrology_intent   (intent classification)
  • compute_natal_object        (Swiss Ephemeris on-demand)
  • build_natal_object_proof_block / build_mirror_object_proof_block
    (deterministic Mirror-voiced LLM prompts)
  • pairwise + axis handling    (NN↔SN, Ceres+Vesta, etc.)
  • multi-object handling
  • cross-chart pairwise        (Pete's Juno ↔ Mel's Juno, etc.)
  • frame-aware chart selection (SELF / MEMBER / PAIRWISE)

Surfaces call ONE function: `resolve_advanced_object(...)`.

Public envelope shape (Pythonic dataclass-equivalent dict):

    {
      "matched":          bool,       # did the query name an advanced object?
      "mode":             str,        # 'single' | 'axis' | 'pairwise' | 'cross_chart_pairwise' | 'none'
      "intent":           dict|None,  # raw classifier output (for debug logging)
      "envelopes":        list,       # all natal-object envelopes computed
      "primary_envelope": dict|None,  # first computed envelope (back-compat)
      "proof_block":      str|None,   # deterministic Mirror-voiced LLM prompt
                                      # to be appended to the system prompt
      "objects":          list,       # canonical object names actually resolved
      "axis":             str|None,   # 'nodal' for NN+SN axis, else None
      "debug": {
          "route_used":   str,        # caller-supplied diagnostic tag
          "frame":        str,        # SELF | MEMBER | PAIRWISE
          "self_used":    bool,       # did we read self chart?
          "target_used":  bool,       # did we read target chart?
          "objects_resolved":   list, # successfully computed canonical names
          "objects_unresolved": list, # canonical names that failed to compute
      }
    }

Surfaces use it as:

    resolved = resolve_advanced_object(
        query=request.message,
        self_chart=self_chart,
        target_chart=target_chart_or_none,
        frame="SELF" | "MEMBER" | "PAIRWISE",
        self_name="Pete",
        target_name="Mel" or None,
        route_tag="forums_chat",   # diagnostic only
    )
    if resolved["matched"]:
        system_prompt += "\n\n" + resolved["proof_block"]
        debug["natal_object_used"]      = True
        debug["natal_object_canonical"] = resolved["primary_envelope"]["object"]

Build marker: ADVANCED-OBJECT-RESOLVER-V1
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

BUILD_MARKER = "advanced-object-resolver-v1"

# Frame literals — kept as strings so this module has no hard import
# dependency on relationship_field_v2.ActiveFrame.
FRAME_SELF     = "SELF"
FRAME_MEMBER   = "MEMBER"
FRAME_PAIRWISE = "PAIRWISE"
FRAME_FORUM    = "FORUM"
FRAME_NONE     = "NONE"


# ---------------------------------------------------------------------------
# Cross-chart "their X / your X" detection
# ---------------------------------------------------------------------------
# When the user asks "How do Mel's Juno and my Juno interact?" we need to
# produce a SINGLE pairwise interpretation comparing the SAME object on
# both charts.  Simple heuristic: if the query references the target by
# name OR uses any possessive-marker pointing at the target (e.g. "their",
# the target's first name), AND the frame is PAIRWISE/MEMBER, we treat the
# query as cross-chart.
import re

_POSSESSIVE_OTHER_RE = re.compile(
    r"\b(their|her|his|"
    r"[A-Z][a-z]+'s)\b",
    re.IGNORECASE,
)


def _query_references_target(query: str, target_name: Optional[str]) -> bool:
    if not target_name:
        return False
    # Direct first-name match (possessive or bare)
    fname = target_name.split()[0].strip()
    if not fname:
        return False
    if re.search(rf"\b{re.escape(fname)}('s|s'|)\b", query, re.IGNORECASE):
        return True
    return bool(_POSSESSIVE_OTHER_RE.search(query))


def _query_references_self(query: str) -> bool:
    return bool(re.search(r"\b(my|mine|i'm|i am|i\b)\b", query, re.IGNORECASE))


def resolve_advanced_object(
    *,
    query: str,
    self_chart: Optional[Dict[str, Any]],
    target_chart: Optional[Dict[str, Any]] = None,
    frame: str = FRAME_SELF,
    self_name: str = "you",
    target_name: Optional[str] = None,
    route_tag: str = "unknown",
    history: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Single entry point.  See module docstring for envelope shape."""
    # Lazy imports — avoid heavy cost when the resolver is not engaged.
    from services.astrology_chat_router import classify_astrology_intent
    from services.natal_object_engine import (
        compute_natal_object,
        build_natal_object_proof_block,
    )
    from services.mirror_object_interpreter import (
        build_axis_mirror_block,
        build_pairwise_mirror_block,
        is_nodal_axis,
    )

    debug = {
        "route_used":          route_tag,
        "frame":               frame or FRAME_NONE,
        "self_used":           False,
        "target_used":         False,
        "objects_resolved":    [],
        "objects_unresolved":  [],
        "build_marker":        BUILD_MARKER,
    }

    not_matched_envelope = {
        "matched": False, "mode": "none",
        "intent": None, "envelopes": [], "primary_envelope": None,
        "proof_block": None, "objects": [], "axis": None,
        "debug": debug,
    }

    # ── 1. classify intent ──────────────────────────────────────────
    try:
        intent = classify_astrology_intent(query, history=history) or {}
    except Exception as e:    # pragma: no cover
        logger.debug(
            f"[advanced_object_resolver] classify_astrology_intent "
            f"raised {type(e).__name__}: {e!r}; passing through as no-match"
        )
        intent = {}

    if (intent.get("data_mode") != "natal_object"
            or not (intent.get("objects") or intent.get("object"))):
        return not_matched_envelope

    objects: List[str] = list(intent.get("objects") or [])
    if not objects and intent.get("object"):
        objects = [intent["object"]]
    axis_tag = intent.get("axis")
    multi    = bool(intent.get("multi")) or len(objects) > 1

    debug["intent_objects"] = objects
    debug["axis"]           = axis_tag

    # ── 2. choose which chart(s) each object should be computed on ──
    # Rules:
    #   FRAME_SELF     → all objects use self_chart
    #   FRAME_MEMBER   → all objects use target_chart (or self if missing)
    #   FRAME_PAIRWISE → if query references both sides:
    #                      cross-chart mode → compute the SAME body on
    #                      both charts and use cross-chart builder.
    #                    else if query only references target → MEMBER
    #                    else → SELF
    #   FRAME_FORUM    → SELF behaviour for now
    #   FRAME_FORUM    → if query references the target by name and NOT
    #                      the self, route as target-only (same shape as
    #                      MEMBER); otherwise fall through to SELF.  This
    #                      handles Forum-tab queries like "Tell me about
    #                      Mel's Juno" where ADV-OBJ-13's bridge has
    #                      already hydrated `target_chart` from the
    #                      orchestrator's resolved target but the message
    #                      contains no self-pronoun (so no PAIRWISE
    #                      escalation was warranted).  ADV-OBJ-14.
    cross_chart = False
    use_target_only = False

    if frame == FRAME_MEMBER and target_chart is not None:
        use_target_only = True
    elif frame == FRAME_PAIRWISE and target_chart is not None:
        refs_self   = _query_references_self(query)
        refs_target = _query_references_target(query, target_name)
        if refs_target and refs_self:
            cross_chart = True
        elif refs_target and not refs_self:
            use_target_only = True
        # else: default to SELF
    elif frame == FRAME_FORUM and target_chart is not None:
        # ADV-OBJ-14 — Target-only Forum-frame path.
        refs_target = _query_references_target(query, target_name)
        refs_self   = _query_references_self(query)
        if refs_target and not refs_self:
            use_target_only = True
        # else: default to SELF
    # FRAME_SELF / FRAME_FORUM (no target_chart) / FRAME_NONE default: self chart.

    envelopes: List[Dict[str, Any]] = []
    target_envelopes: List[Dict[str, Any]] = []

    primary_chart = target_chart if use_target_only else self_chart

    for obj in objects:
        try:
            env = compute_natal_object(primary_chart, obj)
        except Exception as e:    # pragma: no cover
            logger.debug(
                f"[advanced_object_resolver] compute_natal_object "
                f"raised for {obj!r}: {e!r}"
            )
            env = {"success": False, "object": obj,
                   "reason": "compute_exception", "message": str(e)}
        envelopes.append(env)
        debug["self_used"] = debug["self_used"] or (
            not use_target_only
        )
        debug["target_used"] = debug["target_used"] or use_target_only
        if env.get("success"):
            debug["objects_resolved"].append(env.get("object"))
        else:
            debug["objects_unresolved"].append(obj)
        if cross_chart and target_chart is not None:
            try:
                target_env = compute_natal_object(target_chart, obj)
            except Exception as e:    # pragma: no cover
                target_env = {
                    "success": False, "object": obj,
                    "reason": "compute_exception", "message": str(e),
                }
            target_envelopes.append(target_env)
            debug["target_used"] = True
            if target_env.get("success"):
                debug["objects_resolved"].append(
                    f"{target_env.get('object')}@target"
                )
            else:
                debug["objects_unresolved"].append(f"{obj}@target")

    primary_env = envelopes[0] if envelopes else None

    # ── 3. build proof block based on shape ─────────────────────────
    proof_block: Optional[str] = None
    mode = "single"

    if cross_chart and target_envelopes:
        # CROSS-CHART pairwise — one body, two charts (e.g. Pete's Juno
        # vs. Mel's Juno).  We always restrict cross-chart to the FIRST
        # object the user mentioned; multi-body cross-chart queries are
        # currently degraded to single cross-chart of the first body
        # rather than synthesised across the matrix (a follow-up if
        # needed).
        proof_block = build_cross_chart_mirror_block(
            self_env=envelopes[0],
            target_env=target_envelopes[0],
            self_name=self_name,
            target_name=target_name or "they",
        )
        mode = "cross_chart_pairwise"
    elif len(envelopes) >= 2 and axis_tag == "nodal":
        nn_env = next((e for e in envelopes
                       if e.get("object") == "North Node"),
                      envelopes[0])
        sn_env = next((e for e in envelopes
                       if e.get("object") == "South Node"),
                      envelopes[-1])
        proof_block = build_axis_mirror_block(nn_env, sn_env)
        mode = "axis"
    elif len(envelopes) >= 2:
        proof_block = build_pairwise_mirror_block(envelopes)
        mode = "pairwise"
    elif primary_env is not None:
        # ADV-OBJ-15 — When the proof block describes a target chart
        # (Forum-tab target-only path from ADV-OBJ-14), pass the target
        # name so the instruction templates address the right person
        # instead of "you".  No-op in the self-chart case.
        proof_block = build_natal_object_proof_block(
            primary_env,
            chart_owner_name=target_name if use_target_only else None,
        )
        mode = "single"

    # ── 4. log canonical resolver trail ─────────────────────────────
    logger.info(
        "[AdvancedObjectResolver] "
        f"route={route_tag} "
        f"frame={frame} "
        f"mode={mode} "
        f"query={query!r} "
        f"objects={objects} "
        f"cross_chart={cross_chart} "
        f"use_target_only={use_target_only} "
        f"axis={axis_tag} "
        f"resolved={debug['objects_resolved']} "
        f"unresolved={debug['objects_unresolved']}"
    )

    return {
        "matched":          True,
        "mode":             mode,
        "intent":           intent,
        "envelopes":        envelopes,
        "target_envelopes": target_envelopes if cross_chart else [],
        "primary_envelope": primary_env,
        "proof_block":      proof_block,
        "objects":          objects,
        "axis":             axis_tag,
        "debug":            debug,
    }


# ---------------------------------------------------------------------------
# Cross-chart Mirror block — Pete's Juno ↔ Mel's Juno style
# ---------------------------------------------------------------------------
def build_cross_chart_mirror_block(
    *,
    self_env: Dict[str, Any],
    target_env: Dict[str, Any],
    self_name: str,
    target_name: str,
) -> str:
    """Cross-chart pairwise interpretation: ONE body, TWO charts.

    Used by frame=PAIRWISE queries like 'How do Mel's Juno and my Juno
    interact?'.  Each side contributes a placement; the LLM is asked to
    read the interaction as ONE behavioural dynamic, not as two stacked
    single-body reads.
    """
    # Defensive — if either side failed to compute, fall back to the
    # single-block builder for whichever side succeeded.  ADV-OBJ-15:
    # when we fall back to the target side, pass target_name so the
    # instruction block addresses the right person.
    if not self_env or not self_env.get("success"):
        from services.natal_object_engine import build_natal_object_proof_block
        return build_natal_object_proof_block(
            target_env,
            chart_owner_name=target_name,
        )
    if not target_env or not target_env.get("success"):
        from services.natal_object_engine import build_natal_object_proof_block
        return build_natal_object_proof_block(self_env)

    from services.mirror_object_interpreter import _format_placement_display

    self_obj = self_env.get("object", "?")
    target_obj = target_env.get("object", "?")
    self_p = self_env.get("placement") or {}
    target_p = target_env.get("placement") or {}
    self_disp = _format_placement_display(self_p)
    target_disp = _format_placement_display(target_p)
    self_house = self_p.get("house")
    target_house = target_p.get("house")

    return (
        f"━━━━ NATAL OBJECT — CROSS-CHART INTERPRETATION: "
        f"{self_name}'s {self_obj} ↔ {target_name}'s {target_obj} ━━━━\n"
        f"placements:\n"
        f"  {self_name}'s {self_obj}: {self_disp}"
        f"{', house ' + str(self_house) if self_house else ''}\n"
        f"  {target_name}'s {target_obj}: {target_disp}"
        f"{', house ' + str(target_house) if target_house else ''}\n"
        f"build:            {BUILD_MARKER}\n"
        "sign attribution: True Sidereal-M Midpoint (same as natal charts)\n"
        "\n"
        "INSTRUCTION TO YOU:\n"
        "Read this as ONE relational dynamic between two people on the\n"
        "SAME archetypal body, NOT as two separate placements.  Cite\n"
        f"each side's sign+house ONCE in the opening sentence, then\n"
        "switch into behaviour.\n"
        "\n"
        "Use the BEHAVIOR-FIRST CROSS-CHART STRUCTURE (do NOT print the\n"
        "labels; write natural prose):\n"
        "\n"
        f"  SHARED PATTERN — what {self_name} and {target_name} repeatedly\n"
        f"    do TOGETHER around this body in real life.  ONE concrete,\n"
        "    observable scene where both placements are clearly in motion.\n"
        "\n"
        "  SHARED TENSION — the threshold where the two signatures stop\n"
        "    fitting smoothly.  What happens when one person's way of\n"
        "    holding this body collides with the other's.\n"
        "\n"
        "  SHARED GIFT — what becomes available when they meet this body\n"
        "    consciously rather than defaulting into their respective\n"
        "    automatic shapes.\n"
        "\n"
        "  HOW THEY INTERACT — one paragraph (2–3 sentences) on the\n"
        "    daily mechanics: ONE place the two signatures reinforce\n"
        "    each other, ONE place they pull against each other.\n"
        "\n"
        "  OBSERVABLE SIGNAL — one short closing line about what an\n"
        "    outside observer would notice about THIS pairing on THIS\n"
        "    body.\n"
        "\n"
        "VOICE FLOOR: behavioural, present tense, conversational.  No\n"
        "destiny, soulmate, fated, karmic, twin-flame, marriage-guarantee,\n"
        "shadow-cliché, or fortune-telling vocabulary.  No 'this placement\n"
        "suggests' / 'indicates' / 'invites' framing.\n"
        "\n"
        f"Length: 180–260 words total.  Refer to the two people by name\n"
        f"({self_name}, {target_name}), not as 'partner A' / 'partner B'.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
