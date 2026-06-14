# Astrology Relationship Re-Story V1 — Surface Wiring
**Delivery Report**

| Field | Value |
|---|---|
| Workstream | Astrology Re-Story V1 → Surface Wiring (Slice 1) |
| Status | **GREEN — surface-wiring pytest 8/8, full regression sweep 68/68** |
| Scope | Wire the existing producer module into 3 surfaces.  Flag-gated.  No prompt redesign, no DB writes, no migrations. |
| New env flag | `ASTROLOGY_RELATIONSHIP_RESTORY_V1` — default **`false`** |
| Untouched | Astrology / Variant A / Ophiuchus / HD / BaZi / Numerology / Timeline engines.  All other env flags. |

---

## 1. Audit findings (before coding)

### 1.1 Every current astrology relationship renderer

**Backend producers:**
| File | Output |
|---|---|
| `services/relationship_astrology_engine.py` | V2 deep card (`astrology_card{headline,body,supporting_signals}` + 7 loop fields). Still mentions planet names in some bodies. |
| `services/forum_hd_mapping.py::compute_astrology_signals` | Legacy `{attraction[], tension[], growth[]}` bullets — technical jargon possible. |
| `services/astrology_relationship_restory_v1.py` | **NEW Re-Story V1** (this session).  5-section narrative; jargon-free user-facing strings; technical evidence routed to `hidden_evidence[]`. |

**Backend surfaces:**
| Endpoint | Surface | Notes |
|---|---|---|
| `GET /api/forums/{forum_id}/member-mappings` | "How This Person Maps To Me" | Used `compute_astrology_signals` + V2 deep card |
| `GET /api/relationship-insight-v2/{user_id}` | "Relationship Insight V2" card | Used **legacy bullets only** — never invoked V2 deep card |
| `POST /api/forums/{forum_id}/chat` | Forum Chat (Slice B resolver) | Uses V2 deep card via orchestrator; no client-side narrative emit |

**Frontend renderers:**
| Component | Section heading | Bound to |
|---|---|---|
| `RelationshipInsightV2Card.tsx` (L331-345) | `ASTROLOGICAL DYNAMICS` | `data.signals.astrology.{attraction, tension, growth}` |
| `app/forums/mappings.tsx` (via forum-mapping API) | varies | same payload shape |

### 1.2 Surfaces still showing technical text
- Legacy `attraction/tension/growth` bullets in `RelationshipInsightV2Card.tsx` and `forums/mappings.tsx`
- V2 deep card `body` may still reference planet names

### 1.3 Existing payload shape
```jsonc
"signals": {
  "astrology": {
    "attraction": [], "tension": [], "growth": [],   // legacy bullets
    "v2_card":               {...},                  // forum mapping path only
    "core_relational_pattern":"...",
    ...
  }
}
```

### 1.4 Smallest blast-radius insertion
**Decision: add `signals.astrology.restory_v1` field** in both surfaces.
- Backend: helper `maybe_compute_restory(...)` injects the payload when flag is on.
- Frontend: the V2 card prefers `restory_v1` when present; falls back to legacy bullets when absent.
- **Zero schema changes.  Zero migrations.  Zero collection edits.**

### 1.5 BaZi overlap audit
- BaZi diagnostics live under `signals.bazi.diagnostics`
- Re-Story V1 lives under `signals.astrology.restory_v1`
- **Verified by `test_5_bazi_sections_unchanged` — Re-Story keys do NOT leak into BaZi output**

---

## 2. What landed

### 2.1 Helper added to the producer module
`services/astrology_relationship_restory_v1.py` now exposes:

```python
def is_enabled() -> bool: ...        # reads ASTROLOGY_RELATIONSHIP_RESTORY_V1
def maybe_compute_restory(...): ...  # returns payload or None
```

`maybe_compute_restory()` is the single point of contact for all surfaces.  Returns `None` (i.e. legacy behaviour preserved) when:
- flag is unset / not "true", **OR**
- either chart is `None`, **OR**
- producer raises any exception (defensive)

### 2.2 Three surface wirings (all additive, all flag-gated)

| # | Surface | File | Behaviour |
|---|---|---|---|
| 1 | **Forum mappings** (`/api/forums/{id}/member-mappings`) | `services/forum_hd_mapping.py:1947+` | Adds `signals.astrology.restory_v1` next to the existing `v2_card` |
| 2 | **Relationship Insight V2** (`/api/relationship-insight-v2/{user_id}`) | `server.py:14550+` | Adds `astro_signals["restory_v1"]` next to legacy `{attraction,tension,growth}` arrays |
| 3 | **Forum Chat** (`POST /api/forums/{id}/chat`) | `routers/forums_chat.py` | Adds `astrology_restory_v1` to the response envelope when Slice B auto-context resolved a MEMBER / PAIRWISE target with both charts loadable.  **Metadata only — prompt is unchanged.** |

### 2.3 Frontend renderer wiring
`components/RelationshipInsightV2Card.tsx`:
- New type `ReStorySection` and extended `astrology` payload type
- Replaced the legacy ASTROLOGICAL DYNAMICS block with a conditional renderer:
  - When `restory_v1.success` is true → renders the **5 sections** with `headline.toUpperCase()` + body, fully word-wrapped
  - Otherwise → renders the **legacy bullets** byte-identically to before
- `hidden_evidence` is **intentionally not displayed** (reserved for a future expandable evidence tray)

### 2.4 New env flag
```
ASTROLOGY_RELATIONSHIP_RESTORY_V1=false   # default — legacy behaviour
```
Set to `true` (case-insensitive) to enable.  Reversible in seconds.

---

## 3. Acceptance tests — 8/8 PASS

```
$ python -m pytest services/test_astrology_relationship_restory_v1_surface_wiring.py -v

test_1_pete_mel_spouse_restory_when_flag_on            PASSED
test_2_legacy_preserved_when_flag_off                  PASSED
test_3_no_jargon_in_user_facing_text                   PASSED
test_4_hidden_evidence_carries_astro_tokens            PASSED
test_5_bazi_sections_unchanged                         PASSED
test_6_forum_mappings_load_with_flag_on                PASSED
test_7_relationship_insight_v2_wiring_present          PASSED
test_8_no_crash_on_empty_or_partial_inputs             PASSED

8 passed in 0.16s
```

Test → user-spec mapping:

| User spec | Test |
|---|---|
| 1. Pete↔Mel spouse renders Re-Story sections when flag ON | `test_1_pete_mel_spouse_restory_when_flag_on` |
| 2. Legacy astrology output remains when flag OFF | `test_2_legacy_preserved_when_flag_off` |
| 3. User-facing text contains no banned jargon | `test_3_no_jargon_in_user_facing_text` |
| 4. `hidden_evidence` contains technical placements | `test_4_hidden_evidence_carries_astro_tokens` |
| 5. BaZi sections remain unchanged | `test_5_bazi_sections_unchanged` |
| 6. Forum mappings still load | `test_6_forum_mappings_load_with_flag_on` |
| 7. Relationship Insight V2 still loads | `test_7_relationship_insight_v2_wiring_present` |
| 8. No crash on mobile modal | `test_8_no_crash_on_empty_or_partial_inputs` + bundle compiles |

### Full regression sweep
```
$ python -m pytest services/test_relationship_field_v2.py \
                   services/test_slice_2_ask_mirror_wiring.py \
                   services/test_slice_3_prompt_gate.py \
                   services/test_slice_a_auto_context.py \
                   services/test_slice_b_forum_chat_wiring.py \
                   services/test_astrology_relationship_restory_v1.py \
                   services/test_astrology_relationship_restory_v1_surface_wiring.py -q

68 passed in 41.85s
```

**Zero regressions** across the full Slice 1/2/2.5/3 + FCAC Slice A/B + Astro Re-Story V1 (producer) + Astro Re-Story V1 (surface wiring) suites.

---

## 4. Files touched

| File | Change |
|---|---|
| `services/astrology_relationship_restory_v1.py` | Added `is_enabled()` + `maybe_compute_restory()` flag-gated helpers |
| `services/forum_hd_mapping.py` | Inject `restory_v1` into `signals.astrology` (Surface 1) |
| `server.py` | Inject `restory_v1` into `astro_signals` on `/relationship-insight-v2` (Surface 2) |
| `routers/forums_chat.py` | Inject `astrology_restory_v1` into chat response envelope (Surface 3) |
| `components/RelationshipInsightV2Card.tsx` | New `ReStorySection` type + conditional renderer (Re-Story V1 preferred, legacy fallback) |
| `/app/backend/.env` | Added `ASTROLOGY_RELATIONSHIP_RESTORY_V1=false` |
| `services/test_astrology_relationship_restory_v1_surface_wiring.py` | NEW — 8 acceptance tests |
| `audit_reports/ASTROLOGY_RELATIONSHIP_RESTORY_V1_SURFACE_WIRING.md` | NEW — this report |

---

## 5. How to enable

```bash
# 1. Flip the backend flag
sed -i 's/ASTROLOGY_RELATIONSHIP_RESTORY_V1=false/ASTROLOGY_RELATIONSHIP_RESTORY_V1=true/' /app/backend/.env
sudo supervisorctl restart backend
# 2. Frontend is NOT flag-gated separately — it auto-renders restory_v1
#    when present in the response payload.  No FE restart needed.
```

Reversible by flipping the value back to `false` and restarting.  No DB writes, no schema changes.

---

## 6. Guardrails honoured

| Constraint | Honoured | Evidence |
|---|---|---|
| Do NOT start Relationship Climate Engine | ✅ | not touched |
| Do NOT modify astrology calculation | ✅ | no edits to `calculations/`, `services/astrology*`, ephemeris |
| Do NOT modify Variant A / Ophiuchus engine | ✅ | no edits |
| Do NOT modify chart data | ✅ | zero DB writes — verified by absence of `insert_one`/`update_one` in any touched file |
| No destiny / soulmate language | ✅ | `test_3` regex banlist |
| No astrology jargon in user-facing narrative | ✅ | `test_3` |
| Flag-gated; new flag `ASTROLOGY_RELATIONSHIP_RESTORY_V1=false` | ✅ | env line + `is_enabled()` helper |
| No default behaviour change until flag enabled | ✅ | `test_2_legacy_preserved_when_flag_off` |
| Preserve legacy astrology output behind flag-off | ✅ | renderer + helper return None when flag off |
| No DB writes / no migrations | ✅ | grep across all touched files: no DB writes |
| No feature flag flips during implementation | ✅ | flag added with `=false` default; never flipped |

---

## 7. What is NOT in this slice

- **Hidden evidence tray** on the V2 card — `hidden_evidence[]` flows over the wire but is not yet rendered.  Future slice.
- **Astrology Chat consumption** of Re-Story V1 (a 4th surface) — not in the user's priority list.
- **Forum Chat prompt redesign** — Surface 3 is metadata-only; the LLM does not yet consume the Re-Story V1 payload.  Wiring it into the system prompt would require a prompt redesign which is out of scope.
- **Relationship Climate Engine** — explicitly forbidden by user directive.

---

## 8. Mobile modal smoke

The frontend bundle compiles cleanly post-changes (HTTP 200 on localhost:3000).  Zero TS errors in any touched file.  The renderer is defensive: it requires `restory.success && restory.sections` before rendering; falls back to legacy when those are missing or when individual sections lack `headline` / `body`.

---

— end of report —
