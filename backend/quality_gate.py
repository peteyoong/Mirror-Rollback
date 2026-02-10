"""
Deep Dive Quality Gate - V1
============================

Enforces minimum quality standards for deep dive content with section-level
enforcement and automatic retry/augmentation pipeline.

Quality Thresholds:
- Per section: >= 900 characters OR >= 150 words
- Total (Astrology/Numerology): >= 3,000 characters
- Total (Human Design): >= 4,000 characters

Pipeline:
1. Generate via LLM → parse sections
2. Check quality gate
3. If any section is below minimum → retry with "expand detail" prompt
4. If still short after retry → augment only short sections with fallback

Usage:
    from quality_gate import QualityGate, QualityGateResult
    
    gate = QualityGate(lens="astrology")
    result = gate.check(parsed_sections)
    
    if not result.passed:
        # Retry or augment
        expand_prompt = gate.get_expand_prompt(result.short_sections)
"""

import logging
from typing import List, Dict, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# QUALITY THRESHOLDS
# ============================================================================

# Per-section minimums
MIN_SECTION_CHARS = 900
MIN_SECTION_WORDS = 150

# Per-lens total minimums
MIN_TOTAL_CHARS = {
    "astrology": 3000,
    "human_design": 4000,
    "human-design": 4000,
    "numerology": 3000,
    "enneagram": 3000,
}

# Maximum retry attempts
MAX_RETRY_COUNT = 1


class QualityStatus(str, Enum):
    PASSED = "passed"
    RETRY_NEEDED = "retry_needed"
    AUGMENT_NEEDED = "augment_needed"
    FAILED = "failed"


@dataclass
class ShortSection:
    """Info about a section that didn't meet quality standards"""
    section_id: str
    label: str
    char_count: int
    word_count: int
    min_chars: int = MIN_SECTION_CHARS
    min_words: int = MIN_SECTION_WORDS
    
    def to_dict(self) -> dict:
        return {
            "id": self.section_id,
            "label": self.label[:30],
            "chars": self.char_count,
            "words": self.word_count,
            "deficit_chars": max(0, self.min_chars - self.char_count),
            "deficit_words": max(0, self.min_words - self.word_count)
        }


@dataclass
class QualityGateResult:
    """Result of quality gate check"""
    passed: bool
    status: QualityStatus
    total_chars: int = 0
    total_words: int = 0
    min_total_chars: int = 3000
    short_sections: List[ShortSection] = field(default_factory=list)
    all_sections_count: int = 0
    passed_sections_count: int = 0
    
    # Debug fields
    quality_gate_triggered: bool = False
    retry_count: int = 0
    augmented_sections: List[str] = field(default_factory=list)
    
    def to_debug_dict(self) -> dict:
        return {
            "quality_gate_triggered": self.quality_gate_triggered,
            "retry_count": self.retry_count,
            "short_sections": [s.to_dict() for s in self.short_sections],
            "augmented_sections": self.augmented_sections,
            "total_chars": self.total_chars,
            "min_total_chars": self.min_total_chars,
            "passed": self.passed
        }


class QualityGate:
    """
    Quality gate for deep dive content with section-level enforcement.
    """
    
    def __init__(
        self,
        lens: str,
        min_section_chars: int = MIN_SECTION_CHARS,
        min_section_words: int = MIN_SECTION_WORDS,
        min_total_chars: int = None
    ):
        self.lens = lens.lower().replace("-", "_")
        self.min_section_chars = min_section_chars
        self.min_section_words = min_section_words
        self.min_total_chars = min_total_chars or MIN_TOTAL_CHARS.get(self.lens, 3000)
    
    def check_section(self, section_id: str, label: str, body: str) -> Tuple[bool, Optional[ShortSection]]:
        """
        Check if a single section meets quality standards.
        
        Returns:
            (passed, ShortSection if failed else None)
        """
        char_count = len(body) if body else 0
        word_count = len(body.split()) if body else 0
        
        # Section passes if it meets EITHER char OR word minimum
        passed = char_count >= self.min_section_chars or word_count >= self.min_section_words
        
        if passed:
            return True, None
        
        return False, ShortSection(
            section_id=section_id,
            label=label,
            char_count=char_count,
            word_count=word_count,
            min_chars=self.min_section_chars,
            min_words=self.min_section_words
        )
    
    def check(self, sections: List[Dict[str, Any]]) -> QualityGateResult:
        """
        Check all sections against quality standards.
        
        Args:
            sections: List of section dicts with 'label', 'body', and optionally 'section_id'
            
        Returns:
            QualityGateResult with pass/fail status and details
        """
        result = QualityGateResult(
            passed=True,
            status=QualityStatus.PASSED,
            min_total_chars=self.min_total_chars,
            all_sections_count=len(sections)
        )
        
        for i, section in enumerate(sections):
            label = section.get("label", f"Section {i+1}")
            body = section.get("body", "")
            section_id = section.get("section_id", label.lower().replace(" ", "_").replace(":", "")[:20])
            
            char_count = len(body) if body else 0
            word_count = len(body.split()) if body else 0
            
            result.total_chars += char_count
            result.total_words += word_count
            
            passed, short_info = self.check_section(section_id, label, body)
            
            if passed:
                result.passed_sections_count += 1
            else:
                result.short_sections.append(short_info)
        
        # Determine overall status
        if result.short_sections:
            result.passed = False
            result.status = QualityStatus.RETRY_NEEDED
            result.quality_gate_triggered = True
        
        # Also check total chars
        if result.total_chars < self.min_total_chars:
            result.passed = False
            if result.status == QualityStatus.PASSED:
                result.status = QualityStatus.RETRY_NEEDED
            result.quality_gate_triggered = True
        
        logger.info(f"[QUALITY_GATE] {self.lens}: passed={result.passed}, "
                   f"sections={result.passed_sections_count}/{result.all_sections_count}, "
                   f"total_chars={result.total_chars}/{self.min_total_chars}, "
                   f"short_sections={len(result.short_sections)}")
        
        return result
    
    def get_expand_prompt(self, short_sections: List[ShortSection]) -> str:
        """
        Generate a prompt asking the LLM to expand specific short sections.
        
        Args:
            short_sections: List of ShortSection objects to expand
            
        Returns:
            Prompt string for retry
        """
        if not short_sections:
            return ""
        
        section_list = "\n".join([
            f"- {s.section_id}: Currently {s.char_count} chars / {s.word_count} words. "
            f"Need at least {s.min_chars} chars or {s.min_words} words."
            for s in short_sections
        ])
        
        return f"""
IMPORTANT: The following sections are too short and need more detail:

{section_list}

Please EXPAND these sections with:
- More specific observations about patterns
- Concrete examples of how these patterns might manifest
- Nuanced exploration of both comfortable and challenging aspects
- At least 150 words per section

Keep the same section format (---SECTION:id--- / ---BODY--- / ---END---).
Regenerate ALL sections, but focus extra attention on expanding the short ones.
"""
    
    def get_short_section_ids(self, result: QualityGateResult) -> List[str]:
        """Get list of section IDs that are short."""
        return [s.section_id for s in result.short_sections]


def augment_short_sections(
    sections: List[Dict[str, Any]],
    short_section_ids: List[str],
    fallback_content: Dict[str, Tuple[str, str]],
    min_chars: int = MIN_SECTION_CHARS
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Augment short sections with fallback content.
    
    Args:
        sections: List of section dicts
        short_section_ids: IDs of sections to augment
        fallback_content: Dict of section_id -> (label, body)
        min_chars: Minimum chars to consider section adequate
        
    Returns:
        (augmented_sections, list of augmented section ids)
    """
    augmented = []
    augmented_ids = []
    
    for section in sections:
        label = section.get("label", "")
        body = section.get("body", "")
        section_id = section.get("section_id", "")
        
        # Try to match section_id from label if not provided
        if not section_id:
            section_id = label.lower().replace(" ", "_").replace(":", "")[:20]
        
        # Check if this section needs augmentation
        needs_augment = (
            section_id in short_section_ids or
            any(sid in section_id or section_id in sid for sid in short_section_ids)
        )
        
        if needs_augment and len(body) < min_chars:
            # Check if already augmented (idempotent guard)
            if section.get("_augmented"):
                augmented.append(section)
                logger.info(f"[QUALITY_GATE] Section '{section_id}' already augmented (flag), skipping")
                continue
            
            # Find matching fallback
            fallback_body = None
            for fb_id, (fb_label, fb_body) in fallback_content.items():
                if fb_id in section_id or section_id in fb_id:
                    fallback_body = fb_body
                    break
            
            if fallback_body:
                # Augment: keep LLM content, append fallback
                augmented_body = body + "\n\n" + fallback_body if body else fallback_body
                augmented.append({
                    **section,
                    "body": augmented_body,
                    "augmented": True,
                    "_augmented": True  # Idempotent flag to prevent re-augmentation
                })
                augmented_ids.append(section_id)
                logger.info(f"[QUALITY_GATE] Augmented section '{section_id}': "
                           f"{len(body)} -> {len(augmented_body)} chars")
            else:
                augmented.append(section)
        else:
            augmented.append(section)
    
    return augmented, augmented_ids


async def generate_with_quality_gate(
    lens: str,
    generate_fn: Callable,
    parse_fn: Callable,
    fallback_content: Dict[str, Tuple[str, str]],
    expected_sections: List[str],
    context: Dict[str, Any],
    base_prompt: str,
    max_retries: int = MAX_RETRY_COUNT
) -> Tuple[List[Dict[str, Any]], QualityGateResult]:
    """
    Generate deep dive content with quality gate enforcement.
    
    Pipeline:
    1. Generate via LLM
    2. Parse sections
    3. Check quality gate
    4. If short sections: retry with expand prompt
    5. If still short: augment with fallback
    
    Args:
        lens: Lens type (astrology, human_design, numerology)
        generate_fn: Async function(prompt) -> raw_text
        parse_fn: Function(raw_text, expected_sections, fallback) -> ParseResult
        fallback_content: Dict of section_id -> (label, body)
        expected_sections: List of expected section IDs
        context: Context dict for logging
        base_prompt: Base system prompt
        max_retries: Maximum retry attempts
        
    Returns:
        (sections_list, QualityGateResult)
    """
    gate = QualityGate(lens)
    cumulative_result = QualityGateResult(
        passed=False,
        status=QualityStatus.RETRY_NEEDED,
        min_total_chars=gate.min_total_chars
    )
    
    current_prompt = base_prompt
    sections = []
    
    for attempt in range(max_retries + 1):
        cumulative_result.retry_count = attempt
        
        # Generate
        logger.info(f"[QUALITY_GATE] {lens} generation attempt {attempt + 1}/{max_retries + 1}")
        raw_text = await generate_fn(current_prompt)
        
        # Parse
        parse_result = parse_fn(raw_text, expected_sections, fallback_content)
        sections = [
            {"label": s.label, "body": s.body, "section_id": s.section_id}
            for s in parse_result.sections
        ]
        
        # Check quality
        gate_result = gate.check(sections)
        cumulative_result.total_chars = gate_result.total_chars
        cumulative_result.total_words = gate_result.total_words
        cumulative_result.all_sections_count = gate_result.all_sections_count
        cumulative_result.passed_sections_count = gate_result.passed_sections_count
        cumulative_result.short_sections = gate_result.short_sections
        cumulative_result.quality_gate_triggered = gate_result.quality_gate_triggered
        
        if gate_result.passed:
            cumulative_result.passed = True
            cumulative_result.status = QualityStatus.PASSED
            logger.info(f"[QUALITY_GATE] {lens} passed on attempt {attempt + 1}")
            return sections, cumulative_result
        
        # If we have retries left, prepare expand prompt
        if attempt < max_retries and gate_result.short_sections:
            expand_prompt = gate.get_expand_prompt(gate_result.short_sections)
            current_prompt = base_prompt + "\n\n" + expand_prompt
            logger.info(f"[QUALITY_GATE] {lens} retry {attempt + 1}: "
                       f"{len(gate_result.short_sections)} short sections")
    
    # After all retries, augment short sections
    if cumulative_result.short_sections:
        short_ids = [s.section_id for s in cumulative_result.short_sections]
        sections, augmented_ids = augment_short_sections(
            sections, short_ids, fallback_content, gate.min_section_chars
        )
        cumulative_result.augmented_sections = augmented_ids
        cumulative_result.status = QualityStatus.AUGMENT_NEEDED
        
        # Recheck after augmentation
        final_check = gate.check(sections)
        cumulative_result.total_chars = final_check.total_chars
        cumulative_result.total_words = final_check.total_words
        cumulative_result.passed = final_check.passed
        
        logger.info(f"[QUALITY_GATE] {lens} augmented {len(augmented_ids)} sections, "
                   f"final chars={cumulative_result.total_chars}")
    
    return sections, cumulative_result


# ============================================================================
# REGRESSION TESTS
# ============================================================================

def test_short_section_triggers_retry():
    """Test that short sections trigger quality gate and return correct status"""
    gate = QualityGate(lens="astrology")
    
    # Sections with one short
    sections = [
        {"label": "Sun Section", "body": "A" * 1000, "section_id": "sun"},  # OK
        {"label": "Moon Section", "body": "Short content", "section_id": "moon"},  # Short!
        {"label": "Ascendant Section", "body": "B" * 950, "section_id": "ascendant"},  # OK
    ]
    
    result = gate.check(sections)
    
    assert not result.passed, "Should fail with short section"
    assert result.quality_gate_triggered, "Quality gate should be triggered"
    assert len(result.short_sections) == 1, f"Should have 1 short section, got {len(result.short_sections)}"
    assert result.short_sections[0].section_id == "moon", "Moon should be the short section"
    assert result.status == QualityStatus.RETRY_NEEDED, f"Status should be RETRY_NEEDED, got {result.status}"
    
    # Test expand prompt generation
    expand_prompt = gate.get_expand_prompt(result.short_sections)
    assert "moon" in expand_prompt.lower(), "Expand prompt should mention moon section"
    assert "150 words" in expand_prompt, "Expand prompt should mention word requirement"
    
    print("✅ Short section triggers retry test PASSED")
    return True


def test_augmentation_after_retry():
    """Test that short sections get augmented with fallback after retry fails"""
    
    # Simulate sections still short after retry
    sections = [
        {"label": "Sun Section", "body": "Still short sun content that didn't expand enough.", "section_id": "sun"},
        {"label": "Moon Section", "body": "B" * 1000, "section_id": "moon"},  # OK
    ]
    
    short_section_ids = ["sun"]
    
    # Create substantial fallback content (900+ chars)
    fallback_sun_content = """This is the fallback sun content that provides substantial depth for the deep dive section. With your Sun placement, there's a particular quality to how you express your sense of self and engage with life's central themes. This placement shapes your core identity orientation and the way you naturally approach situations that call for leadership, self-expression, or creative initiative.

The Sun represents your essential vitality—the light you carry and the way you tend to shine in the world. It's not about who you should be, but about noticing patterns in how you already operate when you're most yourself. Some find this placement brings a natural orientation toward certain kinds of challenges or creative expressions, while others notice it more in their relationship to authority, visibility, or personal power.

The shadow aspects of this placement might show up as tendencies toward ego-identification, excessive need for recognition, or difficulty sharing the spotlight. These aren't flaws to fix but patterns to notice with curiosity."""
    
    fallback_content = {
        "sun": ("Sun: Your Core Orientation", fallback_sun_content),
    }
    
    augmented, augmented_ids = augment_short_sections(
        sections, short_section_ids, fallback_content, min_chars=900
    )
    
    assert "sun" in augmented_ids, "Sun should be in augmented list"
    assert len(augmented) == 2, "Should still have 2 sections"
    
    sun_section = next(s for s in augmented if s.get("section_id") == "sun")
    assert len(sun_section["body"]) > 900, f"Sun should be augmented to > 900 chars, got {len(sun_section['body'])}"
    assert sun_section.get("augmented") == True, "Sun should be marked as augmented"
    
    print("✅ Augmentation after retry test PASSED")
    return True


def test_total_chars_threshold():
    """Test that total character threshold is enforced"""
    gate = QualityGate(lens="human_design")  # 4000 char minimum
    
    # Each section meets minimum, but total is low
    sections = [
        {"label": "Type", "body": "A" * 500, "section_id": "type"},
        {"label": "Strategy", "body": "B" * 500, "section_id": "strategy"},
        {"label": "Authority", "body": "C" * 500, "section_id": "authority"},
    ]
    
    result = gate.check(sections)
    
    assert not result.passed, "Should fail due to low total chars"
    assert result.quality_gate_triggered, "Quality gate should be triggered"
    assert result.total_chars == 1500, f"Total should be 1500, got {result.total_chars}"
    
    print("✅ Total chars threshold test PASSED")
    return True


def test_quality_gate_passes():
    """Test that quality gate passes with adequate content"""
    gate = QualityGate(lens="astrology")
    
    sections = [
        {"label": "Sun", "body": "A" * 1000, "section_id": "sun"},
        {"label": "Moon", "body": "B" * 1000, "section_id": "moon"},
        {"label": "Ascendant", "body": "C" * 1000, "section_id": "ascendant"},
    ]
    
    result = gate.check(sections)
    
    assert result.passed, "Should pass with adequate content"
    assert not result.quality_gate_triggered, "Quality gate should not be triggered"
    assert result.status == QualityStatus.PASSED
    assert result.total_chars == 3000
    
    print("✅ Quality gate passes test PASSED")
    return True


def test_word_count_alternative():
    """Test that word count can satisfy requirement instead of char count"""
    gate = QualityGate(lens="astrology")
    
    # Short chars but 150+ words
    long_words_content = " ".join(["word"] * 160)  # 160 words, ~800 chars
    
    sections = [
        {"label": "Sun", "body": long_words_content, "section_id": "sun"},
        {"label": "Moon", "body": "A" * 1000, "section_id": "moon"},
        {"label": "Ascendant", "body": "B" * 1000, "section_id": "ascendant"},
    ]
    
    result = gate.check(sections)
    
    # Sun should pass due to word count even though char count is low
    sun_short = any(s.section_id == "sun" for s in result.short_sections)
    assert not sun_short, "Sun should pass due to word count >= 150"
    
    print("✅ Word count alternative test PASSED")
    return True


def run_quality_gate_tests():
    """Run all quality gate regression tests"""
    print("\n" + "="*60)
    print("🧪 QUALITY GATE REGRESSION TESTS")
    print("="*60 + "\n")
    
    tests = [
        ("Short Section Triggers Retry", test_short_section_triggers_retry),
        ("Augmentation After Retry", test_augmentation_after_retry),
        ("Total Chars Threshold", test_total_chars_threshold),
        ("Quality Gate Passes", test_quality_gate_passes),
        ("Word Count Alternative", test_word_count_alternative),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ {name} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {name} ERROR: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    run_quality_gate_tests()
