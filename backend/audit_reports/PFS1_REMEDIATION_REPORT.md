# PFS-1 Remediation — Deliverable Report

| | |
|---|---|
| Date | 2026-06-12 |
| Source of truth | `/app/backend/audit_reports/PRODUCTION_FIDELITY_SPRINT_PFS1.md` |
| Defects fixed | Defect 1 (`"Mel and I"` → forum_member), Defect 2 (cofounder pairs → false partner) |
| Files modified | `services/mirror_chat_phase4_enrichment.py` (classifier + R3b sort priority + prompt-block whitelist) |
| Files added | `tests/test_classify_forum_source.py` (55 unit tests) |
| Files NOT modified | rollout flags, cutover flag, P3 / cross-lens / orchestration flags, timezone migration, Variant A, any production / preview data |

---

## 1. Before / After Classifier Table

The exact production forum names supplied in the audit + the existing preview fixture, run against `_classify_forum_source` before and after the PFS-1 patch:

| forum_name           | BEFORE source / role        | AFTER source / role          | Status |
|----------------------|-----------------------------|------------------------------|--------|
| `Mel and I`          | **forum_member / None**     | **pair_forum / partner**     | ✅ Defect 1 fixed |
| `Pete & Mel`         | pair_forum / **partner**    | pair_forum / **None**        | ✅ Safe default (no romantic assertion on ambiguous pair) |
| `Mel & Pete`         | pair_forum / **partner**    | pair_forum / **None**        | ✅ Safe default |
| `Lu/Pere`            | pair_forum / **partner**    | pair_forum / **None**        | ✅ Defect 2 fixed — no false romantic role on cofounder pair |
| `Pete/Ana`           | pair_forum / **partner**    | pair_forum / **None**        | ✅ Defect 2 fixed |
| `Nic & Pete`         | pair_forum / **partner**    | pair_forum / **None**        | ✅ Defect 2 fixed |
| `Yoong Family`       | family_forum / family       | family_forum / family        | ✅ Unchanged (already correct) |
| `Yoong family`       | family_forum / family       | family_forum / family        | ✅ Unchanged |
| `Pulsifi Leadership` | forum_member / None         | **business_forum / None**    | ✅ More specific source; LLM gets group context |

**Key semantic change**: the safe default for an *ambiguous third-party pair* (e.g. `Pete & Mel` in preview, `Lu/Pere` / `Pete/Ana` / `Nic & Pete` in production) is now `role=None` rather than `role=partner`. The romantic role is only asserted when there is an *explicit signal* — either the canonical self-reference pattern (`<name> and I`, `<name> & I`, `Me and <name>`) or an explicit romantic keyword (`love`, `spouse`, `wife`, `husband`, `marriage`, …).

---

## 2. Unit Tests

**Location**: `/app/backend/tests/test_classify_forum_source.py`
**Total tests**: 55
**Result**: **55 passed, 0 failed, 0 skipped** (0.04s)

### Coverage breakdown

| Group | Cases | What it asserts |
|---|---|---|
| Defect 1 — self-token pair is romantic | 10 + 4 | `Mel and I`, `Mel & I`, `Mel + I`, `Mel/I`, `Pete and I`, `Pete & I`, `I and Mel`, `I & Mel`, case-insensitive variants `mel and i`, `MEL AND I`, plus `Me and Mel`, `Me & Mel`, `Mel and Me`, `Mel & Me` → all `pair_forum/partner` |
| Defect 2 — third-party pair has no romantic role | 8 | `Lu/Pere`, `Pete/Ana`, `Nic & Pete`, `Pete + Ana`, `Lu and Pere`, `Lu+Pere`, `Pete & Mel`, `Mel & Pete` → all `pair_forum/None` |
| Family forum | 5 | `Yoong Family`, `Yoong family`, `Yoong Fam`, `Family Yoong`, `The Smith Family Forum` → all `family_forum/family` |
| Business forum (non-pair) | 8 | `Pulsifi Leadership`, `Acme Cofounders`, `Pulsifi Founders`, `Pulsifi Team`, `The Pulsifi Exec Board`, `Acme Executives`, `Pulsifi Leadership Circle`, `Acme Holdings` → all `business_forum/None` |
| Generic forum_member | 5 | `Tuesday Reflection Circle`, `Yoga Group`, `Coffee Crew`, `Reading Club`, `Reflection Space` → all `forum_member/None` |
| Edge cases | 4 + 1 | empty/whitespace/None → `forum_member/None`; family-token wins over pair-shape |
| Authorization spec table | 8 | Direct reproduction of the 8 entries in the user's PFS-1 spec |
| Aspirational stubs | 2 | Documented limitations on qualifier-suffix names (e.g. `"Lu/Pere Cofounders"`); explicit comment explaining the trade-off |

### Run output (last 12 lines)

```
tests/test_classify_forum_source.py::test_pfs1_authorization_spec_table[Mel and I-pair_forum-partner] PASSED
tests/test_classify_forum_source.py::test_pfs1_authorization_spec_table[Pete & Mel-pair_forum-None] PASSED
tests/test_classify_forum_source.py::test_pfs1_authorization_spec_table[Mel & Pete-pair_forum-None] PASSED
tests/test_classify_forum_source.py::test_pfs1_authorization_spec_table[Lu/Pere-pair_forum-None] PASSED
tests/test_classify_forum_source.py::test_pfs1_authorization_spec_table[Pete/Ana-pair_forum-None] PASSED
tests/test_classify_forum_source.py::test_pfs1_authorization_spec_table[Nic & Pete-pair_forum-None] PASSED
tests/test_classify_forum_source.py::test_pfs1_authorization_spec_table[Yoong Family-family_forum-family] PASSED
tests/test_classify_forum_source.py::test_pfs1_authorization_spec_table[Pulsifi Leadership-business_forum-None] PASSED
============================== 55 passed in 0.04s ==============================
```

---

## 3. Live Probe Traces (POST /api/mirror/chat)

Four live calls run after restart against the preview backend with the canonical Pete (`697f0c6abf35c0528ff06954`), all returning HTTP 200 and persisting receipts via the R3b telemetry-fix path:

### Probe 1 — `Tell me about Mel` (uses preview fixture `Pete & Mel`)

Persisted receipt fields:
```
target_resolution_source = pair_forum
forum_fallback.found     = True
forum_fallback.source    = pair_forum
forum_fallback.role      = None             ← was 'partner' before PFS-1
forum_fallback.name      = Mel
forum_fallback.forum     = Pete & Mel
relationship.role        = None             ← downstream consumer sees None
```

### Probe 2 — `How does Mel map to me?`
Identical resolution path to Probe 1.

### Probe 3 — `Tell me about Isaac` (uses `Yoong family`)

```
target_resolution_source = family_forum
forum_fallback.found     = True
forum_fallback.source    = family_forum
forum_fallback.role      = family
forum_fallback.name      = Isaac Yoong
forum_fallback.forum     = Yoong family
relationship.role        = family
```

### Probe 4 — `Tell me about Thaddeus`

```
target_resolution_source = family_forum
forum_fallback.found     = True
forum_fallback.source    = family_forum
forum_fallback.role      = family
forum_fallback.name      = Thaddeus Yoong
forum_fallback.forum     = Yoong family
relationship.role        = family
```

**Note**: preview's pair forum is named `Pete & Mel` (no self-token), so under the new safe-default rule the relationship role correctly **degrades to `None`** rather than asserting a romantic frame. **In production**, the canonical user-coined name is `Mel and I` — which carries the self-token `I` and *would* produce `role=partner`. See §4 for the static proof.

---

## 4. Confirmation: `Mel and I` Resolves Correctly

Direct evaluation of `_classify_forum_source` against the production forum-name string (the only signal available without production data access):

```python
>>> _classify_forum_source("Mel and I")
('pair_forum', 'partner')

>>> _classify_forum_source("Mel & I")
('pair_forum', 'partner')

>>> _classify_forum_source("Pete and I")
('pair_forum', 'partner')

>>> _classify_forum_source("Me and Mel")
('pair_forum', 'partner')
```

When the production `forum_members` row for `Mel and I` is reached by `resolve_target_via_forums`, the prompt block emitted to the LLM will read:

> `Relationship target: 'Mel' (resolved via pair_forum in the 'Mel and I' forum (relationship_role: partner)). This person is in the user's saved relationship topology — ground your reflection in the actual relationship between them, not in generic projection language.`

The `partner` role is now surfaced **deterministically** to the LLM and to the persisted receipt for the canonical romantic-pair naming pattern.

**Confirmation**: ✅ Defect 1 remediated.

---

## 5. Confirmation: Cofounder / Business Pairs No Longer Emit Romantic Partner Role

Direct evaluation against the three named production cofounder pairs plus a generic ambiguous pair:

```python
>>> _classify_forum_source("Lu/Pere")
('pair_forum', None)

>>> _classify_forum_source("Pete/Ana")
('pair_forum', None)

>>> _classify_forum_source("Nic & Pete")
('pair_forum', None)

>>> _classify_forum_source("Pete + Ana")
('pair_forum', None)

>>> _classify_forum_source("Lu and Pere")
('pair_forum', None)
```

All five produce `role=None`. The prompt block builder uses the role optionally:

```python
role_part = f" (relationship_role: {tgt_role})" if tgt_role else ""
```

When `tgt_role` is `None`, **no `relationship_role` segment is appended** to the prompt. The LLM is told:

> `Relationship target: 'Pere' (resolved via pair_forum in the 'Lu/Pere' forum). This person is in the user's saved relationship topology — ground your reflection in the actual relationship between them, not in generic projection language.`

— with **no romantic / partner assertion**. The relationship type is left for the LLM to derive from the rest of the context (saved_people, timeline, founder context) rather than being pre-asserted by a name-shape heuristic.

**Confirmation**: ✅ Defect 2 remediated.

### Bonus — Pulsifi Leadership now classifies more specifically

```python
>>> _classify_forum_source("Pulsifi Leadership")
('business_forum', None)   # was: ('forum_member', None) before PFS-1
```

The new `business_forum` source is wired into the R3b priority ladder between `family_forum` (priority 1) and `forum_member` (priority 3) — see `_src_priority` in `resolve_target_via_forums`. When a candidate name matches a member of `Pulsifi Leadership`, the resolver surfaces the leadership/business context to the LLM with priority 2 (more specific than generic) but does not assert a per-member role.

---

## 6. Code Changes Summary

### `/app/backend/services/mirror_chat_phase4_enrichment.py`

Three changes — all additive:

1. **Pair regex extension** (`_PAIR_FORUM_NAME_RE`): second-group alternation now accepts the bare self-tokens `I` and `Me` in addition to proper-name shapes.
2. **New helper regexes**:
   - `_SELF_TOKEN_IN_PAIR_RE` — detects `I` / `Me` inside a pair name.
   - `_ROMANTIC_KEYWORD_RE` — explicit romantic markers (love, spouse, wife, husband, marriage, …).
   - `_BUSINESS_KEYWORD_RE` — cofounder / leadership / team / business markers.
3. **`_classify_forum_source` rewritten** as a 4-step ladder:
   - family-named → `family_forum/family`
   - pair-shaped + (self-token OR romantic kw) → `pair_forum/partner`
   - pair-shaped + business kw → `pair_forum/cofounder`
   - pair-shaped + ambiguous → `pair_forum/None`  (safe default)
   - non-pair + business kw → `business_forum/None`
   - else → `forum_member/None`

R3b `_src_priority` updated to include `business_forum=2`.

Prompt-block whitelist in `build_intent_v2_prompt_block` extended to include `business_forum` so the resolved-target block is emitted to the LLM for leadership/team forums.

### `/app/backend/tests/test_classify_forum_source.py`

New file. 55 pytest cases, all passing.

---

## 7. Constraint Compliance (re-verified at report-write time)

| Flag | Required | Actual | Modified during PFS-1 remediation? |
|---|---|---|---|
| `INTENT_ROUTER_V2_CUTOVER` | `false` | `false` | No |
| `INTENT_ROUTER_V2_ROLLOUT_PERCENT` | `10` | `10` | No |
| `RELATIONSHIP_ORCHESTRATION_PROMPT` | `false` | `false` | No |
| `CROSS_LENS_PROMPT_SURFACE` | `false` | `false` | No |
| `INTENT_V2_PROMPT_INJECTION` | `true` | `true` | No |
| `TIMELINE_V2_READ_ENABLED` | `true` | `true` | No |
| `FOUNDER_CONTEXT_ENABLED` | `true` | `true` | No |
| Timezone migration | unchanged | unchanged | No |
| Variant A | unchanged | unchanged | No |
| Production data | unchanged | unchanged | No |
| Preview data | unchanged | unchanged | No |
| User data | unchanged | unchanged | No |
| Forum membership | unchanged | unchanged | No |
| Saved_people | unchanged | unchanged | No |

No P3 / P5 / cross-lens / orchestration / rollout work performed. No data writes. Only code changes were to `services/mirror_chat_phase4_enrichment.py` and the new test file under `tests/`.

---

## 8. Known Limitations Surfaced (Not Fixed)

For your future-prioritisation review only — no action taken:

1. **Qualifier-suffix names** like `"Lu/Pere Cofounders"` or `"Mel and I (Married)"` do not match the strict pair regex anchors (`^token sep token$`). Two aspirational test stubs document this with a comment in `tests/test_classify_forum_source.py`. Resolving this requires either (a) relaxing the regex anchors or (b) sourcing forum-type from structured metadata.

2. **Forum-as-target queries** (e.g., _"What is happening in Pulsifi Leadership?"_) still cannot resolve: R3b matches member names, never forum names. PFS-1 explicitly scoped this out.

3. **Pete & Mel role regression** (preview-only): the existing preview fixture `Pete & Mel` was previously classified as `partner` and now classifies as `None`. This is by design — without a self-token or romantic marker, the safe default is to *not* assert a romantic role. In production, the equivalent forum is named `Mel and I`, which correctly receives `partner`. The preview regression is a test-fixture artefact, not a production regression.

---

## 9. Report Status

🛑 **Stopped for review.**

- Code patch: complete.
- Unit tests: 55/55 passing.
- Live probes: verified end-to-end (chat → R3b → prompt → receipt persistence).
- Production-data verification: still pending (this remains an environment-access blocker, not a code blocker).

Awaiting your direction on next priority (PFS-2 production-faithful probe execution, P3 / P5 ungating, or any other track).
