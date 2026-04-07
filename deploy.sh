#!/bin/bash
#
# deploy.sh - Frontend Web Build and Deploy Script
# ================================================
# This script exports the Expo web build and deploys it to the backend web_dist folder.
# It includes validation to prevent stale deployments.
#
# Usage:
#   ./deploy.sh [--force]
#
# Flags:
#   --force  Skip staleness validation and deploy anyway
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Paths
FRONTEND_DIR="/app/frontend"
BACKEND_DIR="/app/backend"
WEB_DIST_DIR="${BACKEND_DIR}/web_dist"
FRONTEND_DIST_DIR="${FRONTEND_DIR}/dist"

# Parse arguments
FORCE=false
if [ "$1" == "--force" ]; then
    FORCE=true
fi

echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}[Deploy] Starting Frontend Web Build${NC}"
echo -e "${BLUE}=============================================${NC}"

# Get git info
GIT_REV=$(git -C /app rev-parse --short HEAD 2>/dev/null || echo "unknown")
GIT_DIRTY=$(git -C /app status --porcelain 2>/dev/null | wc -l)
if [ "$GIT_DIRTY" -gt 0 ]; then
    GIT_REV="${GIT_REV}*"
fi

echo -e "${BLUE}[Deploy] Git Revision: ${GIT_REV}${NC}"

# Check current deployed bundle
if [ -f "${WEB_DIST_DIR}/index.html" ]; then
    OLD_BUNDLE_TIME=$(stat -c %Y "${WEB_DIST_DIR}/index.html" 2>/dev/null || echo "0")
    OLD_BUNDLE_DATE=$(date -d @${OLD_BUNDLE_TIME} "+%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "unknown")
    echo -e "${YELLOW}[Deploy] Current deployed bundle: ${OLD_BUNDLE_DATE}${NC}"
else
    echo -e "${YELLOW}[Deploy] No existing deployed bundle found${NC}"
fi

# Build the frontend
echo -e "${BLUE}[Deploy] Building Expo web export...${NC}"
cd "${FRONTEND_DIR}"

# Export to web
npx expo export --platform web

if [ ! -f "${FRONTEND_DIST_DIR}/index.html" ]; then
    echo -e "${RED}[Deploy] ERROR: Build failed - no index.html found${NC}"
    exit 1
fi

# Get new build info
NEW_BUNDLE_TIME=$(stat -c %Y "${FRONTEND_DIST_DIR}/index.html" 2>/dev/null || echo "0")
NEW_BUNDLE_DATE=$(date -d @${NEW_BUNDLE_TIME} "+%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "unknown")
NEW_BUNDLE_NAME=$(ls ${FRONTEND_DIST_DIR}/_expo/static/js/web/entry-*.js 2>/dev/null | xargs basename 2>/dev/null || echo "unknown")
NEW_BUNDLE_HASH=$(sha256sum ${FRONTEND_DIST_DIR}/_expo/static/js/web/entry-*.js 2>/dev/null | cut -c1-12 || echo "unknown")

echo -e "${GREEN}[Deploy] Build successful!${NC}"
echo -e "${BLUE}[Deploy] New bundle: ${NEW_BUNDLE_NAME}${NC}"
echo -e "${BLUE}[Deploy] New bundle hash: ${NEW_BUNDLE_HASH}${NC}"
echo -e "${BLUE}[Deploy] Build timestamp: ${NEW_BUNDLE_DATE}${NC}"

# Validate: Check if newest source is older than build
NEWEST_SOURCE=""
NEWEST_SOURCE_TIME=0

for f in components/NumerologySummaryV2.tsx components/NumerologyDeepDiveV2.tsx components/NumerologyLensView.tsx components/InsightCardFooter.tsx; do
    if [ -f "${FRONTEND_DIR}/${f}" ]; then
        FILE_TIME=$(stat -c %Y "${FRONTEND_DIR}/${f}" 2>/dev/null || echo "0")
        if [ "$FILE_TIME" -gt "$NEWEST_SOURCE_TIME" ]; then
            NEWEST_SOURCE_TIME=$FILE_TIME
            NEWEST_SOURCE=$f
        fi
    fi
done

if [ "$NEWEST_SOURCE_TIME" -gt "$NEW_BUNDLE_TIME" ]; then
    NEWEST_SOURCE_DATE=$(date -d @${NEWEST_SOURCE_TIME} "+%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "unknown")
    echo -e "${RED}=============================================${NC}"
    echo -e "${RED}[Deploy] WARNING: STALE BUILD DETECTED!${NC}"
    echo -e "${RED}[Deploy] Source file '${NEWEST_SOURCE}' (${NEWEST_SOURCE_DATE})${NC}"
    echo -e "${RED}[Deploy] is NEWER than the build (${NEW_BUNDLE_DATE})${NC}"
    echo -e "${RED}=============================================${NC}"
    
    if [ "$FORCE" != true ]; then
        echo -e "${RED}[Deploy] Aborting deployment. Use --force to override.${NC}"
        exit 1
    else
        echo -e "${YELLOW}[Deploy] --force flag used, continuing anyway...${NC}"
    fi
fi

# Copy to web_dist
echo -e "${BLUE}[Deploy] Copying build to ${WEB_DIST_DIR}...${NC}"
rm -rf "${WEB_DIST_DIR}/"*
cp -r "${FRONTEND_DIST_DIR}/"* "${WEB_DIST_DIR}/"

# Verify copy
if [ ! -f "${WEB_DIST_DIR}/index.html" ]; then
    echo -e "${RED}[Deploy] ERROR: Copy failed - no index.html in web_dist${NC}"
    exit 1
fi

# Restart backend
echo -e "${BLUE}[Deploy] Restarting backend...${NC}"
sudo supervisorctl restart backend

# Wait for backend to start
sleep 3

# Log summary
echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}[Deploy] DEPLOYMENT COMPLETE${NC}"
echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}  Git Revision:    ${GIT_REV}${NC}"
echo -e "${GREEN}  Bundle:          ${NEW_BUNDLE_NAME}${NC}"
echo -e "${GREEN}  Bundle Hash:     ${NEW_BUNDLE_HASH}${NC}"
echo -e "${GREEN}  Build Timestamp: ${NEW_BUNDLE_DATE}${NC}"
echo -e "${GREEN}=============================================${NC}"

# Verify deployment via health endpoint
echo -e "${BLUE}[Deploy] Verifying deployment via /api/health...${NC}"
sleep 2
curl -s http://localhost:8001/api/health | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    build = data.get('build', {})
    print(f\"  Stamp: {build.get('stamp', 'N/A')}\")
    print(f\"  Valid: {build.get('validation', {}).get('is_current', 'N/A')}\")
except Exception as e:
    print(f'  Error reading health: {e}')
"

echo -e "${GREEN}[Deploy] Done!${NC}"
