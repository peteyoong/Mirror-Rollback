"""
Regression test for /api/forums/{forum_id}/member-mappings after
Relationship Field V1.3 "Layered Convergence" rollout (Phases 1+2+3).
Verifies:
  A) Schema/contract preserved
  B) Layered Convergence behavior (de-dupe, convergence_note in field_paragraph)
  C) 21-45 Money Line rewrite
  D) Pete's mapping with 21-45 — full field dump
  E) Backend logs contain [LayeredConvergence] info lines
"""
import json
import os
import re
import subprocess
import time
from typing import Any, Dict, List, Optional

import requests

BASE_URL = "https://forum-mappings-hub.preview.emergentagent.com/api"
FORUM_ID = "69dda348de9cb1c83c0780fa"  # Yoong family forum
USER_ID = "697f0c6abf35c0528ff06954"   # Pete

REQUIRED_TOP_KEYS = {
    "member_id", "member_name", "headline", "description",
    "signals", "field", "patterns", "story",
    "what_works", "what_to_watch", "why_this_happens",
}

BANNED_21_45_WORDS = [
    "materialism",
    "power imbalance",
    "live wire around direction",
    "control dynamics",
]

EXPECTED_21_45_TRANSLATION = (
    "Together, you naturally start organizing resources, direction, and "
    "responsibility — this connection tends to move toward building "
    "something tangible"
)
OLD_21_45_TRANSLATION = (
    "Resources and responsibility become something you both feel strongly"
)
EXPECTED_21_45_HEADLINE = (
    "Resources, direction, and responsibility quickly become shared territory"
)


def banner(t: str) -> None:
    print("\n" + "=" * 78)
    print(t)
    print("=" * 78)


def truncate_backend_logs() -> None:
    """Truncate logs so we only see what happens during THIS test run."""
    for f in ("/var/log/supervisor/backend.out.log", "/var/log/supervisor/backend.err.log"):
        try:
            open(f, "w").close()
        except Exception:
            pass


def tail_backend_logs(pattern: str) -> List[str]:
    """Return all lines containing pattern from backend logs."""
    hits: List[str] = []
    for f in ("/var/log/supervisor/backend.out.log", "/var/log/supervisor/backend.err.log"):
        try:
            with open(f, "r") as fh:
                for line in fh:
                    if pattern in line:
                        hits.append(line.rstrip())
        except FileNotFoundError:
            pass
    return hits


def get_member_mappings() -> Dict[str, Any]:
    url = f"{BASE_URL}/forums/{FORUM_ID}/member-mappings"
    r = requests.get(url, params={"user_id": USER_ID}, timeout=120)
    print(f"GET {url}?user_id={USER_ID} -> {r.status_code}")
    r.raise_for_status()
    return r.json()


def check_schema(data: Dict[str, Any]) -> Dict[str, bool]:
    results: Dict[str, bool] = {}
    # A1 — 200 OK already checked by raise_for_status; check mappings list
    mappings = data.get("mappings")
    results["A1_200_and_mappings_list"] = isinstance(mappings, list)
    if not isinstance(mappings, list):
        return results

    print(f"  mappings count: {len(mappings)}")
    print(f"  members: {[m.get('member_name') for m in mappings]}")

    # A2 — required keys per mapping
    missing_per_mapping = []
    for m in mappings:
        missing = REQUIRED_TOP_KEYS - set(m.keys())
        if missing:
            missing_per_mapping.append(
                (m.get("member_name"), sorted(missing))
            )
    results["A2_required_keys_each_mapping"] = not missing_per_mapping
    if missing_per_mapping:
        print(f"  MISSING keys: {missing_per_mapping}")

    # A3 — field.version
    bad_version = []
    for m in mappings:
        v = (m.get("field") or {}).get("version")
        if v != "relationship-field-v1":
            bad_version.append((m.get("member_name"), v))
    results["A3_field_version"] = not bad_version
    if bad_version:
        print(f"  WRONG field.version: {bad_version}")

    # A4 — field.themes[*] doesn't expose dimension or source_lens
    leaked = []
    allowed_theme_keys = {"label", "what_lives_here", "friction_inside_it"}
    for m in mappings:
        themes = (m.get("field") or {}).get("themes") or []
        for i, t in enumerate(themes):
            if "dimension" in t or "source_lens" in t:
                leaked.append((m.get("member_name"), i, list(t.keys())))
            extra = set(t.keys()) - allowed_theme_keys
            if extra:
                # Not strictly failing but informational
                print(f"  NOTE: theme {i} of {m.get('member_name')} has extra keys: {extra}")
    results["A4_no_internal_theme_keys"] = not leaked
    if leaked:
        print(f"  LEAKED internal theme keys: {leaked}")
    return results


def check_convergence(data: Dict[str, Any]) -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    mappings = data.get("mappings") or []

    # B1 — no duplicate labels in field.themes (when >= 2 themes)
    dup_failures: List[Any] = []
    for m in mappings:
        themes = (m.get("field") or {}).get("themes") or []
        if len(themes) < 2:
            continue
        labels = [t.get("label") for t in themes]
        lowered = [(l or "").strip().lower() for l in labels]
        if len(set(lowered)) != len(lowered):
            dup_failures.append((m.get("member_name"), labels))
    results["B1_no_duplicate_theme_labels"] = not dup_failures
    if dup_failures:
        print(f"  DUPLICATE labels: {dup_failures}")
    else:
        print("  no duplicate theme labels in any mapping")

    # B2 — convergence sentence in field_paragraph (informational, log presence)
    convergence_pattern = re.compile(
        r"converge on the same pattern here\s*—\s*that's how clearly\s+.+\s+sits in this connection\.",
        re.IGNORECASE,
    )
    convergence_findings: List[Dict[str, Any]] = []
    paragraph_lengths: List[Any] = []
    paragraph_endings_ok = True
    for m in mappings:
        f = m.get("field") or {}
        fp = f.get("field_paragraph") or ""
        paragraph_lengths.append((m.get("member_name"), len(fp)))
        if not fp.rstrip().endswith("."):
            paragraph_endings_ok = False
            print(f"  NOTE: field_paragraph for {m.get('member_name')} doesn't end with period: ...{fp[-40:]!r}")
        has_sentence = bool(convergence_pattern.search(fp))
        convergence_findings.append({
            "member": m.get("member_name"),
            "has_convergence_sentence": has_sentence,
            "field_paragraph": fp,
        })
    results["B2_convergence_findings"] = convergence_findings
    # B3 — paragraph length 50-500
    length_ok = all(50 <= n <= 500 for _, n in paragraph_lengths)
    results["B2_paragraph_length_ok"] = length_ok
    results["B2_paragraph_ends_with_period"] = paragraph_endings_ok
    print(f"  paragraph lengths: {paragraph_lengths}")
    print(f"  paragraph endings ok: {paragraph_endings_ok}")
    return results


def collect_all_strings(obj: Any) -> List[str]:
    out: List[str] = []
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            out.extend(collect_all_strings(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(collect_all_strings(v))
    return out


def check_21_45(data: Dict[str, Any]) -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    mappings = data.get("mappings") or []

    # Find any mapping with 21-45 in human_design signals
    mapping_with_21_45: Optional[Dict[str, Any]] = None
    for m in mappings:
        hd = ((m.get("signals") or {}).get("human_design")) or []
        for entry in hd:
            if entry.get("channel") == "21-45":
                mapping_with_21_45 = m
                break
        if mapping_with_21_45:
            break

    if not mapping_with_21_45:
        print("  No mapping with 21-45 channel found. Skipping C1-C5.")
        results["C_skipped_no_21_45_mapping"] = True
        return results

    print(f"  Found 21-45 mapping with: {mapping_with_21_45.get('member_name')}")
    results["mapping_with_21_45_name"] = mapping_with_21_45.get("member_name")
    hd_signals = (mapping_with_21_45.get("signals") or {}).get("human_design") or []
    entry_21_45 = next(e for e in hd_signals if e.get("channel") == "21-45")
    results["21_45_entry"] = entry_21_45

    # C1 — exact translation match (case-sensitive)
    translation = entry_21_45.get("translation") or ""
    results["C1_translation_exact"] = translation == EXPECTED_21_45_TRANSLATION
    results["C1_old_translation_absent"] = OLD_21_45_TRANSLATION not in translation
    print(f"  C1 translation: {translation!r}")
    print(f"  C1 exact match: {results['C1_translation_exact']}, old phrase absent: {results['C1_old_translation_absent']}")

    # C2 — interpretation.headline (if present)
    interp = entry_21_45.get("interpretation")
    if isinstance(interp, dict):
        results["C2_interpretation_headline_ok"] = interp.get("headline") == EXPECTED_21_45_HEADLINE
        print(f"  C2 interpretation surfaced — headline: {interp.get('headline')!r}")
    else:
        results["C2_interpretation_surfaced"] = False
        print("  C2 interpretation dict NOT surfaced in hd_signals (this may be expected per review spec)")

    # C3 — search strings mentioning 21-45 in what_happens/tensions/gifts/what_works/what_to_watch
    patterns = mapping_with_21_45.get("patterns") or {}
    pools: Dict[str, Any] = {
        "what_happens": patterns.get("what_happens"),
        "tensions": patterns.get("tensions"),
        "gifts": patterns.get("gifts"),
        "what_works": mapping_with_21_45.get("what_works"),
        "what_to_watch": mapping_with_21_45.get("what_to_watch"),
    }
    # collect all strings & find those that "mention 21-45" — we use semantic match:
    # any string referencing money/resources/responsibility/direction in those buckets.
    # But per the review spec: "any string in what_happens/tensions/gifts/what_works/
    # what_to_watch that mentions 21-45" — since strings don't literally include
    # the channel id, we use the 21-45 catalog signature words: "resources", "direction",
    # "responsibility", "provision", "stewardship", or "Money Line".
    # 21-45 signature: provision / stewardship / who carries what / resources & direction /
    # actually build / ambition + follow-through / etc.
    signature = re.compile(
        r"\b(resources|direction|responsibilit|provision|stewardship|"
        r"money\s+line|carries\s+what|who\s+provides|who\s+decides|"
        r"actually\s+build|ambition|follow[- ]through|capital)\b",
        re.IGNORECASE,
    )
    candidate_strings: List[str] = []
    for k, v in pools.items():
        for s in collect_all_strings(v):
            if signature.search(s):
                candidate_strings.append(s)
    print(f"  C3 found {len(candidate_strings)} strings referencing 21-45 territory")
    for s in candidate_strings:
        print(f"     - {s}")
    has_building_word = any(re.search(r"\bbuild(ing)?\b", s, re.IGNORECASE) for s in candidate_strings)
    banned_hits = []
    for s in candidate_strings:
        for w in BANNED_21_45_WORDS:
            if w.lower() in s.lower():
                banned_hits.append((w, s))
    # also check globally across the mapping payload for banned words even if not in 21-45 strings
    all_mapping_strings = collect_all_strings(mapping_with_21_45)
    banned_global = []
    for s in all_mapping_strings:
        for w in BANNED_21_45_WORDS:
            if w.lower() in s.lower():
                banned_global.append((w, s))
    results["C3_has_building_word"] = has_building_word
    results["C3_no_banned_in_21_45_strings"] = not banned_hits
    results["C3_no_banned_anywhere_in_mapping"] = not banned_global
    results["C3_candidate_strings"] = candidate_strings
    if banned_global:
        print(f"  C3 BANNED words found in mapping: {banned_global}")
    else:
        print("  C3 no banned words anywhere in the 21-45 mapping")
    print(f"  C3 has building/build word in 21-45 strings: {has_building_word}")

    # C4 — field.activation
    activation = (mapping_with_21_45.get("field") or {}).get("activation") or ""
    has_rwc = "real-world coordination" in activation.lower()
    has_resources_direction = ("resources" in activation.lower() and "direction" in activation.lower())
    results["C4_activation_mentions_rwc_or_res_dir"] = has_rwc or has_resources_direction
    results["C4_activation_text"] = activation
    print(f"  C4 activation: {activation!r}")
    print(f"  C4 has real-world coordination: {has_rwc}, has resources+direction: {has_resources_direction}")

    # C5 — field.gift_of_this_connection
    gift = (mapping_with_21_45.get("field") or {}).get("gift_of_this_connection") or ""
    has_actually_build = "actually build" in gift.lower()
    has_ambition = "ambition" in gift.lower()
    has_follow_through = "follow-through" in gift.lower() or "follow through" in gift.lower()
    results["C5_gift_has_build_or_ambition_followthrough"] = (
        has_actually_build or (has_ambition and has_follow_through)
    )
    results["C5_gift_text"] = gift
    print(f"  C5 gift: {gift!r}")
    print(f"  C5 actually build: {has_actually_build}, ambition: {has_ambition}, follow-through: {has_follow_through}")
    return results


def dump_pete_21_45(data: Dict[str, Any]) -> Dict[str, Any]:
    """D — full field + 21-45 hd_signal entry dump."""
    mappings = data.get("mappings") or []
    if not mappings:
        return {"D_status": "no_mappings"}

    chosen: Optional[Dict[str, Any]] = None
    for m in mappings:
        hd = ((m.get("signals") or {}).get("human_design")) or []
        if any(e.get("channel") == "21-45" for e in hd):
            chosen = m
            break

    if chosen is None:
        # report and return mapping with most channels
        ranked = sorted(
            mappings,
            key=lambda m: len(((m.get("signals") or {}).get("human_design")) or []),
            reverse=True,
        )
        chosen = ranked[0]
        return {
            "D_status": "no_21_45_in_petes_mappings",
            "fallback_mapping_member": chosen.get("member_name"),
            "fallback_channels": [
                e.get("channel") for e in (((chosen.get("signals") or {}).get("human_design")) or [])
            ],
            "fallback_field": chosen.get("field"),
        }

    hd = (chosen.get("signals") or {}).get("human_design") or []
    entry = next(e for e in hd if e.get("channel") == "21-45")
    return {
        "D_status": "21_45_found",
        "member": chosen.get("member_name"),
        "field": chosen.get("field"),
        "hd_21_45_entry": entry,
    }


def main() -> int:
    banner("Layered Convergence Regression Test")
    truncate_backend_logs()
    time.sleep(0.5)

    try:
        data = get_member_mappings()
    except Exception as e:
        print(f"FATAL: request failed: {e}")
        return 2

    # Save raw response
    out_path = "/app/backend_test_layered_convergence_response.json"
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved raw response to {out_path}")

    banner("A) Schema / Contract")
    schema_results = check_schema(data)
    for k, v in schema_results.items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")

    banner("B) Layered Convergence Behavior")
    conv_results = check_convergence(data)
    for k, v in conv_results.items():
        if isinstance(v, bool):
            print(f"  {k}: {'PASS' if v else 'FAIL'}")

    banner("B2) Convergence sentence per mapping")
    for c in conv_results.get("B2_convergence_findings", []):
        marker = "YES" if c["has_convergence_sentence"] else "no "
        print(f"  [{marker}] {c['member']}: {c['field_paragraph']!r}")

    banner("C) 21-45 Money Line rewrite")
    c_results = check_21_45(data)
    for k, v in c_results.items():
        if isinstance(v, bool):
            print(f"  {k}: {'PASS' if v else 'FAIL'}")

    banner("D) Pete's mapping with 21-45")
    d_results = dump_pete_21_45(data)
    print(json.dumps(d_results, indent=2)[:6000])

    banner("E) Backend logs — [LayeredConvergence] info lines")
    # Trigger one more request (since logs may have been written then rotated)
    time.sleep(0.3)
    log_hits = tail_backend_logs("[LayeredConvergence]")
    print(f"  Found {len(log_hits)} [LayeredConvergence] lines")
    for line in log_hits[:20]:
        print("    " + line)

    banner("OVERALL SUMMARY")
    all_results = {**schema_results}
    # Only include boolean results from B and C
    for k, v in conv_results.items():
        if isinstance(v, bool):
            all_results[k] = v
    for k, v in c_results.items():
        if isinstance(v, bool):
            all_results[k] = v
    all_results["E_LayeredConvergence_log_lines_present"] = bool(log_hits)

    for k, v in all_results.items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")

    failed = [k for k, v in all_results.items() if not v]
    if failed:
        print(f"\nFAILED checks: {failed}")
        return 1
    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
