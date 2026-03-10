"""Gene Keys Pattern Matcher for Mirror Chat

Lightweight deterministic matching between user messages and Gene Keys shadow/gift keywords.
Used to provide subtle context awareness in Mirror Chat responses.

Philosophy:
- This is a support layer, not a diagnostic tool
- Matches should inform reflection, not explain the user
- "Mirror not guru" - always gentle and non-deterministic
"""

import re
import logging
from typing import Optional, List, Dict, Any, TypedDict

logger = logging.getLogger(__name__)


class GeneKeysMatch(TypedDict):
    """Result of Gene Keys pattern matching."""
    sphere_name: str
    sequence: str
    gene_key: int
    shadow: str
    gift: str
    siddhi: str
    matched_keywords: List[str]
    match_type: str  # "shadow" or "gift"
    confidence: str  # "weak", "moderate", "strong"


class GeneKeysMatchResult(TypedDict):
    """Full matching result for chat context."""
    has_match: bool
    primary_match: Optional[GeneKeysMatch]
    secondary_match: Optional[GeneKeysMatch]
    debug_info: Dict[str, Any]


def normalize_text(text: str) -> str:
    """Normalize text for keyword matching.
    
    Converts to lowercase, removes punctuation, extra whitespace.
    """
    # Lowercase
    text = text.lower()
    # Remove punctuation except hyphens (for compound words)
    text = re.sub(r'[^\w\s\-]', ' ', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def tokenize(text: str) -> set:
    """Split normalized text into word tokens."""
    return set(text.split())


def get_word_stems(tokens: set) -> set:
    """Get simple word stems for better matching.
    
    Basic stemming: removes common suffixes like -ing, -ed, -ness, -tion.
    Not a full stemmer, just enough to catch variations.
    """
    stems = set()
    for token in tokens:
        stems.add(token)
        # Add stem variations
        if token.endswith('ing') and len(token) > 5:
            stems.add(token[:-3])  # remove -ing
            stems.add(token[:-3] + 'e')  # restore trailing e (e.g., hoping -> hope)
        if token.endswith('ed') and len(token) > 4:
            stems.add(token[:-2])  # remove -ed
            stems.add(token[:-1])  # remove just -d
        if token.endswith('ness') and len(token) > 6:
            stems.add(token[:-4])  # remove -ness
        if token.endswith('tion') and len(token) > 6:
            stems.add(token[:-4])  # remove -tion
        if token.endswith('ly') and len(token) > 4:
            stems.add(token[:-2])  # remove -ly
        if token.endswith('ful') and len(token) > 5:
            stems.add(token[:-3])  # remove -ful
        if token.endswith('less') and len(token) > 6:
            stems.add(token[:-4])  # remove -less
    return stems


def match_keywords_to_message(
    message_tokens: set,
    keywords: List[str],
    require_min_matches: int = 1
) -> tuple[List[str], int]:
    """Match keywords against message tokens.
    
    Returns:
        Tuple of (matched_keywords, match_score)
    """
    matched = []
    score = 0
    
    for keyword in keywords:
        # Normalize and tokenize the keyword (keywords can be phrases)
        kw_normalized = normalize_text(keyword)
        kw_tokens = tokenize(kw_normalized)
        kw_stems = get_word_stems(kw_tokens)
        
        # Check if any keyword token/stem matches message
        for kw_token in kw_stems:
            if kw_token in message_tokens:
                matched.append(keyword)
                # Longer keywords are more significant
                score += len(kw_token)
                break
    
    if len(matched) >= require_min_matches:
        return matched, score
    return [], 0


def match_gene_keys_to_message(
    user_message: str,
    all_spheres: List[Dict[str, Any]],
    min_keyword_matches: int = 1,
    max_results: int = 2
) -> GeneKeysMatchResult:
    """Match user message against Gene Keys shadow/gift keywords.
    
    Args:
        user_message: The user's chat message
        all_spheres: List of sphere data from Gene Keys profile
        min_keyword_matches: Minimum keyword matches to consider valid
        max_results: Maximum number of sphere matches to return
    
    Returns:
        GeneKeysMatchResult with primary and optional secondary match
    """
    # Normalize and tokenize user message
    normalized_msg = normalize_text(user_message)
    msg_tokens = tokenize(normalized_msg)
    msg_stems = get_word_stems(msg_tokens)
    
    logger.debug(f"[GeneKeysMatcher] Message tokens: {msg_tokens}")
    logger.debug(f"[GeneKeysMatcher] Message stems: {msg_stems}")
    
    # Score each sphere
    sphere_scores: List[tuple[int, str, GeneKeysMatch]] = []
    
    for sphere in all_spheres:
        shadow_keywords = sphere.get('shadow_keywords', [])
        gift_keywords = sphere.get('gift_keywords', [])
        
        # Match shadow keywords
        shadow_matched, shadow_score = match_keywords_to_message(
            msg_stems, shadow_keywords, min_keyword_matches
        )
        
        # Match gift keywords
        gift_matched, gift_score = match_keywords_to_message(
            msg_stems, gift_keywords, min_keyword_matches
        )
        
        # Determine which type matched better
        if shadow_score > gift_score and shadow_matched:
            match_type = "shadow"
            matched_keywords = shadow_matched
            score = shadow_score
        elif gift_score > 0 and gift_matched:
            match_type = "gift"
            matched_keywords = gift_matched
            score = gift_score
        elif shadow_matched:
            match_type = "shadow"
            matched_keywords = shadow_matched
            score = shadow_score
        else:
            continue  # No match for this sphere
        
        # Determine confidence level
        if score >= 15 or len(matched_keywords) >= 3:
            confidence = "strong"
        elif score >= 8 or len(matched_keywords) >= 2:
            confidence = "moderate"
        else:
            confidence = "weak"
        
        match_data: GeneKeysMatch = {
            "sphere_name": sphere.get('sphere_name', 'Unknown'),
            "sequence": sphere.get('sequence', 'Unknown'),
            "gene_key": sphere.get('gene_key', 0),
            "shadow": sphere.get('shadow', ''),
            "gift": sphere.get('gift', ''),
            "siddhi": sphere.get('siddhi', ''),
            "matched_keywords": matched_keywords,
            "match_type": match_type,
            "confidence": confidence
        }
        
        sphere_scores.append((score, match_type, match_data))
    
    # Sort by score descending
    sphere_scores.sort(key=lambda x: x[0], reverse=True)
    
    # Build result
    primary_match = None
    secondary_match = None
    
    if sphere_scores:
        primary_match = sphere_scores[0][2]
        
        # Only include secondary if it's reasonably strong and different sphere
        if len(sphere_scores) > 1:
            secondary = sphere_scores[1]
            if secondary[0] >= 5 and secondary[2]['sphere_name'] != primary_match['sphere_name']:
                secondary_match = secondary[2]
    
    debug_info = {
        "message_tokens_count": len(msg_tokens),
        "spheres_checked": len(all_spheres),
        "matches_found": len(sphere_scores),
        "top_scores": [(s[0], s[2]['sphere_name'], s[1]) for s in sphere_scores[:3]]
    }
    
    result: GeneKeysMatchResult = {
        "has_match": primary_match is not None and primary_match.get('confidence') != 'weak',
        "primary_match": primary_match,
        "secondary_match": secondary_match,
        "debug_info": debug_info
    }
    
    logger.info(f"[GeneKeysMatcher] Match result: has_match={result['has_match']}, "
                f"primary={primary_match['sphere_name'] if primary_match else 'None'}, "
                f"type={primary_match['match_type'] if primary_match else 'None'}, "
                f"confidence={primary_match['confidence'] if primary_match else 'None'}")
    
    return result


def build_gene_keys_chat_context(match_result: GeneKeysMatchResult) -> str:
    """Build a subtle context insert for the chat system prompt.
    
    This provides the LLM with Gene Keys awareness without forcing it to mention.
    The LLM should use this ONLY if naturally relevant to the conversation.
    
    Returns:
        Context string to append to system prompt, or empty string if no match
    """
    if not match_result['has_match'] or not match_result['primary_match']:
        return ""
    
    match = match_result['primary_match']
    
    # Build subtle context based on match type
    if match['match_type'] == 'shadow':
        context = f"""
--- GENE KEYS PATTERN AWARENESS (INTERNAL ONLY) ---
The user's language may echo a pattern from their Gene Keys profile.

Sphere: {match['sphere_name']} ({match['sequence']} Sequence)
Gene Key: {match['gene_key']}
Possible pattern: Movement from {match['shadow']} (shadow) toward {match['gift']} (gift)
Signal detected: Keywords like "{', '.join(match['matched_keywords'][:3])}" suggest shadow expression

IF AND ONLY IF this feels naturally relevant to what the user is exploring:
- You may gently reflect: "What you're describing echoes a pattern that also appears in your Gene Keys..."
- You may name the tension: "There may be a familiar tension here between {match['shadow']} and {match['gift']}..."
- You may offer movement: "One of your spheres points to a possible movement from {match['shadow']} toward {match['gift']}..."

DO NOT:
- Force the connection if it doesn't fit
- Sound authoritative ("Your Gene Key means...")
- Use framework jargon heavily
- Mention more than one sphere unless truly necessary
- Explain the user - just reflect

If the match doesn't feel relevant, ignore this context entirely.
"""
    else:  # gift match
        context = f"""
--- GENE KEYS PATTERN AWARENESS (INTERNAL ONLY) ---
The user's language may echo a pattern from their Gene Keys profile.

Sphere: {match['sphere_name']} ({match['sequence']} Sequence)
Gene Key: {match['gene_key']}
Possible pattern: The gift of {match['gift']} (with shadow side of {match['shadow']})
Signal detected: Keywords like "{', '.join(match['matched_keywords'][:3])}" suggest gift expression

IF AND ONLY IF this feels naturally relevant:
- You may gently affirm: "What you're noticing may connect to a natural capacity you carry..."
- You may reflect depth: "There's something in what you're describing that echoes one of your Gene Keys gifts..."
- You may name the gift: "The quality of {match['gift']} seems to be present in what you're exploring..."

DO NOT:
- Force the connection if it doesn't fit
- Sound authoritative or predictive
- Over-celebrate or inflate
- Mention more than one sphere unless truly necessary
- Explain the user - just reflect

If the match doesn't feel relevant, ignore this context entirely.
"""
    
    return context


def log_gene_keys_match_debug(
    user_id: str,
    message_preview: str,
    match_result: GeneKeysMatchResult
) -> None:
    """Log debug information about Gene Keys matching for development inspection.
    
    This is dev-only logging to help tune the matching algorithm.
    """
    msg_preview = message_preview[:50] + "..." if len(message_preview) > 50 else message_preview
    
    if match_result['has_match']:
        primary = match_result['primary_match']
        logger.info(
            f"[GK_MATCH_DEBUG] user={user_id} | "
            f"msg=\"{msg_preview}\" | "
            f"sphere={primary['sphere_name']} | "
            f"type={primary['match_type']} | "
            f"confidence={primary['confidence']} | "
            f"keywords={primary['matched_keywords']}"
        )
    else:
        logger.info(
            f"[GK_MATCH_DEBUG] user={user_id} | "
            f"msg=\"{msg_preview}\" | "
            f"NO_MATCH | "
            f"spheres_checked={match_result['debug_info']['spheres_checked']}"
        )
