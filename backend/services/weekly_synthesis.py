"""
Weekly Pattern Synthesis Service

Aggregates the last 7 days of Pattern Graph outputs and produces 
a deterministic weekly summary following the Mirror philosophy:
- Reflect patterns, not predictions
- Subtle language
- Astrology hidden as timing context
- Deterministic aggregation → optional LLM narrative layer (future)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

# Pattern categories (imported from pattern_graph for consistency)
PATTERN_DOMAINS = [
    "energy_vitality",
    "emotional_landscape", 
    "identity_direction",
    "mind_meaning",
    "expression_action",
    "relationships_boundaries",
    "growth_transformation"
]

DOMAIN_NAMES = {
    "energy_vitality": "Energy & Vitality",
    "emotional_landscape": "Emotional Landscape",
    "identity_direction": "Identity & Direction",
    "mind_meaning": "Mind & Meaning",
    "expression_action": "Expression & Action",
    "relationships_boundaries": "Relationships & Boundaries",
    "growth_transformation": "Growth & Transformation"
}

# Evidence category mappings (translate raw sources to readable categories)
EVIDENCE_CATEGORIES = {
    "journal": "Repeated reflection signals",
    "mirror_chat": "Mirror chat language patterns",
    "gene_keys": "Structural lens context",
    "human_design": "Structural lens context",
    "enneagram": "Structural lens context",
    "astrology_transit": "Current timing emphasis"
}

# Reflection prompts for the weekly synthesis
REFLECTION_PROMPTS = [
    "What kept repeating, even when it changed form?",
    "What seemed to want your attention this week?",
    "What stayed with you across the days?",
    "What thread connected these patterns?",
    "What might this week have been preparing you to see?",
    "What asked to be noticed, again and again?",
    "Where did your attention keep returning?"
]


def calculate_weekly_domain_stats(
    daily_snapshots: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate weekly statistics for each domain from daily snapshots.
    
    Args:
        daily_snapshots: List of daily pattern graph outputs (7 days max)
        
    Returns:
        Dict mapping domain_id to weekly statistics
    """
    domain_stats: Dict[str, Dict[str, Any]] = {}
    
    for domain_id in PATTERN_DOMAINS:
        daily_scores = []
        days_present = 0
        all_sources = set()
        has_timing_amplification = False
        
        for i, snapshot in enumerate(daily_snapshots):
            categories = snapshot.get("categories", [])
            domain_data = next(
                (c for c in categories if c.get("category_id") == domain_id),
                None
            )
            
            if domain_data:
                score = domain_data.get("pattern_score", 0)
                daily_scores.append(score)
                
                if score > 0.5:
                    days_present += 1
                
                # Collect sources
                sources = domain_data.get("matched_sources", [])
                all_sources.update(sources)
                
                # Check for timing amplification
                if domain_data.get("has_transit_emphasis"):
                    has_timing_amplification = True
            else:
                daily_scores.append(0)
        
        # Pad to 7 days if needed
        while len(daily_scores) < 7:
            daily_scores.append(0)
        
        # Calculate statistics
        weekly_score = sum(daily_scores)
        
        # Recency-weighted score (later days count more)
        recency_weights = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1]
        recency_weighted_score = sum(
            score * weight 
            for score, weight in zip(daily_scores, recency_weights[:len(daily_scores)])
        )
        
        # Trend detection
        if len(daily_scores) >= 4:
            early_avg = sum(daily_scores[:2]) / 2
            late_avg = sum(daily_scores[-2:]) / 2
            
            # Check for emerging pattern
            early_week_avg = sum(daily_scores[:3]) / 3 if len(daily_scores) >= 3 else 0
            late_week_avg = sum(daily_scores[-3:]) / 3 if len(daily_scores) >= 3 else 0
            
            if early_week_avg < 0.5 and late_week_avg > 1:
                trend = "emerging"
            elif late_avg > early_avg * 1.3:  # 30% increase
                trend = "rising"
            elif late_avg < early_avg * 0.7:  # 30% decrease
                trend = "softening"
            else:
                trend = "steady"
        else:
            trend = "steady"
        
        # Build evidence summary from sources
        evidence_summary = []
        seen_evidence = set()
        for source in all_sources:
            evidence_cat = EVIDENCE_CATEGORIES.get(source)
            if evidence_cat and evidence_cat not in seen_evidence:
                evidence_summary.append(evidence_cat)
                seen_evidence.add(evidence_cat)
        
        domain_stats[domain_id] = {
            "domain_id": domain_id,
            "domain_name": DOMAIN_NAMES.get(domain_id, domain_id),
            "weekly_score": round(weekly_score, 2),
            "days_present": days_present,
            "recency_weighted_score": round(recency_weighted_score, 2),
            "trend": trend,
            "timing_amplified": has_timing_amplification,
            "evidence_summary": evidence_summary,
            "daily_scores": daily_scores
        }
    
    return domain_stats


def rank_domains(domain_stats: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank domains using the weekly ranking formula.
    
    Formula:
    weekly_rank_score = weekly_score * 0.5 + days_present * 0.3 + recency_weighted_score * 0.2
    
    Returns:
        Sorted list of domain stats, highest rank first
    """
    ranked = []
    
    for domain_id, stats in domain_stats.items():
        rank_score = (
            stats["weekly_score"] * 0.5 +
            stats["days_present"] * 0.3 +
            stats["recency_weighted_score"] * 0.2
        )
        
        ranked.append({
            **stats,
            "rank_score": round(rank_score, 2)
        })
    
    # Sort by rank score descending
    ranked.sort(key=lambda x: x["rank_score"], reverse=True)
    
    return ranked


def detect_cross_week_shift(
    daily_snapshots: List[Dict[str, Any]]
) -> Optional[str]:
    """
    Detect if the dominant domain changed mid-week.
    
    Returns:
        A shift description string, or None if no significant shift
    """
    if len(daily_snapshots) < 5:
        return None
    
    def get_top_domain(snapshots: List[Dict]) -> Optional[str]:
        """Get the top domain from a set of snapshots."""
        domain_scores: Dict[str, float] = defaultdict(float)
        
        for snapshot in snapshots:
            categories = snapshot.get("categories", [])
            for cat in categories:
                domain_id = cat.get("category_id")
                score = cat.get("pattern_score", 0)
                if domain_id:
                    domain_scores[domain_id] += score
        
        if not domain_scores:
            return None
        
        return max(domain_scores, key=domain_scores.get)
    
    # Split week into early (first 3 days) and late (last 3 days)
    early_top = get_top_domain(daily_snapshots[:3])
    late_top = get_top_domain(daily_snapshots[-3:])
    
    if early_top and late_top and early_top != late_top:
        early_name = DOMAIN_NAMES.get(early_top, early_top)
        late_name = DOMAIN_NAMES.get(late_top, late_top)
        
        # Generate subtle shift description
        shift_templates = [
            f"What began as {early_name.lower()} themes may have increasingly shown up as {late_name.lower()}.",
            f"A pattern that started around {early_name.lower()} appears to have shifted toward {late_name.lower()}.",
            f"The week may have moved from {early_name.lower()} emphasis toward {late_name.lower()}."
        ]
        
        # Use a deterministic selection based on domain names
        template_idx = (ord(early_name[0]) + ord(late_name[0])) % len(shift_templates)
        return shift_templates[template_idx]
    
    return None


def generate_narrative_paragraph(
    top_domains: List[Dict[str, Any]],
    has_timing: bool
) -> str:
    """
    Generate a simple deterministic narrative paragraph from the weekly data.
    
    This is the v0.1 implementation - can be replaced with LLM in future.
    """
    if not top_domains:
        return "This week's patterns are still emerging. Continue reflecting to see what surfaces."
    
    # Get top domain names
    domain_names = [d["domain_name"].lower() for d in top_domains[:3]]
    
    # Build the main sentence
    if len(domain_names) == 1:
        domains_text = domain_names[0]
    elif len(domain_names) == 2:
        domains_text = f"{domain_names[0]} and {domain_names[1]}"
    else:
        domains_text = f"{domain_names[0]}, {domain_names[1]}, and {domain_names[2]}"
    
    # Check for rising trends
    rising_count = sum(1 for d in top_domains[:3] if d.get("trend") == "rising")
    emerging_count = sum(1 for d in top_domains[:3] if d.get("trend") == "emerging")
    
    # Build narrative parts
    parts = []
    
    # Main emphasis
    parts.append(f"This week appears to have carried a stronger emphasis around {domains_text}.")
    
    # Trend observation
    if rising_count > 0 or emerging_count > 0:
        parts.append("Some signals suggest activation rather than resolution, as if certain themes are still unfolding.")
    else:
        parts.append("These patterns seem to have held steady across the days.")
    
    # Timing layer (subtle)
    if has_timing:
        parts.append("A subtle timing influence may also be amplifying patterns that were already present.")
    
    return " ".join(parts)


def select_reflection_prompt(week_start: str) -> str:
    """
    Deterministically select a reflection prompt based on the week.
    """
    # Use week_start string to select prompt consistently
    hash_val = sum(ord(c) for c in week_start)
    prompt_idx = hash_val % len(REFLECTION_PROMPTS)
    return REFLECTION_PROMPTS[prompt_idx]


def generate_weekly_pattern_summary(
    daily_snapshots: List[Dict[str, Any]],
    week_start: Optional[datetime] = None,
    week_end: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Main function to generate the weekly pattern summary.
    
    Args:
        daily_snapshots: List of daily pattern graph outputs (up to 7 days)
        week_start: Start date of the week (defaults to 7 days ago)
        week_end: End date of the week (defaults to today)
        
    Returns:
        Weekly summary JSON contract
    """
    # Set default dates
    if week_end is None:
        week_end = datetime.now()
    if week_start is None:
        week_start = week_end - timedelta(days=6)
    
    week_start_str = week_start.strftime("%Y-%m-%d")
    week_end_str = week_end.strftime("%Y-%m-%d")
    
    # Handle empty snapshots
    if not daily_snapshots:
        return {
            "week_start": week_start_str,
            "week_end": week_end_str,
            "top_domains": [],
            "all_domains": [],
            "cross_week_shift": None,
            "narrative": "Not enough data to generate a weekly synthesis yet. Continue reflecting to see patterns emerge.",
            "reflection_prompt": select_reflection_prompt(week_start_str),
            "evidence_sources": [],
            "has_timing_influence": False
        }
    
    # Step 1: Calculate domain statistics
    domain_stats = calculate_weekly_domain_stats(daily_snapshots)
    
    # Step 2: Rank domains
    ranked_domains = rank_domains(domain_stats)
    
    # Step 3: Get top 3 domains (only those with meaningful scores)
    top_domains = [
        d for d in ranked_domains[:3]
        if d["weekly_score"] > 0.5  # Minimum threshold
    ]
    
    # Step 4: Detect cross-week shift
    cross_week_shift = detect_cross_week_shift(daily_snapshots)
    
    # Step 5: Check for timing influence
    has_timing = any(d.get("timing_amplified") for d in top_domains)
    
    # Step 6: Generate narrative
    narrative = generate_narrative_paragraph(top_domains, has_timing)
    
    # Step 7: Collect all evidence sources
    all_evidence = set()
    for d in top_domains:
        all_evidence.update(d.get("evidence_summary", []))
    
    # Step 8: Select reflection prompt
    reflection_prompt = select_reflection_prompt(week_start_str)
    
    # Build the response
    return {
        "week_start": week_start_str,
        "week_end": week_end_str,
        "top_domains": [
            {
                "domain": d["domain_name"],
                "domain_id": d["domain_id"],
                "trend": d["trend"],
                "weekly_score": d["weekly_score"],
                "days_present": d["days_present"],
                "timing_amplified": d["timing_amplified"],
                "evidence_summary": d["evidence_summary"]
            }
            for d in top_domains
        ],
        "all_domains": [
            {
                "domain": d["domain_name"],
                "domain_id": d["domain_id"],
                "trend": d["trend"],
                "weekly_score": d["weekly_score"],
                "days_present": d["days_present"]
            }
            for d in ranked_domains
        ],
        "cross_week_shift": cross_week_shift,
        "narrative": narrative,
        "reflection_prompt": reflection_prompt,
        "evidence_sources": sorted(list(all_evidence)),
        "has_timing_influence": has_timing
    }


# =============================================================================
# FUTURE HOOK: LLM Narrative Layer
# =============================================================================

async def weekly_llm_narrative(summary_json: Dict[str, Any]) -> Optional[str]:
    """
    Future: Generate a richer narrative using LLM from the deterministic summary.
    
    This is a placeholder for v0.2+
    
    Args:
        summary_json: The deterministic weekly summary from generate_weekly_pattern_summary()
        
    Returns:
        LLM-generated narrative string, or None
    """
    # NOT IMPLEMENTED YET - placeholder for future
    # Will use emergent integrations library when ready
    logger.debug("[WeeklySynthesis] LLM narrative not yet implemented")
    return None
