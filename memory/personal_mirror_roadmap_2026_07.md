# PERSONAL MIRROR — MULTI-SESSION ROADMAP
Companion to `/app/memory/personal_mirror_audit_2026_07.md`
Date: 2026-07-22

This is the sequenced plan for shipping the full "Complete Lens Content
and Coherence Rebuild" (12 phases) after the Session-1 audit + bug fixes.

Session-1 has already SHIPPED:
- Audit doc
- Lens library dynamic count (fix §3a)
- HD centre title "G Center Center" (fix §3b)
- HD Ego/Heart canonicalization on today-diagnosis (fix §3c)
- Phase-11 test scaffold (5 tests, all green)
- Astrology angle-consistency universal test

The remaining sessions are grouped by risk and dependency.

---

## Session-2 (roughly next block) — POLICY DECISIONS + CROSS-CUTTING SCAFFOLDING

Blocks 3-8 until these are decided.

- **§ P5A Astrology degree policy decision** — user picks Option A (raw + label), B (normalized-by-default + drill-down raw), or C (revert to tropical). Recommendation: B. Implementation: 1 session.
- **Shared Lens Content Contract skeleton** — build the 7-section progressive-disclosure envelope defined in Phase 2 as a reusable type + component:
  - `AtAGlanceCard`, `StructureCard`, `CoreStoryCard`, `ComponentStoryCard`, `IntegrationCard`, `EvidenceCard`, `TodayTimingCard`.
  - Backend contract: every lens deep-dive endpoint returns these 7 sections in a canonical envelope.
  - Old code paths keep working via fallback — no big-bang cutover.
- **Cross-lens synthesis layer scaffold (Phase 9)** — new `synthesis_v1.py` service that consumes each lens's evidence bundle and classifies pairs as `CONVERGENCE / COMPLEMENTARITY / PRODUCTIVE_TENSION / DISAGREEMENT / INSUFFICIENT_EVIDENCE`. No content — just structure.
- **Ego/Heart deep-dive live reproduction + test** — playwright script that walks the HD Deep Dive tab and asserts every centre appears exactly once with a single defined/undefined status (blocked in Session-1 because the deep-dive load takes 30-45s and playwright timing was flaky).
- **Full boilerplate similarity test (Phase 11 §16)** — flags any two distinct centres / planets / gates / numbers / pillars whose narratives have Jaccard token overlap ≥ 0.85.

## Session-3 — HUMAN DESIGN REBUILD (Phase 3)

Big session, one lens at a time.

- **Phase 3A**: Verify full HD structure surface — every field from Phase 3's checklist ships in `/human-design/deep-dive`.
- **Phase 3B**: Personality/Design activation table (13 planetary bodies × conscious/unconscious/both × gate/line/centre) — build new `hd_activation_table` endpoint + component.
- **Phase 3C**: Dedicated Channels section — verify Pete's 35-36 / 37-40 / 63-4 render correctly; ship the 9-field-per-channel envelope described in Phase 3C.
- **Phase 3D**: Centres — replace all generic centre boilerplate; per-centre must interpret Pete's specific gates + hanging gates + conditioning; canonical centre-name enforcement in every render path.
- **Phase 3E**: Gates — per-gate 8-field envelope.
- **Phase 3F**: Rebalance the master HD narrative — "acting before emotional clarity" reduced to ONE of many equal threads. Add the 11 other threads listed in Phase 3F.
- **Phase 3G**: Variables/PHS — either fully label with provenance OR withhold until verified. Investigate "wrong acoustics" / "wrong lighting" / "distance creates confusion" — trace to source engine.

## Session-4 — GENE KEYS AS DISTINCT LENS (Phase 4)

- New route `/lenses/gene_keys`
- New lens library card
- Reuse existing activation calculation (do NOT duplicate)
- Activation / Venus / Pearl sequence displays with 8-field-per-sphere envelope
- 4 integrated narratives (Activation, Venus, Pearl, complete Golden Path)
- IP-safe original interpretive copy (no reproduction of licensed source text)

## Session-5 — ASTROLOGY REBUILD (Phase 5, depends on Session-2 policy call)

- **Phase 5A completion**: implement the chosen A/B/C degree policy across backend + FE
- **Phase 5B**: expose full structural coverage — aspect patterns, dispositor tree, chart ruler, angular strength, element/modality balance, mutual receptions, critical degrees
- **Phase 5C**: build the 8-step narrative architecture (Sun-Moon-Asc → planets → generational → nodes/Chiron → angles/houses → aspects → integrated synthesis)
- **Phase 5C**: fix "holds things so tightly" claim — either trace evidence or rewrite

## Session-6 — NUMEROLOGY REBUILD (Phase 6)

- Verify all six existing numbers + Lo Shu with formula display
- Add Maturity / Pinnacles / Challenges / Personal Year/Month/Day / Karmic
- Ship 10 stories per Phase 6 spec
- Kill "almost entirely a Life Path 11 reading" dominance

## Session-7 — ENNEAGRAM DEEPENING (Phase 7)

- Preserve 7w8 assessed result
- Add core desire / fear / passion / fixation / defence / virtue / wing / stress / growth / expressions
- Confidence-score explanation (assessment vs inference)
- Do NOT infer subtype/tritype without assessment provenance

## Session-8 — BAZI REBUILD (Phase 8)

- Full 4-pillar table with hidden stems
- Day Master strength reasoning with method disclosure
- Ten Gods + combinations + clashes + harms + penalties + luck pillars
- Kill reductive language ("calculating underneath" etc.)
- Ship 8 story sections per Phase 8 spec

## Session-9 — CROSS-LENS SYNTHESIS (Phase 9)

- Populate the `synthesis_v1` service scaffold from Session-2 with real classifications
- Build the FE surface for cross-lens views
- Enforce: no lens uses another to validate itself

## Session-10 — UI CONSISTENCY SWEEP (Phase 10)

- Progressive-disclosure enforcement across every lens
- Confidence-level explanations everywhere they appear
- Technical terminology glossary
- Full boilerplate scan + rewrite

## Session-11 — ACCEPTANCE REVIEW (Phase 12)

- Regenerate every lens for pete@pulsifi.me
- Deliver the 12-item deliverable list from Phase 12
- Playwright end-to-end walkthroughs on every lens
- Do NOT deploy until all Phase-11 integrity tests pass

---

## Cross-cutting principles Session-1 already enforced

- ✅ Missing information over false coherence (audit flagged unverified PHS strings and marked pending-verification)
- ✅ Evidence citation required for master insights (test scaffold in place)
- ✅ Canonical vocabulary (centre naming fixed backend-side; FE fallback normalizer added)
- ⏳ Recognition before advice — Session-2+ scope (this is a content rewrite, not a structural fix)
- ⏳ Capacity/shadow/tension distinguishability — enforced at content-contract level in Session-2

---

## Open decisions (blocking downstream work)

1. **Astrology degree policy** — A / B / C (blocks Session-5)
2. **Ego/Heart canonical label** — recommend "Heart/Ego" backend-side (already implemented); "Heart / Ego" display-side. OK?
3. **Gene Keys IP boundary** — how much of the licensed text may we reference verbatim vs. use original interpretive copy? Recommend: original copy only, cite Gene Keys tradition without quoting.
