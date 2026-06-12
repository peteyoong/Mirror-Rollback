# PFS-2.2 Consumer-Side Topology Audit

**Sprint:** Production Fidelity Sprint (PFS-2.2)
**Scope:** Read-only forensic audit of every downstream consumer of relationship-resolution data.
**Goal:** Verify which consumers correctly consume topology-first relationship data and which still rely on heuristic / forum-name signals.
**Mode:** **NO CODE CHANGES.** No flag flips. Pure inspection of the source tree and runtime call ordering.

---

## 0. Constraint Reaffirmation

```
INTENT_ROUTER_V2_CUTOVER             = false   (unchanged)
INTENT_ROUTER_V2_ROLLOUT_PERCENT     = 10      (unchanged)
RELATIONSHIP_ORCHESTRATION_PROMPT    = false   (unchanged)
CROSS_LENS_PROMPT_SURFACE            = false   (unchanged)
```

No flags were modified. No code was modified. This is forensic only.

---

## 1. Summary Verdict

| #   | Consumer                                                                                | Topology-aware | Topology-primary | Heuristic fallback | Status        |
|-----|-----------------------------------------------------------------------------------------|----------------|------------------|--------------------|---------------|
| 1   | **P3 — `relationship_orchestration_v1.plan_lens_priority`**                              | Indirect (role-string only) | **No** — sees only `relationship_role` string | Yes (lexicon match) | **BLOCKED**   |
| 2   | **Intent-V2 prompt block — `build_intent_v2_prompt_block`**                              | Yes (reads `relationship_resolution` post-promotion) | Partial — reads `role` but ignores `topology_role_*` telemetry | Yes (reads `resolution_source`) | **PARTIAL**   |
| 3   | **Cross-Lens Synthesis v2 — `compute_synthesis_v2`**                                     | No (pure raw_scores function) | N/A by design | N/A | **READY** (topology-agnostic by design) |
| 4   | **Founder/Operator context — `build_founder_context_block`**                             | No (lexicon + matched_phrases only) | N/A by design | N/A | **READY** (topology-agnostic by design) |
| 5   | **Timeline V2 modulation — `build_timeline_v2_context`**                                 | No (reads `user_timeline` only) | N/A by design | N/A | **READY** (topology-agnostic by design) |
| 6   | **Relationship Field v1 — `services/relationship_field.py`**                             | No (HD / astrology lens inputs only — no receipt consumption) | N/A | N/A | **READY** (topology-agnostic by design) |
| 7   | **Between-You-Today — `services/relationship_today.py`**                                 | No (transits + relationship_field outputs only) | N/A | N/A | **READY** (topology-agnostic by design) |
| 8   | **Forum Field Intelligence — `forum_field_intelligence.compose_story_of_circle`**        | Yes (reads `forum_relationship_edges` directly via `list_edges`) | Yes (forum-level aggregate of edge `role_type`/`confidence`) | Aggregates only — no per-target role surfacing | **READY** (forum-aggregate axis; not blocked by PFS-2.1) |
| 9   | **Forum Conversational Field — `forum_conversational_field.py`**                         | Yes (consumes `topology_confidence` from `forum_field_intelligence` debug) | Forum-level only | N/A | **READY** |
| 10  | **Contradiction Intelligence — `contradiction_intelligence.py`**                         | Yes (reads `get_topology_confidence_state`) | Forum-level only | N/A | **READY** |
| 11  | **Retrieval validation receipt — `retrieval_validation_v1.build_receipt`**               | Indirect (persists whatever `relationship_resolution` it is handed) | Persists post-promotion topology fields | N/A | **READY** (passthrough; PFS-2.1 patch updated upstream router so the post-promotion dict already includes topology fields) |

**Counts:** READY = **8**, PARTIAL = **1**, BLOCKED = **1**.

---

## 2. Method

For each consumer I answered the five questions specified by the sprint owner:

1. Does it read `topology_role_type` / `topology_confidence` / `topology_inferred`?
2. Does it still read `heuristic_role` / forum-name-derived role?
3. Which source wins if both exist?
4. Does any consumer silently discard topology information?
5. Does any consumer still infer spouse/cofounder/family from forum naming?

Source-tree grep traces:

- `topology_role_type` / `topology_role_found` / `topology_confidence` (as PFS-2.1 fields):
  appear only in `services/mirror_chat_phase4_enrichment.py`, `routers/mirror_chat.py`,
  and the validation scripts. **No other consumer reads them.**
- `topology_confidence` as a forum-aggregate name (different surface, same source collection) appears in:
  `services/forum_field_intelligence.py`, `services/forum_conversational_field.py`,
  `services/contradiction_intelligence.py` — via
  `services.forum_topology.get_topology_confidence_state`.
- Forum-name regex lives in `services/mirror_chat_phase4_enrichment._classify_forum_source`
  and is invoked **only inside `resolve_target_via_forums`** (PFS-1 fallback, now topology-gated).
  No other module performs forum-name regex inference of spouse/cofounder/family.

---

## 3. Critical Finding — P3 Orchestration is BLOCKED

### Call ordering proves the gap

`services/mirror_chat_shadow.compute_v2_envelope_sync` (file: `services/mirror_chat_shadow.py`)
is invoked at `routers/mirror_chat.py:201` **before** the Phase-4 R3b /
PFS-2.1 forum-fallback resolver runs at `routers/mirror_chat.py:963`.

Inside `compute_v2_envelope_sync`:

```python
# routers/mirror_chat.py:201  →  services/mirror_chat_shadow.py:80-216
resolved_role = rel_resolved.role          #  V2 router output — pre-PFS-2.1
envelope = classify_intent_v2(... relationship_role=resolved_role ...)
receipt["relationship_orchestration_v1"] = plan_lens_priority(
    intent_envelope=envd,
    relationship_role=resolved_role,        #  PRE-PFS-2.1 ROLE
    target_resolved=resolved_target_id,     #  PRE-PFS-2.1 TARGET
    forum_topology=forum_topology,
    context_mode=lens or life_domain,
)
```

Then in `routers/mirror_chat.py:963-1003` the post-PFS-2.1 promotion happens:

```python
v2_receipt["relationship_resolution"] = {
    ...,
    "role": _forum_resolved["resolved_role"],          # "spouse" / "child" / "cofounder" …
    "topology_role_found":  ...,
    "topology_role_type":   ...,
    ...
}
```

But the receipt's `relationship_orchestration_v1` has **already been computed**
using the pre-PFS-2.1 `resolved_role`. There is no re-plan / re-orchestrate
step after the promotion. Search confirms: `plan_lens_priority` is called
**only** inside `mirror_chat_shadow.py` (lines 202 and 385) — never inside
`routers/mirror_chat.py` after the topology enrichment.

### Impact

P3's `_resolve_role_bucket` keys on a lexicon match against
`relationship_role`:

| Topology edge `role_type` | Old V2 router `role` (pre-PFS-2.1) | P3 bucket result if PFS-2.1 surfaced it | Current behaviour (still pre-PFS-2.1) |
|---------------------------|-------------------------------------|------------------------------------------|----------------------------------------|
| `spouse`                  | often `partner` (or `None`)         | `spouse` (matches `_SPOUSE_ROLES`)       | `spouse` if V2 returned `partner` ✓; **`self`** if V2 returned `None` (Pete & Mel without saved_people row) |
| `child`                   | usually missing                     | `child`                                   | usually `self` ✗ |
| `cofounder`               | usually missing                     | `cofounder`                               | usually `self` ✗ |
| `mentor` / `manager` / `investor` / `advisor` / `employee` / `coach` | not in P3 lexicon at all | falls through to forum_member | **forum_member or self** — **lexicon gap even AFTER topology consumption.** |

> **Two defects, not one.**
> 1. *Plumbing defect:* P3 is wired to pre-PFS-2.1 role and never re-run after promotion.
> 2. *Lexicon defect:* even when re-wired, P3's `_SPOUSE_ROLES / _CHILD_ROLES / _COFOUNDER_ROLES` sets do NOT cover the full topology vocabulary
>    (`former_partner`, `parent`, `sibling`, `mentor`, `mentee`, `coach`,
>    `coachee`, `manager`, `employee`, `investor`, `advisor`, `business_partner`,
>    `authority_figure`, `collaborator`, `close_friend`, `forum_mate`,
>    `other`).
>    These will silently fall through to `forum_member` or `self` even
>    after the call-ordering is fixed.

**Status: BLOCKED.** Ungating `RELATIONSHIP_ORCHESTRATION_PROMPT` today
would not surface any topology benefit — it would surface the **stale,
pre-topology lens plan** as a "Suggested framing" instruction to the
LLM. That is a regression risk relative to keeping it off.

---

## 4. PARTIAL Finding — Intent V2 Prompt Block

### File: `services/mirror_chat_phase4_enrichment.build_intent_v2_prompt_block`

Lines 733-768 read:

```python
tgt        = rel.get("target")                    # post-PFS-2.1 ✓
tgt_role   = rel.get("role")                      # post-PFS-2.1 (spouse / child / cofounder …) ✓
res_source = rel.get("resolution_source") or v2_receipt.get("target_resolution_source")
```

The role-aware sentence built into the prompt now correctly carries the
**topology-derived role** (`spouse`, `child`, `cofounder`, etc.) because
the `relationship_resolution` dict was promoted by the PFS-2.1 patch in
`routers/mirror_chat.py:979-1005`.

**What it does well:**
- Reads `target_name`, `role`, `forum_name`, `resolution_source` from the
  post-promotion dict ✓
- Includes the role in the LLM-facing sentence:
  `"Relationship target: 'Mel' (resolved via pair_forum in the 'Pete & Mel' forum (relationship_role: spouse))"` ✓
- Allowlist of `resolution_source` values covers `forum_member`,
  `pair_forum`, `family_forum`, `business_forum`, plus the two alias
  forms ✓

**What it discards (the PARTIAL):**
- It does **not** read `topology_role_found`, `topology_confidence`, or
  `topology_inferred`. The prompt has no signal to differentiate
  "this is an EXPLICIT relationship topology edge" from "this is a
  forum-name heuristic guess". A `high / explicit` edge and a `low /
  inferred` edge land in the prompt identically.
- It does **not** surface `topology_edge_id` — useful for downstream
  audit / debugging but not for the LLM.

**Recommendation (no code change in this audit):** add an "ANCHOR /
HEURISTIC" suffix to the existing sentence when `topology_role_found`
flips between True/False, so the LLM can weight confidence accordingly.
**Defer to a separate consumer-patch ticket; not a blocker.**

---

## 5. READY Consumers — Why They Are Safe

### 5.1 `cross_lens_synthesis_v2.compute_synthesis_v2`

Pure function over `intent_envelope.raw_scores` and matched-phrase
evidence. **Never** reads `relationship_resolution`, `target`,
`relationship_role`, or topology. Topology-agnostic by design — and that
is correct. Cross-lens tension is about *domain* signal balance, not
about *who* the user is talking to.

> If a future product spec wants topology-conditioned contradictions
> (e.g. "spouse-vs-team only when target is `spouse`"), it would
> require new code — not a fix.

### 5.2 `build_founder_context_block`

Triggers exclusively on `intent_envelope.primary_domain ∈ {career, leadership}`
or `FOUNDER_LEXICON_SIGNALS` matched phrases. Does not read the
relationship resolution at all. Founder context is a content-domain
signal, not a relationship signal — correctly decoupled.

### 5.3 `build_timeline_v2_context`

Reads `user_timeline` only. No relationship surface. Correctly decoupled.

### 5.4 `services/relationship_field.py` & `services/relationship_today.py`

These are HD / astrology / numerology synthesizers that derive the
"Between Us" envelope from *natal chart math* and forum_hd_mapping
outputs. They never consume `mirror_chat_retrieval_receipts` or
`relationship_resolution`. They sit on a different axis (per-pair lens
synthesis) and therefore cannot be "blocked by" PFS-2.1.

### 5.5 `forum_field_intelligence` / `forum_conversational_field` / `contradiction_intelligence`

These read `forum_relationship_edges` **directly** via
`services.forum_topology.list_edges` and
`services.forum_topology.get_topology_confidence_state`. They consume
**forum-level aggregates** (edge density, high-confidence count, role
distribution counts) — not per-receipt role information. This is the
same physical collection PFS-2.1 leverages, just consumed at a
different granularity.

> Confirmation that no false inference of spouse/cofounder/family from
> forum-name regex occurs in these modules:
> `grep -n "_PAIR_FORUM_NAME_RE\|_FAMILY_FORUM_NAME_RE\|_BUSINESS_KEYWORD_RE" services/forum_*.py services/contradiction_intelligence.py` →
> **zero matches.** All inference is graph-edge-driven.

### 5.6 `retrieval_validation_v1.build_receipt`

A receipt-shape passthrough. Accepts `relationship_resolution` and
embeds it verbatim. Because the PFS-2.1 router patch mutates this dict
to include the five topology telemetry fields BEFORE the post-Phase-4
persist call, the persisted receipt already contains topology
provenance — confirmed by the live trace dump in
`PFS21_PROBE_TRACES.txt`.

---

## 6. Five-Question Matrix (Per Consumer)

| Consumer | Reads `topology_role_type` / `topology_confidence` / `topology_inferred`? | Reads `heuristic_role` / forum-name-derived role? | Source priority if both present | Silently discards topology? | Still infers from forum naming? |
|---|---|---|---|---|---|
| P3 orchestration (`plan_lens_priority`) | No | No (sees only `relationship_role` string from V2 router) | **N/A — only sees one input** | **YES (entire topology telemetry is discarded)** | No |
| Intent-V2 prompt block | No (only reads the post-promoted `role`) | No (the heuristic_role is discarded by router promotion) | Topology wins via the promoted `role` | Partial (the `_role_found / _confidence / _inferred` flags) | No |
| Cross-Lens Synthesis v2 | No | No | N/A — by design | N/A | No |
| Founder context | No | No | N/A — by design | N/A | No |
| Timeline V2 | No | No | N/A — by design | N/A | No |
| Relationship Field v1 | No | No | N/A — different axis | N/A | No |
| Between-You-Today (`relationship_today.py`) | No | No | N/A — different axis | N/A | No |
| Forum Field Intelligence | Indirectly (forum-level confidence aggregate from same source collection) | No | Edge data wins (heuristic never reaches here) | No | No |
| Forum Conversational Field | Indirectly (via forum_field_intelligence) | No | N/A | No | No |
| Contradiction Intelligence | Indirectly (forum confidence aggregate) | No | N/A | No | No |
| Retrieval validation receipt | Yes (passthrough of post-PFS-2.1 dict) | No | Topology wins (router promotion) | No | No |

---

## 7. Recommendations (no code changes in this report)

### P0 — Must fix before P3 ungating
1. **Plumbing:** Move `relationship_orchestration_v1.plan_lens_priority`
   to run **after** the PFS-2.1 forum-fallback enrichment in
   `routers/mirror_chat.py`, so it receives the post-topology
   `resolved_role` and `target_resolved`. OR: keep the shadow-side call
   for back-compat and add a SECOND call in the router that **overwrites**
   `v2_receipt["relationship_orchestration_v1"]` when topology resolved
   a new target/role.
2. **Lexicon:** Expand P3's `_SPOUSE_ROLES / _CHILD_ROLES /
   _COFOUNDER_ROLES` (and add new buckets) to cover the full
   `forum_relationship_edges` role vocabulary so `mentor`, `manager`,
   `investor`, `advisor`, `parent`, `sibling`, `former_partner`,
   `coach`, `coachee`, `employee`, `business_partner`,
   `authority_figure`, `collaborator` produce intentional lens plans —
   not silent `forum_member`/`self` fallthroughs.
3. After P0/1 and P0/2 land, re-run the PFS-2.1 probe set with P3
   enabled in shadow and verify the lens plan changes appropriately.

### P1 — Recommended before any rollout %
4. **Intent-V2 prompt block:** surface a "topology_anchor=true|false"
   tag (single byte) when `relationship_resolution.topology_role_found`
   is True, so the LLM can weight the assertion. Optional but cheap.

### P2 — Nice-to-have
5. Add a dashboard counter in `tools/p3_observation_dashboard.py` that
   tracks the fraction of receipts where
   `relationship_orchestration_v1.role_resolved` matches
   `relationship_resolution.topology_role_type` — this is the
   single most useful continuous metric for the next observation
   window.

### Out of scope for this audit
- Production data parity (Pulsifi Leadership, cofounder/mentor forums)
  remains blocked by Preview ↔ Production isolation
  (`PRODUCTION_TOPOLOGY_AUDIT.md`). Not addressable in Preview.
- Cross-lens "topology-conditioned contradictions" is a *new feature*,
  not a fix.

---

## 8. Recommendation

> **Do not ungate `RELATIONSHIP_ORCHESTRATION_PROMPT`.**
> **Do not ungate `CROSS_LENS_PROMPT_SURFACE`.**
> **Do not change rollout %, cutover, P5, or Variant A flags.**
>
> P3 is **BLOCKED** by a plumbing defect and a lexicon defect that
> together cause the topology-first resolver's benefit to be
> entirely discarded by the orchestration plan. The plan is
> consequently stale relative to the receipt's topology data.
>
> Cross-Lens is **READY by design** (topology-agnostic), but ungating
> it independently provides no PFS-2.1 benefit. Hold until P3 fixed
> so the rollout package is coherent.
>
> Intent-V2 prompt block is **PARTIAL** — already useful (it does
> surface the topology-derived role to the LLM via the promoted
> `relationship_resolution.role`) but discards confidence/inferred
> telemetry. Not blocking by itself.

**Next forensic ticket (after user approval):** PFS-2.3 — patch P3
orchestration to (a) run post-topology and (b) absorb the full role
vocabulary; then re-run the PFS-2.1 probe suite with
`RELATIONSHIP_ORCHESTRATION_PROMPT` *flipped on in shadow only* to
verify topology actually changes the lens plan.

---

## Appendix A — Files Inspected

| File | Reads `relationship_resolution`? | Reads `forum_relationship_edges`? | Status |
|------|----------------------------------|------------------------------------|--------|
| `services/mirror_chat_phase4_enrichment.py`     | Yes (resolver itself + prompt builder) | Yes (PFS-2.1) | PFS-2.1 owner |
| `services/mirror_chat_shadow.py`                | Yes (builds receipt; feeds P3 with pre-PFS-2.1 role) | No | BLOCKED — wrong ordering |
| `services/relationship_orchestration_v1.py`     | No (input is a raw role string)           | No                   | BLOCKED — lexicon gap |
| `services/cross_lens_synthesis_v2.py`           | No                                        | No                   | READY (by design) |
| `services/retrieval_validation_v1.py`           | Yes (passthrough)                         | No                   | READY |
| `services/relationship_field.py`                | No                                        | No                   | READY |
| `services/relationship_today.py`                | No                                        | No                   | READY |
| `services/forum_field_intelligence.py`          | No                                        | Yes (forum-aggregate) | READY |
| `services/forum_conversational_field.py`        | No                                        | Yes (via forum_field_intelligence) | READY |
| `services/contradiction_intelligence.py`        | No                                        | Yes (forum confidence) | READY |
| `services/forum_topology.py`                    | No                                        | Yes (CRUD)            | READY (source-of-truth surface) |

## Appendix B — Grep Trace Evidence

```
$ grep -rln "topology_role_type\|topology_role_found\|topology_inferred" /app/backend --include="*.py"
services/mirror_chat_phase4_enrichment.py
routers/mirror_chat.py
scripts/pfs21_validation_probes.py

$ grep -n "plan_lens_priority" /app/backend/**/*.py
services/mirror_chat_shadow.py:202   ←  fed pre-PFS-2.1 role
services/mirror_chat_shadow.py:385   ←  sync-path variant, same issue
services/mirror_chat_shadow.py:28    ←  import
(no occurrence in routers/mirror_chat.py post-topology)

$ grep -n "_PAIR_FORUM_NAME_RE\|_FAMILY_FORUM_NAME_RE\|_BUSINESS_KEYWORD_RE" \
       /app/backend/services/forum_*.py /app/backend/services/contradiction_*.py
(no matches)
```

Confirms: zero downstream consumers re-invoke the forum-name regex.
The only place forum-name inference still runs is inside
`_classify_forum_source`, called only by the PFS-2.1 resolver as the
heuristic fallback, after the topology lookup has been attempted.

## Appendix C — Files NOT touched in this audit

This audit is read-only. No file under `/app` was modified during
its execution. All probe scripts and report writes go to
`/app/backend/audit_reports/PFS22_CONSUMER_AUDIT.md` only.
