# Why Mirror Sees This — Evidence Tray
**Delivery Report**

| Field | Value |
|---|---|
| Slice | Evidence/proof tray under WHY THIS PERSON MATTERS |
| Status | **GREEN — bundle compiles, zero new TS errors, prettifier verified against live Pete↔Mel** |
| Scope | **Frontend only** — uses existing `proof` payload already flowing from the producer |
| Flag | Re-uses existing `RELATIONSHIP_CURRICULUM_ENGINE` (no new flag) |
| Default state | **Collapsed** (tappable header reveals on demand) |
| Backend changes | **None** (zero schema, zero migration, zero prompt) |

---

## 1. What landed

A collapsible "Why Mirror sees this" tray inside the WHY THIS PERSON MATTERS section.

### Render rules
- Visible only when `data.signals.relationship_curriculum.success === true` (inherited gate)
- Default **collapsed** with a `chevron-down` toggle
- Expanded: shows up to 5 proof groups (`Astrology / Human Design / Enneagram / BaZi / Numerology`)
- Each group rendered ONLY if `items.length > 0` — empty layers stay hidden
- Each line passed through `prettifyProofLine()` then bulleted
- Footer caveat: *"Evidence, not verdict.  These are the signals that landed in Mirror's read — not predictions about you."*

### Prettifier rules (FE-only — backend strings untouched)
| Pattern (input from backend) | Output (rendered) |
|---|---|
| `Descendant in Gemini → curiosity, …` | `Gemini Descendant → curiosity, …` |
| `Gemini ruler (Mercury) in Pisces, house 3` | `Mercury (Gemini ruler) in Pisces, house 3` |
| `Sun in Gemini activates 'curiosity'` | `Sun in Gemini → activates curiosity` |
| `Manifestor ↔ Reflector dynamic → …` | `Manifestor ↔ Reflector → …` |
| `BaZi day pillars: water ↔ earth` | `BaZi day-pillars: water ↔ earth` |
| anything else | (unchanged) |

If no rule matches the input string passes through untouched — never invents content.

---

## 2. Live Pete↔Mel sample (current flag state: ON)

When the tray is expanded, this is what renders today:

```
WHY MIRROR SEES THIS                                          ▲

ASTROLOGY
  • Gemini Descendant → curiosity, perspective-taking, dialogue
  • Mercury (Gemini ruler) in Pisces, house 3
  • Sun in Gemini → activates curiosity
  • Sun in Gemini → activates perspective-taking
  • Sun in Gemini → activates dialogue

HUMAN DESIGN
  • Manifestor ↔ Reflector → initiating without controlling
    outcomes, reflecting without disappearing

Evidence, not verdict.  These are the signals that landed
in Mirror's read — not predictions about you.
```

Enneagram / BaZi / Numerology rows hidden because their arrays are empty for this pair.  No fake "Pluto 7th" appears anywhere — Pete's chart simply doesn't carry it, so the proof ledger doesn't either.

---

## 3. Files touched

| File | Change |
|---|---|
| `frontend/components/RelationshipInsightV2Card.tsx` | Added `prettifyProofLine()` helper (top of file), `proofExpanded` useState, and the tray render inside the WTPM section |

**Zero backend edits.  Zero `.env` edits.  Zero new tests/files.**

---

## 4. Guardrails honoured

| Constraint | Honoured | Evidence |
|---|---|---|
| Additive only | ✅ | new render block + 1 helper + 1 useState; no removals |
| Flag-gated under existing `RELATIONSHIP_CURRICULUM_ENGINE` | ✅ | tray inherits visibility from the parent WTPM section |
| Frontend-only | ✅ | zero backend / `.env` changes |
| No prompt changes | ✅ | LLM prompts not touched |
| No backend schema changes | ✅ | reuses existing proof payload |
| Default collapsed | ✅ | `useState(false)` |
| Render only groups with data | ✅ | `.filter(g => g.items.length > 0)` |
| Plain-language bullets | ✅ | prettifier verified against live data |
| Evidence tone, not verdict | ✅ | footer caveat baked in |

---

## 5. Bundle + regression health

- `tsc --noEmit -p tsconfig.json` → **zero new TS errors** in `RelationshipInsightV2Card.tsx`
- Metro bundles cleanly; `http://localhost:3000` → HTTP 200
- Full pytest sweep: **88/88 PASS** (Relationship Field V2, FCAC Slices A/B, Astro Re-Story V1 producer+wiring, Curriculum producer+wiring) — zero regressions
- Backend live Mirror Chat traffic continues at 200 OK

---

## 6. Reversibility

The tray inherits the existing `RELATIONSHIP_CURRICULUM_ENGINE` flag — flipping the backend flag back to `false` hides the entire WTPM section (including this tray) in one move.  No additional flag needed.

— end of report —
