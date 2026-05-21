"""
Regression test for /api/forums/{forum_id}/member-mappings after the
Relationship Field signal-language polish.

User: Pete (697f0c6abf35c0528ff06954)
Forum: Yoong family (69dda348de9cb1c83c0780fa)
"""

import json
import os
import re
import sys
from typing import Any, Dict, List, Tuple

import requests

BASE = "https://forum-mappings-hub.preview.emergentagent.com/api"
USER_ID = "697f0c6abf35c0528ff06954"
FORUM_ID = "69dda348de9cb1c83c0780fa"


def walk_strings(obj: Any, path: str = "") -> List[Tuple[str, str]]:
    """Yield (json_path, string_value) for every string in the structure."""
    out = []
    if isinstance(obj, str):
        out.append((path, obj))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            out.extend(walk_strings(v, f"{path}.{k}" if path else k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(walk_strings(v, f"{path}[{i}]"))
    return out


def main():
    url = f"{BASE}/forums/{FORUM_ID}/member-mappings"
    params = {"user_id": USER_ID}
    print(f"GET {url}?user_id={USER_ID}")
    r = requests.get(url, params=params, timeout=90)
    print(f"Status: {r.status_code}")

    results: List[Tuple[str, bool, str]] = []

    # ---- CHECK 4 (schema/status first) ----
    if r.status_code != 200:
        print(r.text[:1000])
        results.append(("schema_status_200", False, f"got {r.status_code}"))
        print_report(results, None, None)
        sys.exit(1)
    data = r.json()
    results.append(("schema_status_200", True, "200 OK"))

    if "mappings" not in data or not isinstance(data["mappings"], list):
        results.append(("schema_top_level_mappings", False, "no mappings list"))
        print(json.dumps(data, indent=2)[:2000])
        print_report(results, None, None)
        sys.exit(1)
    mappings = data["mappings"]
    results.append(("schema_top_level_mappings", True, f"{len(mappings)} mappings"))

    required_per_mapping = ["member_user_id", "member_name", "headline", "description", "signals"]
    missing = []
    for m in mappings:
        for k in required_per_mapping:
            if k not in m:
                missing.append(f"{m.get('member_name','?')}.{k}")
    if missing:
        results.append(("schema_per_mapping_keys", False, f"missing: {missing[:5]}"))
    else:
        results.append(("schema_per_mapping_keys", True, f"all required keys present in {len(mappings)} mappings"))

    # Pick mapping to dump verbatim (prefer Mel)
    chosen = None
    for m in mappings:
        nm = (m.get("member_name") or "").lower()
        if "mel" in nm or "melissa" in nm:
            chosen = m
            break
    if chosen is None and mappings:
        chosen = mappings[0]

    # ---- CHECK 1: 21-45 Money Line sanitization ----
    full_text = json.dumps(data, ensure_ascii=False)
    has_2145 = "21-45" in full_text
    has_money_line = "The Money Line" in full_text
    print(f"\nFound '21-45' substring: {has_2145}; 'The Money Line': {has_money_line}")

    banned_old_phrase = "materialism, control, willpower for resources"
    banned_old_translation = "Resources, money, or control become a live wire between you"
    new_theme_expected = "resources, stewardship, responsibility, and the will to provide"
    new_translation_expected = "Resources and responsibility become something you both feel strongly"

    if has_2145 or has_money_line:
        if banned_old_phrase.lower() in full_text.lower():
            results.append(("check1_no_old_theme_phrase",
                            False,
                            f"OLD THEME PHRASE STILL PRESENT: '{banned_old_phrase}'"))
        else:
            results.append(("check1_no_old_theme_phrase", True,
                            "old 'materialism, control, willpower for resources' phrase absent"))

        if banned_old_translation.lower() in full_text.lower():
            results.append(("check1_no_old_translation",
                            False,
                            f"OLD TRANSLATION STILL PRESENT: '{banned_old_translation}'"))
        else:
            results.append(("check1_no_old_translation", True,
                            "old 'live wire' translation absent"))

        # Expected new strings present (only when 21-45 channel actually exists in mappings)
        # The new theme appears in PROMINENT_CHANNELS table; new translation appears in TRANSLATION_MAP signals layer.
        new_theme_present = new_theme_expected.lower() in full_text.lower()
        new_translation_present = new_translation_expected.lower() in full_text.lower()
        results.append(("check1_new_theme_present",
                        new_theme_present,
                        f"new theme '{new_theme_expected[:60]}...' present: {new_theme_present}"))
        results.append(("check1_new_translation_present",
                        new_translation_present,
                        f"new translation present: {new_translation_present}"))

        # Tech labels must still be there
        # If The Money Line / 21-45 appear, both should appear
        if has_money_line:
            results.append(("check1_money_line_label_present", True, "Channel name 'The Money Line' retained"))
        if has_2145:
            results.append(("check1_gate_21_45_present", True, "Gate technical label '21-45' retained"))
        # Check gates 21 and 45 individually
        gate_21 = re.search(r"\b21\b", full_text) is not None
        gate_45 = re.search(r"\b45\b", full_text) is not None
        results.append(("check1_gate_21_present", gate_21, "Gate 21 referenced"))
        results.append(("check1_gate_45_present", gate_45, "Gate 45 referenced"))
    else:
        results.append(("check1_21_45_not_present_in_this_user",
                        True,
                        "21-45/Money Line channel does NOT appear in this user's mappings — sanitization rules vacuously pass"))

    # ---- CHECK 2: banned shadow words in user-facing fields ----
    banned_words = ["materialism", "manipulation", "domination", "selfishness", "weakness", "failure"]
    banned_phrases = ["power imbalance"]
    standalone_control_pattern = re.compile(r",\s*control\s*,", re.IGNORECASE)

    target_paths_under_mapping = [
        ["signals", "human_design"],
        ["signals", "enneagram"],
        ["field", "themes"],          # within themes[*].what_lives_here
        ["field", "field_paragraph"],
        ["field", "activation"],
        ["field", "gift_of_this_connection"],
    ]

    banned_hits: List[Tuple[str, str, str]] = []  # (path, banned_word, snippet)
    control_hits: List[Tuple[str, str]] = []

    def get_nested(obj, path):
        cur = obj
        for p in path:
            if cur is None:
                return None
            if isinstance(cur, dict):
                cur = cur.get(p)
            else:
                return None
        return cur

    for mi, m in enumerate(mappings):
        for sub_path in target_paths_under_mapping:
            sub = get_nested(m, sub_path)
            if sub is None:
                continue
            for json_path, s in walk_strings(sub, ".".join(sub_path)):
                lower = s.lower()
                for w in banned_words:
                    if re.search(rf"\b{re.escape(w)}\b", lower):
                        banned_hits.append((f"mappings[{mi}].{json_path}", w, s[:160]))
                for ph in banned_phrases:
                    if ph in lower:
                        banned_hits.append((f"mappings[{mi}].{json_path}", ph, s[:160]))
                if standalone_control_pattern.search(s):
                    control_hits.append((f"mappings[{mi}].{json_path}", s[:160]))

    if banned_hits:
        results.append(("check2_no_banned_words",
                        False,
                        f"FOUND {len(banned_hits)} banned-word occurrences: {banned_hits[:5]}"))
    else:
        results.append(("check2_no_banned_words", True,
                        "No banned shadow words found in target fields"))

    if control_hits:
        results.append(("check2_no_standalone_control",
                        False,
                        f"Standalone ', control,' found {len(control_hits)} times: {control_hits[:3]}"))
    else:
        results.append(("check2_no_standalone_control", True,
                        "No standalone ', control,' pattern found"))

    # ---- CHECK 3: no raw arrow notation ----
    forbidden_substrings = [
        "You \u2192 ",
        " \u2192 you:",
        "You \u2192 Mel:",
        "What you need most from",
        "What Mel needs most from you",
    ]
    arrow_hits: List[Tuple[str, str, str]] = []

    for mi, m in enumerate(mappings):
        for json_path, s in walk_strings(m, f"mappings[{mi}]"):
            for fs in forbidden_substrings:
                if fs in s:
                    arrow_hits.append((json_path, fs, s[:160]))

    if arrow_hits:
        results.append(("check3_no_raw_arrows",
                        False,
                        f"FOUND {len(arrow_hits)} arrow-notation hits: {arrow_hits[:5]}"))
    else:
        results.append(("check3_no_raw_arrows", True,
                        "No raw arrow notation or 'What X needs most from Y' patterns found"))

    # Verify Mirror prose pattern present in enneagram signals (positive check)
    mirror_pattern = re.compile(r"With\s+(you|\w+),\s+(\w+|you)\s+find[s]?", re.IGNORECASE)
    reaches_pattern = re.compile(r"most reach(?:es)?\s+toward", re.IGNORECASE)
    enn_text_acc = []
    for m in mappings:
        enn = m.get("signals", {}).get("enneagram")
        if enn:
            for _, s in walk_strings(enn, ""):
                enn_text_acc.append(s)
    joined_enn = " || ".join(enn_text_acc)
    mirror_found = bool(mirror_pattern.search(joined_enn)) or bool(reaches_pattern.search(joined_enn))
    results.append(("check3_mirror_prose_present",
                    mirror_found or len(enn_text_acc) == 0,
                    f"Mirror prose ('With X, Y finds...' / 'most reaches toward') present in enneagram signals: {mirror_found}  (enn strings: {len(enn_text_acc)})"))

    # Final print
    print_report(results, chosen, mappings)

    # Exit code = 0 if no fail, 1 otherwise
    any_fail = any(not ok for _, ok, _ in results)
    sys.exit(1 if any_fail else 0)


def print_report(results, chosen_mapping, all_mappings):
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    for name, ok, detail in results:
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {name}: {detail}")
    if all_mappings is not None:
        print(f"\nTotal mappings returned: {len(all_mappings)}")
        names = [m.get("member_name") for m in all_mappings]
        print(f"Members: {names}")

    if chosen_mapping is not None:
        print("\n" + "=" * 80)
        print(f"FULL MAPPING DUMP (Pete -> {chosen_mapping.get('member_name')})")
        print("=" * 80)
        print(json.dumps(chosen_mapping, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
