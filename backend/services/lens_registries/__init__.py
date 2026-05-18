"""
Lens registries — one module per lens.  Each exposes a LensRegistry that
plugs into services.lens_conversation.

Build marker: multi-lens-chat-memory-v1
"""

from .astrology import ASTROLOGY_REGISTRY
from .human_design import HUMAN_DESIGN_REGISTRY
from .numerology import NUMEROLOGY_REGISTRY
from .enneagram import ENNEAGRAM_REGISTRY
from .bazi import BAZI_REGISTRY

REGISTRY_BY_LENS = {
    "astrology": ASTROLOGY_REGISTRY,
    "human_design": HUMAN_DESIGN_REGISTRY,
    "numerology": NUMEROLOGY_REGISTRY,
    "enneagram": ENNEAGRAM_REGISTRY,
    "bazi": BAZI_REGISTRY,
}


def get_registry(lens: str):
    """Return the LensRegistry for a given lens name, or None if unsupported."""
    return REGISTRY_BY_LENS.get(lens)
