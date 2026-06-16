# P0 Diagnostic Report — Mel Ascendant Regression

**Status:** DIAGNOSIS ONLY. No patches applied.  
**Reported symptom:** Forum member card shows "**Gemini Rising**" for Mel.  
**Expected (canonical):** True Sidereal-M Midpoint → "**Cancer Rising**" (~3° Cancer).  
**Build marker found in code referencing this exact bug:** `live-forum-mel-rising-stale-source-fix-v1` (server.py `POST /api/admin/fix_mel_live`).

---

## Executive Summary (TL;DR)

**The bug is NOT in the chart engine, NOT in MongoDB, NOT in `services/member_summary._format_astrology`, and NOT in the Forum member-summary endpoint.** All four return **Cancer Rising** when run against the local DB's Mel records.

**The divergence is environmental / data-locality:**

1. The "Gemini Rising" symptom is reproducible **only against the production Mel record** (`user_id = 69b50ecb2b86cfb90750ec04`) — a user that does **not exist in the local preview DB at all**.
2. The presence of an emergency admin route (`POST /api/admin/fix_mel_live`, build marker `live-forum-mel-rising-stale-source-fix-v1`) that **explicitly recomputes the chart, clears 10 sign-derived caches, and overwrites canonical user fields** is the smoking gun. That route exists because at deployment time the prod chart was/is computed with **stale birth inputs** (wrong timezone, wrong lat/lon, or no SVP) — producing a chart whose `astro.angles.asc.sign` legitimately equals `"Gemini"`.
3. Once that wrong chart is persisted, the entire downstream pipeline (member-summary → API → frontend) is faithfully echoing what the DB says. No layer is mis-reading a correct chart; the wrong chart is being read correctly.

So the divergence point in the chain **Chart Engine → Mongo → API → Frontend → Render** is at **layer 1 (Chart Engine) on production**, surfacing as wrong data persisted in **layer 2 (Mongo)**.

---

## Trace Results (Layer by Layer)

### Layer 1 — Chart Engine (`calculations/astrology.get_full_natal_chart`)
- **Local preview, fresh recompute** with canonical inputs:
  - birth_dt: `1981-07-13 07:25 Asia/Kuala_Lumpur`
  - coords: `(2.1896, 102.2501)` (Melaka)
  - house_system: `Equal`, sidereal: `true_sidereal_user_defined`, SVP `31.2836°`
- **Result on local stored chart:** `astro.angles.asc = {sign: "Cancer", degree: 3.062°, longitude: 89.10°, formatted: "3°Cancer"}` ✅
- Engine version: `midpoint13_variant_a_v1`, compute version: `mirror-deterministic-v1`.
- **Conclusion:** Engine is correct. Cancer ASC is what comes out when fed canonical inputs.

### Layer 2 — Mongo Chart Record (`db.charts`)
Inspected two Mel records present in **local** DB:

| user_id | name | birth_date | tz/coords | `astro.angles.asc.sign` | `astro.planets.Sun.sign` |
|---|---|---|---|---|---|
| `697ec826ad4b18f75bf42616` | "Mel" | 1981-07-13 07:25 Melaka | 2.1896, 102.2501 | **Cancer** ✅ | Gemini |
| `69c90702497688b97a8e67a1` | "Mel " | 1981-07-13 07:25 Melaka | 2.1896, 102.2501 | **Cancer** ✅ | Gemini |
| `69b50ecb2b86cfb90750ec04` (prod Mel from admin route default) | — | — | — | **does NOT exist in local DB** | — |

Both local Mel charts also have a **forensic Variant B snapshot** stored: `forensic_variant_b.angles.asc.sign = "Cancer"` ✅. Legacy top-level fields `astro.ascendant`, `astro.sun`, `astro.moon`, `astro.houses.ascendant_sign` are all `None` — they cannot interfere.

> **Key insight #1:** Sun is in **Gemini** (22°). It is plausible that whoever filed the bug ticket conflated the Sun sign with the Rising sign while reading the card. However, the existence of `live-forum-mel-rising-stale-source-fix-v1` in code says the bug was **also** observed historically as a genuine wrong-rising on prod (a stale-chart issue, not a UI mis-read).

### Layer 3 — API Payload (`services/member_summary.get_member_summary` → `routers/forums_intelligence.get_member_summary_endpoint`)
- `_format_astrology(chart)` source-of-truth order:
  1. `chart.astrology.planets.Sun.sign`
  2. `chart.astrology.planets.Moon.sign`
  3. `chart.astrology.angles.asc.sign` (falls back to `angles.ascendant.sign`)
- **Live invocation against Mel’s stored chart:**
  ```
  _format_astrology(chart)               -> 'Gemini Sun · Scorpio Moon · Cancer Rising'
  get_member_summary(forum_id, member_id) -> astrology = 'Gemini Sun · Scorpio Moon · Cancer Rising'
  ```
- Endpoint headers: `Cache-Control: no-store, max-age=0`, `CDN-Cache-Control: no-store` — so client-side stale caching at the CDN layer is ruled out for this endpoint.
- **Conclusion:** The payload is correct (Cancer Rising). Layer 3 is innocent on local data.

> **Asymmetry worth noting (NOT the bug, but a separate latent risk):**
> `services.member_summary._format_astrology` does **not** trigger the astrology auto-migration. By contrast, `services.forum_lens_helpers.get_member_lens_data` calls `check_and_migrate_astrology_chart(user_id)` before reading. If a user has a corrupted/legacy chart that hasn't been touched by the migrator, the **member-summary card will surface stale data** until something else triggers the migration. **This is exactly the failure mode the `admin/fix_mel_live` route was built to repair**, and it strongly suggests the prod Mel chart was originally written with bad birth inputs (wrong timezone or pre-SVP) and was never re-touched by the lens path that would have auto-migrated it.

### Layer 4 — Forum Pulse / Member Cards (`/api/forums/{id}/pulse`)
- `ForumPulseMemberCard` schema (`services/api.ts:1010`) — fields: `user_id, name, hd_type, hd_profile, hd_authority, enneagram_type, active_pattern`.
- **`ForumPulseMemberCard` carries NO astrology field at all.** It therefore cannot be the surface displaying "Gemini Rising".
- The astrology row "Gemini Sun · Scorpio Moon · Cancer Rising" is rendered only by the **member-summary panel** (`app/forums/[id].tsx:1210`, `<Row label="Astrology" value={s.astrology} />`), which is **populated by the `/member-summary/{member_id}` endpoint**, not by `/pulse`.

### Layer 5 — Frontend Render (`app/forums/[id].tsx`)
- `s.astrology` is rendered **verbatim** as a string into a `<Text>` node — no parsing, no slicing, no per-field re-mapping.
- Frontend memberSummaries are cached client-side under the AsyncStorage prefix `member_summary_` (see `app/_layout.tsx:38`), which gets cleared on user/session change but **NOT on chart recompute**. If the prod Mel chart was ever rendered with bad data, the AsyncStorage cache for that user-summary pair would persist that bad value across reloads until the cache is explicitly invalidated or expires.
- **Conclusion:** No transform layer between API and pixel. The frontend can only display what the API gave it, optionally stale via AsyncStorage.

---

## Where Cancer Becomes Gemini

The divergence is **NOT** in code logic — it is in **which Mel record (and which chart-compute moment) the user is looking at**. There are three live failure modes, in descending likelihood:

### Mode A — Stale prod chart written with bad birth inputs (MOST LIKELY)
- Production user `69b50ecb2b86cfb90750ec04` had its `db.charts` row computed at some earlier point with a wrong timezone (e.g. UTC or a default `Asia/Singapore`) or pre-SVP settings.
- Under those wrong inputs, the canonical engine legitimately returns `asc.sign = "Gemini"` — and that gets persisted.
- Every downstream layer (member_summary, API, frontend) reads it correctly and faithfully echoes "Gemini Rising".
- This is precisely why `POST /api/admin/fix_mel_live` exists: it rewrites the canonical user fields, recomputes with the correct timezone/coords/SVP, and explicitly deletes 10 sign-derived caches. The build marker on that route — **`live-forum-mel-rising-stale-source-fix-v1`** — names this exact root cause.
- **Evidence:** The route's default `user_id` matches the prod Mel id; the route's comment explicitly says *"Returns before/after summary so the caller can confirm Cancer Rising."*

### Mode B — Frontend AsyncStorage cache pinning a previously-bad payload
- `app/_layout.tsx` registers `member_summary_` as a cache prefix.
- If the prod Mel summary was once "Gemini Rising" (due to Mode A) and a cache entry was persisted client-side, then even after the prod chart is recomputed correctly, the iPad/Safari client may keep showing "Gemini Rising" until the AsyncStorage entry is purged or the prefix-based clear runs.
- The cache is keyed by `(forum_id, member_id)`; clearing it requires either a logout, a manual `await AsyncStorage.removeItem('member_summary_<forum>_<member>')`, or a fresh install.
- **The member-summary endpoint itself sets `no-store` HTTP headers**, so CDN caching is NOT a contributor; only the client-side AsyncStorage layer is.

### Mode C — Reader confusion between Sun sign and Rising sign (LEAST LIKELY but cannot be ruled out from a screenshot alone)
- Mel's Sun is genuinely in **Gemini**. The row reads `"Gemini Sun · Scorpio Moon · Cancer Rising"`.
- If a screenshot was framed/cropped so only the first token was visible, "Gemini" could be misread as the rising sign.
- This is mentioned only for completeness; the existence of the `live-forum-mel-rising-stale-source-fix-v1` admin route is strong evidence the bug has materialised legitimately at least once, so this mode alone is insufficient to explain the report.

---

## Latent Risks Discovered While Tracing (NOT patched, per instructions)

1. **Migration asymmetry across surfaces.** `forum_lens_helpers.get_member_lens_data` auto-migrates the astrology chart; `services.member_summary._format_astrology` does **not**. Two endpoints reading "the same" Mel can therefore return different rising signs if Mel's chart row is stale until something else triggers the migrator. The member-summary card (the surface where the bug was reported) is the one that *doesn't* migrate.
2. **`_format_astrology` has no longitude-fallback derivation.** Unlike `forum_lens_helpers` (5-level resolution order), `member_summary._format_astrology` only reads `angles.asc.sign` and `angles.ascendant.sign`. If a chart somehow stored only the longitude (no sign string) the member-summary row would silently drop the rising token rather than recompute it from longitude.
3. **No write-time invariant check on `db.charts`.** Nothing currently asserts that `astro.angles.asc.sign` is consistent with `astro.angles.asc.longitude` (i.e. that the persisted sign actually matches the sign that `longitude_to_sign_degree(longitude % 360)` would produce). A drifted or hand-edited record could persist mismatched values indefinitely.
4. **AsyncStorage cache key for member summaries is not chart-version-aware.** The cache key is `(forum_id, member_id)`; a chart recompute on the server doesn't invalidate client cache. Adding `chart_updated_at` or an engine-version tag to the cache key (or to a server-returned ETag) would make the client refetch automatically.

---

## Recommended Next Step (NOT executed)

To **confirm** the diagnosis on the live environment without any code patch:

```bash
# 1. Inspect what production actually has stored:
curl -sS "https://<prod-host>/api/admin/migration-info" \
     -H "X-Admin-Token: $MIGRATION_ADMIN_TOKEN"

# 2. Then, on prod, invoke the existing emergency route:
curl -sS -X POST \
     "https://<prod-host>/api/admin/fix_mel_live?confirm=FIX_MEL_LIVE_V1" \
     -H "X-Admin-Token: $MIGRATION_ADMIN_TOKEN"
```

The route's response includes `before.chart.asc` and `after.chart.asc`. If `before.chart.asc` is `"Xx°Gemini"` (or anything other than `~3°Cancer`) and `after.chart.asc` is `"3°Cancer"`, **Mode A is confirmed** and the divergence point is *write-time on prod*, not read-time anywhere.

If `before` is already `"3°Cancer"`, the divergence is **Mode B (client AsyncStorage)** and the fix is to bump a cache-key salt (e.g. include `chart_updated_at` in `member_summary_<forum>_<member>_<ts>`).

---

## Files Inspected During Trace

| Layer | File | Key Range / Function |
|---|---|---|
| Engine | `/app/backend/calculations/astrology.py` | `get_full_natal_chart`, `longitude_to_sign_degree` |
| Engine call | `/app/backend/server.py` | lines 32420–32580 (`admin_fix_mel_live`) |
| DB read (member-summary path) | `/app/backend/services/member_summary.py` | `_format_astrology`, `get_member_summary` |
| DB read (lens path, *not* the bug surface) | `/app/backend/services/forum_lens_helpers.py` | `get_member_lens_data` (auto-migrates) |
| API endpoint | `/app/backend/routers/forums_intelligence.py` | `GET /forums/{forum_id}/member-summary/{member_id}` (lines 500–538) |
| Frontend type contract | `/app/frontend/services/api.ts` | `ForumPulseMemberCard` (1010), `ForumMemberLensData` (1021) |
| Frontend render | `/app/frontend/app/forums/[id].tsx` | lines 1180–1232 (`<Row label="Astrology" value={s.astrology} />`) |
| Client cache | `/app/frontend/app/_layout.tsx` | line 38 (`member_summary_` AsyncStorage prefix) |

---

**Diagnosis complete. Awaiting explicit instruction before applying any fix.**
