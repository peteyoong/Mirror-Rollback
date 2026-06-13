# P3 Relationship Orchestration — Ungating Readiness Assessment

**Date:** 2026-06-13
**Status:** 🟥 **NOT SAFE to ungate now. Targeted fixes required.**
**Recommendation:** **B. Safe after targeted fixes** (see §5).
**Reproduce:**
  - `cd /app/backend && python scripts/p3_relationship_readiness_assessment.py`
  - Raw output: `/app/backend/audit_reports/P3_READINESS_ASSESSMENT.json`

All four rollout flags verified **untouched**:
```
INTENT_ROUTER_V2_CUTOVER=false
INTENT_ROUTER_V2_ROLLOUT_PERCENT=10
RELATIONSHIP_ORCHESTRATION_PROMPT=false
CROSS_LENS_PROMPT_SURFACE=false
```

This is an **assessment-only** ticket. No code paths were mutated; the
single new file is a read-only probe at
`backend/scripts/p3_relationship_readiness_assessment.py`. No flags
were toggled. No LLM was invoked.

---

## 1. Relationship Orchestration Map (current architecture)

```
            ┌──────────────────────────────────────────────────────────────┐
            │   POST /api/mirror/chat   ──┐                                │
            │   POST /api/forums/{f}/chat ┘                                │
            └─────────────────────────────────────────┬────────────────────┘
                                                      │
        ┌─────────────────────────────────────────────┴──────────────────────────────────────────────┐
        │  routers/mirror_chat.py · routers/forums_chat.py                                            │
        │                                                                                              │
        │   ① intent_router_v2  →  v2_receipt.intent_envelope (primary_domain, lens_priority)         │
        │      services/intent_router_v2.py                                                            │
        │                                                                                              │
        │   ② mirror_chat_phase4_enrichment.resolve_relationship_target                                │
        │      (saved_people / forum members / pair-forum inference)                                  │
        │      → v2_receipt.relationship_resolution { target, target_name, role, source }             │
        │      *** ROLE IS DRAWN FROM saved_people / forum_members.relationship_type ONLY ***          │
        │      *** does NOT consult forum_relationship_edges (THIS IS THE PRIMARY GAP) ***            │
        │                                                                                              │
        │   ③ relationship_resolver.resolve_relationship                                              │
        │      services/relationship_resolver.py — same data sources, plus relationship_mappings       │
        │                                                                                              │
        │   ④ relationship_orchestration_v1.plan_lens_priority                                        │
        │      services/relationship_orchestration_v1.py                                              │
        │      → receipt-only; emits rule_bucket / framing_hint / domain_bias / lens_priority_after   │
        │                                                                                              │
        │   ⑤ FKR v1 (build_fkr_evidence_block)                                                       │
        │      services/forum_chat_knowledge_retrieval.py                                             │
        │      *** resolves spouse from forum_relationship_edges (PARALLEL UNCONNECTED LOOKUP) ***     │
        │      → injects EVIDENCE block + MANDATORY enforcement footer                                │
        │                                                                                              │
        │   ⑥ mirror_chat_phase4_enrichment.build_intent_v2_prompt_block                             │
        │      → emits "RESOLVED TARGET (HIGH CONFIDENCE)" mandate (uses ② role, not ⑤)               │
        │      → "Suggested framing: …" line is GATED by RELATIONSHIP_ORCHESTRATION_PROMPT            │
        │                                                                                              │
        │   ⑦ emergent_generate(additional_system_prompt=…) ── LLM                                    │
        └──────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Key architectural observation.** The system has **two independent
relationship-role lookups** that disagree:

| Source             | Reads from                                       | Currently sees Pete↔Mel as |
|--------------------|--------------------------------------------------|----------------------------|
| FKR `resolve_targets()` (step ⑤) | `forum_relationship_edges`              | ✅ `spouse` |
| `relationship_resolver` (step ③)   | `relationship_mappings`, `saved_people`, `forum_members.relationship_type` | ❌ `None` |

`relationship_orchestration_v1` reads role from `relationship_resolver`,
so it buckets Mel as `forum_member` even though FKR already knows she
is `spouse`. The framing hint that the gate-flag would surface is
therefore **wrong**.

---

## 2. Live scenario probe results (10 scenarios)

Source: `backend/scripts/p3_relationship_readiness_assessment.py`,
output `audit_reports/P3_READINESS_ASSESSMENT.json`. Scoring dimensions
match the ticket's required deliverable.

### 2.1 Summary

| Dimension                  | PASS / 10 |
|----------------------------|-----------|
| Retrieval (FKR block emitted with target evidence) | **9 / 10** ✅ |
| Target Resolution (name → user_id)                | **10 / 10** ✅ |
| Relationship Resolution (role assigned)            | **4 / 10** ❌ |
| Orchestration Bucket (correct rule bucket)         | **4 / 10** ❌ |
| Prompt Construction (MANDATORY block + target present) | **9 / 10** ✅ |
| Mode Classification (expected mode fires)          | **4 / 10** ⚠️ |
| **Overall scenarios PASS**                         | **2 / 10** 🟥 |

### 2.2 Scenario-by-scenario

| Scenario | Modes | Targets | Role | Bucket | PASS | Failed dimensions |
|---|---|---|---|---|---|---|
| `spouse.affect` "How does Mel affect me?" | RELATIONSHIP | Mel | **None** | **forum_member** | ❌ | role + bucket |
| `spouse.struggle` "What do Mel and I struggle with?" | **∅** | Mel | **None** | **forum_member** | ❌ | role + bucket + modes |
| `spouse.lesson_pronoun` "What is the lesson between us?" | RELATIONSHIP | Mel (spouse auto-bind) | **None** | **forum_member** | ❌ | role + bucket |
| `child.thaddeus_need` "What does Thaddeus need from me?" | **∅** | Thaddeus | **None** | **forum_member** | ❌ | role + bucket + modes |
| `child.isaac_diff` "How is Isaac different from me?" | **∅** | Isaac | **None** | **forum_member** | ❌ | role + bucket + modes |
| `child_child.compare` "Compare Isaac and Thaddeus." | COMPARISON | Thaddeus, Isaac | None | forum_member | ✅ | (sibling-pair bucket not modelled) |
| `child_child.boys_differ` "How do the boys differ emotionally?" | **∅** | **∅** | None | self | ❌ | retrieval + modes + prompt |
| `forum_member.jay` "How does Jay affect me?" | RELATIONSHIP | (none — Jay not in graph) | None | self | ✅ | (correctly reports stranger) |
| `forum_dyn.balance` "Who balances Mel best?" | **∅** | Mel | **None** | **forum_member** | ❌ | role + bucket + modes |
| `forum_dyn.blind_spot` "What is this group's blind spot?" (forum=Yoong) | FACT_LOOKUP (wrong) | ∅ | None | forum_member | ❌ | modes |

### 2.3 Underlying data

`forum_relationship_edges` from Pete's perspective:
```
to=697ec826ad4b18f75bf42616  role=spouse  conf=high  forum=Pete&Mel
to=697ec826ad4b18f75bf42616  role=spouse  conf=high  forum=Yoong family
(NO edges to Thaddeus or Isaac at all)
```

`forum_members` for Yoong family:
```
Pete, Thaddeus, Isaac, Melissa   — all with relationship_type = None
```

`saved_people` for Pete — only fake test rows. `relationship_mappings`
— empty.

---

## 3. Gap Analysis — every capability missing before ungating

### Gap 1 · `relationship_resolver` doesn't read `forum_relationship_edges` (P0)

`services/relationship_resolver.py` priority order is:
1. `relationship_mappings` (empty)
2. `saved_people.relationship_type` (no real family rows)
3. `forum_members.relationship_type` (all `None`)
4. forum-name inference (heuristic, can't tell parent ↔ child)

The collection that DOES have the data (`forum_relationship_edges`) is
**not consulted at all**. FKR's `resolve_targets()` already shows this
collection is read-ready and accurate.

**Impact:** Spouse → resolved as `forum_member`. Suggested framing
would become `forum_member_dynamic` instead of `couple_dynamic`.

### Gap 2 · `forum_relationship_edges` missing parent↔child edges (P0)

The pair-forum (Pete & Mel) and family forum (Yoong family) both have
Pete→Mel `spouse` edges (high conf), but **no edges to the children at
all** — neither `parent`, `child`, nor anything inferable. Even with
Gap 1 fixed, Thaddeus and Isaac would still bucket as `forum_member`
because the graph itself has no edge.

This is a **data-population gap**, not a logic gap. The orchestration
service already supports `child`, `parent`, `sibling` buckets with
modulations; they're just unreachable for this family.

### Gap 3 · FKR-detected role doesn't flow into `v2_receipt` (P0)

FKR's `resolve_targets()` returns `targets = [{name:"Mel", role:"spouse"}]`
correctly, but writes it only into the EVIDENCE block. The
`v2_receipt["relationship_resolution"]["role"]` field used by the
orchestration plan is computed by an independent (failing) resolver.

Even when the LLM sees `Mel (spouse)` in the FKR block, the
orchestration plan separately tells it "rule_bucket: forum_member,
framing: forum_member_dynamic" — these conflict.

### Gap 4 · Mode classifier misses common natural-language patterns (P1)

Mode classifier in `forum_chat_knowledge_retrieval.classify_query()`
returns **no modes at all** for:
- "What do Mel and I struggle with?"  (pronoun + plural verb)
- "What does Thaddeus need from me?"  (parenting need)
- "How is Isaac different from me?"   (comparison phrased without "compare/vs")
- "Who balances Mel best?"            (forum-dynamic phrased as question)
- "What is this group's blind spot?"  (lands on `FACT_LOOKUP`, not `FORUM_DYNAMICS`)

This means the LLM gets no mode-aware enforcement copy, and the
orchestration plan loses one of its inputs (`primary_domain` heuristics).

**Severity is P1, not P0**, because FKR still emits the evidence block
when ≥1 named target resolves (which it does for 8/10 scenarios).

### Gap 5 · No group/plural target resolution (P2)

"How do the boys differ emotionally?" returns zero targets. There is
no path that maps a kinship plural ("the boys", "my kids", "the team")
to the set of forum members.

### Gap 6 · Mode classifier collision: `FACT_LOOKUP` vs `FORUM_DYNAMICS` (P2)

"What is this group's blind spot?" matches the `FACT_LOOKUP` rule
`\bwhat is\b` before the `FORUM_DYNAMICS` rule. Both should fire (the
classifier is intentionally multi-label) but `FACT_LOOKUP` semantically
implies a single-value lookup — the LLM then leads with a "the X is …"
sentence when the question is actually dynamic.

### Gap 7 · No sibling-pair bucket (P3)

`Compare Isaac and Thaddeus` resolves both targets and emits a
COMPARISON-mode block, but the orchestration bucket lands on
`forum_member` (since neither is "self"). There is no
`sibling_pair` / `peer_pair` bucket in `LENS_MODULATIONS`. The angle
fallback isn't wrong — but it's also not differentiated.

### Gap 8 · Receipt-only orchestration plan is not read by FKR enforcement (P3)

Even when the orchestration plan computes correctly, its
`framing_hint` and `domain_bias` are NEVER injected into the FKR
enforcement footer — they only feed the gated "Suggested framing"
line in the intent-v2 block. So ungating the flag exposes a *thin*
sliver of P3 to the LLM (a one-line hint), while FKR's much stronger
MANDATORY enforcement remains role-agnostic.

---

## 4. Risk Assessment

| Risk axis | Level | Reasoning |
|---|---|---|
| **LLM regression risk** | 🟥 HIGH | With Gap 3 unfixed, the gated framing-hint line would emit `"Suggested framing: forum_member_dynamic"` for spouse questions. The LLM would receive a contradictory signal (FKR says spouse, orchestration says forum_member) and lock onto the orchestration plan because it's "Suggested framing:" — a directive phrasing. Worse than current baseline. |
| **Data integrity risk** | 🟧 MEDIUM | Gap 2 (missing edges) means parent/child orchestration would silently degrade to forum_member for 2 of the 4 family members. Not visibly wrong, but quietly wrong. |
| **Classifier risk** | 🟧 MEDIUM | Gap 4 causes 4/10 scenarios to lose mode signal. FKR still emits, but the enforcement copy becomes weaker. Not a regression, but doesn't deliver promised value. |
| **Receipt-only safety net** | 🟩 LOW | The orchestration plan is currently shadow-only (receipt only) — turning on the flag exposes only the framing-hint line, not the lens re-rank. Blast radius is bounded. |
| **Rollback risk** | 🟩 LOW | Flipping the flag back to `false` is instant. No DB writes. |

**Aggregate ungating risk: 🟥 HIGH** — driven by Gap 3 (FKR/orchestration disagreement), which would produce *worse* outputs than the current `=false` state for the most common case (spouse).

---

## 5. Recommendation: **B — Safe after targeted fixes**

Ungating is feasible, but **only after** the following targeted, additive fixes (all in the rendering / wiring layer — no calculator, no birth data, no flag changes required):

### B.1 · Priority-ordered fix list

| # | Severity | Effort | Description |
|---|---|---|---|
| 1 | P0 | S | Bridge FKR-detected role into `v2_receipt.relationship_resolution.role` whenever FKR resolves a target with `role` set via `forum_relationship_edges` — so the orchestration plan and the intent-v2 enforcement copy agree with the FKR evidence block. |
| 2 | P0 | S | Add `forum_relationship_edges` as the **first** lookup source in `relationship_resolver.resolve_relationship()`, before `relationship_mappings`. |
| 3 | P0 | M | Backfill `forum_relationship_edges` with `parent`/`child` edges for Pete↔Thaddeus and Pete↔Isaac (or expose a one-shot admin endpoint to create them from `forum_members` + birth-date deltas, with `confidence=manual`). |
| 4 | P1 | S | Expand `classify_query()` patterns in `forum_chat_knowledge_retrieval.py` to cover: <br>· `\b(\w+) and I\b` → RELATIONSHIP <br>· `\bwhat does .* need\b` → RELATIONSHIP <br>· `\bhow is \w+ different from\b` → COMPARISON <br>· `\bwho (balances|complements|tensions?)\b` → FORUM_DYNAMICS <br>· `\bblind ?spot\b`, `\bthis group\b` → FORUM_DYNAMICS |
| 5 | P2 | M | Group resolution: when message contains `the boys / the kids / my kids / the team`, expand targets to the asker's children/team members from the family forum. |
| 6 | P3 | M | Add `sibling_pair` (and `forum_pair`) bucket to `LENS_MODULATIONS` with relationship +0.30 / human_design +0.25 / enneagram +0.15 modulations. |
| 7 | P3 | M | Inject the orchestration plan's `framing_hint` and `domain_bias` into the FKR enforcement footer (so the strong MANDATORY copy is also role-aware, not just the gated soft hint line). |

### B.2 · Acceptance gate for ungating

After fixes 1–4 land, re-run
`backend/scripts/p3_relationship_readiness_assessment.py` and require:

- **Retrieval ≥ 10/10**
- **Target resolution ≥ 10/10**
- **Relationship resolution ≥ 8/10** (10/10 once family edges are backfilled)
- **Orchestration bucket ≥ 8/10**
- **Prompt construction ≥ 10/10**
- **Mode overlap ≥ 8/10**

Only then is it safe to flip `RELATIONSHIP_ORCHESTRATION_PROMPT=true`.

### B.3 · Why NOT recommendation A (ungate now)

The single most important observation in this assessment is **Gap 3**:
turning the flag on right now would surface
`"Suggested framing: forum_member_dynamic"` for the canonical
spouse question ("How does Mel affect me?"). That is an *actively
misleading* signal — directly contradicting the `Mel (spouse)` entry
the FKR block already injects. The LLM would have to arbitrate, and
historical Phase-3 evidence (cf. INTELLIGENCE_ACTIVATION_SPRINT_REPORT)
shows directive `"Suggested:"` lines win out over body context. We
would *regress* the spouse path.

### B.4 · Why NOT recommendation C (never ungate)

The architecture is sound. The data layer (`forum_relationship_edges`)
already exists. The orchestration service supports all 16 role buckets.
The only thing standing between the current 2/10 and a healthy ≥8/10
is **wiring** (Gap 1, Gap 3) and **data backfill** (Gap 2). None of it
requires touching calculators, birth data, HD logic, astrology,
timeline, or rollout flags.

---

## 6. Constraints honoured

- ✅ No calculator changes.
- ✅ No astrology changes.
- ✅ No HD changes.
- ✅ No timeline changes.
- ✅ No incarnation-cross logic changes.
- ✅ No birth-data changes.
- ✅ All four rollout flags untouched.
- ✅ No ungating performed.
- ✅ Only a read-only probe was added (no instrumentation in production paths).

## 7. Artifacts

- `/app/backend/scripts/p3_relationship_readiness_assessment.py` — replayable probe.
- `/app/backend/audit_reports/P3_READINESS_ASSESSMENT.json` — raw output.
- `/app/backend/audit_reports/P3_RELATIONSHIP_ORCHESTRATION_READINESS.md` — this report.
