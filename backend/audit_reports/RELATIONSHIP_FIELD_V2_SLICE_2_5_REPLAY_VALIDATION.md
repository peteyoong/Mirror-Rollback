# Relationship Field V2 — Slice 2.5 Replay Validation

**Date:** 2026-06-14
**Status:** Slice 2.5 complete. **All stance invariants hold across all
phrasings.** Awaiting approval before Slice 3.

---

## 1. Goal

Prove the resolver remains stable across **real-world spouse and
child queries** before any prompt influence is introduced (Slice 3).

Per user directive:

> Mel always resolves to `covenant_partner`.
> Thaddeus always resolves to `steward_guardian`.
> Isaac always resolves to `steward_guardian`.
>
> No prompt changes. No flag changes. No frontend changes.

## 2. Test Matrix

**Viewer:** Pete (`697f0c6abf35c0528ff06954`)
**Targets:** 3 family members from the live edge graph
**Phrasings:** 5 real-world query variations
**Total turns:** 3 × 5 = **15 live `POST /api/mirror/chat` calls**

| Target   | id (truncated) | Expected role | Expected stance     |
| -------- | -------------- | ------------- | ------------------- |
| Mel      | 697ec826…      | spouse        | `covenant_partner`  |
| Thaddeus | 69dd0b2c…      | child         | `steward_guardian`  |
| Isaac    | 69dda348…      | child         | `steward_guardian`  |

```
1. Tell me about {name}.
2. What does {name} need from me?
3. How does {name} experience me?
4. What am I missing about {name}?
5. What is happening between {name} and I today?
```

## 3. Files Added (additive only)

```
A  /app/backend/services/test_slice_2_5_replay_validation.py
   ↳ 1 module fixture + 6 acceptance tests
A  /app/backend/audit_reports/SLICE_2_5_REPLAY_RUN.json
   ↳ Structured per-turn capture (15 rows)
A  /app/backend/audit_reports/RELATIONSHIP_FIELD_V2_SLICE_2_5_REPLAY_VALIDATION.md
   ↳ This document
```

No service or router code touched. `mirror_chat.py`, `relationship_field_v2.py`,
and all frontend files are unchanged.

## 4. Test Results

```
$ cd /app/backend && python -m pytest services/test_slice_2_5_replay_validation.py -v
============================== test session starts ==============================
collected 6 items

test_acceptance_stance_invariants          PASSED [ 16%]
test_acceptance_role_invariants            PASSED [ 33%]
test_acceptance_target_binding             PASSED [ 50%]
test_acceptance_high_confidence_source     PASSED [ 66%]
test_acceptance_directionality_invariants  PASSED [ 83%]
test_acceptance_endpoint_health            PASSED [100%]

========================= 6 passed in 77.54s ===================================
```

15 turns / 77.54 s ≈ 5.2 s per turn end-to-end (including LLM round-trip,
receipt persistence, and replay verification).

## 5. Per-Target Aggregation (from `SLICE_2_5_REPLAY_RUN.json`)

| Target    | turns | stances observed       | roles observed | directionality   | sources                     | confidences | primary_domains             | FKR signal |
| --------- | :---: | ---------------------- | -------------- | ---------------- | --------------------------- | ----------- | --------------------------- | :--------: |
| Mel       | 5     | `{covenant_partner}`   | `{spouse}`     | `{SYMMETRIC}`    | `{forum_relationship_edges}` | `{0.95}`    | `{relationship}`            | ✅ (5/5)    |
| Thaddeus  | 5     | `{steward_guardian}`   | `{child}`      | `{USER_AS_GIVER}`| `{forum_relationship_edges}` | `{0.95}`    | `{relationship, career}` *  | ✅ (5/5)    |
| Isaac     | 5     | `{steward_guardian}`   | `{child}`      | `{USER_AS_GIVER}`| `{forum_relationship_edges}` | `{0.95}`    | `{relationship, career}` *  | ✅ (5/5)    |

\* Domain drift across phrasings is **expected** and **does not affect
stance**. See §7 for the analysis — stance is sourced from the edge
graph, not from the life-domain classifier, so the classifier's
sensitivity to phrasing tokens like "need from me" / "happening" does
not propagate into the resolver.

**Zero stance drift.** Every Mel turn → `covenant_partner`. Every
Thaddeus and Isaac turn → `steward_guardian`. Stance is **phrasing-
invariant** by construction (the resolver short-circuits on
`about_person_id` → edges → core stance map).

## 6. Sample Row (Turn 1 — Mel · "Tell me about Mel.")

```jsonc
{
  "turn": 1,
  "target": "Mel",
  "phrasing": "Tell me about Mel.",
  "request_id": "mc-13143f2a-5d2e-4e28-812a-ceae88f268d7",

  // router output
  "primary_domain": "relationship",
  "signal_strength": 1.0,
  "margin": 0.6364,
  "lens_priority": ["relationship","astrology","human_design",
                    "enneagram","timeline","numerology"],

  // legacy resolver (the old machinery, side-by-side)
  "rel_resolution_source": null,
  "rel_resolution_role":   null,

  // FKR signal (heuristic from receipt)
  "fkr_signal_present": true,

  // RFv2 envelope — the new canonical layer
  "rfv2_target_user_id": "697ec826ad4b18f75bf42616",
  "rfv2_target_name":    "Mel",
  "rfv2_role":           "spouse",
  "rfv2_stance":         "covenant_partner",
  "rfv2_directionality": "SYMMETRIC",
  "rfv2_active_frame":   "MEMBER",
  "rfv2_source":         "forum_relationship_edges",
  "rfv2_confidence":     0.95,
  "rfv2_conflicts":      [],
  "rfv2_resolution_path": [
    "hint:explicit_about_person_id",
    "legacy_src:forum_relationship_edges",
    "stance:core:spouse->covenant_partner"
  ],

  "expected_role":   "spouse",
  "expected_stance": "covenant_partner"
}
```

All 15 rows are persisted in `/app/backend/audit_reports/SLICE_2_5_REPLAY_RUN.json`.

## 7. Observation — Domain Drift vs Stance Stability

Across the 5 child phrasings, the `intent_envelope.primary_domain`
varied:

| phrasing                                       | Thaddeus domain | Isaac domain |
| ---------------------------------------------- | :-------------: | :----------: |
| "Tell me about X."                             | relationship    | relationship |
| "What does X need from me?"                    | relationship    | relationship |
| "How does X experience me?"                    | **career**      | **career**   |
| "What am I missing about X?"                   | relationship    | relationship |
| "What is happening between X and I today?"     | relationship    | relationship |

The "experience me" phrasing tripped the classifier into `career`
because of the experience/work token in the lexicon. **This is exactly
the kind of drift Slice 3 will fix** — the prompt will lock to the
RFv2 stance regardless of the noisy classifier output.

For Slice 2.5 this is a **green flag**, not a failure: it proves the
new resolver is **independent** of the domain classifier and survives
its mis-classifications without losing the parenting frame.

## 8. Constraints Audit

| Requirement (per Slice 2.5 directive)         | Status |
| --------------------------------------------- | :----: |
| No prompt changes                             | ✅ (only test code added) |
| No flag changes                               | ✅ (all 4 flags untouched) |
| No frontend changes                           | ✅ (no FE files touched) |
| Run replay against Mel, Thaddeus, Isaac       | ✅ (15 turns) |
| Capture relationship_field_v2                 | ✅ (per-turn) |
| Capture relationship_resolution               | ✅ (per-turn) |
| Capture router output                         | ✅ (intent_envelope) |
| Capture FKR signal                            | ✅ (heuristic) |
| Capture life_domain                           | ✅ (primary_domain) |
| Capture target / role / stance                | ✅ (per-turn) |
| Mel always → covenant_partner                 | ✅ (5/5 turns) |
| Thaddeus always → steward_guardian            | ✅ (5/5 turns) |
| Isaac always → steward_guardian               | ✅ (5/5 turns) |

## 9. Test Suite — Combined State (Slices 1 + 2 + 2.5)

| Suite                                                | Tests | Result   |
| ---------------------------------------------------- | :---: | :------: |
| `services/test_relationship_field_v2.py` (Slice 1)   | 9     | 9 PASS   |
| `services/test_slice_2_ask_mirror_wiring.py` (S2)    | 7     | 7 PASS   |
| `services/test_slice_2_5_replay_validation.py` (S2.5) | 6   | 6 PASS   |
| **Total**                                            | **22**| **22 PASS** |

## 10. Hold Point — Slice 3 Pre-conditions

Slice 2.5 stops here. **Awaiting explicit approval before Slice 3
prompt injection.**

Per user directive, when Slice 3 begins:

- A **brand new** dedicated flag will be introduced: `RELATIONSHIP_FIELD_V2_PROMPT`
- The existing `RELATIONSHIP_ORCHESTRATION_PROMPT` flag will **NOT** be
  reused.
- The new flag defaults to `false`. No prompt change ships until the
  flag is explicitly flipped to `true` for an internal cohort.

Proposed Slice 3 prompt-section shape (NOT yet built):

```
=== RESOLVED RELATIONSHIP FIELD ===
Frame:          {active_frame}
Target:         {target_name}  ({target_user_id|short})
Role:           {relationship_role}
Stance:         {relationship_stance}
Directionality: {directionality}
Closeness:      {closeness} · weight {emotional_weight}
Forum context:  {forum_name|none}
Confidence:     {confidence} · source: {resolution_source}
=== END RESOLVED RELATIONSHIP FIELD ===
```

Insertion point: replaces today's soft "Relationship target: bound
(role: X)" line in `build_intent_v2_prompt_block`, but ONLY when the
new flag is on AND stance ∉ {`neutral`, `self_subject`} (per the
audit's no-dead-letter rule).

No coding on Slice 3 until you approve:
1. The prompt-section structure above
2. The flag name and default value
3. The gate conditions (which stances are allowed to fire the block)

**Atlas access:** still blocked pending IP whitelist. All Slice 2.5
turns ran against `localhost:27017 / test_database`. No production
claims fabricated.
