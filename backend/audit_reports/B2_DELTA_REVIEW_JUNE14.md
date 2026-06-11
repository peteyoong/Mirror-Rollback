# Mirror Chat V2 — Slice B2 Delta Review (June 14 window)

_Generated: 2026-06-11 (validation pass; window technically ends 2026-06-14)._

## 0. TL;DR

> **Recommendation: `CONDITIONAL_GO`**
>
> Do **not** flip `INTENT_ROUTER_V2_CUTOVER` yet.
>
> 1. The shadow telemetry observation window has not yet closed (ends `2026-06-14`).
> 2. A new **`Lens-jargon override`** review signal has been surfaced by the
>    expanded section-13 classifiers — operator review required before
>    advancing to the 10% stage.
> 3. **No new regressions** since the June 11 baseline (zero new FP examples,
>    zero new resolver-failure sub-buckets, zero new regression clusters,
>    zero distribution drift in unresolved-named sub-buckets).

## 1. Updated scorecard (REAL-only, frame-aware)

| Gate                                                | Value                                                | Threshold      | Status                |
|----------------------------------------------------|------------------------------------------------------|----------------|-----------------------|
| Golden-set top-1 (validated suites)                 | 100.00% on n=73                                      | ≥ 95%          | **PASS**              |
| Retrieval receipt coverage (PASS rate)              | 100.00%                                              | ≥ 95%          | **PASS**              |
| Target resolution (proposed_action path live)       | 24.49% unresolved_named (path wired)                 | ≥ 5%           | **PASS**              |
| False-positive relationship rate (frame-aware)      | 2.04% (1/49)                                         | ≤ 5%           | **PASS**              |
| Forum/member correctly-handled rate                 | 100.00% (resolver-failure cases = 0)                 | ≥ 90%          | **PASS**              |
| Shadow telemetry window complete                    | 13 receipts; span 18:37 → 19:27 (~50 min on June 11) | ≥ 3d to 06-14  | **FAIL** (expected)   |
| Manual review complete                              | report generated; awaiting operator sign-off         | operator       | PENDING_OPERATOR      |
| **§13.1 Domain drift rate**                         | 100.00% (1/1 ground-truth rows)                      | < 5%, none>10% | **INSUFFICIENT_SAMPLE** |
| **§13.2 Lens-jargon override errors**               | 4.08% (2 cases)                                      | < 3%           | **FAIL** ← review     |
| **§13.3 Relationship-context loss**                 | 0.00% (0 cases)                                      | < 2%           | **PASS**              |
| **§13.4 Wrong-target selection**                    | 0 cases                                              | = 0            | **PASS**              |
| **§13.5 Retrieval payload completeness**            | mandatory_modules mean=3.469 (baseline reference)    | no >25% shrink | **BASELINE_ONLY**     |
| **§13.6 Multi-lens coverage**                       | 100.00% (0 multi-lens prompts in this corpus)        | ≥ 90%          | **PASS**              |
| **§13.7 High-confidence wrong route**               | 1 case (Saturn return @ conf=1.0)                    | < 1%           | **WATCH**             |
| **§13.8 Founder/operator suite**                    | 0 founder-pattern queries in REAL window             | informational  | **WATCH**             |
| **§13.9 Couple ↔ Forum separation**                 | 0 bleed cases                                        | = 0            | **PASS**              |
| **§13.10 Decision explainability**                  | 0 non-explainable (0.00%)                            | informational  | **PASS**              |

## 2. Delta metrics (baseline → current)

| Category                                       | Baseline (2026-06-11 19:27 UTC) | Current (2026-06-11 19:42 UTC) | Δ        |
|-----------------------------------------------|----------------------------------|---------------------------------|----------|
| New false-positive relationship examples       | n/a                              | **0**                           | —        |
| New resolver-failure sub-buckets               | n/a                              | **0**                           | —        |
| Unresolved-named: `true_missing_person`        | 11                               | 11                              | 0        |
| Unresolved-named: `forum_only_member`          | 1                                | 1                               | 0        |
| New forum/member ambiguity examples            | n/a                              | **0**                           | —        |
| New regression clusters (≥3 of same kind)      | n/a                              | **0**                           | —        |
| Retrieval PASS rate                            | 100.00%                          | 100.00%                         | 0.00%    |
| Routing PASS rate                              | 95.92%                           | 95.92%                          | 0.00%    |
| Warning/FAIL routing receipt distribution      | PASS=47, WARNING=1, FAIL=1       | PASS=47, WARNING=1, FAIL=1      | identical|
| Top domains (REAL)                             | identity, growth, work, gen.     | identical                       | identical|

**Replay/live drift:** The 49 REAL messages cover the last 90 days of
`chat_history` / `forum_chat_messages` / `forum_mirror_chat_messages`.
Live shadow receipts (n=13) on June 11 are consistent with replay (no
new domain skew or resolver-failure clusters).

## 3. Representative examples per *new* regression bucket

### Lens-jargon override (FAIL, 2 cases)
- **`Tell me about my Saturn return`** — predicted = `identity` *(should weight `life_direction`; "Saturn return" is a timing/life-direction marker, not a personality trait).*
- **`What's my 7th house about?`** — predicted = `relationship` *(auto-routed without any relational keyword; should retain context-neutrality or weight identity until a partner is named).*

> Both are real **lexicon weighting** issues, not router bugs. Fix in
> B3 hardening (post-cutover): downweight lens-jargon-only triggers
> when no contextual cue accompanies them.

### High-confidence wrong route (WATCH, 1 case)
- **`Tell me about my Saturn return`** — `confidence=1.00`, predicted=`identity`, expected=`life_direction`. **Same root cause** as §13.2 above. Not an independent regression.

### Domain drift (INSUFFICIENT_SAMPLE)
- Only **1** ground-truth row in this corpus (the Saturn-return prompt). Not enough signal to gate cutover on overall drift rate. Live shadow window will populate this; the delta-detector will compare across runs.

## 4. Recommendation

**`CONDITIONAL_GO`** — with two open conditions:

1. **Shadow telemetry window must close** at `2026-06-14`. Today's run is
   the validation/dry-run; a final refresh after the window closes is
   required.
2. **Operator must review the lens-jargon override FAIL** above.
   - Option A: accept it (the issue is lexicon weighting, not router
     correctness; B3 hardening will fix it) → proceed to 10% rollout.
   - Option B: hold cutover until B3 ships the lexicon fix.

## 5. Phased rollout governance (per operator spec)

After the delta review is signed off:

- **Stage 1 — 10%**: enable `INTENT_ROUTER_V2_CUTOVER`, route 10% of
  traffic, collect telemetry for the observation window, deliver:
  - routing accuracy, retrieval PASS rate, FP-rel rate
  - forum/member metrics, unresolved-target metrics
  - section-13 review-signal deltas
  - representative failures.
  - **Await operator approval before advancing.**
- **Stage 2 — 50%**: repeat package; compare against 10% baseline.
  - **Await operator approval before advancing.**
- **Stage 3 — 100%**: final rollout; post-cutover health report after
  the observation window.

### Automatic halt criteria (between stages)

Any of the following will automatically halt progression and require
operator review:

- Retrieval PASS rate **< 97%**
- False-positive relationship rate **> 5%**
- Any **new resolver-failure sub-bucket** in live telemetry
- Forum/member correctly-handled rate **< 90%**
- Any **unexpected rise** in `target_unresolved` rate
- Any **regression cluster** (≥3 cases of the same kind) not represented
  in the golden sets
- Any of the section-13 review-signal gates flipping FAIL since the
  prior stage (domain drift, lens-jargon override, relationship-context
  loss, wrong-target selection, multi-lens coverage, high-confidence
  wrong route, couple↔forum bleed, payload >25% shrinkage).

**Sequence:**
`Delta Review → GO decision → 10% → review → 50% → review → 100%`

No automatic advancement between rollout stages.

---

## How to refresh this report

```bash
# Refresh telemetry → readiness scorecard → delta vs baseline
python /app/backend/tools/b2_replay_runner.py
python /app/backend/tools/b2_readiness_report.py --baseline

# Outputs:
#   /app/backend/audit_reports/B2_READINESS_REPORT.md (sections 1–14)
#   /app/backend/audit_reports/B2_READINESS_REPORT.json (machine-readable)
#   /app/backend/audit_reports/B2_REPLAY_RESULTS.json
#   /app/backend/audit_reports/B2_REPLAY_SAMPLES.md
```

Baseline artifacts (frozen 2026-06-11):
- `audit_reports/B2_READINESS_REPORT.baseline.json`
- `audit_reports/B2_REPLAY_RESULTS.baseline.json`
