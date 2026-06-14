# BaZi Evidence Layer V2 — Live Payload Branch Audit (Read-Only)

**Date:** 2026-06-14
**Surface:** Pete ↔ Mel on `/api/forum-mappings` and `/api/relationship-insight-v2`
**Hypothesis under test:** "`signals.bazi.diagnostics` is missing or empty in
the live API response, causing the defensive fallback branch to render."
**Verdict:** **HYPOTHESIS FALSIFIED.** Diagnostics are present and
fully populated on both endpoints. The main `MAIN-EVIDENCE` renderer
branch should be selected by both surfaces for every probed pair.

---

## 1. Method

Hit each endpoint live (`localhost:8001`), parse JSON, walk the
`signals.bazi` block of the Pete↔Mel mapping, and report the exact
fields the frontend renderer reads to decide the branch:

```js
// Branch decision (from RelationshipInsightV2Card.tsx & forums/mappings.tsx)
if (!diag || !diag.element_a || !diag.element_b) {
    return <legacy flat list>;     // fallback
}
return <four-section evidence>;    // main
```

Read-only. No code, no rebuild, no deploy, no DB writes.

---

## 2. Endpoint A — `POST /api/forum-mappings`

**Payload:** `{user_id: 697f0c6abf35c0528ff06954, forum_id: 69dd05eaa333335fcbf3ad33}`
(Pete & Mel private forum)

```
success            : true
mappings.length    : 1                 (Mel — Pete is excluded as self)

mappings[0].member_name : "Mel"
signals.bazi keys       : ['build_marker', 'diagnostics', 'growth',
                            'support', 'v2_card']
support.length          : 3
tension.length          : 0
growth.length           : 2

diagnostics present?    : YES
  element_a       : 'Metal'
  element_b       : 'Water'
  cycle           : 'a_produces_b'
  animal_a        : 'Monkey'
  animal_b        : 'Rooster'
  animal_relation : 'neutral'
```

**Branch decision:** `diag != null && element_a && element_b` → **MAIN evidence renderer fires.** Not the fallback.

---

## 3. Endpoint B — `GET /api/relationship-insight-v2`

**Payload:** `?other_name=Mel&context=spouse` for Pete's user_id.

```
success            : true
version            : v5_3layer
other_name         : "Mel"
you_name           : "Pete"

signals.bazi keys  : ['activates_growth', 'diagnostics', 'drains',
                      'strengthens']
strengthens.length      : 3
drains.length           : 0
activates_growth.length : 2

diagnostics present?    : YES
  element_a       : 'Metal'
  element_b       : 'Water'
  cycle           : 'a_produces_b'
  animal_a        : 'Monkey'
  animal_b        : 'Rooster'
  animal_relation : 'neutral'
```

**Branch decision:** identical positive — **MAIN evidence renderer fires.**

(Note the schema shape difference between the two endpoints — forum
mappings emits `support / tension / growth`; insight V2 emits the
Slice-2-era adapted `strengthens / drains / activates_growth`. The
renderer code reads the correct keys per surface — confirmed in the
source.)

---

## 4. Side check — Yoong family pairs (Thaddeus, Isaac)

To rule out "maybe diagnostics are missing for some pairs but not
Mel", I queried `POST /api/forum-mappings` for the Yoong family
forum (`69dda348de9cb1c83c0780fa`).

| Member          | diag? | element_a | element_b | cycle           | s/t/g  | branch         |
| --------------- | :---: | :-------: | :-------: | --------------- | :----: | -------------- |
| Mel             | ✅    | Metal     | Water     | a_produces_b    | 3/0/2  | MAIN-EVIDENCE  |
| Thaddeus Yoong  | ✅    | Metal     | Wood      | a_controls_b    | 2/1/2  | MAIN-EVIDENCE  |
| Isaac Yoong     | ✅    | Metal     | Fire      | b_controls_a    | 3/1/0  | MAIN-EVIDENCE  |

All three pairs yield `MAIN-EVIDENCE` branch. **No pair Pete is
currently viewing in his data triggers the fallback.**

---

## 5. Conclusion

The hypothesis is falsified by direct payload inspection.

- `signals.bazi.diagnostics` is **PRESENT** on both endpoints.
- All gating fields (`element_a`, `element_b`) are **POPULATED**.
- All four pairs probed (Pete↔Mel × 2 endpoints, Pete↔Thaddeus,
  Pete↔Isaac) resolve to the **MAIN-EVIDENCE** renderer branch.

If a user is currently seeing the *fallback* flat list ("`+ thing`",
"`- thing`", "`↑ thing`") on either of these surfaces for Pete↔Mel, the cause must be
**client-side, not API-side**. Candidates ranked by likelihood:

1. **Browser caching the pre-parity bundle.** The deployed `entry-*.js`
   (sha-256 `6377fa2cf402…`) carries the new renderer (verified in the
   previous audit), but a service worker / CDN edge / browser disk cache
   may still be serving the older artifact. A hard reload that bypasses
   service-worker + disk cache will refresh it.
2. **A different surface than the audited two.** Some legacy surface
   (older relationship card, an embedded preview, the Mirror Chat
   inline summary) may still render `signals.bazi.support|tension|growth`
   as a flat list by design — those are not bound to the new evidence
   renderer.
3. **A device/browser where the bundle hash differs.** Worth
   capturing the bundle file URL the actual viewer is loading
   (Network panel → `entry-*.js` filename) and confirming it matches
   `entry-b3cdf036630b6f659f0a728a5bb5b997.js`. If the filename
   differs, the viewer is on a stale build.
4. **A pair whose chart data lacks BaZi diagnostics** (would require
   `element_a` or `element_b` to be null/empty). For Pete↔Mel,
   Pete↔Thaddeus, Pete↔Isaac all three return populated diagnostics
   — so this is not the case here.

**Recommended next read-only step (not yet performed, to honour the
"do not code" guardrail):** ask the viewer to open browser DevTools →
Network → find the active `entry-*.js` request, paste its filename
+ response size, and compare against the deployed
`entry-b3cdf036630b6f659f0a728a5bb5b997.js  (3,976,097 b, SHA-256
6377fa2c…)`. A filename or size mismatch is sufficient to confirm a
stale bundle is in play. No deploy or rebuild needed to confirm.

---

## 6. Evidence Reproducibility

The exact commands used (read-only, idempotent, run against
`localhost:8001`):

```bash
# Endpoint A
curl -s -X POST "http://localhost:8001/api/forum-mappings" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"697f0c6abf35c0528ff06954","forum_id":"69dd05eaa333335fcbf3ad33"}'

# Endpoint B
curl -s "http://localhost:8001/api/relationship-insight-v2/697f0c6abf35c0528ff06954?other_name=Mel&context=spouse"
```

Outputs reproduced verbatim in §2 and §3 above.
