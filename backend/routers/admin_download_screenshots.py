"""admin_download_screenshots.py — temporary download endpoint
============================================================

Exposes `/api/admin/download_screenshots.zip` so the user can
download the screenshot package from any browser using just the
confirm token.  READ-ONLY; serves a static file from /app/memory.

Build marker:    download-screenshots-v1
Confirm token:   SCREENSHOTS_DOWNLOAD_V1
Method:          GET
"""
from __future__ import annotations

import os
import logging

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse

logger = logging.getLogger("admin_download_screenshots")

ROUTE_BUILD_MARKER = "download-screenshots-v1"
CONFIRM_TOKEN      = "SCREENSHOTS_DOWNLOAD_V1"
ZIP_PATH           = "/app/memory/screenshots.zip"
INDEX_PATH         = "/app/memory/screenshots/INDEX.md"

router = APIRouter(prefix="/api/admin", tags=["admin-download"])


@router.get("/download_screenshots.zip")
async def download_screenshots_zip(
    request: Request,
    confirm: str = Query(..., description=f"Must equal {CONFIRM_TOKEN}"),
):
    """Return the zipped screenshot package as a file download."""
    if confirm != CONFIRM_TOKEN:
        raise HTTPException(status_code=403, detail={
            "code":    "INVALID_CONFIRM_TOKEN",
            "message": f"Append ?confirm={CONFIRM_TOKEN} to download.",
        })
    if not os.path.exists(ZIP_PATH):
        raise HTTPException(status_code=404, detail={
            "code":    "ZIP_NOT_FOUND",
            "message": "No screenshot package built on this pod yet.",
        })
    return FileResponse(
        ZIP_PATH,
        media_type="application/zip",
        filename="mirror_screenshots.zip",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/screenshots_index")
async def screenshots_index(
    confirm: str = Query(..., description=f"Must equal {CONFIRM_TOKEN}"),
):
    """Return the Markdown index as JSON-wrapped text."""
    if confirm != CONFIRM_TOKEN:
        raise HTTPException(status_code=403, detail={
            "code":    "INVALID_CONFIRM_TOKEN",
            "message": f"Append ?confirm={CONFIRM_TOKEN} to read.",
        })
    if not os.path.exists(INDEX_PATH):
        raise HTTPException(status_code=404, detail={
            "code":    "INDEX_NOT_FOUND",
        })
    with open(INDEX_PATH, "r") as f:
        return JSONResponse(content={
            "build_marker": ROUTE_BUILD_MARKER,
            "index_md":     f.read(),
        })
