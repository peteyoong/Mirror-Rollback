# B3 Hardening — Implementation Plan

_Issued under operator priority change (pre-Stage-1 rollout). All work
performed **with** `INTENT_ROUTER_V2_CUTOVER=false` and
`INTENT_ROUTER_V2_ROLLOUT_PERCENT=0` — no flag is flipped by this work._

Order of execution per operator decision:

1. **B3.2** — Founder / Operator lexicon expansion
2. **P4**   — Forum-topology plumbing (separate plan: `P4_IMPLEMENTATION_PLAN.md`)
3. **B3.1** — Lens-term compound entries + educational-mode disambiguation
4. Re-run validation suite
5. Refresh readiness report
6. Issue revised Stage-1 readiness recommendation

---

## B3.2 — Founder / Operator Lexicon Expansion

**Goal**: lift the founder/operator validation-suite domain accuracy
from 40% to ≥ 80% **without** changing the v2 router's calibration
constants or the offline classifier's overall shape.

### Scope of edits

`/app/backend/services/lens_registries/domain_lexicons.yaml` — additive
only, no existing weights changed.

**`leadership` additions**
- `executive` (w=0.55), `executives` (w=0.55), `the executive` (w=0.65)
- `let this executive go` (w=0.95), `let an executive go` (w=0.95)
- `leadership team` (w=0.85), `management team` (w=0.85), `exec team` (w=0.85)
- `downsiz` (w=0.85) → matches `downsizing`/`downsize`
- `layoff` (w=0.8), `layoffs` (w=0.85), `reduction in force` (w=0.9), `rif`-tokenless variants
- `cofounder` (w=0.85), `co-founder` (w=0.85), `cofounder disagree` (w=0.95),
  `cofounder dispute` (w=0.95), `disagree about product direction` (w=0.9)
- `growth constraint` (w=0.95), `scaling constraint` (w=0.9),
  `bottleneck in the business` (w=0.85), `next growth constraint` (w=0.95)
- `blind spot in my leadership` (w=0.95), `blind spot in my` (w=0.7)
- `decision avoidance` (w=0.9), `avoiding a decision` (w=0.9),
  `am i avoiding` (w=0.85)
- `friction in the company` (w=0.85), `creating friction` (w=0.7),
  `which relationship is creating friction` (w=0.95)

**`career` additions**
- `fundraising or profitability` (w=0.95), `fundraising vs profitability` (w=0.95),
  `prioritize fundraising` (w=0.9)
- `cofounder` (w=0.7) — secondary career signal
- `product direction` (w=0.7), `company direction` (w=0.8)
- `head of product` (already present), `head of engineering` (already present)

**`leadership` bias against generic team-collapse**
- Add `team dynamics` (w=0.7), `dynamic between me and my` (w=0.65),
  `dynamic exists between me and` (w=0.85),
  `between me and my management team` (w=0.95),
  `between me and my team` (w=0.85)

### Anti-collapse rule (router-level)

`intent_router_v2.py` gains a small `_suppress_team_relationship_collapse()`
pass:

> When `active_frame=self` AND the message contains a generic team /
> business-unit phrase (`my team`, `my management team`, `my exec team`,
> `my leadership team`, `the team`, `the business`, `the company`) AND
> the message contains **no proper-name** (per the existing name-extraction
> regex) AND no role noun (`partner`, `wife`, `husband`, `mum`, ...) →
> subtract a fixed penalty from the `relationship` raw score before
> ranking.

The penalty is small (0.30) — strong enough to flip a 0.45/0.25 split
toward leadership/career, but not so large that a real relational signal
ever loses.

### Acceptance criteria (B3.2)

- Founder/operator 30-prompt validation suite domain accuracy ≥ 80%
  (today: 40%).
- Lens-jargon golden set (`golden_set_lens_jargon.yaml`) top-1 ≥ 95%.
- Founder golden set (`golden_set_founder.yaml`) top-1 = 100%.
- Relationship/forum golden set top-1 = 100% (no regressions).
- All `b2_replay_runner.py` regression buckets remain in their pre-B3.2
  status (no new FAILs).

### Test gates

- `tools/intent_router_v2_benchmark.py` over all four golden sets must
  hit top-1 ≥ 95%.
- A new tools script `tools/founder_operator_suite.py` (moved out of
  `/tmp`) reruns the 30-prompt suite and writes
  `audit_reports/B3_FOUNDER_OPERATOR_VALIDATION.json`.
- `b2_replay_runner.py` rerun → `stage1_focused.founder_operator.routing_pass_rate`
  improves vs baseline.

### Out of scope (deferred to a later B-track)

- Per-industry vocabulary (SaaS / consulting / manufacturing-specific).
- LLM-assisted lexicon expansion.
- Multi-turn founder-mode dialog memory.

---

## B3.1 — Lens-Term Compound Entries + Educational-Mode Disambiguation

**Goal**: bring lens-jargon override rate below 1% on the next replay
while preserving all true-positive relational/career/family/money lens
collapses (e.g. "tell me about Mel's 4th house").

### Lexicon additions

`life_direction`:
- `saturn return` (w=0.95), `my saturn return` (w=0.95)
- `nodal return` (w=0.85), `north node return` (w=0.85)
- `chiron return` (w=0.7) (cross-tagged growth at w=0.8 — growth wins)
- `mid-life crisis` (w=0.9), `mid-life return` (w=0.85),
  `midlife crisis transit` (w=0.9)
- `pluto transit` (w=0.85) (cross-tagged growth at w=0.9 — growth wins)

`growth`:
- `progressed moon` (w=0.85), `my progressed moon` (w=0.9)
- `chiron return` (w=0.8), `pluto transit` (w=0.9) — see above

`identity` (already has Saturn return at w=0.65 — lowered to w=0.4 so
life_direction wins the compound)

### Educational-mode disambiguation rule

New helper in `intent_router_v2.py`:
`_apply_educational_mode_disambiguation(text, raw_scores)`.

Trigger:
- Message contains a lens term (uses the same lens-term regex used by
  the replay runner's `_EDU_ASTRO_LENS_RE`).
- Message contains **none** of the contextual cues in
  `_EDU_CONTEXTUAL_CUE_RE` (relational, career, temporal, financial,
  conflict, naming).

Effect:
- Add a fixed bonus (+0.45) to the `identity` raw score so the educational
  framing wins over the lens term's natural domain when the message is
  otherwise purely definitional.
- Bonus is intentionally **smaller than** strong relational scores
  (e.g. `my 7th house` w=0.9 + `between us` w=0.95) so contextual
  relational queries still route to relationship.

### Acceptance criteria (B3.1)

- §13.2 lens-jargon override rate < 1% on the next replay run
  (current: 4.35%).
- Educational astrology routing PASS rate ≥ 95% on the new
  `golden_set_educational_astrology.yaml` (10 prompts).
- Lens-jargon golden set top-1 ≥ 95% (some entries shift from
  identity/relationship/career/family/money to **identity** by design —
  the golden set is updated to reflect this new policy and the diff is
  documented in `B3_VALIDATION_REPORT.md`).

### Test gates

- New `golden_set_educational_astrology.yaml` benchmark top-1 ≥ 95%.
- `b2_replay_runner.py` → `regression_buckets.lens_jargon_override.rate`
  < 0.01.

---

## Implementation order of operations

```
Step 1  Snapshot current benchmark + replay metrics as B3_BASELINE.json
Step 2  Implement B3.2 lexicon additions + anti-collapse rule
Step 3  Re-run benchmark — must keep 100% on existing golden sets
Step 4  Implement P4 plumbing (see P4_IMPLEMENTATION_PLAN.md)
Step 5  Implement B3.1 lexicon additions + educational-mode rule
Step 6  Update lens_jargon golden set entries that shift under the
        new educational-mode policy (LJ1, LJ6–LJ10)
Step 7  Add new golden_set_educational_astrology.yaml (10 cases)
Step 8  Re-run benchmark — all four legacy suites + new edu suite
Step 9  Re-run b2_replay_runner.py + b2_readiness_report.py
Step 10 Re-run founder/operator 30-prompt suite (P4 wired-in mode)
Step 11 Write B3_VALIDATION_REPORT.md + B2_STAGE1_READINESS_REVISED.md
```

All steps preserve `INTENT_ROUTER_V2_CUTOVER=false` and
`INTENT_ROUTER_V2_ROLLOUT_PERCENT=0`. No production traffic is
affected by any of these changes — they all live in the shadow router
and its offline benchmarks.
