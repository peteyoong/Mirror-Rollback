"""Timing Evidence Layer — Timeline Intelligence V2 · Phase 4
=============================================================
Surface marker: timing-evidence-layer-v1

Aggregator that fans out to every registered TimingEngine and composes
their evidence into a single `timing_signals` dict for the Timeline.

Concrete engines that ship today:
    • annual_profection  — Timeline V2 Phase 1+2 (canonical)

Future engines slot in by adding another `.register(instance)` call.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from services.timing_engine_protocol import (
    BUILD_MARKER as PROTOCOL_MARKER,
    TimingEngine,
    TimingEvidence,
)
from services.annual_profection_engine   import (
    BUILD_MARKER as PROFECTION_ENGINE_MARKER,
    compute_profection,
)
from services.annual_profection_narrative import build_narrative

LAYER_BUILD_MARKER = "timing-evidence-layer-v1"


# ---------------------------------------------------------------------------
# First-class engine: Annual Profection plug-in
# ---------------------------------------------------------------------------
class AnnualProfectionTimingEngine(TimingEngine):
    """Wraps the deterministic profection engine as a plug-in."""

    engine_id          = "annual_profection"
    default_confidence = "moderate"
    engine_marker      = PROFECTION_ENGINE_MARKER

    def compute(self, *,
                 natal_chart: Dict[str, Any],
                 birth_datetime_utc: datetime,
                 target_date: Optional[date] = None,
                 extras: Optional[Dict[str, Any]] = None,
                 ) -> TimingEvidence:
        target_date = target_date or datetime.utcnow().date()
        try:
            prof = compute_profection(
                natal_chart        = natal_chart,
                birth_datetime_utc = birth_datetime_utc,
                target_date        = target_date,
            )
        except Exception as exc:                                    # noqa: BLE001
            return TimingEvidence(
                engine_id     = self.engine_id,
                name          = "Annual Profection (unavailable)",
                meaning       = f"could not compute: {exc}",
                confidence    = "low",
                active        = False,
                engine_marker = self.engine_marker,
            )

        narrative = build_narrative(prof)

        return TimingEvidence(
            engine_id  = self.engine_id,
            name       = f"{_ordinal(prof.activated_house)} House Year",
            meaning    = narrative["what_area_is_asking_attention"],
            confidence = self.default_confidence,
            supporting_signals = [
                "natal chart (Variant-A / Equal houses)",
                "traditional rulership table",
                "birth-anchored 12-year cycle",
            ],
            details = {
                "age":                   prof.age,
                "activated_house":       prof.activated_house,
                "profected_sign":        prof.profected_sign,
                "lord_of_the_year":      prof.lord_of_the_year,
                "modern_ruler":          prof.modern_ruler,
                "birthday_range":        prof.birthday_range,
                "element":               prof.element,
                "modality":              prof.modality,
                "is_current":            prof.is_current,
                "ruler_natal_condition": prof.ruler_natal_condition,
                "interpretation":        narrative,
            },
            engine_marker = self.engine_marker,
            active        = True,
        )


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------
class TimingEvidenceLayer:
    """Registry + fan-out for every TimingEngine plug-in.

    Usage:
        layer = TimingEvidenceLayer()
        layer.register(AnnualProfectionTimingEngine())
        layer.register(TransitsTimingEngine())          # future
        layer.register(ZodiacalReleasingTimingEngine()) # future

        signals = layer.aggregate(
            natal_chart        = chart,
            birth_datetime_utc = birth_utc,
            target_date        = today,
        )
    """
    def __init__(self) -> None:
        self._engines: List[TimingEngine] = []

    # ── registry ──────────────────────────────────────────────────────────
    def register(self, engine: TimingEngine) -> "TimingEvidenceLayer":
        if not isinstance(engine, TimingEngine):
            raise TypeError(f"{engine!r} is not a TimingEngine")
        # Replace any existing plug-in with the same id (idempotent register).
        self._engines = [e for e in self._engines if e.engine_id != engine.engine_id]
        self._engines.append(engine)
        return self

    def unregister(self, engine_id: str) -> None:
        self._engines = [e for e in self._engines if e.engine_id != engine_id]

    @property
    def engine_ids(self) -> List[str]:
        return [e.engine_id for e in self._engines]

    # ── fan-out ───────────────────────────────────────────────────────────
    def aggregate(self, *,
                   natal_chart: Dict[str, Any],
                   birth_datetime_utc: datetime,
                   target_date: Optional[date] = None,
                   extras: Optional[Dict[str, Any]] = None,
                   include_inactive: bool = False,
                   ) -> Dict[str, Any]:
        """Run every registered engine and return the composed timing_signals
        block. Engine ordering is preserved.

        `include_inactive=True` surfaces engines that returned `active=False`
        (useful for diagnostic views); default is False.
        """
        signals: Dict[str, Any] = {}
        for engine in self._engines:
            try:
                ev = engine.compute(
                    natal_chart        = natal_chart,
                    birth_datetime_utc = birth_datetime_utc,
                    target_date        = target_date,
                    extras             = extras,
                )
            except Exception as exc:                                # noqa: BLE001
                ev = TimingEvidence(
                    engine_id     = engine.engine_id,
                    name          = f"{engine.engine_id} (error)",
                    meaning       = str(exc),
                    confidence    = "low",
                    active        = False,
                    engine_marker = engine.engine_marker,
                )
            if not ev.active and not include_inactive:
                continue
            signals[engine.engine_id] = ev.to_public_dict()

        return {
            "protocol_marker": PROTOCOL_MARKER,
            "layer_marker":    LAYER_BUILD_MARKER,
            "engines_run":     self.engine_ids,
            "signals":         signals,
        }


# ---------------------------------------------------------------------------
# Default layer — pre-registered with Mirror's canonical engines.
# ---------------------------------------------------------------------------
def build_default_layer() -> TimingEvidenceLayer:
    layer = TimingEvidenceLayer()
    layer.register(AnnualProfectionTimingEngine())
    # Future engines register themselves here:
    #   layer.register(TransitsTimingEngine())
    #   layer.register(ZodiacalReleasingTimingEngine())
    #   layer.register(HumanDesignCycleTimingEngine())
    #   layer.register(LifeMilestoneTimingEngine())
    return layer


def _ordinal(n: int) -> str:
    if 10 <= (n % 100) < 20: suf = "th"
    else: suf = {1:"st", 2:"nd", 3:"rd"}.get(n % 10, "th")
    return f"{n}{suf}"


__all__ = [
    "LAYER_BUILD_MARKER",
    "AnnualProfectionTimingEngine",
    "TimingEvidenceLayer",
    "build_default_layer",
]
