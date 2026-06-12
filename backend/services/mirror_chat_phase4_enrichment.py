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
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("mirror_chat_phase4")


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
    if tgt:
        role_part = f" (role: {tgt_role})" if tgt_role else ""
        lines.append(f"Relationship target: bound{role_part}")
        debug["intent_v2_signals"].append(f"target_bound:{tgt_role or '?'}")
    elif tgt_unres:
        lines.append(
            f"Relationship target: '{tgt_unres}' is mentioned but NOT in "
            f"the user's saved people. Acknowledge this rather than "
            f"guessing who they are. Ask the user who '{tgt_unres}' is."
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
