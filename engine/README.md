# Mirror Engine

Standalone deterministic calculation service.  Speaks HTTP, returns JSON, no
state.  Lifted out of the monolith so multiple frontend apps (B2C consumer,
B2B forum, internal tools) can share the same compute substrate.

Build marker: `mirror-engine-v1`

## What it does

- True-sidereal & tropical natal astrology (10 planets, all major chart
  points, T2 corroboration bodies — Eros / Psyche / Astraea / Hygiea / Eris
  included via bundled `.se1` files)
- Active transits + transit/object resolver
- Human Design bodygraph (Type / Strategy / Authority / Profile / Definition
  / Centers / Channels / Gates)
- Numerology (Life Path, Expression, Soul Urge, Personality, Lo Shu grid)
- BaZi four-pillars
- Enneagram type resolution from results envelope

## What it does NOT do

- No chat, no LLM
- No MongoDB / DB persistence
- No auth
- No forum / relationship / climate / timeline narrative logic
- No "today" / "deep-dive" / "home" content paths

## Quick start (local)

```bash
docker compose up --build
curl http://localhost:8000/health
# {"status":"ok","version":"mirror-engine-v1"}
```

## Endpoints

| Method | Path | Body |
|---|---|---|
| GET  | `/health` | — |
| POST | `/compute/astrology/natal`     | `birth_datetime_utc`, `lat`, `lon`, optional `house_system` / `node_mode` / `sidereal_settings` |
| POST | `/compute/astrology/transits`  | `birth_datetime_utc`, `lat`, `lon`, optional `target_datetime_utc` |
| POST | `/compute/astrology/objects`   | `birth_datetime_utc`, `lat`, `lon`, `objects: ["Juno","Vertex",...]` |
| POST | `/compute/human-design/bodygraph` | `birth_datetime_utc`, `lat`, `lon` |
| POST | `/compute/numerology/full`     | `birth_date`, optional `full_name` |
| POST | `/compute/bazi/four-pillars`   | `birth_datetime_utc` |
| POST | `/compute/enneagram/resolve`   | `enneagram_type` OR `enneagram_results` |

All endpoints return the exact same payload shapes the original monolith's
calculation functions produced — see the `app/main.py` source for the
straight-through dispatch.
