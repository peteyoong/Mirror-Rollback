"""retrieval_validation_v1 — Mirror Chat V2 Slice B1 (SHADOW MODE).

B1.1 update: routing confidence and retrieval completeness are now scored
separately so they don't conflate.  The top-level `validation_status` is
the *retrieval* gate (the user-facing “did we actually retrieve the right
stuff” signal), while `routing_status` is a parallel telemetry signal we
use for shadow-mode dashboards and the B2 cutover decision.

Receipts live in the `mirror_chat_retrieval_receipts` collection (created
on first write) with a 30-day TTL.  Emit-only; never blocks a response.
"""
from __future__ import annotations

import os, uuid, hashlib, logging
from datetime import datetime, timezone as dt_tz
from typing import Any, Dict, List, Optional

log = logging.getLogger("retrieval_validation_v1")
RECEIPTS_COLLECTION = "mirror_chat_retrieval_receipts"
VALIDATOR_VERSION = "retrieval_validation_v1.1.0"

_MANDATORY_MODULES_PER_DOMAIN: Dict[str, List[str]] = {
    "relationship":   ["relationship_resolver", "relationship_field", "relationship_astrology_engine", "relationship_3layer"],
    "family":         ["relationship_resolver", "relationship_3layer"],
    "parenting":      ["relationship_resolver", "relationship_3layer"],
    "career":         ["astrology_domain_context", "cross_lens_synthesis", "timeline"],
    "work":           ["astrology_domain_context", "timeline"],
    "leadership":     ["human_design", "astrology_domain_context", "cross_lens_synthesis"],
    "money":          ["astrology_domain_context", "numerology", "timeline"],
    "purpose":        ["astrology_domain_context", "human_design", "cross_lens_synthesis"],
    "spirituality":   ["astrology_domain_context", "human_design"],
    "health":         ["human_design", "astrology_domain_context"],
    "growth":         ["cross_lens_atoms", "tension_engine"],
    "identity":       ["astrology_domain_context", "human_design", "enneagram"],
    "life_direction": ["astrology_domain_context", "timeline", "human_design"],
    "general":        ["cross_lens_atoms"],
}

# Routing-status thresholds (separate from retrieval).
ROUTING_SIGNAL_PASS = 0.30
ROUTING_SIGNAL_WARN = 0.20
ROUTING_MARGIN_PASS = 0.10


def mandatory_modules(domain: str) -> List[str]:
    return list(_MANDATORY_MODULES_PER_DOMAIN.get(domain, ["cross_lens_atoms"]))


def _hash(blob: Any) -> str:
    return "sha256:" + hashlib.sha256(str(blob).encode("utf-8")).hexdigest()


def _retrieval_status(
    needed: List[str], invoked: List[str], payloads: Dict[str, Any]
) -> tuple[str, List[str], List[str]]:
    """PASS / WARNING / FAIL on retrieval completeness only."""
    missing = [m for m in needed if m not in invoked]
    empties: List[str] = []
    for m in invoked:
        blob = payloads.get(m)
        if blob is None or (hasattr(blob, "__len__") and len(blob) == 0):
            empties.append(f"empty_payload:{m}")
    if missing:
        return "FAIL", missing, empties
    if empties:
        return "WARNING", missing, empties
    return "PASS", missing, empties


def _routing_status(envelope: Dict[str, Any]) -> tuple[str, List[str]]:
    """PASS / WARNING / FAIL on the router's confidence in its own decision."""
    signal = float(envelope.get("signal_strength") or 0.0)
    margin = float(envelope.get("margin") or 0.0)
    domain = envelope.get("primary_domain") or "general"
    reasons: List[str] = []
    if domain == "general":
        reason = (envelope.get("evidence") or {}).get("fallback_reason")
        if reason in ("low_signal", "weak_ambiguous"):
            return "FAIL", [f"routing_fallback:{reason}"]
        return "WARNING", ["routing_general:no_signal"]
    if signal < ROUTING_SIGNAL_WARN:
        return "FAIL", ["routing_signal_below_warn"]
    if signal < ROUTING_SIGNAL_PASS:
        reasons.append("routing_signal_below_pass")
    if margin < ROUTING_MARGIN_PASS:
        reasons.append("routing_margin_below_pass")
    if reasons:
        return "WARNING", reasons
    return "PASS", []


def build_receipt(
    *, request_id: str,
    intent_envelope: Dict[str, Any],
    relationship_resolution: Optional[Dict[str, Any]],
    modules_invoked: List[str],
    payloads: Dict[str, Any],
    timeline_window: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    domain = intent_envelope.get("primary_domain") or "general"
    needed = mandatory_modules(domain)
    retrieval_status, missing, empties = _retrieval_status(needed, modules_invoked, payloads)
    routing_status, routing_reasons = _routing_status(intent_envelope)

    # Top-level `validation_status` mirrors retrieval (that's the user-
    # facing “did we actually retrieve the right stuff” gate).
    receipt = {
        "_id": str(uuid.uuid4()),
        "request_id": request_id,
        "validator_version": VALIDATOR_VERSION,
        "router_version": intent_envelope.get("router_version"),
        "intent_envelope": intent_envelope,
        "relationship_resolution": relationship_resolution,
        "domain_selected": domain,
        "context_retrieved": {
            "user_chart":   bool(payloads.get("user_chart")),
            "target_chart": bool(payloads.get("target_chart")),
            "timeline_window": timeline_window,
            "lens_payloads": [
                {"lens": k, "hash": _hash(v),
                 "size_chars": len(str(v)) if v is not None else 0}
                for k, v in payloads.items() if k in ("astrology", "human_design", "enneagram", "numerology")
            ],
        },
        "mandatory_modules_invoked": modules_invoked,
        "mandatory_modules_missing": missing,
        "validation_status": retrieval_status,        # back-compat → retrieval gate
        "validation_failures": empties,
        "retrieval_status": retrieval_status,
        "retrieval_failures": empties,
        "routing_status": routing_status,
        "routing_reasons": routing_reasons,
        "signal_strength": intent_envelope.get("signal_strength"),
        "margin": intent_envelope.get("margin"),
        "confidence": intent_envelope.get("confidence"),
        "computed_at": datetime.now(dt_tz.utc).isoformat(),
    }
    return receipt


async def persist_receipt(db, receipt: Dict[str, Any]) -> None:
    try:
        await db[RECEIPTS_COLLECTION].insert_one(receipt)
        await db[RECEIPTS_COLLECTION].create_index(
            "computed_at", expireAfterSeconds=30 * 24 * 3600)
    except Exception as e:
        log.warning(f"[RetrievalReceipt] persist failed: {type(e).__name__}: {e}")


def format_log_line(receipt: Dict[str, Any]) -> str:
    env = receipt["intent_envelope"]
    return (
        f"[RetrievalReceipt] req={receipt['request_id']} "
        f"domain={env.get('primary_domain')!r} "
        f"signal={env.get('signal_strength')} margin={env.get('margin')} "
        f"retrieval={receipt['retrieval_status']} "
        f"routing={receipt['routing_status']} "
        f"modules={receipt['mandatory_modules_invoked']} "
        f"missing={receipt['mandatory_modules_missing']}"
    )
