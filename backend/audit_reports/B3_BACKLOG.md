# Mirror Chat V2 — B3 Hardening Backlog

_Generated as part of the June 14 EOD operator decision (rollout preparation
only)._

_Cutover status_: `INTENT_ROUTER_V2_CUTOVER = false` — these items will be
worked **after** the Stage-1 (10%) rollout window has been operator-approved
and observed. None of these items block the Stage-1 entry decision.

---

## B3.1 — Lens-term compound entries + educational-mode disambiguation

**Owner**: Track 1 (Mirror Chat) routing lane.
**Priority**: P2 (queued behind Stage-1 cutover preparation).
**Closes review signal**: §13.2 `lens_jargon_override` FAIL (Saturn return →
identity, 7th house → relationship).

### Problem statement
The lexicon-only intent router does not distinguish:
1. Lens-term compounds where the compound implies a *different* domain than
   either word alone — e.g. `saturn return` is a timing/life-direction event
   (not the identity-shaping themes Saturn alone implies).
2. Lens-term-alone-implies-domain collapse — e.g. `7th house` always routes
   to `relationship` even when the user has no relational context in the
   message (purely educational/chart-explanation framing).

### Acceptance criteria
- Lexicon entries added for at minimum:
  - `saturn return` → life_direction (timing-event compound)
  - `nodal return` → life_direction
  - `progressed moon` → growth
  - `pluto transit` → transformation
  - `mid-life return` / `mid-life crisis transit` → life_direction
  - `chiron return` → growth
- Educational-mode disambiguation rule: if a lens term is present **AND**
  none of `_EDU_CONTEXTUAL_CUE_RE` (relational/career/temporal cue, name)
  fires, downweight the lens-term's natural domain and prefer `identity`
  (the contextually neutral synthesis lane).
- After implementation, the §13.2 lens-jargon override rate must drop to
  `< 1%` on the next replay.
- Educational astrology routing PASS rate stays `≥ 95%` (Stage-1 telemetry
  category 6.2).

### Test gates
- Add 8 educational-astrology prompts to a new golden set
  (`golden_set_educational_astrology.yaml`).
- Add the 2 known failures (Saturn return + 7th house) to that golden set.
- New benchmark suite must hit ≥ 95% top-1.

### Out of scope
- Multi-turn educational lessons (B4 work).
- Embedding-based fallback (intentionally deferred).

---

## B3.2 — Founder / operator lexicon expansion

**Owner**: Track 1 routing lane.
**Priority**: P2 (queued behind B3.1).
**Closes review signal**: Founder/operator validation suite domain accuracy
40% (6/10 prompts fall to `general`).

### Problem statement
The lexicon under-represents founder/operator vocabulary:
- "executive", "downsizing", "cofounder dispute", "growth constraint",
  "fundraising vs. profitability", "blind spot in my leadership",
  "decision avoidance", "management-team dynamics" all currently route to
  `general` (confidence 0.00) or to wrong adjacent domains
  (`relationship` on "between me and my management team").

### Acceptance criteria
- Lexicon additions to the `leadership` and `career` domains in
  `intent_router_v2.py` covering at minimum:
  - executive / executives / leadership team / management team
  - cofounder / co-founder / founder / CEO / CTO / COO / VPE
  - downsizing / layoffs / reduction in force / RIF
  - growth constraint / scaling constraint / bottleneck
  - fundraising / runway / capital allocation / burn rate
  - blind spot / decision avoidance / avoiding a decision
  - delegation / hiring / firing / letting someone go
  - product direction / strategy / company direction
- Bias rule: in `self` frame with founder/operator vocabulary, suppress
  `relationship` collapse from generic phrases like "between me and my
  management team" — the dyad must be a person (Mel, Isaac, named) not a
  team or business unit.
- Founder/operator validation suite domain accuracy ≥ 80% after
  implementation (up from current 40%).
- Founder/operator routing PASS rate ≥ 85% in live Stage-1 telemetry
  (category 6.1).

### Test gates
- The existing `/tmp/b2_validation/founder_suite_v2.py` 30-prompt suite
  must be re-runnable from `/app/backend/tools/` (move out of /tmp) and
  must pass the new threshold.
- Add a 20-prompt founder-only golden set
  (`golden_set_founder_operator.yaml`).
- Benchmark top-1 ≥ 85% on founder golden set.

### Out of scope
- Per-industry vocabulary (consulting/SaaS/manufacturing-specific).
- LLM-assisted lexicon expansion.

---

## P4 — Forum topology resolution

**Owner**: Track 1 / Track 4 (chat surface + resolver lane).
**Priority**: P4 (queued; **largest pre-Stage-2 lever** — affects ~48% of
real traffic).
**Closes**: Forum bucket 0% pass in current production wiring; resolver is
already capable when `forum_topology.active_member_id` is supplied.

### Problem statement
The chat surface today does **not** pass
`forum_topology.active_member_id` to the relationship router when a user is
in a forum chat. The resolver supports the path (verified — flips forum
bucket to 100% pass when wired), but no caller supplies the field.

### Acceptance criteria
- `mirror_chat_shadow.py` and `mirror_chat.py` (or wherever the chat
  request handler builds the resolver kwargs) pass:
  ```python
  forum_topology={
      "forum_id": <active forum id>,
      "active_member_id": <the member currently focused in UI>,
      "members": [...],
  }
  ```
- Frontend forum-chat screen emits `active_member_id` in the request
  payload (already known on the client when a user is viewing a member's
  reflection within the forum).
- Receipt classifier `is_forum_topology_dependent` count drops as a share
  of total receipts (because successful forum-topology resolutions no
  longer satisfy the "dependent + unresolved" criterion).
- Stage-1 telemetry category 6.3 `routing_pass_rate` ≥ 90% (today
  measured at 90.9% on replay; expectation is to stay high once live).
- `context_mode=RELATIONAL` rate on `active_frame=forum` prompts ≥ 90%.

### Test gates
- Re-run the founder/operator validation suite with
  `active_member_id=kara-001` supplied — forum bucket must show 100%
  pass (already verified in `B2_FOUNDER_OPERATOR_VALIDATION_JUNE14.md`).
- Add a 10-prompt forum-topology golden set; benchmark top-1 ≥ 95%.

### Out of scope
- Multi-active-member forum sessions (a single active member at a time is
  sufficient for P4).
- Forum topology auto-population from chat history (different P-track
  item).

---

## Sequence and dependency

```
Stage-1 prep
  │
  ├──► B3.1 (lens-jargon)    ── narrows §13.2 ── enables Stage-2
  │
  ├──► B3.2 (founder lexicon) ── lifts founder PASS ── enables Stage-2
  │
  └──► P4   (forum topology)  ── lifts forum PASS  ── enables Stage-2
           (LARGEST LEVER — 48% of real traffic)
```

The three items are **parallelizable** — they touch different parts of the
stack (lexicon, lexicon+bias, chat-surface plumbing). No serial dependency.

---

## Telemetry hooks already in place

All three items have analytical classifiers already wired into the offline
replay tools (see `b2_replay_runner.py` and `b2_readiness_report.py` §14):

- `is_founder_query`            → B3.2 target lane counter
- `is_educational_astrology`    → B3.1 target lane counter
- `is_forum_topology_dependent` → P4 target lane counter

These counters will become **live-telemetry** counters as soon as the
Stage-1 receipt schema is extended (see Stage-1 plan §9.2 — separate
authorization required).

---

## Tracking

| Item | Status        | ETA       | Operator owner |
|------|---------------|-----------|----------------|
| B3.1 | NOT STARTED   | post-S1   | _to be assigned_ |
| B3.2 | NOT STARTED   | post-S1   | _to be assigned_ |
| P4   | NOT STARTED   | post-S1   | _to be assigned_ |
