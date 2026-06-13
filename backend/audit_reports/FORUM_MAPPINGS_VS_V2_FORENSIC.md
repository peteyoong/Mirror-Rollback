# FORUM-MAPPINGS vs RELATIONSHIP-INSIGHT-V2 — SIDE-BY-SIDE FORENSIC

**Date:** 2026-06-13 (read-only)
**Subject pair:** Pete (`697f0c6abf35c0528ff06954`) ↔ Mel (`697ec826ad4b18f75bf42616`)
**Trigger:** the user's "How This Person Maps To Me" screen shows the diagnostics footer marker `relationship-mapping-diagnostics-footer-v1` with `role: spouse / src: forum_relationship_edges` — confirming the screen is **NOT** the V2 card my R1 work targeted. This audit reconciles the two surfaces.
**Mutation policy:** read-only. No code changes, no deploys, no DB writes, no feature-flag changes.

---

## 0. Bottom line (read this first)

> **Your screen is `/api/forum-mappings`, not `/api/relationship-insight-v2`. The two endpoints render largely overlapping data, but they're not the same code path and they're not equivalent in coverage.**
>
> 1. **BaZi content is IDENTICAL on both endpoints** for Pete↔Mel — verbatim, byte-equal strings (3 support / 0 tension / 2 growth). My R1 work did **not** add any new BaZi content — it only adapted the forum-shape keys for the V2 card's TS interface (`support → strengthens`, `growth → activates_growth`). The forum endpoint has had this BaZi content live since 2026-04-13.
> 2. **The forum surface already renders all of it.** `mappings.tsx` L860–877 iterates `support` (+ ), `tension` (−), and `growth` (↑). Nothing about BaZi is filtered, suppressed, or hidden at the forum UI layer. The 🐒 Monkey ↔ 🐓 Rooster line is reachable via the "Why this is so strong" accordion's ELEMENTAL DYNAMICS subsection.
> 3. **The richer relational content is on the FORUM side, not on V2.** Forum returns 6 HD channels (vs V2's 3), a full V2-deep-astrology card (`core_relational_pattern`, `emotional_safety_loop`, `communication_loop`, `conflict_signature`, `repair_condition`, `spouse_specific_translation`, `ic_emotional_foundation`, build marker `relationship-mapping-deep-astrology-v2`), and an enneagram `friction_pattern` line that V2 has no slot for.
> 4. **Astrology is the only lens where V2 currently has MORE simple-line content than forum.** Forum returns `attraction/tension/growth = 0/0/0` and sets `legacy_hidden_due_to_v2: true` because the deep V2-card astrology has taken over. V2 returns `1/1/1` simple lines because it calls `compute_astrology_signals` directly without the forum's V2-card-pivot logic. Different data shapes, both intentional.

---

## 1. Endpoint coverage matrix (live probes for Pete↔Mel)

| Lens | `/api/forum-mappings` ("How This Person Maps To Me") | `/api/relationship-insight-v2` ("Between you and Mel" card) | Notes |
|---|---:|---:|---|
| `human_design` | **6** channels | **3** channels (V2 takes first 5; here only 3 were resolved) | Different selection logic; forum reads all `defined_channels`, V2 caps + filters |
| `astrology.attraction` | 0 | **1** | Forum hides legacy lines (`legacy_hidden_due_to_v2: true`) — surfaces a V2 deep-astrology card instead (see below) |
| `astrology.tension` | 0 | **1** | same |
| `astrology.growth` | 0 | **1** | same |
| `astrology.v2_card` & deep fields | **present** (8 fields + supporting_signals[5]) | **absent** | Forum-only enrichment, marker `relationship-mapping-deep-astrology-v2` |
| `bazi.support` / `bazi.strengthens` | **3** | **3** | **Byte-identical strings** (forum→V2 key-mapped) |
| `bazi.tension` / `bazi.drains` | 0 | 0 | identical |
| `bazi.growth` / `bazi.activates_growth` | **2** | **2** | **Byte-identical** including the 🐒↔🐓 line |
| `enneagram.how_you_help_them` / `gift_to_them` | **2** | **2** | identical strings |
| `enneagram.how_they_help_you` / `gift_to_you` | **2** | **2** | identical strings |
| `enneagram.friction_pattern` | **1** | **absent (dropped)** | V2 TS type has no slot for this |
| `numerology` | `null` | `{complementarity: [], missing_traits: []}` | Both effectively empty for this pair |

**Totals (countable lines actually surfaced):**
- Forum-mappings: 6 HD + 0/0/0 astro + 3/0/2 BaZi + 2/2/1 enneagram + 0 numer + **rich V2 astrology card (~8 narrative fields + 5 supporting signals)** = **30 distinct content units**
- V2 insight: 3 HD + 1/1/1 astro + 3/0/2 BaZi + 2/2 enneagram + 0 numer = **15 distinct content units**

---

## 2. Direct answers

### A. Which endpoint powers "How This Person Maps To Me"?

**`/api/forum-mappings`** — proved on three planes:

1. **Source file** `/app/frontend/app/forums/mappings.tsx` (file size 59 KB, mtime 2026-05-31) is the only component that:
   - Calls `getForumMappings(...)` from `services/api.ts` → `POST /api/forum-mappings`
   - Contains the literal `relationship-mapping-diagnostics-footer-v1` (L888) — the marker your screen showed
2. **Backend log lines** during the live probe match the screen's footer fields exactly:
   ```
   [RelationshipMappingV2] pair=Pete<->Mel role=spouse source=forum_relationship_edges
   [ForumMapping] Pete ↔ Mel: 6 channels
   ```
3. **The screen renders forum-shape keys** (`signals.bazi.support`, `signals.bazi.tension`, `signals.bazi.growth`) — not V2-shape keys (`strengthens`, `drains`, `activates_growth`). It would not be capable of rendering V2's output without code changes.

### B. Is richer BaZi content only wired into `relationship-insight-v2` and not `forum-mappings`?

**No — the opposite.** Both endpoints ultimately call the same function:

```python
# services/forum_hd_mapping.py
def compute_bazi_signals(chart_a, chart_b, name_a, name_b, pronouns_b=None) -> dict:
    return {"support": [...], "tension": [...], "growth": [...]}
```

* Forum-mappings reads it via `compute_full_relationship_mapping` (since 2026-04-13).
* V2 insight reads it via the R1 import I added 2026-06-13 (server.py:14397). I then **renamed the keys** for the V2 card's TS interface: `support → strengthens`, `tension → drains`, `growth → activates_growth`.

The Pete↔Mel BaZi strings are **byte-identical** on both endpoints:

```
FORUM signals.bazi.support[0]    : "Your core nature is precision, discernment (Metal)…"
V2    signals.bazi.strengthens[0]: "Your core nature is precision, discernment (Metal)…"
FORUM signals.bazi.growth[1]     : "🐒 Monkey meets 🐓 Rooster — different generational energies…"
V2    signals.bazi.activates_growth[1] : "🐒 Monkey meets 🐓 Rooster — different generational energies…"
```

R1 added **zero** new BaZi content; it just made the V2 card *also* able to surface what the forum endpoint had been computing all along.

### C. Is `forum-mappings` rendering all available BaZi signals or only a subset?

**All of them.** The forum UI (`mappings.tsx` L855–879) explicitly maps all three forum-shape arrays:

| Forum array | Render glyph | Renders all? |
|---|:---:|:---:|
| `signals.bazi.support` | `+` (green) | ✅ all items |
| `signals.bazi.tension` | `−` (red) | ✅ all items |
| `signals.bazi.growth` | `↑` (blue) | ✅ all items |

For Pete↔Mel: 3 `+` + 0 `−` + 2 `↑` = **5 BaZi lines rendered** on the forum screen, **all** of them — including the 🐒 Monkey ↔ 🐓 Rooster line under `↑` (BaZi growth). No suppression, no de-dupe, no cap.

**Caveat — gating chain that determines whether the user can SEE these lines:**

The forum screen wraps all five lenses inside a single "Why this is so strong" accordion (`mappings.tsx` L568–585). The accordion's open-gate (L585–589) is:
```ts
const hasEnnea = !!signals?.enneagram && Object.keys(signals.enneagram).length > 0;
const hasBazi  = !!signals?.bazi      && Object.keys(signals.bazi).length > 0;
const hasNumer = !!signals?.numerology && (signals.numerology.themes?.length || 0) > 0;
```
For Pete↔Mel: `hasBazi = true` (the bazi object has keys `support` and `growth`). So the BaZi block is reachable. **No BaZi content is being silently dropped.**

If your screen looks like it's missing the 🐒↔🐓 line, two diagnostic checks:
1. Is the "Why this is so strong" accordion expanded? (one tap opens it).
2. The forum screen also shows a short BaZi animal teaser pill above the accordion via `baziAnimal` (L107–115). That pill picks **only one** line that matches an emoji animal regex. So the Monkey/Rooster line is double-surfaced — once in the pill and once in the accordion's ELEMENTAL DYNAMICS subsection.

### D. Side-by-side payload diff (Pete↔Mel)

Each row is one verbatim line. Truncation at ~115 chars marked with `…`.

#### HUMAN DESIGN
| | Forum (6 ch) | V2 (3 ch) |
|---|---|---|
| channel ids | `5-15, 6-59, 21-45, 35-36, 37-40, 39-55` | `35-36, 37-40, 63-4` |
| overlap | `35-36, 37-40` | (2 of 6 forum channels appear; V2's `63-4` is not in forum's set) |
| schema | forum returns full channel records | V2 returns `{channel, name, translation}` triples |

*This is a known divergence: V2's HD plumbing reads `db.charts.human_design.defined_channels` directly with a `[:5]` cap and different filter logic. The forum path uses `forum_hd_mapping`'s richer extractor.*

#### ASTROLOGY
| | Forum | V2 |
|---|---|---|
| `attraction[0]` | *(empty — V2 card takes over)* | `Your drive activates something soft in Mel — she opens up in response to your directness, not despite it` |
| `tension[0]` | *(empty)* | `You process information differently enough that the same conversation can feel productive to one and circular to the other` |
| `growth[0]` | *(empty)* | `You hold Mel to a higher standard than most people do — she grows because of it, but may resist in the moment` |
| `legacy_hidden_due_to_v2` | `true` (forum intentionally hides simple lines because V2-card is present) | n/a |
| `v2_card.headline` + `body` | present (forum-only) | absent |
| `core_relational_pattern` | `Pete's Sun in Pisces (processes through atmosphere, emotional permeability, subtle signals)…` | absent |
| `emotional_safety_loop` | `Pete feels safe through lands through directness. Mel feels safe through needs trust earned…` | absent |
| `communication_loop` | `Pete feels toward connection; Mel talks toward connection. Mel may believe explanation IS…` | absent |
| `conflict_signature` | `Pete's Moon (fire) and Mel's Moon (water) read conflict differently — one as activity, the…` | absent |
| `repair_condition` | `name the asymmetry out loud before debating content.` | absent |
| `spouse_specific_translation` | `Mel thinks explaining IS presence. Pete may experience that explanation-without-emotional-…` | absent |
| `ic_emotional_foundation` | `Mel's emotional foundation is shaped by Virgo on the IC — lands through small acts of care…` | absent |
| `supporting_signals` | list of 5 sub-signals | absent |
| build marker | `relationship-mapping-deep-astrology-v2` | n/a |

#### BAZI — byte-identical content
| | Forum (`support`/`tension`/`growth`) | V2 (`strengthens`/`drains`/`activates_growth`) |
|---|---|---|
| [+0] | `Your core nature is precision, discernment (Metal) — Mel's is momentum, adaptability (Water)` | **identical** |
| [+1] | `Your Metal energy naturally nourishes Mel's Water — you feed what they need to grow` | **identical** |
| [+2] | `You anchor things when Mel feels ungrounded — your steadiness is something they lean on` | **identical** |
| [−...] | *(none)* | *(none)* |
| [↑0] | `This works best when acknowledged — otherwise you may feel like you're giving more than you're receiving` | **identical** |
| [↑1] | `🐒 Monkey meets 🐓 Rooster — different generational energies that expand each other's perspective` | **identical** |

#### ENNEAGRAM
| | Forum | V2 |
|---|---|---|
| `gift_to_them` ↔ `how_you_help_them` | 2 lines (same text) | 2 lines (same text) |
| `gift_to_you` ↔ `how_they_help_you` | 2 lines (same text) | 2 lines (same text) |
| `friction_pattern` | **1 line:** `You open doors she wants to walk through — but you struggle to stay in one room long enough for her to finish…` | **DROPPED** — V2 TS type has no slot |

#### NUMEROLOGY
| | Forum | V2 |
|---|---|---|
| value | `null` | `{complementarity: [], missing_traits: []}` |
| effective | both empty for this pair | both empty for this pair |

---

## 3. Implications for the user's screen experience

1. **The Monkey ↔ Rooster line was already visible on the forum screen** under the BaZi accordion (ELEMENTAL DYNAMICS, `↑` row). It has been there since the forum endpoint shipped on 2026-04-13. If you weren't seeing it, the accordion was likely collapsed.
2. My R1 + activates_growth work added the same line to the **V2 card** (a different screen at `/relationship-insight?name=Mel`). That work is correct, but it does **not** affect the forum screen because the forum screen renders forum-shape keys directly.
3. **The forum screen is structurally richer than the V2 card** in 4 of 5 lenses (HD, deep astrology, enneagram friction, BaZi parity). V2 only wins on simple-line astrology, and even there forum has chosen to suppress those in favor of the deep card.
4. The only thing the **forum** screen is missing for Pete↔Mel that the **V2** has is the three simple-line astrology entries — and those are intentionally suppressed by the forum's `legacy_hidden_due_to_v2: true` flag because a *richer* deep-astrology card has taken their place.

---

## 4. Recommendation framing (NOT applied — for your direction)

If the goal is **"the forum screen should also expose what V2 newly exposes"** — there's nothing to do. BaZi is already 100% surfaced there. V2's R1 wiring did not add new BaZi content; it just unlocked the same content on the V2 card.

If the goal is **"surface forum's enneagram friction_pattern in the V2 card too"** — that's a one-line UI tweak on V2 (add a `friction_pattern` slot to the TS type and a `.map` block under GROWTH GIFTS). Out of R1 scope.

If the goal is **"bring forum's deep V2 astrology card onto V2 insight too"** — that's a moderate plumbing job: import `astrology_dynamics` from `forum_hd_mapping`'s deep extractor into the V2 endpoint and add a render branch on the V2 card. Worth doing only if you want a single rich relational surface; otherwise the forum already serves this role.

If the goal is **"forum should render the legacy astrology lines"** — flip `legacy_hidden_due_to_v2` off in the forum payload builder (it's currently `true` because forum prefers the deep-card). Not advised — would create duplicate content next to the deep card. The hide-toggle is doing its job.

---

## 5. Reproducibility (read-only)

```bash
PETE="697f0c6abf35c0528ff06954"
FORUM="69dd05eaa333335fcbf3ad33"

# Confirm screen ↔ endpoint binding
grep -n "relationship-mapping-diagnostics-footer-v1" /app/frontend/app/forums/mappings.tsx
# → 888: relationship-mapping-diagnostics-footer-v1
grep -n "getForumMappings\|forum-mappings" /app/frontend/app/forums/mappings.tsx | head -3
# → screen calls /api/forum-mappings only

# BaZi byte equality
diff <(curl -s -X POST http://localhost:8001/api/forum-mappings \
        -H 'Content-Type: application/json' \
        -d "{\"forum_id\":\"$FORUM\",\"user_id\":\"$PETE\"}" \
        | jq -r '.mappings[] | select(.member_name=="Mel") | .signals.bazi.growth[]') \
     <(curl -s "http://localhost:8001/api/relationship-insight-v2/$PETE?other_name=Mel&context=spouse" \
        | jq -r '.signals.bazi.activates_growth[]')
# → no diff

# Forum returns 5 BaZi lines total
curl -s -X POST http://localhost:8001/api/forum-mappings -H 'Content-Type: application/json' \
  -d "{\"forum_id\":\"$FORUM\",\"user_id\":\"$PETE\"}" \
  | jq '.mappings[] | select(.member_name=="Mel") | .signals.bazi | {s:(.support|length), t:(.tension|length), g:(.growth|length)}'
# → {"s":3,"t":0,"g":2}

# Backend log confirms forum src
grep "RelationshipMappingV2.*Mel" /var/log/supervisor/backend.err.log | tail -1
# → [RelationshipMappingV2] pair=Pete<->Mel role=spouse source=forum_relationship_edges
```

---

## 6. One-paragraph bottom line

The user's "How This Person Maps To Me" screen at `/app/frontend/app/forums/mappings.tsx` is powered by `/api/forum-mappings` (proven by the diagnostics footer marker `relationship-mapping-diagnostics-footer-v1` and the `source=forum_relationship_edges` log entry). **BaZi content is byte-identical on both endpoints** — Pete↔Mel returns the same 3 `support` and 2 `growth` strings in both places, including the 🐒↔🐓 Monkey-Rooster line, all rendered with no UI suppression on the forum screen (the lines live inside the "Why this is so strong" accordion's ELEMENTAL DYNAMICS subsection). The R1 wiring fix from earlier today added the *same* BaZi content to a *different* screen (the `/relationship-insight` V2 card) by reusing the same `compute_bazi_signals` function — it did not create new content. **The richer relational data actually lives on the FORUM side, not on V2**: forum has 6 HD channels (vs V2's 3), a complete V2-deep-astrology card with 8 narrative fields + 5 supporting signals (which V2 lacks entirely), and an enneagram `friction_pattern` line that V2's TS type has no slot for. The only lens where V2 has *more visible content* than forum is astrology simple-lines (1/1/1) — and that's because forum has intentionally suppressed those (`legacy_hidden_due_to_v2: true`) in favor of its richer deep-astrology card.

**No DB writes, no code changes, no deploys, no flag flips occurred.**
