"""retrieval_validation_v1 — Mirror Chat V2 Slice B1 (SHADOW MODE).

Emit-only receipts for routing/retrieval decisions.  Receipts live in the
`mirror_chat_retrieval_receipts` collection (created on first write) with a
30-day TTL.  Does NOT block any response; the receipt is logged after the
response has been assembled.
"""
from __future__ import annotations

import os, uuid, hashlib, logging
from datetime import datetime, timezone as dt_tz
from typing import Any, Dict, List, Optional

log = logging.getLogger("retrieval_validation_v1")
RECEIPTS_COLLECTION = "mirror_chat_retrieval_receipts"

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


def mandatory_modules(domain: str) -> List[str]:
    return list(_MANDATORY_MODULES_PER_DOMAIN.get(domain, ["cross_lens_atoms"]))


def _hash(blob: Any) -> str:
    return "sha256:" + hashlib.sha256(str(blob).encode("utf-8")).hexdigest()


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
    missing = [m for m in needed if m not in modules_invoked]
    failures: List[str] = []
    for m in modules_invoked:
        blob = payloads.get(m)
        if blob is None or (hasattr(blob, "__len__") and len(blob) == 0):
            failures.append(f"empty_payload:{m}")

    conf = float(intent_envelope.get("confidence") or 0.0)
    if missing:
        status = "FAIL"
    elif conf < 0.30:
        status = "WARNING"
    elif failures:
        status = "WARNING"
    else:
        status = "PASS"

    receipt = {
        "_id": str(uuid.uuid4()),
        "request_id": request_id,
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
        "validation_status": status,
        "validation_failures": failures,
        "computed_at": datetime.now(dt_tz.utc).isoformat(),
    }
    return receipt


async def persist_receipt(db, receipt: Dict[str, Any]) -> None:
    try:
        await db[RECEIPTS_COLLECTION].insert_one(receipt)
        # TTL idx ensures 30-day retention; idempotent create
        await db[RECEIPTS_COLLECTION].create_index(
            "computed_at", expireAfterSeconds=30 * 24 * 3600)
    except Exception as e:
        log.warning(f"[RetrievalReceipt] persist failed: {type(e).__name__}: {e}")


def format_log_line(receipt: Dict[str, Any]) -> str:
    env = receipt["intent_envelope"]
    return (
        f"[RetrievalReceipt] req={receipt['request_id']} "
        f"domain={env.get('primary_domain')!r} conf={env.get('confidence')} "
        f"status={receipt['validation_status']} "
        f"modules={receipt['mandatory_modules_invoked']} "
        f"missing={receipt['mandatory_modules_missing']}"
    )
