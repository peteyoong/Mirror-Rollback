# BaZi Evidence Layer V2 — AUDIT & PROPOSAL (no code yet)

**Date:** 2026-06-14
**Scope:** Read-only audit of the current `ELEMENTAL DYNAMICS` renderer on the forum "How This Person Maps To Me" screen, and a concrete renderer-only redesign proposal. **No BaZi math, no `compute_bazi_signals` changes, no chart writes, no migrations, no flag changes.**
**Test pair:** Pete ↔ Mel (spouse, Metal→Water, Monkey/Rooster).

---

## 1. Audit — current ELEMENTAL DYNAMICS renderer

### 1.1 Source location
`/app/frontend/app/forums/mappings.tsx`, L899–L925. The current code is a flat triple-`.map()`:

```tsx
<Text style={styles.signalsNote}>ELEMENTAL DYNAMICS</Text>
{signals.bazi.support?.map((item, i) => (<Row icon="+" item={item} />))}
{signals.bazi.tension?.map((item, i) => (<Row icon="−" item={item} />))}
{signals.bazi.growth?.map((item, i) => (<Row icon="↑" item={item} />))}
```

There is no grouping, no section header per category, no use of `diagnostics.element_a`/`element_b`/`cycle`/`animal_*`, and no distinction between "structural facts" and "behavioural observations." All three arrays render as a single visually-uniform list with only colour-coded glyph differentiation.

### 1.2 Current data structure (live, Pete ↔ Mel)

```json
"signals": {
  "bazi": {
    "support":  [3 strings — see below],
    "growth":   [2 strings — see below],
    "v2_card":  { ...wisdom-mode V3 card... },
    "diagnostics": {
      "element_a": "Metal", "element_b": "Water",
      "cycle": "a_produces_b",
      "animal_a": "Monkey", "animal_b": "Rooster",
      "animal_relation": "neutral",
      "role_key": "spouse",
      "support_count": 3, "tension_count": 0, "growth_count": 2
    },
    "build_marker": "relationship-mapping-bazi-narrative-v1"
  }
}
```

Note: **`signals.bazi.tension` is `[]` for this pair** (no drains). The current renderer renders nothing for the tension bucket, so users see only `+` and `↑` rows — no `−` rows.

### 1.3 Current verbatim strings (Pete↔Mel, what the user sees today)

| Bucket | # | String |
|---|---|---|
| `support[0]` | + | "Your core nature is precision, discernment (Metal) — Mel's is momentum, adaptability (Water)" |
| `support[1]` | + | "Your Metal energy naturally nourishes Mel's Water — you feed what they need to grow" |
| `support[2]` | + | "You anchor things when Mel feels ungrounded — your steadiness is something they lean on" |
| `tension`     | − | *(none)* |
| `growth[0]` | ↑ | "This works best when acknowledged — otherwise you may feel like you're giving more than you're receiving" |
| `growth[1]` | ↑ | "🐒 Monkey meets 🐓 Rooster — different generational energies that expand each other's perspective" |

### 1.4 Where these strings come from (provenance)

All 5 strings are produced by `services/forum_hd_mapping.compute_bazi_signals(...)` lines ~1043-1115. The function dates back to **2026-04-13** (`ddb09ade`) and **predates the wisdom-mode V3 narrative engine by ~2 months**. The strings were written when there *was* no narrative layer — they were the entire BaZi UX. They are now structurally overlapping with V3.

### 1.5 Overlap analysis with wisdom-mode V3 narrative

| Current evidence string | Wisdom-mode V3 section already covering the same idea |
|---|---|
| `support[0]` — "Your core nature is precision (Metal) — Mel's is momentum (Water)" | **Core Dynamic** (V3 §1) — "It is the geometry of Metal meeting Water — production downstream, reception upstream" |
| `support[1]` — "Your Metal energy naturally nourishes Mel's Water" | **Core Dynamic** (V3 §1) — "current that runs one way… production downstream, reception upstream" |
| `support[2]` — "You anchor things when Mel feels ungrounded — your steadiness is something they lean on" | **What Strengthens** (V3 §2) — "the dynamic itself, doing its work… the producing as its own integrity" |
| `growth[0]` — "This works best when acknowledged — otherwise you may feel like you're giving more than you're receiving" | **Growth Edge** (V3 §3) — "integrity is not the same as reception. The work Pete does has its own truth even when no one is tracking it" |
| `growth[1]` — "🐒 Monkey meets 🐓 Rooster — different generational energies that expand each other's perspective" | **What Strengthens** (V3 §2) when animal=harmony or **What BaZi Sees Here** (V3 §6) closer when animal=clash |

**Verdict:** every current evidence row is a weaker paraphrase of something the wisdom layer already said upstream. This is exactly the "narrative depth collapses" experience you described.

### 1.6 Root cause of the experience problem

* **Wrong genre.** The current strings are *interpretive* English sentences, not observational mechanics. They tell the same story the wisdom layer just told, only with fewer words.
* **No structural anchor.** The renderer never shows what the structural facts *are* (element-pair, cycle direction, animal relation, who occupies which role in the cycle). Users see conclusions without seeing the geometry the conclusions rest on.
* **Uniform visual treatment.** A single colour-coded list reads as a single rhetorical register. There is no signal that this layer is *evidence*, not *more narrative*.

---

## 2. Proposed renderer structure (presentation-only, no math changes)

### 2.1 Four grouped sections (per your spec)

```
ELEMENTAL DYNAMICS                                 ← unchanged outer header

╭─ 1. Elemental Structure ─────────────────────╮
│ Pete:                            Metal       │
│ Mel:                             Water       │
│ Relationship Geometry:           Metal → Water│
│ Direction of Flow                            │
│   Pete refines    →    Mel adapts            │
│   Pete structures →    Mel metabolises       │
│   Pete names      →    Mel responds          │
│ Year Animals      Monkey · Rooster · neutral │
╰──────────────────────────────────────────────╯

╭─ 2. What Strengthens the Flow ───────────────╮
│ ✓ <support signal #1, in evidence phrasing>  │
│ ✓ <support signal #2>                        │
│ ✓ <support signal #3>                        │
╰──────────────────────────────────────────────╯

╭─ 3. Growth Trigger ──────────────────────────╮
│ ↑ Monkey ↔ Rooster                           │
│   Growth comes through perspective expansion.│
│   <growth signal #1, in evidence phrasing>   │
│   <growth signal #2 if present>              │
╰──────────────────────────────────────────────╯

╭─ 4. Shadow Signal ───────────────────────────╮
│ ⚠ <tension signal #1>   (renders only when   │
│ ⚠ <tension signal #2>    tension array is    │
│                          non-empty)          │
╰──────────────────────────────────────────────╯
```

### 2.2 Section data sources (zero new compute)

| Section | Data source | Notes |
|---|---|---|
| **1. Elemental Structure** | `signals.bazi.diagnostics.{element_a, element_b, cycle, animal_a, animal_b, animal_relation}` + the two name strings already on the page | All values **already in the payload today**. No backend changes required. |
| **2. What Strengthens the Flow** | `signals.bazi.support[]` | Reuse existing array, **rephrased to evidence register** (see §2.4). |
| **3. Growth Trigger** | `signals.bazi.growth[]` + `diagnostics.animal_a/b/animal_relation` | Existing data. Lead with animal pair as the title row. |
| **4. Shadow Signal** | `signals.bazi.tension[]` | Existing data. **Section hidden entirely** when array is empty (Pete↔Mel case). |

### 2.3 The "Direction of Flow" mini-table (Section 1, sentence-level)

This is the highest-value addition because it makes the geometry concrete. It's a **deterministic 6-element-pair × 3-cycle = small lookup table** computed in the renderer (not in the BaZi engine, not in compute_bazi_signals). For productive cycle (`a_produces_b` or `b_produces_a`), three short verbs per element-pair:

| Producer | Receiver | Three verbs |
|---|---|---|
| Wood | Fire | Wood ignites · Wood feeds · Wood fuels // Fire expresses · Fire amplifies · Fire shows |
| Fire | Earth | Fire warms · Fire deposits · Fire enriches // Earth holds · Earth absorbs · Earth gathers |
| Earth | Metal | Earth concentrates · Earth pressurises · Earth refines // Metal extracts · Metal precipitates · Metal clarifies |
| **Metal** | **Water** | **Metal refines · Metal structures · Metal names** // **Water adapts · Water metabolises · Water responds** |
| Water | Wood | Water nourishes · Water moves · Water carries // Wood grows · Wood receives · Wood extends |

For control cycle (`a_controls_b` / `b_controls_a`), the verbs invert: "checks", "shapes", "bounds" on the controller side; "yields", "softens", "redirects" on the controlled side.

For `same`, "Direction of Flow" becomes "Shared Operating Mode" with three matching verbs.
For `neutral`, "Direction of Flow" becomes a one-liner "No automatic cycle — flow is built by agreement."

**All of this is a render-time lookup table — no engine change.** It is observational and structural; it does not reuse wisdom-mode phrasing.

### 2.4 Rephrasing the existing strings into evidence register

The existing strings are interpretive; the evidence layer needs to read **observational and structural**. I propose the renderer **does not invent new sentences** — instead, the renderer **adapts the existing strings to evidence register via a small, deterministic transform** that strips the "you / Mel" subject and reframes as a structural observation. Two implementation options:

**Option A — Render-time prefix transform (purely cosmetic, zero engine touch).**
* `support[0]` "Your core nature is precision (Metal) — Mel's is momentum (Water)" → split into two static rows in Section 1: `Pete: Metal` / `Mel: Water`. The string itself is hidden (its info is now structural).
* `support[1]` "Your Metal energy naturally nourishes Mel's Water" → moved to Section 1's "Relationship Geometry: Metal → Water" header. String hidden.
* `support[2]` "You anchor things when Mel feels ungrounded" → kept in Section 2 as a `✓` bullet, prefixed with a structural label: **"Stabilising function:** You tend to provide structure when the system loses coherence". The label-then-colon pattern shifts the register from narrative to observational.
* `growth[0]` "This works best when acknowledged…" → Section 3 with label: **"Acknowledgement asymmetry:** Production requires recognition to remain unhurt."
* `growth[1]` "🐒 Monkey meets 🐓 Rooster…" → Section 3 title row, animal pair shown structurally + the existing line as the explanation.

The transform is a small lookup: each existing string → `{label, evidence_phrasing}`. The original string can be hover/long-press revealed if you want a "see original" affordance, but is hidden by default.

**Option B — New backend field `signals.bazi.evidence` with pre-shaped phrasing.**
Add a sibling field that the engine fills with evidence-shaped rephrasings, alongside the existing `support`/`tension`/`growth` arrays (which stay unchanged for the V2 card and any other consumers). The new field would look like:
```json
"evidence": {
  "structure": { "element_a": "Metal", "element_b": "Water",
                 "cycle": "a_produces_b",
                 "verbs_a": ["refines","structures","names"],
                 "verbs_b": ["adapts","metabolises","responds"] },
  "strengthens": [{"label":"Precision is received","line":"..."}],
  "growth_trigger":[{"label":"Acknowledgement asymmetry","line":"..."}],
  "shadow":[{"label":"Ledger formation","line":"..."}]
}
```
This is a **slightly larger backend change** (still no BaZi math — just a new build-marker'd derived field), and avoids putting copywriting logic in the renderer.

**My recommendation: Option A.** It is purely a renderer change (matches your "Presentation and organization only" constraint), keeps `compute_bazi_signals` literally untouched, and makes the V3 card immune to any future evidence-layer redesign. The structural labels are a small, audited renderer-side dictionary.

### 2.5 Visual treatment shift (signals this is evidence, not narrative)

| Visual element | Wisdom layer (above) | Evidence layer (below — proposed) |
|---|---|---|
| Section header style | Section title in body-weight text (`Core Dynamic`, etc.) | Smaller all-caps subhead per group + a thin top border on each card |
| Body text | Prose paragraphs | Short labelled bullets + a structural mini-table |
| Glyph use | None | `✓` strengthens · `↑` growth · `⚠` shadow · `→` flow direction |
| Card framing | Single flowing read | 4 visually-distinct framed cards |
| Typography | Comfortable line-height for reading | Tighter, monospaced for the structure table |

No new components — reuses existing `styles.lensSection` + a small new `styles.evidenceCard` definition (1 style addition).

---

## 3. Before / After — Pete ↔ Mel

### 3.1 BEFORE (current production behaviour)

```
ELEMENTAL DYNAMICS
+ Your core nature is precision, discernment (Metal) — Mel's is momentum, adaptability (Water)
+ Your Metal energy naturally nourishes Mel's Water — you feed what they need to grow
+ You anchor things when Mel feels ungrounded — your steadiness is something they lean on
↑ This works best when acknowledged — otherwise you may feel like you're giving more than you're receiving
↑ 🐒 Monkey meets 🐓 Rooster — different generational energies that expand each other's perspective
```

(5 visually-uniform rows; each row re-says something the wisdom layer just said in better English.)

### 3.2 AFTER (proposed)

```
ELEMENTAL DYNAMICS

┌─ Elemental Structure ───────────────────────────────┐
│  Pete                                          Metal│
│  Mel                                           Water│
│  Relationship Geometry                  Metal → Water│
│                                                     │
│  Direction of Flow                                  │
│    Pete refines       →     Mel adapts              │
│    Pete structures    →     Mel metabolises         │
│    Pete names         →     Mel responds            │
│                                                     │
│  Year Animals             Monkey · Rooster · neutral│
└─────────────────────────────────────────────────────┘

┌─ What Strengthens the Flow ─────────────────────────┐
│  ✓  Stabilising function                            │
│     Pete tends to provide structure when the system │
│     loses coherence.                                │
│                                                     │
│  ✓  Asymmetric nourishment                          │
│     Metal contributions land in Water without       │
│     having to be matched.                           │
│                                                     │
│  ✓  Receptive recognition                           │
│     Mel's mode allows Pete's precision to take root │
│     rather than bouncing off.                       │
└─────────────────────────────────────────────────────┘

┌─ Growth Trigger ────────────────────────────────────┐
│  ↑  🐒 Monkey  ↔  🐓 Rooster                          │
│     Growth comes through perspective expansion.     │
│     You rarely grow in the same way — you grow by  │
│     exposing each other to different worlds.       │
│                                                     │
│  ↑  Acknowledgement asymmetry                       │
│     Production requires recognition to remain      │
│     unhurt. When unnamed, the flow inverts.        │
└─────────────────────────────────────────────────────┘

(Section 4 — Shadow Signal — hidden, tension array is empty)
```

The structural facts now lead. Each evidence bullet has a **structural label** (Stabilising function / Asymmetric nourishment / Acknowledgement asymmetry) that reads as an observation, not a story. The shadow section is absent because Pete↔Mel has no tension signals — its hide-when-empty behaviour is what makes the section feel rigorous rather than padded.

---

## 4. Renderer regressions & edge cases to handle

| # | Edge case | Current behaviour | Proposed behaviour |
|---|---|---|---|
| 1 | All three arrays empty (no day-master on one side, or new chart) | Renders nothing (`Object.keys(signals.bazi).length > 0` gate fails) | Same — render nothing. Don't show the new outer header in this case. |
| 2 | `tension` array empty (most pairs, including Pete↔Mel) | Renders no `−` rows | Hide the Shadow Signal card entirely. Don't show an empty card. |
| 3 | `support` empty but `tension` non-empty (rare conflict pair) | Renders only `−` rows | Show Section 1 (structure) + Section 4 (shadow). Hide Sections 2 and 3. |
| 4 | `cycle == "same"` (both same element) | Same flat list, "Wood meets Wood" reads odd | Section 1 changes "Direction of Flow" header to "Shared Operating Mode"; renders 3 matching verbs. |
| 5 | `cycle == "neutral"` (no productive/control link) | Same flat list, no acknowledgment of the absence | Section 1 collapses Direction of Flow to a single-line "No automatic cycle — flow is built by agreement." |
| 6 | `animal_relation == "clash"` | Currently the growth string includes the clash glyph; no special framing | Section 3 title row shows `⚠ {animal_a} ↔ {animal_b}` (clash uses warning), evidence line names "Generational instinct divergence". |
| 7 | `animal_relation == "harmony"` | Often appears in support strings as `🐉 ↔ 🐒` style | Section 1 closing row: "Year Animals — Dragon · Monkey · harmony". Section 2 picks up "Synchronised pacing" as a labelled strengthener. |
| 8 | `diagnostics` missing (older payloads pre-wisdom-mode) | n/a | Defensive: render the *original* flat list as a fallback. No regression for legacy data. |
| 9 | Strings contain user names other than the actual viewer (e.g., user pronouns localised to "they") | Currently strings hardcode "You / Mel" | Strings remain unchanged. The new structural labels are name-agnostic. |
| 10 | Long-press / accessibility | No special handling | New `accessibilityLabel` per evidence bullet contains both the label and the body so screen readers get the full sentence. |
| 11 | Mobile width truncation of "Pete refines → Mel adapts" | n/a (not rendered) | Use `flexShrink: 1` on both sides + `numberOfLines={2}` defensively. Mini-table degrades to stacked rows under ~340px. |
| 12 | Translation/i18n | Strings are English-only | New structural labels are also English-only; live in a single `BAZI_EVIDENCE_LABELS` object so they're trivially externalisable later. |

### Forward-compat
* Forum-mappings consumers (the deployed app, the V2 card via R1, any internal tooling) keep reading `signals.bazi.{support,tension,growth}` as today — **wire format unchanged**.
* The wisdom-mode V3 card on top stays untouched. Bundle marker `What BaZi Sees Here` stays present.
* V2 endpoint mapping (R1) stays unchanged — V2 card's "ELEMENTAL DYNAMICS" block on `RelationshipInsightV2Card.tsx` is a different file; we can leave it alone for this delivery OR mirror the same redesign there (decision needed — see open question below).

### Risks
* **Risk:** the new structural labels are a renderer-side dictionary that has to cover all 25 element pairs × cycle types. Mitigation: it's a small, auditable, deterministic table (≤ 30 entries), kept in one location with a unit-style sanity check that every (cycle, label) combination resolves.
* **Risk:** the original support/growth strings still appear in `signals.bazi.support[]`/`growth[]`, so any downstream consumer that prints them verbatim still gets the old phrasing. Mitigation: this renderer change is local to `mappings.tsx`. If we later want evidence-shaped strings everywhere, that's Option B in §2.4.

---

## 5. Implementation footprint (when you approve)

| Change | File | Approx size |
|---|---|---|
| New renderer block (4 cards replacing the flat list) | `frontend/app/forums/mappings.tsx` (L899-925) | ~140 lines replacing 27 |
| New `BAZI_EVIDENCE_LABELS` lookup table (Direction of Flow verbs, structural strengthener labels by cycle, shadow labels by cycle) | new helper at top of same file, or `frontend/services/bazi/evidenceLabels.ts` (cleaner) | ~80 lines, pure data |
| `styles.evidenceCard` + `styles.evidenceLabel` style additions | same file | ~12 lines |
| `yarn build:deploy` to refresh `backend/web_dist` | n/a | <30 s |
| **NO change to** `compute_bazi_signals`, `relationship_bazi_engine.py`, `forum_hd_mapping.py`, any backend route, any DB document, or any feature flag |  | 0 |

---

## 6. Open questions for you before coding

1. **Mirror the redesign on the V2 card (`RelationshipInsightV2Card.tsx`)?** That card has its own `ELEMENTAL DYNAMICS` block (R1 wiring) at L319-335 that currently renders the same forum-shape strings (mapped to `strengthens/drains/activates_growth`). Same problem will exist there. Two options:
   * (a) Mirror the redesign on the V2 card too — single source of truth.
   * (b) Forum screen only this round; V2 card is a follow-up.
   Recommend **(a)** for visual parity.

2. **Option A vs Option B for the rephrasing (§2.4):**
   * (a) **Renderer-side transform** (recommended): zero backend change, no engine touch. Pure presentation. Constraint-pure.
   * (b) **Backend `signals.bazi.evidence` field**: cleaner separation of concerns, but expands the BaZi engine surface slightly.
   Recommend **(a)** to stay strictly in "presentation and organization only" territory.

3. **Behaviour when `tension` array is empty (Pete↔Mel today):**
   * (a) Hide Section 4 entirely (recommended — feels rigorous).
   * (b) Render Section 4 with a single line "No structural conflict signals on this pair."
   Recommend **(a)**.

4. **Preserve the original interpretive strings somewhere accessible?** They'll no longer be the headline; should they be available behind a "show raw signals" toggle for power users / forensic audits?
   * (a) Hidden entirely — the structural labels carry the meaning.
   * (b) Available behind a long-press / details toggle.
   Recommend **(a)** for now (less UI weight); easy to add later.

5. **Outer header text:** keep `ELEMENTAL DYNAMICS` (current), or rename to `ELEMENTAL DYNAMICS — Evidence` to explicitly signal the role of this layer?
   Recommend **rename to `ELEMENTAL DYNAMICS — Evidence`** — the rename is the cheapest way to communicate "this is proof, not narrative" to the user.

---

## 7. Acceptance criteria (when implemented)

| Criterion | How verified |
|---|---|
| User reads V3 wisdom card → reaches evidence layer → feels the evidence *validates* the narrative rather than repeating it | Visual review on preview |
| All 5 current strings (Pete↔Mel) still reachable in some form — none silently dropped | Manual diff against §3.1 |
| Section 4 (Shadow) hidden for Pete↔Mel (tension=[]) | Live probe |
| Section 1 shows `Pete: Metal` / `Mel: Water` / `Metal → Water` / 3 flow-direction rows / `Monkey · Rooster · neutral` | Visual |
| `signals.bazi.{support,tension,growth}` wire format unchanged on `/api/forum-mappings` | Byte-equal diff of payload field |
| `/api/relationship-insight-v2` Pete↔Mel signals counts unchanged: `hd=3 astro=3 bazi=5 ennea=4` | Live probe |
| Wisdom-mode V3 sections unchanged (Core Dynamic, …, What BaZi Sees Here) | Live probe |
| All 4 constrained feature flags untouched | grep |
| New bundle is_current = true, no STALE flags | `/api/health` |

---

## 8. One-sentence proposal

**Replace the current 5-row flat bullet list under "ELEMENTAL DYNAMICS" with four visually-distinct, hide-when-empty cards — *Elemental Structure* (computed from `signals.bazi.diagnostics`), *What Strengthens the Flow* (existing support strings re-rendered with structural labels), *Growth Trigger* (existing growth strings + animal pair as title), and *Shadow Signal* (existing tension strings, hidden when empty) — driven entirely by a single new renderer-side label dictionary, with zero changes to `compute_bazi_signals`, the BaZi engine, the wire format, the database, or feature flags.**

---

**Awaiting your decisions on the 5 open questions in §6 before I write any code.**
