# Project Mirror - Backend Documentation Index

## Architecture Documents

| Document | Status | Description |
|----------|--------|-------------|
| [INTERPRETATION_LAYER_v1.md](./INTERPRETATION_LAYER_v1.md) | ✅ APPROVED | Contract for interpretation layer (not yet implemented) |

## Module Documentation

| Module | README | Status |
|--------|--------|--------|
| `/calculations/` | [README.md](../calculations/README.md) | FROZEN (deterministic core) |

## Key Concepts

### Deterministic vs Interpretation Layer

```
DETERMINISTIC CORE (frozen, tested)
├── astrology.py
├── human_design.py  
└── timezone_utils.py
         │
         │ Facts only, no meanings
         ▼
INTERPRETATION LAYER (approved design, not implemented)
└── docs/INTERPRETATION_LAYER_v1.md
         │
         │ Narratives, tone, sovereignty
         ▼
USER-FACING OUTPUT
```

### Computation Version

Current: `mirror-deterministic-v1`

All chart API responses include this version string.
Bump version when modifying frozen files.

---

## Regression Tests

```bash
# Run all tests
cd /app/backend && python tests/test_mel_regression.py

# Expected output: ALL TESTS PASSED
```

---

*Last updated: 2025-06*
