"""
Enneagram v2 Assessment Simulation for 7w8 Profile
Simulates honest, consistent responses from a true 7w8 perspective
"""
import asyncio
import json
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import math

# MongoDB connection
MONGO_URL = 'mongodb://localhost:27017'
DB_NAME = 'test_database'

# ============================================
# V2 QUESTIONS (as implemented)
# ============================================

CORE_MOTIVATION_QUESTIONS = {
    # Type 1 - Perfectionist
    'Q01': {'type': 1, 'text': 'I experience a persistent inner sense that things could and should be better than they are.'},
    'Q02': {'type': 1, 'text': 'I feel uneasy when I compromise my standards, even in small ways.'},
    'Q03': {'type': 1, 'text': 'There is an internal pressure to correct mistakes — especially my own.'},
    
    # Type 2 - Helper
    'Q04': {'type': 2, 'text': 'I naturally focus on what others need, often before noticing my own.'},
    'Q05': {'type': 2, 'text': 'Feeling appreciated or valued by others strongly affects my sense of worth.'},
    'Q06': {'type': 2, 'text': 'I find it difficult to disengage when someone depends on me.'},
    
    # Type 3 - Achiever
    'Q07': {'type': 3, 'text': 'I instinctively adapt myself to what will be valued or rewarded in a given environment.'},
    'Q08': {'type': 3, 'text': 'Achievement and visible progress strongly influence how I evaluate myself.'},
    'Q09': {'type': 3, 'text': 'I feel driven to be effective, capable, and ahead of expectations.'},
    
    # Type 4 - Individualist (v2 - behavioral tradeoffs)
    'Q10': {'type': 4, 'text': 'I would rather feel deeply understood by a few than broadly liked by many.'},
    'Q11': {'type': 4, 'text': 'I have withdrawn from opportunities because they felt ordinary or inauthentic.'},
    'Q12': {'type': 4, 'text': 'I sometimes envy what others have while also feeling my experience is fundamentally different from theirs.'},
    
    # Type 5 - Investigator (v2 - behavioral tradeoffs)
    'Q13': {'type': 5, 'text': 'I routinely decline social invitations to protect time for thinking or projects.'},
    'Q14': {'type': 5, 'text': 'I delay taking action until I have gathered enough information, even when others want me to move faster.'},
    'Q15': {'type': 5, 'text': 'I feel drained after extended interaction and need significant alone time to recover.'},
    
    # Type 6 - Loyalist
    'Q16': {'type': 6, 'text': 'I naturally anticipate potential problems and think through what could go wrong.'},
    'Q17': {'type': 6, 'text': 'I seek certainty or reassurance before fully committing to decisions.'},
    'Q18': {'type': 6, 'text': 'Trust and reliability are central concerns in how I navigate relationships and systems.'},
    
    # Type 7 - Enthusiast (v2 - pursuit framing)
    'Q19': {'type': 7, 'text': 'I am energised by new possibilities and quickly move toward the next interesting thing.'},
    'Q20': {'type': 7, 'text': 'I prefer to keep multiple projects or plans active so I can switch between them freely.'},
    'Q21': {'type': 7, 'text': 'I naturally focus on what could go right and find ways to make situations more enjoyable.'},
    
    # Type 8 - Challenger
    'Q22': {'type': 8, 'text': 'I feel a strong need to stay in control of my life and circumstances.'},
    'Q23': {'type': 8, 'text': 'I resist being constrained, dominated, or told what to do.'},
    'Q24': {'type': 8, 'text': 'I respect strength and directness more than sensitivity or hesitation.'},
    
    # Type 9 - Peacemaker
    'Q25': {'type': 9, 'text': 'I tend to minimise conflict and smooth things over to maintain harmony.'},
    'Q26': {'type': 9, 'text': 'I can lose touch with my own priorities by accommodating others.'},
    'Q27': {'type': 9, 'text': 'I feel most comfortable when there is stability and little emotional tension.'},
}

DISAMBIGUATION_QUESTIONS = {
    'FC01': {'A': 7, 'B': 3, 'textA': 'I pursue many experiences because the world is full of exciting possibilities.', 'textB': 'I pursue goals strategically because success opens doors and earns respect.'},
    'FC02': {'A': 7, 'B': 6, 'textA': 'I generate enthusiasm and momentum to expand what is possible.', 'textB': 'I think carefully and prepare so I am ready for whatever comes.'},
    'FC03': {'A': 7, 'B': 8, 'textA': 'I move quickly toward new opportunities and enjoy the variety.', 'textB': 'I take charge directly and make things happen through force of will.'},
    'FC04': {'A': 5, 'B': 1, 'textA': 'I withdraw to preserve energy and understanding.', 'textB': 'I tighten control to correct what feels wrong.'},
    'FC05': {'A': 3, 'B': 8, 'textA': 'I focus on winning approval through performance.', 'textB': 'I focus on asserting power and independence.'},
    'FC06': {'A': 2, 'B': 9, 'textA': 'I stay connected by being useful and supportive.', 'textB': 'I stay connected by maintaining harmony and avoiding friction.'},
    'FC07': {'A': 8, 'B': 6, 'textA': 'I dislike being limited by rules and prefer to follow my own instincts.', 'textB': 'I appreciate clear guidelines and feel uneasy when expectations are vague.'},
    'FC08': {'A': 7, 'B': 3, 'textA': 'I am more motivated by the excitement of starting things than finishing them.', 'textB': 'I am more motivated by completing things and seeing measurable results.'},
    'FC09': {'A': 8, 'B': 6, 'textA': 'When challenged, I push back and assert my position directly.', 'textB': 'When challenged, I consider multiple angles before responding.'},
}

# ============================================
# 7w8 RESPONSE SIMULATION
# ============================================

def get_7w8_likert_responses():
    """
    Simulate honest, consistent Likert responses from a true 7w8 profile.
    Scale: 1=Strongly Disagree, 2=Disagree, 3=Neutral, 4=Agree, 5=Strongly Agree
    """
    responses = {
        # Type 1 - Perfectionist (7w8 is spontaneous, not perfectionistic)
        'Q01': 2,  # Disagree - 7s don't dwell on "should be better"
        'Q02': 2,  # Disagree - 7s are flexible with standards
        'Q03': 2,  # Disagree - 7s move on quickly, don't fixate on mistakes
        
        # Type 2 - Helper (7w8 is self-focused, not other-focused)
        'Q04': 2,  # Disagree - 7s focus on their own interests first
        'Q05': 2,  # Disagree - 7s derive worth from experiences, not approval
        'Q06': 2,  # Disagree - 7s avoid feeling obligated
        
        # Type 3 - Achiever (7w8 has some overlap but different motivation)
        'Q07': 3,  # Neutral - 7s adapt for opportunities, not just rewards
        'Q08': 3,  # Neutral - 7s care about achievement but not obsessively
        'Q09': 4,  # Agree - 7w8s are driven to be capable
        
        # Type 4 - Individualist (v2: now behavioral, 7w8 won't relate)
        'Q10': 2,  # Disagree - 7s prefer being liked by many, not just few
        'Q11': 1,  # Strongly Disagree - 7s don't withdraw from opportunities
        'Q12': 2,  # Disagree - 7s don't dwell in envy, they pursue what they want
        
        # Type 5 - Investigator (v2: now behavioral, 7w8 won't relate)
        'Q13': 2,  # Disagree - 7s love social interaction
        'Q14': 2,  # Disagree - 7s act quickly, don't over-research
        'Q15': 1,  # Strongly Disagree - 7s are energized by interaction
        
        # Type 6 - Loyalist (7w8 is confident, not anxious)
        'Q16': 2,  # Disagree - 7s focus on positives, not problems
        'Q17': 2,  # Disagree - 7s are decisive, don't need reassurance
        'Q18': 3,  # Neutral - trust matters but 7s are optimistic about people
        
        # Type 7 - Enthusiast (v2: now pursuit-framed, 7w8 will strongly relate)
        'Q19': 5,  # Strongly Agree - core 7 trait
        'Q20': 5,  # Strongly Agree - core 7 trait
        'Q21': 5,  # Strongly Agree - core 7 trait
        
        # Type 8 - Challenger (7w8 has strong 8 wing)
        'Q22': 4,  # Agree - 8 wing shows here
        'Q23': 5,  # Strongly Agree - 8 wing, resists constraints
        'Q24': 4,  # Agree - 8 wing values directness
        
        # Type 9 - Peacemaker (7w8 is assertive, not conflict-avoidant)
        'Q25': 2,  # Disagree - 7w8 engages rather than smooths over
        'Q26': 2,  # Disagree - 7s know their priorities
        'Q27': 2,  # Disagree - 7s are comfortable with change
    }
    return responses

def get_7w8_forced_choice_responses():
    """
    Simulate honest forced-choice responses from a true 7w8 profile.
    """
    responses = {
        'FC01': 'A',  # 7 - pursue experiences for possibilities (not strategic achievement)
        'FC02': 'A',  # 7 - generate enthusiasm and momentum (not careful preparation)
        'FC03': 'A',  # 7 - move toward opportunities (though 7w8 also has 8 energy, variety is key)
        'FC04': 'B',  # 1 - 7w8 doesn't withdraw, would rather correct/engage
        'FC05': 'B',  # 8 - asserting power and independence (8 wing)
        'FC06': 'A',  # 2 - 7s stay connected by being useful (not avoiding friction)
        'FC07': 'A',  # 8 - dislike rules, follow instincts (8 wing)
        'FC08': 'A',  # 7 - excited by starting, not finishing
        'FC09': 'A',  # 8 - push back directly (8 wing)
    }
    return responses

# ============================================
# V2 SCORING ALGORITHM
# ============================================

def compute_v2_scoring(likert_responses, fc_responses):
    """
    Compute Enneagram v2 scoring with:
    - FC multiplier = 1.0 (not 1.5)
    - New confidence tier rules
    - Non-collapsing wing access
    """
    # Step 1: Compute mean Likert scores per type
    type_scores = {t: [] for t in range(1, 10)}
    for qid, value in likert_responses.items():
        q_type = CORE_MOTIVATION_QUESTIONS[qid]['type']
        type_scores[q_type].append(value)
    
    mean_likert = {}
    for t in range(1, 10):
        scores = type_scores[t]
        mean_likert[str(t)] = round(sum(scores) / len(scores), 2) if scores else 0
    
    # Step 2: Count forced-choice hits
    forced_hits = {str(t): 0 for t in range(1, 10)}
    for qid, choice in fc_responses.items():
        selected_type = DISAMBIGUATION_QUESTIONS[qid][choice]
        forced_hits[str(selected_type)] += 1
    
    # Step 3: Compute raw scores (FC multiplier = 1.0)
    FC_MULTIPLIER = 1.0
    raw_scores = {}
    for t in range(1, 10):
        raw_scores[str(t)] = round(mean_likert[str(t)] + (FC_MULTIPLIER * forced_hits[str(t)]), 2)
    
    # Step 4: Z-score normalization
    raw_values = list(raw_scores.values())
    mean = sum(raw_values) / len(raw_values)
    variance = sum((v - mean) ** 2 for v in raw_values) / len(raw_values)
    stddev = math.sqrt(variance) if variance > 0 else 1
    
    z_scores = {}
    for t in range(1, 10):
        z_scores[str(t)] = round((raw_scores[str(t)] - mean) / stddev, 4)
    
    # Step 5: Softmax to probabilities
    exp_values = {str(t): math.exp(z_scores[str(t)]) for t in range(1, 10)}
    sum_exp = sum(exp_values.values())
    
    probabilities = []
    prob_dict = {}
    for t in range(1, 10):
        prob = exp_values[str(t)] / sum_exp
        probabilities.append({'type': t, 'probability': round(prob, 4)})
        prob_dict[str(t)] = round(prob, 4)
    
    # Sort by probability
    probabilities.sort(key=lambda x: x['probability'], reverse=True)
    
    inferred_core = probabilities[0]['type']
    top_prob = probabilities[0]['probability']
    second_prob = probabilities[1]['probability'] if len(probabilities) > 1 else 0
    gap = top_prob - second_prob
    
    # New confidence tier rules
    if top_prob >= 0.45 and gap >= 0.15:
        confidence_tier = 'high'
    elif top_prob >= 0.33 and gap >= 0.08:
        confidence_tier = 'medium'
    else:
        confidence_tier = 'low'
    
    is_close = gap < 0.08
    
    return {
        'inferred_core': inferred_core,
        'confidence': top_prob,
        'confidence_tier': confidence_tier,
        'is_close': is_close,
        'top_candidates': probabilities[:3],
        'mean_likert': mean_likert,
        'forced_hits': forced_hits,
        'raw_scores': raw_scores,
        'z_scores': z_scores,
        'probabilities': prob_dict
    }

# ============================================
# WING RESOLUTION (simplified for core type 7)
# ============================================

def compute_wing_access(inferred_core):
    """
    For Type 7, wings are 6 (left) and 8 (right)
    Simulate wing resolution responses for 7w8
    """
    if inferred_core != 7:
        return {
            'left_type': inferred_core - 1 if inferred_core > 1 else 9,
            'right_type': inferred_core + 1 if inferred_core < 9 else 1,
            'left_score': 0,
            'right_score': 0,
            'left_accessible': False,
            'right_accessible': False,
            'dominant_wing': None
        }
    
    # 7w8 wing resolution responses (6=left, 8=right)
    # Likert wing questions (2 left, 2 right)
    left_likert = [2, 2]  # Disagree with 6-wing items (seek support, uncertainty pushes to seek structure)
    right_likert = [5, 5]  # Strongly Agree with 8-wing items (alive when asserting, push through)
    
    # Forced choice wing questions (2 total)
    left_fc = 0  # FC choices for 6
    right_fc = 2  # FC choices for 8
    
    left_mean = sum(left_likert) / len(left_likert)
    right_mean = sum(right_likert) / len(right_likert)
    
    WING_FC_MULTIPLIER = 1.0
    left_score = left_mean + (WING_FC_MULTIPLIER * left_fc)
    right_score = right_mean + (WING_FC_MULTIPLIER * right_fc)
    
    # Normalize to 0-1 (max = 5 + 2 = 7)
    max_score = 7
    norm_left = left_score / max_score
    norm_right = right_score / max_score
    
    # Access rules
    left_accessible = norm_left >= 0.20
    right_accessible = norm_right >= 0.20
    
    # Dominant wing rules
    norm_diff = abs(norm_left - norm_right)
    if norm_diff < 0.07:
        dominant_wing = 'balanced'
    elif norm_right >= 0.25 and norm_right > norm_left:
        dominant_wing = 8
    elif norm_left >= 0.25 and norm_left > norm_right:
        dominant_wing = 6
    else:
        dominant_wing = None
    
    return {
        'left_type': 6,
        'right_type': 8,
        'left_score': round(left_score, 2),
        'right_score': round(right_score, 2),
        'left_accessible': left_accessible,
        'right_accessible': right_accessible,
        'dominant_wing': dominant_wing
    }

async def run_simulation():
    # Get simulated responses
    likert = get_7w8_likert_responses()
    fc = get_7w8_forced_choice_responses()
    
    # Compute v2 scoring
    scoring = compute_v2_scoring(likert, fc)
    
    # Compute wing access
    wing = compute_wing_access(scoring['inferred_core'])
    
    # Build output
    open_wings = []
    if wing['left_accessible']:
        open_wings.append(wing['left_type'])
    if wing['right_accessible']:
        open_wings.append(wing['right_type'])
    
    result = {
        "result": {
            "dominant_type": scoring['inferred_core'],
            "confidence_band": scoring['confidence_tier'],
            "top_three_types": scoring['top_candidates'],
            "wing_access": {
                "open_wings": open_wings,
                "dominant_wing": wing['dominant_wing']
            }
        },
        "debug": {
            "mean_likert_per_type": scoring['mean_likert'],
            "forced_hits_per_type": {k: int(v) for k, v in scoring['forced_hits'].items()},
            "raw_score_per_type": scoring['raw_scores'],
            "z_score_per_type": scoring['z_scores'],
            "probability_per_type": scoring['probabilities']
        },
        "wing_detail": {
            "left_type": wing['left_type'],
            "right_type": wing['right_type'],
            "left_score": wing['left_score'],
            "right_score": wing['right_score']
        }
    }
    
    print(json.dumps(result, indent=2))
    
    # Save to database for pete@pulsifi.me
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Find pete's user ID
    pete = await db.users.find_one({'email': 'pete@pulsifi.me'})
    if pete:
        user_id = str(pete['_id'])
        
        # Save v2 result
        result_doc = {
            "user_id": user_id,
            "method": "assessment_inference_v2",
            "version": "v2",
            "inferred_core": scoring['inferred_core'],
            "inferred_wing": wing['dominant_wing'],
            "confidence": scoring['confidence'],
            "confidence_tier": scoring['confidence_tier'],
            "is_close": scoring['is_close'],
            "top_candidates": scoring['top_candidates'],
            "state_calibration": {
                "energy_state": "high",
                "life_context": "expanding",
                "answer_frame": "best_self"
            },
            "debug_scores": {
                "raw_scores": scoring['raw_scores'],
                "z_scores": scoring['z_scores'],
                "wing_scores": {
                    "left": wing['left_score'],
                    "right": wing['right_score'],
                    "diff": abs(wing['left_score'] - wing['right_score'])
                },
                "mean_likert": scoring['mean_likert'],
                "forced_hits": scoring['forced_hits'],
                "probabilities": scoring['probabilities'],
                "wing_access": {
                    "left_type": wing['left_type'],
                    "right_type": wing['right_type'],
                    "left_accessible": wing['left_accessible'],
                    "right_accessible": wing['right_accessible'],
                    "dominant_wing": wing['dominant_wing']
                }
            },
            "created_at": datetime.now(timezone.utc)
        }
        
        await db.enneagram_results.update_one(
            {"user_id": user_id},
            {"$set": result_doc},
            upsert=True
        )
        
        print(f"\n✅ Saved v2 assessment result for pete@pulsifi.me (user_id: {user_id})")
    else:
        print("\n⚠️ pete@pulsifi.me not found in database")
    
    client.close()
    return result

if __name__ == "__main__":
    asyncio.run(run_simulation())
