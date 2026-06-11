# Ana Regression Baseline — Intake Package

> **STATUS:** AWAITING USER SUBMISSION
> **CREATED:** Phase 4 — Ana intake collection
> **POLICY:** No DB writes. No user creation. No baseline records. Information gathering only.

Fill in the `[ ]` fields below. Attach screenshots/PDFs to `/app/backend/audit_reports/ana_intake_attachments/` (path TBD when you provide files).

---

## SECTION 1 — REQUIRED BIRTH DATA

### 1.1 Legal birth date
- **Value (YYYY-MM-DD):** `[ ]`

### 1.2 Birth time
- **Value (HH:MM, 24-hour):** `[ ]`
- **Source confidence:** `[ ] birth_certificate  |  [ ] hospital_record  |  [ ] family_memory  |  [ ] rectified  |  [ ] other:____`
- **If rectified — by whom and when:** `[ ]`

### 1.3 Birth location
- **City:** `[ ]`
- **State / Province:** `[ ]`
- **Country:** `[ ]`

### 1.4 Coordinates
- **Latitude (4 dp):** `[ ]`
- **Longitude (4 dp):** `[ ]`
- **Coordinate source:** `[ ] google_maps  |  [ ] gmaps_address_lookup  |  [ ] geocoder_other:____`

### 1.5 Historical timezone verification (we compute; you confirm)
- **Resolved IANA timezone:** `[ to be filled by qa script after submission ]`
- **Historical UTC offset at birth instant:** `[ to be filled by qa script after submission ]`
- **Source-of-truth for historical offset:** `IANA tzdata 2024a + zoneinfo + pytz cross-ref`

> ⚠ Verification report will be auto-generated once §1.1–§1.4 are populated by re-running `python tools/historical_tz_verify_<name>.py`.

---

## SECTION 2 — GENETIC MATRIX PACKAGE

### 2.1 Attachments expected
- `[ ]` Human Design bodygraph PDF — `gm_bodygraph.pdf`
- `[ ]` Human Design summary PDF — `gm_summary.pdf`
- `[ ]` Variables PDF *(optional)* — `gm_variables.pdf`
- `[ ]` Incarnation Cross details page — `gm_cross.pdf`
- `[ ]` Full gate activation listing screenshot — `gm_gates.png`
- `[ ]` Full channel listing screenshot — `gm_channels.png`

### 2.2 Normalised extraction (to be populated from the PDFs)

```yaml
type:               # Generator | Manifestor | Manifesting Generator | Projector | Reflector
strategy:           # To Respond | To Inform | etc.
authority:          # Sacral | Splenic | Emotional | Ego | Self-Projected | Lunar | None
profile:            # e.g. "3/5"
definition:         # None | Single | Split | Triple Split | Quadruple Split

incarnation_cross:
  name:             #
  gates:            # e.g. "30/29 | 4/49"
  personality_sun:  #
  personality_earth:#
  design_sun:       #
  design_earth:     #

personality_gates:  # list of ints
design_gates:       # list of ints
defined_channels:   # list of "g1-g2"
defined_centers:    # list
undefined_centers:  # list
design_datetime_utc_iso:  # ISO from Genetic Matrix
```

---

## SECTION 3 — ASTROLOGY PACKAGE

### 3.1 Attachments expected
- `[ ]` Astro.com natal wheel PDF (tropical, Equal houses, includes Chiron + Nodes) — `astrocom_natal.pdf`
- `[ ]` Astro.com aspect table PDF — `astrocom_aspects.pdf`
- `[ ]` Planet positions table screenshot — `astrocom_planets.png`
- `[ ]` House cusps table screenshot — `astrocom_cusps.png`

### 3.2 Configuration assumed
- **Zodiac:** tropical
- **House system:** Equal Houses
- **Bodies:** Sun → Pluto, Chiron, North Node, South Node
- **Orbs for aspect table:** Astro.com defaults (we will normalise on import)

### 3.3 Normalised extraction template

```yaml
ascendant:
  long_deg:          # 0–360
  sign:              #
  deg_in_sign:       #

midheaven:
  long_deg:
  sign:
  deg_in_sign:

house_cusps:         # 12 floats

planets:
  Sun:       { long_deg:, sign:, deg_in_sign:, retrograde: false, house: }
  Moon:      { ... }
  Mercury:   { ... }
  Venus:     { ... }
  Mars:      { ... }
  Jupiter:   { ... }
  Saturn:    { ... }
  Uranus:    { ... }
  Neptune:   { ... }
  Pluto:     { ... }
  Chiron:    { ... }
  North Node:{ ... }
  South Node:{ ... }

aspects:
  - { body1:, body2:, type:, orb:, exact_angle: }
  # all major aspects from Astro.com aspect grid
```

---

## SECTION 4 — NUMEROLOGY PACKAGE

### 4.1 Attachments expected
- `[ ]` Numerology calculator screenshot or PDF — `numerology_source.pdf`
- **Calculator used:** `[ ] numerology.com  |  [ ] tokenrock  |  [ ] worldnumerology  |  [ ] other:____`
- **Spelling used for name calculation:** `[ ]` *(exact spelling as it appears on birth certificate)*

### 4.2 Normalised extraction

```yaml
life_path:        # int
expression:       # int (may include master numbers 11/22/33)
soul_urge:        # int
personality:      # int
birthday:         # int
pinnacles:        # array of 4 ints
challenges:       # array of 4 ints
```

---

## SECTION 5 — ENNEAGRAM PACKAGE

### 5.1 Attachments expected
- `[ ]` Enneagram assessment result — `enneagram_result.pdf` or `enneagram_result.png`
- **Assessment used:** `[ ] RHETI (Riso-Hudson)  |  [ ] iEQ9  |  [ ] EnneagramInstitute  |  [ ] EclecticEnergies  |  [ ] other:____`
- **Date of assessment:** `[ ]`

### 5.2 Normalised extraction

```yaml
primary_type:   # 1..9
wing:           # e.g. "4w5"
tritype:        # 3 digits, e.g. "459"   (optional)
instinct_stack: # e.g. "sx/sp"            (optional)
```

---

## SECTION 6 — RELATIONSHIP FIELD PLACEHOLDERS (RESERVED — DO NOT POPULATE YET)

```yaml
relationship_field_with_pete:
  status:                  RESERVED
  populate_after:          Ana baseline locked AND Pete baseline locked
  expected_payload_shape:
    composite_asc_long:    null
    composite_mc_long:     null
    synastry_aspects:      []
    field_tone:            null

relationship_field_with_mel:
  status:                  RESERVED
  populate_after:          Ana baseline locked AND Mel baseline locked
  expected_payload_shape:
    composite_asc_long:    null
    composite_mc_long:     null
    synastry_aspects:      []
    field_tone:            null
```

---

## SECTION 7 — BASELINE READINESS CHECK

| Category | Required items | Provided | Confidence | Status |
|---|---:|---:|---|---|
| Birth data        | 5 fields (date / time / city / lat / lon) | 0 | n/a | ❌ NOT_PROVIDED |
| Astrology         | 4 attachments + planet/cusp/aspect tables | 0 | n/a | ❌ NOT_PROVIDED |
| Human Design      | 2–6 attachments + extracted bodygraph     | 0 | n/a | ❌ NOT_PROVIDED |
| Numerology        | 1 attachment + 7 numeric values            | 0 | n/a | ❌ NOT_PROVIDED |
| Enneagram         | 1 attachment + type + wing                 | 0 | n/a | ❌ NOT_PROVIDED |

**Confidence score formula** (per category):
```
0   = no data
0.4 = partial extraction (some fields filled by hand, no attachment)
0.7 = attachment provided, extraction unverified
1.0 = attachment provided AND extraction verified against engine
```

### Overall readiness

> # `BASELINE_READINESS = NOT_READY`

**Reason:** zero of five required input categories have been submitted. No birth data, no Genetic Matrix package, no Astro.com package, no numerology, no enneagram.

---

## Next steps for the operator

To advance from `NOT_READY` to `PARTIALLY_READY` (then `READY_FOR_PHASE_4A`):

1. Submit §1 birth data (5 fields) — minimum to unlock §1.5 timezone verification.
2. Drop the Genetic Matrix bodygraph PDF into `/app/backend/audit_reports/ana_intake_attachments/`.
3. Drop the Astro.com natal-wheel PDF + aspects PDF in the same folder.
4. Drop the numerology + enneagram screenshots.
5. Reply `RECHECK ANA INTAKE` and I will re-evaluate the readiness scorecard and produce an updated report.

**Threshold transitions:**
- `NOT_READY → PARTIALLY_READY`: birth data + at least one of {Astrology, HD} complete and verified.
- `PARTIALLY_READY → READY_FOR_PHASE_4A`: all 5 categories at confidence ≥ 0.7 AND birth-data verification passed.

---

## Compliance ledger

```json
{
  "phase": "4-intake",
  "writes_performed": 0,
  "users_created": 0,
  "baselines_created": 0,
  "framework_changes": 0,
  "intake_attachments_received": 0,
  "intake_categories_complete": 0,
  "baseline_readiness": "NOT_READY"
}
```
