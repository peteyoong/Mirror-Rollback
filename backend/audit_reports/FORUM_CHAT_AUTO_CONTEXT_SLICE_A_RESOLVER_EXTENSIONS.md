# Slice A — Forum Chat Auto-Context Resolver Extensions
**Delivery Report**

| Field | Value |
|---|---|
| Slice | A — Backend Resolver Extensions |
| Status | **GREEN — pytest 10/10 + zero prior-suite regressions (34/34)** |
| Scope | Resolver only.  No prompt surface.  No UI changes.  No flag flips. |
| Touched file | `/app/backend/services/relationship_field_v2.py` |
| New test file | `/app/backend/services/test_slice_a_auto_context.py` |
| Feature flag | `FORUM_CHAT_AUTO_CONTEXT_PROMPT` — **NOT introduced yet** (Slice C/D) |
| Untouched flags | `INTENT_ROUTER_V2_CUTOVER`, `RELATIONSHIP_ORCHESTRATION_PROMPT`, `CROSS_LENS_PROMPT_SURFACE`, `RELATIONSHIP_FIELD_V2_PROMPT` |

---

## 1. What landed

Three additive intent paths were grafted **above** the existing edges-first
chain inside `resolve_relationship_field()`.  All paths are guarded by
`if not has_target_hint:` — so explicit `about_person_id`,
`forum_topology.active_member_id`, `last_target_id+pronoun`, and
`target_name_hint` continue to take canonical priority.

```
hint? ──Yes──▶ canonical Step 1 → Step 2 (edges resolver) → … (unchanged)
   │
   No
   ▼
@mention (single)  →  feeds Step 2 with discovered candidate
@mention (≥2 close) →  return AMBIGUOUS
PAIRWISE pattern   →  return PAIRWISE   (both names must resolve cleanly)
MULTI_PERSON scope →  return MULTI_PERSON  ("my children", …)
FORUM intent       →  return FORUM       (conservative seed list)
   │
   ▼
Step 1+2 (existing edges-first ladder) — unchanged
Step 3 (proper-name fallback) — upgraded to use ambiguity detector
```

### Ordering bias (per user directive)
**MEMBER > PAIRWISE > FORUM.**  The FORUM intent regex is intentionally
narrow ("this forum", "the forum dynamic/energy/theme/field", "forum as
a whole").  Member questions like *"What does Thaddeus need from me?"*
flow through unchanged and bind to the EDGES graph.

### New enum values
| Constant | Value |
|---|---|
| `ActiveFrame.PAIRWISE` | `"PAIRWISE"` |
| `ActiveFrame.MULTI_PERSON` | `"MULTI_PERSON"` |
| `ActiveFrame.AMBIGUOUS` | `"AMBIGUOUS"` |
| `ResolutionSource.AT_MENTION` | `"at_mention"` |
| `ResolutionSource.PAIRWISE_PATTERN` | `"pairwise_pattern"` |
| `ResolutionSource.SCOPE_CLASS` | `"scope_class"` |
| `ResolutionSource.FORUM_INTENT` | `"forum_intent"` |
| `ResolutionSource.AMBIGUITY` | `"ambiguity"` |

### New RelationshipField fields
```python
target_user_id_b: Optional[str]      = None
target_name_b:    Optional[str]      = None
scope_class:      Optional[str]      = None
ambiguity_candidates: List[Dict]     = []
```

### New helpers (all read-only, all in `relationship_field_v2.py`)
- `_extract_at_mention(text)`
- `_extract_pairwise_names(text) -> Optional[Tuple[str, str]]`
- `_extract_scope_class(text)`
- `_has_forum_intent(text)`
- `_evaluate_ambiguity(cands) -> {ambiguous, competing_count, top_confidence}`
- `async _resolve_name_to_candidates(db, self_user_id, name) -> List[...]`

### Critical fix
Pre-existing partial injection from the previous session referenced
`candidate_target_id is None` **before** the variable was declared.
This would have raised `NameError` on any first-class @mention or
PAIRWISE path.  Declarations were moved above the Slice A block.

---

## 2. Acceptance matrix (10 tests, all green)

| # | Scenario | Message | Expected frame | Expected source | Status |
|---|---|---|---|---|---|
| S1 | SELF | *"Tell me about myself."* | `SELF` | `self_no_target` | ✅ |
| S2 | MEMBER spouse (name-only) | *"What does Mel need from me?"* | `MEMBER` | `forum_relationship_edges` | ✅ |
| S3 | MEMBER child (name-only)  | *"What does Thaddeus need from me?"* | `MEMBER` | `forum_relationship_edges` | ✅ |
| S4 | FORUM intent | *"What's the energy of this forum as a whole?"* | `FORUM` (multi-match flag) | `forum_intent` | ✅ |
| S5 | PAIRWISE | *"How are Mel and Thaddeus affecting each other?"* | `PAIRWISE` | `pairwise_pattern` | ✅ |
| S6 | MULTI_PERSON | *"What about my children right now?"* | `MULTI_PERSON` (scope=`my_children`) | `scope_class` | ✅ |
| S7 | AMBIGUOUS | *"Tell me about Test."* (5 saved_people match) | `AMBIGUOUS` | `ambiguity` | ✅ |
| S8 | Pronoun follow-up | *"What does she need from me?"* + `last_target_id=MEL` | `MEMBER` | `forum_relationship_edges` | ✅ |
| S9 | Pairwise family no-misbind | *(same as S5 but asserts neither target is the viewer)* | — | — | ✅ |
| B1 | Bias regression (3 messages) | *e.g. "How is Mel doing today?"* | NOT `FORUM`, NOT scope | — | ✅ |

```
$ python -m pytest services/test_slice_a_auto_context.py -v
=== 10 passed in 0.19s ===
```

---

## 3. Regression sweep (prior slices)

```
$ python -m pytest services/test_relationship_field_v2.py \
                   services/test_slice_2_ask_mirror_wiring.py \
                   services/test_slice_2_5_replay_validation.py \
                   services/test_slice_3_prompt_gate.py -v
=== 34 passed in 104.29s ===
```

Zero regressions in Slice 1, Slice 2, Slice 2.5, or Slice 3 suites.

---

## 4. Guardrails honoured

| Guardrail | Honoured | Evidence |
|---|---|---|
| G1 — provisional ≠ override of frozen-core stance | ✅ | Slice 1 tests still green |
| G2 — lexicon-only never auto-binds HIGH-CONFIDENCE | ✅ | AMBIGUOUS path returns conf=0.50, no role |
| G3 — `self → self_subject` (never null) | ✅ | S1 test |
| G4 — URL context conflicts recorded, edges win | ✅ | Slice 1 test still green |
| G5 — `prior_relational_memory_keys` pointer-only | ✅ | unchanged |
| Calculators / birth data / timeline / HD / astrology | UNTOUCHED | no edits |
| New collections / schema migrations | UNTOUCHED | no DB writes |
| `INTENT_ROUTER_V2_CUTOVER`, `..._ROLLOUT_PERCENT`, `RELATIONSHIP_ORCHESTRATION_PROMPT`, `CROSS_LENS_PROMPT_SURFACE` | UNTOUCHED | no env edits |
| `RELATIONSHIP_FIELD_V2_PROMPT` | UNTOUCHED (`false`) | no env edits |
| `FORUM_CHAT_AUTO_CONTEXT_PROMPT` | **NOT introduced** | reserved for Slice C/D |

---

## 5. Design notes & deliberate trade-offs

1. **FORUM bias** — narrow regex, expects an explicit forum self-reference.
   We will miss some forum-level questions (e.g. *"how is everyone doing"*)
   rather than mis-bind a member question to FORUM.
2. **PAIRWISE requires double-resolution** — both names must resolve to
   a single high-confidence candidate.  Otherwise we fall through to the
   normal Step 3 fallback.  This defuses *"Mel and I"* false positives
   ("I" is blocklisted in `_NAME_BLOCKLIST`).
3. **Ambiguity window** — `(top_conf − cand_conf) ≤ 0.10`.  Tunable.
4. **`_resolve_name_to_candidates` reach** — saved_people + forum-co-members
   via `forum_members → users` join.  Does NOT inspect
   `forum_relationship_edges` directly (Step 2 already does that with
   higher fidelity once a candidate is selected).
5. **No prompt surface yet** — Slice A is a pure resolver upgrade.  Ask
   Mirror, Forum Chat, and Astro Chat consume the existing
   `RelationshipField` envelope via the prompt-block emitter, which
   remains gated on `RELATIONSHIP_FIELD_V2_PROMPT` and (soon)
   `FORUM_CHAT_AUTO_CONTEXT_PROMPT`.

---

## 6. What is NOT in this slice

- Forum Chat backend wiring (Slice B)
- Frontend tab hide / Context chip (Slice C)
- Ambiguity clarification panel (Slice D)
- Pronoun memory threading at the surface layer (Slice E)
- Astrology Chat consumption (Slice F)
- `FORUM_CHAT_AUTO_CONTEXT_PROMPT` flag wiring (planned for Slice C/D)

---

## 7. Next step

Await user review of this report.  On approval → proceed to
**Slice B (Forum Chat backend wiring)**.

— end of report —
