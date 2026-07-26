"""hd_definition_topology.py — Formal Human Design Definition topology
========================================================================

Session-3c Decision 4: independently derive the Definition topology
type (Single / Split / Triple Split / Quadruple Split) from the
defined-centre / defined-channel graph, so we never have to trust the
upstream engine's `definition` label blind.

Definition rule (canonical HD topology — verifiable):
------------------------------------------------------
Build an undirected graph:
    nodes  = the 9 canonical HD centres that are DEFINED for this chart
    edges  = every DEFINED channel whose two endpoints are both defined
             centres

Count the connected components on that subgraph. The count maps
one-to-one onto the definition type:

    1 component  → Single Definition
    2 components → Split Definition
    3 components → Triple Split Definition
    4 components → Quadruple Split Definition

Any other count (0, 5+) is unreachable in a well-formed BodyGraph and
is returned as `Unknown` with `unverified=True` — never silently coerced.

Subtype policy (Session-3c decision-4, safety-first):
------------------------------------------------------
"Small Split" vs "Wide Split" is defined in HD literature by the
minimum-bridging-gate count between the two split components, but the
published algorithms across HD sources disagree on whether the count is
measured in gates, channels, or centres, and whether "activated one
side" gates change the count. Because we cannot pick a single
documented, deterministic and universally-accepted rule without
inventing our own heuristic, this module DOES NOT emit a subtype. It
returns:

    split_subtype: None
    split_subtype_unverified: True     # only when definition_type is Split
    split_subtype_reason: 'no_formal_algorithm_verified'

The frontend must therefore render "Split Definition" (never
"Small Split" / "Wide Split") until a formally verified algorithm is
added AND tests are shipped for it.

build_marker: the-mirror-hd-definition-topology-v1
"""
from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple, Any

# ---------------------------------------------------------------------------
# Canonical HD centres (must match hd_center_canonical.CANONICAL_CENTERS)
# ---------------------------------------------------------------------------
CANONICAL_CENTERS: Tuple[str, ...] = (
    "Head",
    "Ajna",
    "Throat",
    "G/Identity",
    "Heart/Ego",
    "Solar Plexus",
    "Sacral",
    "Spleen",
    "Root",
)

# ---------------------------------------------------------------------------
# Definition-type map by connected-component count
# ---------------------------------------------------------------------------
_COMPONENTS_TO_TYPE: Dict[int, str] = {
    1: "Single Definition",
    2: "Split Definition",
    3: "Triple Split Definition",
    4: "Quadruple Split Definition",
}

DERIVATION_RULE_ID = "hd_definition_topology_component_count_v1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _canon(name: Any) -> Optional[str]:
    """Normalise a centre name into the canonical form or return None."""
    if not isinstance(name, str):
        return None
    n = name.strip()
    if not n:
        return None
    aliases = {
        "Ego": "Heart/Ego",
        "Heart": "Heart/Ego",
        "Will": "Heart/Ego",
        "G": "G/Identity",
        "Identity": "G/Identity",
        "Emotional": "Solar Plexus",
        "Solar-Plexus": "Solar Plexus",
        "SolarPlexus": "Solar Plexus",
    }
    n = aliases.get(n, n)
    if n in CANONICAL_CENTERS:
        return n
    # Strip parenthetical e.g. "Ajna (Mind)"
    if "(" in n:
        stripped = n.split("(", 1)[0].strip()
        if stripped in CANONICAL_CENTERS:
            return stripped
    return None


def _extract_channel_edge(channel: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    """Extract a canonical centre-centre edge from a channel dict."""
    if not isinstance(channel, dict):
        return None
    centres = channel.get("centers") or channel.get("centres") or []
    if not isinstance(centres, list) or len(centres) < 2:
        return None
    a = _canon(centres[0])
    b = _canon(centres[1])
    if not a or not b or a == b:
        return None
    return (a, b)


def _connected_components(
    nodes: Set[str], edges: List[Tuple[str, str]]
) -> List[Set[str]]:
    """Return the list of connected components (each a set of node names)."""
    # Union-find
    parent: Dict[str, str] = {n: n for n in nodes}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: str, y: str) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    for a, b in edges:
        if a in parent and b in parent:
            union(a, b)

    buckets: Dict[str, Set[str]] = {}
    for n in nodes:
        r = find(n)
        buckets.setdefault(r, set()).add(n)
    # Deterministic ordering: sort by size desc, then by min-name asc
    return sorted(
        buckets.values(),
        key=lambda s: (-len(s), sorted(s)[0] if s else ""),
    )


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------
def analyse_definition_topology(
    defined_centers: Optional[List[str]],
    defined_channels: Optional[List[Dict[str, Any]]],
    upstream_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Independently derive the Definition topology from the graph.

    Parameters
    ----------
    defined_centers   : canonical-or-alias list of defined centre names
    defined_channels  : list of channel dicts with a `centers` list of
                        length 2 (endpoints).  Channels touching an
                        undefined centre are ignored (they cannot glue
                        components on the defined-centre subgraph).
    upstream_label    : the definition label already reported by the
                        chart engine, purely for reconciliation.

    Returns
    -------
    dict with fields:
        derived_type             : one of "Single Definition",
                                    "Split Definition",
                                    "Triple Split Definition",
                                    "Quadruple Split Definition",
                                    "No Definition", "Unknown"
        components_count         : int (0..N)
        components               : list[list[str]]  (sorted deterministic)
        edges_used               : list[[a,b]]
        upstream_label           : the reported label (for reconciliation)
        matches_upstream         : bool (True/False/None)
        split_subtype            : always None in this version
        split_subtype_unverified : True iff derived_type == Split Definition
                                    else False
        split_subtype_reason     : 'no_formal_algorithm_verified' when
                                    unverified else None
        derivation_rule          : DERIVATION_RULE_ID
        confidence               : 'high' | 'partial' | 'unknown'
        provenance               : {source, algorithm}
    """
    # -- Canonicalise nodes ------------------------------------------------
    raw_centres = defined_centers or []
    nodes: Set[str] = set()
    for c in raw_centres:
        can = _canon(c)
        if can:
            nodes.add(can)

    # -- Build edges (only when BOTH endpoints are defined) ---------------
    edges: List[Tuple[str, str]] = []
    for ch in defined_channels or []:
        edge = _extract_channel_edge(ch)
        if edge is None:
            continue
        a, b = edge
        if a in nodes and b in nodes:
            edges.append((a, b))

    # -- No defined centres → No Definition -------------------------------
    if not nodes:
        return {
            "derived_type": "No Definition",
            "components_count": 0,
            "components": [],
            "edges_used": [],
            "upstream_label": upstream_label,
            "matches_upstream": (upstream_label or "").strip().lower()
            in {"none", "no definition", "no-definition"}
            if upstream_label
            else None,
            "split_subtype": None,
            "split_subtype_unverified": False,
            "split_subtype_reason": None,
            "derivation_rule": DERIVATION_RULE_ID,
            "confidence": "high",
            "provenance": {
                "source": "hd_definition_topology",
                "algorithm": "connected_components_on_defined_center_graph",
            },
        }

    # -- Connected components ---------------------------------------------
    comps = _connected_components(nodes, edges)
    n_comp = len(comps)
    derived = _COMPONENTS_TO_TYPE.get(n_comp, "Unknown")

    # -- Reconcile with upstream label ------------------------------------
    matches = None
    if upstream_label:
        u = upstream_label.strip().lower()
        d = derived.strip().lower()
        # Accept short-forms like "Split", "Single", etc.
        aliases_match = {
            "single": "single definition",
            "split": "split definition",
            "triple": "triple split definition",
            "triple split": "triple split definition",
            "quadruple": "quadruple split definition",
            "quadruple split": "quadruple split definition",
            "no": "no definition",
        }
        u_norm = aliases_match.get(u, u)
        matches = u_norm == d

    # -- Subtype policy (safety-first) ------------------------------------
    is_split = derived == "Split Definition"
    return {
        "derived_type": derived,
        "components_count": n_comp,
        "components": [sorted(c) for c in comps],
        "edges_used": [list(e) for e in edges],
        "upstream_label": upstream_label,
        "matches_upstream": matches,
        "split_subtype": None,
        "split_subtype_unverified": is_split,
        "split_subtype_reason": "no_formal_algorithm_verified" if is_split else None,
        "derivation_rule": DERIVATION_RULE_ID,
        "confidence": "high" if derived != "Unknown" else "unknown",
        "provenance": {
            "source": "hd_definition_topology",
            "algorithm": "connected_components_on_defined_center_graph",
        },
    }


__all__ = [
    "analyse_definition_topology",
    "CANONICAL_CENTERS",
    "DERIVATION_RULE_ID",
]
