"""test_the_mirror_session3e_consolidation.py
========================================================================
Session-3e final HD UX consolidation gate.

- FE component exports both HDReadingSections + HDExploreSections and
  the parent uses both (Reading + Explore modes).
- The old "13-planet activation table" label is gone; the new label is
  "Personality and Design Activations".
- Reading mode presents recognition-first sections and does not render
  the legacy Explore-mode structural cards.
- Explore mode presents BodyGraph first and does not render the
  Reading-mode recognition-first sections.
- Profile-coverage matrix is accurate: all 12 pairs are FULLY_AUTHORED.
- No 13-planet / session terminology anywhere in the FE component or
  the backend narrative payloads.
- All 99 previous tests remain green.
"""
from __future__ import annotations

import os
import re
import sys
import pathlib

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


DEEP_DIVE_FE = pathlib.Path(
    "/app/frontend/components/lens_contract/HumanDesignDeepDiveSections.tsx"
)
PARENT_FE = pathlib.Path("/app/frontend/components/HumanDesignLensView.tsx")


# ─────────────────────────────────────────────────────────────
# 1. Component exports both Reading + Explore sections
# ─────────────────────────────────────────────────────────────
def test_component_exports_reading_and_explore():
    assert DEEP_DIVE_FE.exists()
    src = DEEP_DIVE_FE.read_text()
    assert "export const HDReadingSections" in src, src[:200]
    assert "export const HDExploreSections" in src, src[:200]


def test_parent_uses_both_reading_and_explore_exports():
    src = PARENT_FE.read_text()
    assert "HDReadingSections" in src, "parent must render HDReadingSections"
    assert "HDExploreSections" in src, "parent must render HDExploreSections"


# ─────────────────────────────────────────────────────────────
# 2. No top-of-Deep-Dive stacking
# ─────────────────────────────────────────────────────────────
def test_new_canonical_content_not_stacked_above_modes():
    """The parent's renderDeepDiveTab must not mount the canonical
    sections outside of Reading or Explore mode."""
    src = PARENT_FE.read_text()
    # The renderDeepDiveTab body follows a well-known sentinel:
    marker = "// DEEP DIVE TAB - with mode toggle (Explore / Reading)"
    idx = src.find(marker)
    assert idx >= 0
    # Slice out the function body (~ next 900 chars is enough for the
    # skeleton pre-toggle block).
    block = src[idx:idx + 1500]
    # No direct <HumanDesignDeepDiveSections /> or <HDReadingSections />
    # or <HDExploreSections /> BEFORE the mode toggle.
    pre_toggle = block.split("Mode Toggle", 1)[0]
    for banned in (
        "<HumanDesignDeepDiveSections",
        "<HDReadingSections",
        "<HDExploreSections",
    ):
        assert banned not in pre_toggle, (banned, pre_toggle[:400])


# ─────────────────────────────────────────────────────────────
# 3. Activation-table terminology — no "13-planet"
# ─────────────────────────────────────────────────────────────
def _strip_comments_and_docstrings(src: str, lang: str) -> str:
    """Remove comments/docstrings so we only inspect user-visible strings."""
    if lang == "ts":
        # Remove /* ... */ blocks and // line comments
        src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
        src = re.sub(r"(?m)^\s*//.*$", "", src)
    else:  # py
        # Remove triple-quoted docstrings and # line comments
        src = re.sub(r'"""(?:.|\n)*?"""', "", src)
        src = re.sub(r"'''(?:.|\n)*?'''", "", src)
        src = re.sub(r"(?m)#.*$", "", src)
    return src


def test_no_thirteen_planet_terminology_in_fe():
    src = DEEP_DIVE_FE.read_text()
    src_no_comments = _strip_comments_and_docstrings(src, "ts")
    lowered = src_no_comments.lower()
    for banned in ("13-planet", "13 planet", "thirteen planet"):
        assert banned not in lowered, banned


def test_activation_table_label_is_canonical_in_fe():
    src = DEEP_DIVE_FE.read_text()
    assert "Personality and Design Activations" in src, "canonical label missing"


def test_no_thirteen_planet_terminology_in_backend():
    """Even the backend must not label the activation surface as
    '13-planet' in any user-facing string (comments/docstrings ignored)."""
    root = pathlib.Path("/app/backend/services")
    for p in root.glob("hd_*.py"):
        src = p.read_text()
        src_no_comments = _strip_comments_and_docstrings(src, "py")
        txt = src_no_comments.lower()
        assert "13-planet" not in txt, p
        assert "13 planet" not in txt, p


# ─────────────────────────────────────────────────────────────
# 4. Profile-coverage matrix accuracy — all 12 FULLY_AUTHORED
# ─────────────────────────────────────────────────────────────
def test_all_twelve_profiles_are_authored():
    from services.hd_narratives import profile_narrative
    all_profiles = ["1/3", "1/4", "2/4", "2/5", "3/5", "3/6",
                     "4/6", "4/1", "5/1", "5/2", "6/2", "6/3"]
    for p in all_profiles:
        blk = profile_narrative(p)
        assert blk["variant"] == "authored", (p, blk["variant"])
        assert blk["text"], p


# ─────────────────────────────────────────────────────────────
# 5. No session/debug terminology in Reading / Explore surfaces
# ─────────────────────────────────────────────────────────────
def test_no_session_debug_terminology_in_fe():
    src = DEEP_DIVE_FE.read_text()
    for banned in [
        "Session-3c · Human Design narratives",
        "The Mirror · Session-3c",
        "Authored narrative pending",
        "structural_fallback",
    ]:
        assert banned not in src, banned


# ─────────────────────────────────────────────────────────────
# 6. Explore mode BodyGraph is preserved in the parent
# ─────────────────────────────────────────────────────────────
def test_explore_mode_still_renders_bodygraph():
    src = PARENT_FE.read_text()
    # renderExploreMode body must reference renderImprovedBodygraph
    idx = src.find("const renderExploreMode = ()")
    assert idx >= 0
    body = src[idx:idx + 5000]
    assert "renderImprovedBodygraph" in body, "BodyGraph must be preserved in Explore"


# ─────────────────────────────────────────────────────────────
# 7. Reading mode does NOT render legacy PDF sections
# ─────────────────────────────────────────────────────────────
def test_reading_mode_uses_only_canonical_sections():
    src = PARENT_FE.read_text()
    idx = src.find("const renderReadingMode = ()")
    assert idx >= 0
    # Slice up to the end of the function; find the first "  };"
    body = src[idx:idx + 4000]
    # Canonical is the ONLY thing inside; legacy sections were moved to
    # _renderLegacyReadingMode.
    assert "<HDReadingSections" in body, "Reading mode must use HDReadingSections"
    # Legacy section titles must NOT appear in the active renderReadingMode
    early_body = body.split("_renderLegacyReadingMode", 1)[0]
    for banned in (
        "Your Core Pattern",
        "How You Make Decisions",
        "How Others Experience You",
        "Where Things Go Wrong",
        "What Actually Works For You",
        "Your Deeper Pattern",
    ):
        assert banned not in early_body, (banned, early_body[-400:])


# ─────────────────────────────────────────────────────────────
# 8. Regression umbrella — all earlier tests still green
# ─────────────────────────────────────────────────────────────
def test_regression_earlier_sessions_still_green():
    import subprocess
    result = subprocess.run(
        [
            "pytest",
            "tests/test_the_mirror_session1_integrity.py",
            "tests/test_lens_content_contract.py",
            "tests/test_the_mirror_session3_hd_structural.py",
            "tests/test_the_mirror_session3b_narratives.py",
            "tests/test_the_mirror_session3c_topology_activation.py",
            "tests/test_the_mirror_session3c_narratives_corestory.py",
            "tests/test_the_mirror_session3d_generalisation.py",
            "-q", "--no-header", "-x",
        ],
        capture_output=True, text=True, cwd=_ROOT,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
