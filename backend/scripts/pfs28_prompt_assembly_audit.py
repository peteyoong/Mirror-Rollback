"""PFS-2.8 read-only prompt-assembly instrumentation.

Imports the prompt-builder modules and measures the token / char weight
of each block under a synthetic Jay-in-Pulsifi-Leadership receipt.

No source files are modified. No prompts are sent to any LLM. The
script only runs the in-process builders to measure their output size.
"""
import asyncio
import json
import os
import sys
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
sys.path.insert(0, "/app/backend")


def tk(text: str) -> int:
    """Best-effort token count: prefer tiktoken if installed, else
    fall back to a 4-chars-per-token estimate (industry rule of thumb)."""
    if not text:
        return 0
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return (len(text) + 3) // 4


def measure(label: str, text: str) -> Dict[str, Any]:
    return {
        "label":  label,
        "chars":  len(text) if text else 0,
        "tokens": tk(text or ""),
    }


def main():
    # ── 1. Base system prompt
    from server import MIRROR_SYSTEM_PROMPT, LENS_PROMPTS
    base = measure("MIRROR_SYSTEM_PROMPT (base)", MIRROR_SYSTEM_PROMPT)

    # ── 2. Lens preambles (LENS_PROMPTS dict)
    lens_sizes = {
        k: measure(f"LENS_PROMPTS[{k!r}]", v) for k, v in LENS_PROMPTS.items()
    }

    # ── 3. PFS-2.1/2.3 intent V2 prompt block (the block that carries
    #      topology + P3 + cross-lens). Build it against a SYNTHETIC
    #      Jay scenario to get its exact emitted size.
    from services.mirror_chat_phase4_enrichment import (
        build_intent_v2_prompt_block,
    )

    # Synthetic v2_receipt matching what the resolver+planner would
    # emit for "What role does Jay play in helping this leadership
    # team succeed?" with topology edge Pete → Jay : cofounder in
    # Pulsifi Leadership.
    synthetic_receipt: Dict[str, Any] = {
        "shadow_mode": True,
        "intent_envelope": {
            "primary_domain": "leadership",
            "confidence":     0.74,
            "secondary_domains": ["career", "team_dynamics"],
            "evidence": {
                "matched_phrases": {
                    "leadership":     ["leadership team", "role"],
                    "career":         ["succeed"],
                }
            },
        },
        "relationship_resolution": {
            "target":       "synthetic-jay-uid",
            "target_name":  "Jay",
            "role":         "cofounder",
            "forum_id":     "synthetic-pulsifi-fid",
            "forum_name":   "Pulsifi Leadership",
            "resolution_source": "business_forum",
            "topology_role_found":  True,
            "topology_role_type":   "cofounder",
            "topology_confidence":  "high",
            "topology_inferred":    False,
        },
        "relationship_orchestration_v1": {
            "computed":       True,
            "version":        "relationship_orchestration_v1.1.0",
            "role_resolved":  "cofounder",
            "rule_bucket":    "cofounder",
            "framing_hint":   "cofounder_strategic",
            "domain_bias":    "work",
            "lens_priority_before": ["astrology", "human_design", "enneagram",
                                     "numerology", "relationship", "timeline"],
            "lens_priority_after":  ["astrology", "human_design", "enneagram",
                                     "relationship", "numerology", "timeline"],
            "replanned_after_topology": True,
        },
        "cross_lens_synthesis_v2": {
            "computed": True,
            "contradictions": [
                {"dominant": "leadership", "counter": "relationship",
                 "delta": 0.41},
            ],
        },
        "forum_topology_resolution": {
            "topology_supplied": True,
            "active_member_id":  "synthetic-jay-uid",
        },
        "frame_source": {"derived_frame": "forum"},
    }

    iv2_block, iv2_debug = build_intent_v2_prompt_block(synthetic_receipt)
    iv2_measure = measure("intent_v2 prompt block (PFS-2.1/2.3 surface)",
                          iv2_block or "")

    # Also build it WITH the P3 + cross-lens flags forced on so we can
    # see what the block WOULD look like once the flags flip — this is
    # a STATIC analysis, no env var is changed for the running backend.
    os.environ["RELATIONSHIP_ORCHESTRATION_PROMPT"] = "true"
    os.environ["CROSS_LENS_PROMPT_SURFACE"]         = "true"
    # The enrichment module reads the env on each call via helpers.
    iv2_block_ungated, iv2_debug_ungated = build_intent_v2_prompt_block(
        synthetic_receipt)
    iv2_ungated_measure = measure(
        "intent_v2 prompt block (HYPOTHETICAL with both flags=true)",
        iv2_block_ungated or "")
    # Restore — this only affected the in-process env of this script.
    os.environ["RELATIONSHIP_ORCHESTRATION_PROMPT"] = "false"
    os.environ["CROSS_LENS_PROMPT_SURFACE"]         = "false"

    # ── 4. Proof block builders — measure approximate output for a
    #      typical user by reading the module source (handler functions
    #      with multi-line f-strings).  We cannot easily synthesise
    #      complete chart envelopes for these, so we report a
    #      static-source line-count + an estimated multiplier from
    #      the chart-payload contract.
    proof_files = [
        ("services/house_inventory_engine.py",   "build_house_inventory_proof_block"),
        ("services/field_synthesis_engine.py",   "build_field_synthesis_proof_block"),
        ("services/lifecycle_engine.py",         "build_lifecycle_proof_block"),
        ("services/solar_return_engine.py",      "build_solar_return_proof_block"),
        ("services/natal_object_engine.py",      "build_natal_object_proof_block"),
        ("services/pressure_topology_engine.py", "build_pressure_topology_proof_block"),
        ("services/astrology_chat_router.py",    "build_transit_object_proof_block"),
        ("services/relationship_resolver.py",    "build_relational_synthesis_block"),
    ]
    proof_measurements = []
    for path, fn in proof_files:
        full = os.path.join("/app/backend", path)
        if not os.path.exists(full):
            continue
        with open(full, "r") as fh:
            text = fh.read()
        # Approximate output: take everything between def ... and the
        # next top-level def or EOF.
        idx = text.find(f"def {fn}")
        if idx == -1: continue
        nxt = text.find("\ndef ", idx + 1)
        snippet = text[idx:nxt if nxt != -1 else len(text)]
        proof_measurements.append({
            "file": path, "fn": fn,
            "source_lines":     snippet.count("\n"),
            "source_chars":     len(snippet),
            "approx_output_tokens_lower_bound": tk(snippet) // 3,
            "approx_output_tokens_upper_bound": tk(snippet),
            "note":
                "lower=runtime output is shorter than source; "
                "upper=runtime output occasionally matches source verbatim. "
                "Treat as order-of-magnitude.",
        })

    # ── 5. Founder context + timeline V2 blocks — also static
    from services.mirror_chat_phase4_enrichment import (
        build_founder_context_block,
        build_timeline_v2_context,
    )

    fc_block, _ = asyncio.run(_call_founder(synthetic_receipt))
    tl_block, _ = asyncio.run(_call_timeline())
    fc_measure = measure("founder_context block (PFS phase4)", fc_block or "")
    tl_measure = measure("timeline_v2 block (PFS phase4)", tl_block or "")

    # ── 6. Dominance ranking — sort by tokens desc
    blocks = [base, iv2_measure, iv2_ungated_measure, fc_measure, tl_measure]
    blocks += [
        {"label": pm["fn"] + "  (approx, source-proxy)",
         "chars":  pm["source_chars"],
         "tokens": pm["approx_output_tokens_upper_bound"]}
        for pm in proof_measurements
    ]
    blocks += [{"label": f"LENS_PROMPTS[{k}]",
                "chars": v["chars"], "tokens": v["tokens"]}
               for k, v in lens_sizes.items()]
    ranking = sorted(blocks, key=lambda b: b["tokens"], reverse=True)

    # ── Output ────────────────────────────────────────────────────────
    out = {
        "base_system_prompt":               base,
        "lens_preambles":                   lens_sizes,
        "intent_v2_block_current_flags_off": iv2_measure,
        "intent_v2_block_current_flags_off_debug": iv2_debug,
        "intent_v2_block_hypothetical_flags_on": iv2_ungated_measure,
        "intent_v2_block_hypothetical_flags_on_debug": iv2_debug_ungated,
        "founder_context_block":            fc_measure,
        "timeline_v2_block":                tl_measure,
        "proof_block_source_proxies":       proof_measurements,
        "dominance_ranking_by_tokens_desc": ranking,
    }
    print(json.dumps(out, indent=2, default=str))


async def _call_founder(receipt):
    from services.mirror_chat_phase4_enrichment import build_founder_context_block
    try:
        return await build_founder_context_block(
            db=None, user_id="x", v2_receipt=receipt,
            user_message="What role does Jay play in helping this leadership team succeed?")
    except Exception as e:
        return (f"<builder error: {type(e).__name__}: {e}>",
                {"error": True})


async def _call_timeline():
    from services.mirror_chat_phase4_enrichment import build_timeline_v2_context
    try:
        return await build_timeline_v2_context(
            db=None, user_id="x", window_days=14, max_events=8)
    except Exception as e:
        return (f"<builder error: {type(e).__name__}: {e}>",
                {"error": True})


if __name__ == "__main__":
    main()
