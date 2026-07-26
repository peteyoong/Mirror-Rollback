# RECOMMENDED SESSION-3 PROMPT — Human Design Rebuild

Copy the block below into a new chat when you're ready to kick off
Session-3. It is deliberately bounded so Session-3 delivers ONE lens
rebuild cleanly rather than sprawling.

---

## PROMPT (paste as-is)

PERSONAL MIRROR SESSION 3 — HUMAN DESIGN REBUILD (STRUCTURE FIRST)

Session 2 is accepted. Shared Lens Content Contract + adapter + Heart/Ego
canonicalizer + Variant-A degree tests + Gene Keys IP policy have all
shipped and pass 19/19 tests. See:
- /app/memory/personal_mirror_session2_audit_2026_07.md
- /app/memory/personal_mirror_audit_2026_07.md
- /app/memory/personal_mirror_roadmap_2026_07.md

Session-3 scope is Phase 3 from the master rebuild plan — Human Design
only. Structure work FIRST, narrative rebalancing SECOND.

BOUNDED SCOPE (do all of this, nothing more):

1. STRUCTURAL SURFACE COMPLETION (Phase 3A–3E)
   - Expose the full HD structure through the shared contract:
     Type, Strategy, Authority, Profile, Definition (with Split-Small /
     Split-Wide / Triple sub-classifier), Signature, Not-Self theme,
     Incarnation Cross (verify get_incarnation_cross_full against GM),
     defined + undefined centres, channels, gates, personality/design
     activations, hanging gates.
   - Ship the Personality/Design planetary-activation TABLE
     (Sun/Earth/North Node/South Node/Moon/Mercury/Venus/Mars/Jupiter/
     Saturn/Uranus/Neptune/Pluto × conscious/unconscious × gate/line/centre).
     Data unavailable → mark unavailable, do not fabricate.
   - Ship the dedicated Channels section: for Pete verify and interpret
     35–36, 37–40, 63–4 at minimum with 9-field envelope (gates,
     centres, circuit, capacity, relational expression, distortion,
     interaction with authority, interaction with type, interaction
     with profile, interaction with definition).
   - Replace the generic centre boilerplate. Head + Ajna must interpret
     Pete's specific gates (61, 63 / 4, 47) and Channel 63-4.
   - Apply canonicalize_centers() to EVERY remaining backend endpoint
     that emits a centre list (deep-dive prose paths, mechanics
     endpoint, prompts). Test the union.
   - Alias chart["channels"] = chart["defined_channels"] for GM parity.
   - Variables/PHS: audit "wrong acoustics" / "wrong lighting" /
     "distance creates confusion" strings against source engine. Either
     label with provenance or withhold behind an explicit
     "content_provenance: unverified" gate.

2. HD ADAPTER POPULATION
   - Fill the CORE STORY / COMPONENT STORIES / INTEGRATION / EVIDENCE
     layers of `adapt_human_design(...)` with real content sourced from
     the existing HD deep-dive endpoint (no new calculation engines).
   - CORE STORY must draw from at LEAST 3 of these 11 threads
     (Session-2 audit §3f): initiation/impact, emotional clarity,
     5/1 investigative intelligence, 5-line projection field, tribal
     agreements, willpower, conceptual doubt, experience/change,
     migration, split-definition, complete channels. "Acting before
     emotional clarity" may appear but MUST NOT dominate.
   - Every MaterialClaim must satisfy validate_governance() —
     evidence-backed and capacity ≠ distortion.

3. TESTS
   - test_hd_lens_structure_completeness — 4 personality/design
     planet rows minimum surfaced with gate + line + centre + origin
   - test_hd_lens_canonical_centres_end_to_end — canonicalizer applied
     everywhere; no legacy alias leaks in any HD endpoint response
   - test_hd_lens_core_story_not_dominated_by_acting_before_clarity —
     tokenise the CoreStory prose; the exact phrase and its close
     variants must not appear in more than one of the seven core-story
     slots
   - test_hd_lens_channel_narratives_35_36_37_40_63_4 — those three
     channels for Pete each have a populated 9-field ComponentStory
   - test_hd_lens_variables_phs_provenance — every PHS string is
     either labelled with content_provenance OR marked unavailable
   - All Session-1 (5) + Session-2 (14) tests must still pass

4. UI
   - Wire the HD lens deep-dive route through LensContractView so the
     new envelope actually renders on `/lenses/human_design` — Deep Dive
     tab. Keep the current legacy view as a fallback if the envelope is
     empty. Do not touch other lens routes.

NON-NEGOTIABLES:
- No calculation-engine duplication
- No lens narrative rewrites for astrology / numerology / bazi /
  enneagram / gene keys (those are their own sessions)
- No cross-lens synthesis
- Missing information over false coherence
- No deploy

DELIVERABLES (Session-3 exit criteria):
- All 5 Session-3 tests green
- Session-1 + Session-2 tests still green (24 total)
- Live playwright screenshot of Pete's HD deep dive showing the new
  envelope with populated CORE STORY + at least 3 COMPONENT STORIES for
  centres and 3 for channels
- Session-3 audit doc at
  /app/memory/personal_mirror_session3_audit_2026_07.md
- Recommended bounded Session-4 prompt (Astrology or Gene Keys — pick
  the higher-user-value lens next based on Session-3 findings)

---

Do NOT paste the copy-blocks or the outer heading — just the "PROMPT"
section starting at "PERSONAL MIRROR SESSION 3 ..." — that is the
kickoff message.
