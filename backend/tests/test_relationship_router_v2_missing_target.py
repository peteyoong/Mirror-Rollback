"""Sanity check: missing-target fallback emits target_unresolved_name & proposed_action."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.relationship_router_v2 import (
    resolve_relationship_context,
    _extract_proper_name_candidates,
)


def _r(msg, frame="self", role=None, saved=None):
    return resolve_relationship_context(
        self_user_id="u1",
        user_message=msg,
        active_frame=frame,
        saved_people=saved or [],
    )


def test_extract_proper_name_basic():
    assert _extract_proper_name_candidates("How does Sarah show up at work?") == ["Sarah"]
    assert _extract_proper_name_candidates("Tell me about Pete's 4th house") == ["Pete"]
    # planets/signs should be filtered
    assert "Saturn" not in _extract_proper_name_candidates("my Saturn return")
    # wh-words filtered
    assert _extract_proper_name_candidates("How am I doing today?") == []
    # multiple candidates
    cands = _extract_proper_name_candidates("Mel and Sarah are at odds")
    assert set(cands) == {"Mel", "Sarah"}
    # sentence-initial common name should still be detected when message has no wh-word
    assert _extract_proper_name_candidates("Sarah showed up late") == ["Sarah"]


def test_mt1_sarah_unresolved():
    r = _r("How does Sarah show up at work?")
    assert r.target is None
    assert r.target_unresolved_name == "Sarah"
    assert "target_unresolved" in r.missing_data
    pa = r.proposed_action
    assert pa is not None
    assert pa["type"] == "add_to_circle"
    assert pa["suggested_name"] == "Sarah"
    assert pa["reason"]
    assert pa["source_text"] == "How does Sarah show up at work?"
    assert 0 < pa["confidence"] <= 1


def test_mt2_husband_no_name():
    # role-only ("my husband") — no proper name → no proposed_action
    r = _r("Tell me about my husband's Saturn return")
    assert r.target_unresolved_name is None
    assert r.proposed_action is None


def test_mt3_alex_between_me():
    r = _r("What's going on between Alex and me?")
    assert r.target_unresolved_name == "Alex"
    assert r.proposed_action and r.proposed_action["suggested_name"] == "Alex"


def test_mt5_pete_unresolved():
    r = _r("Tell me about Pete's 4th house")
    assert r.target_unresolved_name == "Pete"
    assert r.proposed_action and r.proposed_action["suggested_name"] == "Pete"


def test_resolved_target_does_not_fire_fallback():
    saved = [{"id": "mel", "name": "Mel", "role": "partner", "closeness": 0.9}]
    r = _r("How is Mel doing today?", saved=saved)
    assert r.target == "mel"
    assert r.target_unresolved_name is None
    assert r.proposed_action is None


def test_partial_overlap_resolved():
    """If the proper name DOES match someone in saved_people (case-insensitive)
    we should NOT mark it unresolved."""
    saved = [{"id": "pete", "name": "Pete", "role": "colleague", "closeness": 0.8}]
    r = _r("Tell me about Pete's 4th house", saved=saved)
    assert r.target == "pete"
    assert r.target_unresolved_name is None


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in list(globals().items()) if k.startswith("test_") and callable(v)]
    fails = 0
    for fn in fns:
        try:
            fn()
            print(f"  ✓ {fn.__name__}")
        except Exception:
            fails += 1
            print(f"  ✗ {fn.__name__}")
            traceback.print_exc()
    print(f"\n{len(fns) - fails}/{len(fns)} passed")
    sys.exit(0 if fails == 0 else 1)
