#!/bin/bash
# =============================================================================
# prepublish.sh — Run BEFORE clicking "Publish" in the Emergent dashboard
# =============================================================================
# Verifies that /app/backend/web_dist/ contains a bundle at least as fresh
# as the relevant /app/frontend/ sources. If anything has been edited
# since the last `yarn build:deploy`, this script exits non-zero and
# names the stale files so you can rebuild before publishing.
#
# Exit codes:
#   0 — bundle is fresh, safe to Publish
#   1 — stale: a frontend source is newer than the bundle (or no bundle)
#   2 — script error (Python missing, etc.)
#
# Flags forwarded to the Python guard:
#   --json    machine-readable JSON output (for CI)
#   --force   accept stale anyway (escape hatch; logged loudly)
#
# Usage:
#   ./prepublish.sh
#   ./prepublish.sh --json
#   ./prepublish.sh --force          # acknowledged stale-bundle publish
#
# Why this exists
# ---------------
# The Emergent Publish flow containerizes whatever is in
# `/app/backend/web_dist/` AS-IS — it does NOT run `expo export` for you.
# So if you forget to rebuild after a source change, Publish will ship
# the previous bundle and silently regress your live URL. This script
# catches that condition before you hit the button.
# =============================================================================

set -eu

BACKEND_DIR="/app/backend"
GUARD="${BACKEND_DIR}/deployment_guard.py"

if [ ! -f "${GUARD}" ]; then
    echo "[prepublish] FATAL: ${GUARD} not found" >&2
    exit 2
fi

python3 "${GUARD}" prepublish "$@"
RC=$?

if [ ${RC} -ne 0 ]; then
    echo "" >&2
    echo "[prepublish] STALE bundle detected — DO NOT click Publish yet." >&2
    echo "[prepublish] Rebuild with:  cd /app/frontend && yarn build:deploy" >&2
    echo "[prepublish] Then re-run:   /app/prepublish.sh" >&2
fi

exit ${RC}
