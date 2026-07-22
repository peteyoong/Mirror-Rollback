"""Timing Engine Protocol — Timeline Intelligence V2 · Phase 4
==============================================================
Surface marker: timing-engine-protocol-v1

Abstract plug-in contract for every longitudinal timing engine in Mirror.

Timeline Engine
        ↓
Timing Evidence Layer   ← this file (protocol + evidence dataclass)
        ↓
Narrative Synthesis
        ↓
Timeline Experience

Concrete engines register themselves against this protocol so the
Timeline can compose evidence from an arbitrary number of layers
(annual profection, transits, zodiacal releasing, planetary periods,
Human Design cycles, progressions, life-milestone anchors, recognition
moments…) without any layer knowing about the others.

Contract
--------
Each `TimingEngine` returns one `TimingEvidence` per call.  The evidence
is intentionally "quiet" — a name, a short human-facing meaning line, a
confidence label, the supporting signals it consulted, and an optional
`details` payload that the UI may expand on demand.

Non-negotiables
---------------
• Evidence first.
• Identity first.
• Never claim certainty.
• Never use fatalistic language.
• Observational over predictive.
• Extensible: additional engines must not require changes here.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timezone as _tz
from typing import Any, Dict, List, Literal, Optional

BUILD_MARKER = "timing-engine-protocol-v1"

# ---------------------------------------------------------------------------
# Confidence vocabulary — deliberately small.
#   "high"        — strong deterministic signal + broad literature backing
#   "moderate"    — one canonical technique with meaningful uncertainty
#   "conditional" — signal depends on user-supplied evidence (e.g. life
#                   milestones, recognition moments)
#   "low"         — surface only when explicitly requested
# ---------------------------------------------------------------------------
Confidence = Literal["high", "moderate", "conditional", "low"]


@dataclass
class TimingEvidence:
    """One timing-engine's contribution to the aggregated signals block."""
    engine_id:            str                                       # e.g. "annual_profection"
    name:                 str                                       # human-facing label
    meaning:              str                                       # short observational meaning
    confidence:           Confidence
    supporting_signals:   List[str] = field(default_factory=list)   # what fed the compute
    details:              Dict[str, Any] = field(default_factory=dict)
    engine_marker:        str = ""
    active:               bool = True   # False → engine deliberately silent this cycle

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "engine_id":          self.engine_id,
            "name":               self.name,
            "meaning":            self.meaning,
            "confidence":         self.confidence,
            "supporting_signals": list(self.supporting_signals),
            "details":            dict(self.details),
            "engine_marker":      self.engine_marker,
            "active":             self.active,
        }


class TimingEngine(ABC):
    """Base class for every timing layer plug-in.

    Concrete engines override `compute()`.  `id()` and `default_confidence()`
    are class-level metadata used by the aggregator when the engine emits an
    empty/silent evidence (still needed for the UI legend).
    """

    #: Stable identifier used in the aggregated `timing_signals` dict.
    engine_id: str = "abstract"
    #: Default confidence when the engine has no case-specific override.
    default_confidence: Confidence = "moderate"
    #: Free-form marker for provenance/debugging (bump on breaking change).
    engine_marker: str = "abstract"

    @abstractmethod
    def compute(self,
                 *,
                 natal_chart: Dict[str, Any],
                 birth_datetime_utc: datetime,
                 target_date: Optional[date] = None,
                 extras: Optional[Dict[str, Any]] = None,
                 ) -> TimingEvidence:
        """Return this engine's TimingEvidence for the given moment.

        Implementations must be:
          * deterministic (same inputs → same output),
          * side-effect free (no I/O, no DB, no clock reads),
          * cheap enough to run in a request-response cycle,
          * tolerant of missing optional inputs (return `active=False`
            evidence rather than raising).
        """
        raise NotImplementedError


__all__ = [
    "BUILD_MARKER",
    "Confidence",
    "TimingEvidence",
    "TimingEngine",
]
