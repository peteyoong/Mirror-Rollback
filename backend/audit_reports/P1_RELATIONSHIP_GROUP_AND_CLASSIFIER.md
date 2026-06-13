# P1 Relationship Orchestration Readiness — Group Resolution + Classifier Expansion

**Date:** 2026-06-13
**Status:** ✅ ALL ACCEPTANCE TARGETS EXCEEDED
**Scope:** Display/rendering & query-classification layer only. No
calculators, astrology, Human Design, timeline, incarnation-cross,
birth data, rollout flags, orchestration ungating, new collections, or
schema migrations were touched.

All four rollout flags **verified untouched** at end of sprint:
```
INTENT_ROUTER_V2_CUTOVER=false
INTENT_ROUTER_V2_ROLLOUT_PERCENT=10
RELATIONSHIP_ORCHESTRATION_PROMPT=false
CROSS_LENS_PROMPT_SURFACE=false
```

---

## 1. Before / After scores

| Dimension                  | Before P0 | After P0 | **After P1 (this sprint)** | Acceptance target |
|----------------------------|-----------|----------|----------------------------|-------------------|
| Retrieval                  | 9 / 10    | 9 / 10   | **12 / 12 ✅**             | 10/10 |
| Target resolution          | 10 / 10   | 10 / 10  | **12 / 12 ✅**             | — |
| Relationship resolution    | 4 / 10    | 10 / 10  | **12 / 12 ✅**             | 10/10 |
| Orchestration bucket       | 4 / 10    | 10 / 10  | **12 / 12 ✅**             | 10/10 |
| Prompt construction        | 9 / 10    | 9 / 10   | **12 / 12 ✅**             | 10/10 |
| Mode overlap               | 4 / 10    | 4 / 10   | **12 / 12 ✅**             | ≥ 8/10 |
| **Overall scenarios PASS** | **2 / 10**| 4 / 10   | **12 / 12 ✅**             | ≥ 8/10 |

Two new scenarios were added (`child_child.more_like_me`,
`family.our_family`) for the new capabilities introduced in this sprint
— hence the denominator grew from 10 to 12. The previous denominator
of 10 also now all PASS.

**FKR v1 regression:** 5/5 still PASS — Thaddeus's Incarnation Cross
still returns "Right Angle Cross of Sleeping Phoenix" with zero
"Sphinx" leakage.

---

## 2. Files touched

| Path | Type | Purpose |
|---|---|---|
| `backend/services/forum_chat_knowledge_retrieval.py` | edit | (a) Classifier expansion — 5 modes gained ≥1 new pattern. (b) Group/plural target resolution — "the boys", "my kids", "the children", "which child", "our family", … expand to the underlying `forum_relationship_edges`-typed people. |
| `backend/scripts/p3_relationship_readiness_assessment.py` | edit | Added two new scenarios (`child_child.more_like_me`, `family.our_family`) and updated existing `child_child.boys_differ` expectation to require group expansion. |
| `backend/audit_reports/P3_READINESS_AFTER_P1_FIX.json` | new | Raw probe output (12/12). |
| `backend/audit_reports/P1_RELATIONSHIP_GROUP_AND_CLASSIFIER.md` | new (this file) | Implementation + acceptance. |

No new collections. No schema migrations. No calculator changes. No
prompt-copy changes. No flag changes.

---

## 3. Section A — Group / plural target resolution

`resolve_targets()` now post-processes the message with two precompiled
regex groups, fired AFTER alias matching so they never duplicate an
already-resolved person:

```python
GROUP_PATTERNS = {
    "children": re.compile(
        r"\b("
        r"the boys|my boys|both boys|"
        r"the kids|my kids|both kids|"
        r"the children|my children|the babies|my babies|"
        r"both children|both of them|my offspring|"
        r"which child|which kid|which boy|which girl|"
        r"which one of (the|my) (kids|children|boys|girls)|"
        r"which of (the|my) (kids|children|boys|girls)"
        r")\b",
        re.IGNORECASE,
    ),
    "family": re.compile(
        r"\b(our family|the family|my family)\b",
        re.IGNORECASE,
    ),
}
```

When `children` matches, `_expand_group(["child"])` queries
`forum_relationship_edges` from `asker → *` where `role_type="child"`
and appends each previously-unmatched person to the targets list with
`source="group_expansion"`.

When `family` matches, the same helper is called with the kinship
filter `["spouse","child","parent","sibling"]` — explicitly excluding
non-kin forum members so "the family" cannot pull in an in-law's
acquaintance who happens to share a forum.

### Examples (live probe)

| Phrase | Resolved targets |
|---|---|
| `"How do the boys differ emotionally?"` | **Thaddeus, Isaac** (from `forum_relationship_edges.role_type=child`) |
| `"Which child is more like me?"` | **Thaddeus, Isaac** |
| `"What is happening in our family?"` | **Mel (spouse), Thaddeus, Isaac (children)** |
| `"How does Mel affect me?"` | Mel (unchanged — alias match, no group expansion) |
| `"How does Jay affect me?"` | (empty — Jay not in the graph; correctly reports stranger) |

All group-expanded targets carry the `role` from the edge graph, so
downstream the orchestration plan, the FKR evidence block, and the
intent-v2 enforcement copy all see the correct kinship role for each
person.

---

## 4. Section B — Classifier expansion

`classify_query()` now multi-labels the following natural phrasings:

### RELATIONSHIP
- `\b\w+ and i\b` · `\b\w+ and me\b` ("Mel and I struggle…")
- `\bwhat does \w+ need from (me|us)\b`
- `\bhow is \w+ different from (me|us)\b`
- `\bwhat keeps happening between\b`
- `\bwhat (do|are) we (struggle|fight|argue|repeat)\b`
- `\bwhat are we repeating\b` · `\bwhat are we working through\b`

### COMPARISON
- `\bhow is \w+ different from\b`
- `\bhow do .* differ\b` ("How do the boys differ", "how do my kids differ")
- `\bwhich (one|child|kid|boy|girl|of \w+) is more\b`
- `\bmore like (me|you|us)\b`
- `\bwhich (\w+) (challenges|tests|stretches) me\b`
- `\bstrengths complement\b`

### FORUM_DYNAMICS
- `\bwho (balances|complements|grounds|steadies|tensions?)\b`
- `\bwho creates (the )?(most )?tension\b`
- `\bwhat is (this|the|our) (group|family|team|forum)'?s? blind ?spot\b`
- `\bblind ?spot\b` · `\bthis group\b` · `\bthis forum\b` · `\bthis (family|team)\b`
- `\bwhat role does \w+ play\b`

### INTERPRETATION
- `\bwhat does .+ need from (me|us)\b` (multi-labelled with RELATIONSHIP)

### Examples (live probe)

| Message | Classified modes |
|---|---|
| `"What do Mel and I struggle with?"` | RELATIONSHIP |
| `"What does Thaddeus need from me?"` | INTERPRETATION, RELATIONSHIP |
| `"How is Isaac different from me?"` | RELATIONSHIP, COMPARISON |
| `"Compare Isaac and Thaddeus."` | COMPARISON |
| `"How do the boys differ emotionally?"` | COMPARISON |
| `"Which child is more like me?"` | COMPARISON |
| `"What is happening in our family?"` | FORUM_DYNAMICS |
| `"Who balances Mel best?"` | FORUM_DYNAMICS |
| `"What is this group's blind spot?"` | FORUM_DYNAMICS |

All previously-empty mode sets now resolve to at least one (often two)
modes, so the FKR enforcement copy is fully mode-aware.

---

## 5. Section C — Sibling-pair awareness

Sibling-pair behaviour is achieved without introducing any new
orchestration bucket (P3 backlog item retained). The mechanism:

1. **Both children resolve as targets.** "Compare Isaac and Thaddeus",
   "How do the boys differ", "Which child is more like me" all return
   `[Isaac, Thaddeus]` with `role=child` (from the canonical edge
   graph).
2. **FKR evidence block carries both profiles.** Each child gets a
   full HD/Astrology/Numerology/Enneagram/Timeline section labelled
   `Thaddeus (child)` and `Isaac (child)` so the LLM cannot lose
   either side. The asker `(you)` block precedes them — preserving the
   **parent frame** because Pete is the user the message is being
   answered for.
3. **Orchestration bucket = `child`.** Because both targets share
   `role=child`, the plan_lens_priority computation picks the `child`
   bucket and applies the parenting-focused lens re-rank
   (human_design +0.30, enneagram +0.25, relationship +0.20). No
   collapse to `forum_member`.
4. **No prompt copy changed.** The MANDATORY enforcement footer in the
   FKR block already says "Use the EXACT stored value" and "For
   RELATIONSHIP/COMPARISON, name both targets and contrast values side
   by side." — which is exactly what a sibling comparison needs.

---

## 6. Section D — Verification

`backend/scripts/p3_relationship_readiness_assessment.py` was re-run
**unchanged in its scoring logic**; only the scenario list grew (two
additions for newly-supported capabilities, one expectation update for
the now-resolving `boys_differ` scenario).

### 12/12 PASS — scenario-by-scenario

| Scenario | Modes | Targets | Role | Bucket | PASS |
|---|---|---|---|---|---|
| `spouse.affect`            | RELATIONSHIP                 | Mel              | spouse | spouse | ✅ |
| `spouse.struggle`          | RELATIONSHIP                 | Mel              | spouse | spouse | ✅ |
| `spouse.lesson_pronoun`    | RELATIONSHIP                 | Mel              | spouse | spouse | ✅ |
| `child.thaddeus_need`      | INTERPRETATION, RELATIONSHIP | Thaddeus         | child  | child  | ✅ |
| `child.isaac_diff`         | RELATIONSHIP, COMPARISON     | Isaac            | child  | child  | ✅ |
| `child_child.compare`      | COMPARISON                   | Thaddeus, Isaac  | child  | child  | ✅ |
| `child_child.boys_differ`  | COMPARISON                   | Thaddeus, Isaac  | child  | child  | ✅ |
| `child_child.more_like_me` | COMPARISON                   | Thaddeus, Isaac  | child  | child  | ✅ |
| `family.our_family`        | FORUM_DYNAMICS               | Mel, Thaddeus, Isaac | spouse | spouse | ✅ |
| `forum_member.jay`         | RELATIONSHIP                 | ∅ (stranger)     | None   | self   | ✅ |
| `forum_dyn.balance`        | FORUM_DYNAMICS               | Mel              | spouse | spouse | ✅ |
| `forum_dyn.blind_spot`     | FORUM_DYNAMICS               | ∅                | None   | forum_member | ✅ |

### Score dimensions

```
retrieval:                12 / 12  ✅
target_resolution:        12 / 12  ✅
relationship_resolution:  12 / 12  ✅
orchestration_bucket:     12 / 12  ✅
prompt_construction:      12 / 12  ✅
modes_overlap:            12 / 12  ✅
```

### Acceptance target

| Required | Achieved |
|---|---|
| Retrieval ≥ 10/10 | **12/12** ✅ |
| Prompt construction ≥ 10/10 | **12/12** ✅ |
| Relationship resolution ≥ 10/10 | **12/12** ✅ |
| Orchestration bucket ≥ 10/10 | **12/12** ✅ |
| Mode overlap ≥ 8/10 | **12/12** ✅ |
| Overall scenario PASS ≥ 8/10 | **12/12** ✅ |

All six acceptance bars met or exceeded.

---

## 7. Constraints honoured

- ✅ No calculator changes.
- ✅ No astrology / HD / timeline / incarnation-cross logic changes.
- ✅ No prompt-copy modifications (FKR enforcement footer untouched;
  no new system-prompt lines added).
- ✅ No new intelligence systems introduced (only existing edges read).
- ✅ No flag changes; no ungating; no rollout.
- ✅ All four locked flags verified untouched at `/app/backend/.env`.
- ✅ No new collections, no schema migrations.

## 8. Regression status

- ✅ FKR v1 deterministic probes: 5/5 PASS (Sleeping Phoenix preserved).
- ✅ Backend health: `/api/health` returns 200 healthy.
- ✅ HD Incarnation Cross renderer: still emits distinct cards per
  family.
- ✅ Spouse / child role resolution from P0 still 10/10.

## 9. Open backlog (unchanged from previous report)

- **P3** — Add `sibling_pair` bucket to `LENS_MODULATIONS` (currently
  child-bucket is being reused, which is functional but
  not semantically differentiated). Optional polish.
- **P3** — Propagate the orchestration plan's `framing_hint` and
  `domain_bias` into the FKR MANDATORY footer (currently the gated
  flag's "Suggested framing" line is the only place these surface).
- **P0-A** — Astrology Angle Staleness (unrelated; still awaiting
  remediation design).

## 10. Re-run

```bash
cd /app/backend && python scripts/p3_relationship_readiness_assessment.py
# 12/12 PASS expected

cd /app/backend && python scripts/fkr_v1_acceptance_probes.py
# 5/5 PASS expected

grep -E "INTENT_ROUTER_V2_CUTOVER|INTENT_ROUTER_V2_ROLLOUT_PERCENT|RELATIONSHIP_ORCHESTRATION_PROMPT|CROSS_LENS_PROMPT_SURFACE" /app/backend/.env
# All four still =false / =10 as required.
```
