#!/bin/bash
# =============================================================================
# BUILD SCRIPT - Automated Frontend Build & Copy to Backend
# =============================================================================
# This script:
# 1. Builds the Expo frontend for web
# 2. Copies the dist folder to backend/web_dist
# 3. Ensures the backend serves the latest frontend
#
# Run this before deploying to ensure frontend changes are included.
# =============================================================================

set -e  # Exit on any error

echo "=============================================="
echo "  Mirror Build Script v1.0"
echo "=============================================="

# Navigate to frontend
cd /app/frontend

echo ""
echo "[1/3] Building frontend for web..."
npx expo export --platform web

echo ""
echo "[2/3] Copying dist to backend/web_dist..."
rm -rf /app/backend/web_dist
cp -r /app/frontend/dist /app/backend/web_dist

echo ""
echo "[3/3] Verifying build..."
BUNDLE_HASH=$(ls /app/backend/web_dist/_expo/static/js/web/entry-*.js 2>/dev/null | xargs basename)
echo "Bundle: $BUNDLE_HASH"

echo ""
echo "=============================================="
echo "  Build Complete!"
echo "  Frontend is ready in /app/backend/web_dist"
echo "  You can now deploy."
echo "=============================================="
