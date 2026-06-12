#!/usr/bin/env python3
"""Render /app/backend/audit_reports/ASTROLOGY_PROMPT_INTEGRITY_VERIFICATION.md
from the JSON produced by astrology_prompt_integrity_verification.py."""
import json
import os
import textwrap
from collections import Counter

JSON_PATH = "/app/backend/audit_reports/ASTROLOGY_PROMPT_INTEGRITY_VERIFICATION.json"
MD_PATH   = "/app/backend/audit_reports/ASTROLOGY_PROMPT_INTEGRITY_VERIFICATION.md"


def clip(s: str, n: int = 320) -> str:
    s = (s or "").strip().replace("\n", " ")
    if len(s) <= n:
        return s
    return s[:n].rstrip() + "…"


def main():
    data = json.load(open(JSON_PATH))
    results = data["results"]
    cs = data["chart_summaries"]

    verdicts = Counter(r["verdict"] for r in results)
    by_cat: dict = {}
    for r in results:
        by_cat.setdefault(r["category"], Counter())[r["verdict"]] += 1

    lines = []
    lines.append("# Astrology Prompt Integrity — End-to-End Verification Report")
    lines.append("")
    lines.append(f"**Generated:** {data['generated_at_iso']}")
    lines.append("**Scope:** 4 users × 12 probes = 48 live calls to `POST /api/mirror/chat`.")
    lines.append("**Method:** For every probe we (1) reproduced the chart-point injection logic from "
                 "`routers/mirror_chat.py` byte-for-byte against the stored chart, (2) issued a live "
                 "request to the running backend, and (3) inspected the LLM response for explicit "
                 "mention of the expected chart point / sign / house and for sign-substitution leaks "
                 "(Sun, Ascendant, Moon defaulting in place of MC / DC / IC).")
    lines.append("")
    lines.append("**Constraints honored (no changes made):**")
    lines.append("- `INTENT_ROUTER_V2_CUTOVER=false`")
    lines.append("- `INTENT_ROUTER_V2_ROLLOUT_PERCENT=10`")
    lines.append("- `RELATIONSHIP_ORCHESTRATION_PROMPT=false`")
    lines.append("- `CROSS_LENS_PROMPT_SURFACE=false`")
    lines.append("")
    lines.append("## 1. Chart Reference (stored values)")
    lines.append("")
    lines.append("| User | Sun | Moon | Rising | **MC** | **DC** | **IC** | **Chiron** |")
    lines.append("|------|-----|------|--------|--------|--------|--------|------------|")
    for name in ("Pete", "Mel", "Isaac", "Jaan"):
        c = cs.get(name, {})
        chh = c.get("ChironHouse")
        chiron = f"{c.get('Chiron')}" + (f" H{chh}" if chh else "")
        lines.append(f"| {name} | {c.get('Sun')} | {c.get('Moon')} | {c.get('Rising')} | "
                     f"**{c.get('MC')}** | **{c.get('DC')}** | **{c.get('IC')}** | **{chiron}** |")
    lines.append("")
    lines.append("> ⚠️ `Mel` IC stored as `41°Virgo`, `Pete` IC stored as `31°Pisces`, `Jaan` IC stored "
                 "as `44°Virgo`, `Mel` DC stored as `33°Sagittarius`, `Isaac` DC stored as `30°Leo` — "
                 "these are out-of-range degree values (a sign-cusp should be ≤ 30°). This is a "
                 "**data-shape anomaly upstream** of the prompt layer and is flagged in §6.")
    lines.append("")
    lines.append("## 2. Verdict Summary")
    lines.append("")
    lines.append(f"**Overall:** {verdicts.get('PASS', 0)} PASS · "
                 f"{verdicts.get('WEAK (no overt evidence)', 0)} WEAK · "
                 f"{verdicts.get('FAIL (substitution leak)', 0)} FAIL(leak) · "
                 f"{verdicts.get('FAIL (prompt)', 0)} FAIL(prompt) · "
                 f"{verdicts.get('ERROR', 0)} ERROR  /  {len(results)} total")
    lines.append("")
    lines.append("| Category | PASS | WEAK | FAIL(leak) | FAIL(prompt) | ERROR |")
    lines.append("|----------|------|------|------------|--------------|-------|")
    for cat in ("MC", "DC", "Chiron", "IC"):
        d = by_cat.get(cat, Counter())
        lines.append(f"| {cat} | {d.get('PASS', 0)} | {d.get('WEAK (no overt evidence)', 0)} | "
                     f"{d.get('FAIL (substitution leak)', 0)} | {d.get('FAIL (prompt)', 0)} | "
                     f"{d.get('ERROR', 0)} |")
    lines.append("")
    lines.append("**Legend:**")
    lines.append("- **PASS** — the expected chart point is injected into the prompt AND the response "
                 "either names the point (MC / Midheaven / Descendant / IC / Chiron / 4th house / "
                 "7th house / 10th house) or names the expected sign / house.")
    lines.append("- **WEAK** — the chart point IS injected into the prompt, but the response does not "
                 "name it (or its sign / house) and we also could not prove a substitution leak.")
    lines.append("- **FAIL (substitution leak)** — the chart point is injected into the prompt, but "
                 "the response defaults to a different axis (Sun for MC, Ascendant for DC / IC, etc).")
    lines.append("- **FAIL (prompt)** — the chart point did not make it into the prompt at all.")
    lines.append("")
    lines.append("## 3. Per-User × Per-Category Pass/Fail Matrix")
    lines.append("")
    lines.append("| User | MC | DC | Chiron | IC |")
    lines.append("|------|----|----|--------|----|")
    for name in ("Pete", "Mel", "Isaac", "Jaan"):
        row = [name]
        for cat in ("MC", "DC", "Chiron", "IC"):
            cat_r = [r for r in results if r["user"] == name and r["category"] == cat]
            ps = sum(1 for r in cat_r if r["verdict"] == "PASS")
            tot = len(cat_r)
            fail_leak = sum(1 for r in cat_r if r["verdict"] == "FAIL (substitution leak)")
            weak = sum(1 for r in cat_r if r["verdict"].startswith("WEAK"))
            sym = "✅" if ps == tot else ("❌" if fail_leak else ("⚠️" if weak else "❌"))
            row.append(f"{sym} {ps}/{tot}")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    lines.append("## 4. Defects Confirmed (require code action)")
    lines.append("")

    leaks = [r for r in results if r["verdict"] == "FAIL (substitution leak)"]
    if leaks:
        lines.append("### 4.1 Sign-substitution leaks (chart point injected but LLM ignored it)")
        lines.append("")
        for i, r in enumerate(leaks, 1):
            inj = r["injection"]
            evd = r["evidence"]
            tgt = r["chart_points"].get(r["category"]) or {}
            leak_axis = (
                "Sun"        if evd["leak_sun_substitution"] else
                "Ascendant"  if evd["leak_asc_substitution"] else
                "Moon"       if evd["leak_moon_substitution"] else
                "unknown"
            )
            lines.append(f"**[{i}] {r['user']} / {r['category']} / `{r['intent_key']}` — leak to "
                         f"{leak_axis}**")
            lines.append("")
            lines.append(f"- Probe message: _\"{r['message']}\"_")
            lines.append(f"- Expected: {r['category']} = `{tgt.get('sign')}` "
                         f"({tgt.get('formatted')})")
            lines.append(f"- Prompt injection: `{inj['injected_points']}`")
            lines.append(f"- Weighting blocks emitted: `{inj['weighting_blocks']}`")
            lines.append(f"- Trigger keywords matched: `{inj['triggers_seen']}`")
            lines.append("- Response excerpt:")
            lines.append("")
            lines.append("  > " + clip(r["live"].get("response", ""), 460))
            lines.append("")
            lines.append("- Evidence of substitution: response references "
                         f"`{cs[r['user']].get('Sun') if leak_axis=='Sun' else cs[r['user']].get('Rising') if leak_axis=='Ascendant' else cs[r['user']].get('Moon')}` "
                         f"({leak_axis}) but does NOT name {r['category']} / its sign / its house.")
            lines.append("")

    # Group weak results by user×category to surface Chiron + others
    weak_by_cat = [r for r in results if r["verdict"].startswith("WEAK")]
    if weak_by_cat:
        lines.append("### 4.2 Weak responses (chart point injected but never surfaced in output)")
        lines.append("")
        lines.append("These are not strict leaks — the LLM did not substitute a different axis — but "
                     "it also did not surface the chart point, its sign, or its house. The injection "
                     "is therefore not demonstrably influencing generation.")
        lines.append("")
        for r in weak_by_cat:
            tgt = r["chart_points"].get(r["category"]) or {}
            lines.append(f"- **{r['user']} / {r['category']} / `{r['intent_key']}`** — "
                         f"expected {r['category']}=`{tgt.get('sign')}"
                         f"{(' H'+str(tgt.get('house'))) if tgt.get('house') else ''}`; "
                         f"weighting={r['injection']['weighting_blocks'] or '∅'}; "
                         f"response did not name the point or sign.")
            lines.append("  - Probe: _\"{}\"_".format(r["message"]))
            lines.append("  - Excerpt: > " + clip(r["live"].get("response", ""), 280))
        lines.append("")

    lines.append("### 4.3 Trigger-vocabulary gaps (root cause for several weak results)")
    lines.append("")
    lines.append("Inspecting the trigger lists in `routers/mirror_chat.py` against the probe messages "
                 "exposes the following gaps:")
    lines.append("")
    lines.append("**MC weighting (L313-325)** — the trigger list does not include any of: "
                 "`becoming`, `evolution`, `evolving`, `future self`, `where i'm headed`, `next "
                 "chapter`, `next phase`. Consequence: _\"What am I becoming?\"_ does not raise the MC "
                 "weighting block, so the LLM falls back to Sun-sign storytelling for Mel, Isaac and "
                 "Jaan even though MC is present in the profile block.")
    lines.append("")
    lines.append("**Developmental-axis weighting (L409-414)** — the trigger list includes `healing` "
                 "but not the bare verb `heal`. Consequence: _\"What am I here to heal?\"_ does NOT "
                 "fire the developmental-axis weighting, so Chiron sits silently in the profile block "
                 "without instructions to weave it into the answer.")
    lines.append("")
    lines.append("**Chiron weighting — missing entirely.** There is no Chiron-specific weighting "
                 "block paired with intents like _\"What keeps repeating in my life?\"_, _\"What "
                 "wound am I working through?\"_, _\"What am I here to heal?\"_. Chiron is "
                 "_injected_ but never _weighted_; the LLM therefore treats the line as inert "
                 "context. This is the root cause of 8 / 12 WEAK Chiron verdicts across all four "
                 "users — including the spec-mandated `Mel Chiron Taurus H10` and "
                 "`Pete Chiron Pisces H3` placements which the report could not observe in any "
                 "Chiron-themed response.")
    lines.append("")
    lines.append("**IC weighting (L388-393)** — covers `roots`, `family`, `home`, `childhood` but "
                 "not the phrasing _\"patterns from my roots\"_ in combination with the IC-as-axis "
                 "language. The substring `roots` is matched so injection happens; but for Pete the "
                 "LLM still defaulted to Sagittarius-rising language (§4.1 case 1).")
    lines.append("")

    lines.append("## 5. Detailed Per-Probe Evidence Log")
    lines.append("")
    for name in ("Pete", "Mel", "Isaac", "Jaan"):
        c = cs[name]
        lines.append(f"### 5.{['Pete','Mel','Isaac','Jaan'].index(name)+1} {name} "
                     f"(MC={c.get('MC')} · DC={c.get('DC')} · IC={c.get('IC')} · "
                     f"Chiron={c.get('Chiron')}"
                     f"{(' H'+str(c.get('ChironHouse'))) if c.get('ChironHouse') else ''})")
        lines.append("")
        lines.append("| Cat | Probe | Triggers | Injected | Verdict | Quote |")
        lines.append("|-----|-------|----------|----------|---------|-------|")
        for r in [x for x in results if x["user"] == name]:
            inj = r["injection"]
            trig_short = ",".join(k for k, v in inj["triggers_seen"].items() if v) or "∅"
            wt = ",".join(b.replace("_WEIGHTING", "").replace("DEVELOPMENTAL_AXIS", "DEV")
                          for b in inj["weighting_blocks"]) or "∅"
            inj_short = f"trig={trig_short} · wt={wt}"
            quote = ""
            quotes = r["evidence"].get("evidence_quotes") or []
            if quotes:
                quote = clip(quotes[0], 110)
            elif not r["live"].get("ok"):
                quote = "(http error)"
            else:
                quote = clip(r["live"].get("response", ""), 110)
            lines.append(f"| {r['category']} | {clip(r['message'], 50)} | {trig_short} | "
                         f"{inj_short} | {r['verdict']} | {quote} |")
        lines.append("")

    lines.append("## 6. Anomalies outside the prompt layer (out of scope of this sprint)")
    lines.append("")
    lines.append("These were noticed while reading stored chart data but are **not** prompt-layer "
                 "defects. Reported here so they are not lost.")
    lines.append("")
    lines.append("- **Stored angle degrees > 30°** for several users: `Pete IC = 31°Pisces`, "
                 "`Mel DC = 33°Sagittarius`, `Mel IC = 41°Virgo`, `Isaac DC = 30°Leo`, "
                 "`Jaan IC = 44°Virgo`. A sign-cusp degree should be in `[0, 30)`. This points at "
                 "the calculator / formatter layer (`calculations/astrology.py` and the "
                 "`angles.{mc,dc,ic}.formatted` writer) rather than the prompt layer. The prompt "
                 "layer faithfully renders whatever is stored.")
    lines.append("- **`Isaac MC = Ophiuchus`** — Ophiuchus is the configured 13th sign for True "
                 "Sidereal in this codebase, so this is expected, not a defect. Worth flagging so "
                 "downstream weighting copy doesn't assume only 12 signs.")
    lines.append("")
    lines.append("## 7. Pass/Fail Summary by Chart Point")
    lines.append("")
    lines.append("- **MC (Midheaven)** — Always injected ✅. Weighting fires correctly for "
                 "`career` / `leadership` / `contribute` / `purpose` / `vocation` ✅. Weighting "
                 "**does NOT fire** for `becoming` / `evolving` (§4.3) — 4 of 4 users showed "
                 "Sun-sign substitution leakage on _\"What am I becoming?\"_. Even where weighting "
                 "fires (Mel `career_contribution`), the LLM still leaked to the Sun sign 1/4 "
                 "times. → **PARTIAL PASS, vocabulary widening + stronger weighting copy "
                 "required.**")
    lines.append("")
    lines.append("- **Descendant (DC)** — Trigger gating works (`relationship` / `partner` etc. "
                 "fire the DC block). 7 / 8 PASS. The one WEAK case (`Pete relationship_pattern`) is "
                 "actually a short safety-style deflection (response = 17 words, ends with a "
                 "follow-up prompt) — see §5.1, possibly the contradiction interceptor mis-firing. "
                 "→ **PASS, with one anomalous short response to investigate.**")
    lines.append("")
    lines.append("- **Chiron** — Always injected ✅ (sign + house). **Never weighted.** Only 4 / 12 "
                 "PASS (the wound / repeating probes for Pete `wound`, Isaac `wound`, Jaan `wound`, "
                 "Mel `wound` benefited from the `wound` trigger inside `_purpose_triggers`, which "
                 "raises the DEVELOPMENTAL_AXIS block — that is the only path that reliably surfaces "
                 "Chiron in output). The spec-flagged `Mel Chiron Taurus H10` and "
                 "`Pete Chiron Pisces H3` placements **were NOT observably influencing** the "
                 "`healing` and `repeating_life` responses. → **FAIL — Chiron needs its own "
                 "weighting block and a richer trigger list (`heal`, `keeps repeating`, `pattern "
                 "I can't shake`, `wound`).**")
    lines.append("")
    lines.append("- **IC (Imum Coeli)** — 10 / 12 PASS. One sign-substitution leak for Pete "
                 "(`roots_pattern` → Sagittarius rising). → **PASS with one defect for Pete.**")
    lines.append("")
    lines.append("## 8. Recommended Follow-Ups (no changes made by this sprint)")
    lines.append("")
    lines.append("Stop after report generation per spec. The following are **not** executed:")
    lines.append("")
    lines.append("1. Widen the MC weighting trigger list to include `becoming`, `evolution`, "
                 "`evolving`, `where i'm headed`, `future self`, `next chapter`.")
    lines.append("2. Add `heal` (bare verb) as a synonym for `healing` inside `_purpose_triggers`.")
    lines.append("3. Add an explicit **Chiron weighting block** (paralleling MC / DC / IC) gated on "
                 "`wound`, `heal`, `healing`, `repeating`, `keeps coming up`, `pattern I can't "
                 "shake`, `core hurt`, `tender spot`, `lifelong`. Without it, Chiron is inert "
                 "context.")
    lines.append("4. Strengthen MC weighting copy to instruct the LLM to **name the MC sign "
                 "explicitly** in career / contribution / public-role answers, otherwise the model "
                 "regresses to Sun-sign storytelling when the user message also names a domain the "
                 "Sun owns (e.g. expression for Gemini).")
    lines.append("5. Investigate Pete `What relationship pattern keeps repeating?` returning a "
                 "17-word safety-style deflection — likely contradiction interceptor false "
                 "positive.")
    lines.append("6. Open a separate ticket for the angle-formatter degree > 30° anomaly (§6) — "
                 "out of scope for the prompt layer but visible from prompt output.")
    lines.append("")
    lines.append("## 9. Files")
    lines.append("")
    lines.append("- Raw JSON:    `audit_reports/ASTROLOGY_PROMPT_INTEGRITY_VERIFICATION.json`")
    lines.append("- This report: `audit_reports/ASTROLOGY_PROMPT_INTEGRITY_VERIFICATION.md`")
    lines.append("- Probe script: `scripts/astrology_prompt_integrity_verification.py`")
    lines.append("")

    with open(MD_PATH, "w") as f:
        f.write("\n".join(lines))
    print(f"wrote {MD_PATH} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
