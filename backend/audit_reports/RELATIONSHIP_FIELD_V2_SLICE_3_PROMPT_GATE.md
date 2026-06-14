# Relationship Field V2 — Slice 3 Prompt Gate Delivery

**Date:** 2026-06-14
**Status:** Slice 3 complete. **Flag remains OFF in committed state.**
Awaiting approval before Slice 4 (Forum Chat wiring).

---

## 1. Scope (verbatim user directive)

> Add a small, controlled RESOLVED RELATIONSHIP FIELD prompt section
> to **Ask Mirror only**, gated by a brand-new dedicated flag:
>
> ```
> RELATIONSHIP_FIELD_V2_PROMPT=false   (default)
> ```
>
> Do **NOT** reuse `RELATIONSHIP_ORCHESTRATION_PROMPT`.
> Do **NOT** wire Forum Chat / Astrology Chat / Relationship Insight V2
> / How They Map To Me.

## 2. Files Touched

```
A  /app/backend/services/relationship_field_v2_prompt.py
   └─ 158-line gated builder. Reads RELATIONSHIP_FIELD_V2_PROMPT on
      every call (no startup cache → flag flips at runtime).
M  /app/backend/.env
   └─ +RELATIONSHIP_FIELD_V2_PROMPT=false   (NEW LINE)
   └─ INTENT_ROUTER_V2_CUTOVER             unchanged (false)
   └─ INTENT_ROUTER_V2_ROLLOUT_PERCENT     unchanged (10)
   └─ RELATIONSHIP_ORCHESTRATION_PROMPT    unchanged (false)
   └─ CROSS_LENS_PROMPT_SURFACE            unchanged (false)
M  /app/backend/routers/mirror_chat.py
   └─ ~38-line block inserted immediately after the existing
      build_intent_v2_prompt_block invocation.
A  /app/backend/services/test_slice_3_prompt_gate.py
   └─ 11 unit tests (flag/conf/source/conflict/stance-shape) + 1 live
      "flag OFF" smoke test = 12 tests
A  /app/backend/audit_reports/RELATIONSHIP_FIELD_V2_SLICE_3_PROMPT_GATE.md
   (this file)
```

`MirrorChatRequest` schema **unchanged**. Frontend **unchanged**.
Forum Chat / Astrology Chat / Relationship Insight V2 / How They Map
To Me **untouched**.

## 3. Prompt Block (verbatim, as injected when gates pass)

```
RESOLVED RELATIONSHIP FIELD
Target: <name>
Role: <role>
Stance: <relationship_stance>
Directionality: <directionality>
Confidence: <confidence>
Source: <source>

Instruction:
Interpret this person through the relationship field above.
Do not ignore the relationship context.
Do not substitute a generic person profile when role/stance are high confidence.
```

For `stance == self_subject`, `Target:` is filled with
`(the user themselves)`.

## 4. Gates (in evaluation order)

| # | Gate                                                                | Skip reason emitted to phase4_debug                        |
| - | ------------------------------------------------------------------- | ---------------------------------------------------------- |
| 1 | `v2_receipt` exists                                                 | `no_v2_receipt`                                            |
| 2 | `v2_receipt.relationship_field_v2` is a dict                        | `no_rfv2_envelope`                                         |
| 3 | env `RELATIONSHIP_FIELD_V2_PROMPT == "true"` (case-insensitive)     | `flag_off`                                                 |
| 4 | `conflicts[]` is empty                                              | `conflicts_present:<n>`                                    |
| 5 | `resolution_source != "proposed_unresolved"`                        | `source_proposed_unresolved`                               |
| 6 | `resolution_source` ∈ allowed-list                                  | `source_not_allowed:'<src>'`                               |
| 7 | `confidence >= 0.70`                                                | `confidence_below_threshold:<conf> < 0.70`                 |

Allowed `resolution_source` (G3.3): `forum_relationship_edges`,
`saved_people`, `relationship_mappings`, `explicit_map` (V2 enum
alias for `relationship_mappings`), `self_no_target`.

## 5. Acceptance Evidence — Live Endpoint, Flag ON

Manually flipped `.env` to `true`, restarted backend, fired 5
scenarios, captured `[MIRROR_CHAT][RFv2-prompt]` log line, then
restored flag to `false` and restarted.

```
[RFv2-prompt] block_emitted=True   role=spouse  stance=covenant_partner   source=forum_relationship_edges  conf=0.95   ← Mel
[RFv2-prompt] block_emitted=True   role=child   stance=steward_guardian   source=forum_relationship_edges  conf=0.95   ← Thaddeus
[RFv2-prompt] block_emitted=True   role=child   stance=steward_guardian   source=forum_relationship_edges  conf=0.95   ← Isaac
[RFv2-prompt] block_emitted=False  flag_enabled=True   reason='source_proposed_unresolved'                              ← Patricia
[RFv2-prompt] block_emitted=True   role=self    stance=self_subject       source=self_no_target            conf=0.95   ← self
```

| Acceptance criterion (per user directive)                | Result |
| -------------------------------------------------------- | :----: |
| Mel emits covenant_partner block                         | ✅      |
| Thaddeus emits steward_guardian block                    | ✅      |
| Isaac emits steward_guardian block                       | ✅      |
| Patricia does NOT emit high-confidence block             | ✅      |
| self emits self_subject block                            | ✅      |

## 6. Acceptance Evidence — Live Endpoint, Flag OFF (default)

After restoring `.env` to `false` and restarting:

```
HTTP 200 OK
[RFv2-prompt] block_emitted=False  flag_enabled=False  reason='flag_off'
```

| Acceptance criterion                                            | Result |
| --------------------------------------------------------------- | :----: |
| With flag OFF, no prompt block emitted                          | ✅      |
| Endpoint still returns 200                                      | ✅      |
| Receipt still includes `relationship_field_v2`                  | ✅ (Slice 2 attachment intact) |
| Responses unchanged                                              | ✅ (same prompt path as pre-Slice-3 except for the now-skipped block) |

## 7. FKR + Evidence Drawer + Ophiuchus Regression

Backend log evidence (flag ON sample, all five lines belong to one
batch of test calls):

```
[evidence-drawer-v2] evidence_emitted=True keys=['marker','calibration']
[RFv2-prompt]        block_emitted=True role=child stance=steward_guardian source=forum_relationship_edges conf=0.95
[FKR-v1]             block_emitted=True modes=[] targets=['you','Thaddeus'] chars=5227
[FKR-v1]             role bridged into v2_receipt: name='Thaddeus' role='child'
```

| Existing surface                              | Status |
| --------------------------------------------- | :----: |
| FKR v1 block still emits                      | ✅ (chars=5194–5227) |
| FKR role bridge still fires                   | ✅      |
| Evidence drawer v2 still emits                | ✅      |
| Ophiuchus / Variant-A test suite              | ✅ **31/31 PASS** (`tests/test_variant_a_canonical.py` + `tests/test_ophiuchus_first_class.py`) |
| `intent_envelope` / `relationship_resolution` still present in receipt | ✅ |

## 8. Combined Test Suite State

```
$ cd /app/backend && python -m pytest \
    services/test_relationship_field_v2.py \
    services/test_slice_2_ask_mirror_wiring.py \
    services/test_slice_3_prompt_gate.py -v

============================== test session starts ==============================
collected 28 items

services/test_relationship_field_v2.py ............         9/9   PASS
services/test_slice_2_ask_mirror_wiring.py ..........       7/7   PASS
services/test_slice_3_prompt_gate.py ................      12/12  PASS

============================== 28 passed in 34.99s ============================
```

Plus the existing Variant-A / Ophiuchus suite:

```
tests/test_variant_a_canonical.py + tests/test_ophiuchus_first_class.py
    31 passed in 0.04s
```

## 9. Constraints Audit

| Constraint                                                          | Status |
| ------------------------------------------------------------------- | :----: |
| New dedicated flag `RELATIONSHIP_FIELD_V2_PROMPT`                   | ✅ Added (default `false`) |
| `RELATIONSHIP_ORCHESTRATION_PROMPT` NOT reused                      | ✅ (untouched; separate flag created) |
| Ask Mirror only                                                     | ✅ (no Forum / Astro / Insight V2 / Mappings wiring) |
| No frontend changes                                                 | ✅      |
| No DB writes                                                        | ✅ (no new collections, no new fields, no writes) |
| No migrations                                                       | ✅      |
| No prior-flag changes                                               | ✅ (4 prior flags untouched) |
| Flag remains OFF in committed state                                 | ✅ (`.env` reverted to `false` before this report was written) |
| Gate: confidence ≥ 0.70                                              | ✅ (G3.2 — tested) |
| Gate: allowed source list                                            | ✅ (G3.3 — tested) |
| Gate: never on proposed_unresolved                                   | ✅ (G3.4 — tested + live-observed) |
| Gate: blocked when conflicts[] non-empty                             | ✅ (G3.5 — tested) |

## 10. Flag State at End of Slice 3

```
$ grep RELATIONSHIP_FIELD_V2_PROMPT /app/backend/.env
RELATIONSHIP_FIELD_V2_PROMPT=false
```

The flag is **NOT enabled globally.** It can be flipped to `true` for
an internal cohort by:

```
1. Edit /app/backend/.env → RELATIONSHIP_FIELD_V2_PROMPT=true
2. sudo supervisorctl restart backend
3. (optional) flip back to false to disable
```

No DB / migration / frontend change is needed to toggle.

## 11. Hold Point — Slice 4 Pre-conditions

Slice 3 stops here. Awaiting your review of:

1. The prompt-block copy in §3 (final wording check)
2. The gate evaluation order in §4 (any additional gates you want?)
3. Whether to enable the flag for an internal cohort, or leave OFF
   pending Slice 4 wiring

Proposed Slice 4 work (NOT started):
- Wire `resolve_relationship_field()` into `routers/forums_chat.py`
  the same way it landed in `routers/mirror_chat.py` — attach to
  forum chat's own receipt, gate the same prompt block behind the
  same `RELATIONSHIP_FIELD_V2_PROMPT` flag.
- Add forum-specific gate: only emit when forum_topology is supplied
  and active_member_id resolves to a high-confidence target.

No coding on Slice 4 until you approve. Atlas access remains blocked.
