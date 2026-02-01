# Calculations Module - Deterministic Computation Core

**Version:** mirror-deterministic-v1  
**Status:** FROZEN

---

## Overview

This module contains Project Mirror's deterministic computation core.
All outputs are **facts only** — no interpretations, meanings, or advice.

## Files

| File | Purpose | Status |
|------|---------|--------|
| `astrology.py` | True Sidereal positions, Equal houses | FROZEN |
| `human_design.py` | Type, Profile, Gates, Channels | FROZEN |
| `timezone_utils.py` | UTC resolution from local + offset | FROZEN |
| `numerology.py` | Life path calculations | Active |
| `consciousness.py` | Hawkins scale reference | Active |

## Constraints

1. **Outputs are deterministic** — Same input = same output, always
2. **Facts only** — No meanings, symbolism, or advice
3. **Frozen files require regression tests** before modification
4. **Version bump required** for any change to frozen files

## Regression Tests

```bash
cd /app/backend && python tests/test_mel_regression.py
```

All tests must pass before deployment.

## Interpretation Layer

The interpretation of deterministic facts happens in a **separate layer**.

📄 **See:** [`/app/backend/docs/INTERPRETATION_LAYER_v1.md`](../docs/INTERPRETATION_LAYER_v1.md)

This document defines the contract for how facts become narratives.
**Implementation is blocked** until a dedicated scope-locked session begins.

---

## Architecture

```
┌─────────────────────────────────────┐
│  THIS MODULE                        │
│  Deterministic Computation Core     │
│                                     │
│  Output: FACTS ONLY                 │
└──────────────┬──────────────────────┘
               │
      INTERPRETATION BOUNDARY
               │
               ▼
┌─────────────────────────────────────┐
│  Interpretation Layer (downstream)  │
│  See: docs/INTERPRETATION_LAYER_v1  │
└─────────────────────────────────────┘
```

---

*Do NOT add interpretation logic to this module.*
