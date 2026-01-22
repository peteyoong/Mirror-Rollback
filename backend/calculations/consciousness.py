"""Levels of Consciousness (Hawkins Scale) framework"""
from typing import Dict, List

# Hawkins Scale of Consciousness (simplified for V1)
CONSCIOUSNESS_LEVELS = [
    {'level': 20, 'name': 'Shame', 'emotion': 'Humiliation', 'view': 'Miserable'},
    {'level': 30, 'name': 'Guilt', 'emotion': 'Blame', 'view': 'Evil'},
    {'level': 50, 'name': 'Apathy', 'emotion': 'Despair', 'view': 'Hopeless'},
    {'level': 75, 'name': 'Grief', 'emotion': 'Regret', 'view': 'Tragic'},
    {'level': 100, 'name': 'Fear', 'emotion': 'Anxiety', 'view': 'Frightening'},
    {'level': 125, 'name': 'Desire', 'emotion': 'Craving', 'view': 'Demanding'},
    {'level': 150, 'name': 'Anger', 'emotion': 'Hate', 'view': 'Antagonistic'},
    {'level': 175, 'name': 'Pride', 'emotion': 'Scorn', 'view': 'Inflated'},
    {'level': 200, 'name': 'Courage', 'emotion': 'Affirmation', 'view': 'Feasible'},
    {'level': 250, 'name': 'Neutrality', 'emotion': 'Trust', 'view': 'Satisfactory'},
    {'level': 310, 'name': 'Willingness', 'emotion': 'Optimism', 'view': 'Hopeful'},
    {'level': 350, 'name': 'Acceptance', 'emotion': 'Forgiveness', 'view': 'Harmonious'},
    {'level': 400, 'name': 'Reason', 'emotion': 'Understanding', 'view': 'Meaningful'},
    {'level': 500, 'name': 'Love', 'emotion': 'Reverence', 'view': 'Benign'},
    {'level': 540, 'name': 'Joy', 'emotion': 'Serenity', 'view': 'Complete'},
    {'level': 600, 'name': 'Peace', 'emotion': 'Bliss', 'view': 'Perfect'},
    {'level': 700, 'name': 'Enlightenment', 'emotion': 'Ineffable', 'view': 'Is'}
]

def get_level_info(level_value: int) -> Dict:
    """Get information about a consciousness level"""
    for level in CONSCIOUSNESS_LEVELS:
        if level['level'] == level_value:
            return level
    return None

def get_closest_level(estimated_level: int) -> Dict:
    """Find closest consciousness level to estimated value"""
    closest = min(CONSCIOUSNESS_LEVELS, key=lambda x: abs(x['level'] - estimated_level))
    return closest

def get_level_description(level_name: str) -> str:
    """Get detailed description of consciousness level"""
    descriptions = {
        'Shame': 'Below 20: Perilously close to death, feelings of unworthiness',
        'Guilt': 'Feeling of wrongness, self-blame, emotional paralysis',
        'Apathy': 'State of helplessness, hopelessness, poverty consciousness',
        'Grief': 'Level of sadness, loss, regret, living in the past',
        'Fear': 'Anxiety dominates, world seems threatening and dangerous',
        'Desire': 'Craving and wanting, never satisfied, consumerism',
        'Anger': 'Frustration and resentment, can be motivating but exhausting',
        'Pride': 'Feeling better than others, vulnerable to criticism',
        'Courage': 'First level of true power, willingness to try new things',
        'Neutrality': 'Flexible, non-judgmental, realistic, confident',
        'Willingness': 'Optimistic, helpful, growth-oriented, reliable',
        'Acceptance': 'Forgiveness, harmony, proactive, self-responsible',
        'Reason': 'Intellectual understanding, logic, knowledge-seeking',
        'Love': 'Unconditional love, compassion, intuitive, forgiving',
        'Joy': 'Inner peace, serenity, gratitude, transformational',
        'Peace': 'Bliss, transcendence, non-duality, rare attainment',
        'Enlightenment': 'Pure consciousness, ultimate truth, sages and saints'
    }
    return descriptions.get(level_name, 'Unknown level')

def get_consciousness_framework() -> List[Dict]:
    """Get the complete consciousness framework"""
    return [
        {
            **level,
            'description': get_level_description(level['name'])
        }
        for level in CONSCIOUSNESS_LEVELS
    ]

def analyze_consciousness_indicators(journal_text: str = None) -> Dict:
    """Analyze text for consciousness level indicators
    For V1, this is simplified - full implementation would use NLP
    """
    # Simplified keyword-based analysis for V1
    keywords_mapping = {
        'Shame': ['worthless', 'humiliated', 'ashamed'],
        'Guilt': ['guilty', 'blame', 'wrong'],
        'Apathy': ['hopeless', 'pointless', 'numb'],
        'Grief': ['sad', 'loss', 'regret'],
        'Fear': ['afraid', 'anxious', 'worried'],
        'Desire': ['want', 'need', 'crave'],
        'Anger': ['angry', 'frustrated', 'hate'],
        'Pride': ['better', 'superior', 'deserve'],
        'Courage': ['try', 'willing', 'face'],
        'Neutrality': ['okay', 'fine', 'acceptable'],
        'Willingness': ['help', 'grow', 'learn'],
        'Acceptance': ['accept', 'forgive', 'allow'],
        'Reason': ['understand', 'analyze', 'think'],
        'Love': ['love', 'compassion', 'care'],
        'Joy': ['joy', 'grateful', 'blessed'],
        'Peace': ['peace', 'calm', 'serene']
    }
    
    if not journal_text:
        return {
            'estimated_level': 'Courage',
            'note': 'Default baseline - refine with journal entries'
        }
    
    # Simple keyword matching (V1)
    text_lower = journal_text.lower()
    matches = {}
    
    for level_name, keywords in keywords_mapping.items():
        count = sum(text_lower.count(keyword) for keyword in keywords)
        if count > 0:
            matches[level_name] = count
    
    if matches:
        dominant_level = max(matches, key=matches.get)
        return {
            'estimated_level': dominant_level,
            'indicators': matches,
            'note': 'Based on language patterns in journal'
        }
    
    return {
        'estimated_level': 'Courage',
        'note': 'Neutral baseline'
    }
