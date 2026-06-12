#!/usr/bin/env python3
"""
P0 Intelligence Activation Follow-up — Verification Probe Suite.

Runs the 6 probes from Task 3 against the live backend, captures the
V2 receipt + response per probe, and writes JSON for the markdown
renderer.  Read-only.  No mutations.
"""
import asyncio, json, os, sys, time
from typing import Any, Dict, List, Tuple
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()
BACKEND = "http://localhost:8001"
ENDPOINT = f"{BACKEND}/api/mirror/chat"
USERS = {"Pete": "697f0c6abf35c0528ff06954"}

PROBES: List[Tuple[str, str, str]] = [
    # Relationship
    ("Relationship", "us_tension",
     "What tension exists between us?"),
    ("Relationship", "we_learning",
     "What are we learning together?"),
    # Founder
    ("Founder", "pulsifi_struggling",
     "What is Pulsifi struggling to see?"),
    ("Founder", "leadership_team_tension",
     "What tension exists inside the leadership team?"),
    # Forum
    ("Forum", "yoong_family",
     "What is happening in Yoong Family?"),
    ("Forum", "pulsifi_leadership_emerging",
     "What is emerging in Pulsifi Leadership?"),
]


async def post_chat(client, uid, msg):
    t0 = time.time()
    try:
        r = await client.post(ENDPOINT, json={
            "user_id": uid, "message": msg,
            "include_journal": False, "include_history": False,
        }, timeout=180.0)
        ok = r.status_code == 200
        body = r.json() if ok else None
        return {"ok": ok, "status": r.status_code,
                "response": (body or {}).get("response", ""),
                "elapsed_s": time.time() - t0,
                "error": None if ok else r.text[:300]}
    except Exception as e:
        return {"ok": False, "status": None, "response": "",
                "elapsed_s": time.time() - t0,
                "error": f"{type(e).__name__}: {e}"}


async def fetch_receipt(db, uid, after_ts):
    cursor = db.mirror_chat_retrieval_receipts.find(
        {"user_id": uid}).sort("computed_at", -1).limit(2)
    async for r in cursor:
        ca = r.get("computed_at")
        try:
            ts = ca.timestamp() if hasattr(ca, "timestamp") else None
        except Exception:
            ts = None
        if ts is None or ts >= after_ts - 5.0:
            r["_id"] = str(r.get("_id"))
            return r
    return None


def grep_logs(after_ts, uid):
    try:
        with open("/var/log/supervisor/backend.err.log", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return []
    relevant = []
    for line in lines[-3000:]:
        if "[MIRROR_CHAT]" in line and (uid in line or
                                        "phase4-" in line or
                                        "[evidence-drawer-v2]" in line):
            relevant.append(line.strip())
    return relevant[-25:]


async def main():
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"]]
    results = []
    async with httpx.AsyncClient() as client:
        for i, (cat, key, msg) in enumerate(PROBES, 1):
            uid = USERS["Pete"]
            t = time.time()
            print(f"[{i}/{len(PROBES)}] {cat:13} | {key:<28} | {msg!r}",
                  flush=True)
            live = await post_chat(client, uid, msg)
            time.sleep(1.0)
            rec = await fetch_receipt(db, uid, t)
            logs = grep_logs(t, uid)
            r_lean = {}
            if rec:
                env = rec.get("intent_envelope") or {}
                rel = rec.get("relationship_resolution") or {}
                r_lean = {
                    "request_id": rec.get("request_id"),
                    "shadow_mode": rec.get("shadow_mode"),
                    "intent_envelope": {
                        "primary_domain":        env.get("primary_domain"),
                        "confidence":            env.get("confidence"),
                        "relationship_relevant": env.get("relationship_relevant"),
                        "target_resolved":       env.get("target_resolved"),
                        "matched_phrases":
                            (env.get("evidence") or {}).get("matched_phrases"),
                    },
                    "relationship_resolution": {
                        "target":             rel.get("target"),
                        "target_name":        rel.get("target_name"),
                        "role":               rel.get("role"),
                        "forum_id":           rel.get("forum_id"),
                        "forum_name":         rel.get("forum_name"),
                        "resolution_source":  rel.get("resolution_source"),
                        "spouse_auto_bind":   rel.get("spouse_auto_bind"),
                        "lexicon_match":      rel.get("lexicon_match"),
                        "company_phrase_hits": rel.get("company_phrase_hits"),
                        "topology_role_found": rel.get("topology_role_found"),
                        "topology_role_type": rel.get("topology_role_type"),
                    },
                }
            results.append({
                "i": i, "category": cat, "intent_key": key,
                "message": msg, "live": live, "receipt": r_lean,
                "log_lines": logs,
            })
            await asyncio.sleep(0.4)

    out = "/app/backend/audit_reports/INTELLIGENCE_ROUTING_VERIFICATION.json"
    with open(out, "w") as f:
        json.dump({
            "generated_at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                              time.gmtime()),
            "probes": results,
        }, f, indent=2, default=str)
    print(f"wrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
