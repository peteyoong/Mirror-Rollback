# The Mirror — Product Requirements & Progress

## Product
Self-understanding app ("The Mirror") — Expo (web + native) frontend, FastAPI backend, MongoDB.
Lenses: True Sidereal Astrology, Human Design, Numerology, Enneagram, BaZi.
Two-mode lens architecture: **Reading** (recognition-first) and **Explore** (technical chart data).

## Canonical identity
- Name is strictly **"The Mirror"** (never "Project Mirror") in all UI.

## Design system ("6 Glass / Luxe DARK")
- Blueprint: `/app/design_guidelines.json`; tokens: `/app/frontend/theme/tokens.ts`.
- Dark-first palette: bg `#111111`, surface `#1C1C1C`, text `#F5F5F0`, gold accent `#C6A87C`.
- Typography: serif display headers (Cormorant Garamond/Georgia stack), body sans; **font weights capped at 500 app-wide** (no 600/700/bold).
- Global palettes live in `contexts/ThemeContext.tsx` (Dark/Light) and `constants/colors.ts` — both aligned to tokens (June 2026 retrofit).

## Completed (as of 2026-06 fork)
- Sessions 3c/3d/3e: HD narratives, activation table, topology, product integration, Reading/Explore UX. 110 backend unit tests pass (`pytest /app/backend/tests/`).
- App-wide UI/UX retrofit (this session):
  - Root cause of unclickable Sign in fixed: PWA "Add to Home Screen" banner overlaid the sign-in row; banner now hidden on /welcome, /onboarding, /questionnaire, dark-styled, bottom:78 on tab routes else bottom:0 (`components/AddToHomeScreenBanner.tsx`).
  - Landing `welcome.tsx`: ScrollView (no clipping at 360x700), "I'm new here" / "Sign in" as bordered ghost buttons (44px+ targets); login form scrollable.
  - Global font-weight cap sweep (~150 files) to 500.
  - Serif display headers: Home header + HomeInsightV6Card headline, Lenses, Reflect hero, Forums, mappings headers/headlines/modal, RoleCard (Life), tab-bar native headers.
  - Duplicate native headers hidden on Reflect and Lenses tabs.
  - `forums/mappings.tsx`: friendly error instead of infinite spinner when no forumId param.
  - Verified end-to-end by testing agent (iteration_27, all 11 flows pass at 360x700).

## Key endpoints
- `GET /api/account/login?email=...` — email-only login (no password).
- `GET /api/human-design/mechanics/{user_id}` — canonical HD fetch.
- `GET /api/forums/{forum_id}/mappings` — member mappings ("How they map to me").

## Test account
- pete@pulsifi.me (id 697f0c6abf35c0528ff06954); forums incl. "Yoong family" 69dda348de9cb1c83c0780fa.

## Backlog (priority order)
1. P1 Chart Provenance Hash verification on chart load.
2. P1 Session 4 — Gene Keys standalone lens (do not duplicate calc engines).
3. P1 Sessions 5–8 — Astrology / Numerology / Enneagram / BaZi narrative rebuilds.
4. P1 Session 9 — Cross-Lens Coherence.
5. P2 `gm_compat_sign` additive field (blocked on user GM screenshots).
6. P2 Stale `chart.migration_info` cleanup; malformed chart row `chart_id=6a2a9113d0b74d4608c6b3bf`.
7. P2 Relationship Memory; Variant A migration; test account rationalization.
8. Minor: onboarding emits two "text node cannot be a child of <View>" web warnings (cosmetic); RN-web shadow*/pointerEvents deprecation warnings.
