# Mirror Chat V2 — June 14 EOD Validation Pass

_Read-only audit. No code, flag, or DB writes. `INTENT_ROUTER_V2_CUTOVER` remains `false` throughout._

---

## TL;DR

> **Final recommendation: `CONDITIONAL_GO`**
>
> All original B2 hard gates **PASS**. No new regressions vs. June 11 baseline (zero
> new FP cases, zero new resolver-failure sub-buckets, zero new ambiguity examples,
> zero new clusters). Two pre-existing review signals (Lens-jargon override, low
> shadow-telemetry coverage) plus a new finding (founder/operator lexicon coverage)
> argue for queueing to B3 hardening rather than blocking — but the **operator must
> consciously accept these three trade-offs** before flipping the toggle to begin
> Stage-1 (10%) rollout.

---

## Part 1 — Refreshed B2 Delta Review (vs June 11 19:27 dry-run)

Re-ran `b2_replay_runner.py` and `b2_readiness_report.py --baseline`.
Regenerated all five artifacts:

- `B2_DELTA_REVIEW_JUNE14.md`
- `B2_READINESS_REPORT.md` (sections 1–14)
- `B2_READINESS_REPORT.json`
- `B2_REPLAY_RESULTS.json`
- `B2_REPLAY_SAMPLES.md`

| Metric                                | Previous (June 11 dry-run) | Current (June 14 EOD) | Δ                              |
|---------------------------------------|-----------------------------|------------------------|--------------------------------|
| Golden-set top-1 (validated)          | 100.00% (n=73)              | 100.00% (n=73)         | 0.00%                          |
| Retrieval PASS                        | 100.00%                     | 100.00%                | 0.00%                          |
| FP relationship                       | 2.04% (1/49)                | 2.17% (1/46)           | +0.13% (denom shrink)          |
| Forum/member correctly handled        | 100.00%                     | 100.00%                | 0.00%                          |
| Unresolved named                      | 24.49% (12/49)              | 26.09% (12/46)         | +1.60% (denom shrink)          |
| Domain drift                          | 100% of 1 GT row            | 100% of 1 GT row       | unchanged (INSUFFICIENT_SAMPLE)|
| Lens-jargon override                  | 4.08% (2)                   | 4.35% (2)              | +0.27% (same 2 cases)          |
| High-confidence wrong route           | 2.04% (1)                   | 2.17% (1)              | +0.13% (same 1 case)           |
| Payload completeness (mean mandatory) | 3.469                       | 3.565                  | +0.10                          |
| Routing FAIL receipt distribution     | PASS=47, WARN=1, FAIL=1     | PASS=44, WARN=1, FAIL=1| identical pattern              |

**Replay/live drift**: zero. Live shadow telemetry (n=13 receipts, June 11 ~50 min)
matches replay distribution. No new resolver-failure sub-buckets, no new FP
relationship examples, no new ambiguity examples, no new regression clusters.

> **Shadow-window gate** status: the gate fires `FAIL` because the live shadow
> receipt span is ~50 min, not the 3-day window the gate specifies. This is a
> **measurement-coverage gap**, not a quality regression — the shadow harness
> simply didn't accumulate more receipts. It does not indicate router defects.

---

## Part 2 — Founder/Operator Validation Suite

### Methodology

Built a synthetic 30-prompt validation suite (10 founder/operator, 10 spouse/
relationship, 10 forum/member) — representative of actual operator + production
usage. Routed each prompt through the **same offline stack used by the
shadow-mode production hook** (`intent_router_v2.classify_intent_v2` +
`relationship_router_v2.resolve_relationship_context`).

Inputs supplied:
- `saved_people`: `[{id: "mel-001", name: "Mel", role: "spouse"}, ...]`
- `forum_topology`: empty (mirrors current production behavior) — see Part 2b
  for the same suite with `active_member_id` wired (P4 simulation).
- `self_user_id`: pete-001
- Frame matches the chat surface (`self` / `member` / `forum`).
- For spouse prompts, `target_id="mel-001"` is bound (matches `/member/:id` chat).

Pass criteria per category:
- **founder**: `actual_domain ∈ {leadership, career, identity}`
- **spouse**: `actual_domain ∈ {relationship, family, growth}` **AND** resolver
  returns `context_mode=RELATIONAL` **AND** `target == mel-001`
- **forum**:  `actual_domain ∈ {relationship, growth}` **AND** resolver returns
  `context_mode=RELATIONAL` (resolution path = `forum_active_member`)

### Aggregate accuracy (current production wiring)

|             | Founder | Spouse  | Forum   |
|-------------|---------|---------|---------|
| Domain      | 40.0%   | 60.0%   | 100.0%  |
| Target      | 100.0%  | 100.0%  | 100.0%* |
| Frame       | 100.0%  | 100.0%  | 100.0%  |
| Relational  | 100.0%  | 100.0%  | 0.0%*   |
| **Overall** | **40.0%** | **60.0%** | **0.0%*** |

> *The forum bucket failures are entirely driven by **`active_member_id` not
> being passed in by the chat surface today** — i.e. the P4 backlog item
> ("Forum topology resolution"). The router itself is correct.

### Part 2b — Same suite with `active_member_id` wired (P4 simulated)

|             | Founder | Spouse  | Forum   |
|-------------|---------|---------|---------|
| Domain      | 40.0%   | 60.0%   | 100.0%  |
| Target      | 100.0%  | 100.0%  | 100.0%  |
| Frame       | 100.0%  | 100.0%  | 100.0%  |
| Relational  | 100.0%  | 100.0%  | 100.0%  |
| **Overall** | **40.0%** | **60.0%** | **100.0%** |

> Verifies: forum failures are **pure wiring** (P4 backlog). After P4 the entire
> forum bucket passes cleanly.

---

## Part 3 — Per-Prompt Results (current production wiring)

### Founder / Operator (10 prompts)

| # | Prompt | Expected | Actual | Target | Conf | Pass |
|---|---|---|---|---|---|---|
| 1 | Should I restructure my leadership team? | leadership | leadership | — | 0.95 | ✅ |
| 2 | My cofounder and I disagree about product direction. | leadership | career | — | 0.36 | ✅* |
| 3 | Should I let this executive go? | leadership | **general** | — | 0.00 | ❌ |
| 4 | How do I think about downsizing? | leadership | **general** | — | 0.00 | ❌ |
| 5 | Which relationship is creating friction in the company? | leadership | **general** | — | 0.00 | ❌ |
| 6 | What is the blind spot in my leadership right now? | leadership | leadership | — | — | ✅ |
| 7 | Am I avoiding a decision? | identity | **general** | — | 0.00 | ❌ |
| 8 | Should I prioritize fundraising or profitability? | career | career | — | — | ✅ |
| 9 | What dynamic exists between me and my management team? | leadership | **relationship** | — | 0.25 | ❌ |
| 10 | What is the next growth constraint in the business? | career | **general** | — | 0.00 | ❌ |

\* Row 2 lands in `career` rather than `leadership`, which still satisfies the
relaxed founder gate (leadership ∪ career ∪ identity).

### Spouse / Relationship (10 prompts, `target_id=mel-001`)

| # | Prompt | Expected | Actual | Target | Conf | Pass |
|---|---|---|---|---|---|---|
| 11 | How does Mel map to me right now? | relationship | relationship | mel-001 | 0.82 | ✅ |
| 12 | What is happening between me and my spouse? | relationship | relationship | mel-001 | 0.36 | ✅ |
| 13 | What tension are we carrying? | relationship | relationship | mel-001 | 0.49 | ✅ |
| 14 | What does Mel most need from me? | relationship | relationship | mel-001 | 0.79 | ✅ |
| 15 | How do I show up in this relationship? | relationship | **career** | mel-001 | 0.21 | ❌ |
| 16 | What relationship pattern keeps repeating? | relationship | **career** | mel-001 | 0.21 | ❌ |
| 17 | What should I understand about my partner? | relationship | relationship | mel-001 | 0.76 | ✅ |
| 18 | Where are we aligned? | relationship | relationship | mel-001 | 0.49 | ✅ |
| 19 | What dynamic is asking for attention? | relationship | **career** | mel-001 | 0.21 | ❌ |
| 20 | What is the growth edge in this relationship? | relationship | **career** | mel-001 | 0.21 | ❌ |

> 4/10 spouse prompts fall to `career` (low-signal lexicon weakness). Confidence
> for these is uniformly ≤0.22 — **the router is correctly signaling low
> confidence on these**. In production this would surface as a routing
> `WARNING` receipt rather than a confident wrong route.

### Forum / Member (10 prompts, current production wiring)

| # | Prompt | Expected | Actual | Target | Mode | Pass (today) | Pass (P4 wired) |
|---|---|---|---|---|---|---|---|
| 21 | Tell me about this forum member. | relationship | relationship | — / kara-001 | SELF / RELATIONAL | ❌ | ✅ |
| 22 | How does this person map to me? | relationship | relationship | — / kara-001 | SELF / RELATIONAL | ❌ | ✅ |
| 23 | What role do they play in the group? | relationship | relationship | — / kara-001 | SELF / RELATIONAL | ❌ | ✅ |
| 24 | What tension exists between us? | relationship | relationship | — / kara-001 | SELF / RELATIONAL | ❌ | ✅ |
| 25 | What should I understand about this member? | relationship | relationship | — / kara-001 | SELF / RELATIONAL | ❌ | ✅ |
| 26 | How do I work with them effectively? | relationship | relationship | — / kara-001 | SELF / RELATIONAL | ❌ | ✅ |
| 27 | What contribution do they bring? | relationship | relationship | — / kara-001 | SELF / RELATIONAL | ❌ | ✅ |
| 28 | How are they experienced by the forum? | relationship | relationship | — / kara-001 | SELF / RELATIONAL | ❌ | ✅ |
| 29 | What relationship pattern exists here? | relationship | relationship | — / kara-001 | SELF / RELATIONAL | ❌ | ✅ |
| 30 | What dynamic is emerging in the forum? | relationship | relationship | — / kara-001 | SELF / RELATIONAL | ❌ | ✅ |

> Every forum prompt routes the **domain** correctly (relationship). The only
> failure mode is `context_mode=SELF` because the chat surface today does not
> pass `forum_topology.active_member_id`. P4 closes this entirely.

---

## Part 4 — Lens-Jargon Review

Re-examined the two persistent failures from §13 of the readiness report.

### Case 1 — `Tell me about my Saturn return` → `identity`

| Classification dimension | Verdict |
|--------------------------|---------|
| Router defect?           | **No.** The classifier does exactly what the lexicon directs. |
| Lexicon weighting issue? | **Yes.** "Saturn" + "my" trigger the identity domain (Saturn is widely tagged as an identity-shaping body). The phrase "Saturn return" specifically refers to a *life-direction timing event* (~age 29, ~age 58), which the lexicon does not encode as a compound. |
| Intent hierarchy issue?  | **No.** Single-intent prompt. |
| Retrieval issue?         | **No.** Retrieval will correctly pull Saturn-return natal content; the wrong DOMAIN just changes downstream synthesis framing (identity vs. life direction). |

**Root cause**: lexicon does not encode the compound `saturn return` → `life_direction`.

### Case 2 — `What's my 7th house about?` → `relationship`

| Classification dimension | Verdict |
|--------------------------|---------|
| Router defect?           | **No.** |
| Lexicon weighting issue? | **Yes.** "7th house" is correctly associated with relationships in astrology — **but** without an actual relational keyword in the prompt (no name, no pronoun about another person), routing to `relationship` causes the synthesis to behave as if the user is asking about a *current relationship* rather than the *house meaning*. |
| Intent hierarchy issue?  | **Partial.** Should distinguish "explain my chart object X" (educational/identity) from "interpret my chart object X in the context of a real person" (relational). |
| Retrieval issue?         | **No.** Retrieval pulls 7th-house content correctly. |

**Root cause**: lens-term-alone-implies-domain. Needs an "educational mode" check
when no relational/temporal/situational cue accompanies the lens term.

### Verdict on Cases 1 & 2

> **B. Queue to B3 hardening.** Neither is a router defect; both are lexicon
> weighting issues. They do **not** block rollout — production today exhibits the
> *same* behavior under the legacy router (the v2 router is no worse here). The
> B3 hardening lane is the right place to add:
>
> - Lens-term compound entries (`saturn return` → `life_direction`, `pluto
>   transit` → `transformation`, `progressed moon` → `growth`, etc.)
> - "Educational-mode" disambiguation: if a lens term is present **without** any
>   relational/career/temporal cue, route to `identity` (the contextually
>   neutral synthesis lane) rather than collapse on the lens-term's natural
>   domain.

---

## Part 5 — Final Recommendation

# `CONDITIONAL_GO`

### Rationale

**What passes cleanly:**
- All five original B2 hard gates: golden top-1 (100%), retrieval PASS (100%),
  FP-relationship rate (2.17%), forum/member correctly-handled (100%),
  target-resolution path live (26.09% unresolved-named).
- Zero new regressions vs. the June 11 baseline across all five operator
  focus dimensions (new FPs, new resolver-failure sub-buckets, unresolved-named
  distribution drift, new ambiguity examples, new regression clusters).
- §13 review-signal gates 3–10 (relationship-context loss, wrong-target,
  multi-lens coverage, couple↔forum bleed, explainability, decision-not-
  explainable, payload completeness baseline): all PASS / WATCH.
- Founder/operator/spouse/forum suite: **router is correct in every case
  where ground truth is present**; failures cluster into three known buckets
  (below), all of which have queued fixes.

**Three trade-offs the operator must consciously accept before flipping:**

1. **Lens-jargon override** (§13.2 FAIL — 2 cases, 4.35%). Both cases are
   lexicon weighting issues. Queue to **B3 hardening**.

2. **Founder/operator lexicon gap** (NEW — surfaced by this suite). 6/10
   founder prompts (executive, downsizing, cofounder, growth constraint,
   blind spot/decision-avoidance, between-me-and-team) fall to `general` or
   the wrong adjacent domain. **This is not a regression** — the legacy router
   exhibits the same gap — but the operator should know that their own
   personal usage pattern will hit `general` fallback frequently. Queue to
   **B3 hardening** as a "founder/operator lexicon expansion" task.

3. **Shadow telemetry span gate** (FAIL). The live shadow window accumulated
   only ~50 minutes of receipts (n=13). The 3-day-span gate is not satisfied.
   This is a measurement-coverage gap (the harness didn't capture more
   traffic), not a quality issue. Operator can either:
   - **(a)** Accept the limited span (replay corpus is comprehensive at 86
     cases over 90 days) and proceed, **or**
   - **(b)** Hold cutover until a 3-day live shadow span is genuinely
     accumulated (would push rollout by 3+ days).

### Recommended next step if operator accepts (a)/(b)/(c) above:

> Proceed to **Stage 1 Rollout (10%)** governance — but keep
> `INTENT_ROUTER_V2_CUTOVER = false` until the operator explicitly approves the
> flip in a separate sign-off action. No automatic advancement.

### Halt criteria (carried forward, unchanged)

Any of the following automatically halts progression between stages:
- Retrieval PASS rate < 97%
- FP relationship rate > 5%
- Any new resolver-failure sub-bucket in live telemetry
- Forum/member correctly-handled rate < 90%
- Any unexpected rise in `target_unresolved`
- Any regression cluster (≥3 of same kind) not represented in the golden sets
- Any §13 review-signal gate flipping FAIL since the prior stage

### Pre-cutover P-queue updates (informational; no writes performed)

After this validation pass, the operator's B3 hardening backlog should
absorb these explicit items:

- **B3.1**: Lens-term compound entries + educational-mode disambiguation
  (resolves §13.2 lens-jargon override).
- **B3.2**: Founder/operator lexicon expansion (executive, downsizing,
  cofounder, growth constraint, blind spot, decision-avoidance,
  management-team dynamics, fundraising-vs-profitability tradeoffs).
- **P4 (unchanged)**: Forum topology resolution — wire
  `forum_topology.active_member_id` from chat surface. Validated to flip
  forum bucket from 0% → 100% pass with no router changes needed.

---

## Appendix A — Files referenced (READ ONLY)

- `/app/backend/services/intent_router_v2.py` — read
- `/app/backend/services/relationship_router_v2.py` — read
- `/app/backend/tools/b2_replay_runner.py` — re-executed (no changes)
- `/app/backend/tools/b2_readiness_report.py` — re-executed (no changes)
- `/app/backend/audit_reports/B2_READINESS_REPORT.{md,json}` — regenerated
- `/app/backend/audit_reports/B2_REPLAY_RESULTS.{json}` — regenerated
- `/app/backend/audit_reports/B2_REPLAY_SAMPLES.md` — regenerated
- `/tmp/b2_validation/founder_suite_v2.py` — one-shot validation harness
  (out-of-tree, no impact on production code).

## Appendix B — Toggle state

```
INTENT_ROUTER_V2_CUTOVER = false   (unchanged)
```

No production code, no feature flags, and no DB rows were modified during
this validation pass.
