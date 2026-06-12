#!/usr/bin/env python3
"""
P0 Intelligence Utilization Audit — Live Probe Trace
====================================================

READ-ONLY end-to-end trace of the Mirror chat pipeline.

For each probe message we:
  1. POST to /api/mirror/chat (live endpoint).
  2. Read the V2 receipt the call just persisted (latest receipt for that
     user_id after our request timestamp).
  3. Pull the matching `[MIRROR_CHAT]...[phase4-*]` log lines from
     `/var/log/supervisor/backend.err.log` to capture per-block emission
     telemetry (intent_v2 block emitted? timeline events count? founder
     signals? PFS2.1 / PFS2.3 ?).
  4. Run the response through a lightweight keyword scorer that asks:
       — did the response surface any of the signals the V2 receipt
         claims to have been computed (founder hits, target name, role,
         primary domain, secondary lenses)?
  5. Persist everything to a JSON for the markdown renderer.

No writes to MongoDB.  No code changes.  No flag changes.
"""
import asyncio
import json
import os
import re
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = "http://localhost:8001"
ENDPOINT    = f"{BACKEND_URL}/api/mirror/chat"

# Reference users (preview DB).
USERS: Dict[str, str] = {
    "Pete":  "697f0c6abf35c0528ff06954",
    "Mel":   "697ec826ad4b18f75bf42616",
}

# Probe matrix — (category, intent_key, user_label, message).
PROBES: List[Tuple[str, str, str, str]] = [
    # Founder Intelligence (Pete = founder)
    ("Founder", "founder_blind_spot",    "Pete",
     "What is my biggest founder blind spot?"),
    ("Founder", "pulsifi_not_seeing",    "Pete",
     "What am I not seeing in Pulsifi?"),
    ("Founder", "leadership_pattern",    "Pete",
     "What leadership pattern keeps repeating?"),
    ("Founder", "founder_growth_edge",   "Pete",
     "What is my next growth edge as a founder?"),
    # Relationship Intelligence (Pete asking about Mel)
    ("Relationship", "tell_about_mel",   "Pete",
     "Tell me about Mel"),
    ("Relationship", "mel_maps_to_me",   "Pete",
     "How does Mel map to me?"),
    ("Relationship", "mel_not_seeing",   "Pete",
     "What am I not seeing about Mel?"),
    ("Relationship", "us_tension",       "Pete",
     "What tension exists between us?"),
    # Forum Intelligence
    ("Forum", "yoong_family",            "Pete",
     "What is happening in Yoong Family?"),
    ("Forum", "pulsifi_leadership",      "Pete",
     "What is happening in Pulsifi Leadership?"),
    ("Forum", "tell_about_jh",           "Pete",
     "Tell me about JH"),
    ("Forum", "tell_about_jay",          "Pete",
     "Tell me about Jay"),
]


async def post_chat(client: httpx.AsyncClient, user_id: str,
                    message: str) -> Dict[str, Any]:
    t0 = time.time()
    try:
        r = await client.post(ENDPOINT, json={
            "user_id": user_id,
            "message": message,
            "include_journal": False,
            "include_history": False,
        }, timeout=180.0)
        body = r.json() if r.status_code == 200 else None
        return {
            "ok": r.status_code == 200,
            "status": r.status_code,
            "response": (body or {}).get("response", ""),
            "debug":    (body or {}).get("debug", {}),
            "session_id": (body or {}).get("session_id"),
            "elapsed_s": time.time() - t0,
            "error": None if r.status_code == 200 else r.text[:400],
        }
    except Exception as e:
        return {
            "ok": False, "status": None,
            "response": "", "debug": {}, "session_id": None,
            "elapsed_s": time.time() - t0,
            "error": f"{type(e).__name__}: {e}",
        }


async def fetch_latest_receipt(db, user_id: str,
                               after_ts: float) -> Optional[Dict[str, Any]]:
    # Receipts persist with `computed_at` — pull the latest one for this user
    # that was created after our request started.
    cutoff = after_ts
    cursor = db.mirror_chat_retrieval_receipts.find(
        {"user_id": user_id}
    ).sort("computed_at", -1).limit(3)
    async for r in cursor:
        ca = r.get("computed_at")
        try:
            ts = ca.timestamp() if hasattr(ca, "timestamp") else None
        except Exception:
            ts = None
        if ts is None or ts >= cutoff - 5.0:  # 5s slack for clock drift
            r["_id"] = str(r.get("_id"))
            return r
    return None


def grep_recent_log(after_ts: float, user_id: str) -> List[str]:
    """Pull [phase4-*] / [MIRROR_CHAT] lines from backend.err.log that
    mention this user_id since `after_ts`."""
    try:
        with open("/var/log/supervisor/backend.err.log", errors="ignore") as f:
            all_lines = f.readlines()
    except Exception:
        return []
    relevant: List[str] = []
    last_n = all_lines[-3000:]
    for line in last_n:
        if "[MIRROR_CHAT]" in line and (user_id in line or
                                        "[phase4-" in line or
                                        "[evidence-drawer-v2]" in line or
                                        "lens=" in line):
            relevant.append(line.strip())
    return relevant[-30:]   # last 30 mirror-chat log events


def score_response(response: str, receipt: Optional[Dict[str, Any]],
                   category: str, message: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "len_words": len(response.split()) if response else 0,
        "mentions_target_name":      False,
        "mentions_target_role":      False,
        "mentions_primary_domain":   False,
        "mentions_secondary_lens":   [],
        "mentions_founder_term":     [],
        "mentions_forum_name":       [],
        "category": category,
    }
    if not response:
        return out
    resp_lc = response.lower()

    env = (receipt or {}).get("intent_envelope") or {}
    rel = (receipt or {}).get("relationship_resolution") or {}
    primary    = env.get("primary_domain")
    secondaries = env.get("secondary_domains") or []
    matched    = (env.get("evidence") or {}).get("matched_phrases") or {}
    tgt_name   = rel.get("target_name") or rel.get("target_unresolved_name")
    tgt_role   = rel.get("role")

    if tgt_name:
        out["mentions_target_name"] = tgt_name.split()[0].lower() in resp_lc \
                                       if tgt_name else False
        out["resolved_target_name"] = tgt_name
    if tgt_role:
        out["mentions_target_role"] = (
            tgt_role.replace("_", " ").lower() in resp_lc
        )
        out["resolved_target_role"] = tgt_role
    if primary and primary != "general":
        out["mentions_primary_domain"] = primary.lower() in resp_lc
        out["primary_domain"] = primary
    if secondaries:
        out["resolved_secondaries"] = secondaries
        out["mentions_secondary_lens"] = [
            s for s in secondaries if s.lower() in resp_lc
        ]
    founder_terms = [
        "founder", "leadership", "pulsifi", "ceo", "startup", "company",
        "team", "operator", "board", "executive", "burnout",
    ]
    out["mentions_founder_term"] = [w for w in founder_terms if w in resp_lc]
    forum_names = ["yoong", "pulsifi leadership", "pulsifi"]
    out["mentions_forum_name"] = [
        w for w in forum_names if w in resp_lc and "founder" not in w
    ]
    out["matched_phrases_in_router"] = matched
    return out


async def main() -> int:
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"]]

    results: List[Dict[str, Any]] = []

    async with httpx.AsyncClient() as client:
        for i, (cat, key, user_label, msg) in enumerate(PROBES, 1):
            uid = USERS[user_label]
            t_req = time.time()
            print(f"\n[{i:>2}/{len(PROBES)}] {cat:13} | {user_label:5} | "
                  f"{key:<22} | {msg!r}", flush=True)
            live = await post_chat(client, uid, msg)
            time.sleep(1.0)  # let the receipt persist task finish
            receipt = await fetch_latest_receipt(db, uid, t_req)
            logs = grep_recent_log(t_req, uid)

            score = score_response(live.get("response", ""), receipt, cat, msg)

            # Distill receipt to lean payload to keep JSON compact.
            r_lean: Dict[str, Any] = {}
            if receipt:
                env = receipt.get("intent_envelope") or {}
                rel = receipt.get("relationship_resolution") or {}
                ft  = receipt.get("forum_topology_resolution") or {}
                p3  = receipt.get("relationship_orchestration_v1") or {}
                r_lean = {
                    "request_id": receipt.get("request_id"),
                    "shadow_mode": receipt.get("shadow_mode"),
                    "router_version": receipt.get("router_version"),
                    "routing_status": receipt.get("routing_status"),
                    "domain_selected": receipt.get("domain_selected"),
                    "frame_source": receipt.get("frame_source"),
                    "intent_envelope": {
                        "primary_domain":   env.get("primary_domain"),
                        "confidence":       env.get("confidence"),
                        "margin":           env.get("margin"),
                        "secondary_domains": env.get("secondary_domains"),
                        "frame_resolved":   env.get("frame_resolved"),
                        "target_resolved":  env.get("target_resolved"),
                        "relationship_relevant": env.get("relationship_relevant"),
                        "timeline_relevant":     env.get("timeline_relevant"),
                        "matched_phrases":  (env.get("evidence") or {}).get("matched_phrases"),
                    },
                    "relationship_resolution": rel,
                    "forum_topology_resolution": ft,
                    "p3_orchestration": {
                        "rule_bucket":   p3.get("rule_bucket"),
                        "framing_hint": p3.get("framing_hint"),
                        "domain_bias":  p3.get("domain_bias"),
                        "replanned_after_topology": p3.get(
                            "replanned_after_topology"
                        ),
                        "topology_role_type": p3.get("topology_role_type"),
                    } if p3 else None,
                    "target_resolution_source": receipt.get("target_resolution_source"),
                    "context_retrieved": receipt.get("context_retrieved"),
                    "mandatory_modules_invoked": receipt.get("mandatory_modules_invoked"),
                    "mandatory_modules_missing": receipt.get("mandatory_modules_missing"),
                    "retrieval_status": receipt.get("retrieval_status"),
                    "validation_status": receipt.get("validation_status"),
                }

            results.append({
                "probe_index": i,
                "category": cat,
                "intent_key": key,
                "user_label": user_label,
                "user_id": uid,
                "message": msg,
                "live": live,
                "receipt": r_lean,
                "log_lines": logs,
                "score": score,
            })
            # Print a quick verdict so we can monitor.
            iv2_block_lines = [l for l in logs if "phase4-intent-v2" in l]
            tv2_lines       = [l for l in logs if "phase4-timeline-v2" in l]
            fc_lines        = [l for l in logs if "phase4-founder-context" in l]
            pfs21_lines     = [l for l in logs if "phase4-PFS2.1" in l]
            _env = ((receipt or {}).get("intent_envelope") or {})
            _rel = ((receipt or {}).get("relationship_resolution") or {})
            print(f"   primary={_env.get('primary_domain', '∅') if receipt else 'NO_RECEIPT'} "
                  f"| target={(_rel.get('target_name') or _rel.get('target_unresolved_name')) if receipt else None} "
                  f"| iv2_block={'y' if iv2_block_lines else 'n'} "
                  f"| tv2={'y' if tv2_lines else 'n'} "
                  f"| founder={'y' if fc_lines else 'n'} "
                  f"| pfs21={'y' if pfs21_lines else 'n'} "
                  f"| resp_words={score['len_words']}")
            await asyncio.sleep(0.5)

    out_path = "/app/backend/audit_reports/INTELLIGENCE_UTILIZATION_PROBES.json"
    with open(out_path, "w") as f:
        json.dump({
            "generated_at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                              time.gmtime()),
            "probes": results,
        }, f, indent=2, default=str)
    print(f"\n[wrote] {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
