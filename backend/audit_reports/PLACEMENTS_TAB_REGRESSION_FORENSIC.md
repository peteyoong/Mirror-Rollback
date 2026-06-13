# PLACEMENTS TAB REGRESSION FORENSIC

**Target preview / deployed URL:** `https://mirror-lens-fixes-r-1779710763.emergent.host`
**Generated:** 2026-06-13 (read-only audit — no code changes, no deploys, no migrations, no flag flips)

---

## 0. Headline finding (read this first)

> **This is NOT a regression. The Placements tab has never existed in this repo's source tree, in any committed branch, in any built artifact, or in any deployed bundle.**
>
> Every forensic axis confirms it: the literal strings `AstrologyPlacementsTab`, `placements-tab-v1`, and `GROWTH & PURPOSE` produce **zero** matches anywhere — source, git history (all branches + reflog), `/app/frontend/dist`, `/app/backend/web_dist`, **and the live bundle fetched fresh from the deployed URL.** The deployed bundle and the local bundle have **identical MD5 hashes** — they are the same artifact.
>
> The matching open item from the handoff summary is the **upcoming P0 task**: *"Placements Tab in Astrology Lens (UI currently missing)."* So the correct framing is "feature never built" — not "feature reverted." Whatever you saw on a previous session was almost certainly a different workspace/fork, a planning mockup, or a confusion with the *Core Placements* section that already exists inside the **At a Glance** and **Deep Dive** tabs (both consume the `CorePlacements` type and render Sun/Moon/Asc/Mercury/Venus/Mars/Jupiter/Saturn/Chiron/Nodes already).

---

## 1. Workspace source inspection

### 1A. Does `AstrologyPlacementsTab.tsx` exist?
```bash
$ find /app/frontend -name "AstrologyPlacementsTab*"
# → (empty)
```
**No.** No file by that name exists anywhere in `/app/frontend` (or anywhere else in `/app`).

For reference, the full `frontend/components/astrology/` directory contains exactly these tab components:
```
AstrologyAtAGlanceTab.tsx       (14 KB, Apr 18)
AstrologyDeepDiveTab.tsx        (149 KB, Jun 09)
AstrologySharedComponents.tsx   (5.5 KB, Mar 22)
AstrologyTimelineSection.tsx    (27 KB, Apr 13)
AstrologyTimelineTab.tsx        (55 KB, Jun 09)
AstrologyTodayTab.tsx           (24 KB, Apr 28)
AstrologyTodayV3.tsx            (17 KB, Apr 28)
AstrologyTodayV4.tsx            (36 KB, May 23)
ConstellationOverlayCard.tsx    (14 KB, Apr 18)
```
No `Placements*` file in any form.

### 1B. `AstrologyLensView.tsx` content

File last modified: **2026-04-18**. The relevant excerpts:

| Concern | Evidence (line numbers) |
|---|---|
| `activeTab` union | **L43:** `useState<'at_a_glance' \| 'today' \| 'deep_dive' \| 'timeline'>('at_a_glance')` — **4 values, no `'placements'`** |
| Imports | L23–L28: only `AstrologyAtAGlanceTab`, `AstrologyTodayTab`, `AstrologyTodayV3`, `AstrologyTodayV4`, `AstrologyDeepDiveTab`, `AstrologyTimelineTab`. **No `AstrologyPlacementsTab` import** |
| `renderTabs()` | L223–L258: 4 `TouchableOpacity` blocks — `At a Glance`, `Today`, `Deep Dive`, `Timeline`. **No Placements `TouchableOpacity`** |
| `renderContent()` | L263–L317: branches on `at_a_glance | today | deep_dive | timeline` only |

### 1C. Was the code overwritten later?

Git log for `frontend/components/AstrologyLensView.tsx` shows ~20+ auto-commit revisions on `main`, but a **pickaxe search across all branches, all commits, and the reflog** returns no commit that ever introduced the string `AstrologyPlacementsTab` (see §2). So there is nothing to "overwrite" — the tab was never there to begin with.

---

## 2. Git history forensic

| Query (all branches + reflog) | Hits |
|---|---:|
| `git log --all -S "AstrologyPlacementsTab"` | **0** |
| `git log --all -S "placements-tab-v1"` | **0** |
| `git log --all --grep="[Pp]lacements"` | **0** |
| `git log --all -- '**/AstrologyPlacementsTab*'` | **0** |
| `git fsck --no-reflogs --unreachable` for orphans with the string | none reachable |
| `git stash list` | empty |
| `git log --all -S "CORE IDENTITY"` | 10 commits — **but** all in `HomeInsightV5Card.tsx` / backend `home_insight_v5.py`, **not** in the Astrology Lens (see §4) |
| `git log --all -S "rel-v2-suppression-v2-and-empty-state"` | 3 commits — pertains to relationship-aware astrology / empty-state UX, **not** a Placements tab marker |

The Placements tab was **never added in any commit** that any branch, tag, or reflog entry of this repo's git history can see.

---

## 3. Static deployed-bundle source inspection

### 3A. `/app/frontend/dist` and `/app/backend/web_dist`

Both directories contain the **same single web bundle** (mtime `2026-05-31 03:45:49`):
```
/app/frontend/dist/_expo/static/js/web/entry-a840aeeb2b1699890e640de9e505b634.js
/app/backend/web_dist/_expo/static/js/web/entry-a840aeeb2b1699890e640de9e505b634.js
```
File size: **3,936,149 bytes**
MD5: **`a636bddaa7b57579a3e0055e2cd080b6`** (identical between the two locations)

### 3B. Marker grep against the static bundle

| Marker | Hits in bundle |
|---|---:|
| `AstrologyPlacementsTab` | **0** |
| `placements-tab-v1` | **0** |
| `CORE IDENTITY` | **0** |
| `GROWTH & PURPOSE` | **0** |
| `"Placements"` (as a tab label string) | **0** |
| `Placements` (any context) | **1** — the only hit is `extractPlacements` (an unrelated JS function exported from the astrology service module; this is a *data accessor*, **not** a tab label) |
| `"At a Glance"` | 3 |
| `"Today"` | 24 |
| `"Deep Dive"` | 7 |
| `"Timeline"` | 12 |

Conclusion: the static bundle in this workspace **does not contain a Placements tab** in any form.

---

## 4. Live deployed-URL inspection

### 4A. `index.html` fetch
```http
GET https://mirror-lens-fixes-r-1779710763.emergent.host/

HTTP/2 200
last-modified: Sun, 31 May 2026 03:45:49 GMT
cache-control: no-cache, no-store, must-revalidate, max-age=0
cf-cache-status: DYNAMIC
server: cloudflare
```
Bundle reference inside `index.html`:
```
/_expo/static/js/web/entry-a840aeeb2b1699890e640de9e505b634.js
```

### 4B. JS bundle fetch
```http
GET https://mirror-lens-fixes-r-1779710763.emergent.host/_expo/static/js/web/entry-a840aeeb2b1699890e640de9e505b634.js

HTTP/2 200
content-type: text/javascript; charset=utf-8
content-length: 3936149
etag: "56ed3bb0fbdfab1d23ce0f921ea59f8d"
last-modified: Sun, 31 May 2026 03:45:49 GMT
cache-control: no-cache, no-store, must-revalidate, max-age=0
cf-cache-status: BYPASS
server: cloudflare
```

| Field | Value |
|---|---|
| Bundle filename | `entry-a840aeeb2b1699890e640de9e505b634.js` |
| Last-Modified | **2026-05-31 03:45:49 UTC** |
| ETag | `"56ed3bb0fbdfab1d23ce0f921ea59f8d"` |
| Size | 3,936,149 bytes |
| `cf-cache-status` | `BYPASS` (proves we got origin, not a CF-cached copy) |
| `cache-control` | `no-cache, no-store, must-revalidate` (rules out browser cache as a cause) |
| MD5 of downloaded body | **`a636bddaa7b57579a3e0055e2cd080b6`** |
| BUILD_ID exposed via `EXPO_PUBLIC_BUILD_ID` | `20260514_120951-hotfix` (per `/app/frontend/.env`) — set at build time, no separate "BUILD_ID" in bundle headers |
| Tab labels in deployed bundle | `"At a Glance"`, `"Today"`, `"Deep Dive"`, `"Timeline"` |
| `AstrologyPlacementsTab` in deployed bundle | **0 hits** |
| `placements-tab-v1` in deployed bundle | **0 hits** |
| `CORE IDENTITY` / `GROWTH & PURPOSE` in deployed bundle | **0 hits** |

### 4C. Live vs. local artifact comparison
```
md5 local  : a636bddaa7b57579a3e0055e2cd080b6  /app/backend/web_dist/.../entry-a840aeeb2b1699890e640de9e505b634.js
md5 remote : a636bddaa7b57579a3e0055e2cd080b6  /tmp/deployed_bundle.js
```
**Byte-for-byte identical.** The deployed bundle is the exact same artifact as `/app/backend/web_dist/...` in this workspace.

---

## 5. Cross-section comparison

| Plane | Has `AstrologyPlacementsTab`? | Has `"Placements"` tab label? | Has `placements-tab-v1`? | Has `CORE IDENTITY` (in Astrology surface)? |
|---|:---:|:---:|:---:|:---:|
| Workspace source (`frontend/components/...`) | ❌ | ❌ | ❌ | ❌ (only in HomeInsightV5Card) |
| Git history (all branches + reflog) | ❌ | ❌ | ❌ | ❌ in any Astrology file |
| `/app/frontend/dist` (built artifact) | ❌ | ❌ | ❌ | ❌ |
| `/app/backend/web_dist` (deployment staging) | ❌ | ❌ | ❌ | ❌ |
| **Live `mirror-lens-fixes-r-1779710763.emergent.host`** | **❌** | **❌** | **❌** | **❌** |

Every plane is consistent: the Placements tab does not exist.

---

## 6. Cause determination — which scenario fits?

The user's prompt enumerates six scenarios. Walking each one against the evidence:

| Scenario | Verdict | Why |
|---|---|---|
| **A. Source code reverted** | **Ruled out.** | Pickaxe `git log -S "AstrologyPlacementsTab"` returns 0 across **all** branches and the reflog. You cannot revert what was never committed. |
| **B. Static `web_dist` stale** | **Ruled out.** | The static `web_dist` contains the same MD5 as the live bundle — so even a stale dir would have nothing to do with it. The bundle itself doesn't contain Placements either. |
| **C. Deployment bound to old artifact** | **Ruled out.** | Local `web_dist` and live deployed bundle have identical MD5. The deployed `/api/health` flags a *source-code* staleness (TSX edited 2026-06-09 vs bundle 2026-05-31), but the missing piece in that gap is **`AstrologyDeepDiveTab.tsx`**, not anything Placements-related. No pre-2026-05-31 artifact contained Placements either. |
| **D. Browser / service-worker cache** | **Ruled out.** | Bundle headers are `cache-control: no-cache, no-store, must-revalidate` and `cf-cache-status: BYPASS`. We fetched fresh and confirmed 0 hits. The app does not register a service worker for this path in the current bundle (the JS payload does not call `serviceWorker.register` for the lens views). |
| **E. Wrong deployed URL** | **Highly likely.** | The user's "yesterday" observation is not reproducible against `mirror-lens-fixes-r-1779710763.emergent.host` because that URL has never served a Placements tab from this codebase. If the user has *another* Emergent deployment (a different workspace / fork / branch) that was open in a previous tab, that's the most consistent explanation. |
| **F. Runtime condition hiding tab** | **Logically impossible.** | The literal label string `"Placements"` would need to exist in the bundle for any runtime condition to *hide* it. It does not exist. There is no codepath that conditionally renders a tab that wasn't compiled in. |

**Most likely cause: (E) — different deployed URL / workspace** the user is recalling, OR a planning artifact / screenshot misremembered as production state. A small secondary contributor is the fact that the `CorePlacements` data structure and a "Core Placements" subsection **do exist** inside the **At a Glance** and **Deep Dive** tabs (they display Sun/Moon/Asc/Mercury/Venus/Mars/Jupiter/Saturn/Chiron/Nodes), which could easily be misremembered as a standalone "Placements tab."

---

## 7. Definitive answer to the success criterion

> **"Why was Placements visible yesterday but missing today?"**

It wasn't visible yesterday on this codebase / this deployed URL. The Placements tab has **never been implemented, committed, built, or deployed** by any artifact reachable from `/app` or from `mirror-lens-fixes-r-1779710763.emergent.host`. The byte-identical MD5 between local `web_dist` and the live bundle, together with zero pickaxe hits in git history, makes "regression" and "revert" both physically impossible explanations. The most defensible reading is that what was seen previously came from a **different Emergent workspace / deployment URL**, a planning mock, or a misidentification of the existing **Core Placements** section inside At a Glance / Deep Dive.

---

## 8. Minimal proposed fix (NOT applied — awaiting approval)

Because the correct framing is *"feature never built"* (this matches the handoff's upcoming P0 task: **"P0: Placements Tab in Astrology Lens (UI currently missing)"**), the minimal fix is **a forward-build, not a revert**:

### Proposed change set (await approval before any code edit)

1. **Create** `/app/frontend/components/astrology/AstrologyPlacementsTab.tsx`
   - Accepts the same props the existing tabs do: `placements: CorePlacements`, `fullChartData: FullChartData | null`, `theme`, `onOpenChat`.
   - Renders a single scrollable list of every planet & angle from `fullChartData.natal.planets` (Sun → Pluto, North/South Node, Chiron) and `fullChartData.natal.angles` (ASC/MC/IC/DC) — each row showing sign, degree, house, retrograde flag, and (optionally) the constellation overlay from `ConstellationOverlayCard`.
   - Reuses helpers already present in `AstrologyDeepDiveTab.tsx` (`generateDeepDiveCards`, `getChartSpine`) — no new backend, no new endpoint, no calculator change.
   - Add a build marker `// MARKER: placements-tab-v1` for future forensic audits.

2. **Edit** `/app/frontend/components/AstrologyLensView.tsx`
   - L43: extend `activeTab` union to include `'placements'`.
   - L23–L28: add `import AstrologyPlacementsTab from './astrology/AstrologyPlacementsTab';`
   - L223–L258 (`renderTabs`): insert a 5th `TouchableOpacity` for "Placements" between "At a Glance" and "Today" (the location follows the user-flow ordering: glance → placements → today → deep dive → timeline).
   - L263–L317 (`renderContent`): add a `placements` branch that renders `<AstrologyPlacementsTab ... />`.

3. **Build & deploy**
   - `cd /app/frontend && yarn build:web` (or whatever the workspace's standard build step is) → emits a new bundle into `frontend/dist` and `backend/web_dist`.
   - Trigger an Emergent publish so the live deployment picks up the new bundle.

### Risk assessment of proposed change

- **Calculators / birth data / HD / astrology generation:** untouched — per your standing constraints.
- **Backend:** no changes.
- **Feature flags:** none flipped (`INTENT_ROUTER_V2_CUTOVER`, `RELATIONSHIP_ORCHESTRATION_PROMPT`, `CROSS_LENS_PROMPT_SURFACE` stay false).
- **Other tabs:** unaffected — the union extension and tab insertion are additive only.
- **Bundle size impact:** ~10–25 KB (one new TSX file consuming already-bundled types and helpers).

**No code changes have been applied. Awaiting your explicit approval before touching any file.**

---

## 9. Reproducibility — exact commands

```bash
# 1. Source-tree presence
find /app/frontend -name "AstrologyPlacementsTab*"      # → empty
grep -rIln "AstrologyPlacementsTab" /app                # → empty

# 2. Git history (pickaxe across all refs + reflog)
git log --all -S "AstrologyPlacementsTab"               # → empty
git log --all -S "placements-tab-v1"                    # → empty
git fsck --no-reflogs --unreachable                     # → no Placements blobs

# 3. Local built bundles
md5sum /app/frontend/dist/_expo/static/js/web/entry-*.js
md5sum /app/backend/web_dist/_expo/static/js/web/entry-*.js
grep -oE '"(At a Glance|Today|Deep Dive|Timeline|Placements)"' \
  /app/backend/web_dist/_expo/static/js/web/entry-*.js | sort -u

# 4. Live deployed bundle
curl -s https://mirror-lens-fixes-r-1779710763.emergent.host/ \
  | grep -oE '/_expo/static/js/web/entry-[a-f0-9]+\.js'
curl -s -o /tmp/d.js -D - \
  https://mirror-lens-fixes-r-1779710763.emergent.host/_expo/static/js/web/entry-a840aeeb2b1699890e640de9e505b634.js
md5sum /tmp/d.js                                        # → a636bd...80b6  (== local)
grep -oc "AstrologyPlacementsTab" /tmp/d.js             # → 0
grep -oc "placements-tab-v1" /tmp/d.js                  # → 0
```

**No DB writes, no code edits, no deploys, no migrations, no flag flips occurred during this audit.**
