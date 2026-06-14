# Relationship Field V2 — Slice 1 Delivery Report

**Date:** 2026-06-14
**Status:** Slice 1 complete. Awaiting review before Slice 2 wiring.

---

## 1. Scope

User-approved Slice 1 (verbatim):

> Build canonical `resolve_relationship_field()` service only.
> - Read `forum_relationship_edges` first.
> - Preserve `relationship_role`.
> - Add `relationship_stance`.
> - Add `directionality`.
> - Add `closeness` / `emotional_weight` if available.
> - Add provenance.
> - Add `conflicts` array.
> - No prompt changes. No feature flag changes. No DB writes. No
>   migrations.

## 2. Files Added (only two — additive)

```
A  /app/backend/services/relationship_field_v2.py         (446 lines, 1 fn)
A  /app/backend/services/test_relationship_field_v2.py    (9 tests)
```

`grep` confirms `resolve_relationship_field` is referenced **only** from
these two files — no surface (Ask Mirror, Forum Chat, Astrology Chat,
How They Map To Me, Relationship Insight V2) has been wired yet.

## 3. Design Adherence — Guardrail Audit

| Guardrail (per user directive) | Implementation                                                                                  | Test                                   |
| --- | --- | --- |
| **G1** Provisional stances must NEVER override an explicit `forum_relationship_edges` role | `_derive_stance()` checks `CORE_STANCE_MAP` FIRST; provisional only fires for non-core role tokens; audit trail flags provisional-masquerading-as-core | `test_g1_provisional_does_not_collide_with_core_keys` |
| **G2** Lexicon-only matches must NOT bind HIGH-CONFIDENCE | `_HIGH_CONFIDENCE_SOURCES` excludes `MEMBER_ALIAS_LEX` and `PROPOSED_UNRESOLVED`; proper-name fallback caps confidence at 0.55 | `test_patricia_unknown_neutral` asserts `confidence < HIGH_CONFIDENCE_THRESHOLD (0.7)` |
| **G3** `self` → `self_subject` (never null) | Self-pronoun short-circuit sets `relationship_role="self"`, `stance="self_subject"` deterministically | `test_self_subject_no_target` |
| **G4** URL `context` mismatch with edges: edges win, conflict recorded | `Step 6 — Conflict detection` appends `url_context_vs_edge:...` to `conflicts[]`, never overwrites role | `test_g4_url_context_conflict_recorded_not_overriding_edges` + synonym test |
| **G5** `prior_relational_memory_keys`: pointer-only | Slice 1 leaves the field as an empty list (placeholder); no eager-load logic exists | (no test needed — field is `[]`) |

## 4. Stance Taxonomy (final state)

### 4.1 CORE — frozen (8 entries)

```python
CORE_STANCE_MAP = {
    "spouse":       "covenant_partner",
    "child":        "steward_guardian",
    "parent":       "lineage_source",
    "sibling":      "shared_origin",
    "close_friend": "chosen_ally",
    "mentor":       "guide",
    "forum_member": "peer",
    "unknown":      "neutral",
}
```

### 4.2 PROVISIONAL — additive, never overrides edges (21 entries)

```
former_partner / ex_partner       → severed_covenant
mentee                            → apprentice
coach                             → accountable_guide
coachee / client                  → accountable_apprentice
cofounder / business_partner      → co_architect
advisor                           → counsel
investor                          → stakeholder
manager / boss                    → authority_above
employee / direct_report          → authority_below
authority_figure                  → power_holder
collaborator                      → peer_in_motion
forum_mate                        → peer
close_circle / friend             → chosen_ally
colleague                         → peer_in_motion
self                              → self_subject
```

Provisional table is **single-source-edit**: any future revision (lock,
trim, or extend) touches only the `PROVISIONAL_STANCE_MAP` constant.

## 5. Directionality Taxonomy (first-class per user disposition #2)

```
SYMMETRIC         spouse · partner · sibling · close_friend · friend ·
                  forum_member · close_circle · collaborator · forum_mate ·
                  cofounder · business_partner · ex_partner · former_partner

USER_AS_GIVER     child · employee · direct_report · mentee · coachee ·
                  client · coach

USER_AS_RECEIVER  parent · mentor · manager · boss · advisor · investor ·
                  authority_figure
```

## 6. Resolution Ladder (single canonical source)

```
  1. forum_relationship_edges          ← canonical (confidence 0.95)
  2. explicit_map                      (confidence 0.85)
  3. saved_people                      (confidence 0.85)
  4. forum_members                     (confidence 0.85)
  5. forum_inference                   (confidence 0.65)
  6. member_alias_lexicon              (LOW — never high-confidence)
  7. pronoun_memory                    (LOW unless last_target was edge-bound)
  8. proposed_unresolved               (confidence 0.55, proposed_action emitted)
  9. self_no_target                    (confidence 0.95, stance=self_subject)
```

Lower sources fire only if higher sources return no role. This is the
**single canonical resolver** that eliminates the audit's race
condition between V2 router and post-router lexicon enrichment.

## 7. Test Results

```
$ cd /app/backend && python -m pytest services/test_relationship_field_v2.py -v
============================== test session starts ==============================
collected 9 items

test_mel_spouse_covenant_partner                                PASSED [ 11%]
test_thaddeus_child_steward_guardian                            PASSED [ 22%]
test_isaac_child_steward_guardian                               PASSED [ 33%]
test_patricia_unknown_neutral                                   PASSED [ 44%]
test_self_subject_no_target                                     PASSED [ 55%]
test_g1_core_stance_frozen_lookup                               PASSED [ 66%]
test_g1_provisional_does_not_collide_with_core_keys             PASSED [ 77%]
test_g4_url_context_conflict_recorded_not_overriding_edges      PASSED [ 88%]
test_g4_url_context_synonyms_do_not_trip_conflict               PASSED [100%]

============================== 9 passed in 0.14s ===============================
```

### 7.1 Per-acceptance-criterion evidence

#### A1 — Mel (spouse → covenant_partner)

```
hints = {"about_person_id": "697ec826…"}
→ relationship_role     = "spouse"
  relationship_stance   = "covenant_partner"
  directionality        = "SYMMETRIC"
  closeness             = "HIGH"
  emotional_weight      = "HIGH"
  resolution_source     = "forum_relationship_edges"
  confidence            = 0.95
  conflicts             = []
  resolution_path       = ["hint:explicit_about_person_id",
                           "legacy_src:forum_relationship_edges",
                           "stance:core:spouse->covenant_partner"]
```

#### A2 — Thaddeus (child → steward_guardian, USER_AS_GIVER)

```
hints = {"about_person_id": "69dd0b2c…"}
→ relationship_role     = "child"
  relationship_stance   = "steward_guardian"
  directionality        = "USER_AS_GIVER"
  closeness             = "HIGH"
  resolution_source     = "forum_relationship_edges"
  confidence            = 0.95
```

#### A3 — Isaac (child → steward_guardian, USER_AS_GIVER)

Same shape as A2 with `target_user_id = "69dda348…"`. Confirms
stance/directionality stability across same-role pairs with different
question phrasings ("What's coming up for Thaddeus" vs "What does
Isaac need from me right now").

#### A4 — Patricia (unknown → neutral, proposed_unresolved)

```
hints = {}
→ target_user_id        = None
  relationship_role     = None
  relationship_stance   = "neutral"
  directionality        = None
  resolution_source     = "proposed_unresolved"
  confidence            = 0.55          ← below HIGH (0.70) per G2
  missing_data          = ["target_unresolved"]
  proposed_action       = {"type": "add_to_circle",
                           "suggested_name": "Patricia",
                           "confidence": 0.55,
                           "reason": "name 'Patricia' appears in message
                                      but is not in user's saved_people
                                      OR any of their forums",
                           "source_text": "..."}
```

#### A5 — Self (no target, self_subject)

```
hints = {}
message = "Tell me about myself."
→ target_user_id        = None
  relationship_role     = "self"
  relationship_stance   = "self_subject"            ← G3 satisfied
  directionality        = None
  active_frame          = "SELF"
  resolution_source     = "self_no_target"
  confidence            = 0.95
```

### 7.2 Guardrail evidence

#### G4 — URL context conflict recording

```
hints = {"about_person_id": "697ec826…", "url_context": "stranger"}
→ relationship_role     = "spouse"               ← edges still win
  relationship_stance   = "covenant_partner"
  conflicts             = ["url_context_vs_edge:url='stranger' vs
                           resolved_role='spouse'
                           (source=forum_relationship_edges)
                           — edges override"]
```

#### G4 — Synonym, no conflict

```
hints = {"about_person_id": "697ec826…", "url_context": "partner"}
→ relationship_role     = "spouse"
  conflicts             = []                      ← partner~spouse
```

## 8. Side-Effect Audit

```
$ grep -rn "relationship_field_v2\|resolve_relationship_field" \
    --include='*.py' /app/backend/ | grep -v __pycache__
./services/relationship_field_v2.py:   <self-defs only>
./services/test_relationship_field_v2.py:<imports + asserts only>
```

- **No surface wired** to the new resolver.
- **No prompt changes** (only `audit_reports/*.md` and the new
  service file were touched).
- **No DB writes anywhere** in the resolver path; only `find_one` reads.
- **No flag changes** (`INTENT_ROUTER_V2_CUTOVER`,
  `INTENT_ROUTER_V2_ROLLOUT_PERCENT`,
  `RELATIONSHIP_ORCHESTRATION_PROMPT`,
  `CROSS_LENS_PROMPT_SURFACE` — all untouched).
- **No migrations**, no new collections.
- Atlas access remains blocked pending IP whitelist; all tests ran
  against `localhost:27017 / test_database`.

## 9. Hold Point — Next Slices

Slice 1 stops here. Awaiting review before:

- **Slice 2** — Wire `resolve_relationship_field()` into Ask Mirror's
  request path (read-only; replaces the today's three-tree race with
  a single envelope read). No prompt-block rewrites yet — Mirror's
  existing soft "bound (role: X)" line continues to fire, just sourced
  from the field instead of the lexicon.
- **Slice 3** — Replace today's mandate block and soft line with a
  single "RESOLVED FIELD" prompt section that reads
  `relationship_role`, `relationship_stance`, `directionality`,
  `closeness`, and `forum_topology` from the field. Gated by an opt-in
  rollout flag.
- **Slice 4** — Wire into Forum Chat orchestrator (replaces the
  ad-hoc Phase 1-4 path with a single field read).
- **Slice 5** — Wire into Relationship Insight V2 (`context=` query
  param validated against `relationship_role` from the field; mismatch
  surfaces in `conflicts[]`).
- **Slice 6** — Wire into "How This Person Maps To Me" (forum
  mappings) so all five surfaces read from the same envelope.

No coding on any of these slices until the user reviews Slice 1.
