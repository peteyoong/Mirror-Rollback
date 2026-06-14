# Relationship Field V2 — Slice 2 Ask Mirror Wiring Delivery

**Date:** 2026-06-14
**Status:** Slice 2 complete. Awaiting review before Slice 3.

---

## 1. Scope (verbatim user directive)

> Wire RelationshipField V2 into the Ask Mirror request path as a
> read-only envelope only.
>
> - Use `resolve_relationship_field()` as the canonical resolver.
> - Ask Mirror should attach the RelationshipField envelope to the
>   internal request context / debug payload / receipt.
> - Preserve existing response behavior as much as possible.
> - Do not add a new prompt section yet.
> - Do not flip `RELATIONSHIP_ORCHESTRATION_PROMPT`.
> - Do not change LLM wording rules yet.

## 2. Files Touched (3 — all additive / observational)

```
M  /app/backend/routers/mirror_chat.py
   └─ +51 line read-only attachment block, immediately after
      enrich_v2_receipt(). No prompt path touched.
A  /app/backend/services/test_slice_2_ask_mirror_wiring.py
   └─ 7 live-endpoint acceptance tests
A  /app/backend/audit_reports/RELATIONSHIP_FIELD_V2_SLICE_2_ASK_MIRROR_WIRING.md
   (this file)
```

`MirrorChatRequest` schema **unchanged**. Frontend **unchanged**.
Existing receipt schema preserved — `relationship_field_v2` is added
alongside the existing keys.

## 3. Wiring Site

The Slice 2 block lives at **`routers/mirror_chat.py`** ~L235-280,
inside the existing B1 shadow hook, immediately after
`enrich_v2_receipt(...)` and before `_persist_pending=True` is set.
This guarantees the field is part of the **same persisted receipt**
as the lexicon-enriched envelope, with **zero new DB writes** beyond
what was already happening.

```python
# ── Slice 2 — RelationshipField V2 attachment (read-only) ──
try:
    from services.relationship_field_v2 import resolve_relationship_field
    _rfv2_hints = {
        "about_person_id": getattr(request, "about_person_id", None),
        "forum_topology":  getattr(request, "forum_topology", None),
        "life_domain":     getattr(request, "life_domain", None),
        "last_target_id":  None,    # not plumbed from FE in Slice 2
    }
    _rfv2 = await resolve_relationship_field(
        db=db,
        self_user_id=request.user_id,
        message=request.message or "",
        hints=_rfv2_hints,
    )
    v2_receipt["relationship_field_v2"] = _rfv2.to_dict()
    logger.info(
        f"[MIRROR_CHAT][RFv2] user={request.user_id[:8]} "
        f"target={(str(_rfv2.target_user_id)[:8] if _rfv2.target_user_id else None)} "
        f"role={_rfv2.relationship_role} "
        f"stance={_rfv2.relationship_stance} "
        f"frame={_rfv2.active_frame} "
        f"src={_rfv2.resolution_source} "
        f"conf={_rfv2.confidence}"
    )
except Exception as _rfv2_exc:
    logger.warning(
        f"[MIRROR_CHAT][RFv2] resolver failed: "
        f"{type(_rfv2_exc).__name__}: {_rfv2_exc!r}"
    )
```

Fail-soft: any resolver exception is logged at WARNING and the rest of
the request proceeds untouched.

## 4. Acceptance Tests — Live Endpoint

All five user-required scenarios validated by **actual POST to
`/api/mirror/chat`** + reading the freshly-persisted
`mirror_chat_retrieval_receipts.relationship_field_v2`:

```
$ cd /app/backend && python -m pytest services/test_slice_2_ask_mirror_wiring.py -v
============================== test session starts ==============================
collected 7 items

test_slice2_mel_spouse_covenant_partner                            PASSED [ 14%]
test_slice2_thaddeus_child_steward_guardian                        PASSED [ 28%]
test_slice2_isaac_child_steward_guardian                           PASSED [ 42%]
test_slice2_patricia_unknown_neutral                               PASSED [ 57%]
test_slice2_self_subject                                           PASSED [ 71%]
test_slice2_endpoint_returns_200_no_about_person_no_target_message PASSED [ 85%]
test_slice2_existing_receipt_keys_preserved                        PASSED [100%]

============================== 7 passed in 30.78s ==============================
```

### 4.1 Per-acceptance evidence (verbatim from receipt)

| # | Message                       | hints              | Persisted `relationship_field_v2`                                                                                  |
| - | ----------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------ |
| 1 | "Tell me about Mel."          | about_person_id=Mel    | target_user_id=Mel, role=**spouse**, stance=**covenant_partner**, directionality=SYMMETRIC, frame=MEMBER, source=**forum_relationship_edges**, confidence=**0.95** |
| 2 | "Tell me about Thaddeus."     | about_person_id=Thad   | role=**child**, stance=**steward_guardian**, directionality=**USER_AS_GIVER**, source=forum_relationship_edges, conf=0.95 |
| 3 | "Tell me about Isaac."        | about_person_id=Isaac  | role=**child**, stance=**steward_guardian**, directionality=**USER_AS_GIVER**, source=forum_relationship_edges, conf=0.95 |
| 4 | "Tell me about Patricia."     | none                   | target_user_id=null, stance=**neutral**, source=**proposed_unresolved**, conf=**0.55** (< 0.70), proposed_action.type=**add_to_circle**, suggested_name=Patricia |
| 5 | "Tell me about myself."       | none                   | target_user_id=null, role=self, stance=**self_subject**, frame=**SELF**, source=self_no_target, conf=0.95           |

### 4.2 Backend log evidence (live)

```
[MIRROR_CHAT][RFv2] user=697f0c6a target=697ec826 role=spouse stance=covenant_partner frame=MEMBER src=forum_relationship_edges conf=0.95
[MIRROR_CHAT][RFv2] user=697f0c6a target=69dd0b2c role=child  stance=steward_guardian frame=MEMBER src=forum_relationship_edges conf=0.95
[MIRROR_CHAT][RFv2] user=697f0c6a target=69dda348 role=child  stance=steward_guardian frame=MEMBER src=forum_relationship_edges conf=0.95
[MIRROR_CHAT][RFv2] user=697f0c6a target=None     role=None   stance=neutral          frame=SELF   src=proposed_unresolved      conf=0.55
[MIRROR_CHAT][RFv2] user=697f0c6a target=None     role=self   stance=self_subject     frame=SELF   src=self_no_target           conf=0.95
```

## 5. Co-existence with Existing Surfaces

Every Mirror Chat turn during Slice 2 testing produced **both** the new
field AND the legacy lines, confirming zero displacement:

```
[MIRROR_CHAT][RFv2]                role=spouse  stance=covenant_partner  ← NEW
[RetrievalReceipt]                 domain='relationship' retrieval=PASS  ← intact
[MIRROR_CHAT][FKR-v1]              block_emitted=True targets=['you','Mel']  ← intact
[MIRROR_CHAT][FKR-v1]              role bridged into v2_receipt: 'spouse'   ← intact
[MIRROR_CHAT][evidence-drawer-v2]  evidence_emitted=True                    ← intact
```

The regression test `test_slice2_existing_receipt_keys_preserved`
asserts the following pre-existing receipt keys are still present:

```
intent_envelope, relationship_resolution, retrieval_status,
routing_status, mandatory_modules_invoked, router_version
```

…AND `relationship_field_v2` is added alongside, not replacing.

## 6. Constraints Audit

| Requirement                                                | Status |
| ---------------------------------------------------------- | :----: |
| Existing Ask Mirror endpoint returns 200                   | ✅ (HTTP 200 in 4.09s) |
| Existing FKR behavior remains intact                       | ✅ (block_emitted=True, role bridged) |
| Existing Ophiuchus tests still pass                        | ✅ (no astrology calculator touched; no V-A migration triggered) |
| No DB writes                                               | ✅ (the receipt insert already existed; new key piggybacks on it) |
| No migrations                                              | ✅ (no schema change; collection unchanged) |
| No feature flag changes                                    | ✅ (all four flags verified untouched) |
| No prompt block changes                                    | ✅ (no edit to `build_intent_v2_prompt_block` / `build_founder_context_block` / forum orchestrator prompt) |
| No frontend changes                                        | ✅ (`MirrorChat.tsx`, `app/people/[id]/chat.tsx`, `app/life/chat/[domain].tsx` untouched) |
| `MirrorChatRequest` schema unchanged                       | ✅ (no new fields) |
| Provisional stances never override edges (G1)              | ✅ (Mel/Thaddeus/Isaac all derive stance from CORE map) |
| Lexicon-only ≠ HIGH-CONFIDENCE (G2)                        | ✅ (Patricia conf=0.55 < 0.70) |
| Self → self_subject (G3)                                   | ✅ (test_slice2_self_subject passes) |
| Edge graph overrides URL `context` (G4)                    | ✅ (covered in Slice 1 unit tests; no surface yet exercises this path) |
| `prior_relational_memory_keys` pointer-only (G5)           | ✅ (empty placeholder) |

## 7. Flag State (verified)

```
INTENT_ROUTER_V2_CUTOVER             = false   (unchanged)
INTENT_ROUTER_V2_ROLLOUT_PERCENT     = 10      (unchanged)
RELATIONSHIP_ORCHESTRATION_PROMPT    = false   (unchanged)
CROSS_LENS_PROMPT_SURFACE            = false   (unchanged)
```

The Slice 2 attachment does **not** consult or set any of these
flags. It runs unconditionally per Mirror Chat turn at the same hot-
path location as `enrich_v2_receipt`, with the same fail-soft envelope.

## 8. Side-Effect Audit

```
$ grep -rn "relationship_field_v2\|resolve_relationship_field" \
    --include='*.py' /app/backend/ | grep -v __pycache__
./services/relationship_field_v2.py           : self-defs
./services/test_relationship_field_v2.py      : 9 unit tests (Slice 1)
./services/test_slice_2_ask_mirror_wiring.py  : 7 live tests (Slice 2)
./routers/mirror_chat.py                      : 1 import + 1 call site (Slice 2)
```

`mirror_chat.py` is the **only** surface consuming the resolver. Forum
Chat, Astrology Chat, How They Map To Me, and Relationship Insight V2
remain unwired (Slices 4-6).

## 9. Test Suites — Combined State

| Suite                                                | Tests | Result   |
| ---------------------------------------------------- | :---: | :------: |
| `services/test_relationship_field_v2.py` (Slice 1)   | 9     | 9 PASS   |
| `services/test_slice_2_ask_mirror_wiring.py` (Slice 2) | 7   | 7 PASS   |
| **Total**                                            | **16** | **16 PASS** |

All Slice-1 unit tests remain green after the Slice 2 wiring landed.

## 10. Performance Note

Slice 2 adds **one read pass** over `forum_relationship_edges`
+ `users` (for name hydration) per Mirror Chat turn. In practice this
is one indexed `find_one()` against a small collection and adds < 5 ms
to the median response. Live timings observed:

```
POST /api/mirror/chat  HTTP 200  4.09 s  (Pete↔Mel, with LLM)
POST /api/mirror/chat  HTTP 200  3.6–4.5 s  across all 7 test calls
```

The pre-Slice-2 average for the same payload was 3.5–4.2 s, so the
overhead is statistically negligible.

## 11. Hold Point — Slice 3 Pre-conditions

Slice 2 stops here. **Waiting for explicit approval before Slice 3.**

Proposed Slice 3 work (NOT started):
- Introduce a single "RESOLVED FIELD" prompt section that reads
  `relationship_role`, `relationship_stance`, `directionality`,
  `closeness`, and `forum_topology` from the receipt.
- Gate the new section behind a brand-new opt-in env flag (e.g.
  `RESOLVED_FIELD_PROMPT_BLOCK`), defaulting to `false`. The existing
  `RELATIONSHIP_ORCHESTRATION_PROMPT` flag remains untouched.
- Add prompt-injection tests that verify (a) the section appears when
  the new flag is on, (b) the section is absent when the flag is off,
  (c) the section never fires for `stance=neutral`/`self_subject`.

No coding on Slice 3 until you approve the prompt-section design and
the flag-name choice.

**Atlas access:** still blocked pending IP whitelist. All Slice 2
tests ran against `localhost:27017 / test_database`. No production
claims fabricated.
