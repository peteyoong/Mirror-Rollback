# RELATIONSHIP FIELD RENDER PIPELINE — FORENSIC AUDIT
## Mel "spouse mapping" page — BaZi visibility investigation

**Date:** 2026-06-13 (read-only forensic — no code edits, no deploys, no flag flips, no DB writes)
**Subject pair:** Pete (`697f0c6abf35c0528ff06954`) ↔ Mel (`melissa.mars@gmail.com`, `697ec826ad4b18f75bf42616`)
**Workspace MongoDB:** `mongodb://localhost:27017 / test_database` (per `DATABASE_TOPOLOGY_TRUTH_REPORT.md`)

---

## 0. Bottom-line answer

For Mel's spouse-mapping surface, BaZi relationship dynamics are exhibiting **a combination of cases (2) and (3)** depending on which screen the user is looking at, plus a **birth-defect suppression gate** on top:

| Screen | What is happening to BaZi | Cases (per your taxonomy) |
|---|---|---|
| **`/people/[id]` — spouse profile page** (Mel's saved-person card) | BaZi has **never been wired into this screen.** Page is 100% deterministic & client-side; renders only Enneagram-driven "Person Story" with no API call to any relationship engine. No BaZi line in the evidence panel; no BaZi chip in the lens row. | Not regressed — never present. |
| **`/relationship-insight?name=Mel` — V2 3-layer "Between you and Mel" card** | BaZi shape is **declared in the frontend type, computed in the data plane, and rendered in the UI** — **but** the backend V2 endpoint **does not pass `bazi_signals` into `generate_3layer_insight(...)`**, so the field always defaults to `{strengthens: [], drains: [], activates_growth: []}`. Even if it *were* populated, the frontend's `hasAnySignals` gate only opens the "Why this is so strong" container when **HD or Enneagram** has content — BaZi alone cannot un-suppress the section. | (3) No longer computed by this endpoint + (2) Frontend-gated by HD/Enneagram-only `hasAnySignals`. |
| **`/api/forum-mappings` & `POST /api/journal` (forum member maps)** | BaZi **is fully computed and returned.** Live probe for Pete↔Mel in shared forum `69dd05eaa333335fcbf3ad33` returned `bazi.support=3, bazi.growth=2` along with HD/Astrology/Enneagram. This is the path used by forum member chips, not the spouse page. | None — fully active. |

So: the **compute-side BaZi machinery is alive and working** (forum path proves it for the exact Pete↔Mel pair). The **per-person spouse screens** either skip the wiring entirely or gate it behind HD/Enneagram. This is **not a revert** — git history shows `hasAnySignals` has been HD/Enneagram-only since `RelationshipInsightV2Card.tsx`'s birth commit on 2026-04-13 (`b75185df`), and `/people/[id].tsx` has never contained the string "BaZi" or any API call to relational engines in its entire history.

---

## 1. Active section inventory (what currently renders)

### 1a. `/people/[id]` — Mel's saved-person profile (the "spouse mapping" page)

| Section | Source | What it shows |
|---|---|---|
| **Snapshot card** | `formatRelationshipType()`, `precisionLabel()` — local helpers | Name, relationship type, Born/Time/Place/Precision rows, lens-chip row |
| **Lens chip row** | Client-side computed in `availableLenses` (L376–389) | Only adds chips for: **Astrology · Human Design · Numerology · Enneagram**. BaZi & Zi Wei not present. |
| **Person Story (6 rows)** | `buildPersonStory()` → `ENNEAGRAM_CORE` map (L81–144) + `RELATIONSHIP_FALLBACK_CORE` map (L149–273) | Deterministic 6 rows: *Core pattern · How they tend to move through life · How they may feel to be around · What they may need from others · Shadow / pressure pattern · Relationship clue for me* |
| **Ask about this person button** | Routes to `/people/[id]/chat.tsx` | Hands off to the chat surface, which DOES support a `bazi` lens key but is a separate screen |
| **"What this is based on" accordion** | `EvidenceLine` 4×, hardcoded | Lists 4 lenses only: Human Design · Astrology · Numerology · Enneagram. **No BaZi line.** |
| **Enhance profile form** | Local form posts `full_birth_name`, `enneagram_type` to people API | Not a render section |

### 1b. `/relationship-insight` — V2 3-layer card

| Layer | Section | Source module |
|---|---|---|
| **L1 STORY** | `storyHeadline`, `storySummary` | `backend/services/relationship_3layer.py` → `STORY_TEMPLATES` |
| **L2 PATTERNS** | `WHAT HAPPENS BETWEEN YOU` | same module → `data.patterns.what_happens` |
| **L2 PATTERNS** | `WHERE FRICTION SHOWS UP` | same module → `data.patterns.tensions` |
| **L2 PATTERNS** | `WHAT YOU GIVE EACH OTHER` (gifts) | same module → `data.patterns.gifts` |
| **L3 SIGNALS** (expandable) | `DESIGN CONNECTIONS` (HD) | server.py L14430–14447 → `db.charts.find_one({"user_id":…}).human_design.defined_channels` |
| **L3 SIGNALS** | `GROWTH GIFTS` (Enneagram) | declared, defaults `[]` — *not currently populated by the endpoint* |
| **L3 SIGNALS** | `ASTROLOGICAL DYNAMICS` | declared, defaults `[]` — *not currently populated by the endpoint* |
| **L3 SIGNALS** | `ELEMENTAL DYNAMICS` (BaZi) | declared, defaults `[]` — *not currently populated by the endpoint* |

> **All Layer-3 groups are individually gated by their own `.length > 0` checks AND by an outer `hasAnySignals` gate** that only checks HD + Enneagram. See §3.

### 1c. `/api/forum-mappings` — forum member map (the active BaZi path)

| Field | Source module | Live (Pete↔Mel) |
|---|---|---|
| `signals.human_design[]` | `forum_hd_mapping.compute_full_relationship_mapping` | ✅ 3 channels |
| `signals.astrology.{attraction,tension,growth}` | `compute_astrology_signals` | ✅ active |
| `signals.enneagram.{gift_to_them,gift_to_you}` | `compute_enneagram_signals` | ✅ active |
| `signals.bazi.{support,tension,growth}` | `compute_bazi_signals` (`forum_hd_mapping.py:986`) | ✅ **support=3, growth=2** |
| `signals.numerology.{complementarity,missing_traits}` | `compute_numerology_signals` | ✅ numer=False on this pair (no shared name data) |

---

## 2. Suppressed section inventory

| Section | Where suppressed | Mechanism |
|---|---|---|
| BaZi on `/people/[id]` evidence panel | `/app/frontend/app/people/[id].tsx` L563–578 | **Hardcoded** to 4 `EvidenceLine` items (HD, Astrology, Numerology, Enneagram). BaZi is not in this list. Not a runtime suppression — a design-time omission. |
| BaZi chip in `/people/[id]` lens row | same file L376–389, `availableLenses` useMemo | Only pushes 4 lens strings. No `bazi` push. Design-time omission. |
| BaZi block on `/relationship-insight` V2 card | `/app/frontend/components/RelationshipInsightV2Card.tsx` L312 | **Inner gate:** `(data.signals.bazi.strengthens.length > 0 || data.signals.bazi.drains.length > 0)` — fires only when arrays are non-empty. Currently arrays are empty (see §3) so the BaZi `<View>` never mounts. |
| All Layer-3 signal groups on V2 card | same file L156–159, L230 | **Outer `hasAnySignals` gate**: `const hasAnySignals = hasHDSignals \|\| enneagram.gift_to_them.length>0 \|\| enneagram.gift_to_you.length>0;` — astrology, **BaZi**, and numerology are **excluded** from the hasAny check. If HD and Enneagram are both empty, the entire L3 container never renders even when astrology/BaZi/numerology are populated. |
| `signals.bazi.activates_growth` array on V2 card | same file L311–324 | **Computed-shape declared, never rendered.** The render code only iterates `strengthens` and `drains` (L317, L320). `activates_growth` is in the TS type (L49) and would be sent in the payload, but no `<View>` consumes it. |

---

## 3. Source module for each section (one-line tracer)

| Section header | Frontend mount | Backend payload key | Backend producer |
|---|---|---|---|
| `WHAT HAPPENS BETWEEN YOU` | V2Card L200 | `patterns.what_happens` | `relationship_3layer.generate_3layer_insight` |
| `WHERE FRICTION SHOWS UP` | V2Card L210 | `patterns.tensions` | same |
| `WHAT YOU GIVE EACH OTHER` | V2Card L220 | `patterns.gifts` | same |
| `DESIGN CONNECTIONS` | V2Card L252 | `signals.human_design` | server.py L14430–14447 (direct read from `db.charts.human_design.defined_channels`) |
| `GROWTH GIFTS` | V2Card L276 | `signals.enneagram` | **NOT WIRED** by V2 endpoint — `relationship_insight_engine.compute_enneagram_signals` exists in `forum_hd_mapping.py` but is not imported here |
| `ASTROLOGICAL DYNAMICS` | V2Card L295 | `signals.astrology` | **NOT WIRED** by V2 endpoint — `forum_hd_mapping.compute_astrology_signals` exists but is not imported here |
| `ELEMENTAL DYNAMICS` (BaZi) | V2Card L313 | `signals.bazi` | **NOT WIRED** by V2 endpoint — `forum_hd_mapping.compute_bazi_signals` exists at `forum_hd_mapping.py:986` and is actively used by `compute_full_relationship_mapping`, but the V2 endpoint never imports or calls it |
| Person Story 6 rows on `/people/[id]` | people/[id].tsx L519–533 | n/a (no API) | `buildPersonStory()` local function from `ENNEAGRAM_CORE` + `RELATIONSHIP_FALLBACK_CORE` static maps |
| Evidence accordion 4 lines on `/people/[id]` | people/[id].tsx L563–578 | n/a (no API) | Hardcoded text branches per `birth_time_accuracy`, `birth_location_accuracy`, `full_birth_name`, `enneagram_type` |

---

## 4. Is BaZi present in payloads?

Live read-only probes against the workspace backend (port 8001), authenticated as `user_id=697f0c6abf35c0528ff06954` (Pete):

### 4a. `/api/relationship-insight-v2/{pete_id}?other_name=Mel&context=spouse`
```json
"signals": {
  "human_design": [/* 3 channels */],
  "astrology":  {"attraction": [], "tension": [], "growth": []},
  "bazi":       {"strengthens": [], "drains": [], "activates_growth": []},
  "enneagram":  {"gift_to_them": [], "gift_to_you": []},
  "numerology": {"complementarity": [], "missing_traits": []}
}
```
**BaZi is structurally present (the key exists in the response) but contains no content.** The endpoint at `server.py:14365` only piped `hd_signals` into `generate_3layer_insight(...)`; the four other signal kwargs are never provided, so `relationship_3layer.py:372–377` falls through to the empty-array defaults.

### 4b. `POST /api/forum-mappings` (shared forum `69dd05eaa333335fcbf3ad33`, Pete↔Mel)
```text
Mel  bazi_keys={'support': 3, 'growth': 2}  hd=True  astro=True  ennea=True  numer=False
```
**BaZi is present AND populated** — proving the compute machinery for the exact Pete↔Mel pair is alive and working. The wall is at the *spouse-page wiring layer*, not at the calculator layer.

---

## 5. Did duplicate suppression remove BaZi?

**No.** I searched the codebase for duplicate-suppression / dedupe / "already seen" mechanisms in the relationship render pipeline. The actual suppressors are:

| Mechanism | File | Effect |
|---|---|---|
| `hasAnySignals = hasHDSignals \|\| enneagram.gift_to_them.length>0 \|\| enneagram.gift_to_you.length>0` | `RelationshipInsightV2Card.tsx:156–159` | **Outer gate** that hides the entire L3 signals container — explicitly excludes astrology, **BaZi**, and numerology from the OR-check. This is the dominant suppressor. |
| Inner per-section `.length > 0` checks | same file L275, L294, L312 | Per-group conditional render — fires correctly only when arrays are non-empty. Currently empty for BaZi at this endpoint. |
| Hardcoded evidence-line list (4 entries) | `people/[id].tsx:563–578` | Design-time omission of a 5th "BaZi" `EvidenceLine`. |
| Hardcoded `availableLenses` push list | `people/[id].tsx:376–389` | Design-time omission of a `lenses.push('BaZi')` branch. |

**No de-dupe, no "already shown this lens", no convergence-collapse filter** is responsible. The suppression is **gating logic + missing wiring**, not duplicate elimination.

---

## 6. Git-history trace for BaZi relationship dynamics

| Plane | Earliest commit | What it introduced | Latest state |
|---|---|---|---|
| `services/relationship_3layer.py` — `bazi_signals` kwarg | `b75185df` (2026-04-13) | Added `bazi_signals: Optional[Dict] = None` to `generate_3layer_insight` signature + default empty-array fallback | **Still parameter-only; never connected at the V2 endpoint call site** |
| `services/forum_hd_mapping.py` — `compute_bazi_signals(...)` | `5ff42f6d` (2026-04-13) | `bazi_signals = None  # Will be populated when BaZi data is available` (placeholder) | |
| same file | `ddb09ade` (2026-04-13) | `bazi_signals = compute_bazi_signals(chart_a, chart_b, current_user_name, member_name)` — **first real wiring** | **Still actively used by `compute_full_relationship_mapping` / forum endpoints** |
| same file | `edb2b3f1` (2026-04-14) | Added `pronouns_b` arg to `compute_bazi_signals(...)` — gender-aware copy | (current) |
| same file | `0320b609` (2026-05-21) | Added shadow-word sanitizer that *passes through* `bazi_signals` | (current) |
| `services/relationship_field.py` | `7ea80786` (2026-05-20) | Created the unified "Relationship Field" layer with `STRUCTURE: bazi` dimension and `bazi_support/tension` matching | (current) — wired into `forum_hd_mapping.compute_full_relationship_mapping`, **not** into the V2 endpoint |
| `frontend/components/RelationshipInsightV2Card.tsx` — `data.signals.bazi` shape | `b75185df` (2026-04-13) | TS interface + ELEMENTAL DYNAMICS render branch — born already gated by HD/Enneagram-only `hasAnySignals` | **Unchanged since birth**; only 2 commits ever touched this file. The hasAnySignals defect has been present since day 1. |
| `frontend/app/people/[id].tsx` | `3b7183e8` (file's birth commit) | Created already with 4-lens chip row and 4-line evidence panel; **the substring "BaZi" / "bazi" has never appeared in this file's git history** | (current) — Person Story remains 100% deterministic, Enneagram-fallback, no relational API call |

**Last commit where BaZi relationship dynamics were rendered to a Mel-style screen:**

* For `/people/[id]` (spouse profile): **never**. Zero commits ever introduced BaZi to this surface.
* For `/relationship-insight` V2 card: **never as visible UI** for Pete↔Mel. The render branch has existed since 2026-04-13 (`b75185df`), but its gating + the missing endpoint wiring mean BaZi has likely never lit up on this card for any pair in this workspace. (A field-test could prove this is also true on Atlas / deployed, but that requires the Atlas allowlist work flagged earlier.)
* For the **forum** path (e.g. `/forums/[id]`): BaZi has been rendered since `ddb09ade` (2026-04-13) and is **currently live** for Pete↔Mel (today's probe returned 3 support + 2 growth strings).

So the user's recollection of "BaZi relationship dynamics being visible before" almost certainly maps to the **forum member mapping** screen, not the spouse-profile / relationship-insight screens.

---

## 7. Verdict — which of the four cases applies?

> **You asked:** Are BaZi relationship dynamics
> (1) computed but hidden by duplicate suppression,
> (2) computed but not rendered,
> (3) no longer computed,
> (4) regressed from a previous branch/deploy?

**Answer:** All depends on screen, but for the spouse-mapping surfaces:

- **Not (1).** No duplicate-suppression in this pipeline.
- **Partially (2).** The compute path *does* exist (proved by the forum endpoint returning BaZi for Pete↔Mel). On the V2 card, the rendering branch exists. But the spouse-facing endpoint `/relationship-insight-v2` never plumbs the computed `bazi_signals` through to `generate_3layer_insight`, and even if it did, the frontend `hasAnySignals` gate would still hide it unless HD/Enneagram are also non-empty.
- **Partially (3).** From the V2 endpoint's perspective, BaZi is *not currently being computed* during a `/relationship-insight-v2` request — the endpoint simply doesn't call `compute_bazi_signals(...)`. The wider system computes it elsewhere (forum path).
- **Not (4).** Git history shows the V2 card's HD/Enneagram-only `hasAnySignals` gate has been in place since the file's birth commit. The V2 endpoint has never piped `bazi_signals` to `generate_3layer_insight` — there is no earlier branch/deploy where this was wired differently for the V2 endpoint. The `/people/[id]` page has never contained "BaZi" in its history. Pre-Apr-13 there was no V2 card at all.

**The user-perceived "BaZi appeared, then disappeared" pattern is best explained by:**
1. The user previously saw BaZi inside a **forum member mapping** (the forum path that *is* fully wired), not on the spouse-profile or relationship-insight screens. Switching from the forum view to the per-person spouse view crosses into a render path that has never had BaZi.
2. Within `/relationship-insight`, the HD/Enneagram-only `hasAnySignals` gate is a permanent silent suppressor that no pair has been able to overcome without HD or Enneagram content — that's a birth-defect that has never been fixed.

---

## 8. Read-only reproduction commands

```bash
# 1. Confirm /people/[id].tsx has no BaZi (and never did)
grep -c "BaZi\|bazi" /app/frontend/app/people/\[id\].tsx                   # → 0
git log --all -S "bazi" -- "frontend/app/people/[id].tsx"                  # → 0 commits

# 2. Confirm V2 endpoint doesn't wire bazi_signals
sed -n '14449,14460p' /app/backend/server.py                               # only hd_signals
grep -n "hasAnySignals" /app/frontend/components/RelationshipInsightV2Card.tsx
# → L156-159 (HD + Enneagram only — astrology/BaZi/numerology excluded)

# 3. Forum mapping path IS wired and DOES return BaZi for Pete↔Mel
curl -sS -X POST http://localhost:8001/api/forum-mappings \
  -H "Content-Type: application/json" \
  -d '{"forum_id":"69dd05eaa333335fcbf3ad33","user_id":"697f0c6abf35c0528ff06954"}' \
  | jq '.mappings[] | select(.member_name=="Mel") | .signals.bazi'
# → { "support": [...3 items...], "growth": [...2 items...] }

# 4. V2 endpoint returns empty BaZi for the SAME pair
curl -sS "http://localhost:8001/api/relationship-insight-v2/697f0c6abf35c0528ff06954?other_name=Mel&context=spouse" \
  | jq '.signals.bazi'
# → { "strengthens": [], "drains": [], "activates_growth": [] }
```

---

## 9. Proposed remediation options (NOT applied — for your approval)

Two options, both **read-only safe to plan, additive when applied**, no calculator or backend math changes:

### Option R1 — Plumb existing BaZi compute into the V2 endpoint (additive)
* In `server.py:14365 get_relationship_insight_v2_endpoint`, after the HD signal block, additionally import and call `compute_bazi_signals(chart_a, chart_b, ...)`, `compute_astrology_signals(...)`, `compute_enneagram_signals(...)`, `compute_numerology_signals(...)` from `services/forum_hd_mapping` (already battle-tested by the forum path), and pass them into `generate_3layer_insight(...)` as the existing kwargs `astro_signals=`, `bazi_signals=`, `enneagram_signals=`, `numerology_signals=`.
* In `RelationshipInsightV2Card.tsx`, extend `hasAnySignals` to also OR-in `bazi.strengthens.length > 0`, `bazi.drains.length > 0`, `astrology.{attraction,tension,growth}.length > 0`, and `numerology.{complementarity,missing_traits}.length > 0`.
* No new endpoints, no new collections, no chart recompute. Reuses the *same* calculators already proven correct on the forum path.

### Option R2 — Surface "Open Relationship Insight" from `/people/[id]` (UX only)
* Add a button on `/people/[id]` that routes to `/relationship-insight?name={person.name}&context={relationship_type}` so the spouse page no longer feels relationally-thin even when the V2 endpoint is fixed.
* Plus optionally a 5th `EvidenceLine` on the evidence panel: `BaZi — birth date present ⇒ Day-Master and elemental balance can be computed.`
* No backend changes.

Implementing **R1 alone** restores BaZi visibility on the relationship-insight screen for Pete↔Mel without any spouse-page changes. **R1 + R2** also makes the spouse page aware that BaZi is a lens.

**No edits have been made. Awaiting your direction.**

---

**Constraints honored:** read-only audit, no code changes, no deploys, no flag flips, no DB writes. All four feature flags (`INTENT_ROUTER_V2_CUTOVER`, `INTENT_ROUTER_V2_ROLLOUT_PERCENT`, `RELATIONSHIP_ORCHESTRATION_PROMPT`, `CROSS_LENS_PROMPT_SURFACE`) untouched.
