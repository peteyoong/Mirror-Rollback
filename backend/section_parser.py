"""
Plain Text Section Parser for Deep Dive LLM Responses
======================================================

This module provides resilient parsing of LLM responses that use plain text
section markers instead of JSON. This eliminates JSON truncation failures.

Format Expected from LLM:
-------------------------
---SECTION:section_id---
Section Title Here
---BODY---
The body content for this section goes here.
It can span multiple lines and paragraphs.

---SECTION:another_section---
Another Section Title
---BODY---
More content here...

---END---

Parsing is resilient:
- Missing sections are skipped (other sections still returned)
- Truncated sections are marked as partial
- Malformed markers are handled gracefully
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class SectionStatus(str, Enum):
    OK = "ok"
    PARTIAL = "partial"
    MISSING = "missing"
    ERROR = "error"


@dataclass
class ParsedSection:
    """A single parsed section from LLM output"""
    section_id: str
    label: str
    body: str
    status: SectionStatus = SectionStatus.OK
    char_count: int = 0
    word_count: int = 0
    
    def __post_init__(self):
        self.char_count = len(self.body)
        self.word_count = len(self.body.split()) if self.body else 0
    
    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "body": self.body,
            "status": self.status.value if self.status != SectionStatus.OK else None
        }
    
    def to_output_dict(self) -> dict:
        """Return dict for API output (excludes status if OK)"""
        d = {"id": self.section_id, "label": self.label, "body": self.body}
        if self.status != SectionStatus.OK:
            d["status"] = self.status.value
        return d


@dataclass 
class ParseResult:
    """Result of parsing LLM plain text output"""
    sections: List[ParsedSection] = field(default_factory=list)
    source: str = "LLM"  # LLM, LLM_PARTIAL, FALLBACK
    truncated: bool = False
    raw_length: int = 0
    parse_errors: List[str] = field(default_factory=list)
    sections_ok: int = 0
    sections_partial: int = 0
    sections_missing: int = 0
    
    def to_sections_list(self) -> List[dict]:
        """Convert to list of section dicts for API response"""
        return [s.to_output_dict() for s in self.sections if s.body]
    
    def get_trace(self) -> List[dict]:
        """Get section generation trace for debug stamp"""
        return [
            {
                "section_id": s.section_id,
                "status": s.status.value,
                "source": "llm" if s.status in (SectionStatus.OK, SectionStatus.PARTIAL) else "missing",
                "char_count": s.char_count,
                "word_count": s.word_count
            }
            for s in self.sections
        ]


# Section marker patterns
SECTION_START_PATTERN = re.compile(r'---SECTION:(\w+)---\s*\n?', re.IGNORECASE)
BODY_MARKER_PATTERN = re.compile(r'---BODY---\s*\n?', re.IGNORECASE)
END_MARKER_PATTERN = re.compile(r'---END---', re.IGNORECASE)

# Alternative patterns for flexibility
ALT_SECTION_PATTERN = re.compile(r'\[SECTION:(\w+)\]|\*\*SECTION:(\w+)\*\*|##\s*SECTION:(\w+)', re.IGNORECASE)


def parse_plain_text_sections(
    raw_text: str,
    expected_sections: List[str] = None,
    fallback_content: Dict[str, Tuple[str, str]] = None,
    min_body_length: int = 50
) -> ParseResult:
    """
    Parse plain text LLM output into sections.
    
    Args:
        raw_text: The raw LLM response text
        expected_sections: List of expected section IDs (for detecting missing sections)
        fallback_content: Dict of section_id -> (label, body) for fallback
        min_body_length: Minimum body length to consider section complete
        
    Returns:
        ParseResult with parsed sections and metadata
    """
    result = ParseResult(raw_length=len(raw_text) if raw_text else 0)
    
    if not raw_text or not raw_text.strip():
        result.source = "FALLBACK"
        result.parse_errors.append("Empty LLM response")
        if fallback_content and expected_sections:
            for section_id in expected_sections:
                if section_id in fallback_content:
                    label, body = fallback_content[section_id]
                    result.sections.append(ParsedSection(
                        section_id=section_id,
                        label=label,
                        body=body,
                        status=SectionStatus.OK
                    ))
                    result.sections_ok += 1
        return result
    
    # Check for truncation indicators
    text = raw_text.strip()
    has_end_marker = bool(END_MARKER_PATTERN.search(text))
    ends_cleanly = text.endswith('---END---') or text.endswith('.')
    
    if not has_end_marker and not ends_cleanly:
        result.truncated = True
        logger.warning(f"[SECTION_PARSER] Response appears truncated (no ---END--- marker, length={len(text)})")
    
    # Find all section markers
    section_matches = list(SECTION_START_PATTERN.finditer(text))
    
    # If no standard markers found, try alternative patterns
    if not section_matches:
        alt_matches = list(ALT_SECTION_PATTERN.finditer(text))
        if alt_matches:
            logger.info(f"[SECTION_PARSER] Using alternative section markers")
            # Convert to standard format conceptually
            for match in alt_matches:
                section_id = match.group(1) or match.group(2) or match.group(3)
                # Try to extract content after the marker
                start_pos = match.end()
                # Find next marker or end
                next_match = None
                for m in alt_matches:
                    if m.start() > start_pos:
                        next_match = m
                        break
                end_pos = next_match.start() if next_match else len(text)
                
                content = text[start_pos:end_pos].strip()
                # Split first line as label, rest as body
                lines = content.split('\n', 1)
                label = lines[0].strip() if lines else section_id.title()
                body = lines[1].strip() if len(lines) > 1 else ""
                
                if body:
                    result.sections.append(ParsedSection(
                        section_id=section_id.lower(),
                        label=label,
                        body=body,
                        status=SectionStatus.OK if len(body) >= min_body_length else SectionStatus.PARTIAL
                    ))
                    if len(body) >= min_body_length:
                        result.sections_ok += 1
                    else:
                        result.sections_partial += 1
    
    # Parse standard format sections
    for i, match in enumerate(section_matches):
        section_id = match.group(1).lower()
        start_pos = match.end()
        
        # Find end of this section (next section marker or end of text)
        if i + 1 < len(section_matches):
            end_pos = section_matches[i + 1].start()
        else:
            # Last section - goes to end or ---END--- marker
            end_match = END_MARKER_PATTERN.search(text, start_pos)
            end_pos = end_match.start() if end_match else len(text)
        
        section_content = text[start_pos:end_pos].strip()
        
        # Parse section content - look for ---BODY--- marker
        body_match = BODY_MARKER_PATTERN.search(section_content)
        
        if body_match:
            # Title is before ---BODY---, body is after
            label = section_content[:body_match.start()].strip()
            body = section_content[body_match.end():].strip()
        else:
            # No ---BODY--- marker - first line is title, rest is body
            lines = section_content.split('\n', 1)
            label = lines[0].strip() if lines else section_id.replace('_', ' ').title()
            body = lines[1].strip() if len(lines) > 1 else ""
        
        # Clean up label
        label = label.strip('*#').strip()
        if not label:
            label = section_id.replace('_', ' ').title()
        
        # Determine section status
        if not body:
            status = SectionStatus.MISSING
            result.sections_missing += 1
        elif len(body) < min_body_length:
            status = SectionStatus.PARTIAL
            result.sections_partial += 1
        else:
            status = SectionStatus.OK
            result.sections_ok += 1
        
        # Check if this is the last section and truncated
        if i == len(section_matches) - 1 and result.truncated and body:
            # Last section may be truncated
            if not body.endswith('.') and not body.endswith('?') and not body.endswith('!'):
                status = SectionStatus.PARTIAL
                if status != SectionStatus.PARTIAL:
                    result.sections_ok -= 1
                    result.sections_partial += 1
        
        result.sections.append(ParsedSection(
            section_id=section_id,
            label=label,
            body=body,
            status=status
        ))
    
    # Handle missing expected sections
    if expected_sections:
        found_ids = {s.section_id for s in result.sections}
        for section_id in expected_sections:
            if section_id not in found_ids:
                result.sections_missing += 1
                # Add fallback content if available
                if fallback_content and section_id in fallback_content:
                    label, body = fallback_content[section_id]
                    result.sections.append(ParsedSection(
                        section_id=section_id,
                        label=label,
                        body=body,
                        status=SectionStatus.OK  # Fallback is complete
                    ))
                    result.sections_ok += 1
                    result.sections_missing -= 1
                    logger.info(f"[SECTION_PARSER] Using fallback for missing section: {section_id}")
    
    # Fill in partial sections with fallback if available
    if fallback_content:
        for section in result.sections:
            if section.status == SectionStatus.PARTIAL and section.section_id in fallback_content:
                label, fallback_body = fallback_content[section.section_id]
                # Append fallback to partial content
                section.body = section.body + "\n\n" + fallback_body
                section.status = SectionStatus.OK
                section.char_count = len(section.body)
                section.word_count = len(section.body.split())
                result.sections_partial -= 1
                result.sections_ok += 1
                logger.info(f"[SECTION_PARSER] Augmented partial section with fallback: {section.section_id}")
    
    # Determine overall source
    if result.sections_ok == 0 and result.sections_partial == 0:
        result.source = "FALLBACK"
    elif result.sections_partial > 0 or result.truncated:
        result.source = "LLM_PARTIAL"
    else:
        result.source = "LLM"
    
    logger.info(f"[SECTION_PARSER] Parsed {len(result.sections)} sections: "
                f"ok={result.sections_ok}, partial={result.sections_partial}, "
                f"missing={result.sections_missing}, source={result.source}")
    
    return result


def generate_section_prompt_format(section_configs: List[Dict]) -> str:
    """
    Generate the prompt instructions for the plain text format.
    
    Args:
        section_configs: List of {id, label, description} dicts
        
    Returns:
        Formatted string with instructions
    """
    sections_list = "\n".join([
        f"- {config['id']}: {config.get('description', config.get('label', ''))}"
        for config in section_configs
    ])
    
    return f"""
RESPONSE FORMAT INSTRUCTIONS:
Return your response as plain text with section markers. Do NOT use JSON.

Use this exact format:

---SECTION:section_id---
Section Title
---BODY---
The full content for this section goes here. Write at least 150 words.
Include multiple paragraphs for depth.

(Repeat for each section)

---END---

REQUIRED SECTIONS:
{sections_list}

IMPORTANT:
- Use the exact section IDs shown above
- Write substantial content (150+ words per section)
- End with ---END--- marker
- Do NOT use JSON, brackets, or code formatting
"""


# ============================================================================
# REGRESSION TEST UTILITIES
# ============================================================================

def test_truncated_parsing():
    """Test that truncated input still produces usable output"""
    
    # Simulate truncated LLM output (cut off mid-section)
    truncated_input = """---SECTION:sun---
Sun: Your Core Orientation
---BODY---
With your Sun in Aries, there's a pioneering quality to how you engage with life. You tend to move toward challenges rather than away from them, and there's often an initiating energy that wants to start things, lead things, or be first at something. This isn't ego in the shallow sense—it's a genuine life force that moves forward.

The shadow can show up as impatience, as charging ahead before reading the room, or as an identity too tied to being strong.

---SECTION:moon---
Moon: Your Emotional Texture
---BODY---
Your Moon in Cancer suggests a deep emotional nature that needs safety, belonging, and nurtur"""  # Truncated!
    
    expected_sections = ["sun", "moon", "ascendant"]
    fallback_content = {
        "ascendant": ("Ascendant: How You Meet the World", "Fallback ascendant content here with enough words to be considered complete and valid for the user experience.")
    }
    
    result = parse_plain_text_sections(
        truncated_input,
        expected_sections=expected_sections,
        fallback_content=fallback_content,
        min_body_length=50
    )
    
    # Assertions
    assert result.source in ("LLM", "LLM_PARTIAL"), f"Expected LLM or LLM_PARTIAL, got {result.source}"
    assert result.truncated == True, "Should detect truncation"
    assert len(result.sections) >= 2, f"Should have at least 2 sections, got {len(result.sections)}"
    
    # Sun section should be complete
    sun_section = next((s for s in result.sections if s.section_id == "sun"), None)
    assert sun_section is not None, "Sun section should exist"
    assert sun_section.status == SectionStatus.OK, f"Sun should be OK, got {sun_section.status}"
    
    # Moon section should be partial (truncated)
    moon_section = next((s for s in result.sections if s.section_id == "moon"), None)
    assert moon_section is not None, "Moon section should exist"
    assert moon_section.status == SectionStatus.PARTIAL, f"Moon should be PARTIAL, got {moon_section.status}"
    
    print("✅ Truncated parsing test PASSED")
    return True


def test_complete_parsing():
    """Test that complete input parses correctly"""
    
    complete_input = """---SECTION:type---
Type: Your Energy Architecture
---BODY---
As a Generator, your energy architecture is built around sustainable life force. This means you have consistent access to sacral energy when you're engaged in work that lights you up. The key is responding to what genuinely excites you rather than initiating from mental decisions alone.

Your strategy is to wait to respond, which doesn't mean being passive. It means letting life bring you opportunities and then noticing your gut response. When something sparks genuine excitement, you have the energy to see it through.

---SECTION:authority---
Authority: Your Clarity Process
---BODY---
With Sacral Authority, your clarity comes through your gut response. This isn't about thinking your way to decisions—it's about feeling the yes or no in your body. The sacral center communicates through sounds and sensations: the "uh-huh" of excitement or the "unh-unh" of disinterest.

Learning to trust this embodied knowing over mental reasoning is often a lifelong practice. Your body knows before your mind does.

---END---"""
    
    result = parse_plain_text_sections(complete_input, expected_sections=["type", "authority"])
    
    assert result.source == "LLM", f"Expected LLM, got {result.source}"
    assert result.truncated == False, "Should not be truncated"
    assert len(result.sections) == 2, f"Should have 2 sections, got {len(result.sections)}"
    assert result.sections_ok == 2, f"Should have 2 OK sections, got {result.sections_ok}"
    
    print("✅ Complete parsing test PASSED")
    return True


def run_parser_tests():
    """Run all parser regression tests"""
    print("\n" + "="*60)
    print("🧪 SECTION PARSER REGRESSION TESTS")
    print("="*60 + "\n")
    
    tests = [
        ("Truncated Parsing", test_truncated_parsing),
        ("Complete Parsing", test_complete_parsing),
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
    run_parser_tests()


# ============================================================================
# ADDITIONAL REGRESSION TESTS FOR TRUNCATION HANDLING
# ============================================================================

def test_severely_truncated_input():
    """Test handling of severely truncated input (mid-word cut)"""
    severely_truncated = """---SECTION:sun---
Sun: Your Core Orientation
---BODY---
With your Sun in Aries, there's a pioneering qua"""  # Cut mid-word
    
    fallback_content = {
        "sun": ("Sun: Your Core Orientation", "Full fallback sun content that is substantial and meets the minimum length requirement for proper display."),
        "moon": ("Moon: Your Emotional Texture", "Full fallback moon content that provides adequate information about the lunar placement."),
    }
    
    result = parse_plain_text_sections(
        severely_truncated,
        expected_sections=["sun", "moon"],
        fallback_content=fallback_content,
        min_body_length=50
    )
    
    # Should get sections even with severe truncation
    assert len(result.sections) >= 1, f"Should have at least 1 section, got {len(result.sections)}"
    assert result.truncated == True, "Should detect truncation"
    
    # Sun should be partial (augmented with fallback)
    sun_section = next((s for s in result.sections if s.section_id == "sun"), None)
    if sun_section:
        assert len(sun_section.body) > 50, "Sun section should have fallback content"
    
    print("✅ Severely truncated input test PASSED")
    return True


def test_empty_response():
    """Test handling of empty/null LLM response"""
    empty_inputs = ["", None, "   ", "\n\n"]
    
    fallback_content = {
        "test": ("Test Section", "Fallback content that should be used when LLM returns nothing."),
    }
    
    for empty_input in empty_inputs:
        result = parse_plain_text_sections(
            empty_input,
            expected_sections=["test"],
            fallback_content=fallback_content
        )
        
        assert result.source == "FALLBACK", f"Empty input should result in FALLBACK source"
        assert len(result.sections) >= 1, "Should have fallback section"
    
    print("✅ Empty response test PASSED")
    return True


def test_partial_with_complete_sections():
    """Test that complete sections are preserved even when response is truncated"""
    partial_with_complete = """---SECTION:first---
First Complete Section
---BODY---
This is a complete first section with enough content to be considered valid and useful. It contains multiple sentences and provides substantial information about the topic at hand. This section should be marked as complete.

---SECTION:second---
Second Complete Section
---BODY---
This is also a complete second section with adequate content. It has enough words to pass the minimum threshold and should be treated as a valid, complete section with proper status.

---SECTION:third---
Third Section - Trun"""  # Truncated mid-title
    
    result = parse_plain_text_sections(
        partial_with_complete,
        expected_sections=["first", "second", "third"],
        min_body_length=30
    )
    
    # First two sections should be OK
    ok_sections = [s for s in result.sections if s.status == SectionStatus.OK]
    assert len(ok_sections) >= 2, f"Should have at least 2 OK sections, got {len(ok_sections)}"
    
    # Source should be LLM_PARTIAL (not full FALLBACK)
    assert result.source in ("LLM", "LLM_PARTIAL"), f"Source should be LLM or LLM_PARTIAL, got {result.source}"
    
    print("✅ Partial with complete sections test PASSED")
    return True


def run_all_parser_tests():
    """Run all parser tests including new truncation tests"""
    print("\n" + "="*60)
    print("🧪 COMPLETE SECTION PARSER REGRESSION TESTS")
    print("="*60 + "\n")
    
    tests = [
        ("Truncated Parsing", test_truncated_parsing),
        ("Complete Parsing", test_complete_parsing),
        ("Severely Truncated Input", test_severely_truncated_input),
        ("Empty Response", test_empty_response),
        ("Partial with Complete Sections", test_partial_with_complete_sections),
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
