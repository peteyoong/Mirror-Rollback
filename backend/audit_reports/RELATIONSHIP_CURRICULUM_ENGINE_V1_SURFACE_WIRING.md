# Relationship Curriculum Engine V1 — Surface Wiring
**Delivery Report**

| Field | Value |
|---|---|
| Slice | Surface wiring (post-producer slice) |
| Status | **GREEN — surface tests 5/5, full regression 88/88, bundle compiles** |
| Producer (already shipped) | `services/relationship_curriculum_engine.py` |
| Surfaces wired | (1) Forum mappings, (2) Relationship Insight V2, (3) Forum Chat response envelope, (4) V2 Card renderer |
| Flag | `RELATIONSHIP_CURRICULUM_ENGINE=false` (unchanged; default OFF) |
| Untouched | Astrology / HD / BaZi / Numerology / Timeline / Variant A engines.  All other env flags. |

---

## 1. What landed

Four additive wirings — all flag-gated, default OFF, zero schema/migration impact:

### 1.1 Surface 1 — Forum Mappings (`services/forum_hd_mapping.py`)
After `build_relationship_astrology` + `maybe_compute_restory`, the engine helper is called and the payload is attached at the **top level of `signals`** (NOT nested under astrology):

```python
signals["relationship_curriculum"] = _maybe_curriculum(...)
```

Rationale: the curriculum spans astrology + HD + enneagram + bazi, so it sits at the signal-set root next to the other lenses.

### 1.2 Surface 2 — Relationship Insight V2 (`server.py` ~14570)
Same helper call inside the V2 endpoint's astrology adapter block; the payload is mounted on the response under `signals.relationship_curriculum` exactly like surface 1.  When the user-spec role inference is empty it falls back to `forum_member` (role_weight 0.4) — keeps the engine confident even at unknown-role calls.

### 1.3 Surface 3 — Forum Chat (`routers/forums_chat.py`)
- `ForumChatResponse` gained an additive optional field `relationship_curriculum: Optional[Dict[str, Any]] = None`.
- Computed ONLY when:
  - Slice B auto-context resolved a **MEMBER** target (not pairwise, not group)
  - Resolver bound a target_user_id ≠ asker
  - Both charts are loadable from MongoDB
  - The flag is on
- Metadata only — **the LLM prompt is unchanged**.  FE can render the section in the chat envelope; future slice may wire it into the system prompt.

### 1.4 Frontend Card Section (`components/RelationshipInsightV2Card.tsx`)
- New `RelationshipCurriculum` TS type added
- New section rendered between Layer 2 (Patterns) and Layer 3 (Signals):

```
┌────────────────────────────────────────────────────────────┐
│  WHY THIS PERSON MATTERS                                   │
│  A meaning layer — not a destiny claim.                    │
│                                                            │
│  THE GIFT                                                  │
│  What Mel appears to bring into your life is curiosity,    │
│  perspective-taking, and dialogue.  …                      │
│                                                            │
│  THE CHALLENGE                                             │
│  The same qualities that make this relationship a gift …   │
│                                                            │
│  WHAT WANTS TO GROW                                        │
│  dialogue over certainty, perspective over position, …     │
│                                                            │
│  THE CURRICULUM                                            │
│  If this relationship has a curriculum, the shape …        │
│                                                            │
│  Strong signal                                             │
└────────────────────────────────────────────────────────────┘
```

Rendering rules:
- Section appears ONLY when `data.signals.relationship_curriculum.success === true`
- All 4 strings rendered straight from the producer (no FE composition, no jargon injection)
- Confidence rendered as Mirror-voice label (Strong / Moderate / Light signal — never "low/medium/high")
- Falls back to NOTHING (no placeholder) when the payload is absent — flag-off behaviour byte-identical to before

---

## 2. Acceptance tests — 5/5 PASS

```
$ python -m pytest services/test_relationship_curriculum_engine_surface_wiring.py -v

test_wiring_helper_returns_payload_when_flag_on             PASSED
test_wiring_helper_returns_none_when_flag_off               PASSED
test_forum_mapping_source_wiring_present                    PASSED
test_relationship_insight_v2_source_wiring_present          PASSED
test_forum_chat_source_wiring_present                       PASSED

5 passed in 0.13s
```

Source-presence tests defend against silent regression (if a future edit removes the wiring, the test fails immediately).

### Full regression sweep

```
$ python -m pytest services/test_relationship_curriculum_engine*.py \
                   services/test_astrology_relationship_restory_v1*.py \
                   services/test_slice_a_auto_context.py \
                   services/test_slice_b_forum_chat_wiring.py \
                   services/test_relationship_field_v2.py \
                   services/test_slice_2_ask_mirror_wiring.py \
                   services/test_slice_3_prompt_gate.py -q

88 passed in 38.80s
```

**Zero regressions** across all Relationship Field V2 + FCAC + Astro Re-Story V1 + Curriculum Engine producer + Curriculum Engine surface-wiring suites.

### Bundle health
- `tsc --noEmit` against `tsconfig.json` → **zero new TS errors in any touched file**
- Metro re-bundled `1393 modules` cleanly
- `http://localhost:3000` → HTTP 200
- Mirror Chat live traffic continues at 200 OK

---

## 3. Honest data integrity note (per your instruction)

Real Pete chart has **Pluto in Leo / H9** (NOT 7th) and Mercury in Pisces / H3 (NOT 7th).  The UI will never imply "Pluto 7th" for Pete because:
- The engine reads the **live chart payload** (`_planets_in_house(ch_a, 7)`)
- Pete's actual H7 contains only **South Node**
- The proof ledger for Pete↔Mel correctly reads: "Descendant in Gemini → curiosity, perspective-taking, dialogue" + "Gemini ruler (Mercury) in Pisces, house 3" + "Sun in Gemini activates 'curiosity'" (× 3 anchors) + "Manifestor ↔ Reflector dynamic →…"
- Confidence still grades **high** for spouse role on real data — Mel's triple Gemini activation alone hits the threshold

---

## 4. Guardrails honoured (per your spec)

| Constraint | Honoured | Evidence |
|---|---|---|
| Surface wiring additive | ✅ | only new payload fields; no removals |
| Flag-gated, default OFF | ✅ | `RELATIONSHIP_CURRICULUM_ENGINE=false` unchanged |
| Zero prompt changes | ✅ | LLM system prompts not touched anywhere |
| Zero schema migrations | ✅ | no DB writes / no collection edits |
| Legacy behaviour preserved when flag OFF | ✅ | helper returns None; surface code sees None; renders nothing |
| Honest data integrity (no fake Pluto-H7 for Pete) | ✅ | engine reads live planets-in-house from chart payload |
| No destiny / soulmate / karmic / fate language | ✅ | producer banlist regex still passes |
| Climate Engine NOT started | ✅ | no such code |
| Variant A migration untouched | ✅ | RUN_VARIANT_A_MIGRATION flag still unset |

---

## 5. Files touched (this slice)

| File | Change |
|---|---|
| `services/forum_hd_mapping.py` | Wire `maybe_compute_restory` + `maybe_generate` calls; attach `signals.relationship_curriculum` |
| `server.py` | Same wiring inside `/relationship-insight-v2` block + top-level attach |
| `routers/forums_chat.py` | New optional `relationship_curriculum` field on response; compute on MEMBER frame |
| `components/RelationshipInsightV2Card.tsx` | New TS types `RelationshipCurriculum`; new section between Layer 2 and Layer 3 |
| `services/test_relationship_curriculum_engine_surface_wiring.py` | NEW — 5 surface-wiring acceptance tests |
| `audit_reports/RELATIONSHIP_CURRICULUM_ENGINE_V1_SURFACE_WIRING.md` | NEW — this report |

**No changes** to the producer module, no changes to any other engine, no changes to any `.env` file.

---

## 6. How to enable

```bash
# Single flag flip enables all 3 backend surfaces + the FE card section.
sed -i 's/RELATIONSHIP_CURRICULUM_ENGINE=false/RELATIONSHIP_CURRICULUM_ENGINE=true/' \
    /app/backend/.env
sudo supervisorctl restart backend
# Frontend has no separate flag — it auto-renders when payload is present.
```

Reversible in seconds.  No DB impact.

---

## 7. What is NOT in this slice

- **LLM prompt consumption** — Forum Chat sends the curriculum payload only as response metadata.  Hooking it into the system prompt requires the prompt-redesign work which is out of scope.
- **`hidden_evidence` tray** — proof ledger flows over the wire but is not displayed in the card UI yet.  Reserved for a future expandable evidence tray.
- **Relationship Climate Engine** — explicitly parked per your prior directive.

---

## 8. Next step

Awaiting your review with the flag flipped on for internal cohort observation.  When you flip the flag, the "Why This Person Matters" section will appear in:
1. `RelationshipInsightV2Card` between How-This-Maps and Between-You-Today
2. Forum mappings page (signals.relationship_curriculum on the same card)
3. Forum Chat response envelope (data only — UI rendering of chat-message-side curriculum is a separate FE slice)

— end of report —
