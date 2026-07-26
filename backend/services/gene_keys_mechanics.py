"""Gene Keys Canonical Mechanics — Session 4A

Single canonical read model that consumes the existing verified activation
engine (`calculations/human_design.get_human_design_chart`) and produces the
Gene Keys mechanics envelope used by the standalone lens.

We deliberately *do not* recompute astronomy or gate placement here.  This
module reads from the HD chart's `personality`/`design` planet tables and
labels each sphere per `services/gene_keys_sphere_map.CANONICAL_SPHERE_MAP`.

Session-4A guardrails:
- Star Pearl is deferred (see STAR_PEARL_AVAILABILITY in sphere_map).
- No Human Design vocabulary (Type / Strategy / Authority / Centres /
  Channels / Definition / Signature / Not-Self) leaks into the output.
- Every content-bearing field carries `content_provenance`.
- Verification status is emitted per-sphere.
- Line is present only when the underlying HD engine returned it.
- Pete regression discrepancy (Session 4A) is surfaced honestly via
  `verification_status="discrepancy_held"` with an evidence pointer.

Version: gene_keys_mechanics_v1
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional, TypedDict

from services.gene_keys_sphere_map import (
    CANONICAL_SPHERE_MAP,
    GENE_KEYS_SPHERE_MAP_VERSION,
    METHODOLOGY_PROVENANCE,
    SEQUENCES,
    SHARED_ACTIVATION_ROLES,
    STAR_PEARL_AVAILABILITY,
    STAR_PEARL_REASON,
    get_unique_activation_points,
    get_sphere_role_map,
)


GENE_KEYS_MECHANICS_VERSION = "gene_keys_mechanics_v1"


# -------------------------------------------------------------------------
# Pete regression fixture (used ONLY to stamp verification status per sphere).
# NOT consumed as a lookup for values — actual gate/line always derives from
# the HD engine.  If Pete's derived gates differ from these expected values
# under the canonical mapping, the affected spheres are marked
# `verification_status="discrepancy_held"` per user rule.
# -------------------------------------------------------------------------

PETE_USER_ID = "697f0c6abf35c0528ff06954"
PETE_EXPECTED_GATES: Dict[str, int] = {
    "Life's Work": 37,
    "Evolution":   40,
    "Radiance":    5,
    "Purpose":     35,
    "Attraction":  41,
    "IQ":          13,
    "EQ":          5,
    "SQ":          28,
    "Core":        25,
    "Vocation":    61,
    "Culture":     62,
    "Brand":       37,
    "Pearl":       31,
}


class SphereMechanics(TypedDict, total=False):
    sphere_name: str
    sequences: List[str]                # sphere may appear in more than one
    gene_key: Optional[int]
    line: Optional[int]                 # only when engine returned one
    activation: Dict[str, str]          # {planet, chart_side}
    source_longitude: Optional[float]
    evidence_ref: Dict[str, Any]        # HD activation lineage
    content_provenance: str             # "mirror_original" | "structural_label"
    structural_labels: Dict[str, str]   # shadow/gift/siddhi structural label refs
    verification_status: str
    verification_note: Optional[str]


def _safe_extract_gate_line(planet_data: Dict[str, Any]) -> Dict[str, Any]:
    """Return {gate, line, longitude} from an HD planet entry (or Nones)."""
    if not isinstance(planet_data, dict):
        return {"gate": None, "line": None, "longitude": None}
    gate_info = planet_data.get("gate") or {}
    if not isinstance(gate_info, dict):
        return {"gate": None, "line": None, "longitude": planet_data.get("longitude")}
    gate = gate_info.get("gate")
    line = gate_info.get("line")
    longitude = planet_data.get("longitude")
    return {"gate": gate, "line": line, "longitude": longitude}


def _pick_planet(personality: Dict[str, Any], design: Dict[str, Any], planet: str, side: str) -> Dict[str, Any]:
    table = personality if side == "personality" else design
    return table.get(planet, {}) if isinstance(table, dict) else {}


def build_gene_keys_mechanics(
    hd_chart: Dict[str, Any],
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the canonical mechanics envelope for one user.

    Args:
        hd_chart:  Output of `get_human_design_chart(...)` or the cached
                   equivalent (must contain 'personality' and 'design').
        user_id:   Optional — used to attach Pete regression status.

    Returns:
        Canonical mechanics envelope (Session 4A schema).
    """
    if not isinstance(hd_chart, dict):
        return _empty_envelope(reason="hd_chart_missing", user_id=user_id)

    personality = hd_chart.get("personality") or {}
    design = hd_chart.get("design") or {}
    if not personality or not design:
        return _empty_envelope(reason="hd_activations_missing", user_id=user_id)

    role_map = get_sphere_role_map()
    sphere_records: List[SphereMechanics] = []
    missing_fields: List[str] = []
    discrepancies: List[Dict[str, Any]] = []

    for sphere_name, activation in CANONICAL_SPHERE_MAP.items():
        planet_data = _pick_planet(personality, design, activation["planet"], activation["chart_side"])
        extracted = _safe_extract_gate_line(planet_data)

        gate = extracted["gate"]
        line = extracted["line"]

        # Structural-label references only — no copyrighted prose is embedded.
        structural_labels = {
            "shadow_label_ref": f"Shadow of Gene Key {gate}" if gate else None,
            "gift_label_ref":   f"Gift of Gene Key {gate}"    if gate else None,
            "siddhi_label_ref": f"Siddhi of Gene Key {gate}"  if gate else None,
        }

        # Verification status
        expected = PETE_EXPECTED_GATES.get(sphere_name)
        verification_status = "verified" if gate is not None else "engine_missing"
        verification_note = None
        if user_id == PETE_USER_ID and expected is not None and gate is not None and gate != expected:
            verification_status = "discrepancy_held"
            verification_note = (
                f"Pete regression: expected Gene Key {expected} for sphere '{sphere_name}' "
                f"under a pre-canonical mapping; canonical first-party mapping derives "
                f"Gene Key {gate}.  Mechanics and UI for this sphere are HELD pending "
                f"a user decision (Session 4A rule)."
            )
            discrepancies.append({
                "sphere": sphere_name,
                "expected_gene_key": expected,
                "derived_gene_key": gate,
                "canonical_activation": dict(activation),
                "source_longitude": extracted["longitude"],
                "likely_source": "pete_fixture_used_pre_canonical_mapping",
            })

        if gate is None:
            missing_fields.append(sphere_name)

        record: SphereMechanics = {
            "sphere_name": sphere_name,
            "sequences": role_map[sphere_name]["sequences"],  # list[str]
            "gene_key": gate,
            "line": line if isinstance(line, int) else None,
            "activation": dict(activation),
            "source_longitude": extracted["longitude"],
            "evidence_ref": {
                "origin": "calculated",
                "engine": "the_mirror.hd_sidereal_v1",
                "planet": activation["planet"],
                "chart_side": activation["chart_side"],
                "longitude_key": f"{activation['chart_side']}.{activation['planet']}.longitude",
                "gate_mandala": "human_design_64_gate_i_ching_wheel",
            },
            "content_provenance": "structural_label",  # this record ships labels only
            "structural_labels": structural_labels,
            "verification_status": verification_status,
            "verification_note": verification_note,
        }
        sphere_records.append(record)

    # Deduplicate shared activations for the unique-spheres block.
    seen_activation_keys: set = set()
    unique_spheres: List[SphereMechanics] = []
    for r in sphere_records:
        key = (r["activation"]["planet"], r["activation"]["chart_side"])
        if key in seen_activation_keys:
            continue
        seen_activation_keys.add(key)
        unique_spheres.append(r)

    # Profile availability
    profile_available = len(missing_fields) == 0
    all_verified = all(r["verification_status"] == "verified" for r in sphere_records)

    envelope = {
        "mechanics_version": GENE_KEYS_MECHANICS_VERSION,
        "sphere_map_version": GENE_KEYS_SPHERE_MAP_VERSION,
        "methodology": METHODOLOGY_PROVENANCE,
        "profile_availability": "present" if profile_available else "partial",
        "sequences": {
            seq_name: [_sphere_public(r) for r in sphere_records if seq_name in r["sequences"]]
            for seq_name in SEQUENCES.keys()
        },
        "unique_spheres": [_sphere_public(r) for r in unique_spheres],
        "shared_activation_roles": SHARED_ACTIVATION_ROLES,
        "all_spheres": [_sphere_public(r) for r in sphere_records],
        "missing_fields": missing_fields,
        "verification_status": "verified" if all_verified else "partial",
        "verification_discrepancies": discrepancies,
        "methodology_disclosure": METHODOLOGY_PROVENANCE["disclosure"],
        "star_pearl_availability": STAR_PEARL_AVAILABILITY,
        "star_pearl_reason": STAR_PEARL_REASON,
        "reading_availability": {
            "state": "pending_session_4b",
            "reason": (
                "Standalone Reading mode ships in Session 4B once IP-safe, "
                "Mirror-authored narrative content for the profile has been "
                "reviewed.  No temporary generic reading is fabricated here."
            ),
        },
        "user_id": user_id,
    }
    return envelope


def _sphere_public(record: SphereMechanics) -> Dict[str, Any]:
    """Public projection of SphereMechanics — no internal-only fields."""
    return {
        "sphere_name": record["sphere_name"],
        "sequences": record["sequences"],
        "gene_key": record["gene_key"],
        "line": record["line"],
        "activation": record["activation"],
        "source_longitude": record["source_longitude"],
        "evidence_ref": record["evidence_ref"],
        "content_provenance": record["content_provenance"],
        "structural_labels": record["structural_labels"],
        "verification_status": record["verification_status"],
        "verification_note": record["verification_note"],
    }


def _empty_envelope(reason: str, user_id: Optional[str]) -> Dict[str, Any]:
    return {
        "mechanics_version": GENE_KEYS_MECHANICS_VERSION,
        "sphere_map_version": GENE_KEYS_SPHERE_MAP_VERSION,
        "methodology": METHODOLOGY_PROVENANCE,
        "profile_availability": "unavailable",
        "sequences": {name: [] for name in SEQUENCES.keys()},
        "unique_spheres": [],
        "shared_activation_roles": SHARED_ACTIVATION_ROLES,
        "all_spheres": [],
        "missing_fields": list(CANONICAL_SPHERE_MAP.keys()),
        "verification_status": "unavailable",
        "verification_discrepancies": [],
        "methodology_disclosure": METHODOLOGY_PROVENANCE["disclosure"],
        "star_pearl_availability": STAR_PEARL_AVAILABILITY,
        "star_pearl_reason": STAR_PEARL_REASON,
        "reading_availability": {"state": "pending_session_4b", "reason": reason},
        "user_id": user_id,
        "unavailable_reason": reason,
    }
