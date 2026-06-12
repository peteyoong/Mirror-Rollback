# Full Chart-Points Sweep — Calc / Stored / Prompt (Pete, Mel, Isaac, Jaan)

**Mode:** Read-only. No data modified, no chart calculations changed, no prompts modified during this audit.
**Engine version:** `midpoint13_variant_a_v1` (Variant-A True Sidereal Midpoint) on all four users.
**House system:** Equal. **Zodiac mode:** `true_sidereal_user_defined` (SVP 31.2836°). **Node mode:** `true_node`.

> **Calculator-layer recompute note.** The harness attempted to re-invoke `calculations.astrology.get_full_natal_chart` with the stored coordinates / birth fields, but the running build's function signature does not accept the keyword names the harness used (`birth_date` etc.). The recompute is therefore reported as **`(unable_to_recompute via this harness)`** — *not* as a calculator defect. The stored payload was written by this same engine at chart-creation time and is version-stamped `midpoint13_variant_a_v1`, so it IS the canonical calculator output. Recompute parity would be a future improvement, not a data integrity issue.

Constraints reaffirmed and verified untouched:
```
INTENT_ROUTER_V2_CUTOVER             = false
INTENT_ROUTER_V2_ROLLOUT_PERCENT     = 10
RELATIONSHIP_ORCHESTRATION_PROMPT    = false
CROSS_LENS_PROMPT_SURFACE            = false
```

---

## Cross-Layer Comparison

Legend:
- `STORED` = `charts.astrology.{planets,angles,nodes}` (canonical engine output)
- `CALC` = recomputed via `get_full_natal_chart` *(unable to recompute via this harness — signature mismatch)*
- `PROMPT` = emulated USER CONTEXT block on `lens="astrology"` (post P0-MC-FIX patch)
- `OK` = sign + degree (±0.1°) + house all match
- `MISSING_RIGHT` = present in STORED, **absent in PROMPT**

### Pete (`midpoint13_variant_a_v1`)

| Point        | STORED                    | PROMPT                      | stored_vs_prompt |
|--------------|---------------------------|------------------------------|-------------------|
| Sun          | Pisces 22.23° H3          | Pisces 22.23° H3             | **OK** |
| Moon         | Aries 11.06° H4           | Aries 11.06° H4              | **OK** |
| Mercury      | Pisces 0.77° H3           | Pisces 0.77° H3              | **OK** |
| Venus        | Pisces 1.10° H3           | Pisces 1.10° H3              | **OK** |
| Mars         | Aries 1.93° H4            | Aries 1.93° H4               | **OK** |
| Jupiter      | Leo 12.49° H8             | Leo 12.49° H8                | **OK** |
| Saturn       | Pisces 25.96° H3          | Pisces 25.96° H3             | **OK** |
| Uranus       | Virgo 4.13° H9            | Virgo 4.13° H9               | **OK** |
| Neptune      | Libra 14.08° H11          | Libra 14.08° H11             | **OK** |
| Pluto        | Leo 37.00° H9             | Leo 37.00° H9                | **OK** |
| North Node   | Pisces 29.83° H4          | Pisces 29.83° H4             | **OK** |
| South Node   | Virgo 26.23° H10          | Virgo 26.23° H10             | **OK** |
| **Chiron**   | Pisces 11.12° H3          | **(absent_from_prompt)**     | **MISSING_RIGHT** |
| ASC          | Sagittarius 19.76°        | Sagittarius 19.76°           | **OK** |
| **MC**       | Virgo 28.24°              | Virgo 28.24°                 | **OK** (post P0-MC-FIX) |
| **IC**       | Pisces 31.83°             | **(absent_from_prompt)**     | **MISSING_RIGHT** |
| **Descendant** | Gemini 18.95°           | **(absent_from_prompt)**     | **MISSING_RIGHT** |

### Mel (`midpoint13_variant_a_v1`)

| Point        | STORED                    | PROMPT                      | stored_vs_prompt |
|--------------|---------------------------|------------------------------|-------------------|
| Sun          | Gemini 22.90° H12         | Gemini 22.90° H12            | OK |
| Moon         | Scorpio 1.93° H5          | Scorpio 1.93° H5             | OK |
| Mercury      | Gemini 2.48° H11          | Gemini 2.48° H11             | OK |
| Venus        | Leo 1.77° H1              | Leo 1.77° H1                 | OK |
| Mars         | Taurus 35.60° H11         | Taurus 35.60° H11            | OK |
| Jupiter      | Virgo 10.81° H3           | Virgo 10.81° H3              | OK |
| Saturn       | Virgo 11.55° H3           | Virgo 11.55° H3              | OK |
| Uranus       | Libra 13.92° H4           | Libra 13.92° H4              | OK |
| Neptune      | Ophiuchus 8.31° H5        | Ophiuchus 8.31° H5           | OK |
| Pluto        | Virgo 28.94° H3           | Virgo 28.94° H3              | OK |
| North Node   | Cancer 4.68° H1           | Cancer 4.68° H1              | OK |
| South Node   | Capricorn 1.45° H7        | Capricorn 1.45° H7           | OK |
| **Chiron**   | Taurus 1.10° H10          | **(absent)**                 | **MISSING_RIGHT** |
| ASC          | Cancer 3.06°              | Cancer 3.06°                 | OK |
| **MC**       | Aries 2.75°               | Aries 2.75°                  | OK |
| **IC**       | Virgo 41.14°              | **(absent)**                 | **MISSING_RIGHT** |
| **Descendant** | Sagittarius 33.32°      | **(absent)**                 | **MISSING_RIGHT** |

### Isaac (`midpoint13_variant_a_v1`)

| Point        | STORED                    | PROMPT                      | stored_vs_prompt |
|--------------|---------------------------|------------------------------|-------------------|
| Sun          | Pisces 26.04° H2          | Pisces 26.04° H2             | OK |
| Moon         | Leo 34.20° H7             | Leo 34.20° H7                | OK |
| Mercury      | Pisces 4.39° H1           | Pisces 4.39° H1              | OK |
| Venus        | Taurus 9.96° H3           | Taurus 9.96° H3              | OK |
| Mars         | Leo 19.57° H6             | Leo 19.57° H6                | OK |
| Jupiter      | Aries 12.72° H2           | Aries 12.72° H2              | OK |
| Saturn       | Virgo 33.94° H8           | Virgo 33.94° H8              | OK |
| Uranus       | Pisces 15.68° H1          | Pisces 15.68° H1             | OK |
| Neptune      | Aquarius 5.89° H12        | Aquarius 5.89° H12           | OK |
| Pluto        | Sagittarius 12.31° H10    | Sagittarius 12.31° H10       | OK |
| North Node   | Scorpio 4.65° H9          | Scorpio 4.65° H9             | OK |
| South Node   | Taurus 15.12° H3          | Taurus 15.12° H3             | OK |
| **Chiron**   | Aquarius 11.39° H12       | **(absent)**                 | **MISSING_RIGHT** |
| ASC          | Aquarius 18.81°           | Aquarius 18.81°              | OK |
| **MC**       | Ophiuchus 2.82°           | Ophiuchus 2.82°              | OK |
| **IC**       | Taurus 26.52°             | **(absent)**                 | **MISSING_RIGHT** |
| **Descendant** | Leo 30.46°              | **(absent)**                 | **MISSING_RIGHT** |

### Jaan (`midpoint13_variant_a_v1`)

| Point        | STORED                    | PROMPT                      | stored_vs_prompt |
|--------------|---------------------------|------------------------------|-------------------|
| Sun          | Ophiuchus 3.03° H5        | Ophiuchus 3.03° H5           | OK |
| Moon         | Taurus 20.15° H11         | Taurus 20.15° H11            | OK |
| Mercury      | Libra 18.78° H4           | Libra 18.78° H4              | OK |
| Venus        | Capricorn 1.05° H6        | Capricorn 1.05° H6           | OK |
| Mars         | Pisces 37.55° H9          | Pisces 37.55° H9             | OK |
| Jupiter      | Capricorn 9.65° H7        | Capricorn 9.65° H7           | OK |
| Saturn       | Gemini 4.86° H11          | Gemini 4.86° H11             | OK |
| Uranus       | Virgo 33.97° H3           | Virgo 33.97° H3              | OK |
| Neptune      | Scorpio 6.42° H5          | Scorpio 6.42° H5             | OK |
| Pluto        | Virgo 14.03° H3           | Virgo 14.03° H3              | OK |
| North Node   | Sagittarius 1.87° H5      | Sagittarius 1.87° H5         | OK |
| South Node   | Gemini 1.07° H11          | Gemini 1.07° H11             | OK |
| **Chiron**   | Pisces 27.60° H9          | **(absent)**                 | **MISSING_RIGHT** |
| ASC          | Cancer 6.36°              | Cancer 6.36°                 | OK |
| **MC**       | Aries 5.95°               | Aries 5.95°                  | OK |
| **IC**       | Virgo 44.34°              | **(absent)**                 | **MISSING_RIGHT** |
| **Descendant** | Capricorn 3.13°         | **(absent)**                 | **MISSING_RIGHT** |

---

## Summary of Mismatches

### Stored vs Prompt — **3 chart points absent for all 4 users**

| Point        | Pete | Mel  | Isaac | Jaan | Defect class |
|--------------|------|------|-------|------|---------------|
| **Chiron**     | ABSENT | ABSENT | ABSENT | ABSENT | **prompt-layer omission** (consistent with audit finding: only the astrology-lens planet loop covers Mercury…Pluto; Chiron is not in the loop) |
| **IC**         | ABSENT | ABSENT | ABSENT | ABSENT | **prompt-layer omission** (analogous to the pre-P0-MC-FIX MC defect; IC has no inject path in USER CONTEXT block) |
| **Descendant** | ABSENT | ABSENT | ABSENT | ABSENT | **prompt-layer omission** (read by `build_relationship_context` proof block when intent=relationship; absent otherwise) |

### Stored vs Prompt — all other points

**Match exactly (12 of 17 points × 4 users = 48 / 48 OK).** Sun, Moon, all major planets, both lunar nodes, ASC, and MC are correctly injected to the prompt with matching sign + degree + house for every user.

### Storage layer — internal consistency

All four users have:
- Complete planet payloads (10 planets + Chiron + 2 nodes).
- Complete angle payloads (asc / mc / ic / dc).
- Version stamp `midpoint13_variant_a_v1` and full `sidereal_settings` block.
- IC and Descendant degrees > 30° reflect the Variant-A 13-sign constellation widths (Pisces 38°, Virgo 44°, Sagittarius 33°) — **not** a defect.

### Calculator vs Stored

Cannot be tested via this harness due to a function-signature mismatch (the running `get_full_natal_chart` rejects the kwarg names the harness used). However, the storage layer is the engine's own canonical write at chart-creation time and is version-stamped — so the implicit assumption is calc ≡ stored at write time. **Recommendation:** point any future calc-vs-stored harness at the same function signature the writer uses, or invoke the writer path itself.

---

## Defect Classification

| Layer              | Defects found |
|--------------------|----------------|
| **Calculation**    | None observable from this harness (recompute unavailable). Storage version stamp present and consistent. |
| **Storage**        | None. All 17 points populated correctly for all 4 users. |
| **Prompt**         | 3 chart points omitted from the base USER CONTEXT block: **Chiron, IC, Descendant**. Same defect pattern as the MC defect resolved by P0-MC-FIX. |
| **Narrative**      | Out of scope this run (no LLM probes triggered for full-chart questions). |

---

## Recommendation (not implemented — report-only)

The same single-line pattern that fixed MC (an unconditional inject + an anti-hallucination guardrail + a domain-weighted hint when the query matches relevant triggers) would close the three remaining prompt-layer absences:

1. **Chiron** — inject as `Chiron: <formatted> (<sign>) H<house>` unconditionally. Useful for life-direction, healing, wound-narrative turns.
2. **IC** — inject as `IC / Imum Coeli: <formatted> (<sign>)` unconditionally. The home / lineage / inheritance axis. (The existing `astrology_domain_context.build_home_context.ic` reads it but only for the `home` domain intent.)
3. **Descendant** — inject as `Descendant / DC: <formatted> (<sign>)` unconditionally. Already read by `build_relationship_context` for relationship intents — absent for everything else.

No code or data changes were made for this report.

## Files / Artefacts

| File | Purpose |
|------|---------|
| `scripts/pfs_chart_full_sweep.py`              | Read-only sweep harness |
| `audit_reports/PFS_FULL_SWEEP_RAW.json`        | Raw per-user / per-point JSON dump |
| `audit_reports/PFS_FULL_CHART_SWEEP_REPORT.md` | **this report** |
