"""test_forum_mapping_http_v154.py — v1.5.4 LIVE regression tests
-----------------------------------------------------------------
HTTP-level checks against the deployed preview backend. Validates the
v1.5.4 surgical fixes:

  1. Headline contains NO raw lens identifiers
     (human_design / numerology / enneagram / bazi / astrology / "converge)").
  2. Evidence ladder claims do NOT echo any story slot or repair line
     (sentence-level, normalized).
  3. None of the broken production phrases ever appear in story.* or
     evidence_ladder[*].claim.
  4. relationship_synthesis.undertone_for_today does not echo any story
     slot at sentence level.
  5. Mel ASC migration sanity (peek_chart_angles).

The endpoint shape (verified on live preview):
    GET /api/forums/{forum_id}/member-mappings?user_id=<viewer_user_id>
    → {"success": True, "mappings": [...]}
"""
from __future__ import annotations
import os
import re
import pytest
import requests


# ─── Resolve preview backend URL from frontend/.env ────────────────────
def _resolve_backend_url() -> str:
    url = os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL")
    if not url:
        env_path = "/app/frontend/.env"
        if os.path.exists(env_path):
            with open(env_path) as fh:
                for line in fh:
                    line = line.strip()
                    if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
                        url = line.split("=", 1)[1].strip()
                        break
    if not url:
        pytest.skip("EXPO_PUBLIC_BACKEND_URL not configured")
    return url.rstrip("/")


BASE_URL = _resolve_backend_url()

PETE_ID = "697f0c6abf35c0528ff06954"
MEL_ID = "697ec826ad4b18f75bf42616"
PETE_MEL_FORUM = "69dd05eaa333335fcbf3ad33"
YOONG_FORUM = "69dda348de9cb1c83c0780fa"

# Strings that MUST NOT appear in the headline.
HEADLINE_BAD_TOKENS = (
    "human_design", "numerology", "enneagram", "bazi", "astrology",
    "converge)",
)

# Broken phrases reported in production v1.5.3 screenshots.
BROKEN_PHRASES = [
    # double article
    "the the field between you",
    # malformed possessive
    "pete's one of you",
    "mel's one of you",
    "ana's one of you",
    # compound residue
    "open-the field",
    "defined-the field",
    # leaked HD jargon
    "lunar-authority",
]
RAW_CENTERS = ("ajna", "solar plexus", " sacral ", " sacral.", " sacral,")
# Regex catching "the field between <ProperName>" (any non-pronoun name)
FIELD_BETWEEN_NAME_RE = re.compile(r"the field between [A-Z][a-z]+")


# ─── Helpers ───────────────────────────────────────────────────────────
def _sentences(text: str):
    if not text:
        return []
    # Split on sentence terminators while keeping reasonably-sized pieces
    parts = re.split(r"(?<=[\.!?])\s+", str(text).strip())
    return [p.strip() for p in parts if p and p.strip()]


def _norm(s: str) -> str:
    s = (s or "").lower().strip()
    # collapse whitespace
    s = re.sub(r"\s+", " ", s)
    # strip trailing punctuation
    s = re.sub(r"[\.!?;:,'\"\u2013\u2014\-\s]+$", "", s)
    s = re.sub(r"^[\.!?;:,'\"\u2013\u2014\-\s]+", "", s)
    return s


def _story_sentence_set(story: dict) -> set:
    """Every sentence in every story slot (incl. repair_pathway lines)."""
    out = set()
    for key in ("headline", "summary", "current_movement",
                "growth_edge", "shadow_pattern", "question_to_ask"):
        v = story.get(key)
        if isinstance(v, str):
            for sent in _sentences(v):
                n = _norm(sent)
                if n:
                    out.add(n)
    for line in story.get("repair_pathway") or []:
        if isinstance(line, str):
            for sent in _sentences(line):
                n = _norm(sent)
                if n:
                    out.add(n)
    return out


def _all_story_text(story: dict) -> str:
    parts = [
        story.get("headline", ""),
        story.get("summary", ""),
        story.get("current_movement", ""),
        story.get("growth_edge", ""),
        story.get("shadow_pattern", ""),
        story.get("question_to_ask", ""),
    ]
    parts.extend(story.get("repair_pathway") or [])
    return " ".join([p for p in parts if isinstance(p, str)])


# ─── Fixtures ──────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _fetch_mappings(session, forum_id, viewer_id=PETE_ID):
    r = session.get(
        f"{BASE_URL}/api/forums/{forum_id}/member-mappings",
        params={"user_id": viewer_id},
        timeout=60,
    )
    assert r.status_code == 200, f"GET /member-mappings → {r.status_code}: {r.text[:300]}"
    data = r.json()
    assert data.get("success") is True
    return data["mappings"]


@pytest.fixture(scope="module")
def pete_mel_mappings(session):
    return _fetch_mappings(session, PETE_MEL_FORUM)


@pytest.fixture(scope="module")
def yoong_mappings(session):
    return _fetch_mappings(session, YOONG_FORUM)


# ─── 1) Headline must not leak lens names ──────────────────────────────
def test_pete_mel_headline_no_lens_names(pete_mel_mappings):
    assert pete_mel_mappings, "no mappings returned"
    for m in pete_mel_mappings:
        rs = m.get("relationship_synthesis") or {}
        story = rs.get("story") or {}
        h = (story.get("headline") or "").lower()
        assert h, f"{m['member_name']}: missing headline"
        for tok in HEADLINE_BAD_TOKENS:
            assert tok not in h, (
                f"{m['member_name']} headline still leaks '{tok}': "
                f"{story.get('headline')!r}"
            )


def test_yoong_headlines_no_lens_names(yoong_mappings):
    assert yoong_mappings, "no mappings returned"
    for m in yoong_mappings:
        rs = m.get("relationship_synthesis") or {}
        story = rs.get("story") or {}
        h = (story.get("headline") or "").lower()
        assert h, f"{m['member_name']}: missing headline"
        for tok in HEADLINE_BAD_TOKENS:
            assert tok not in h, (
                f"{m['member_name']} headline leaks '{tok}': "
                f"{story.get('headline')!r}"
            )


# ─── 2) Ladder must not echo story slots (sentence-level) ───────────────
def _assert_ladder_no_echo(mapping):
    rs = mapping.get("relationship_synthesis") or {}
    story = rs.get("story") or {}
    ladder = rs.get("evidence_ladder") or []
    # If ladder has only 1 entry it's the fallback case (allowed to echo)
    if len(ladder) <= 1:
        return
    story_sents = _story_sentence_set(story)
    for entry in ladder:
        claim = entry.get("claim") or ""
        for sent in _sentences(claim):
            n = _norm(sent)
            if not n:
                continue
            assert n not in story_sents, (
                f"{mapping['member_name']} ladder echoes story slot:\n"
                f"  ladder claim sentence: {sent!r}\n"
                f"  duplicated norm: {n!r}"
            )


def test_pete_mel_ladder_does_not_echo_story(pete_mel_mappings):
    for m in pete_mel_mappings:
        _assert_ladder_no_echo(m)


def test_yoong_ladder_does_not_echo_story(yoong_mappings):
    for m in yoong_mappings:
        _assert_ladder_no_echo(m)


# ─── 3) No broken phrases anywhere in story or ladder ──────────────────
def _assert_no_broken_phrases(mapping):
    rs = mapping.get("relationship_synthesis") or {}
    story = rs.get("story") or {}
    ladder = rs.get("evidence_ladder") or []

    blob_for_story = _all_story_text(story)
    blob_for_ladder = " ".join([(e.get("claim") or "") for e in ladder])
    full_blob = (blob_for_story + " " + blob_for_ladder).lower()

    for bad in BROKEN_PHRASES:
        assert bad not in full_blob, (
            f"{mapping['member_name']}: broken phrase '{bad}' leaked.\n"
            f"  story+ladder blob excerpt: "
            f"{full_blob[max(0, full_blob.find(bad)-40):full_blob.find(bad)+80]!r}"
        )

    # "the field between <ProperName>" regex on cased text (not lowercased)
    cased_blob = blob_for_story + " " + " ".join([(e.get("claim") or "") for e in ladder])
    m = FIELD_BETWEEN_NAME_RE.search(cased_blob)
    assert m is None, (
        f"{mapping['member_name']}: broken phrase pattern leaked: {m.group(0)!r}\n"
        f"  context: ...{cased_blob[max(0,m.start()-40):m.end()+40]}..."
    )

    # Raw HD center names
    for c in RAW_CENTERS:
        # Use a stricter form — look only in story (ladder is allowed to
        # carry technical refs in supporting_signals, but `claim` is
        # human-readable too, so we still scan it).
        assert c not in full_blob, (
            f"{mapping['member_name']}: raw HD center token '{c.strip()}' "
            f"leaked into story/ladder.\n  blob excerpt: "
            f"{full_blob[max(0, full_blob.find(c)-40):full_blob.find(c)+80]!r}"
        )


def test_pete_mel_no_broken_phrases(pete_mel_mappings):
    for m in pete_mel_mappings:
        _assert_no_broken_phrases(m)


def test_yoong_no_broken_phrases(yoong_mappings):
    for m in yoong_mappings:
        _assert_no_broken_phrases(m)


# ─── 4) Undertone must not echo story slots ────────────────────────────
def _assert_undertone_independent(mapping):
    rs = mapping.get("relationship_synthesis") or {}
    story = rs.get("story") or {}
    undertone = rs.get("undertone_for_today") or ""
    if not undertone:
        return  # spec allows empty
    story_sents = _story_sentence_set(story)
    for sent in _sentences(undertone):
        n = _norm(sent)
        if not n:
            continue
        assert n not in story_sents, (
            f"{mapping['member_name']}: undertone echoes story slot:\n"
            f"  undertone sentence: {sent!r}"
        )


def test_pete_mel_undertone_independent(pete_mel_mappings):
    for m in pete_mel_mappings:
        _assert_undertone_independent(m)


def test_yoong_undertone_independent(yoong_mappings):
    for m in yoong_mappings:
        _assert_undertone_independent(m)


# ─── 5) Mel ASC sanity (peek_chart_angles) ─────────────────────────────
def test_mel_asc_sanity(session):
    r = session.get(
        f"{BASE_URL}/api/admin/peek_chart_angles",
        params={
            "user_id": MEL_ID,
            "confirm": "PEEK_CHART_ANGLES_2026_06_26",
        },
        timeout=30,
    )
    assert r.status_code == 200, f"peek_chart_angles → {r.status_code}: {r.text[:200]}"
    payload = r.json()
    assert payload.get("ok") is True, f"peek_chart_angles returned not-ok: {payload}"

    asc = payload.get("stored", {}).get("ASC") or {}
    assert asc.get("sign") == "Cancer", (
        f"Mel ASC sign expected Cancer, got {asc!r}"
    )
    deg = asc.get("degree")
    assert isinstance(deg, (int, float)), f"ASC degree missing: {asc!r}"
    # Spec says ~3.0; tolerate 2.5–3.6 (Cancer-band)
    assert 2.5 <= deg <= 3.6, f"Mel ASC degree out of expected band: {deg}"


# ─── 6) Case-4 auto-migration code path is wired into server ────────────
def test_case4_legacy_plus_08_fallback_code_present():
    """Static-source check: Case 4 detection logic exists in server.py and
    references the exact tokens the request requires. Cannot exercise the
    migration here because dev Mel chart is already on +07:30; the bad
    state lives on production."""
    src_path = "/app/backend/server.py"
    assert os.path.exists(src_path), "server.py missing"
    with open(src_path) as fh:
        src = fh.read()
    # Required signals for Case 4
    required = [
        'Case 4',
        'resolved_offset',
        '"+08:00"',
        'provenance_hash',
        'Asia/Kuala_Lumpur',
        'Asia/Kuching',
        'Asia/Singapore',
        'Asia/Brunei',
        'legacy_plus_08_fallback_pre_1982_malaysia',
        'bd.year < 1982',
    ]
    missing = [t for t in required if t not in src]
    assert not missing, f"Case-4 logic missing tokens in server.py: {missing}"


# ─── 7) Smoke: structure is intact (story keys, ladder shape) ─────────
def _assert_payload_shape(mapping):
    rs = mapping.get("relationship_synthesis") or {}
    assert "story" in rs, f"{mapping['member_name']}: missing story"
    assert "evidence_ladder" in rs, f"{mapping['member_name']}: missing ladder"
    story = rs["story"]
    for k in ("headline", "summary"):
        assert isinstance(story.get(k), str) and story.get(k), (
            f"{mapping['member_name']}: missing story.{k}"
        )
    ladder = rs["evidence_ladder"]
    assert isinstance(ladder, list) and ladder, (
        f"{mapping['member_name']}: empty ladder"
    )
    for e in ladder:
        for k in ("claim", "supporting_signals", "lens_contributions",
                  "technical_refs"):
            assert k in e, (
                f"{mapping['member_name']}: ladder entry missing key {k}"
            )


def test_pete_mel_payload_shape(pete_mel_mappings):
    for m in pete_mel_mappings:
        _assert_payload_shape(m)


def test_yoong_payload_shape(yoong_mappings):
    for m in yoong_mappings:
        _assert_payload_shape(m)
