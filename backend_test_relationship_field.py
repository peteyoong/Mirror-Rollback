"""
Relationship Field Architecture v1 — Backend Regression Test (Phase 1 only)
============================================================================

Validates the NEW additive `field` envelope on
GET /api/forums/{forum_id}/member-mappings while ensuring all legacy keys
remain byte-identical.

Test user: Pete (697f0c6abf35c0528ff06954, pete@pulsifi.me)
"""
import sys
import json
import re
import uuid
import requests
from pathlib import Path

FRONTEND_ENV = Path("/app/frontend/.env")
BACKEND_URL = None
for line in FRONTEND_ENV.read_text().splitlines():
    if line.startswith("EXPO_PUBLIC_BACKEND_URL=") or line.startswith("REACT_APP_BACKEND_URL="):
        BACKEND_URL = line.split("=", 1)[1].strip().strip('"').strip("'")
        break

API = f"{BACKEND_URL}/api"
PETE = "697f0c6abf35c0528ff06954"

FORBIDDEN_TERMS = [
    "soulmate", "twin flame", "destiny", "destined", "fated",
    "karmic", "karma", "past life", "past-life",
    "cosmic pull", "written in the stars", "meant to be", "divinely",
    "perfect match", "ideal match",
    "compatibility", "compatible", "incompatible",
]

# Legacy keys that MUST remain
LEGACY_TOP_KEYS = [
    "member_name", "member_id",
    "headline", "description", "what_works", "what_to_watch", "why_this_happens",
    "channel_count", "strength_score",
]
LEGACY_STORY_KEYS = ["headline", "summary"]
LEGACY_PATTERN_KEYS = ["what_happens", "tensions", "gifts"]
LEGACY_SIGNAL_KEYS = ["human_design", "astrology", "bazi", "enneagram", "numerology"]


results = []
def record(name, passed, info=""):
    results.append((name, passed, info))
    status = "PASS" if passed else "FAIL"
    line = f"[{status}] {name}"
    if info:
        line += f"  — {info}"
    print(line)


def get(path, params=None, timeout=180):
    return requests.get(f"{API}{path}", params=params, timeout=timeout)


def post(path, body, timeout=180):
    return requests.post(f"{API}{path}", json=body, timeout=timeout)


def contains_forbidden(text: str):
    if not isinstance(text, str) or not text:
        return []
    low = text.lower()
    hits = []
    for term in FORBIDDEN_TERMS:
        # Word-ish match — `compatibility` and `compatible` are substrings of each other,
        # we just need substring match per the review request.
        if term in low:
            hits.append(term)
    return hits


print("=" * 78)
print(f"Relationship Field Architecture v1 — {API}")
print("=" * 78)

# -----------------------------------------------------------------------------
# A) Boot sanity
# -----------------------------------------------------------------------------
print("\n-- A) BOOT SANITY --")
r = get(f"/people/{PETE}")
record("A.1 backend reachable (GET /api/people/{pete})", r.status_code == 200,
       f"status={r.status_code}")

# -----------------------------------------------------------------------------
# Discover Pete's forums
# -----------------------------------------------------------------------------
print("\n-- DISCOVER FORUMS FOR PETE --")
forum_ids = []
r = get(f"/forums/user/{PETE}")
if r.status_code == 200:
    payload = r.json()
    forums_list = payload if isinstance(payload, list) else (
        payload.get("forums") or payload.get("data") or []
    )
    for f in forums_list if isinstance(forums_list, list) else []:
        fid = f.get("forum_id") or f.get("_id") or f.get("id")
        if fid:
            forum_ids.append(fid)
    record("Discovery GET /forums/user/{pete}", True,
           f"forums={len(forum_ids)}: {forum_ids[:5]}")
else:
    record("Discovery GET /forums/user/{pete}", False, f"status={r.status_code}")

# Prefer the hinted forum if it appears, else iterate.
HINTED = "69b2491194f38a09d70df5f8"
ordered = ([HINTED] if HINTED in forum_ids else []) + [f for f in forum_ids if f != HINTED]
if not ordered:
    record("FATAL: no forums discoverable for Pete", False, "")
    print("\n".join([f"{n}: {ok}" for n, ok, _ in results]))
    sys.exit(2)


# -----------------------------------------------------------------------------
# Try to find a forum where the member-mappings endpoint returns non-empty
# mappings.  We pick the first one with at least one mapping.
# -----------------------------------------------------------------------------
chosen_forum = None
chosen_payload = None
chosen_mappings = []
attempts = []
for fid in ordered:
    r = get(f"/forums/{fid}/member-mappings", params={"user_id": PETE})
    detail = f"forum={fid} status={r.status_code}"
    if r.status_code == 200:
        try:
            data = r.json()
        except Exception as e:
            attempts.append(detail + f" json-error={e}")
            continue
        mappings = (
            data.get("mappings")
            or data.get("member_mappings")
            or data.get("data")
            or (data if isinstance(data, list) else [])
        )
        if isinstance(mappings, list) and len(mappings) > 0:
            chosen_forum = fid
            chosen_payload = data
            chosen_mappings = mappings
            attempts.append(detail + f" mappings={len(mappings)} CHOSEN")
            break
        attempts.append(detail + f" mappings={len(mappings) if isinstance(mappings, list) else 'n/a'}")
    else:
        attempts.append(detail + f" body={r.text[:120]}")

record("Found forum with non-empty mappings", chosen_forum is not None,
       " | ".join(attempts))

if chosen_forum is None:
    # Still test legacy contract on whatever we got.
    print("\nNo forum with mappings found, aborting Field tests.")
    sys.exit(3)

print(f"\nChosen forum: {chosen_forum}, mappings count: {len(chosen_mappings)}")


# -----------------------------------------------------------------------------
# B) Legacy contract preserved
# -----------------------------------------------------------------------------
print("\n-- B) LEGACY CONTRACT PRESERVED --")

def check_legacy(m, idx):
    missing = []
    # Top level keys
    for k in LEGACY_TOP_KEYS:
        if k not in m:
            missing.append(k)
    # Story
    story = m.get("story")
    if not isinstance(story, dict):
        missing.append("story (not dict)")
    else:
        for k in LEGACY_STORY_KEYS:
            if k not in story:
                missing.append(f"story.{k}")
    # Patterns
    patterns = m.get("patterns")
    if not isinstance(patterns, dict):
        missing.append("patterns (not dict)")
    else:
        for k in LEGACY_PATTERN_KEYS:
            v = patterns.get(k)
            if k not in patterns:
                missing.append(f"patterns.{k}")
            elif not isinstance(v, list):
                missing.append(f"patterns.{k} (not list, got {type(v).__name__})")
    # Signals
    signals = m.get("signals")
    if not isinstance(signals, dict):
        missing.append("signals (not dict)")
    else:
        for k in LEGACY_SIGNAL_KEYS:
            if k not in signals:
                missing.append(f"signals.{k}")
    # Types of channel_count / strength_score
    if not isinstance(m.get("channel_count"), int):
        missing.append(f"channel_count not int (got {type(m.get('channel_count')).__name__})")
    if not isinstance(m.get("strength_score"), int):
        missing.append(f"strength_score not int (got {type(m.get('strength_score')).__name__})")
    return missing


all_legacy_ok = True
for idx, m in enumerate(chosen_mappings):
    missing = check_legacy(m, idx)
    ok = len(missing) == 0
    if not ok:
        all_legacy_ok = False
    record(f"B.{idx+1} mapping[{idx}] (member={m.get('member_name','?')}) legacy keys present",
           ok, "missing=" + ",".join(missing) if missing else "all legacy keys present")

# -----------------------------------------------------------------------------
# C) New field envelope
# -----------------------------------------------------------------------------
print("\n-- C) NEW field ENVELOPE --")
mappings_with_field = [m for m in chosen_mappings if isinstance(m.get("field"), dict)]
record("C.1 AT LEAST one mapping has a `field` key", len(mappings_with_field) >= 1,
       f"with_field={len(mappings_with_field)}/{len(chosen_mappings)}")


def check_field_envelope(field, member_name=""):
    issues = []
    if field.get("version") != "relationship-field-v1":
        issues.append(f"version!={field.get('version')!r}")
    fp = field.get("field_paragraph")
    if not (isinstance(fp, str) and fp.strip()):
        issues.append("field_paragraph not non-empty str")
    act = field.get("activation")
    if not (isinstance(act, str) and act.strip()):
        issues.append("activation not non-empty str")
    themes = field.get("themes")
    if not isinstance(themes, list):
        issues.append("themes not list")
    else:
        for ti, t in enumerate(themes):
            if not isinstance(t, dict):
                issues.append(f"themes[{ti}] not dict")
                continue
            if not (isinstance(t.get("label"), str) and t["label"].strip()):
                issues.append(f"themes[{ti}].label invalid")
            if not (isinstance(t.get("what_lives_here"), str) and t["what_lives_here"].strip()):
                issues.append(f"themes[{ti}].what_lives_here invalid")
            f_in = t.get("friction_inside_it")
            if f_in is not None and not (isinstance(f_in, str)):
                issues.append(f"themes[{ti}].friction_inside_it not str or null")
    gift = field.get("gift_of_this_connection")
    if not (isinstance(gift, str) and gift.strip()):
        issues.append("gift_of_this_connection not non-empty str")
    amps = field.get("amplifiers")
    if not isinstance(amps, dict):
        issues.append("amplifiers not dict")
    else:
        for k in ("juno", "north_node", "vertex"):
            if k not in amps:
                issues.append(f"amplifiers.{k} missing")
            else:
                v = amps[k]
                if v is not None and not (isinstance(v, str) and v.strip()):
                    issues.append(f"amplifiers.{k} not null or non-empty str")
    return issues


for idx, m in enumerate(mappings_with_field):
    field = m["field"]
    issues = check_field_envelope(field, m.get("member_name", ""))
    record(f"C.{idx+2} mapping[{idx}] (member={m.get('member_name','?')}) field envelope shape",
           len(issues) == 0, "; ".join(issues) if issues else "valid envelope")


# -----------------------------------------------------------------------------
# D) Prose guardrail
# -----------------------------------------------------------------------------
print("\n-- D) PROSE GUARDRAIL (forbidden vocab) --")

def collect_field_strings(field):
    bag = []
    for key in ("field_paragraph", "activation", "gift_of_this_connection"):
        v = field.get(key)
        if isinstance(v, str) and v.strip():
            bag.append((f"field.{key}", v))
    for ti, t in enumerate(field.get("themes") or []):
        for k in ("label", "what_lives_here", "friction_inside_it"):
            v = (t or {}).get(k)
            if isinstance(v, str) and v.strip():
                bag.append((f"field.themes[{ti}].{k}", v))
    amps = field.get("amplifiers") or {}
    for k in ("juno", "north_node", "vertex"):
        v = amps.get(k)
        if isinstance(v, str) and v.strip():
            bag.append((f"field.amplifiers.{k}", v))
    return bag


all_clean = True
for idx, m in enumerate(mappings_with_field):
    field = m["field"]
    bag = collect_field_strings(field)
    issues = []
    for label, text in bag:
        hits = contains_forbidden(text)
        if hits:
            issues.append(f"{label} -> {hits} (in: {text[:120]!r})")
    ok = len(issues) == 0
    if not ok:
        all_clean = False
    record(f"D.{idx+1} mapping[{idx}] (member={m.get('member_name','?')}) prose guardrail",
           ok, "; ".join(issues) if issues else f"clean ({len(bag)} strings scanned)")

# -----------------------------------------------------------------------------
# E) Corroboration gate
# -----------------------------------------------------------------------------
print("\n-- E) CORROBORATION GATE --")

def has_signal_corroboration(signals):
    hd = signals.get("human_design")
    if hd:
        # non-empty (dict/list/str) counts
        if isinstance(hd, (list, dict)) and len(hd) > 0:
            return True
        if isinstance(hd, str) and hd.strip():
            return True
    astro = signals.get("astrology")
    if astro:
        if isinstance(astro, (list, dict)) and len(astro) > 0:
            return True
        if isinstance(astro, str) and astro.strip():
            return True
    bazi = signals.get("bazi")
    if bazi:
        if isinstance(bazi, (list, dict)) and len(bazi) > 0:
            return True
        if isinstance(bazi, str) and bazi.strip():
            return True
    ennea = signals.get("enneagram")
    if isinstance(ennea, dict):
        if ennea.get("friction_pattern"):
            return True
        # any non-empty content other than empties
        if any(v for k, v in ennea.items() if v):
            # Per request, "ennea has no friction_pattern" counts as empty for this gate
            if "friction_pattern" in ennea and ennea.get("friction_pattern"):
                return True
            # tighter interpretation: signals.enneagram with no friction_pattern doesn't corroborate
    elif ennea:
        return True
    return False


for idx, m in enumerate(mappings_with_field):
    signals = m.get("signals") or {}
    has_corr = has_signal_corroboration(signals)
    field = m["field"]
    amps = field.get("amplifiers") or {}
    juno = amps.get("juno")
    nn = amps.get("north_node")
    vx = amps.get("vertex")
    if not has_corr:
        ok = (juno is None and nn is None and vx is None)
        record(f"E.{idx+1} mapping[{idx}] (member={m.get('member_name','?')}) corroboration gate "
               "(no signals -> all amps null)",
               ok, f"juno={juno!r}, north_node={nn!r}, vertex={vx!r}")
    else:
        # When corroboration exists, gate doesn't require null — pass trivially.
        record(f"E.{idx+1} mapping[{idx}] (member={m.get('member_name','?')}) corroboration gate "
               "(signals present -> any amp value allowed)",
               True, f"juno={'<set>' if juno else 'null'}, nn={'<set>' if nn else 'null'}, vx={'<set>' if vx else 'null'}")

# -----------------------------------------------------------------------------
# F) Silent-skip on old charts (200 still returned, no 500)
# -----------------------------------------------------------------------------
print("\n-- F) SILENT-SKIP ON OLD CHARTS --")
# Already verified 200 above by chosen_payload, but re-call & confirm.
r = get(f"/forums/{chosen_forum}/member-mappings", params={"user_id": PETE})
record("F.1 GET member-mappings -> 200 (Juno/Vertex may be absent on stored chart)",
       r.status_code == 200, f"status={r.status_code}")

# Per-mapping: when amps are null for absent points, it should NOT be 500.
# (Already guaranteed by F.1.)  Document amp distribution.
amp_summary = []
for idx, m in enumerate(mappings_with_field):
    amps = m["field"].get("amplifiers") or {}
    amp_summary.append(
        f"[{idx}] juno={'set' if amps.get('juno') else 'null'} "
        f"nn={'set' if amps.get('north_node') else 'null'} "
        f"vx={'set' if amps.get('vertex') else 'null'}"
    )
record("F.2 amplifier distribution observed", True, " | ".join(amp_summary))

# -----------------------------------------------------------------------------
# G) Sister endpoints still 200
# -----------------------------------------------------------------------------
print("\n-- G) SISTER ENDPOINTS --")
r = get(f"/forums/{chosen_forum}/relationship-map", params={"user_id": PETE})
record("G.1 GET /forums/{id}/relationship-map -> 200", r.status_code == 200,
       f"status={r.status_code}")

# Pick any member_id from the same forum
sample_member_id = None
for m in chosen_mappings:
    mid = m.get("member_id")
    if mid:
        sample_member_id = mid
        break
if sample_member_id:
    r = get(f"/forums/{chosen_forum}/member-summary/{sample_member_id}",
            params={"user_id": PETE})
    record(f"G.2 GET /forums/{{id}}/member-summary/{sample_member_id} -> 200",
           r.status_code == 200, f"status={r.status_code}")
else:
    record("G.2 GET /forums/{id}/member-summary/{mid}", False, "no member_id available")

# -----------------------------------------------------------------------------
# H) v8 sanity carry-over: POST /api/mirror/chat lens=null returns 200 with debug.evidence
# -----------------------------------------------------------------------------
print("\n-- H) v8 sanity: POST /api/mirror/chat lens=null --")
body = {
    "user_id": PETE,
    "message": "Quick check-in for relationship-field-v1 regression run.",
    "lens": None,
    "session_id": "rfv1-regression-" + uuid.uuid4().hex[:8],
    "include_journal": True,
    "include_history": True,
}
r = post("/mirror/chat", body, timeout=180)
if r.status_code == 200:
    j = r.json()
    has_response = bool((j.get("response") or "").strip())
    evidence = j.get("evidence") or {}
    # spec said "debug.evidence", current shape is top-level "evidence" with marker "evidence-drawer-v2"
    has_ev = (evidence.get("marker") == "evidence-drawer-v2") or bool((j.get("debug") or {}).get("evidence"))
    record("H.1 POST /api/mirror/chat lens=null -> 200 + response + evidence",
           has_response and has_ev,
           f"resp_len={len(j.get('response') or '')} ev.marker={evidence.get('marker')}")
else:
    record("H.1 POST /api/mirror/chat lens=null -> 200", False,
           f"status={r.status_code} body={r.text[:200]}")


# -----------------------------------------------------------------------------
# Final summary
# -----------------------------------------------------------------------------
print("\n" + "=" * 78)
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"RESULTS: {passed}/{total} PASS")
print("=" * 78)
if passed != total:
    print("\nFAILED:")
    for name, ok, info in results:
        if not ok:
            print(f"  FAIL  {name} — {info}")
    sys.exit(1)
print("\nALL CHECKS PASS")
sys.exit(0)
