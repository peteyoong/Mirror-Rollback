"""
Cross-Lens Atoms Router
=======================
Build marker: cross-lens-atoms-v1

Single endpoint that exposes the multi-lens "atoms" detected for a user.
Live computation (no caching at this layer). All matched atoms require
EVERY signal to be present — partial matches are silently omitted.

Routes:
  GET /api/synthesis/atoms/{user_id}

Response:
  {
    "success":      true,
    "data_mode":    "cross_lens_atoms",
    "build_marker": "cross-lens-atoms-v1",
    "atoms":        [ <atom>, ... ],
    "atom_count":   0
  }
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from services.cross_lens_atoms import BUILD_MARKER, compute_atoms

logger = logging.getLogger(__name__)


def register_cross_lens_atoms_routes(api_router: APIRouter, db) -> None:
    """Attach the /api/synthesis/atoms/{user_id} endpoint."""

    @api_router.get("/synthesis/atoms/{user_id}")
    async def get_cross_lens_atoms(user_id: str) -> JSONResponse:
        # Resolve chart (try string id; ObjectId.is_valid gates secondary lookup)
        chart: Dict[str, Any] | None = await db.charts.find_one({"user_id": user_id})
        if chart is None and ObjectId.is_valid(user_id):
            chart = await db.charts.find_one({"user_id": str(user_id)})
        if chart is None:
            raise HTTPException(status_code=404, detail="chart not found for user")

        atoms = compute_atoms(chart)

        logger.info(
            f"[CrossLensAtoms] user={user_id[:8]}... atoms={len(atoms)} "
            f"ids={[a.get('atom_id') for a in atoms]}"
        )

        return JSONResponse(
            content={
                "success":      True,
                "data_mode":    "cross_lens_atoms",
                "build_marker": BUILD_MARKER,
                "atoms":        atoms,
                "atom_count":   len(atoms),
            },
            headers={"Cache-Control": "no-store, max-age=0"},
        )
