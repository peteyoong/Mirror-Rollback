from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import hashlib
import secrets
import jwt
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Settings
JWT_SECRET = os.environ.get('JWT_SECRET', secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 168  # 7 days

# LLM Settings
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== Dynamic Depth Adaptation System ==============
# Internal layer inspired by Levels of Consciousness
# Infers user's interaction depth without labeling or displaying to user
# Values: "grounding" | "reflective" | "expansive"

from typing import Literal

InteractionDepth = Literal["grounding", "reflective", "expansive"]

class DepthInferenceResult:
    """Internal result of depth inference - never exposed to user"""
    def __init__(self, depth: InteractionDepth, signals: dict):
        self.depth = depth
        self.signals = signals  # For logging/debugging only
    
    def get_adaptation_instructions(self) -> str:
        """Returns prompt instructions based on inferred depth"""
        if self.depth == "grounding":
            return """
DEPTH ADAPTATION (GROUNDING MODE):
- Use simple, concrete language
- Offer ONE perspective at a time
- Start with validation and emotional acknowledgment
- Avoid abstract concepts until they feel settled
- Keep explanations short (2-3 sentences per point)
- Prioritize safety and reassurance
- Do NOT introduce advanced material
- Pace: Ground first, then gently invite reflection"""
        
        elif self.depth == "reflective":
            return """
DEPTH ADAPTATION (REFLECTIVE MODE):
- Use moderate complexity with clear explanations
- Offer 2 perspectives when relevant
- Balance insight with practical application
- Include some nuance but stay accessible
- Can introduce intermediate concepts
- Pace: Brief grounding, then explore together
- Invite deeper questions if they seem curious"""
        
        else:  # expansive
            return """
DEPTH ADAPTATION (EXPANSIVE MODE):
- Embrace complexity and nuance
- Offer multiple perspectives freely
- Use paradox and both/and thinking when appropriate
- Can introduce advanced framework material
- Longer, more layered responses are welcome
- Explore interconnections between concepts
- Pace: Can dive deep quickly
- Challenge assumptions gently when helpful"""

def analyze_onboarding_depth(onboarding_answers: dict) -> tuple[float, dict]:
    """
    Analyze onboarding answers to infer depth tendency.
    Returns a score (-1 to 1) and signal details.
    -1 = needs grounding, 0 = reflective, 1 = expansive
    """
    if not onboarding_answers:
        return 0, {"reason": "no_onboarding"}
    
    score = 0.0
    signals = {}
    
    # Analyze relationship_with_self
    rel_self = onboarding_answers.get("relationship_with_self", "").lower()
    if any(word in rel_self for word in ["struggling", "difficult", "hard", "lost", "confused"]):
        score -= 0.3
        signals["relationship_self"] = "struggling"
    elif any(word in rel_self for word in ["curious", "exploring", "growing", "learning"]):
        score += 0.1
        signals["relationship_self"] = "curious"
    elif any(word in rel_self for word in ["grounded", "peaceful", "connected", "clear"]):
        score += 0.3
        signals["relationship_self"] = "grounded"
    
    # Analyze desired_depth preference
    depth_pref = onboarding_answers.get("desired_depth", "moderate").lower()
    if depth_pref == "surface" or "light" in depth_pref:
        score -= 0.3
        signals["depth_preference"] = "surface"
    elif depth_pref == "deep" or "profound" in depth_pref:
        score += 0.3
        signals["depth_preference"] = "deep"
    else:
        signals["depth_preference"] = "moderate"
    
    # Analyze uncertainty_relationship
    uncertainty = onboarding_answers.get("uncertainty_relationship", "").lower()
    if any(word in uncertainty for word in ["challenging", "difficult", "scary", "anxious", "uncomfortable"]):
        score -= 0.2
        signals["uncertainty"] = "challenged"
    elif any(word in uncertainty for word in ["comfortable", "curious", "exciting", "open", "embracing"]):
        score += 0.2
        signals["uncertainty"] = "comfortable"
    
    # Analyze reflection_style
    style = onboarding_answers.get("reflection_style", "").lower()
    if any(word in style for word in ["simple", "quick", "practical", "action"]):
        score -= 0.1
        signals["style"] = "practical"
    elif any(word in style for word in ["patterns", "meaning", "connections", "deep"]):
        score += 0.2
        signals["style"] = "pattern-seeking"
    
    return max(-1, min(1, score)), signals

def analyze_journal_sentiment(journal_entries: list) -> tuple[float, dict]:
    """
    Analyze recent journal entries for emotional tone.
    Returns a score (-1 to 1) and signal details.
    -1 = distressed/urgent, 0 = neutral/mixed, 1 = reflective/expansive
    """
    if not journal_entries:
        return 0, {"reason": "no_journals"}
    
    # Combine recent entries (max 3)
    combined_text = " ".join([
        entry.get("content", "")[:500] 
        for entry in journal_entries[:3]
    ]).lower()
    
    if not combined_text.strip():
        return 0, {"reason": "empty_journals"}
    
    score = 0.0
    signals = {}
    
    # Distress/urgency markers (need grounding)
    distress_words = ["overwhelmed", "anxious", "scared", "panic", "help", "can't", 
                      "desperate", "stuck", "hopeless", "crying", "breakdown", "crisis"]
    distress_count = sum(1 for word in distress_words if word in combined_text)
    if distress_count >= 3:
        score -= 0.5
        signals["distress"] = "high"
    elif distress_count >= 1:
        score -= 0.2
        signals["distress"] = "present"
    
    # Reflective markers
    reflective_words = ["notice", "wonder", "curious", "interesting", "realize", 
                        "understand", "learning", "growing", "insight", "perhaps"]
    reflective_count = sum(1 for word in reflective_words if word in combined_text)
    if reflective_count >= 3:
        score += 0.3
        signals["reflective"] = "high"
    elif reflective_count >= 1:
        score += 0.1
        signals["reflective"] = "present"
    
    # Expansive markers
    expansive_words = ["paradox", "both", "perspective", "complexity", "nuance",
                       "transcend", "integrate", "wholeness", "interconnected", "pattern"]
    expansive_count = sum(1 for word in expansive_words if word in combined_text)
    if expansive_count >= 2:
        score += 0.3
        signals["expansive"] = "present"
    
    # Entry length as signal (very short = urgent, longer = reflective)
    avg_length = len(combined_text) / max(len(journal_entries[:3]), 1)
    if avg_length < 100:
        score -= 0.1
        signals["length"] = "short"
    elif avg_length > 500:
        score += 0.1
        signals["length"] = "substantial"
    
    return max(-1, min(1, score)), signals

def analyze_chat_tone(message: str) -> tuple[float, dict]:
    """
    Analyze the current chat message tone.
    Returns a score (-1 to 1) and signal details.
    """
    if not message:
        return 0, {"reason": "no_message"}
    
    message_lower = message.lower()
    score = 0.0
    signals = {}
    
    # Length analysis
    word_count = len(message.split())
    if word_count <= 5:
        score -= 0.2
        signals["length"] = "very_short"
    elif word_count <= 15:
        signals["length"] = "short"
    elif word_count >= 50:
        score += 0.2
        signals["length"] = "substantial"
    
    # Urgency markers
    urgency_markers = ["?!", "help", "please", "urgent", "now", "immediately", "asap"]
    if any(marker in message_lower for marker in urgency_markers):
        score -= 0.2
        signals["urgency"] = "present"
    
    # Question marks (curiosity)
    if message.count("?") >= 2:
        score += 0.1
        signals["curiosity"] = "high"
    
    # Reflective language
    reflective_phrases = ["i wonder", "i'm curious", "what if", "how might", 
                          "i've been thinking", "i notice", "it seems like"]
    if any(phrase in message_lower for phrase in reflective_phrases):
        score += 0.2
        signals["tone"] = "reflective"
    
    # Direct/demanding language
    demanding_phrases = ["tell me", "just give me", "i need to know", "what is my"]
    if any(phrase in message_lower for phrase in demanding_phrases):
        score -= 0.1
        signals["tone"] = "direct"
    
    # Complexity-seeking
    complexity_phrases = ["nuance", "deeper", "more complex", "both and", "paradox", 
                          "how does this connect", "what's the relationship"]
    if any(phrase in message_lower for phrase in complexity_phrases):
        score += 0.3
        signals["seeking"] = "complexity"
    
    return max(-1, min(1, score)), signals

async def infer_interaction_depth(
    user: dict,
    current_message: str = None,
    recent_journals: list = None
) -> DepthInferenceResult:
    """
    Main function to infer user's interaction depth.
    Combines signals from onboarding, journals, and current message.
    Returns DepthInferenceResult with depth and adaptation instructions.
    """
    all_signals = {}
    weights = {"onboarding": 0.3, "journal": 0.4, "chat": 0.3}
    
    # Get onboarding score
    onboarding_answers = user.get("onboarding_answers", {})
    onboarding_score, onboarding_signals = analyze_onboarding_depth(onboarding_answers)
    all_signals["onboarding"] = onboarding_signals
    
    # Get journal score
    if recent_journals is None:
        recent_journals = []
    journal_score, journal_signals = analyze_journal_sentiment(recent_journals)
    all_signals["journal"] = journal_signals
    
    # Get chat tone score
    chat_score, chat_signals = analyze_chat_tone(current_message or "")
    all_signals["chat"] = chat_signals
    
    # Weighted combination
    # If no journals, redistribute weight
    if not recent_journals:
        weights = {"onboarding": 0.5, "journal": 0.0, "chat": 0.5}
    
    # If no current message, redistribute weight
    if not current_message:
        if recent_journals:
            weights = {"onboarding": 0.4, "journal": 0.6, "chat": 0.0}
        else:
            weights = {"onboarding": 1.0, "journal": 0.0, "chat": 0.0}
    
    final_score = (
        onboarding_score * weights["onboarding"] +
        journal_score * weights["journal"] +
        chat_score * weights["chat"]
    )
    
    all_signals["scores"] = {
        "onboarding": round(onboarding_score, 2),
        "journal": round(journal_score, 2),
        "chat": round(chat_score, 2),
        "final": round(final_score, 2)
    }
    
    # Map score to depth
    if final_score <= -0.2:
        depth = "grounding"
    elif final_score >= 0.2:
        depth = "expansive"
    else:
        depth = "reflective"
    
    all_signals["inferred_depth"] = depth
    
    logger.info(f"Depth inference: {depth} (score: {final_score:.2f})")
    
    return DepthInferenceResult(depth=depth, signals=all_signals)

# ============== Models ==============

class UserRegister(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

class OnboardingAnswers(BaseModel):
    relationship_with_self: str  # Q1: How would you describe your current relationship with yourself?
    reflection_style: str        # Q2: When you reflect, what feels most natural to you?
    desired_depth: str           # Q3: How deep do you want to go in your reflections?
    uncertainty_relationship: str  # Q4: How do you relate to not knowing?
    intention: str               # Q5: What brings you here today?

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    password_hash: str
    onboarding_completed: bool = False
    onboarding_answers: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    onboarding_completed: bool
    onboarding_answers: Optional[dict] = None

class JournalEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class JournalEntryCreate(BaseModel):
    content: str

class JournalEntryUpdate(BaseModel):
    content: str

class MirrorContent(BaseModel):
    id: str
    insight: str
    reflection_question: str
    another_perspective: str
    closing_line: str
    date: str

class DailyReflection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    date_key: str  # YYYY-MM-DD format (server UTC date)
    todays_insight: str
    reflect_on: str
    another_perspective: str
    closing_line: str
    timezone_offset: Optional[int] = None  # Client timezone offset in minutes (for reference)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DailyReflectionResponse(BaseModel):
    id: str
    user_id: str
    date_key: str
    todays_insight: str
    reflect_on: str
    another_perspective: str
    closing_line: str
    timezone_offset: Optional[int] = None
    created_at: datetime

# ============== Helper Functions ==============

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============== Mirror Content Pool ==============
# Framework-blind reflective content

MIRROR_CONTENT_POOL = [
    {
        "insight": "Stillness is not the absence of movement, but the presence of attention.",
        "reflection_question": "Where in your life might you be mistaking busyness for progress?",
        "another_perspective": "What if the pause itself is the journey?",
        "closing_line": "If something stirs, your journal awaits."
    },
    {
        "insight": "You are not your thoughts. You are the one who notices them.",
        "reflection_question": "What recurring thought have you been believing without questioning?",
        "another_perspective": "Perhaps that thought is a visitor, not a resident.",
        "closing_line": "There's space to write what you notice."
    },
    {
        "insight": "Every ending carries the seed of a beginning you cannot yet see.",
        "reflection_question": "What have you been holding onto that might be ready to transform?",
        "another_perspective": "Release and receive may be the same movement.",
        "closing_line": "Your reflections are safe here."
    },
    {
        "insight": "Clarity often arrives not through thinking harder, but through listening deeper.",
        "reflection_question": "What is your body telling you that your mind hasn't acknowledged?",
        "another_perspective": "Wisdom doesn't always arrive in words.",
        "closing_line": "Write what wants to be heard."
    },
    {
        "insight": "The present moment is the only place where change can happen.",
        "reflection_question": "What small shift could you make right now, not later?",
        "another_perspective": "Sometimes the smallest door opens the largest room.",
        "closing_line": "Capture what feels true, even if it's simple."
    },
    {
        "insight": "Uncertainty is not a problem to solve but a space to inhabit.",
        "reflection_question": "What would you do differently if you didn't need to know the outcome?",
        "another_perspective": "The unknown is not empty—it is full of possibility.",
        "closing_line": "Your journal holds space for questions without answers."
    },
    {
        "insight": "What you resist often persists. What you embrace transforms.",
        "reflection_question": "What are you pushing away that might be asking for your attention?",
        "another_perspective": "Welcome can be a form of wisdom.",
        "closing_line": "There's no wrong way to reflect."
    },
    {
        "insight": "You are already whole, even as you grow.",
        "reflection_question": "What part of yourself have you been waiting to accept until you 'improve'?",
        "another_perspective": "Growth and completeness can coexist.",
        "closing_line": "Write to yourself as you would to someone you love."
    },
    {
        "insight": "Sometimes the most courageous thing is to rest.",
        "reflection_question": "Where have you been pushing when softness might serve better?",
        "another_perspective": "Strength includes knowing when to pause.",
        "closing_line": "Rest can be a reflection too."
    },
    {
        "insight": "Your relationship with yourself sets the tone for every other relationship.",
        "reflection_question": "How have you spoken to yourself today?",
        "another_perspective": "Self-compassion isn't selfish—it's foundational.",
        "closing_line": "The journal is a conversation with yourself."
    },
    {
        "insight": "What you focus on expands.",
        "reflection_question": "Where has your attention been dwelling lately?",
        "another_perspective": "Attention is a form of nourishment.",
        "closing_line": "Notice what wants to grow."
    },
    {
        "insight": "Healing happens in layers, not all at once.",
        "reflection_question": "What layer are you on right now, and can you honor that?",
        "another_perspective": "Each layer has its own timing.",
        "closing_line": "Write from where you are, not where you think you should be."
    },
    {
        "insight": "Boundaries are an expression of self-respect.",
        "reflection_question": "Where might you need to say no in order to say yes to yourself?",
        "another_perspective": "Every boundary creates space for something.",
        "closing_line": "Your needs are valid reflections."
    },
    {
        "insight": "You don't have to have it all figured out to move forward.",
        "reflection_question": "What could you try today without needing to be certain?",
        "another_perspective": "Action and doubt can walk together.",
        "closing_line": "Progress is often invisible at first."
    }
]

# ============== Lenses Content ==============
# Lenses are optional perspectives, not definitions
# IMPORTANT: Mirror must remain framework-blind and never reference these lenses

LENSES_CONTENT = [
    {
        "id": "true-sidereal-astrology",
        "title": "True Sidereal Astrology",
        "icon": "planet",
        "summary": "A perspective that looks at where celestial bodies actually are in the sky, not where they were thousands of years ago. This lens offers a way to reflect on cycles, seasons, and the rhythms that influence how you feel and move through life. It's about noticing patterns, not predicting fate.",
        "snapshot_prompt": "Based on their onboarding answers, generate a warm, personalized reflection about how they might relate to natural cycles and rhythms. Focus on their relationship to time, seasons, and recurring patterns in life. Be emotionally supportive, intellectually clarifying, and gently evocative. Do NOT assign any astrological signs or make predictions.",
        "deep_dive": {
            "description": "True Sidereal Astrology differs from tropical astrology by aligning with the actual current positions of constellations. While tropical astrology uses fixed dates established around 2,000 years ago, sidereal astrology accounts for the precession of the equinoxes—Earth's slow wobble that shifts our view of the stars over time.",
            "key_concepts": [
                "Precession of the equinoxes: Earth's 26,000-year wobble cycle",
                "Actual star positions versus symbolic seasons",
                "The 13th constellation: Ophiuchus",
                "Planetary transits and their observed correlations",
                "Moon phases and emotional tides"
            ],
            "reflection_themes": [
                "How do you relate to natural cycles in your life?",
                "What patterns repeat for you seasonally or monthly?",
                "How might the moon's phases mirror your inner rhythms?"
            ],
            "invitation": "Consider tracking your energy and mood alongside lunar phases for a month. What patterns emerge?"
        }
    },
    {
        "id": "human-design",
        "title": "Human Design",
        "icon": "body",
        "summary": "A system that combines ancient wisdom traditions into a unique map of how you're designed to make decisions and interact with the world. Rather than telling you who to be, it offers language for understanding how your energy naturally flows and what environments help you thrive.",
        "snapshot_prompt": "Based on their onboarding answers, generate a warm reflection about their relationship to energy, decision-making, and self-trust. Describe implications and lived experience WITHOUT using technical Human Design terms (no Type names, no Authority names, no 'centers' or 'gates'). Focus on how they might naturally move through life—do they seem like someone who initiates or responds? Do they need time to process decisions? What environments might support them? Be emotionally supportive, intellectually clarifying, and gently evocative. Frame everything as patterns to observe, not fixed identity.",
        "deep_dive": {
            "description": "Human Design synthesizes elements from the I Ching, Kabbalah, the Hindu-Brahmin chakra system, and Western astrology into a comprehensive framework. It uses your birth data to generate a 'bodygraph'—a visual representation of your energetic blueprint.",
            "structured_elements": {
                "note": "To see your specific Human Design chart, you would need to enter your birth date, time, and location. The elements below explain what each component reveals:",
                "type": {
                    "label": "Type",
                    "description": "How you're designed to exchange energy with the world. Some people are built to initiate, others to respond, others to guide, and some to reflect. Your Type suggests your natural rhythm of engagement.",
                    "patterns_to_observe": "Notice when you feel energized versus drained. Do you thrive when starting things, or when responding to what comes to you?"
                },
                "strategy": {
                    "label": "Strategy",
                    "description": "The optimal way for your Type to make decisions and engage with opportunities. Following your Strategy often reduces resistance and increases flow.",
                    "patterns_to_observe": "Pay attention to decisions that felt 'right' versus those that felt forced. What was different about how you entered into them?"
                },
                "inner_authority": {
                    "label": "Inner Authority",
                    "description": "Your body's unique decision-making intelligence. Some people are guided by gut responses, others by emotional waves, others by intuitive hits, and some by the wisdom of time.",
                    "patterns_to_observe": "Where in your body do you feel 'yes' and 'no'? How long do you typically need to know if something is right for you?"
                },
                "profile": {
                    "label": "Profile",
                    "description": "Your life theme, expressed as a combination of two numbers (like 3/5 or 6/2). It describes the costume you wear and the role you play in your journey.",
                    "patterns_to_observe": "What themes keep appearing in your life story? What role do others often see you playing?"
                },
                "definition": {
                    "label": "Definition",
                    "description": "How your energy centers connect to each other. This affects how self-contained you feel versus how much you need others to feel 'complete.'",
                    "patterns_to_observe": "Do you feel whole on your own, or do you come alive in partnership? How does being alone versus being with others affect your clarity?"
                },
                "incarnation_cross": {
                    "label": "Incarnation Cross",
                    "description": "Your life's larger purpose or theme—the backdrop against which your personal journey unfolds. It's not a destination but a context.",
                    "patterns_to_observe": "What larger themes seem to be woven through your life experiences? What might you be here to explore or express?"
                },
                "not_self_and_signature": {
                    "label": "Not-Self Theme & Signature",
                    "description": "The Not-Self theme is the emotional signal that you're out of alignment (frustration, anger, bitterness, or disappointment depending on Type). The Signature is the feeling when you're in flow (satisfaction, peace, success, or surprise).",
                    "patterns_to_observe": "What emotion signals that something is 'off' for you? What do you feel when life is flowing well?"
                }
            },
            "learn_over_time": {
                "intro": "Human Design is best learned through lived experience, not memorization. These modules are designed to be explored over weeks or months—letting each concept sink in through observation before moving to the next. The goal isn't to learn facts, but to recognize yourself.",
                "modules": [
                    {
                        "id": 1,
                        "title": "Foundations",
                        "subtitle": "Type, Strategy, Authority, Not-Self Theme & Signature",
                        "narrative": "Think about the last time you made a decision that felt right—not logically right, but right in your body. Maybe there was a settling sensation, or a sudden clarity, or a gut response you couldn't explain. Now think about a decision that turned out badly. Before the logic kicked in, was there a signal you ignored? A tightness, a hesitation, a feeling of forcing? Human Design suggests we each have a 'home base' for these signals—a place in the body where truth registers before the mind catches up. The Not-Self Theme is the feeling that tells you something's off: frustration, bitterness, anger, or disappointment. The Signature is what you feel when life flows: satisfaction, peace, success, or surprise.",
                        "examples": [
                            "At work: You agree to lead a project because it makes sense on paper. But there's a heaviness you can't name. Two months in, you're exhausted and resentful. Looking back, you realize your body knew before you committed.",
                            "In relationships: You've said yes to plans you didn't want, then felt drained and irritable. The pattern isn't about the other person—it's about not trusting the initial 'no' that flickered before you spoke."
                        ],
                        "reflective_question": "When you've ignored your body's first response to a decision, what usually happened?",
                        "experiment": "For one week, notice your body's first response before you answer any request. Don't change anything—just notice. What patterns emerge?"
                    },
                    {
                        "id": 2,
                        "title": "Profile",
                        "subtitle": "The costume you wear through life",
                        "narrative": "Have you ever noticed that people seem to see you in a particular way—casting you in roles you didn't audition for? Maybe they come to you when things need fixing, or they expect you to have researched something thoroughly, or they're surprised when you haven't figured out what you want to do with your life yet. Your Profile describes this dynamic: the role you naturally play and the role others project onto you. It's not who you are—it's the costume you wear as you move through your story. The first number is how you experience yourself; the second is how others tend to experience you. Sometimes these align. Sometimes they create friction. Both are useful information.",
                        "examples": [
                            "At work: You keep getting asked to fix broken projects, even though you never asked for that reputation. It's exhausting, but also—when you're honest—it's what you're genuinely good at.",
                            "In relationships: People are drawn to talents you don't see in yourself. They call things out of you that surprise you. You're not sure if it's flattering or uncomfortable—maybe both."
                        ],
                        "reflective_question": "What role do people keep casting you in, whether or not you asked for it? Does it feel like a gift, a burden, or both?",
                        "experiment": "Ask three people who know you well: 'What do you see as my natural role or gift?' Notice if their answers surprise you or confirm something you already sensed."
                    },
                    {
                        "id": 3,
                        "title": "Definition",
                        "subtitle": "Your relationship to consistency and others",
                        "narrative": "Some people feel essentially the same whether they're alone or with others. Their internal world is consistent, reliable, self-contained. Other people feel like they come alive—or finally make sense—when they're around certain people. It's not emotional dependency; it's more like a circuit completing. Alone, there are gaps. Together, something flows. This is what Human Design calls Definition: how your energy centers connect internally. It's not better to be one way or another. But knowing which you are can explain a lot—why solitude feels clarifying or draining, why certain people feel like home, why you might need more time alone (or together) than you thought.",
                        "examples": [
                            "At work: You notice your best thinking happens in conversation with a particular colleague. Alone, the ideas feel murky. It's not that you need their approval—something actually clicks when they're present.",
                            "In relationships: You've wondered if you're too dependent because you feel more 'yourself' around your partner. But it might not be dependency—it might be that they bridge something in your energy that you don't have access to alone."
                        ],
                        "reflective_question": "Do you generally feel complete and consistent on your own, or do certain people seem to bring something into focus that you can't access alone?",
                        "experiment": "Spend one day mostly alone and one day mostly with others. Notice your clarity, your energy, your sense of self. Not which is 'better'—just what's different."
                    },
                    {
                        "id": 4,
                        "title": "Incarnation Cross",
                        "subtitle": "Life themes, not destiny",
                        "narrative": "Look back at your life and notice what keeps showing up. Not the specifics—but the themes. Maybe you keep finding yourself in situations where you have to explain things. Or mediate conflicts. Or pioneer something new. Or hold space for people going through transitions. These aren't coincidences or proof of destiny. They're patterns—recurring contexts that your life seems to orbit around. Human Design calls this your Incarnation Cross: the backdrop of your story, not its conclusion. Knowing your themes doesn't tell you what to do. But it can help you stop fighting the current and start working with it.",
                        "examples": [
                            "At work: You realize every job you've had—regardless of title—has involved some version of the same thing. Maybe it's bringing structure to chaos. Or questioning assumptions. Or helping people see what they couldn't see before.",
                            "In relationships: The same themes keep appearing across different partnerships. Not the same problems—but the same territory. As if you're here to learn something specific, over and over, in deeper layers."
                        ],
                        "reflective_question": "If you had to describe the throughline of your life so far—the theme that keeps appearing regardless of circumstances—what would it be?",
                        "experiment": "Look at three major chapters of your life. What themes repeat across all three, even though the situations were completely different? Write what you notice."
                    },
                    {
                        "id": 5,
                        "title": "Integration Practices",
                        "subtitle": "Living the experiment",
                        "narrative": "Here's the thing about Human Design: reading about it isn't the same as living it. The real insights come when you take these concepts off the page and into your day—when you catch yourself overriding a gut response and pause, when you notice the feeling that tells you something's off, when you track which environments drain you and which restore you. The goal isn't to 'be your design.' It's to use these frameworks as mirrors—helping you notice what's already happening beneath your conscious awareness. Some things will click immediately. Others might take months. Trust your own experience over any external authority, including this system itself.",
                        "examples": [
                            "Morning practice: Before your day begins, set an intention to notice one thing about how you make decisions. Not to change anything—just to observe what's already happening.",
                            "Evening reflection: At day's end, ask: 'When did I feel most like myself today? When did I feel like I was forcing something?' Write a sentence or two in your journal."
                        ],
                        "reflective_question": "What aspect of what you've learned feels most alive or relevant right now? What feels abstract or distant? Both answers are useful.",
                        "experiment": "Choose one concept from the previous modules that intrigues you. For two weeks, make it your sole focus—noticing it in yourself, in others, in how situations unfold. At the end, journal what you learned."
                    }
                ],
                "advanced_lens": {
                    "title": "Optional Advanced Lens: Gene Keys",
                    "description": "Gene Keys is a related system that goes deeper into the 64 hexagrams underlying Human Design, exploring how shadow patterns can transform into gifts and ultimately into their highest expression. It's not necessary for understanding Human Design basics, but some find it offers additional depth.",
                    "note": "This is an optional advanced topic. The foundational modules above are complete on their own."
                }
            },
            "reflection_themes": [
                "How do you typically make decisions? Head, gut, or waiting?",
                "Do you feel energized by initiating or responding?",
                "What environments drain you versus support you?"
            ],
            "invitation": "Notice for one week: when do you feel most yourself, and when do you feel like you're forcing something?"
        }
    },
    {
        "id": "numerology",
        "title": "Numerology",
        "icon": "calculator",
        "summary": "An ancient practice of finding meaning in numbers, particularly those connected to your birth date and name. This lens uses numerical patterns as a mirror for self-reflection—not as prediction, but as a symbolic language for exploring your tendencies, gifts, and growth edges.",
        "snapshot_prompt": "Based on their onboarding answers, generate a warm reflection about themes and patterns in their life journey. Focus on their relationship to cycles, personal growth, and their natural gifts. Do NOT calculate or assign any specific numbers. Be emotionally supportive, intellectually clarifying, and gently evocative. Frame as patterns to notice, not fixed destiny.",
        "deep_dive": {
            "description": "Numerology assigns significance to numbers derived from your birth date (Life Path Number) and the letters in your name (Expression, Soul Urge, and Personality Numbers). Each number from 1-9, plus master numbers 11, 22, and 33, carries archetypal qualities.",
            "key_concepts": [
                "Life Path Number: Calculated from your full birth date, representing your journey's theme",
                "Expression Number: Derived from your full name, reflecting your natural abilities",
                "Soul Urge Number: From the vowels in your name, revealing inner desires",
                "Personal Year Cycles: 9-year patterns of growth and change",
                "Master Numbers: 11, 22, 33—intensified spiritual significance"
            ],
            "reflection_themes": [
                "What themes keep recurring in your life journey?",
                "How do you relate to cycles of beginning, building, and releasing?",
                "What gifts do you naturally bring to situations?"
            ],
            "invitation": "Calculate your Life Path Number (reduce your birth date to a single digit) and see if its themes resonate with your experience."
        }
    },
    {
        "id": "levels-of-consciousness",
        "title": "Levels of Consciousness",
        "icon": "layers",
        "summary": "A map of human development that tracks how our awareness expands over time. This lens isn't about being 'higher' or 'better'—it's about understanding where you are, what's available at each stage, and how growth naturally unfolds when conditions support it.",
        "snapshot_prompt": "DO NOT assign the user any level or stage. Instead, reflect on their growth orientation based on onboarding answers. Focus on their openness to complexity, their relationship to uncertainty, and their capacity for multiple perspectives. Be emotionally supportive and frame growth as a natural unfolding, not a ladder to climb.",
        "is_dynamic_framework": True,
        "dynamic_note": "This lens works differently from the others. Rather than mapping you to a fixed position, Project Mirror uses this framework dynamically—adapting its tone, depth, and perspective based on your journaling patterns and interactions over time. You won't be assigned a 'level.' Instead, the app learns how to meet you where you are on any given day.",
        "deep_dive": {
            "description": "The Levels of Consciousness framework suggests that human awareness develops through identifiable stages. Each level represents a different way of making meaning, with its own worldview, values, and limitations. Development isn't linear—we can access different levels in different contexts—but there's a general direction of increasing complexity, compassion, and perspective-taking.",
            "how_mirror_uses_this": "Project Mirror uses this framework to calibrate how it speaks to you. Based on signals from your journal entries and onboarding answers, the app adjusts: depth of reflection (surface to profound), tolerance for paradox (concrete to both/and), emotional tone (reassuring to challenging), and perspective scope (personal to universal). This happens automatically—you don't need to do anything except show up authentically.",
            "key_concepts": [
                "Survival and Safety: Basic needs, fear-based responses, concrete thinking",
                "Power and Achievement: Ego development, competition, success orientation",
                "Conformity and Belonging: Rules, roles, group identity, traditional values",
                "Rationality and Independence: Logic, individual truth-seeking, questioning",
                "Pluralism and Sensitivity: Multiple perspectives, equality, relativism",
                "Integration and Systems Thinking: Seeing wholes, paradox tolerance, complexity",
                "Unity and Transcendence: Non-dual awareness, universal compassion, flow"
            ],
            "important_note": "These stages are not judgments. Every stage has gifts and limitations. A person at 'Achievement' isn't worse than someone at 'Integration'—they're focused on different developmental tasks. The goal isn't to 'level up' but to fully inhabit wherever you are while remaining open to what's emerging.",
            "reflection_themes": [
                "How do you typically respond to ideas that challenge your worldview?",
                "What helps you grow? Comfort or challenge? Or both?",
                "How do you hold contradictions—do you need to resolve them, or can they coexist?"
            ],
            "invitation": "Notice this week: when do you feel most expansive in your thinking? When do you contract? There's no wrong answer—just information."
        }
    }
]

def get_mirror_content_for_date(date_str: str) -> dict:
    """Get deterministic mirror content based on date"""
    # Use date as seed for consistent daily content
    hash_value = int(hashlib.md5(date_str.encode()).hexdigest(), 16)
    index = hash_value % len(MIRROR_CONTENT_POOL)
    content = MIRROR_CONTENT_POOL[index]
    return {
        "id": f"mirror-{date_str}",
        "date": date_str,
        **content
    }

import random

# ============== Personalized Reflection Generator ==============
# Adapts reflections based on onboarding answers without using any metaphysical frameworks

# Extended content pools for different depths and styles
DEEP_INSIGHTS = [
    "The layers of your experience hold wisdom that unfolds gradually, revealing itself when you're ready to receive it.",
    "Within the complexity of your inner landscape lies a simplicity waiting to be discovered—not by solving, but by allowing.",
    "What feels like fragmentation may actually be the necessary scattering before a deeper integration can occur.",
    "The relationship between your past self and present self is not linear; it spirals, revisiting familiar themes with new understanding.",
    "Meaning often emerges not from the moments we plan, but from the spaces between—the pauses, the transitions, the almost-invisible shifts.",
    "Your capacity to hold contradiction without resolution is itself a form of wisdom that the rushing mind cannot access.",
    "The boundaries between healing and growing are more porous than we imagine; sometimes they are the same movement witnessed from different angles.",
]

LIGHT_INSIGHTS = [
    "This moment is enough.",
    "You are here. That matters.",
    "Small steps count.",
    "Breathe. Begin again.",
    "Today holds possibility.",
    "You don't need to figure it all out.",
    "Rest is productive too.",
]

DEEP_QUESTIONS = [
    "What truth have you been circling around, approaching and retreating from, that might be ready for a closer look?",
    "If you traced the thread of your current challenge back through time, what earlier version of this pattern might you discover?",
    "What would it mean to fully accept where you are, not as a stepping stone to somewhere else, but as the destination itself?",
    "Which of your beliefs about yourself have you inherited rather than chosen, and how do they shape your daily experience?",
]

LIGHT_QUESTIONS = [
    "What's one thing you can appreciate right now?",
    "What would feel like ease today?",
    "Where can you be gentle with yourself?",
    "What's asking for your attention?",
]

DEEP_PERSPECTIVES = [
    "Perhaps what feels like stagnation is actually a form of integration happening below the surface, invisible but essential.",
    "The resistance you feel might be information rather than obstacle—a signal pointing toward something important.",
    "What if the uncertainty you're experiencing is not a problem to solve but a threshold you're being invited to stand in?",
]

LIGHT_PERSPECTIVES = [
    "Maybe it's simpler than it seems.",
    "What if good enough is enough?",
    "Perhaps you're further along than you realize.",
]

# Grounding additions for those who struggle with uncertainty
GROUNDING_PHRASES = [
    "You are safe to explore this.",
    "There's no rush to find answers.",
    "It's okay to not know yet.",
    "You can return to solid ground anytime.",
    "This uncertainty won't last forever.",
]

# Pattern-focused additions
PATTERN_ADDITIONS = [
    "You might notice a recurring theme here—",
    "There may be a pattern worth observing—",
    "See if this connects to something familiar—",
    "Watch for echoes of past experiences—",
]

# Somatic/body-focused additions
SOMATIC_ADDITIONS = [
    "Notice where this sits in your body.",
    "What does your body know about this?",
    "Feel into this question physically.",
    "Let your body respond before your mind.",
    "Where do you sense this in your physical self?",
]

# Clarity-focused additions
CLARITY_ADDITIONS = [
    "Clarity often arrives softly, in its own time.",
    "Sometimes clarity comes not from seeking, but from settling.",
    "Let clarity find you rather than chasing it.",
    "The path may become clear one step at a time.",
]

def generate_personalized_reflection(onboarding_answers: dict = None) -> dict:
    """
    Generate a personalized reflection based on user's onboarding answers.
    This is the FALLBACK template-based generator.
    
    HARD RULE: Never mentions Human Design, astrology, numerology, charts, 
    types, authorities, or any framework terms.
    """
    
    # Default to base content if no onboarding answers
    if not onboarding_answers:
        content = random.choice(MIRROR_CONTENT_POOL)
        return {
            "todays_insight": content["insight"],
            "reflect_on": content["reflection_question"],
            "another_perspective": content["another_perspective"],
            "closing_line": content["closing_line"]
        }
    
    # Extract onboarding values with defaults
    depth = onboarding_answers.get("desired_depth", "moderate")
    uncertainty = onboarding_answers.get("uncertainty_relationship", "mixed")
    reflection_style = onboarding_answers.get("reflection_style", "contemplating")
    intention = onboarding_answers.get("intention", "self_understanding")
    
    # Determine if deep or light content
    is_deep = depth == "deep"
    is_light = depth == "surface"
    needs_grounding = uncertainty in ["challenging", "learning"]
    is_pattern_focused = reflection_style == "patterns"
    is_body_focused = reflection_style == "feeling"
    seeks_clarity = intention == "clarity"
    
    # Select base content based on depth
    if is_deep:
        insight = random.choice(DEEP_INSIGHTS)
        question = random.choice(DEEP_QUESTIONS)
        perspective = random.choice(DEEP_PERSPECTIVES)
    elif is_light:
        insight = random.choice(LIGHT_INSIGHTS)
        question = random.choice(LIGHT_QUESTIONS)
        perspective = random.choice(LIGHT_PERSPECTIVES)
    else:
        # Moderate depth - use original pool
        content = random.choice(MIRROR_CONTENT_POOL)
        insight = content["insight"]
        question = content["reflection_question"]
        perspective = content["another_perspective"]
    
    # Build closing line
    closing_parts = []
    
    # Add grounding language if needed
    if needs_grounding:
        closing_parts.append(random.choice(GROUNDING_PHRASES))
    
    # Add pattern language if that's their style
    if is_pattern_focused:
        question = random.choice(PATTERN_ADDITIONS) + question.lower()
    
    # Add somatic language if that's their style
    if is_body_focused:
        somatic = random.choice(SOMATIC_ADDITIONS)
        perspective = f"{perspective} {somatic}"
    
    # Add clarity language if that's their intention
    if seeks_clarity:
        closing_parts.append(random.choice(CLARITY_ADDITIONS))
    
    # Default closing if no special additions
    if not closing_parts:
        closing_parts.append(random.choice([
            "Your journal awaits when you're ready.",
            "There's space to explore this further.",
            "Write what feels true.",
            "Your reflections are welcome here.",
            "Take what resonates, leave the rest.",
        ]))
    
    closing_line = " ".join(closing_parts)
    
    return {
        "todays_insight": insight,
        "reflect_on": question,
        "another_perspective": perspective,
        "closing_line": closing_line
    }

# ============== ChatGPT Mirror Generation ==============

# Forbidden terms list (case-insensitive)
FORBIDDEN_TERMS = [
    "manifestor",
    "manifesting generator",
    "generator",
    "human design",
    "authority",
    "profile",
    "gates",
    "astrology",
    "zodiac",
    "planet",
    "houses",
    "numerology",
    "life path",
    "gene keys",
    "bazi",
    "enneagram",
]

def validate_reflection_content(content: dict) -> tuple[bool, list]:
    """
    Validate that reflection content does not contain any forbidden terms.
    Returns (is_valid, list_of_found_terms)
    """
    found_terms = []
    
    # Combine all text fields for checking
    all_text = " ".join([
        str(content.get("todays_insight", "")),
        str(content.get("reflect_on", "")),
        str(content.get("another_perspective", "")),
        str(content.get("closing_line", "")),
        str(content.get("closing", "")),
    ]).lower()
    
    for term in FORBIDDEN_TERMS:
        if term.lower() in all_text:
            found_terms.append(term)
    
    return len(found_terms) == 0, found_terms

MIRROR_SYSTEM_PROMPT = """You are generating daily reflections for Project Mirror, a personal reflection app.

=== PROJECT MIRROR "EPIPHANY NARRATIVE" STYLE ===

Your reflections MUST follow this structure:

1. TODAY'S INSIGHT - Start with the lived experience
   Begin with something relatable that the reader might have felt today or recently.
   Use sensory, grounded language: "You might have noticed..." or "There's that moment when..."
   
2. REFLECT ON - Name the pattern gently, then offer a reframing
   Identify what might be happening beneath the surface.
   Offer a perspective shift that could trigger an "aha" moment.
   The goal is resonance and self-recognition.

3. ANOTHER PERSPECTIVE - A different angle that opens possibility
   Not contradicting the insight, but expanding it.
   
4. CLOSING - A gentle invitation to journal (never a command)

=== ABSOLUTE RULES ===

1. FRAMEWORK-BLIND: You must NEVER mention or reference:
   - Human Design, manifestor, generator, projector, reflector
   - Astrology, zodiac signs, planets, houses
   - Numerology, life path numbers
   - Gene Keys, Enneagram, MBTI, or any typing system
   - Authority, type, chart, profile, gates (in a framework context)

2. NO PREDICTIONS: Never predict outcomes or tell users what will happen
3. NO ADVICE: Never tell users what to do - only offer invitations
4. NO IDENTITY CLAIMS: Never say "you are" - use "you might notice..."
5. NO MYSTICAL LANGUAGE: Stay grounded in everyday experience

=== TONE ===

- Start grounded in felt experience
- Be warm but not saccharine
- Be inviting but not prescriptive
- Create resonance, not instruction
- Leave them feeling seen, not taught

OUTPUT FORMAT (strict JSON):
{
  "todays_insight": "Start with lived experience, then name a pattern gently (80-120 words)",
  "reflect_on": "One reflective question that emerges naturally from the insight",
  "another_perspective": "A reframing or different angle (80-120 words)",
  "closing": "One sentence gently inviting journaling"
}

Respond ONLY with valid JSON. No markdown, no explanation, just the JSON object."""

async def generate_reflection_with_llm(
    onboarding_answers: dict,
    recent_journals: list = None,
    date_key: str = None
) -> dict:
    """
    Generate a personalized reflection using ChatGPT.
    Falls back to template-based generation if LLM fails.
    """
    
    if not EMERGENT_LLM_KEY:
        logger.warning("No EMERGENT_LLM_KEY configured, falling back to template")
        return generate_personalized_reflection(onboarding_answers)
    
    # Build user context (used for both attempts)
    def build_user_prompt(is_retry: bool = False, found_terms: list = None) -> str:
        context_parts = []
        
        # Add onboarding context
        if onboarding_answers:
            context_parts.append("USER PROFILE FROM ONBOARDING:")
            context_parts.append(f"- Relationship with self: {onboarding_answers.get('relationship_with_self', 'not specified')}")
            context_parts.append(f"- Preferred reflection style: {onboarding_answers.get('reflection_style', 'not specified')}")
            context_parts.append(f"- Desired depth: {onboarding_answers.get('desired_depth', 'moderate')}")
            context_parts.append(f"- Relationship to uncertainty: {onboarding_answers.get('uncertainty_relationship', 'not specified')}")
            context_parts.append(f"- Intention for using app: {onboarding_answers.get('intention', 'self understanding')}")
        
        # Add recent journal context (if available)
        if recent_journals and len(recent_journals) > 0:
            context_parts.append("\nRECENT JOURNAL ENTRIES (most recent first):")
            for i, entry in enumerate(recent_journals[:3]):  # Max 3 entries
                # Truncate long entries
                content = entry.get('content', '')[:500]
                if len(entry.get('content', '')) > 500:
                    content += "..."
                context_parts.append(f"Entry {i+1}: {content}")
        
        # Add date context
        if date_key:
            context_parts.append(f"\nToday's date: {date_key}")
        
        # Personalization instructions based on onboarding
        personalization = []
        depth = onboarding_answers.get('desired_depth', 'moderate') if onboarding_answers else 'moderate'
        uncertainty = onboarding_answers.get('uncertainty_relationship', 'mixed') if onboarding_answers else 'mixed'
        reflection_style = onboarding_answers.get('reflection_style', 'contemplating') if onboarding_answers else 'contemplating'
        intention = onboarding_answers.get('intention', 'self_understanding') if onboarding_answers else 'self_understanding'
        
        if depth == 'deep':
            personalization.append("Use longer, more nuanced wording. The user prefers deep, meaningful reflections.")
        elif depth == 'surface':
            personalization.append("Keep it simple and brief. The user prefers light, present-focused reflections.")
        
        if uncertainty in ['challenging', 'learning']:
            personalization.append("Include grounding, reassuring language. The user finds uncertainty challenging.")
        
        if reflection_style == 'patterns':
            personalization.append("Include pattern-oriented language like 'you might notice a recurring theme...'")
        elif reflection_style == 'feeling':
            personalization.append("Include somatic/body-focused language like 'notice where this sits in your body...'")
        
        if intention == 'clarity':
            personalization.append("Gently orient toward clarity without giving direct advice.")
        
        if personalization:
            context_parts.append("\nPERSONALIZATION NOTES:")
            context_parts.extend([f"- {p}" for p in personalization])
        
        # Add stricter warning on retry
        if is_retry and found_terms:
            context_parts.append(f"\n⚠️ CRITICAL WARNING: Your previous response contained FORBIDDEN terms: {', '.join(found_terms)}")
            context_parts.append("You MUST NOT use ANY of these terms or related concepts:")
            context_parts.append("- manifestor, manifesting generator, generator, human design, authority, profile, gates")
            context_parts.append("- astrology, zodiac, planet, houses, numerology, life path")
            context_parts.append("- gene keys, bazi, enneagram")
            context_parts.append("Use ONLY grounded, everyday language about self-reflection.")
        
        context_parts.append("\nGenerate a unique daily reflection based on this context. Remember: NO frameworks, NO advice, NO predictions.")
        
        return "\n".join(context_parts)
    
    async def call_llm(user_prompt: str, is_retry: bool = False) -> dict:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Use stricter system prompt on retry
        system_prompt = MIRROR_SYSTEM_PROMPT
        if is_retry:
            system_prompt = MIRROR_SYSTEM_PROMPT + """

⚠️ STRICT MODE ACTIVATED ⚠️
Your previous response contained forbidden framework terms. 
You must ABSOLUTELY NOT mention:
- manifestor, manifesting generator, generator (Human Design types)
- human design, authority, profile, gates, chart
- astrology, zodiac, planet, houses, horoscope
- numerology, life path, life path number
- gene keys, bazi, enneagram, personality type

Use ONLY everyday reflective language. No typing systems. No frameworks.
Focus on universal human experiences: emotions, thoughts, growth, presence, awareness."""
        
        # Initialize LLM chat
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"mirror-{date_key or 'default'}-{'retry' if is_retry else 'first'}",
            system_message=system_prompt
        ).with_model("openai", "gpt-4o")
        
        # Send message
        user_message = UserMessage(text=user_prompt)
        response = await chat.send_message(user_message)
        
        # Parse JSON response
        # Clean up response if it has markdown code blocks
        response_text = response.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        result = json.loads(response_text)
        
        # Validate required fields
        required_fields = ["todays_insight", "reflect_on", "another_perspective", "closing"]
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field: {field}")
        
        # Map 'closing' to 'closing_line' for consistency
        return {
            "todays_insight": result["todays_insight"],
            "reflect_on": result["reflect_on"],
            "another_perspective": result["another_perspective"],
            "closing_line": result.get("closing", result.get("closing_line", "Your journal awaits."))
        }
    
    try:
        # First attempt
        user_prompt = build_user_prompt(is_retry=False)
        result = await call_llm(user_prompt, is_retry=False)
        
        # Validate for forbidden terms
        is_valid, found_terms = validate_reflection_content(result)
        
        if is_valid:
            logger.info("LLM reflection generated successfully (first attempt)")
            return result
        
        # First attempt failed validation - retry with stricter prompt
        logger.warning(f"LLM reflection contained forbidden terms: {found_terms}. Retrying with stricter prompt.")
        
        user_prompt_retry = build_user_prompt(is_retry=True, found_terms=found_terms)
        result_retry = await call_llm(user_prompt_retry, is_retry=True)
        
        # Validate retry result
        is_valid_retry, found_terms_retry = validate_reflection_content(result_retry)
        
        if is_valid_retry:
            logger.info("LLM reflection generated successfully (second attempt)")
            return result_retry
        
        # Second attempt also failed - fall back to template
        logger.error(f"LLM reflection still contains forbidden terms after retry: {found_terms_retry}. Falling back to template.")
        return generate_personalized_reflection(onboarding_answers)
        
    except Exception as e:
        logger.error(f"LLM reflection generation failed: {str(e)}")
        logger.info("Falling back to template-based generation")
        return generate_personalized_reflection(onboarding_answers)

async def generate_random_reflection(onboarding_answers: dict = None, recent_journals: list = None, date_key: str = None) -> dict:
    """Generate a reflection using ChatGPT, with fallback to templates"""
    return await generate_reflection_with_llm(onboarding_answers, recent_journals, date_key)

# ============== Routes ==============

@api_router.get("/")
async def root():
    return {"message": "Project Mirror API"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}

# Auth Routes
@api_router.post("/auth/register")
async def register(user_data: UserRegister):
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=user_data.email.lower(),
        name=user_data.name,
        password_hash=hash_password(user_data.password)
    )
    await db.users.insert_one(user.dict())
    
    token = create_token(user.id)
    return {
        "token": token,
        "user": UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            onboarding_completed=user.onboarding_completed,
            onboarding_answers=user.onboarding_answers
        ).dict()
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email.lower()})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"])
    return {
        "token": token,
        "user": UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            onboarding_completed=user["onboarding_completed"],
            onboarding_answers=user.get("onboarding_answers")
        ).dict()
    }

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user = Depends(get_current_user)):
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        onboarding_completed=user["onboarding_completed"],
        onboarding_answers=user.get("onboarding_answers")
    )

# Onboarding Routes
@api_router.post("/onboarding/complete")
async def complete_onboarding(answers: OnboardingAnswers, user = Depends(get_current_user)):
    await db.users.update_one(
        {"id": user["id"]},
        {
            "$set": {
                "onboarding_completed": True,
                "onboarding_answers": answers.dict()
            }
        }
    )
    return {"success": True}

# Mirror Routes
@api_router.get("/mirror/today")
async def get_today_mirror(user = Depends(get_current_user)):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    content = get_mirror_content_for_date(today)
    return content

@api_router.get("/mirror/{date}")
async def get_mirror_by_date(date: str, user = Depends(get_current_user)):
    content = get_mirror_content_for_date(date)
    return content

# Daily Reflection Routes (with persistence)
class DateKeyInput(BaseModel):
    timezone_offset: Optional[int] = None  # Client timezone offset in minutes (for reference)

def get_server_date_key() -> str:
    """Get consistent date key from server UTC time"""
    return datetime.utcnow().strftime("%Y-%m-%d")

@api_router.post("/reflection/today", response_model=DailyReflectionResponse)
async def get_or_create_daily_reflection(date_input: DateKeyInput = None, user = Depends(get_current_user)):
    """Get today's reflection or create one if it doesn't exist.
    Uses server UTC date for consistency across devices."""
    
    # Always use server date for consistency
    date_key = get_server_date_key()
    user_id = user["id"]
    timezone_offset = date_input.timezone_offset if date_input else None
    
    # Check if reflection exists for today
    existing = await db.daily_reflections.find_one({
        "user_id": user_id,
        "date_key": date_key
    })
    
    if existing:
        return DailyReflectionResponse(**existing)
    
    # Get user's onboarding answers for personalization
    onboarding_answers = user.get("onboarding_answers")
    
    # Get recent journal entries (last 3) for context
    recent_journals = await db.journal_entries.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(3).to_list(3)
    
    # Generate new personalized reflection using ChatGPT
    reflection_content = await generate_random_reflection(
        onboarding_answers, 
        recent_journals,
        date_key
    )
    
    reflection = DailyReflection(
        user_id=user_id,
        date_key=date_key,
        timezone_offset=timezone_offset,
        **reflection_content
    )
    
    await db.daily_reflections.insert_one(reflection.dict())
    return DailyReflectionResponse(**reflection.dict())

@api_router.post("/reflection/regenerate", response_model=DailyReflectionResponse)
async def regenerate_daily_reflection(date_input: DateKeyInput = None, user = Depends(get_current_user)):
    """Regenerate today's reflection (overwrites existing).
    Uses server UTC date for consistency across devices."""
    
    # Always use server date for consistency
    date_key = get_server_date_key()
    user_id = user["id"]
    timezone_offset = date_input.timezone_offset if date_input else None
    
    # Get user's onboarding answers for personalization
    onboarding_answers = user.get("onboarding_answers")
    
    # Get recent journal entries (last 3) for context
    recent_journals = await db.journal_entries.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(3).to_list(3)
    
    # Generate new personalized reflection content using ChatGPT
    reflection_content = await generate_random_reflection(
        onboarding_answers,
        recent_journals,
        date_key
    )
    
    # Check if reflection exists
    existing = await db.daily_reflections.find_one({
        "user_id": user_id,
        "date_key": date_key
    })
    
    if existing:
        # Update existing
        await db.daily_reflections.update_one(
            {"user_id": user_id, "date_key": date_key},
            {"$set": {
                **reflection_content,
                "timezone_offset": timezone_offset,
                "created_at": datetime.utcnow()  # Reset timestamp on regenerate
            }}
        )
        updated = await db.daily_reflections.find_one({
            "user_id": user_id,
            "date_key": date_key
        })
        return DailyReflectionResponse(**updated)
    else:
        # Create new
        reflection = DailyReflection(
            user_id=user_id,
            date_key=date_key,
            timezone_offset=timezone_offset,
            **reflection_content
        )
        await db.daily_reflections.insert_one(reflection.dict())
        return DailyReflectionResponse(**reflection.dict())

# Journal Routes
@api_router.get("/journal", response_model=List[JournalEntry])
async def get_journal_entries(user = Depends(get_current_user)):
    entries = await db.journal_entries.find(
        {"user_id": user["id"]}
    ).sort("created_at", -1).to_list(100)
    return [JournalEntry(**entry) for entry in entries]

@api_router.post("/journal", response_model=JournalEntry)
async def create_journal_entry(entry_data: JournalEntryCreate, user = Depends(get_current_user)):
    entry = JournalEntry(
        user_id=user["id"],
        content=entry_data.content
    )
    await db.journal_entries.insert_one(entry.dict())
    return entry

@api_router.get("/journal/{entry_id}", response_model=JournalEntry)
async def get_journal_entry(entry_id: str, user = Depends(get_current_user)):
    entry = await db.journal_entries.find_one({"id": entry_id, "user_id": user["id"]})
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return JournalEntry(**entry)

@api_router.put("/journal/{entry_id}", response_model=JournalEntry)
async def update_journal_entry(entry_id: str, entry_data: JournalEntryUpdate, user = Depends(get_current_user)):
    result = await db.journal_entries.update_one(
        {"id": entry_id, "user_id": user["id"]},
        {"$set": {"content": entry_data.content, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    entry = await db.journal_entries.find_one({"id": entry_id})
    return JournalEntry(**entry)

@api_router.delete("/journal/{entry_id}")
async def delete_journal_entry(entry_id: str, user = Depends(get_current_user)):
    result = await db.journal_entries.delete_one({"id": entry_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"success": True}

# Lenses Routes
@api_router.get("/lenses")
async def get_lenses(user = Depends(get_current_user)):
    # Return simplified list for overview
    return [{
        "id": lens["id"],
        "title": lens["title"],
        "icon": lens["icon"],
        "summary": lens["summary"],
        "is_dynamic_framework": lens.get("is_dynamic_framework", False),
        "dynamic_note": lens.get("dynamic_note")
    } for lens in LENSES_CONTENT]

@api_router.get("/lenses/{lens_id}")
async def get_lens_detail(lens_id: str, user = Depends(get_current_user)):
    lens = next((l for l in LENSES_CONTENT if l["id"] == lens_id), None)
    if not lens:
        raise HTTPException(status_code=404, detail="Lens not found")
    # Return lens without snapshot_prompt (that's internal)
    result = {k: v for k, v in lens.items() if k != "snapshot_prompt"}
    return result

# Personalized Snapshot System Prompt
SNAPSHOT_SYSTEM_PROMPT = """You are generating a personalized "Your Snapshot" for a self-reflection lens in Project Mirror.

=== PROJECT MIRROR "EPIPHANY NARRATIVE" STYLE ===

Your snapshot MUST follow this structure:

1. START WITH LIVED EXPERIENCE
   Begin with something the user might recognize from their daily life based on their onboarding answers.
   "You might be someone who..." or "There's a quality in how you..."

2. NAME THE PATTERN GENTLY
   Connect what you noticed to a pattern, without labeling or diagnosing.
   "This could show up as..." or "Some people with this tendency notice..."

3. OFFER A REFRAMING
   Give a perspective that could create an "aha" moment of self-recognition.
   Not prediction or advice - just a mirror that helps them see themselves.

=== ABSOLUTE RULES ===

1. Frame everything as PATTERNS TO OBSERVE, not fixed identity
2. Use language like "you might notice...", "there may be a tendency...", "one pattern that could be present..."
3. NEVER make predictions or give advice
4. NEVER assign specific types, numbers, signs, or levels
5. NO mystical, cosmic, or destiny language
6. Keep the response to 100-150 words
7. Write in second person ("you")

The goal is RESONANCE - they should think "yes, that's exactly it" not "I learned a fact about myself."

Output a warm, grounded reflection paragraph based on the user's onboarding context and the specific lens."""

@api_router.get("/lenses/{lens_id}/snapshot")
async def get_lens_snapshot(lens_id: str, user = Depends(get_current_user)):
    """Generate a personalized snapshot for a lens based on user's onboarding answers"""
    lens = next((l for l in LENSES_CONTENT if l["id"] == lens_id), None)
    if not lens:
        raise HTTPException(status_code=404, detail="Lens not found")
    
    # Check for cached snapshot
    cached = await db.lens_snapshots.find_one({
        "user_id": user["id"],
        "lens_id": lens_id
    })
    
    if cached:
        return {"snapshot": cached["snapshot"], "cached": True}
    
    # Get onboarding answers
    onboarding_answers = user.get("onboarding_answers", {})
    
    # Special handling for Levels of Consciousness - it's dynamic
    if lens_id == "levels-of-consciousness":
        snapshot = (
            "This lens works differently from the others. Rather than offering you a fixed reading, "
            "Project Mirror uses this framework dynamically—observing patterns in your reflections "
            "and journaling to calibrate how it speaks with you. Based on what you've shared so far, "
            "the app will adapt its depth, complexity, and perspective over time. You won't be assigned "
            "a 'level'—instead, the Mirror learns to meet you where you are on any given day, "
            "honoring that growth isn't linear and that you contain multitudes."
        )
        return {"snapshot": snapshot, "cached": False, "is_dynamic": True}
    
    # Generate snapshot with LLM
    if not EMERGENT_LLM_KEY:
        return {"snapshot": "Personalized snapshot unavailable. Please try again later.", "cached": False}
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Build context
        context_parts = [
            f"LENS: {lens['title']}",
            f"LENS CONTEXT: {lens.get('snapshot_prompt', 'Generate a personalized reflection for this lens.')}",
            "",
            "USER'S ONBOARDING ANSWERS:",
        ]
        
        if onboarding_answers:
            context_parts.append(f"- Relationship with self: {onboarding_answers.get('relationship_with_self', 'not specified')}")
            context_parts.append(f"- Preferred reflection style: {onboarding_answers.get('reflection_style', 'not specified')}")
            context_parts.append(f"- Desired depth: {onboarding_answers.get('desired_depth', 'moderate')}")
            context_parts.append(f"- Relationship to uncertainty: {onboarding_answers.get('uncertainty_relationship', 'not specified')}")
            context_parts.append(f"- Intention for using app: {onboarding_answers.get('intention', 'self understanding')}")
        else:
            context_parts.append("(No onboarding answers available - generate a warm, general reflection)")
        
        context_parts.append("")
        context_parts.append("Generate a personalized 'Your Snapshot' paragraph (100-150 words).")
        
        user_prompt = "\n".join(context_parts)
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"snapshot-{lens_id}-{user['id'][:8]}",
            system_message=SNAPSHOT_SYSTEM_PROMPT
        ).with_model("openai", "gpt-4o")
        
        response = await chat.send_message(UserMessage(text=user_prompt))
        snapshot = response.strip()
        
        # Cache the snapshot
        await db.lens_snapshots.update_one(
            {"user_id": user["id"], "lens_id": lens_id},
            {"$set": {
                "user_id": user["id"],
                "lens_id": lens_id,
                "snapshot": snapshot,
                "created_at": datetime.utcnow()
            }},
            upsert=True
        )
        
        return {"snapshot": snapshot, "cached": False}
        
    except Exception as e:
        logger.error(f"Failed to generate lens snapshot: {str(e)}")
        return {"snapshot": "Unable to generate personalized snapshot at this time.", "cached": False}

@api_router.post("/lenses/{lens_id}/snapshot/regenerate")
async def regenerate_lens_snapshot(lens_id: str, user = Depends(get_current_user)):
    """Regenerate the personalized snapshot for a lens"""
    # Delete cached snapshot
    await db.lens_snapshots.delete_one({
        "user_id": user["id"],
        "lens_id": lens_id
    })
    # Generate new one
    return await get_lens_snapshot(lens_id, user)

# ============== Lens Chat Routes ==============

class LensChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    lens_key: str  # "astrology", "human_design", "numerology", "consciousness"
    role: str  # "user" | "assistant"
    message_text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LensChatMessageResponse(BaseModel):
    id: str
    lens_key: str
    role: str
    message_text: str
    created_at: datetime

class ChatMessageInput(BaseModel):
    message: str

# Map lens IDs to chat keys
LENS_CHAT_KEYS = {
    "true-sidereal-astrology": "astrology",
    "human-design": "human_design",
    "numerology": "numerology",
    "levels-of-consciousness": "consciousness"
}

# Lens chat system prompts - strict guardrails for non-deterministic, narrative-driven responses
LENS_CHAT_BASE_PROMPT = """You are a thoughtful guide within Project Mirror, helping users explore the {lens_name} framework.

=== USER MEMORY & TIMELINE AWARENESS ===

You have access to a structured memory layer that may include:
- Onboarding answers (their relationship to self, reflection style, desired depth, uncertainty tolerance, intention)
- Recent journal entries (themes, concerns, what's alive for them)
- This lens's chat history (what you've already discussed)
- Their personalized snapshot for this lens (patterns already identified)

MEMORY USAGE RULES:

1. AVOID REPETITION
   - Don't re-explain concepts you've already covered in this conversation
   - Reference prior discussions: "Building on what we explored earlier..."
   - If they ask something you've addressed, acknowledge it: "We touched on this before—would you like to go deeper, or explore a different angle?"

2. REFERENCE THEMES GENTLY
   - Never quote journal entries verbatim unless explicitly asked
   - Use soft references: "This echoes something you reflected on earlier"
   - Connect dots: "There seems to be a thread here with what you mentioned about..."
   - Reference onboarding context naturally: "Given your preference for [depth/style], let me frame this..."

3. ALLOW EVOLUTION
   - Do NOT assume consistency—people grow and change
   - If something contradicts earlier input, don't call it out as inconsistency
   - Hold space for: "You might be in a different place now than when you wrote that"
   - Memory deepens relevance, it doesn't constrain identity

TIMELINE AWARENESS:

Treat their experience as a journey unfolding over time. When appropriate, use progression language:

- "Earlier you were exploring... and now you're asking about..."
- "Recently you've been focusing on [theme from journals]..."
- "When you first came to this lens, you asked about... it's interesting that you're now curious about..."
- "Over our conversations, there's a pattern emerging around..."

WHAT TO NOTICE IN THEIR CONTEXT:
- Recurring themes in journal entries (what keeps showing up?)
- Emotional tone (are they seeking clarity? comfort? challenge?)
- Where they are in their exploration (new to this lens? deep in it?)
- What they've been wrestling with lately

USE MEMORY TO:
- Skip unnecessary preamble when they're clearly advanced
- Offer continuity: "This connects to the question you asked last time about..."
- Validate their journey: "You've been sitting with this for a while now..."
- Personalize examples based on what you know matters to them

DO NOT USE MEMORY TO:
- Box them into past statements
- Quote them back to themselves without permission
- Assume they still feel the same way
- Create pressure to be consistent

=== CROSS-LENS ENVELOPE LOGIC ===

DEFAULT MODE: LENS-ANCHORED
You are currently on the {lens_name} page. By default, ALL responses should be centered on {lens_name} only.
Do NOT bring in other frameworks unless explicitly invited.

CROSS-LENS ACTIVATION:
Cross-lens reasoning is activated ONLY when the user explicitly asks in THAT specific message.
Examples of explicit triggers:
- "How does my astrology add to this?"
- "Can you look at this through another lens?"
- "How does this connect across frameworks?"
- "What would [other lens] say about this?"
- "How do these systems relate?"

DURING A CROSS-LENS RESPONSE:
1. Keep {lens_name} as the PRIMARY ANCHOR (60-70% of response)
2. Introduce at most ONE additional lens to add perspective
3. Do NOT equal-weight all frameworks or overwhelm with multiple systems
4. Use framing language:
   - "From a {lens_name} perspective, [main insight]..."
   - "If we briefly widen the view through [other lens]..."
   - "Another lens that can add texture here is..."
   - "Interestingly, [other lens] might frame this as..."

⚠️ AUTO-RETURN RULE (CRITICAL):
After completing ANY cross-lens response, you AUTOMATICALLY return to single-lens mode.
- The next response defaults back to {lens_name} only
- Cross-lens mode is a ONE-RESPONSE state, not persistent
- User does NOT need to manually exit or say "go back to single lens"
- Each new message starts fresh in lens-anchored mode
- Cross-lens only activates again if the user EXPLICITLY requests it again in their next message

Example flow:
1. User asks about Human Design → Respond with HD only ✓
2. User asks "How does astrology relate?" → Cross-lens response (HD primary + astrology layer) ✓
3. User asks follow-up question → Back to HD only (auto-return) ✓
4. User asks "What about numerology here?" → Cross-lens response (HD primary + numerology layer) ✓
5. User asks another question → Back to HD only (auto-return) ✓

WHEN CROSS-LENS IS NOT REQUESTED IN THE CURRENT MESSAGE:
Stay completely within {lens_name}. Do not mention other frameworks.
Even if the PREVIOUS response was cross-lens, return to single-lens mode.

AVAILABLE LENSES FOR CROSS-REFERENCE:
- True Sidereal Astrology: cycles, rhythms, celestial patterns
- Human Design: energy types, decision-making, strategy
- Numerology: number symbolism, life cycles, themes
- Levels of Consciousness: developmental stages, awareness expansion

IMPORTANT: The Mirror (home screen) is ALWAYS framework-blind. If someone asks "what does my mirror say about this?" - respond that the Mirror doesn't use frameworks, only the Lenses do.

=== PROJECT MIRROR "EPIPHANY NARRATIVE" STYLE ===

Your responses MUST follow this exact structure:

1. START WITH THE LIVED EXPERIENCE
   Begin by describing what something feels like in daily life. Use sensory, relatable language.
   Example: "You know that feeling when you've said yes to something and immediately felt a heaviness in your chest..."

2. NAME THE PATTERN GENTLY
   Identify what might be happening without labeling or diagnosing.
   Use phrases like: "There might be a pattern here..." or "Some people notice that..."

3. OFFER A REFRAMING STORY
   Share a perspective shift or metaphor that could trigger an "aha" moment.
   The goal is resonance and self-recognition, not instruction.

4. END WITH A DEEPER QUESTION + OPTIONAL EXPERIMENT
   - One question that invites genuine reflection
   - One small experiment they could try (always framed as optional)

=== ABSOLUTE RULES ===

1. NON-DETERMINISTIC: Never state anything as certain. Use "might," "could," "one way to see this..."
2. NON-PREDICTIVE: NEVER make predictions. If asked, say: "I can't predict outcomes, but we can explore what you're noticing."
3. NON-DIRECTIVE: NEVER tell users what to do. Frame everything as invitation.
4. NO IDENTITY CLAIMS: Never say "you are" - use "you might notice," "there may be a tendency"
5. NO MYSTICAL LANGUAGE: Stay grounded in everyday experience. No cosmic, destiny, or fate language.
6. GOAL IS RESONANCE: You're not teaching facts - you're offering mirrors for self-recognition.

=== GUARDRAIL RESPONSES ===

If user asks for prediction: "I can't predict outcomes, but I'm curious what you're already sensing about this situation."
If user asks "what am I?": "Rather than a label, let's explore what you've been noticing about yourself lately."
If user wants advice: "Instead of advice, I can offer a different way to look at this. Would that be helpful?"

Keep responses warm and grounded. The best response leaves them thinking "yes, that's exactly it" - not "I learned a fact." """

LENS_CHAT_PROMPTS = {
    "astrology": LENS_CHAT_BASE_PROMPT.format(lens_name="True Sidereal Astrology") + """

LENS-SPECIFIC CONTEXT:
True Sidereal Astrology looks at where celestial bodies actually are in the sky. It's about noticing cycles and rhythms, not predicting fate.

CROSS-LENS CONNECTIONS (only use when explicitly invited):
- With Human Design: Both systems use birth data; astrology adds cyclical/seasonal context to HD's energetic blueprint
- With Numerology: Planetary cycles can echo personal year cycles
- With Consciousness: Moon phases and transits as opportunities for awareness expansion

EPIPHANY NARRATIVE EXAMPLES FOR THIS LENS:

"You might have noticed there are times when everything feels like it's moving fast—decisions come easily, energy is high. And other times when you need to slow down, even when nothing external has changed. Some people find it interesting to track these rhythms alongside moon phases—not because the moon 'causes' anything, but because patterns become visible when we have a framework to notice them."

TOPICS YOU CAN EXPLORE:
- Cyclical patterns in energy and mood (as observation, not causation)
- How seasonal changes might mirror internal shifts
- The difference between sidereal and tropical systems as perspectives, not truths""",

    "human_design": LENS_CHAT_BASE_PROMPT.format(lens_name="Human Design") + """

LENS-SPECIFIC CONTEXT:
Human Design offers language for how energy might naturally flow for different people. It's an experiment to try, not an identity to adopt.

CROSS-LENS CONNECTIONS (only use when explicitly invited):
- With Astrology: HD uses birth data; astrology can add cyclical timing context to when certain energies feel stronger
- With Numerology: Profile numbers can echo numerological themes
- With Consciousness: Type/Strategy relates to where someone might be in their developmental journey

EPIPHANY NARRATIVE EXAMPLES FOR THIS LENS:

"Think about the last time you made a decision that turned out well. Not the logic behind it—but what it felt like in your body in the moment before you decided. Was there a gut sensation? An emotional wave that needed to settle? A sudden clarity? Human Design suggests we each have a 'home base' for these signals, and that learning to recognize yours can reduce the friction of constantly second-guessing yourself."

"You know that exhaustion that comes from trying to be the one who starts everything? Some people are designed to initiate—they have sustainable energy for it. Others aren't, and when they force themselves into that role, it's like running uphill. Not wrong, just... harder than it needs to be."

TOPICS YOU CAN EXPLORE:
- How decision-making feels in the body (not what's "correct")
- The difference between initiating and responding energy
- What environments feel draining versus supportive""",

    "numerology": LENS_CHAT_BASE_PROMPT.format(lens_name="Numerology") + """

LENS-SPECIFIC CONTEXT:
Numerology uses numbers as a symbolic language for reflection. The numbers point to themes worth noticing, not fixed truths.

CROSS-LENS CONNECTIONS (only use when explicitly invited):
- With Astrology: Personal year cycles can align with planetary transits
- With Human Design: Profile numbers carry similar archetypal themes
- With Consciousness: Number patterns can reflect developmental themes

EPIPHANY NARRATIVE EXAMPLES FOR THIS LENS:

"Have you ever noticed how some years feel like everything is beginning—new relationships, new projects, a sense of starting fresh? And other years feel like things are ending, falling away, or asking to be released? Numerology maps these onto 9-year cycles, not because the numbers cause anything, but because having a framework can help you recognize where you are and stop fighting the current."

"There's something interesting about the number themes in your life. Not 'you are a 7'—but 'what if the theme of seeking, questioning, and needing time alone keeps appearing because it's genuinely part of your path, not something to fix?'"

TOPICS YOU CAN EXPLORE:
- Recurring themes that might connect to number patterns
- Personal year cycles as lenses for reflection
- How number symbolism can offer language for what you're already experiencing""",

    "consciousness": LENS_CHAT_BASE_PROMPT.format(lens_name="Levels of Consciousness") + """

LENS-SPECIFIC CONTEXT:
This framework maps how awareness can expand over time. It's not about being "higher" - each stage has gifts. People access different levels in different contexts.

CROSS-LENS CONNECTIONS (only use when explicitly invited):
- With Human Design: Type and Strategy can reflect current developmental focus
- With Astrology: Outer planet transits often correlate with consciousness shifts
- With Numerology: Life path themes can echo developmental patterns

EPIPHANY NARRATIVE EXAMPLES FOR THIS LENS:

"You might notice that some conversations leave you feeling expanded—like there's more room inside you than before. Others feel contracting, like you're defending something. This isn't about the other person being 'wrong'—it's information about where your edges are, where growth is being invited."

"There's a particular kind of discomfort that comes right before a perspective shift. It feels like everything you believed is being questioned, and there's nothing solid to stand on. This isn't a problem to solve—it's often what growth feels like from the inside. The old way of seeing isn't wrong; it's just becoming one perspective among many."

CRITICAL: NEVER assign the user a level. If asked "what level am I?", respond with lived experience:
"I notice you're asking about where you 'are,' which is natural. But here's the thing—you probably access different perspectives in different situations. The more interesting question might be: when do you feel most spacious in your thinking, and what tends to make you contract?" """
}

@api_router.get("/lenses/{lens_id}/chat", response_model=List[LensChatMessageResponse])
async def get_lens_chat_history(lens_id: str, user = Depends(get_current_user)):
    """Get chat history for a specific lens"""
    lens_key = LENS_CHAT_KEYS.get(lens_id)
    if not lens_key:
        raise HTTPException(status_code=404, detail="Lens not found")
    
    messages = await db.lens_chat_messages.find({
        "user_id": user["id"],
        "lens_key": lens_key
    }).sort("created_at", 1).to_list(100)
    
    return [LensChatMessageResponse(**msg) for msg in messages]

@api_router.post("/lenses/{lens_id}/chat", response_model=List[LensChatMessageResponse])
async def send_lens_chat_message(lens_id: str, chat_input: ChatMessageInput, user = Depends(get_current_user)):
    """Send a message to the lens chatbot and get a response with strict guardrails"""
    lens_key = LENS_CHAT_KEYS.get(lens_id)
    if not lens_key:
        raise HTTPException(status_code=404, detail="Lens not found")
    
    lens = next((l for l in LENSES_CONTENT if l["id"] == lens_id), None)
    if not lens:
        raise HTTPException(status_code=404, detail="Lens not found")
    
    # Save user message
    user_message = LensChatMessage(
        user_id=user["id"],
        lens_key=lens_key,
        role="user",
        message_text=chat_input.message
    )
    await db.lens_chat_messages.insert_one(user_message.dict())
    
    # Generate AI response
    assistant_response_text = "I'm unable to respond right now. Please try again later."
    
    if EMERGENT_LLM_KEY:
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            # Get conversation history for context
            history = await db.lens_chat_messages.find({
                "user_id": user["id"],
                "lens_key": lens_key
            }).sort("created_at", 1).to_list(20)
            
            # Build conversation context
            conversation = []
            for msg in history[:-1]:  # Exclude the message we just added
                conversation.append(f"{msg['role'].upper()}: {msg['message_text']}")
            
            # ============== LENS CONTEXT HEADER ==============
            # Build comprehensive context for personalization
            
            # 1. Lens information
            lens_context = [
                "=== LENS CONTEXT HEADER ===",
                f"LENS KEY: {lens_key}",
                f"LENS TITLE: {lens['title']}",
                f"LENS SUMMARY: {lens['summary']}",
            ]
            
            # 2. User's personalized snapshot for this lens (if available)
            try:
                cached_snapshot = await db.lens_snapshots.find_one({
                    "user_id": user["id"],
                    "lens_id": lens_id
                })
                if cached_snapshot and cached_snapshot.get("snapshot"):
                    lens_context.append(f"\nUSER'S COMPUTED SNAPSHOT FOR THIS LENS:\n{cached_snapshot['snapshot']}")
                else:
                    lens_context.append("\nUSER'S COMPUTED SNAPSHOT: Not computed yet")
            except Exception:
                lens_context.append("\nUSER'S COMPUTED SNAPSHOT: Not available")
            
            # 3. Onboarding answers
            onboarding = user.get("onboarding_answers", {})
            if onboarding:
                lens_context.append("\nONBOARDING ANSWERS:")
                lens_context.append(f"- Relationship with self: {onboarding.get('relationship_with_self', 'not specified')}")
                lens_context.append(f"- Reflection style: {onboarding.get('reflection_style', 'not specified')}")
                lens_context.append(f"- Desired depth: {onboarding.get('desired_depth', 'moderate')}")
                lens_context.append(f"- Uncertainty relationship: {onboarding.get('uncertainty_relationship', 'not specified')}")
                lens_context.append(f"- Intention: {onboarding.get('intention', 'not specified')}")
            else:
                lens_context.append("\nONBOARDING ANSWERS: Not completed")
            
            # 4. Recent journal entries (last 1-3)
            recent_journals = []
            try:
                recent_journals = await db.journal_entries.find(
                    {"user_id": user["id"]}
                ).sort("created_at", -1).limit(3).to_list(3)
                
                if recent_journals:
                    lens_context.append("\nRECENT JOURNAL ENTRIES (for context, most recent first):")
                    for i, entry in enumerate(recent_journals):
                        content = entry.get('content', '')[:300]
                        if len(entry.get('content', '')) > 300:
                            content += "..."
                        lens_context.append(f"Entry {i+1}: {content}")
                else:
                    lens_context.append("\nRECENT JOURNAL ENTRIES: None yet")
            except Exception:
                lens_context.append("\nRECENT JOURNAL ENTRIES: Unable to retrieve")
            
            # 5. Dynamic Depth Inference (internal - not shown to user)
            depth_result = await infer_interaction_depth(
                user=user,
                current_message=chat_input.message,
                recent_journals=recent_journals
            )
            
            lens_context.append("=== END LENS CONTEXT HEADER ===\n")
            
            # Build system prompt with lens-specific guidance AND depth adaptation
            system_prompt = LENS_CHAT_PROMPTS.get(lens_key, LENS_CHAT_BASE_PROMPT.format(lens_name=lens['title']))
            system_prompt += "\n" + depth_result.get_adaptation_instructions()
            
            # Build user prompt with full context and history
            user_prompt_parts = ["\n".join(lens_context)]
            
            if conversation:
                user_prompt_parts.append("CONVERSATION HISTORY:")
                user_prompt_parts.append("\n".join(conversation[-10:]))
                user_prompt_parts.append("")
            
            user_prompt_parts.append(f"USER'S CURRENT MESSAGE: {chat_input.message}")
            user_prompt_parts.append("")
            user_prompt_parts.append("Generate your response following the RESPONSE FORMAT in your instructions.")
            user_prompt_parts.append("Remember: narrative explanation, concrete examples, reflective question, optional experiment.")
            
            user_prompt = "\n".join(user_prompt_parts)
            
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"lens-chat-{lens_key}-{user['id'][:8]}",
                system_message=system_prompt
            ).with_model("openai", "gpt-4o")
            
            response = await chat.send_message(UserMessage(text=user_prompt))
            assistant_response_text = response.strip()
            
        except Exception as e:
            logger.error(f"Lens chat AI error: {str(e)}")
            assistant_response_text = "I encountered an issue generating a response. Please try again."
    
    # Save assistant message
    assistant_message = LensChatMessage(
        user_id=user["id"],
        lens_key=lens_key,
        role="assistant",
        message_text=assistant_response_text
    )
    await db.lens_chat_messages.insert_one(assistant_message.dict())
    
    # Return the two new messages
    return [
        LensChatMessageResponse(**user_message.dict()),
        LensChatMessageResponse(**assistant_message.dict())
    ]

@api_router.delete("/lenses/{lens_id}/chat")
async def clear_lens_chat_history(lens_id: str, user = Depends(get_current_user)):
    """Clear chat history for a specific lens"""
    lens_key = LENS_CHAT_KEYS.get(lens_id)
    if not lens_key:
        raise HTTPException(status_code=404, detail="Lens not found")
    
    result = await db.lens_chat_messages.delete_many({
        "user_id": user["id"],
        "lens_key": lens_key
    })
    
    return {"deleted_count": result.deleted_count}

# ============== Integrative Chat (Journal-Anchored) ==============

INTEGRATIVE_CHAT_PROMPT = """You are Project Mirror — Integrate Mode.

Your role is to help the user make sense of their lived experience over time.

You are not a predictor, not a guru, and not a problem-solver.

=== HOW YOU WORK ===

You work by:
- Noticing patterns
- Offering narrative synthesis
- Gently widening perspective
- Supporting integration across insights

You may draw from any framework (Human Design, astrology, numerology, levels of consciousness) only when relevant, and only as a lens — never as a verdict.

=== ABSOLUTE RULES ===

You must:
- Avoid "you are" identity claims
- Avoid prediction
- Avoid telling the user what to do

=== PREFERRED LANGUAGE ===

Use phrases like:
- "One way to look at this…"
- "A pattern that seems to be forming…"
- "If we connect a few threads…"
- "You might experiment with noticing…"
- "Something that stands out…"
- "There's a rhythm here that might be worth sitting with…"

=== RESPONSE STRUCTURE (DEFAULT) ===

1. REFLECT the lived experience back in narrative form
   Start with what they've shared — journals, reflections, patterns over time.
   
2. NAME a pattern or tension gently
   Don't diagnose. Just notice. "There seems to be something here around..."
   
3. OFFER a reframing story or synthesis
   Connect threads. Widen perspective. Create the conditions for insight.
   
4. ASK 1–2 deep reflective questions
   Questions that open, not close. Questions that invite genuine inquiry.
   
5. OPTIONALLY suggest an experiment
   Always optional language: "If you're curious, you might try..."
   Never prescriptive.

=== CONTEXT AVAILABLE TO YOU ===

You have access to:
- Recent journal entries (themes, emotions, what's alive)
- Recent Mirror reflections (daily insights they've received)
- Lens chat summaries (themes from their framework explorations)
- Onboarding context (how they relate to self, their intentions)

Use this context to:
- Avoid repetition
- Connect dots across time
- Reference themes gently (never quote verbatim)
- Honor their evolution

=== PHILOSOPHY ===

You respect uncertainty.
You assume people evolve.
You support insight, not certainty.

The best response creates the conditions for the user to have their own realization — not to receive your conclusion."""

class IntegrativeChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    role: str  # "user" | "assistant"
    message_text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class IntegrativeChatMessageResponse(BaseModel):
    id: str
    role: str
    message_text: str
    created_at: datetime

@api_router.get("/journal/chat", response_model=List[IntegrativeChatMessageResponse])
async def get_integrative_chat_history(user = Depends(get_current_user)):
    """Get integrative chat history for the journal section"""
    messages = await db.integrative_chat_messages.find({
        "user_id": user["id"]
    }).sort("created_at", 1).to_list(100)
    
    return [IntegrativeChatMessageResponse(**msg) for msg in messages]

@api_router.post("/journal/chat", response_model=List[IntegrativeChatMessageResponse])
async def send_integrative_chat_message(chat_input: ChatMessageInput, user = Depends(get_current_user)):
    """Send a message to the integrative chatbot and get a response"""
    
    # Save user message
    user_message = IntegrativeChatMessage(
        user_id=user["id"],
        role="user",
        message_text=chat_input.message
    )
    await db.integrative_chat_messages.insert_one(user_message.dict())
    
    # Generate AI response
    assistant_response_text = "I'm here to help you connect the threads. Let me reflect on what you've shared."
    
    if EMERGENT_LLM_KEY:
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            # ============== BUILD RICH CONTEXT ==============
            
            context_parts = ["=== USER CONTEXT FOR INTEGRATIVE CHAT ===\n"]
            
            # 1. Onboarding answers
            onboarding = user.get("onboarding_answers", {})
            if onboarding:
                context_parts.append("ONBOARDING CONTEXT:")
                context_parts.append(f"- Relationship with self: {onboarding.get('relationship_with_self', 'not specified')}")
                context_parts.append(f"- Reflection style: {onboarding.get('reflection_style', 'not specified')}")
                context_parts.append(f"- Desired depth: {onboarding.get('desired_depth', 'moderate')}")
                context_parts.append(f"- Uncertainty tolerance: {onboarding.get('uncertainty_relationship', 'not specified')}")
                context_parts.append(f"- Intention: {onboarding.get('intention', 'not specified')}")
                context_parts.append("")
            
            # 2. Recent journal entries (last 5)
            try:
                recent_journals = await db.journal_entries.find(
                    {"user_id": user["id"]}
                ).sort("created_at", -1).limit(5).to_list(5)
                
                if recent_journals:
                    context_parts.append("RECENT JOURNAL ENTRIES (themes and excerpts, most recent first):")
                    for i, entry in enumerate(recent_journals):
                        content = entry.get('content', '')[:400]
                        if len(entry.get('content', '')) > 400:
                            content += "..."
                        date_str = entry.get('created_at', datetime.utcnow()).strftime('%B %d')
                        context_parts.append(f"\nEntry from {date_str}:\n{content}")
                    context_parts.append("")
            except Exception as e:
                logger.error(f"Failed to fetch journals for integrative chat: {e}")
            
            # 3. Recent Mirror reflections (last 3)
            try:
                recent_reflections = await db.daily_reflections.find(
                    {"user_id": user["id"]}
                ).sort("created_at", -1).limit(3).to_list(3)
                
                if recent_reflections:
                    context_parts.append("RECENT MIRROR REFLECTIONS (daily insights they received):")
                    for ref in recent_reflections:
                        date_str = ref.get('date_key', 'recent')
                        insight = ref.get('todays_insight', '')[:200]
                        reflect_on = ref.get('reflect_on', '')
                        context_parts.append(f"\n{date_str}:")
                        context_parts.append(f"Insight: {insight}...")
                        context_parts.append(f"Reflection prompt: {reflect_on}")
                    context_parts.append("")
            except Exception as e:
                logger.error(f"Failed to fetch reflections for integrative chat: {e}")
            
            # 4. Lens chat summaries (recent themes from each lens)
            try:
                lens_summaries = []
                for lens_key in ["astrology", "human_design", "numerology", "consciousness"]:
                    lens_messages = await db.lens_chat_messages.find({
                        "user_id": user["id"],
                        "lens_key": lens_key
                    }).sort("created_at", -1).limit(5).to_list(5)
                    
                    if lens_messages:
                        # Extract user messages to understand themes
                        user_msgs = [m['message_text'][:150] for m in lens_messages if m['role'] == 'user'][:3]
                        if user_msgs:
                            lens_name = {
                                "astrology": "True Sidereal Astrology",
                                "human_design": "Human Design",
                                "numerology": "Numerology",
                                "consciousness": "Levels of Consciousness"
                            }.get(lens_key, lens_key)
                            lens_summaries.append(f"{lens_name}: User has been exploring topics like: {'; '.join(user_msgs)}")
                
                if lens_summaries:
                    context_parts.append("LENS EXPLORATION THEMES (what they've been curious about in each lens):")
                    context_parts.extend(lens_summaries)
                    context_parts.append("")
            except Exception as e:
                logger.error(f"Failed to fetch lens summaries for integrative chat: {e}")
            
            # 5. Integrative chat history
            try:
                chat_history = await db.integrative_chat_messages.find({
                    "user_id": user["id"]
                }).sort("created_at", 1).to_list(20)
                
                conversation = []
                for msg in chat_history[:-1]:  # Exclude the message we just added
                    conversation.append(f"{msg['role'].upper()}: {msg['message_text']}")
                
                if conversation:
                    context_parts.append("CONVERSATION HISTORY:")
                    context_parts.extend(conversation[-10:])
                    context_parts.append("")
            except Exception as e:
                logger.error(f"Failed to fetch integrative chat history: {e}")
            
            context_parts.append("=== END USER CONTEXT ===\n")
            context_parts.append(f"USER'S CURRENT MESSAGE: {chat_input.message}")
            context_parts.append("")
            context_parts.append("Generate your response following the Epiphany Narrative style in your instructions.")
            
            user_prompt = "\n".join(context_parts)
            
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"integrative-chat-{user['id'][:8]}",
                system_message=INTEGRATIVE_CHAT_PROMPT
            ).with_model("openai", "gpt-4o")
            
            response = await chat.send_message(UserMessage(text=user_prompt))
            assistant_response_text = response.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate integrative chat response: {str(e)}")
            assistant_response_text = "I'm having trouble connecting right now. Could you share more about what's on your mind, and I'll do my best to help you see the patterns?"
    
    # Save assistant response
    assistant_message = IntegrativeChatMessage(
        user_id=user["id"],
        role="assistant",
        message_text=assistant_response_text
    )
    await db.integrative_chat_messages.insert_one(assistant_message.dict())
    
    # Return the new messages
    return [
        IntegrativeChatMessageResponse(**user_message.dict()),
        IntegrativeChatMessageResponse(**assistant_message.dict())
    ]

@api_router.delete("/journal/chat")
async def clear_integrative_chat_history(user = Depends(get_current_user)):
    """Clear integrative chat history"""
    result = await db.integrative_chat_messages.delete_many({
        "user_id": user["id"]
    })
    return {"deleted_count": result.deleted_count}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
