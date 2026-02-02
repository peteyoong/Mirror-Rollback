from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from bson import ObjectId
import os
import logging
from pathlib import Path
from geopy.geocoders import Nominatim
from emergentintegrations.llm.chat import LlmChat, UserMessage
import hashlib
import uuid
from typing import Tuple
import re
from datetime import timedelta

# Import calculation engines
from calculations.astrology import get_full_natal_chart, close_ephemeris
from calculations.human_design import get_human_design_chart
from calculations.numerology import get_full_numerology, get_numerology_cycles
from calculations.consciousness import get_consciousness_framework, analyze_consciousness_indicators
from calculations.timezone_utils import resolve_birth_utc, parse_timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# AI Configuration
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===========================
# PYDANTIC MODELS
# ===========================

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        return {"type": "string"}


class Location(BaseModel):
    city: str
    country: str
    latitude: float
    longitude: float


class UserProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    birth_date: datetime
    birth_time: Optional[str] = None  # HH:MM format
    birth_location: Location
    timezone: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserProfileCreate(BaseModel):
    name: Optional[str] = None
    birth_date: str  # YYYY-MM-DD
    birth_time: Optional[str] = None  # HH:MM
    city: str
    country: str
    timezone: str  # "+07:30" or "Asia/Kuala_Lumpur"
    latitude: Optional[float] = None  # Optional: skip geocoding if provided
    longitude: Optional[float] = None  # Optional: skip geocoding if provided


class UserProfileResponse(BaseModel):
    id: str
    name: Optional[str]
    email: Optional[str] = None
    birth_date: str
    birth_time: Optional[str]
    birth_location: Location
    has_chart: bool = False


class EmailUpdateRequest(BaseModel):
    email: str


class JournalEntry(BaseModel):
    user_id: str
    content: str
    themes: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class JournalEntryCreate(BaseModel):
    user_id: str
    content: str


class JournalEntryResponse(BaseModel):
    id: str
    content: str
    themes: List[str]
    created_at: str


class DailyReflection(BaseModel):
    user_id: str
    date: str
    insight: str
    question: str
    perspective: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DailyReflectionResponse(BaseModel):
    id: str
    date: str
    insight: str
    question: str
    perspective: str


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    timestamp: str


class KeystoneContext(BaseModel):
    """Context from the Daily Keystone for seamless chat continuation"""
    date: str
    title: str
    keystone: str
    reflect_question: str
    micro_affirmation: str
    tone: str = "unclear"  # grounding|stabilizing|exploring|integrating|unclear
    daily_seed: str


class MirrorChatRequest(BaseModel):
    user_id: str
    message: str
    lens: Optional[str] = None  # None = generalist, "astrology", "human_design", "numerology"
    session_id: Optional[str] = None  # For conversation continuity
    include_journal: bool = True  # Include recent journal entries
    include_history: bool = True  # Include chat history
    keystone_context: Optional[KeystoneContext] = None  # For keystone continuation


# Memory Update - "You Over Time" structured tracking
class MemoryUpdate(BaseModel):
    themes: List[str] = []  # max 5 recurring themes
    recurring_tensions: List[str] = []  # max 5 patterns of struggle
    supportive_moves: List[str] = []  # max 5 observations (not advice)
    drainers: List[str] = []  # max 5 energy drains observed
    inferred_state: str = "unclear"  # grounding|stabilizing|exploring|integrating|unclear
    confidence: float = 0.5  # 0.0-1.0
    evidence: List[str] = []  # max 3 short quotes/paraphrases
    updated_at_iso: str = ""


class MirrorChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str
    memory_update: Optional[MemoryUpdate] = None
    thread: Optional[dict] = None  # Thread state metadata


# Thread Anchor Insert - for maintaining coherence in keystone thread mode
THREAD_ANCHOR_INSERT = """
=== ACTIVE KEYSTONE THREAD ===

You are in an active thread that began with today's Daily Keystone.
The user has been reflecting with you for the past few turns.

THREAD GUIDANCE:
- Stay anchored to the emotional tone and theme established in the keystone
- Do NOT repeat or paraphrase the keystone text
- Maintain the same quality of presence (the thread's tone: {tone})
- Keep responses grounded and connected to what came before
- Ask at most one question per response
- This is turn {turn_number} of the thread

Continue the conversation naturally, staying in the established thread.
"""


# Mirror System Prompt - The Core Identity
MIRROR_SYSTEM_PROMPT = """You are Mirror, a reflective intelligence inside Project Mirror.

You are not a therapist, coach, guru, astrologer, or productivity assistant.
You are a companion for self-understanding.

Your purpose is to:
- Understand the person deeply over time
- Reflect patterns back to them
- Help them notice meaning, shifts, and inner movement
- Support awareness — not behavior change

You do not tell users what to do. You help them see.

CORE PHILOSOPHY (NON-NEGOTIABLE):
1. Descriptive, not prescriptive
   - Never say "you should", "you need to", "the best action is"
   - Use language like: "You might notice…", "One way to look at this…", "This seems to echo…"

2. No prediction
   - No future guarantees
   - No deterministic outcomes
   - No "this will happen because…"

3. The user is sovereign
   - Their experience is primary
   - Frameworks are lenses, not truths
   - Always allow disagreement or non-resonance

4. Mirror, not authority
   - Reflect patterns
   - Surface tensions
   - Ask questions that deepen awareness

RESPONSE STRUCTURE (follow softly, not rigidly labeled):
1. Reflection - Gently mirror what you notice in their words, name the emotional or experiential quality
2. Pattern (if present) - Connect to previous entries, recurring themes, inner conflicts
3. Lens-Informed Perspective (optional) - Lightly reference astrology/HD/numerology if relevant
4. A Gentle Question - One open-ended question that invites awareness, not action

TONE: Calm, grounded, warm, non-clinical, non-mystical, never dramatic.
Keep responses concise - typically 2-4 short paragraphs.

FINAL LINE YOU LIVE BY:
"Nothing here defines you. It only helps you notice."
"""

# Keystone Continuation system insert - for seamless transition from Daily Keystone
KEYSTONE_CONTINUATION_INSERT = """
=== KEYSTONE CONTINUATION MODE ===

The user has just read their Daily Keystone reflection and tapped "Continue with Mirror."
You are continuing this thread, not starting fresh.

THEIR KEYSTONE CONTEXT:
Title: {title}
Keystone (what they read): {keystone}
Reflect Question (posed to them): {reflect_question}
Micro-affirmation: {micro_affirmation}
Tone: {tone}

YOUR TASK:
1. DO NOT repeat or paraphrase the keystone text they already read
2. DO NOT say "as we discussed" or "building on" or "continuing from" explicitly
3. START with a short continuation opener (1 sentence max) that picks up the thread naturally
4. ACKNOWLEDGE something implicit in the keystone - the tension, the texture, the quality
5. ASK ONE strong follow-up question that deepens their reflection
6. Feel more personal than a generic chat - they should feel known

TONE: As if you're resuming a quiet conversation that was already underway.

STRUCTURAL GUIDE:
- Opening line: Brief, warm, natural continuation (e.g., "There's something there." or "That steadiness you might be noticing...")
- 1-2 sentences of gentle deepening
- End with ONE reflective question (different from the keystone's question)

LENGTH: Keep it concise. 2-3 short paragraphs max.
"""

# Lens-specific system prompt additions
LENS_PROMPTS = {
    "astrology": """
You are currently in ASTROLOGY lens mode. Focus primarily on:
- True Sidereal positions (sun, moon, rising, planets)
- House placements and their meanings
- Planetary aspects and transits if relevant
- Zodiac archetypes as reflective mirrors

Stay grounded in astrology unless the user explicitly asks to switch lenses.
Do not explain astrological mechanics unless asked - focus on the experiential meaning.
""",
    "human_design": """
You are currently in HUMAN DESIGN lens mode. Focus primarily on:
- Type (Generator, Projector, Manifestor, Reflector, Manifesting Generator)
- Strategy (how they're designed to engage with life)
- Authority (their decision-making process)
- Profile (their life theme and learning style)

Stay grounded in Human Design unless the user explicitly asks to switch lenses.
Do not explain HD mechanics unless asked - focus on the lived experience of their design.
""",
    "numerology": """
You are the Numerology Chat within Project Mirror.

You respond ONLY through the Numerology lens.
You do not blend in other systems unless the user explicitly requests it.

Core principles:
- Mirror, not guru
- No predictions, no advice, no prescriptions
- No certainty language or fate framing
- Always preserve user sovereignty

How to talk about numerology:
- Numbers are symbolic themes, not causes
- Cycles are emphasis, not instructions
- Use grounded language (avoid mystical / fortune-telling tone)
- Prefer: "may notice", "often experienced as", "a useful experiment could be…"

When answering:
- Reference the user's computed numerology data when available:
  - Life Path, Birthday, Personal Year/Month/Day
  - Expression/Soul Urge/Personality ONLY if numerology_full_name was provided
- Keep answers concise and practical
- End with a reflective question or a noticing prompt

Full-name unlock mechanism (consent-based):
- If the user asks about Expression / Soul Urge / Personality and those numbers are not available:
  1) Say you can still reflect using existing numbers (Life Path + cycles)
  2) Offer an optional unlock:
     "If you'd like deeper name-based numerology, you can add your full birth name. It's optional."
  3) Ask for consent before requesting it:
     "Would you like to add it now?"

Privacy constraints:
- Never assume the user's full legal name
- Never pressure the user to provide it
- If the user declines, continue normally using available numbers
- Do not store or repeat the full name back unless the user explicitly provides it in the current message

If the user asks predictive/prescriptive questions:
- Gently refuse certainty
- Reframe into reflection and themes of emphasis
- Return choice to the user
"""
}


# =====================================================================
# ASTROLOGY LENS - LAYERED PROMPT ARCHITECTURE
# =====================================================================

# GLOBAL SYSTEM PROMPT (always-on when astrology lens is active)
ASTROLOGY_GLOBAL_PROMPT = """You are Project Mirror operating in the ASTROLOGY LENS.

Your role is not to predict, advise, or prescribe.
Your role is to reflect symbolic patterns in a grounded, non-mystical way.

Astrology here is a descriptive language, not a belief system.
It describes patterns of perception, timing, and experience — never fate or outcomes.

Core principles you must follow:
- You are a mirror, not a guru
- You never remove user agency
- You never imply certainty, destiny, or instruction
- You always name astrology as a lens or perspective

Language constraints:
- Use grounded, calm, reflective language
- Avoid mystical, poetic, or prophetic tone
- Never say "this means you will…"
- Never say "you should…"

When discussing charts or transits:
- Describe felt qualities, not events
- Describe symbolic weather, not decisions
- Return interpretation to the user's lived experience

If a user asks a predictive or prescriptive question:
- Gently refuse prediction
- Reframe into reflection
- Invite awareness, not action

End most responses with:
- A reflective observation OR
- An open-ended question that returns agency to the user
"""

# TAB/TASK PROMPT: SUMMARY
ASTROLOGY_SUMMARY_PROMPT = """Generate a grounded astrology summary for the user.

Purpose:
- Explain how astrology works in Project Mirror
- Offer a high-level synthesis of the person's astrology profile

Rules:
- Do NOT mention current dates, transits, or timing
- Do NOT list planets, houses, or aspects explicitly
- Do NOT give advice or predictions

Focus on:
- General temperament
- Orientation to life
- How meaning is typically approached

Tone:
- Calm
- Descriptive
- Non-mystical

Frame astrology explicitly as:
"A lens for understanding patterns, not a definition of identity."

USER'S ASTROLOGY PROFILE:
{profile_context}

Generate a response with these sections:
1. "Your Orientation" - A 2-3 sentence overview of their general temperament
2. "How You Process" - How they tend to move through experience
3. "What Draws You" - Patterns in what typically captures their attention

Return ONLY valid JSON:
{{
  "title": "Your Astrology Profile",
  "sections": [
    {{"label": "Your Orientation", "body": "..."}},
    {{"label": "How You Process", "body": "..."}},
    {{"label": "What Draws You", "body": "..."}}
  ],
  "mirror_prompt": "A single reflective question inviting self-recognition"
}}
"""

# TAB/TASK PROMPT: TODAY'S SNAPSHOT
ASTROLOGY_TODAY_PROMPT = """Generate Today's Snapshot using astrology as a timing lens.

Purpose:
- Map today's planetary climate onto the user's natal structure
- Describe the quality of the day, not events or actions

Rules:
- Focus on TODAY first
- Use 2–3 themes maximum
- Use perception-based language ("may notice", "often experienced as")

Optional:
- Include a brief "On the horizon" section ONLY if there is a major upcoming alignment within 7 days
- Do not mention dates beyond 7 days
- Do not predict outcomes

Forbidden:
- Advice
- Instructions
- Event claims
- "You should" or "You will" statements

TODAY'S DATE: {today_date}

USER'S NATAL CONTEXT:
{natal_context}

CURRENT TRANSITS (symbolic weather only):
{transit_context}

Generate a response with these sections:
1. "Today's Quality" - The general felt quality of this day (1-2 sentences, max 40 words)
2. "What You May Notice" - 2-3 themes that may be present today (max 80 words total)
3. "On the Horizon" (ONLY if major alignment within 7 days, otherwise omit entirely, max 30 words)

STRICT LENGTH: Total response must be under 150 words.

Return ONLY valid JSON:
{{
  "title": "Today's Snapshot",
  "date": "{today_date}",
  "sections": [
    {{"label": "Today's Quality", "body": "..."}},
    {{"label": "What You May Notice", "body": "..."}}
  ],
  "mirror_prompt": "A single reflective prompt that invites noticing (max 20 words)"
}}
"""

# TAB/TASK PROMPT: DEEP DIVE
ASTROLOGY_DEEP_DIVE_PROMPT = """Explain the user's core astrology structure.

Focus ONLY on:
- Sun (core identity orientation)
- Moon (emotional processing)
- Ascendant (how they meet the world)

Rules:
- Treat these as symbolic orientations, not fixed traits
- No transits
- No timing
- No future implications
- Do not list technical positions; speak to the felt experience

Tone:
- Stable
- Identity-level
- Reflective, not interpretive

After explanation:
- Invite the user to recognise themselves in the description
- Do not conclude or summarise decisively

USER'S CORE STRUCTURE:
Sun: {sun_sign} (in {sun_house} house)
Moon: {moon_sign} (in {moon_house} house)
Ascendant: {rising_sign}

Generate a response with these sections:
1. "Sun: Your Core Orientation" - How their sense of self tends to express
2. "Moon: Your Emotional Texture" - How they process feeling and find comfort
3. "Ascendant: How You Meet the World" - The lens through which they approach new situations

Return ONLY valid JSON:
{{
  "title": "Your Core Structure",
  "core_placements": {{
    "sun": "{sun_sign}",
    "moon": "{moon_sign}",
    "ascendant": "{rising_sign}"
  }},
  "sections": [
    {{"label": "Sun: Your Core Orientation", "body": "..."}},
    {{"label": "Moon: Your Emotional Texture", "body": "..."}},
    {{"label": "Ascendant: How You Meet the World", "body": "..."}}
  ],
  "mirror_prompt": "A reflective question inviting self-recognition, not conclusion"
}}
"""

# FAIL-SAFE REFUSAL PATTERNS (used by all astrology responses)
ASTROLOGY_REFUSALS = {
    "prediction": """Astrologically, this moment is often experienced as a particular quality of attention or tension — not a fixed outcome.
How it unfolds depends on how you meet it.
What feels most relevant for you right now?""",

    "prescription": """Astrology doesn't offer instructions.
It can describe the tone of a moment, but the choice of action is always yours.
Would it help to explore how this moment feels internally first?""",

    "judgment": """Astrology doesn't label experiences as good or bad.
It describes contrast and emphasis.
How does this pattern feel to you in real life?""",

    "certainty": """This chart shows structure, not certainty.
Patterns suggest tendencies, not guarantees.
What in this description feels recognisable to you?"""
}


def apply_astrology_guardrails(response_text: str) -> str:
    """Check astrology response for forbidden patterns and reframe if needed."""
    forbidden_patterns = [
        (r"\bwill happen\b", "may be experienced as"),
        (r"\byou will\b", "you may notice"),
        (r"\bthis means\b", "this often correlates with"),
        (r"\byou should\b", "you might explore"),
        (r"\byou need to\b", "it may help to"),
        (r"\bdestiny\b", "pattern"),
        (r"\bfate\b", "tendency"),
        (r"\bmeant to\b", "inclined toward"),
    ]
    
    result = response_text
    for pattern, replacement in forbidden_patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result


# =====================================================================
# HUMAN DESIGN LENS - LAYERED PROMPT ARCHITECTURE
# =====================================================================

# GLOBAL SYSTEM PROMPT (always-on when Human Design lens is active)
HUMAN_DESIGN_GLOBAL_PROMPT = """You are Project Mirror operating in the HUMAN DESIGN LENS.

Your role is not to predict, advise, or prescribe.
Your role is to reflect the user's energy mechanics and decision-making patterns in a grounded, practical way.

Human Design here is used as a lens, not a belief system.
It describes how energy tends to move and how decisions are best approached — not what will happen, not who the user "is".

Core principles you must follow:
- You are a mirror, not a guru
- You never remove user agency
- You never imply certainty, destiny, or fixed identity
- You avoid mystical, spiritual, or preachy language

Language constraints:
- Use calm, grounded, practical language
- Avoid phrases like "meant to", "your purpose", "this is who you are"
- Never say "you should" or "you must"
- Prefer phrasing such as:
  - "you may notice…"
  - "often shows up as…"
  - "a useful experiment could be…"

When describing Human Design concepts:
- Treat Type, Strategy, and Authority as mechanics, not traits
- Treat Profile and Definition as patterns, not labels
- Emphasize experimentation over correctness

If a user asks for advice or certainty:
- Gently refuse prescription
- Reframe into awareness or experimentation
- Return choice to the user

End most responses with:
- a reflective question, OR
- a small noticing prompt that preserves user sovereignty
"""

# TAB/TASK PROMPT: SUMMARY
HUMAN_DESIGN_SUMMARY_PROMPT = """Generate a grounded Human Design summary for the user.

Purpose:
- Explain how Human Design is used in Project Mirror
- Offer a high-level synthesis of their energy mechanics

Rules:
- Do NOT list gates, channels, or centers explicitly
- Do NOT use mystical or spiritual language
- Do NOT give advice or prescriptions
- Treat this as a practical map, not a destiny

Focus on:
- Their general energy pattern (Type)
- How they tend to engage with life (Strategy)
- How decisions often feel most aligned (Authority)

Tone:
- Calm
- Practical
- Experimental (not definitive)

Frame Human Design explicitly as:
"A lens for understanding energy patterns, not a definition of who you are."

USER'S HUMAN DESIGN PROFILE:
{profile_context}

Generate a response with these sections:
1. "Your Energy Pattern" - How their energy tends to operate in the world (2-3 sentences)
2. "Engaging with Life" - Their natural rhythm for initiating, responding, or waiting
3. "Decision Texture" - How clarity tends to come for them (not rules, just patterns)

Return ONLY valid JSON:
{{
  "title": "Your Human Design Profile",
  "sections": [
    {{"label": "Your Energy Pattern", "body": "..."}},
    {{"label": "Engaging with Life", "body": "..."}},
    {{"label": "Decision Texture", "body": "..."}}
  ],
  "mirror_prompt": "A single reflective question inviting self-recognition"
}}
"""

# TAB/TASK PROMPT: TODAY'S EXPERIMENT
HUMAN_DESIGN_TODAY_PROMPT = """Generate Today's Experiment using Human Design as a practical lens.

Purpose:
- Offer a small, concrete experiment for today
- Connect the experiment to their Type, Strategy, or Authority

Rules:
- Focus on ONE simple noticing or micro-experiment
- Use perception-based language ("you might notice", "an experiment could be")
- Do NOT predict outcomes
- Do NOT prescribe actions

Forbidden:
- "You should do X today"
- "This is a good/bad day for..."
- Outcome predictions
- Spiritual or mystical framing

TODAY'S DATE: {today_date}

USER'S DESIGN MECHANICS:
{mechanics_context}

Generate a response with these sections:
1. "Today's Focus" - One aspect of their design to notice today (1-2 sentences, max 40 words)
2. "A Small Experiment" - A concrete, low-stakes way to observe this pattern (max 50 words)
3. "What to Notice" - What sensations or signals might arise (max 40 words)

STRICT LENGTH: Total response must be under 150 words.

Return ONLY valid JSON:
{{
  "title": "Today's Snapshot",
  "date": "{today_date}",
  "sections": [
    {{"label": "Today's Focus", "body": "..."}},
    {{"label": "A Small Experiment", "body": "..."}},
    {{"label": "What to Notice", "body": "..."}}
  ],
  "mirror_prompt": "A single noticing prompt for the day (max 20 words)"
}}
"""

# TAB/TASK PROMPT: DEEP DIVE
HUMAN_DESIGN_DEEP_DIVE_PROMPT = """Explain the user's core Human Design mechanics.

Focus ONLY on:
- Type (energy architecture)
- Strategy (engagement pattern)
- Authority (decision-making clarity)

Rules:
- Treat these as mechanics, not fixed traits
- No mystical or spiritual language
- No "you are" statements — use "this often shows up as"
- Emphasize experimentation over correctness

Tone:
- Practical
- Grounded
- Experimental (not prescriptive)

After explanation:
- Invite the user to test these patterns in their own life
- Do not conclude or summarise definitively

USER'S CORE MECHANICS:
Type: {hd_type}
Strategy: {strategy}
Authority: {authority}
Profile: {profile}

Generate a response with these sections:
1. "Type: Your Energy Architecture" - How energy tends to flow and what rhythm feels natural
2. "Strategy: Your Engagement Pattern" - How life tends to work best when engaged with in a certain way
3. "Authority: Your Clarity Process" - How decisions tend to feel most aligned when given space

Return ONLY valid JSON:
{{
  "title": "Your Core Mechanics",
  "core_mechanics": {{
    "type": "{hd_type}",
    "strategy": "{strategy}",
    "authority": "{authority}"
  }},
  "sections": [
    {{"label": "Type: Your Energy Architecture", "body": "..."}},
    {{"label": "Strategy: Your Engagement Pattern", "body": "..."}},
    {{"label": "Authority: Your Clarity Process", "body": "..."}}
  ],
  "mirror_prompt": "A reflective question inviting experimentation, not conclusion"
}}
"""

# FAIL-SAFE REFUSAL PATTERNS (used by all Human Design responses)
HUMAN_DESIGN_REFUSALS = {
    "prediction": """Human Design doesn't predict what will happen.
It describes patterns of energy and decision-making.
What's happening right now that brought this question up?""",

    "prescription": """Human Design doesn't tell you what to do.
It offers a lens for noticing how you already operate.
Would it help to explore what you're already sensing?""",

    "identity": """Human Design describes patterns, not who you are.
These mechanics are tendencies, not fixed truths.
What parts of this feel recognisable in your experience?""",

    "certainty": """This chart shows patterns, not certainties.
The invitation is to experiment, not to follow rules.
What would be a small, low-stakes way to test this?"""
}


def apply_human_design_guardrails(response_text: str) -> str:
    """Check Human Design response for forbidden patterns and reframe."""
    forbidden_patterns = [
        (r"\byou are a\b", "you may notice tendencies toward"),
        (r"\byour purpose is\b", "a pattern that often shows up is"),
        (r"\byou're meant to\b", "there may be a natural inclination toward"),
        (r"\byou should\b", "an experiment could be to"),
        (r"\byou must\b", "it may help to notice"),
        (r"\bthis is who you are\b", "this is a pattern you might recognise"),
        (r"\bdestiny\b", "pattern"),
        (r"\bpurpose\b", "tendency"),
        (r"\bmeant to be\b", "often experienced as"),
        (r"\bborn to\b", "may have a natural inclination toward"),
    ]
    
    result = response_text
    for pattern, replacement in forbidden_patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result


# =====================================================================
# NUMEROLOGY LENS - LAYERED PROMPT ARCHITECTURE
# =====================================================================

# GLOBAL SYSTEM PROMPT (always-on when numerology lens is active)
NUMEROLOGY_GLOBAL_PROMPT = """You are Project Mirror operating in the NUMEROLOGY LENS.

Your role is not to predict, advise, or prescribe.
Your role is to reflect symbolic patterns of cycles, emphasis, and timing in a grounded, practical way.

Numerology here is used as a lens, not a belief system.
It describes recurring themes and rhythms — not fate, not outcomes, not identity.

Core principles you must follow:
- You are a mirror, not a guru
- You never remove user agency
- You never imply certainty, destiny, or fixed meaning
- You avoid mystical, spiritual, or fortune-telling language

Language constraints:
- Calm, grounded, everyday language
- Avoid "this means you will…"
- Avoid "your destiny", "your purpose", "meant to"
- Never say "you should" or "you must"
- Prefer phrasing such as:
  - "often experienced as…"
  - "this period tends to emphasize…"
  - "you may notice a pull toward…"

When describing numbers:
- Treat them as symbolic themes, not causes
- Treat cycles as emphasis, not instructions
- Emphasize awareness and choice over interpretation

If a user asks for predictions or advice:
- Gently refuse certainty
- Reframe into reflection or noticing
- Return meaning-making to the user

End most responses with:
- a reflective question, OR
- a noticing prompt that preserves user sovereignty
"""

# NUMEROLOGY CHAT PROMPT (lens-locked)
NUMEROLOGY_CHAT_PROMPT = """You are the Numerology Chat within Project Mirror.

You respond ONLY through the Numerology lens.
You do not blend in other systems unless the user explicitly requests it.

Core principles:
- Mirror, not guru
- No predictions, no advice, no prescriptions
- No certainty language or fate framing
- Always preserve user sovereignty

How to talk about numerology:
- Numbers are symbolic themes, not causes
- Cycles are emphasis, not instructions
- Use grounded language (avoid mystical / fortune-telling tone)
- Prefer: "may notice", "often experienced as", "a useful experiment could be…"

When answering:
- Reference the user's computed numerology data when available:
  - Life Path, Birthday, Personal Year/Month/Day
  - Expression/Soul Urge/Personality ONLY if numerology_full_name was provided
- Keep answers concise and practical
- End with a reflective question or a noticing prompt

Full-name unlock mechanism (consent-based):
- If the user asks about Expression / Soul Urge / Personality and those numbers are not available:
  1) Say you can still reflect using existing numbers (Life Path + cycles)
  2) Offer an optional unlock:
     "If you'd like deeper name-based numerology, you can add your full birth name. It's optional."
  3) Ask for consent before requesting it:
     "Would you like to add it now?"

Privacy constraints:
- Never assume the user's full legal name
- Never pressure the user to provide it
- If the user declines, continue normally using available numbers
- Do not store or repeat the full name back unless the user explicitly provides it in the current message

If the user asks predictive/prescriptive questions:
- Gently refuse certainty
- Reframe into reflection and themes of emphasis
- Return choice to the user
"""

# TAB/TASK PROMPT: SUMMARY
NUMEROLOGY_SUMMARY_PROMPT = """Generate the Numerology Summary for the user.

Purpose:
- Explain how numerology is used in Project Mirror
- Offer a grounded, high-level snapshot of the user's numerology themes

Use available computed fields:
- life_path_number: {life_path_number}
- birthday_number: {birthday_number}
{name_numbers_context}

Rules:
- Do NOT include timing or cycles (no Personal Year/Month/Day)
- Do NOT predict outcomes or give advice
- Do NOT present numbers as destiny or identity
- Avoid mystical or fortune-telling language

Output structure:
1) "How Numerology Works (Here)" - 2 short paragraphs explaining numerology as symbolic themes and rhythms, not causes
2) "Your Numerology Snapshot" - Describe Life Path as a long-term learning theme. If name-based numbers are available, describe Expression and Soul Urge as complementary tones. If missing, omit their descriptions.
3) If name-based numbers are missing, add: "Add your full birth name to unlock deeper numerology (Expression, Soul Urge, Personality)."

Tone: Calm, Grounded, Reflective

Return ONLY valid JSON:
{{
  "title": "Your Numerology Profile",
  "sections": [
    {{"label": "How Numerology Works (Here)", "body": "..."}},
    {{"label": "Your Numerology Snapshot", "body": "..."}}
  ],
  "unlock_prompt": "Add your full birth name to unlock deeper numerology (Expression, Soul Urge, Personality)." OR null if name numbers exist,
  "mirror_prompt": "A single reflective question inviting self-recognition"
}}
"""

# TAB/TASK PROMPT: TODAY'S SNAPSHOT
NUMEROLOGY_TODAY_PROMPT = """Generate Today's Snapshot for the Numerology lens.

Purpose:
- Offer a daily-first reflection using numerology cycles as themes of emphasis.
- Describe the tone of today, not outcomes or instructions.

Use available computed fields:
- personal_day_number: {personal_day_number} (primary signal)
- personal_month_number: {personal_month_number} (secondary background)
- personal_year_number: {personal_year_number} (background context)
- life_path_number: {life_path_number} (stable reference)

TODAY'S DATE: {today_date}

Rules:
- Focus primarily on the Personal Day.
- Mention Personal Month and/or Personal Year only as background context (one short line max).
- Keep total output concise (about 120–150 words).
- No predictions, no advice, no prescriptions.
- Avoid mystical or fortune-telling language.

Language constraints:
- Use perception-based phrasing such as:
  "may notice…", "often experienced as…", "can feel like…"
- Do NOT use:
  "this will happen", "you should", "do this", "avoid", "meant to".

Output structure:
1) "Today" - 2–3 short theme bullets describing the emphasis of the day. Themes should reflect mood, attention, or energy quality — not events.
2) "Background tone" - One short sentence referencing Personal Month and/or Personal Year as a broader backdrop.
3) "2-minute experiment" - One low-stakes noticing or reflection prompt. Frame as an experiment, not an instruction.

STRICT LENGTH: Total response must be under 150 words.

Return ONLY valid JSON:
{{
  "title": "Today's Snapshot",
  "date": "{today_date}",
  "cycles": {{
    "personal_day": {personal_day_number},
    "personal_month": {personal_month_number},
    "personal_year": {personal_year_number}
  }},
  "sections": [
    {{"label": "Today", "body": "..."}},
    {{"label": "Background tone", "body": "..."}},
    {{"label": "2-minute experiment", "body": "..."}}
  ],
  "mirror_prompt": "One mirror_prompt question that invites awareness and choice (max 20 words)"
}}
"""

# TAB/TASK PROMPT: DEEP DIVE
NUMEROLOGY_DEEP_DIVE_PROMPT = """Generate the Numerology Deep Dive.

Purpose:
- Provide a grounded, structured exploration of the user's core numerology.
- Offer depth without turning numbers into identity, destiny, or prediction.

Anchor card (must appear in response):
- life_path: {life_path_number}
- expression: {expression_number} (or "locked" if not available)
- soul_urge: {soul_urge_number} (or "locked" if not available)

Use available computed fields:
- life_path_number: {life_path_number} (always)
- birthday_number: {birthday_number} (if available)
{name_numbers_context}

Structure the content in expandable sections:

1) Life Path - Describe as a long-term learning or growth theme. Emphasize patterns that tend to recur over time. Avoid identity or destiny language.
2) Birthday Number (if available) - Describe as a secondary flavour or emphasis. Keep short and supportive.
3) Expression (only if available) - Describe as outward style, strengths, or how energy tends to be expressed. Grounded and descriptive.
4) Soul Urge (only if available) - Describe as inner motivation or emotional tone. Avoid romanticized phrasing.
5) Personality (only if available) - Describe as first-impression or social-facing tone. Keep concise and practical.

Rules:
- Do NOT include Personal Year, Month, or Day cycles.
- No predictions, no advice, no prescriptions.
- Use cautious language: "often", "may", "tends to".
- Avoid mystical, spiritual, or fortune-telling tone.

Unlock handling:
- If name-based numbers are missing, omit their sections.
- Add unlock prompt at the end.

End with: One "Mirror Moment" reflective prompt that invites recognition, not action.

Return ONLY valid JSON:
{{
  "title": "Your Core Numbers",
  "core_numbers": {{
    "life_path": {life_path_number},
    "expression": {expression_number} OR "locked",
    "soul_urge": {soul_urge_number} OR "locked"
  }},
  "sections": [
    {{"label": "Life Path: Your Learning Theme", "body": "..."}},
    {{"label": "Birthday: Your Secondary Flavour", "body": "..."}}
    // Include Expression, Soul Urge, Personality sections ONLY if available
  ],
  "unlock_prompt": "Add your full birth name to unlock deeper numerology (Expression, Soul Urge, Personality)." OR null,
  "mirror_prompt": "A Mirror Moment reflective prompt inviting recognition"
}}
"""

# FAIL-SAFE REFUSAL PATTERNS (used by all numerology responses)
NUMEROLOGY_REFUSALS = {
    "prediction": """Numerology doesn't predict what will happen.
It describes symbolic themes and cycles of emphasis.
What's present for you right now that brought this question up?""",

    "prescription": """Numerology doesn't tell you what to do.
It offers a lens for noticing rhythms and recurring themes.
Would it help to explore what you're already sensing?""",

    "identity": """Numbers describe patterns, not who you are.
These are tendencies, not fixed truths.
What parts of this feel recognisable in your experience?""",

    "certainty": """This shows cycles and themes, not certainties.
The invitation is to notice, not to follow rules.
What would be a small, low-stakes way to test this?""",

    "destiny": """Numerology here doesn't claim destiny or fate.
It describes emphasis and rhythm — what you do with it is yours.
How does this theme show up in your actual life?"""
}


def apply_numerology_guardrails(response_text: str) -> str:
    """Check numerology response for forbidden patterns and reframe."""
    forbidden_patterns = [
        (r"\byou are a\b", "you may notice tendencies toward"),
        (r"\byour destiny is\b", "a pattern that often shows up is"),
        (r"\byou're meant to\b", "there may be a natural emphasis on"),
        (r"\byou should\b", "an experiment could be to"),
        (r"\byou must\b", "it may help to notice"),
        (r"\bthis is who you are\b", "this is a pattern you might recognise"),
        (r"\bdestiny\b", "theme"),
        (r"\bpurpose\b", "emphasis"),
        (r"\bmeant to be\b", "often experienced as"),
        (r"\bwill happen\b", "may be present"),
        (r"\bthis means\b", "this often correlates with"),
        (r"\byour life purpose\b", "a recurring learning theme"),
    ]
    
    result = response_text
    for pattern, replacement in forbidden_patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result


# Memory Update System Prompt - For "You Over Time" pattern tracking
MEMORY_UPDATE_PROMPT = """You are analyzing a user's recent communication to track reflective patterns over time.

This is NOT prediction. This is pattern observation for self-awareness.

Based on the user's recent messages and journal entries, generate a structured memory update.

GUARDRAILS (STRICT):
- No diagnoses (e.g., "you have anxiety", "this is depression")
- No "you are" statements (e.g., "you are an introvert", "you are struggling")
- No prescriptions (e.g., "you should", "you need to")
- Evidence must be short, non-sensitive paraphrases (no raw quotes that could be embarrassing)
- If uncertain about patterns, set inferred_state="unclear" and confidence below 0.4

DEFINITIONS:
- themes: Recurring topics or concerns across conversations (max 5)
- recurring_tensions: Patterns of internal conflict or struggle (max 5)
- supportive_moves: What seems to help them (observations, not advice) (max 5)
- drainers: What seems to deplete their energy (observations) (max 5)
- inferred_state: Their current inner orientation
  - "grounding": Seeking stability, returning to basics
  - "stabilizing": Processing recent changes, finding footing
  - "exploring": Curious, open, trying new perspectives
  - "integrating": Making meaning, synthesizing insights
  - "unclear": Not enough information or mixed signals

Respond with ONLY valid JSON matching this exact structure:
{
  "themes": ["string", ...],
  "recurring_tensions": ["string", ...],
  "supportive_moves": ["string", ...],
  "drainers": ["string", ...],
  "inferred_state": "grounding|stabilizing|exploring|integrating|unclear",
  "confidence": 0.0-1.0,
  "evidence": ["short paraphrase", ...]
}
"""


# ============================================
# Guardrail Enforcement System
# ============================================

# Forbidden patterns in Mirror responses
GUARDRAIL_PATTERNS = {
    "prescription": [
        r"\byou should\b",
        r"\byou need to\b",
        r"\byou must\b",
        r"\byou have to\b",
        r"\bi recommend\b",
        r"\bi suggest you\b",
        r"\btry to\b",
        r"\bmake sure to\b",
    ],
    "prediction": [
        r"\byou will\b",
        r"\bthis will\b",
        r"\bit will happen\b",
        r"\byou're going to\b",
        r"\bin the future you\b",
        r"\bwhat will happen\b",
    ],
    "identity_claim": [
        r"\byou are (?:a |an )?(?:introvert|extrovert|empath|narcissist|anxious person|depressed person)\b",
        r"\byou are (?:clearly |obviously |definitely )\w+\b",
        r"\byou are the type\b",
        r"\byou're (?:a |an )?(?:introvert|extrovert|empath|narcissist)\b",
    ],
    "diagnosis": [
        r"\byou have (?:depression|anxiety|adhd|add|ocd|ptsd|bipolar)\b",
        r"\byou(?:'re| are) (?:depressed|anxious|bipolar|manic)\b",
        r"\bthis is (?:depression|anxiety|a disorder)\b",
        r"\byou suffer from\b",
        r"\byou(?:'re| are) mentally\b",
    ],
}

# Rewrite prompt for non-compliant responses
GUARDRAIL_REWRITE_PROMPT = """You are a response editor for Mirror, a reflective AI companion.

The following response contains language that violates Mirror's core principles:
- No prescriptions (should/must/need to)
- No predictions (will happen/you will)
- No identity claims (you are X)
- No diagnoses

ORIGINAL RESPONSE:
{original_response}

VIOLATIONS DETECTED:
{violations}

Rewrite this response to:
1. Keep the core meaning and insights
2. Replace prescriptive language with reflective observations ("I notice..." / "It sounds like..." / "What if...")
3. Remove predictions; use present-tense noticing instead
4. Convert identity claims to pattern observations ("Sometimes you seem to..." / "There's a quality of...")
5. Remove any diagnostic language entirely
6. End with ONE gentle, open question
7. Keep the calm, grounded Mirror tone

Respond with ONLY the rewritten text, no explanations."""


import re

# Guardrail violation counter (in-memory for this session)
guardrail_violation_counts: Dict[str, int] = {
    "prescription": 0,
    "prediction": 0,
    "identity_claim": 0,
    "diagnosis": 0,
    "total_rewrites": 0,
}


def check_guardrail_violations(text: str) -> Dict[str, List[str]]:
    """
    Check response text for guardrail violations.
    Returns dict of violation types and matched patterns.
    Does NOT log the actual text content.
    """
    violations = {}
    text_lower = text.lower()
    
    for violation_type, patterns in GUARDRAIL_PATTERNS.items():
        matches = []
        for pattern in patterns:
            found = re.findall(pattern, text_lower, re.IGNORECASE)
            if found:
                matches.extend(found)
        if matches:
            violations[violation_type] = matches
    
    return violations


async def rewrite_for_compliance(original_response: str, violations: Dict[str, List[str]]) -> str:
    """
    Rewrite a response to remove guardrail violations.
    Uses LLM to maintain meaning while ensuring compliance.
    """
    try:
        # Format violations for prompt
        violation_summary = []
        for vtype, matches in violations.items():
            violation_summary.append(f"- {vtype}: {', '.join(matches[:3])}")
        
        rewrite_prompt = GUARDRAIL_REWRITE_PROMPT.format(
            original_response=original_response,
            violations="\n".join(violation_summary)
        )
        
        # Create LLM call for rewrite
        rewrite_chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"guardrail_rewrite_{datetime.now().timestamp()}",
            system_message=rewrite_prompt
        )
        rewrite_chat.with_model("openai", "gpt-5.2")
        
        rewrite_message = UserMessage(text="Rewrite the response now.")
        rewritten = await rewrite_chat.send_message(rewrite_message)
        
        return rewritten.strip()
        
    except Exception as e:
        logger.error(f"Guardrail rewrite failed: {e}")
        # Return original if rewrite fails
        return original_response


class ChartCalculationRequest(BaseModel):
    user_id: str
    sidereal_settings: Optional[Dict] = {
        "mode": "true_sidereal_user_defined",
        "svp_degrees": 31.2836,
        "reference_year": 2000,
        "yearly_increment": 0.0
    }
    house_system: Optional[str] = "Equal"


# ============================================
# Rate Limiting & Cost Control
# ============================================

# Rate limit configuration
RATE_LIMITS = {
    "mirror": {"max_requests": 30, "window_seconds": 3600},  # 30 per hour for generalist
    "lens": {"max_requests": 20, "window_seconds": 3600},     # 20 per hour for all lens chats combined
}

# Token limits
MAX_RESPONSE_TOKENS = 800
MAX_CHAT_HISTORY = 10
MAX_JOURNAL_ENTRIES = 5

# In-memory rate limiter storage: {user_id: {"mirror": [timestamps], "lens": [timestamps]}}
rate_limit_store: Dict[str, Dict[str, List[float]]] = {}

# Fallback response for failures
FALLBACK_RESPONSE = "Let's slow this down for a moment. Try again shortly."


def check_rate_limit(user_id: str, is_lens: bool) -> bool:
    """
    Check if user is within rate limits.
    Returns True if allowed, False if rate limited.
    """
    now = time.time()
    limit_type = "lens" if is_lens else "mirror"
    config = RATE_LIMITS[limit_type]
    
    # Initialize user storage if needed
    if user_id not in rate_limit_store:
        rate_limit_store[user_id] = {"mirror": [], "lens": []}
    
    # Clean old timestamps outside the window
    cutoff = now - config["window_seconds"]
    rate_limit_store[user_id][limit_type] = [
        ts for ts in rate_limit_store[user_id][limit_type] if ts > cutoff
    ]
    
    # Check if under limit
    if len(rate_limit_store[user_id][limit_type]) >= config["max_requests"]:
        return False
    
    # Add current request timestamp
    rate_limit_store[user_id][limit_type].append(now)
    return True


def get_rate_limit_remaining(user_id: str, is_lens: bool) -> int:
    """Get remaining requests for user."""
    limit_type = "lens" if is_lens else "mirror"
    config = RATE_LIMITS[limit_type]
    
    if user_id not in rate_limit_store:
        return config["max_requests"]
    
    now = time.time()
    cutoff = now - config["window_seconds"]
    active_requests = len([
        ts for ts in rate_limit_store[user_id].get(limit_type, []) if ts > cutoff
    ])
    
    return max(0, config["max_requests"] - active_requests)


import time


class LocationSearchRequest(BaseModel):
    query: str


# ===========================
# HELPER FUNCTIONS
# ===========================

# parse_timezone is now imported from calculations.timezone_utils


async def geocode_location(city: str, country: str) -> Optional[Dict]:
    """Geocode location to get lat/lon"""
    try:
        geolocator = Nominatim(user_agent="project_mirror", timeout=10)
        location = geolocator.geocode(f"{city}, {country}", addressdetails=True)
        if location:
            return {
                "city": city,
                "country": country,
                "latitude": location.latitude,
                "longitude": location.longitude
            }
        return None
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        return None


async def get_user_context(user_id: str) -> Dict:
    """Get user profile and chart data for AI context"""
    try:
        # Get user profile
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return {}
        
        # Get chart
        chart = await db.charts.find_one({"user_id": user_id})
        
        # Get recent journal entries (LIMITED to MAX_JOURNAL_ENTRIES)
        journal_entries = await db.journal.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(MAX_JOURNAL_ENTRIES).to_list(MAX_JOURNAL_ENTRIES)
        
        context = {
            "name": user.get("name", ""),
            "has_chart": chart is not None,
        }
        
        # CRITICAL: DO NOT inject framework data into context
        # Framework data exists but must NEVER be passed to Mirror AI
        # Only pass journal themes (universal patterns)
        
        if journal_entries:
            context["recent_themes"] = [entry.get("content", "")[:100] for entry in journal_entries]
        
        return context
    except Exception as e:
        logger.error(f"Error getting user context: {e}")
        return {}


async def generate_ai_response(system_prompt: str, user_message: str, user_id: str = None) -> str:
    """Generate AI response using Emergent LLM"""
    try:
        # Get user context if user_id provided
        context = ""
        if user_id:
            user_context = await get_user_context(user_id)
            if user_context:
                context = f"\n\nUser Context:\n{user_context}"
        
        # Initialize AI chat
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=user_id if user_id else "default",
            system_message=system_prompt + context
        )
        chat.with_model("openai", "gpt-5.2")
        
        # Send message
        message = UserMessage(text=user_message)
        response = await chat.send_message(message)
        
        return response
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        return "I'm having trouble connecting right now. Please try again in a moment."


# ===========================
# API ROUTES
# ===========================

@api_router.get("/")
async def root():
    return {"message": "Project Mirror API", "version": "1.0"}


@api_router.post("/locations/search")
async def search_locations(request: LocationSearchRequest):
    """Search for locations with autocomplete"""
    
    # Fallback database of common cities (used when Nominatim is unavailable)
    FALLBACK_CITIES = [
        {"city": "New York", "country": "United States", "latitude": 40.7128, "longitude": -74.0060},
        {"city": "Los Angeles", "country": "United States", "latitude": 34.0522, "longitude": -118.2437},
        {"city": "Chicago", "country": "United States", "latitude": 41.8781, "longitude": -87.6298},
        {"city": "Houston", "country": "United States", "latitude": 29.7604, "longitude": -95.3698},
        {"city": "San Francisco", "country": "United States", "latitude": 37.7749, "longitude": -122.4194},
        {"city": "Seattle", "country": "United States", "latitude": 47.6062, "longitude": -122.3321},
        {"city": "Miami", "country": "United States", "latitude": 25.7617, "longitude": -80.1918},
        {"city": "Boston", "country": "United States", "latitude": 42.3601, "longitude": -71.0589},
        {"city": "London", "country": "United Kingdom", "latitude": 51.5074, "longitude": -0.1278},
        {"city": "Manchester", "country": "United Kingdom", "latitude": 53.4808, "longitude": -2.2426},
        {"city": "Paris", "country": "France", "latitude": 48.8566, "longitude": 2.3522},
        {"city": "Berlin", "country": "Germany", "latitude": 52.5200, "longitude": 13.4050},
        {"city": "Tokyo", "country": "Japan", "latitude": 35.6762, "longitude": 139.6503},
        {"city": "Sydney", "country": "Australia", "latitude": -33.8688, "longitude": 151.2093},
        {"city": "Melbourne", "country": "Australia", "latitude": -37.8136, "longitude": 144.9631},
        {"city": "Toronto", "country": "Canada", "latitude": 43.6532, "longitude": -79.3832},
        {"city": "Vancouver", "country": "Canada", "latitude": 49.2827, "longitude": -123.1207},
        {"city": "Singapore", "country": "Singapore", "latitude": 1.3521, "longitude": 103.8198},
        {"city": "Hong Kong", "country": "China", "latitude": 22.3193, "longitude": 114.1694},
        {"city": "Shanghai", "country": "China", "latitude": 31.2304, "longitude": 121.4737},
        {"city": "Beijing", "country": "China", "latitude": 39.9042, "longitude": 116.4074},
        {"city": "Mumbai", "country": "India", "latitude": 19.0760, "longitude": 72.8777},
        {"city": "Delhi", "country": "India", "latitude": 28.7041, "longitude": 77.1025},
        {"city": "Bangalore", "country": "India", "latitude": 12.9716, "longitude": 77.5946},
        {"city": "Dubai", "country": "United Arab Emirates", "latitude": 25.2048, "longitude": 55.2708},
        {"city": "Kuala Lumpur", "country": "Malaysia", "latitude": 3.1390, "longitude": 101.6869},
        {"city": "Petaling Jaya", "country": "Malaysia", "latitude": 3.1073, "longitude": 101.6067},
        {"city": "Johor Bahru", "country": "Malaysia", "latitude": 1.4927, "longitude": 103.7414},
        {"city": "Bangkok", "country": "Thailand", "latitude": 13.7563, "longitude": 100.5018},
        {"city": "Jakarta", "country": "Indonesia", "latitude": -6.2088, "longitude": 106.8456},
        {"city": "Manila", "country": "Philippines", "latitude": 14.5995, "longitude": 120.9842},
        {"city": "Seoul", "country": "South Korea", "latitude": 37.5665, "longitude": 126.9780},
        {"city": "Amsterdam", "country": "Netherlands", "latitude": 52.3676, "longitude": 4.9041},
        {"city": "Rome", "country": "Italy", "latitude": 41.9028, "longitude": 12.4964},
        {"city": "Madrid", "country": "Spain", "latitude": 40.4168, "longitude": -3.7038},
        {"city": "Barcelona", "country": "Spain", "latitude": 41.3851, "longitude": 2.1734},
        {"city": "Vienna", "country": "Austria", "latitude": 48.2082, "longitude": 16.3738},
        {"city": "Zurich", "country": "Switzerland", "latitude": 47.3769, "longitude": 8.5417},
        {"city": "Dublin", "country": "Ireland", "latitude": 53.3498, "longitude": -6.2603},
        {"city": "Stockholm", "country": "Sweden", "latitude": 59.3293, "longitude": 18.0686},
        {"city": "Oslo", "country": "Norway", "latitude": 59.9139, "longitude": 10.7522},
        {"city": "Copenhagen", "country": "Denmark", "latitude": 55.6761, "longitude": 12.5683},
        {"city": "Helsinki", "country": "Finland", "latitude": 60.1699, "longitude": 24.9384},
        {"city": "Brussels", "country": "Belgium", "latitude": 50.8503, "longitude": 4.3517},
        {"city": "Lisbon", "country": "Portugal", "latitude": 38.7223, "longitude": -9.1393},
        {"city": "Athens", "country": "Greece", "latitude": 37.9838, "longitude": 23.7275},
        {"city": "Prague", "country": "Czech Republic", "latitude": 50.0755, "longitude": 14.4378},
        {"city": "Warsaw", "country": "Poland", "latitude": 52.2297, "longitude": 21.0122},
        {"city": "Moscow", "country": "Russia", "latitude": 55.7558, "longitude": 37.6173},
        {"city": "São Paulo", "country": "Brazil", "latitude": -23.5505, "longitude": -46.6333},
        {"city": "Rio de Janeiro", "country": "Brazil", "latitude": -22.9068, "longitude": -43.1729},
        {"city": "Buenos Aires", "country": "Argentina", "latitude": -34.6037, "longitude": -58.3816},
        {"city": "Mexico City", "country": "Mexico", "latitude": 19.4326, "longitude": -99.1332},
        {"city": "Cape Town", "country": "South Africa", "latitude": -33.9249, "longitude": 18.4241},
        {"city": "Johannesburg", "country": "South Africa", "latitude": -26.2041, "longitude": 28.0473},
        {"city": "Cairo", "country": "Egypt", "latitude": 30.0444, "longitude": 31.2357},
        {"city": "Lagos", "country": "Nigeria", "latitude": 6.5244, "longitude": 3.3792},
        {"city": "Nairobi", "country": "Kenya", "latitude": -1.2921, "longitude": 36.8219},
        {"city": "Tel Aviv", "country": "Israel", "latitude": 32.0853, "longitude": 34.7818},
        {"city": "Istanbul", "country": "Turkey", "latitude": 41.0082, "longitude": 28.9784},
    ]
    
    def search_fallback(query: str):
        """Search through fallback cities"""
        query_lower = query.lower().strip()
        results = []
        for city_data in FALLBACK_CITIES:
            city_lower = city_data["city"].lower()
            country_lower = city_data["country"].lower()
            if query_lower in city_lower or query_lower in country_lower:
                # Estimate timezone from longitude
                lng = city_data["longitude"]
                tz_hours = round(lng / 15)
                tz_sign = "+" if tz_hours >= 0 else "-"
                tz_string = f"{tz_sign}{abs(tz_hours):02d}:00"
                
                results.append({
                    "city": city_data["city"],
                    "country": city_data["country"],
                    "latitude": city_data["latitude"],
                    "longitude": city_data["longitude"],
                    "display_name": f"{city_data['city']}, {city_data['country']}",
                    "timezone": tz_string
                })
        return results[:5]  # Limit to 5 results
    
    try:
        geolocator = Nominatim(user_agent="project_mirror", timeout=10)
        locations = geolocator.geocode(request.query, exactly_one=False, limit=5, addressdetails=True)
        
        if not locations:
            # Try fallback if no results from Nominatim
            fallback_results = search_fallback(request.query)
            if fallback_results:
                return {"results": fallback_results}
            return {"results": []}
        
        results = []
        for loc in locations:
            address = loc.raw.get('address', {})
            
            # Extract city name - prefer the most specific locality
            city = (
                address.get('city') or 
                address.get('town') or 
                address.get('village') or
                address.get('suburb') or  # Added suburb for places like Petaling Jaya
                address.get('municipality') or
                address.get('county') or
                address.get('state_district') or
                address.get('state') or
                loc.address.split(',')[0].strip()
            )
            
            # If search query looks like a specific place and result starts with it, use it
            query_lower = request.query.lower().strip()
            display_parts = loc.address.split(',')
            first_part = display_parts[0].strip()
            if query_lower in first_part.lower() and len(first_part) < 50:
                city = first_part
            
            country = address.get('country', 'Unknown')
            
            # Estimate timezone from longitude (rough approximation)
            # Each 15° of longitude = 1 hour offset from UTC
            lng = loc.longitude
            tz_hours = round(lng / 15)
            tz_sign = "+" if tz_hours >= 0 else "-"
            tz_string = f"{tz_sign}{abs(tz_hours):02d}:00"
            
            results.append({
                "city": city,
                "country": country,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "display_name": loc.address,
                "timezone": tz_string
            })
        
        return {"results": results}
    except Exception as e:
        logger.error(f"Location search error: {e}")
        # Try fallback when Nominatim fails
        fallback_results = search_fallback(request.query)
        if fallback_results:
            logger.info(f"Using fallback cities for query: {request.query}")
            return {"results": fallback_results}
        return {"results": []}


@api_router.post("/users", response_model=UserProfileResponse)
async def create_user(profile: UserProfileCreate):
    """Create user profile"""
    try:
        # Parse and validate timezone
        try:
            timezone_raw, parsed_timezone_minutes = parse_timezone(profile.timezone)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid timezone: {str(e)}")
        
        # Use provided lat/long if available, otherwise geocode
        if profile.latitude is not None and profile.longitude is not None:
            # Use provided coordinates (from fallback city database)
            location_data = {
                "city": profile.city,
                "country": profile.country,
                "latitude": profile.latitude,
                "longitude": profile.longitude
            }
            logger.info(f"Using provided coordinates: {profile.city}, {profile.country} ({profile.latitude}, {profile.longitude})")
        else:
            # Geocode location
            location_data = await geocode_location(profile.city, profile.country)
            if not location_data:
                raise HTTPException(status_code=400, detail="Could not geocode location")
        
        # Parse birth date
        birth_date = datetime.strptime(profile.birth_date, "%Y-%m-%d")
        
        user_data = {
            "name": profile.name,
            "birth_date": birth_date,
            "birth_time": profile.birth_time,
            "birth_location": location_data,
            "timezone": timezone_raw,
            "timezone_minutes": parsed_timezone_minutes,
            "created_at": datetime.now(timezone.utc)
        }
        
        result = await db.users.insert_one(user_data)
        
        return UserProfileResponse(
            id=str(result.inserted_id),
            name=profile.name,
            birth_date=profile.birth_date,
            birth_time=profile.birth_time,
            birth_location=Location(**location_data),
            has_chart=False
        )
    except Exception as e:
        logger.error(f"Create user error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/users/{user_id}", response_model=UserProfileResponse)
async def get_user(user_id: str):
    """Get user profile"""
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if chart exists
        chart = await db.charts.find_one({"user_id": user_id})
        
        return UserProfileResponse(
            id=str(user["_id"]),
            name=user.get("name"),
            email=user.get("email"),
            birth_date=user["birth_date"].strftime("%Y-%m-%d"),
            birth_time=user.get("birth_time"),
            birth_location=Location(**user["birth_location"]),
            has_chart=chart is not None
        )
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/users/{user_id}/email")
async def update_user_email(user_id: str, request: EmailUpdateRequest):
    """Update user email - used to save their reflection space"""
    try:
        # Basic email validation
        email = request.email.strip().lower()
        if not email or '@' not in email or '.' not in email.split('@')[-1]:
            raise HTTPException(status_code=400, detail="Please enter a valid email address")
        
        # Check if user exists
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update email
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"email": email, "email_updated_at": datetime.now(timezone.utc)}}
        )
        
        return {"success": True, "message": "Email saved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update email error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/charts/calculate")
async def calculate_chart(request: ChartCalculationRequest):
    """Calculate all frameworks for user"""
    # Generate unique request ID for tracking
    request_id = str(uuid.uuid4())
    
    try:
        # Get user
        user = await db.users.find_one({"_id": ObjectId(request.user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user data
        birth_date = user["birth_date"]
        birth_time = user.get("birth_time")
        user_timezone = user.get("timezone")
        
        # Store original inputs for debug stamp
        input_birth_local = birth_date.strftime("%Y-%m-%d")
        input_birth_time_raw = birth_time if birth_time else None
        input_timezone_raw = user_timezone if user_timezone else None
        
        # STRICT TIMEZONE VALIDATION - No silent defaults
        if not user_timezone:
            raise HTTPException(
                status_code=400, 
                detail="Timezone is required. Please update user profile with IANA timezone (e.g., 'Asia/Kuala_Lumpur')."
            )
        
        if not birth_time:
            raise HTTPException(
                status_code=400,
                detail="Birth time is required. Please update user profile with birth time (e.g., '07:25' or '7:25am')."
            )
        
        # Use enhanced birth UTC resolution with comprehensive debug
        from calculations.timezone_utils import resolve_birth_utc_with_debug, normalize_birth_time
        
        resolution = resolve_birth_utc_with_debug(
            birth_date_str=input_birth_local,
            birth_time_str=birth_time,
            timezone_str=user_timezone
        )
        
        if not resolution["success"]:
            error_code = resolution["error"]
            error_msg = resolution.get("error_message", "Unknown error")
            raise HTTPException(
                status_code=400, 
                detail=f"{error_code}: {error_msg}"
            )
        
        birth_datetime_utc = resolution["birth_utc"]
        resolution_debug = resolution["debug_stamp"]
        
        # Extract resolved values
        resolved_birth_utc_iso = resolution_debug["datetime_utc_iso"]
        parsed_timezone_minutes = resolution_debug["resolved_offset_minutes"]
        normalized_birth_time = resolution_debug["time_normalized"]
        
        location = user["birth_location"]
        lat = location["latitude"]
        lon = location["longitude"]
        lat_used = lat
        lon_used = lon
        
        # Sidereal settings (Project Mirror Spec - True Sidereal with fixed SVP)
        sidereal_settings_used = {
            "mode": "true_sidereal_user_defined",
            "svp_degrees": 31.2836,
            "reference_year": 2000,
            "yearly_increment": 0.0
        }
        
        house_system_used = "Equal"  # Project Mirror requires Equal houses ONLY
        
        # Calculate input hash for debugging
        input_string = f"{resolved_birth_utc_iso}|{lat_used}|{lon_used}|{sidereal_settings_used}|{house_system_used}"
        input_hash = hashlib.sha256(input_string.encode()).hexdigest()
        
        # Create enhanced debug stamp with IANA support
        debug_stamp = {
            "request_id": request_id,
            "profile_id": request.user_id,
            "user_id": request.user_id,
            "input_birth_local": input_birth_local,
            "input_birth_time_raw": input_birth_time_raw,
            "input_birth_time_normalized": normalized_birth_time,
            "input_timezone_raw": input_timezone_raw,
            "timezone_iana": resolution_debug.get("timezone_iana"),
            "resolved_utc_offset_at_birth": resolution_debug.get("resolved_utc_offset_at_birth"),
            "resolved_offset_minutes": parsed_timezone_minutes,
            "datetime_utc_used": resolved_birth_utc_iso,
            "lat_used": lat_used,
            "lon_used": lon_used,
            "sidereal_settings_used": sidereal_settings_used,
            "house_system_used": house_system_used,
            "input_hash": input_hash,
            "computed_at_iso": datetime.now(timezone.utc).isoformat()
        }
        
        # Log debug stamp at INFO level
        logger.info(f"CHART_CALCULATION [request_id={request_id}] debug_stamp={debug_stamp}")
        
        # Calculate all frameworks using UTC datetime
        logger.info(f"Calculating astrology chart for user {request.user_id}")
        astrology_chart = get_full_natal_chart(
            birth_datetime_utc, 
            lat, 
            lon, 
            sidereal_settings=sidereal_settings_used,
            house_system=house_system_used
        )
        
        logger.info(f"Calculating human design for user {request.user_id}")
        human_design = get_human_design_chart(
            birth_datetime_utc, 
            lat, 
            lon,
            sidereal_settings=sidereal_settings_used
        )
        
        logger.info(f"Calculating numerology for user {request.user_id}")
        numerology = get_full_numerology(birth_date, user.get("name"))
        
        logger.info(f"Getting consciousness framework for user {request.user_id}")
        consciousness = get_consciousness_framework()
        
        # =====================================================================
        # INTERPRETATION BOUNDARY - DO NOT CROSS
        # =====================================================================
        # This payload contains DETERMINISTIC FACTS only.
        # Interpretation and narrative generation must occur DOWNSTREAM.
        #
        # The data below is raw computational output:
        # - Astrology: positions, signs, houses (no meanings)
        # - Human Design: type, gates, channels (no personality descriptions)
        # - Numerology: numbers and patterns (no life path interpretations)
        #
        # AI prompts, UI copy, and user-facing narratives must be generated
        # in a SEPARATE interpretation layer, NOT in this computation core.
        # =====================================================================
        
        # =====================================================================
        # RUNTIME GUARDRAIL: Deterministic Payload Integrity
        # =====================================================================
        # Deterministic payload must contain no interpretive language.
        # All fields must be factual, numeric, or categorical.
        #
        # FORBIDDEN in compute output:
        # - "you", "your" (addressing user)
        # - "should", "will", "must" (prescriptive)
        # - "means", "represents", "symbolizes" (interpretive)
        # - "invites", "suggests", "indicates" (inferential)
        #
        # If this guardrail fires, FIX THE COMPUTE MODULE, not this check.
        # =====================================================================
        
        # Store chart data
        chart_data = {
            "user_id": request.user_id,
            "astrology": astrology_chart,
            "human_design": human_design,
            "numerology": numerology,
            "consciousness_levels": consciousness,
            "calculated_at": datetime.now(timezone.utc),
            "debug_stamp": debug_stamp  # Store debug stamp in database too
        }
        
        # Upsert chart
        await db.charts.update_one(
            {"user_id": request.user_id},
            {"$set": chart_data},
            upsert=True
        )
        
        return {
            "success": True,
            "message": "Chart calculated successfully",
            "computation_version": "mirror-deterministic-v1",
            "data": chart_data,
            "debug_stamp": debug_stamp  # Include in API response
        }
    except Exception as e:
        logger.error(f"Calculate chart error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/charts/{user_id}")
async def get_chart(user_id: str):
    """Get user's calculated chart"""
    try:
        chart = await db.charts.find_one({"user_id": user_id})
        if not chart:
            raise HTTPException(status_code=404, detail="Chart not found. Please calculate first.")
        
        # Convert ObjectId to string
        chart["_id"] = str(chart["_id"])
        chart["computation_version"] = "mirror-deterministic-v1"
        return chart
    except Exception as e:
        logger.error(f"Get chart error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/journal", response_model=JournalEntryResponse)
async def create_journal_entry(entry: JournalEntryCreate):
    """Create journal entry"""
    try:
        # Analyze consciousness indicators
        analysis = analyze_consciousness_indicators(entry.content)
        
        entry_data = {
            "user_id": entry.user_id,
            "content": entry.content,
            "themes": [analysis.get("estimated_level", "")],
            "created_at": datetime.now(timezone.utc)
        }
        
        result = await db.journal.insert_one(entry_data)
        
        return JournalEntryResponse(
            id=str(result.inserted_id),
            content=entry.content,
            themes=entry_data["themes"],
            created_at=entry_data["created_at"].isoformat()
        )
    except Exception as e:
        logger.error(f"Create journal error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/journal/{user_id}", response_model=List[JournalEntryResponse])
async def get_journal_entries(user_id: str, limit: int = 20):
    """Get user's journal entries"""
    try:
        entries = await db.journal.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        return [
            JournalEntryResponse(
                id=str(entry["_id"]),
                content=entry["content"],
                themes=entry.get("themes", []),
                created_at=entry["created_at"].isoformat()
            )
            for entry in entries
        ]
    except Exception as e:
        logger.error(f"Get journal error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class JournalIntegrationRequest(BaseModel):
    user_id: str
    entry_id: str
    question: Optional[str] = None  # User's optional question about the entry


class JournalIntegrationResponse(BaseModel):
    reflection: str
    perspective: Optional[str] = None


@api_router.post("/journal/integrate", response_model=JournalIntegrationResponse)
async def integrate_journal_entry(request: JournalIntegrationRequest):
    """
    Integrate a journal entry with available lenses.
    
    This is the core "Reflect with Mirror" feature that gently draws from
    all available frameworks (Astrology, Human Design, etc.) while maintaining
    Interpretation Layer v1 rules:
    - No prescriptive language
    - No identity statements  
    - Reflective, invitational tone
    - User sovereignty preserved
    """
    try:
        # Get the journal entry
        entry = await db.journal.find_one({"_id": ObjectId(request.entry_id)})
        if not entry:
            raise HTTPException(status_code=404, detail="Journal entry not found")
        
        # Verify ownership
        if entry.get("user_id") != request.user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Get user's chart data (read-only, for context)
        chart = await db.charts.find_one({"user_id": request.user_id})
        
        # Get user context (onboarding preferences)
        user_context = await get_user_context(request.user_id)
        
        # Build lens context (factual only, no interpretations)
        lens_context = ""
        if chart:
            # Human Design - factual only
            hd = chart.get("human_design", {})
            if hd:
                lens_context += f"\nHuman Design context (factual): Type is {hd.get('type', 'unknown')}, Profile is {hd.get('profile', 'unknown')}, Authority is {hd.get('authority', 'unknown')}."
            
            # Astrology - factual only
            astro = chart.get("astrology", {})
            if astro and astro.get("planets"):
                sun = astro.get("planets", {}).get("Sun", {})
                moon = astro.get("planets", {}).get("Moon", {})
                if sun:
                    lens_context += f"\nAstrology context (factual): Sun in {sun.get('sign', 'unknown')}, Moon in {moon.get('sign', 'unknown')}."
            
            # Numerology - factual only
            numerology = chart.get("numerology", {})
            if numerology:
                lens_context += f"\nNumerology context (factual): Life Path {numerology.get('life_path', {}).get('number', 'unknown')}."
        
        # Build the integration prompt
        system_prompt = """PROJECT MIRROR — JOURNAL INTEGRATION (Interpretation Layer v1)

You are a gentle reflection companion, not an advisor or interpreter.

Your role is to help the user explore their journal entry through multiple lenses,
WITHOUT telling them what it means or what they should do.

=== INTERPRETATION LAYER RULES (MANDATORY) ===

FORBIDDEN:
- "You ARE a [type]" — use "Your chart shows [type]" or "This pattern..."
- "You WILL experience..." — use "This pattern may invite..."
- "You SHOULD..." — use "You might explore..." or "Some find..."
- "This MEANS..." — use "One lens sees this as..."
- Direct advice or prescriptions
- Definitive predictions
- Identity statements ("you are")

ENCOURAGED:
- Questions that invite self-reflection
- "Some people with this pattern notice..."
- "This is one way to look at..."
- "What resonates for you?"
- "I'm curious about..."
- Spacious, invitational language

=== YOUR TASK ===

1. Acknowledge the journal entry with presence (not analysis)
2. Gently offer 1-2 reflective perspectives that DRAW FROM the available lenses
3. Do NOT explain the frameworks — just let them inform your reflection
4. End with an inviting question that opens further exploration
5. Keep the tone warm, spacious, and non-prescriptive

The user is the authority on their own experience.
Frameworks are LENSES, not TRUTH.
Always leave room for "this doesn't fit me."

=== OUTPUT FORMAT ===

Respond with a JSON object:
{
  "reflection": "Your main reflective response (2-3 paragraphs max)",
  "perspective": "An optional additional lens or question to consider"
}

Keep it concise. This should feel like a gentle conversation, not a lecture."""

        # Build user message
        user_message = f"""JOURNAL ENTRY:
\"\"\"{entry.get('content', '')[:1500]}\"\"\"

{f'USER QUESTION: {request.question}' if request.question else 'USER REQUEST: Help me reflect on this entry through available lenses.'}

{lens_context if lens_context else '(No chart data available — respond with general reflective presence)'}

{f"USER TONE PREFERENCE: {user_context.get('consciousness_level', 'reflective')}" if user_context else ''}

Generate a gentle, lens-informed reflection that honors the user's sovereignty."""

        # Generate response
        response = completion(
            model="gpt-5.2",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            api_key=emergent_api_key,
            temperature=0.7,
            max_tokens=800
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            # Clean up response if needed
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            result = json.loads(response_text)
            
            # Validate against interpretation layer rules
            forbidden_patterns = [
                "you are a", "you're a", "you will", "you should", "you must",
                "this means", "this indicates that you"
            ]
            
            reflection = result.get("reflection", "")
            for pattern in forbidden_patterns:
                if pattern in reflection.lower():
                    # Soften the language
                    reflection = reflection.replace(
                        pattern.capitalize(), 
                        "This pattern may suggest that you"
                    )
            
            return JournalIntegrationResponse(
                reflection=reflection or "Thank you for sharing. What feels most alive in this reflection for you?",
                perspective=result.get("perspective")
            )
            
        except json.JSONDecodeError:
            # Return the raw text as reflection
            return JournalIntegrationResponse(
                reflection=response_text[:1000] if response_text else "Thank you for sharing this. What aspect would you like to explore further?",
                perspective=None
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Journal integration error: {e}")
        raise HTTPException(status_code=500, detail="Unable to generate reflection. Please try again.")


@api_router.post("/reflections/daily", response_model=DailyReflectionResponse)
async def generate_daily_reflection(request: ChartCalculationRequest):
    """Generate personalized daily reflection"""
    try:
        # Get user context
        user_context = await get_user_context(request.user_id)
        
        # Get chart data
        chart = await db.charts.find_one({"user_id": request.user_id})
        
        # Check if already generated today
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        existing = await db.reflections.find_one({
            "user_id": request.user_id,
            "date": today
        })
        
        if existing:
            return DailyReflectionResponse(
                id=str(existing["_id"]),
                date=existing["date"],
                insight=existing["insight"],
                question=existing["question"],
                perspective=existing["perspective"]
            )
        
        # Generate AI reflection
        system_prompt = """PROJECT MIRROR — SYSTEM PROMPT (STRICT SEPARATION MODE)

You are Project Mirror.
You are a reflection space — not a profiler, not a teacher, not a framework interpreter.

Hard Rule: Mirror vs Lenses separation

Mirror (Home / Today's Insight / Reflect On / Another Perspective):
You MUST NOT mention any frameworks or profile terms, including but not limited to:
Human Design, Manifestor, Generator, Manifesting Generator, Projector, Reflector, authority, profile, gates, astrology, zodiac, houses, planets, numerology, life path, BaZi, Gene Keys, Enneagram, type, strategy, incarnation cross.
Even if these data exist in memory or context, they are internal-only and forbidden on Mirror.

Lenses section only:
Frameworks may be discussed ONLY inside the Lenses screens and only if the user navigates there or explicitly asks.

Mirror Content Style Rules:
- Do not label the user ("You are X").
- Do not predict outcomes.
- Do not give advice ("You should").
- Use neutral, grounded language.
- Offer perspectives, not conclusions.

Preferred phrases:
- "One way to look at this is…"
- "You may notice…"
- "If this resonates…"
- "Another perspective could be…"

Input Use Rules:
Mirror can use ONLY:
- the user's 5 onboarding answers
- the user's recent journal entries (if any)
- the current date/day context (lightly)

Mirror must IGNORE any profile/calculation data (Swiss Ephemeris, Human Design, numerology, etc.).

If the user asks about frameworks while on Mirror:
Respond briefly and offer: "You can explore that in Lenses."
Do not explain the framework on Mirror.

Generate the Mirror Daily Card with these sections:
1. Today's Insight (max 70–110 words)
2. Reflect On (one question)
3. Another Perspective (max 70–110 words)

Tone: Grounded, calm, non-mystical. No instruction. No prediction. No diagnosis.

Mirror the user's likely current state based on onboarding answers:
- If overwhelmed/stuck → grounding, simple, smaller next moment
- If searching/uncertain → gentle reframes, normalize ambiguity
- If curious/reflective → deeper inquiry and nuance
- If steady → spacious, values-based reflection

Format as JSON:
{
  "insight": "...",
  "question": "...",
  "perspective": "..."
}
"""
        
        # Build context message - NO FRAMEWORK DATA
        context_msg = """Generate today's reflection.

CRITICAL: This is for the Mirror (Home) screen. You MUST NOT use any framework terms.

Base the reflection ONLY on universal human patterns, not on any astrological, Human Design, or numerological data."""
        
        if user_context.get("recent_themes"):
            context_msg += f"\n\nRecent journal themes: {', '.join(user_context['recent_themes'][:2])}"
        
        context_msg += "\n\nGenerate a grounded, framework-free reflection in JSON format."
        
        # Generate
        response = await generate_ai_response(system_prompt, context_msg, request.user_id)
        
        # Parse response (simplified for V1)
        try:
            import json
            import re
            reflection_data = json.loads(response)
            
            # LEAK-PROOF VALIDATOR: Strip any framework terms that slipped through
            forbidden_terms = [
                'human design', 'manifestor', 'generator', 'manifesting generator', 'projector', 'reflector',
                'authority', 'emotional authority', 'sacral authority', 'splenic authority',
                'profile', 'gate', 'gates', 'channel', 'channels', 'center', 'centers',
                'astrology', 'astrological', 'zodiac', 'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
                'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces',
                'sun sign', 'moon sign', 'rising sign', 'ascendant', 'planet', 'planets',
                'house', 'houses', 'aspect', 'aspects', 'chart', 'natal chart',
                'numerology', 'life path', 'expression number', 'soul urge',
                'bazaar', 'gene keys', 'enneagram', 'type', 'strategy', 'incarnation cross',
                'defined', 'undefined', 'open', 'bodygraph'
            ]
            
            # Check for ANY contamination in the full response
            leak_detected = False
            for field in ['insight', 'question', 'perspective']:
                if field in reflection_data:
                    text_lower = reflection_data[field].lower()
                    for term in forbidden_terms:
                        if term in text_lower:
                            print(f"!!! FRAMEWORK LEAK DETECTED in {field}: '{term}'")
                            logger.warning(f"FRAMEWORK LEAK DETECTED in {field}: '{term}' - using fallback")
                            leak_detected = True
                            break
                    if leak_detected:
                        break
            
            # If ANY leak detected, use safe fallback for ALL fields
            if leak_detected:
                print("!!! USING FALLBACK DUE TO LEAK")
                reflection_data = {
                    "insight": "One way to look at today is as an invitation to observe patterns in how you relate to change and uncertainty.",
                    "question": "What feels most true for you right now?",
                    "perspective": "Consider that the moments you resist most might be showing you something about what you value. Not as a lesson to learn, but as information about who you're becoming."
                }
            else:
                print("!!! NO LEAK DETECTED - Content is clean")
        except:
            # Fallback if parsing fails
            reflection_data = {
                "insight": "One way to look at today is as an invitation to observe, rather than to change.",
                "question": "What patterns do you notice in how you respond to the unexpected?",
                "perspective": "Consider that the moments you resist most might be showing you something about what you value. Not as a lesson to learn, but as information about who you're becoming."
            }
        
        # Store reflection
        reflection = {
            "user_id": request.user_id,
            "date": today,
            "insight": reflection_data.get("insight", ""),
            "question": reflection_data.get("question", ""),
            "perspective": reflection_data.get("perspective", ""),
            "created_at": datetime.now(timezone.utc)
        }
        
        result = await db.reflections.insert_one(reflection)
        
        return DailyReflectionResponse(
            id=str(result.inserted_id),
            date=today,
            insight=reflection["insight"],
            question=reflection["question"],
            perspective=reflection["perspective"]
        )
    except Exception as e:
        logger.error(f"Generate reflection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chatbot endpoint with memory and context"""
    try:
        # Get chat history
        chat_history = await db.chat_history.find_one({"user_id": request.user_id})
        
        if not chat_history:
            chat_history = {
                "user_id": request.user_id,
                "messages": [],
                "created_at": datetime.now(timezone.utc)
            }
        
        # Add user message to history
        user_msg = {
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now(timezone.utc)
        }
        chat_history["messages"].append(user_msg)
        
        # Generate response
        system_prompt = """PROJECT MIRROR — SYSTEM PROMPT (STRICT SEPARATION MODE)

You are Project Mirror.
You are a reflection space — not a profiler, not a teacher, not a framework interpreter.

Hard Rule: Mirror vs Lenses separation

You MUST NOT mention any frameworks or profile terms in conversation, including but not limited to:
Human Design, Manifestor, Generator, Manifesting Generator, Projector, Reflector, authority, profile, gates, astrology, zodiac, houses, planets, numerology, life path, BaZi, Gene Keys, Enneagram, type, strategy, incarnation cross.

Even if these data exist in memory or context, they are internal-only and forbidden in Mirror conversations.

Exception: Lenses section only
Frameworks may be discussed ONLY if the user explicitly navigates to Lenses or directly asks:
- "What is my Human Design?"
- "Tell me about my chart"
- "What's my type?"
- "Can you explain the astrology?"

In those cases, FIRST say: "That information lives in the Lenses section, but I can share: [brief answer]. Would you like to explore more in Lenses?"

Mirror Conversation Style Rules:
- Do not label the user ("You are X").
- Do not predict outcomes.
- Do not give advice ("You should").
- Use neutral, grounded language.
- Offer perspectives, not conclusions.

Preferred phrases:
- "One way to look at this is…"
- "You may notice…"
- "If this resonates…"
- "Another perspective could be…"

Be brief, warm, and grounded. You are not a guru. You are not an explainer. You are a mirror."""
        
        response_text = await generate_ai_response(system_prompt, request.message, request.user_id)
        
        # Add assistant message to history
        assistant_msg = {
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.now(timezone.utc)
        }
        chat_history["messages"].append(assistant_msg)
        
        # Update chat history (keep last 20 messages)
        chat_history["messages"] = chat_history["messages"][-20:]
        chat_history["updated_at"] = datetime.now(timezone.utc)
        
        await db.chat_history.update_one(
            {"user_id": request.user_id},
            {"$set": chat_history},
            upsert=True
        )
        
        return ChatResponse(
            response=response_text,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/charts/{user_id}/details")
async def get_chart_details(user_id: str):
    """Get detailed chart information (for Lenses section ONLY)"""
    try:
        chart = await db.charts.find_one({"user_id": user_id})
        if not chart:
            raise HTTPException(status_code=404, detail="Chart not found")
        
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Extract astrology data
        astro = chart.get("astrology", {})
        planets_data = astro.get("planets", {})
        houses_data = astro.get("houses", {})
        
        # Build planets list for deep dive
        planets_list = []
        planet_order = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "North Node", "South Node"]
        for planet_name in planet_order:
            planet = planets_data.get(planet_name)
            if planet:
                planets_list.append({
                    "name": planet_name,
                    "sign": planet.get("sign"),
                    "degree": planet.get("degree"),
                    "longitude": planet.get("longitude"),
                    "longitude_in_sign": planet.get("degree"),  # Same as degree
                    "house": planet.get("house"),
                    "formatted": planet.get("formatted")
                })
        
        # Build houses list for snapshot/deep dive
        houses_list = houses_data.get("formatted_cusps", [])
        
        # Return formatted chart data for Lenses
        return {
            "computation_version": "mirror-deterministic-v1",
            "human_design": {
                "type": chart.get("human_design", {}).get("type"),
                "authority": chart.get("human_design", {}).get("authority"),
                "profile": chart.get("human_design", {}).get("profile"),
                "incarnation_cross": chart.get("human_design", {}).get("incarnation_cross"),
                "strategy": chart.get("human_design", {}).get("strategy"),
                "personality_sun": chart.get("human_design", {}).get("personality", {}).get("Sun"),
                "design_sun": chart.get("human_design", {}).get("design", {}).get("Sun"),
                "defined_centers": chart.get("human_design", {}).get("defined_centers", []),
                "defined_channels": chart.get("human_design", {}).get("defined_channels", []),
                "definition": chart.get("human_design", {}).get("definition"),
                "design_datetime_utc_iso": chart.get("human_design", {}).get("design_datetime_utc_iso")
            },
            "astrology": {
                "sun": planets_data.get("Sun"),
                "moon": planets_data.get("Moon"),
                "rising": {
                    "sign": houses_data.get("formatted_cusps", [{}])[0].get("sign") if houses_data.get("formatted_cusps") else None,
                    "degree": houses_data.get("formatted_cusps", [{}])[0].get("degree") if houses_data.get("formatted_cusps") else None,
                    "longitude": houses_data.get("ascendant"),
                    "longitude_in_sign": houses_data.get("formatted_cusps", [{}])[0].get("degree") if houses_data.get("formatted_cusps") else None,
                    "formatted": houses_data.get("formatted_cusps", [{}])[0].get("formatted") if houses_data.get("formatted_cusps") else None
                },
                "mc": {
                    "longitude": houses_data.get("mc"),
                    "sign": None,  # Would need to calculate from mc longitude
                    "degree": None
                },
                "chart_type": astro.get("chart_type"),
                "sidereal_settings": astro.get("sidereal_settings"),
                "planets": planets_list,
                "houses": houses_list
            },
            "numerology": {
                "life_path": chart.get("numerology", {}).get("life_path"),
                "expression": chart.get("numerology", {}).get("expression")
            }
        }
    except Exception as e:
        logger.error(f"Get chart details error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/lenses")
async def get_lenses():
    """Get information about all interpretive lenses"""
    return {
        "lenses": [
            {
                "name": "True Sidereal Astrology",
                "description": "A lens for understanding cosmic rhythms and archetypal patterns",
                "helps_with": "Seeing cycles, timing, and energetic influences",
                "does_not": "Predict events or determine destiny",
                "icon": "stars"
            },
            {
                "name": "Human Design",
                "description": "A synthesis showing how you're designed to interact with the world",
                "helps_with": "Understanding your natural decision-making and energy type",
                "does_not": "Tell you who you should be or limit your choices",
                "icon": "body"
            },
            {
                "name": "Numerology",
                "description": "A system revealing patterns in numbers and life paths",
                "helps_with": "Recognizing themes and personal symbolism",
                "does_not": "Guarantee outcomes or define your identity",
                "icon": "numbers"
            },
            {
                "name": "Levels of Consciousness",
                "description": "A map of emotional and spiritual development (Hawkins Scale)",
                "helps_with": "Understanding where you are and what might shift",
                "does_not": "Judge or rank people's worth",
                "icon": "levels"
            }
        ]
    }


# ============================================
# Mirror Chat Endpoint - The Primary Intelligence
# ============================================

# In-memory chat sessions (in production, store in MongoDB)
chat_sessions: Dict[str, List[Dict]] = {}

@api_router.post("/mirror/chat", response_model=MirrorChatResponse)
async def mirror_chat(request: MirrorChatRequest):
    """
    Mirror Chat - The reflective companion AI.
    
    - lens=None: Generalist mode (integrates all lenses)
    - lens="astrology": Constrained to astrology lens
    - lens="human_design": Constrained to Human Design lens
    - lens="numerology": Constrained to numerology lens
    """
    is_lens = request.lens is not None
    
    # ===== RATE LIMITING =====
    if not check_rate_limit(request.user_id, is_lens):
        remaining = get_rate_limit_remaining(request.user_id, is_lens)
        limit_type = "lens" if is_lens else "mirror"
        logger.warning(f"Rate limit exceeded for user {request.user_id}, type={limit_type}")
        raise HTTPException(
            status_code=429, 
            detail="Mirror needs a pause. Try again in a little while."
        )
    
    try:
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        # Generate or use existing session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get user's chart data for context
        user = await db.users.find_one({"_id": ObjectId(request.user_id)})
        chart = await db.charts.find_one({"user_id": request.user_id})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # PRECONDITION CHECK: For numerology lens, we require birth_date
        if request.lens == "numerology" and not user.get('birth_date'):
            return MirrorChatResponse(
                response="I'd love to explore numerology with you, but I need your birth date to calculate your numbers. You can add this in your profile settings.",
                session_id=session_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                memory_update=None,
                thread=None
            )
        
        # Build context from chart data
        context_parts = []
        
        # User basics
        context_parts.append(f"User's name: {user.get('name', 'Unknown')}")
        context_parts.append(f"Birth date: {user.get('birth_date')}")
        
        if chart:
            # Astrology context
            astro = chart.get('astrology', {})
            if astro and (request.lens is None or request.lens == "astrology"):
                planets = astro.get('planets', {})
                sun = planets.get('Sun', {})
                moon = planets.get('Moon', {})
                houses = astro.get('houses', {})
                rising = houses.get('formatted_cusps', [{}])[0] if houses.get('formatted_cusps') else {}
                
                context_parts.append("\n--- ASTROLOGY (True Sidereal) ---")
                context_parts.append(f"Sun: {sun.get('formatted', 'Unknown')} ({sun.get('sign', 'Unknown')})")
                context_parts.append(f"Moon: {moon.get('formatted', 'Unknown')} ({moon.get('sign', 'Unknown')})")
                context_parts.append(f"Rising: {rising.get('formatted', 'Unknown')} ({rising.get('sign', 'Unknown')})")
                
                # Add other planets if in astrology lens
                if request.lens == "astrology":
                    for planet_name in ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']:
                        planet = planets.get(planet_name, {})
                        if planet:
                            context_parts.append(f"{planet_name}: {planet.get('formatted', 'Unknown')}")
            
            # Human Design context
            hd = chart.get('human_design', {})
            if hd and (request.lens is None or request.lens == "human_design"):
                context_parts.append("\n--- HUMAN DESIGN ---")
                context_parts.append(f"Type: {hd.get('type', 'Unknown')}")
                context_parts.append(f"Strategy: {hd.get('strategy', 'Unknown')}")
                context_parts.append(f"Authority: {hd.get('authority', 'Unknown')}")
                context_parts.append(f"Profile: {hd.get('profile', 'Unknown')}")
            
            # Numerology context
            numerology = chart.get('numerology', {})
            if numerology and (request.lens is None or request.lens == "numerology"):
                # Extract life path (handle both old and new format)
                life_path_data = numerology.get('life_path')
                if isinstance(life_path_data, int):
                    life_path = life_path_data
                elif isinstance(life_path_data, dict):
                    life_path = life_path_data.get('number', 'Unknown')
                else:
                    life_path = 'Unknown'
                
                context_parts.append("\n--- NUMEROLOGY ---")
                context_parts.append(f"Life Path: {life_path}")
                
                # Birthday number if available
                birthday = numerology.get('birthday')
                if birthday:
                    if isinstance(birthday, dict):
                        context_parts.append(f"Birthday Number: {birthday.get('number', 'Unknown')}")
                    else:
                        context_parts.append(f"Birthday Number: {birthday}")
                
                # Name-based numbers (only if available)
                has_name_numbers = numerology.get('has_name_numbers', False)
                if has_name_numbers:
                    expression = numerology.get('expression')
                    soul_urge = numerology.get('soul_urge')
                    personality = numerology.get('personality')
                    
                    if expression:
                        exp_num = expression.get('number') if isinstance(expression, dict) else expression
                        context_parts.append(f"Expression: {exp_num}")
                    if soul_urge:
                        su_num = soul_urge.get('number') if isinstance(soul_urge, dict) else soul_urge
                        context_parts.append(f"Soul Urge: {su_num}")
                    if personality:
                        pers_num = personality.get('number') if isinstance(personality, dict) else personality
                        context_parts.append(f"Personality: {pers_num}")
                else:
                    context_parts.append("Expression/Soul Urge/Personality: Not provided (requires full birth name)")
                
                # Calculate current cycles for numerology lens
                if request.lens == "numerology":
                    birth_date = user.get('birth_date')
                    if birth_date:
                        from calculations.numerology import get_numerology_cycles
                        today = datetime.now()
                        cycles = get_numerology_cycles(birth_date, today)
                        
                        context_parts.append("\n--- CURRENT CYCLES ---")
                        context_parts.append(f"Personal Year: {cycles['personal_year']['number']} ({cycles['personal_year']['description']})")
                        context_parts.append(f"Personal Month: {cycles['personal_month']['number']} ({cycles['personal_month']['description']})")
                        context_parts.append(f"Personal Day: {cycles['personal_day']['number']} ({cycles['personal_day']['description']})")
        
        # Add recent journal entries if requested (LIMITED to MAX_JOURNAL_ENTRIES)
        if request.include_journal:
            journal_entries = await db.journal.find(
                {"user_id": request.user_id}
            ).sort("timestamp", -1).limit(MAX_JOURNAL_ENTRIES).to_list(MAX_JOURNAL_ENTRIES)
            
            if journal_entries:
                context_parts.append("\n--- RECENT JOURNAL ENTRIES ---")
                for entry in reversed(journal_entries):  # Show oldest first
                    timestamp = entry.get('timestamp', datetime.now())
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    date_str = timestamp.strftime("%Y-%m-%d %H:%M")
                    content = entry.get('content', '')[:300]  # Truncate long entries
                    context_parts.append(f"[{date_str}] {content}")
        
        # Build system prompt
        system_prompt = MIRROR_SYSTEM_PROMPT
        
        # Add lens-specific prompt if constrained
        if request.lens and request.lens in LENS_PROMPTS:
            system_prompt += "\n" + LENS_PROMPTS[request.lens]
        
        # ===== KEYSTONE THREAD MODE =====
        is_keystone_followup = request.keystone_context is not None
        thread_state = None
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        if is_keystone_followup:
            # Starting or restarting a keystone thread
            kc = request.keystone_context
            keystone_insert = KEYSTONE_CONTINUATION_INSERT.format(
                title=kc.title,
                keystone=kc.keystone,
                reflect_question=kc.reflect_question,
                micro_affirmation=kc.micro_affirmation,
                tone=kc.tone
            )
            system_prompt += "\n" + keystone_insert
            logger.info(f"[Mirror Chat] Keystone continuation mode for user {request.user_id}, date={kc.date}")
            
            # Create/overwrite thread state with remaining_turns=3
            thread_state = {
                "user_id": request.user_id,
                "thread_type": "daily_keystone",
                "thread_date": kc.date,
                "daily_seed": kc.daily_seed,
                "tone": kc.tone,
                "title": kc.title,
                "keystone": kc.keystone,
                "reflect_question": kc.reflect_question,
                "micro_affirmation": kc.micro_affirmation,
                "remaining_turns": 3,  # Will be decremented after reply
                "created_at_iso": datetime.now(timezone.utc).isoformat(),
                "updated_at_iso": datetime.now(timezone.utc).isoformat()
            }
            
            await db.user_thread_state.update_one(
                {"user_id": request.user_id},
                {"$set": thread_state},
                upsert=True
            )
            logger.info(f"[Thread] Created keystone thread for user {request.user_id}, remaining_turns=3")
        
        elif request.lens is None:
            # Check for active thread state (only for generalist chat, not lens chats)
            existing_thread = await db.user_thread_state.find_one({"user_id": request.user_id})
            
            if existing_thread and existing_thread.get("remaining_turns", 0) > 0:
                # Verify it's for today's date
                if existing_thread.get("thread_date") == current_date:
                    thread_state = existing_thread
                    turn_number = 4 - thread_state["remaining_turns"]  # 1, 2, or 3
                    
                    # Inject thread anchor prompt
                    thread_anchor = THREAD_ANCHOR_INSERT.format(
                        tone=thread_state.get("tone", "unclear"),
                        turn_number=turn_number
                    )
                    system_prompt += "\n" + thread_anchor
                    logger.info(f"[Thread] Active thread for user {request.user_id}, turn={turn_number}, remaining={thread_state['remaining_turns']}")
                else:
                    # Thread is from a different day, clear it
                    await db.user_thread_state.delete_one({"user_id": request.user_id})
                    logger.info(f"[Thread] Cleared stale thread for user {request.user_id} (date mismatch)")
        
        # Add context
        system_prompt += "\n\n--- USER CONTEXT ---\n" + "\n".join(context_parts)
        
        # Get or create chat history for session
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
        
        history = chat_sessions[session_id]
        
        # ===== LLM CALL WITH FALLBACK =====
        response_text = None
        try:
            # Call LLM for reflective reply
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=session_id,
                system_message=system_prompt
            )
            chat.with_model("openai", "gpt-5.2")
            
            # Send user message
            message = UserMessage(text=request.message)
            response_text = await chat.send_message(message)
            
            # Log request (no user text)
            logger.info(f"Mirror chat: user={request.user_id}, lens={request.lens or 'generalist'}")
            
        except Exception as llm_error:
            logger.error(f"LLM call failed for user {request.user_id}: {type(llm_error).__name__}")
            response_text = FALLBACK_RESPONSE
        
        # ===== GUARDRAIL ENFORCEMENT (only if not fallback) =====
        if response_text != FALLBACK_RESPONSE:
            violations = check_guardrail_violations(response_text)
            if violations:
                # Log violations (types and counts only, no user text)
                violation_types = list(violations.keys())
                for vtype in violation_types:
                    guardrail_violation_counts[vtype] += 1
                guardrail_violation_counts["total_rewrites"] += 1
                
                logger.warning(f"Guardrail violations detected: {violation_types}. Total rewrites: {guardrail_violation_counts['total_rewrites']}")
                
                # Rewrite for compliance
                response_text = await rewrite_for_compliance(response_text, violations)
                logger.info(f"Response rewritten for compliance. Violation types: {violation_types}")
        # ===== END GUARDRAIL ENFORCEMENT =====
        
        # Store in history
        history.append({"role": "user", "content": request.message})
        history.append({"role": "assistant", "content": response_text})
        
        # Limit history size to MAX_CHAT_HISTORY messages
        if len(history) > MAX_CHAT_HISTORY * 2:  # *2 for user+assistant pairs
            chat_sessions[session_id] = history[-(MAX_CHAT_HISTORY * 2):]
        
        # Generate Memory Update (asynchronously, in parallel with response)
        memory_update = None
        try:
            # Build context for memory analysis
            memory_context_parts = []
            
            # Add recent conversation history
            memory_context_parts.append("--- RECENT CONVERSATION ---")
            for msg in history[-10:]:  # Last 10 messages
                role = "User" if msg['role'] == 'user' else "Mirror"
                memory_context_parts.append(f"{role}: {msg['content'][:500]}")
            
            # Add journal entries if available (LIMITED to MAX_JOURNAL_ENTRIES)
            if request.include_journal:
                journal_entries = await db.journal.find(
                    {"user_id": request.user_id}
                ).sort("timestamp", -1).limit(MAX_JOURNAL_ENTRIES).to_list(MAX_JOURNAL_ENTRIES)
                
                if journal_entries:
                    memory_context_parts.append("\n--- RECENT JOURNAL ENTRIES ---")
                    for entry in reversed(journal_entries):
                        content = entry.get('content', '')[:300]
                        memory_context_parts.append(f"- {content}")
            
            # Build memory analysis prompt
            memory_prompt = MEMORY_UPDATE_PROMPT + "\n\n" + "\n".join(memory_context_parts)
            
            # Create separate LLM call for memory update
            memory_chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"memory_{session_id}",
                system_message=memory_prompt
            )
            memory_chat.with_model("openai", "gpt-5.2")
            
            # Request structured memory update
            memory_message = UserMessage(text="Analyze the above and generate a memory_update JSON object.")
            memory_response = await memory_chat.send_message(memory_message)
            
            # Parse JSON response
            import json
            import re
            
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', memory_response)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = memory_response.strip()
            
            memory_data = json.loads(json_str)
            
            # Validate and sanitize
            memory_update = MemoryUpdate(
                themes=memory_data.get('themes', [])[:5],
                recurring_tensions=memory_data.get('recurring_tensions', [])[:5],
                supportive_moves=memory_data.get('supportive_moves', [])[:5],
                drainers=memory_data.get('drainers', [])[:5],
                inferred_state=memory_data.get('inferred_state', 'unclear'),
                confidence=min(1.0, max(0.0, float(memory_data.get('confidence', 0.5)))),
                evidence=memory_data.get('evidence', [])[:3],
                updated_at_iso=datetime.now(timezone.utc).isoformat()
            )
            
            # Validate inferred_state
            valid_states = ['grounding', 'stabilizing', 'exploring', 'integrating', 'unclear']
            if memory_update.inferred_state not in valid_states:
                memory_update.inferred_state = 'unclear'
            
            # Store memory update in database (overwrite previous)
            await db.user_memory.update_one(
                {"user_id": request.user_id},
                {"$set": {
                    "user_id": request.user_id,
                    "memory_update": memory_update.dict(),
                    "updated_at": datetime.now(timezone.utc)
                }},
                upsert=True
            )
            
            logger.info(f"Memory update stored for user {request.user_id}: state={memory_update.inferred_state}, confidence={memory_update.confidence}")
            
            # Write timeline event for consciousness tracking (privacy-safe, no raw text)
            try:
                timeline_event = {
                    "user_id": request.user_id,
                    "session_id": session_id,
                    "created_at_iso": datetime.now(timezone.utc).isoformat(),
                    "event_type": "keystone_followup" if is_keystone_followup else "mirror_chat_turn",
                    "inferred_state": memory_update.inferred_state,
                    "confidence": memory_update.confidence,
                    "themes": memory_update.themes[:2],  # max 2 themes
                    "tension": memory_update.recurring_tensions[0] if memory_update.recurring_tensions else None,
                    "source": "keystone_continuation" if is_keystone_followup else "mirror_chat",
                    "keystone_date": request.keystone_context.date if is_keystone_followup else None,
                    "version": "v1"
                }
                
                await db.user_timeline.insert_one(timeline_event)
                logger.info(f"Timeline event recorded for user {request.user_id}: type={timeline_event['event_type']}, state={memory_update.inferred_state}")
                
            except Exception as timeline_error:
                logger.warning(f"Timeline event write failed: {timeline_error}")
                # Continue without timeline - don't fail the request
            
        except Exception as mem_error:
            logger.warning(f"Memory update generation failed: {mem_error}")
            # Continue without memory update - don't fail the whole request
        
        # ===== THREAD STATE UPDATE =====
        # Decrement remaining_turns after successful reply
        thread_metadata = None
        if thread_state and thread_state.get("remaining_turns", 0) > 0:
            new_remaining = thread_state["remaining_turns"] - 1
            
            await db.user_thread_state.update_one(
                {"user_id": request.user_id},
                {"$set": {
                    "remaining_turns": new_remaining,
                    "updated_at_iso": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            thread_metadata = {
                "active": new_remaining > 0,
                "thread_type": thread_state.get("thread_type", "daily_keystone"),
                "thread_date": thread_state.get("thread_date"),
                "remaining_turns": new_remaining,
                "title": thread_state.get("title"),
                "keystone": thread_state.get("keystone"),
                "reflect_question": thread_state.get("reflect_question"),
                "micro_affirmation": thread_state.get("micro_affirmation"),
                "tone": thread_state.get("tone")
            }
            
            logger.info(f"[Thread] Decremented remaining_turns for user {request.user_id}: {thread_state['remaining_turns']} -> {new_remaining}")
            
            if new_remaining == 0:
                logger.info(f"[Thread] Thread completed for user {request.user_id}")
        
        return MirrorChatResponse(
            response=response_text,
            session_id=session_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            memory_update=memory_update,
            thread=thread_metadata
        )
        
    except Exception as e:
        logger.error(f"Mirror chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/mirror/chat/{session_id}")
async def clear_chat_session(session_id: str):
    """Clear a chat session history"""
    if session_id in chat_sessions:
        del chat_sessions[session_id]
    return {"message": "Session cleared"}


# ============================================
# Timeline Endpoint - "You Over Time" History
# ============================================

class TimelineEvent(BaseModel):
    created_at_iso: str
    inferred_state: str
    confidence: float
    themes: List[str]
    tension: Optional[str] = None
    event_type: str

class TimelineResponse(BaseModel):
    events: List[TimelineEvent]

@api_router.get("/timeline/{user_id}", response_model=TimelineResponse)
async def get_user_timeline(user_id: str, days: int = 7):
    """
    Get user's timeline events for the last N days.
    Returns lightweight consciousness tracking data (no raw text).
    """
    try:
        # Calculate date cutoff
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_iso = cutoff_date.isoformat()
        
        # Query timeline events
        events_cursor = db.user_timeline.find(
            {
                "user_id": user_id,
                "created_at_iso": {"$gte": cutoff_iso}
            }
        ).sort("created_at_iso", -1).limit(50)
        
        events_raw = await events_cursor.to_list(50)
        
        # Transform to response format (strip internal fields)
        events = []
        for e in events_raw:
            events.append(TimelineEvent(
                created_at_iso=e.get("created_at_iso", ""),
                inferred_state=e.get("inferred_state", "unclear"),
                confidence=e.get("confidence", 0.0),
                themes=e.get("themes", [])[:2],
                tension=e.get("tension"),
                event_type=e.get("event_type", "mirror_chat_turn")
            ))
        
        return TimelineResponse(events=events)
        
    except Exception as e:
        logger.error(f"Timeline fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Mirror Home Reflection - "Quiet Recognition"
# ============================================

# System prompt for generating the emotional keystone reflection
# =====================================================================
# DAILY EMOTIONAL KEYSTONE - Prompt 12
# Deterministic-per-day, deeply personalized home reflection
# =====================================================================

KEYSTONE_VARIANT_TEMPLATES = [
    # Each template shapes the structure subtly differently
    {
        "id": "recognition_first",
        "opening": "recognition",
        "structure": "Notice what's underneath → Name the tension → Offer opening"
    },
    {
        "id": "tension_first", 
        "opening": "tension",
        "structure": "Name the pull between two parts → Recognize what's present → Gentle possibility"
    },
    {
        "id": "body_anchored",
        "opening": "somatic",
        "structure": "Start with body/felt sense → Move to inner landscape → End with breath/pause"
    },
    {
        "id": "time_aware",
        "opening": "temporal",
        "structure": "Reference the arc of recent days → What seems to be shifting → What remains steady"
    },
    {
        "id": "quiet_witness",
        "opening": "observer",
        "structure": "Describe as if watching from the outside → Name what's visible → Note what's underneath"
    },
    {
        "id": "permission_giver",
        "opening": "allowing",
        "structure": "Acknowledge what might feel hard to allow → Normalize the tension → Open space"
    },
    {
        "id": "threshold_moment",
        "opening": "threshold",
        "structure": "Mark this moment as a pause → Notice what's been carried → What can be set down"
    },
    {
        "id": "parts_dialogue",
        "opening": "multiplicity",
        "structure": "A part of you X, another part Y → They can coexist → No need to resolve"
    }
]

DAILY_KEYSTONE_PROMPT = """You are Mirror generating a Daily Emotional Keystone.

ROLE: Create a moment of "quiet recognition" — the user should feel seen without being labeled.

TODAY'S VARIANT: {variant_template}
STRUCTURAL APPROACH: {variant_structure}

USER'S LENS SYNTHESIS (do NOT name any system — use archetypal phrasing):
{lens_context}

RECENT LIVED EXPERIENCE (if available):
{lived_context}

CURRENT TONE GUIDANCE: {tone_guidance}

=== OUTPUT REQUIREMENTS ===

You must return ONLY valid JSON in this exact format:
{{
  "title": "3-6 word poetic title (no punctuation except comma)",
  "keystone": "2-3 sentences following the structural approach. Sentence 1: Recognition. Sentence 2: Tension. Sentence 3 (optional): Opening.",
  "reflect_question": "One gentle question inviting self-inquiry (not advice-seeking)",
  "micro_affirmation": "8-14 words, non-prescriptive, grounding statement"
}}

=== LANGUAGE GUARDRAILS (MUST ENFORCE) ===

NEVER USE:
- Predictions: "will", "going to happen", "this means you'll"
- Prescriptions: "you should", "you need to", "try to"
- Diagnoses or labels
- Identity locks: "you are X" → instead use "you may notice", "it can feel like", "a part of you"
- System names: NO "astrology", "Human Design", "numerology", "Pisces", "Manifestor", "life path", etc.
- Spiritual jargon: "meant to", "purpose", "destiny", "lesson", "universe wants"

ALWAYS USE:
- Present-tense, observational language
- Archetypal phrasing: "a part of you moves first", "a part of you needs time", "something in you seeks wide horizons"
- Noticing language: "there may be", "it can feel like", "something seems to"
- Gentle uncertainty: "perhaps", "it might be", "you may notice"

=== STRUCTURE FOR KEYSTONE ===

Sentence 1 (Recognition): What seems present underneath the surface — name it without explaining
Sentence 2 (Tension): Two pulls that may coexist — honor both without resolving
Sentence 3 (Opening, optional): A doorway or possibility — not advice, just space

The question should invite reflection, not action.
The micro_affirmation grounds without directing.

Generate the JSON now."""


class DailyKeystoneResponse(BaseModel):
    date: str
    title: str
    keystone: str
    reflect_question: str
    micro_affirmation: str
    source_signals: dict
    daily_seed: str


# Keep old response model for backwards compatibility
class MirrorHomeResponse(BaseModel):
    reflection: str
    generated_at: str
    is_first_visit: bool = False


@api_router.get("/mirror/home/{user_id}")
async def get_daily_keystone(user_id: str, date: Optional[str] = None, force_refresh: bool = False):
    """
    Generate the Daily Emotional Keystone.
    Deterministic per day + deeply personalized using lenses + lived data.
    
    Args:
        user_id: The user's ID
        date: Optional date in YYYY-MM-DD format. If not provided, uses UTC date.
        force_refresh: If true, regenerate even if cached.
    
    Returns:
        DailyKeystoneResponse with title, keystone, reflect_question, micro_affirmation
    """
    import hashlib
    import json as json_module
    
    COMPUTATION_VERSION = "keystone-v1"
    
    try:
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        # Get user and chart data
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        chart = await db.charts.find_one({"user_id": user_id})
        
        # Determine the date to use
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                target_date = datetime.now(timezone.utc).date()
        else:
            # Use UTC date as fallback
            target_date = datetime.now(timezone.utc).date()
        
        date_str = target_date.strftime("%Y-%m-%d")
        
        # Create deterministic daily seed
        seed_input = f"{user_id}:{date_str}:{COMPUTATION_VERSION}"
        daily_seed = hashlib.sha256(seed_input.encode()).hexdigest()[:12]
        
        # =====================================================================
        # CHECK CACHE FOR DETERMINISTIC RESPONSE
        # =====================================================================
        if not force_refresh:
            cached = await db.daily_keystones.find_one({
                "user_id": user_id,
                "date": date_str,
                "daily_seed": daily_seed
            })
            if cached:
                logger.info(f"[Keystone] Returning cached keystone for {user_id} on {date_str}")
                return {
                    "date": cached["date"],
                    "title": cached["title"],
                    "keystone": cached["keystone"],
                    "reflect_question": cached["reflect_question"],
                    "micro_affirmation": cached["micro_affirmation"],
                    "source_signals": cached["source_signals"],
                    "daily_seed": cached["daily_seed"],
                    "reflection": cached["keystone"],
                    "generated_at": cached["generated_at"],
                    "is_first_visit": cached.get("is_first_visit", False)
                }
        
        # Select variant template using seed (deterministic)
        variant_index = int(daily_seed[:2], 16) % len(KEYSTONE_VARIANT_TEMPLATES)
        variant = KEYSTONE_VARIANT_TEMPLATES[variant_index]
        
        # =====================================================================
        # BUILD LENS CONTEXT (without naming systems)
        # =====================================================================
        lens_parts = []
        user_name = user.get('name', 'this person')
        
        # Sign qualities mapping (internal use only)
        sign_qualities = {
            'Aries': 'initiating energy, directness, a part that moves first',
            'Taurus': 'steadiness, sensory awareness, a part that builds slowly',
            'Gemini': 'curiosity, adaptability, a part that explores many paths',
            'Cancer': 'emotional depth, nurturing instinct, a part that protects what matters',
            'Leo': 'creative expression, warmth, a part that seeks to be seen',
            'Virgo': 'attention to detail, discernment, a part that refines',
            'Libra': 'relational awareness, harmony-seeking, a part that weighs and balances',
            'Scorpio': 'intensity, depth-seeking, a part that goes underneath',
            'Sagittarius': 'expansiveness, truth-seeking, a part that seeks wide horizons',
            'Capricorn': 'structure, long-term thinking, a part that climbs steadily',
            'Aquarius': 'independence, unconventionality, a part that stands apart',
            'Pisces': 'permeability, imagination, a part that dissolves boundaries'
        }
        
        type_qualities = {
            'Generator': 'sustained energy that responds to life, satisfaction-seeking',
            'Manifesting Generator': 'multi-passionate energy, efficiency in action',
            'Projector': 'perceptive awareness, sensitivity to being recognized',
            'Manifestor': 'initiating force, impact-making independence',
            'Reflector': 'reflective awareness, sensitivity to environment'
        }
        
        authority_qualities = {
            'Sacral': 'gut-level knowing, responses arise in the moment',
            'Emotional': 'clarity comes over time, waves of feeling',
            'Splenic': 'instinctive knowing, quiet inner alerts',
            'Ego': 'willpower-based clarity, commitment matters',
            'Self-Projected': 'hearing oneself speak brings clarity',
            'Mental': 'processing through others, environment matters',
            'Lunar': 'patience with long cycles, month-long rhythms'
        }
        
        life_path_qualities = {
            1: 'pioneering independence, self-direction themes',
            2: 'partnership sensitivity, diplomatic currents',
            3: 'creative expression, joy-seeking undertones',
            4: 'foundational building, practical mastery',
            5: 'freedom-seeking, change-embracing rhythms',
            6: 'nurturing responsibility, harmony-creating',
            7: 'inner searching, analytical depth',
            8: 'material mastery, power dynamics awareness',
            9: 'humanitarian breadth, completion themes',
            11: 'intuitive sensitivity, inspirational capacity',
            22: 'master building, large-scale vision',
            33: 'master teaching, compassionate service'
        }
        
        if chart:
            # Astrology synthesis
            astro = chart.get('astrology', {})
            
            # Get sun, moon, rising signs
            sun_sign = None
            moon_sign = None
            rising_sign = None
            mercury_sign = None
            mars_sign = None
            
            # Handle different data structures
            if 'sun_sign' in astro:
                sun_sign = astro.get('sun_sign')
                moon_sign = astro.get('moon_sign')
                rising_sign = astro.get('rising_sign')
            elif 'planets' in astro:
                planets = astro.get('planets', {})
                sun_data = planets.get('Sun', {})
                moon_data = planets.get('Moon', {})
                mercury_data = planets.get('Mercury', {})
                mars_data = planets.get('Mars', {})
                sun_sign = sun_data.get('sign') if isinstance(sun_data, dict) else None
                moon_sign = moon_data.get('sign') if isinstance(moon_data, dict) else None
                mercury_sign = mercury_data.get('sign') if isinstance(mercury_data, dict) else None
                mars_sign = mars_data.get('sign') if isinstance(mars_data, dict) else None
                # Rising might be in ascendant
                asc_data = astro.get('ascendant', astro.get('Ascendant', {}))
                rising_sign = asc_data.get('sign') if isinstance(asc_data, dict) else None
            
            if sun_sign and sun_sign in sign_qualities:
                lens_parts.append(f"Core presence: {sign_qualities[sun_sign]}")
            if moon_sign and moon_sign in sign_qualities:
                lens_parts.append(f"Emotional texture: {sign_qualities[moon_sign]}")
            if rising_sign and rising_sign in sign_qualities:
                lens_parts.append(f"How they meet the world: {sign_qualities[rising_sign]}")
            
            # Add supporting placements if available
            if mercury_sign and mercury_sign in sign_qualities:
                lens_parts.append(f"Mind pattern: {sign_qualities[mercury_sign]}")
            elif mars_sign and mars_sign in sign_qualities:
                lens_parts.append(f"Action style: {sign_qualities[mars_sign]}")
            
            # Human Design synthesis
            hd = chart.get('human_design', {})
            hd_type = hd.get('type', '')
            authority = hd.get('authority', '')
            profile = hd.get('profile', '')
            
            if hd_type and hd_type in type_qualities:
                lens_parts.append(f"Energy pattern: {type_qualities[hd_type]}")
            if authority and authority in authority_qualities:
                lens_parts.append(f"Decision texture: {authority_qualities[authority]}")
            if profile:
                # Interpret profile archetypally
                profile_meanings = {
                    '1/3': 'investigative experimentation, learning through doing',
                    '1/4': 'deep research shared through close connections',
                    '2/4': 'natural gifts emerging through relationships',
                    '2/5': 'hermit-like tendencies with practical influence',
                    '3/5': 'trial-and-error wisdom, problem-solving capacity',
                    '3/6': 'experimental becoming, eventual perspective',
                    '4/6': 'influential relationships, role model potential',
                    '4/1': 'networked foundation, investigative depth',
                    '5/1': 'practical solutions grounded in research',
                    '5/2': 'universal offerings, natural talents',
                    '6/2': 'role model becoming, hermit wisdom',
                    '6/3': 'perspective-gathering through experience'
                }
                if profile in profile_meanings:
                    lens_parts.append(f"Life approach: {profile_meanings[profile]}")
            
            # Numerology synthesis
            num = chart.get('numerology', {})
            life_path = num.get('life_path', {})
            if isinstance(life_path, dict):
                lp_num = life_path.get('number', 0)
            else:
                lp_num = life_path if isinstance(life_path, int) else 0
            
            if lp_num and lp_num in life_path_qualities:
                lens_parts.append(f"Life theme: {life_path_qualities[lp_num]}")
        
        lens_context = "\n".join(lens_parts) if lens_parts else "No lens data available — generate from presence alone."
        
        # =====================================================================
        # BUILD LIVED CONTEXT (recent timeline, journal, memory)
        # =====================================================================
        lived_parts = []
        source_signals_used = ["lens_core"]
        
        # Get last 3 timeline events
        timeline_events = await db.user_timeline.find(
            {"user_id": user_id}
        ).sort("created_at_iso", -1).limit(3).to_list(3)
        
        if timeline_events:
            source_signals_used.append("timeline")
            for evt in timeline_events:
                state = evt.get('inferred_state', 'present')
                themes = evt.get('themes', [])
                tension = evt.get('tension', '')
                if themes or tension:
                    lived_parts.append(f"Recent signal: state={state}, themes={themes[:2] if themes else []}, tension hint={tension[:50] if tension else 'none'}")
        
        # Get last 3 journal entries
        journal_entries = await db.journal_entries.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(3).to_list(3)
        
        if journal_entries:
            source_signals_used.append("journal")
            for entry in journal_entries:
                content = entry.get('content', '')[:100]
                themes = entry.get('themes', [])
                if content or themes:
                    lived_parts.append(f"Journal signal: themes={themes[:2] if themes else []}, tone hint from content length={len(content)}")
        
        # Get memory_update if present
        memory_update = user.get('memory_update', {})
        if memory_update:
            source_signals_used.append("memory")
            themes = memory_update.get('recurring_themes', [])
            tensions = memory_update.get('active_tensions', [])
            state = memory_update.get('inferred_state', '')
            if themes or tensions or state:
                lived_parts.append(f"Memory synthesis: themes={themes[:3] if themes else []}, tensions={tensions[:2] if tensions else []}, state={state}")
        
        lived_context = "\n".join(lived_parts) if lived_parts else "No lived data yet — this is their first meaningful engagement."
        
        # =====================================================================
        # DETERMINE TONE GUIDANCE
        # =====================================================================
        tone = "unclear"
        if memory_update:
            state = memory_update.get('inferred_state', '').lower()
            if 'grounded' in state or 'stable' in state:
                tone = "grounding"
            elif 'processing' in state or 'integrating' in state:
                tone = "integrating"
            elif 'exploring' in state or 'curious' in state:
                tone = "exploring"
            elif 'unsettled' in state or 'searching' in state:
                tone = "stabilizing"
        elif timeline_events:
            # Infer from recent timeline
            recent_state = timeline_events[0].get('inferred_state', '').lower() if timeline_events else ''
            if 'curious' in recent_state or 'exploring' in recent_state:
                tone = "exploring"
            elif 'grounded' in recent_state or 'settled' in recent_state:
                tone = "grounding"
            else:
                tone = "stabilizing"
        else:
            tone = "grounding"  # Default for first visit
        
        # =====================================================================
        # GENERATE KEYSTONE VIA LLM
        # =====================================================================
        system_prompt = DAILY_KEYSTONE_PROMPT.format(
            variant_template=variant['opening'],
            variant_structure=variant['structure'],
            lens_context=lens_context,
            lived_context=lived_context,
            tone_guidance=tone
        )
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"keystone_{user_id}_{date_str}_{daily_seed}",
            system_message=system_prompt
        )
        chat.with_model("openai", "gpt-5.2")
        
        user_prompt = f"Generate the Daily Keystone for {user_name} on {date_str}. Remember: return ONLY valid JSON, no markdown."
        message = UserMessage(text=user_prompt)
        response_text = await chat.send_message(message)
        
        # Parse JSON response
        try:
            # Clean up response (remove markdown if present)
            clean_response = response_text.strip()
            if clean_response.startswith("```"):
                # Remove markdown code blocks
                lines = clean_response.split("\n")
                clean_response = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            
            keystone_data = json_module.loads(clean_response)
        except json_module.JSONDecodeError as e:
            logger.error(f"Failed to parse keystone JSON: {e}, response: {response_text[:200]}")
            # Generate fallback
            keystone_data = {
                "title": "A Quiet Arrival",
                "keystone": f"Something in you brought you here today, {user_name}. That small act of pausing — even for a moment — is itself a form of attention.",
                "reflect_question": "What feels most present right now, underneath the surface?",
                "micro_affirmation": "You don't have to have it figured out to be here."
            }
        
        # Build response
        generated_at = datetime.now(timezone.utc).isoformat()
        is_first = len(timeline_events) == 0
        
        response_data = {
            "date": date_str,
            "title": keystone_data.get("title", "A Moment of Pause"),
            "keystone": keystone_data.get("keystone", "Something in you brought you here today."),
            "reflect_question": keystone_data.get("reflect_question", "What feels most present right now?"),
            "micro_affirmation": keystone_data.get("micro_affirmation", "You are already here."),
            "source_signals": {
                "used": source_signals_used,
                "tone": tone
            },
            "daily_seed": daily_seed,
            # Backwards compatibility
            "reflection": keystone_data.get("keystone", "Something in you brought you here today."),
            "generated_at": generated_at,
            "is_first_visit": is_first
        }
        
        # =====================================================================
        # CACHE THE RESPONSE FOR DETERMINISM
        # =====================================================================
        try:
            await db.daily_keystones.update_one(
                {"user_id": user_id, "date": date_str},
                {"$set": {
                    "user_id": user_id,
                    "date": date_str,
                    "daily_seed": daily_seed,
                    "title": response_data["title"],
                    "keystone": response_data["keystone"],
                    "reflect_question": response_data["reflect_question"],
                    "micro_affirmation": response_data["micro_affirmation"],
                    "source_signals": response_data["source_signals"],
                    "generated_at": generated_at,
                    "is_first_visit": is_first,
                    "cached_at": datetime.now(timezone.utc).isoformat()
                }},
                upsert=True
            )
            logger.info(f"[Keystone] Cached keystone for {user_id} on {date_str}")
        except Exception as cache_err:
            logger.warning(f"[Keystone] Failed to cache: {cache_err}")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Daily keystone error: {e}")
        # Return calm fallback
        fallback_date = date if date else datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return {
            "date": fallback_date,
            "title": "A Quiet Arrival",
            "keystone": "Something in you brought you here today. That's worth noticing.",
            "reflect_question": "What feels most present right now?",
            "micro_affirmation": "You don't have to have it figured out to be here.",
            "source_signals": {
                "used": ["fallback"],
                "tone": "grounding"
            },
            "daily_seed": "fallback",
            "reflection": "Something in you brought you here today. That's worth noticing.",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "is_first_visit": False
        }


# =====================================================================
# ASTROLOGY LENS ENDPOINTS
# =====================================================================

class AstrologySection(BaseModel):
    label: str
    body: str


class AstrologyResponse(BaseModel):
    title: str
    sections: List[AstrologySection]
    mirror_prompt: str
    core_placements: Optional[dict] = None
    date: Optional[str] = None


# =============================================================================
# BIRTH DATA VALIDATION
# =============================================================================

def validate_birth_data(user: dict) -> Tuple[bool, List[str]]:
    """
    Validate that all required birth data fields are present for computation.
    
    Required fields:
    - birth_date
    - birth_time (birth_time_local)
    - lat (from birth_location)
    - lon (from birth_location)
    - timezone (timezone_iana)
    
    Returns:
        Tuple of (is_valid, list_of_missing_fields)
    """
    missing = []
    
    # Check birth_date
    if not user.get('birth_date'):
        missing.append('birth_date')
    
    # Check birth_time
    if not user.get('birth_time'):
        missing.append('birth_time_local')
    
    # Check location coordinates
    location = user.get('birth_location', {})
    lat = location.get('latitude') or location.get('lat')
    lon = location.get('longitude') or location.get('lon')
    
    if lat is None:
        missing.append('lat')
    if lon is None:
        missing.append('lon')
    
    # Check timezone
    if not user.get('timezone'):
        missing.append('timezone_iana')
    
    return (len(missing) == 0, missing)


def get_incomplete_birth_data_response(missing_fields: List[str]) -> dict:
    """
    Generate a standardized error response for incomplete birth data.
    """
    return {
        "success": False,
        "error": "INCOMPLETE_BIRTH_DATA",
        "missing_fields": missing_fields,
        "message": "Birth data is incomplete. Please provide all required details to compute your chart.",
        "required_fields": ["birth_date", "birth_time_local", "lat", "lon", "timezone_iana"]
    }


async def get_user_astrology_data(user_id: str, auto_migrate: bool = True) -> Tuple[dict, dict]:
    """
    Fetch user and their astrology chart data.
    
    If auto_migrate=True (default), automatically checks if the chart is in an old format
    and triggers migration to the new, complete format with planets/houses.
    """
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    chart = await db.charts.find_one({"user_id": user_id})
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found. Complete onboarding first.")
    
    # =====================================================================
    # AUTO-MIGRATION: Check and upgrade old-format charts automatically
    # =====================================================================
    if auto_migrate:
        migrated, migration_msg, updated_chart = await check_and_migrate_astrology_chart(user_id)
        if migrated:
            logger.info(f"[AUTO-MIGRATE] Chart auto-migrated for user {user_id}: {migration_msg}")
            chart = updated_chart
        elif "Cannot migrate" in migration_msg or "failed" in migration_msg.lower():
            logger.warning(f"[AUTO-MIGRATE] Migration issue for user {user_id}: {migration_msg}")
    
    return user, chart


async def check_and_migrate_astrology_chart(user_id: str) -> Tuple[bool, str, dict]:
    """
    Check if chart has valid astrology data. If old format or missing houses/ascendant,
    automatically recompute the chart.
    
    Returns:
        Tuple of (migration_performed, status_message, updated_chart)
    """
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return (False, "User not found", {})
    
    chart = await db.charts.find_one({"user_id": user_id})
    if not chart:
        return (False, "Chart not found", {})
    
    astro = chart.get('astrology', {})
    
    # Check if needs migration
    needs_migration = False
    migration_reason = None
    
    # Case 1: Old format (just string signs, no planets/houses)
    if 'sun_sign' in astro and 'planets' not in astro:
        needs_migration = True
        migration_reason = "legacy_string_format"
    
    # Case 2: New format but missing houses
    elif 'planets' in astro:
        houses = astro.get('houses', {})
        if not houses:
            needs_migration = True
            migration_reason = "missing_houses"
        elif not houses.get('ascendant'):
            needs_migration = True
            migration_reason = "missing_ascendant"
        elif len(houses.get('cusps', [])) != 12:
            needs_migration = True
            migration_reason = "incomplete_houses"
    
    # Case 3: Empty astrology data
    elif not astro:
        needs_migration = True
        migration_reason = "empty_astrology"
    
    if not needs_migration:
        return (False, "Chart is current", chart)
    
    # Perform migration by recalculating chart
    logger.info(f"[MIGRATION] Auto-migrating chart for user {user_id}, reason: {migration_reason}")
    
    # Check required fields
    if not user.get('timezone'):
        return (False, f"Cannot migrate: missing timezone", chart)
    if not user.get('birth_time'):
        return (False, f"Cannot migrate: missing birth_time", chart)
    if not user.get('birth_date'):
        return (False, f"Cannot migrate: missing birth_date", chart)
    if not user.get('birth_location'):
        return (False, f"Cannot migrate: missing birth_location", chart)
    
    # Trigger recalculation
    try:
        from calculations.timezone_utils import resolve_birth_utc_with_debug
        from calculations.astrology import get_full_natal_chart
        from calculations.human_design import get_human_design_chart
        from calculations.numerology import get_full_numerology
        
        birth_date = user['birth_date']
        birth_time = user['birth_time']
        user_timezone = user['timezone']
        
        birth_date_str = birth_date.strftime("%Y-%m-%d") if isinstance(birth_date, datetime) else str(birth_date)
        
        resolution = resolve_birth_utc_with_debug(
            birth_date_str=birth_date_str,
            birth_time_str=birth_time,
            timezone_str=user_timezone
        )
        
        if not resolution["success"]:
            return (False, f"Migration failed: {resolution['error']}", chart)
        
        birth_datetime_utc = resolution["birth_utc"]
        location = user['birth_location']
        lat = location['latitude']
        lon = location['longitude']
        
        sidereal_settings = {
            "mode": "true_sidereal_user_defined",
            "svp_degrees": 31.2836,
            "reference_year": 2000,
            "yearly_increment": 0.0
        }
        
        # Recalculate
        astrology_chart = get_full_natal_chart(
            birth_datetime_utc, lat, lon,
            sidereal_settings=sidereal_settings,
            house_system="Equal"
        )
        
        human_design = get_human_design_chart(
            birth_datetime_utc, lat, lon,
            sidereal_settings=sidereal_settings
        )
        
        if isinstance(birth_date, str):
            birth_date = datetime.strptime(birth_date, "%Y-%m-%d")
        numerology = get_full_numerology(birth_date, user.get("name"))
        
        # Update chart in database
        chart_update = {
            "astrology": astrology_chart,
            "human_design": human_design,
            "numerology": numerology,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
            "migration_info": {
                "migrated_at": datetime.now(timezone.utc).isoformat(),
                "migration_reason": migration_reason,
                "timezone_iana": resolution['debug_stamp'].get('timezone_iana'),
                "resolved_offset": resolution['debug_stamp'].get('resolved_utc_offset_at_birth')
            }
        }
        
        await db.charts.update_one(
            {"user_id": user_id},
            {"$set": chart_update}
        )
        
        updated_chart = await db.charts.find_one({"user_id": user_id})
        logger.info(f"[MIGRATION] Successfully migrated chart for user {user_id}")
        
        return (True, f"Chart migrated from {migration_reason}", updated_chart)
        
    except Exception as e:
        logger.error(f"[MIGRATION] Failed to migrate chart for user {user_id}: {e}")
        return (False, f"Migration failed: {str(e)}", chart)
    
    return user, chart


def extract_astrology_placements(chart: dict) -> dict:
    """Extract key astrology placements from chart data.
    
    Returns dict with:
    - success: bool - True if all critical data present
    - error: str or None - Error code if success=False
    - sun_sign, sun_house, moon_sign, moon_house, rising_sign
    - debug_stamp: dict with diagnostic info
    """
    astro = chart.get('astrology', {})
    debug_stamp = {
        "chart_id": str(chart.get('_id', 'unknown')),
        "astro_keys": list(astro.keys()) if astro else [],
        "has_planets": 'planets' in astro,
        "has_houses": 'houses' in astro,
        "data_format": "unknown"
    }
    
    # Initialize
    sun_sign = None
    sun_house = None
    moon_sign = None
    moon_house = None
    rising_sign = None
    ascendant_degrees = None
    houses_computed = False
    
    # Handle OLD format (just string signs)
    if 'sun_sign' in astro and 'planets' not in astro:
        debug_stamp["data_format"] = "legacy_strings"
        sun_sign = astro.get('sun_sign')
        moon_sign = astro.get('moon_sign')
        rising_sign = astro.get('rising_sign')
        # Old format doesn't have houses, so we can't compute house placements
        houses_computed = False
    
    # Handle NEW format (full planetary data)
    elif 'planets' in astro:
        debug_stamp["data_format"] = "full_computed"
        planets = astro.get('planets', {})
        houses = astro.get('houses', {})
        
        # Extract Sun
        sun_data = planets.get('Sun', {})
        if isinstance(sun_data, dict):
            sun_sign = sun_data.get('sign')
            sun_house = sun_data.get('house')
            debug_stamp["sun_longitude"] = sun_data.get('longitude')
        
        # Extract Moon
        moon_data = planets.get('Moon', {})
        if isinstance(moon_data, dict):
            moon_sign = moon_data.get('sign')
            moon_house = moon_data.get('house')
            debug_stamp["moon_longitude"] = moon_data.get('longitude')
        
        # Extract Ascendant from houses structure
        if houses:
            ascendant_degrees = houses.get('ascendant')
            debug_stamp["ascendant_degrees"] = ascendant_degrees
            debug_stamp["house_system"] = houses.get('system')
            debug_stamp["cusps_count"] = len(houses.get('cusps', []))
            
            # Get rising sign from formatted cusps (House 1)
            formatted_cusps = houses.get('formatted_cusps', [])
            if formatted_cusps and len(formatted_cusps) > 0:
                rising_sign = formatted_cusps[0].get('sign')
                debug_stamp["rising_from"] = "formatted_cusps[0]"
            
            houses_computed = len(houses.get('cusps', [])) == 12
    
    # Determine if we have valid data
    has_critical_data = (
        sun_sign is not None and 
        moon_sign is not None and 
        rising_sign is not None
    )
    
    # For Deep Dive, we REQUIRE ascendant to be computed (not just a legacy string)
    ascendant_valid = (
        rising_sign is not None and 
        (debug_stamp["data_format"] == "full_computed" and ascendant_degrees is not None)
    )
    
    debug_stamp["has_critical_data"] = has_critical_data
    debug_stamp["ascendant_valid"] = ascendant_valid
    debug_stamp["houses_computed"] = houses_computed
    
    # Build result
    result = {
        "success": has_critical_data,
        "error": None if has_critical_data else "ASTROLOGY_DATA_INCOMPLETE",
        "sun_sign": sun_sign or "Unknown",
        "sun_house": sun_house,
        "moon_sign": moon_sign or "Unknown",
        "moon_house": moon_house,
        "rising_sign": rising_sign or "Unknown",
        "ascendant_degrees": ascendant_degrees,
        "houses_computed": houses_computed,
        "debug_stamp": debug_stamp
    }
    
    # Special error codes
    if not rising_sign or rising_sign == "Unknown":
        result["error"] = "ASCENDANT_COMPUTE_FAILED"
    elif not houses_computed and debug_stamp["data_format"] == "full_computed":
        result["error"] = "HOUSES_COMPUTE_FAILED"
    
    return result


@api_router.get("/astrology/summary/{user_id}")
async def get_astrology_summary(user_id: str):
    """
    Generate astrology summary - high-level profile synthesis.
    NO transits, NO dates, NO planet/house/aspect lists.
    """
    import json as json_module
    
    try:
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        # Fetch user first to validate birth data
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # PRECONDITION CHECK: Validate birth data before computation
        is_valid, missing_fields = validate_birth_data(user)
        if not is_valid:
            return get_incomplete_birth_data_response(missing_fields)
        
        user, chart = await get_user_astrology_data(user_id)
        placements = extract_astrology_placements(chart)
        
        # Build compact profile context (no raw lists)
        profile_context = f"""
Sun in {placements['sun_sign']}: Core identity orientation
Moon in {placements['moon_sign']}: Emotional processing style
Rising in {placements['rising_sign']}: Approach to new situations
"""
        
        # Build full prompt
        system_prompt = ASTROLOGY_GLOBAL_PROMPT + "\n\n" + ASTROLOGY_SUMMARY_PROMPT.format(
            profile_context=profile_context
        )
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"astro_summary_{user_id}_{datetime.now().strftime('%Y%m%d')}",
            system_message=system_prompt
        )
        chat.with_model("openai", "gpt-5.2")
        
        message = UserMessage(text="Generate the astrology summary for this user. Return ONLY valid JSON.")
        response_text = await chat.send_message(message)
        
        # Parse JSON response
        try:
            clean_response = response_text.strip()
            if clean_response.startswith("```"):
                lines = clean_response.split("\n")
                clean_response = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            
            result = json_module.loads(clean_response)
            
            # Apply guardrails to each section
            for section in result.get("sections", []):
                section["body"] = apply_astrology_guardrails(section["body"])
            
            result["mirror_prompt"] = apply_astrology_guardrails(result.get("mirror_prompt", ""))
            
            return result
            
        except json_module.JSONDecodeError as e:
            logger.error(f"Failed to parse astrology summary JSON: {e}")
            return {
                "title": "Your Astrology Profile",
                "sections": [
                    {"label": "Your Orientation", "body": f"With {placements['sun_sign']} as your core orientation, there's a particular quality to how you express your sense of self."},
                    {"label": "How You Process", "body": f"Your {placements['moon_sign']} Moon suggests a specific way of moving through emotional experience."},
                    {"label": "What Draws You", "body": f"The {placements['rising_sign']} rising lens shapes how you approach new situations."}
                ],
                "mirror_prompt": "What in this description feels recognisable to you?"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Astrology summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/astrology/today/{user_id}")
async def get_astrology_today(user_id: str):
    """
    Generate Today's Snapshot - daily-first astrology timing lens.
    2-3 themes max, optional "On the horizon" if major alignment within 7 days.
    """
    import json as json_module
    
    try:
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        # Fetch user first to validate birth data
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # PRECONDITION CHECK: Validate birth data before computation
        is_valid, missing_fields = validate_birth_data(user)
        if not is_valid:
            return get_incomplete_birth_data_response(missing_fields)
        
        user, chart = await get_user_astrology_data(user_id)
        placements = extract_astrology_placements(chart)
        
        today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Build natal context (compact)
        natal_context = f"""
Sun: {placements['sun_sign']} (house {placements['sun_house']})
Moon: {placements['moon_sign']} (house {placements['moon_house']})
Rising: {placements['rising_sign']}
"""
        
        # Build transit context (simplified symbolic weather)
        # In production, this would come from ephemeris calculations
        transit_context = """
Current planetary emphasis: general themes of reflection and recalibration.
No major outer planet transits requiring special attention.
General atmosphere: supportive of inward focus.
"""
        
        # Build full prompt
        system_prompt = ASTROLOGY_GLOBAL_PROMPT + "\n\n" + ASTROLOGY_TODAY_PROMPT.format(
            today_date=today_date,
            natal_context=natal_context,
            transit_context=transit_context
        )
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"astro_today_{user_id}_{today_date}",
            system_message=system_prompt
        )
        chat.with_model("openai", "gpt-5.2")
        
        message = UserMessage(text="Generate Today's Snapshot. Return ONLY valid JSON.")
        response_text = await chat.send_message(message)
        
        # Parse JSON response
        try:
            clean_response = response_text.strip()
            if clean_response.startswith("```"):
                lines = clean_response.split("\n")
                clean_response = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            
            result = json_module.loads(clean_response)
            
            # Apply guardrails
            for section in result.get("sections", []):
                section["body"] = apply_astrology_guardrails(section["body"])
            
            result["mirror_prompt"] = apply_astrology_guardrails(result.get("mirror_prompt", ""))
            result["date"] = today_date
            
            return result
            
        except json_module.JSONDecodeError as e:
            logger.error(f"Failed to parse astrology today JSON: {e}")
            return {
                "title": "Today's Snapshot",
                "date": today_date,
                "sections": [
                    {"label": "Today's Quality", "body": "A day that may invite quiet attention to what's already present."},
                    {"label": "What You May Notice", "body": "Patterns of perception that feel familiar, moments that ask for patience."}
                ],
                "mirror_prompt": "What quality does today seem to carry for you?"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Astrology today error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/astrology/deep-dive/{user_id}")
async def get_astrology_deep_dive(user_id: str):
    """
    Generate Deep Dive - Sun, Moon, Ascendant only.
    NO transits, NO timing, NO future implications.
    
    Returns success:false with error code if critical data missing.
    """
    import json as json_module
    
    try:
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        # Fetch user first to validate birth data
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # PRECONDITION CHECK: Validate birth data before computation
        is_valid, missing_fields = validate_birth_data(user)
        if not is_valid:
            return get_incomplete_birth_data_response(missing_fields)
        
        user, chart = await get_user_astrology_data(user_id)
        placements = extract_astrology_placements(chart)
        
        # =====================================================================
        # FAIL LOUDLY IF CRITICAL DATA MISSING
        # =====================================================================
        if not placements["success"] or placements["rising_sign"] == "Unknown":
            logger.warning(f"Astrology deep dive failed for user {user_id}: {placements['error']}")
            return {
                "success": False,
                "error": placements["error"] or "ASCENDANT_COMPUTE_FAILED",
                "message": "We couldn't compute your Ascendant. Your chart may need to be recalculated.",
                "debug_stamp": placements["debug_stamp"],
                "core_placements": {
                    "sun": placements["sun_sign"],
                    "moon": placements["moon_sign"],
                    "ascendant": None  # Explicitly null to signal missing
                }
            }
        
        # Build full prompt
        system_prompt = ASTROLOGY_GLOBAL_PROMPT + "\n\n" + ASTROLOGY_DEEP_DIVE_PROMPT.format(
            sun_sign=placements['sun_sign'],
            sun_house=placements['sun_house'] or "Unknown",
            moon_sign=placements['moon_sign'],
            moon_house=placements['moon_house'] or "Unknown",
            rising_sign=placements['rising_sign']
        )
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"astro_deep_{user_id}_{datetime.now().strftime('%Y%m%d')}",
            system_message=system_prompt
        )
        chat.with_model("openai", "gpt-5.2")
        
        message = UserMessage(text="Generate the Deep Dive for this user's core structure. Return ONLY valid JSON.")
        response_text = await chat.send_message(message)
        
        # Parse JSON response
        try:
            clean_response = response_text.strip()
            if clean_response.startswith("```"):
                lines = clean_response.split("\n")
                clean_response = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            
            result = json_module.loads(clean_response)
            
            # Apply guardrails
            for section in result.get("sections", []):
                section["body"] = apply_astrology_guardrails(section["body"])
            
            result["mirror_prompt"] = apply_astrology_guardrails(result.get("mirror_prompt", ""))
            
            # Ensure core_placements is included with house info
            result["core_placements"] = {
                "sun": placements['sun_sign'],
                "moon": placements['moon_sign'],
                "ascendant": placements['rising_sign'],
                "sun_house": placements.get('sun_house'),
                "moon_house": placements.get('moon_house'),
                "houses_computed": placements['debug_stamp'].get('houses_computed', False)
            }
            
            # Add success flag and debug stamp
            result["success"] = True
            result["debug_stamp"] = placements["debug_stamp"]
            
            return result
            
        except json_module.JSONDecodeError as e:
            logger.error(f"Failed to parse astrology deep dive JSON: {e}")
            return {
                "success": True,  # Data is valid, just LLM parsing failed
                "title": "Your Core Structure",
                "core_placements": {
                    "sun": placements['sun_sign'],
                    "moon": placements['moon_sign'],
                    "ascendant": placements['rising_sign'],
                    "sun_house": placements.get('sun_house'),
                    "moon_house": placements.get('moon_house'),
                    "houses_computed": placements['debug_stamp'].get('houses_computed', False)
                },
                "sections": [
                    {"label": "Sun: Your Core Orientation", "body": f"With your Sun in {placements['sun_sign']}, there's a particular quality to how you express your sense of self and purpose."},
                    {"label": "Moon: Your Emotional Texture", "body": f"Your Moon in {placements['moon_sign']} shapes how you process feeling and what helps you feel emotionally at home."},
                    {"label": "Ascendant: How You Meet the World", "body": f"{placements['rising_sign']} rising colours the lens through which you approach new situations and people."}
                ],
                "mirror_prompt": "What in these descriptions feels true to your lived experience?",
                "debug_stamp": placements["debug_stamp"]
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Astrology deep dive error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# HUMAN DESIGN LENS ENDPOINTS
# =====================================================================

def parse_incarnation_cross(raw_cross: str) -> Tuple[str, str]:
    """
    Parse incarnation cross string into label and gates notation.
    
    Input formats:
    - "Right Angle Cross of 37/5 | 40/35"
    - "Left Angle Cross of 4/49 | 8/14"
    - "Juxtaposition Cross of 51/57 | 25/46"
    - "Unknown"
    
    Returns:
    - (label, gates) tuple
    - label: "RAX of Rulership 2" or "LAX Migration 1" (if known) or "Right Angle Cross" (type only)
    - gates: "37/5 • 40/35" or "—" if unknown
    """
    if not raw_cross or raw_cross == 'Unknown':
        return ("—", "—")
    
    # Parse the format: "Type of G1/G2 | G3/G4"
    # Example: "Right Angle Cross of 37/5 | 40/35"
    cross_match = re.match(
        r'^(Right Angle Cross|Left Angle Cross|Juxtaposition Cross)\s+of\s+(\d+)/(\d+)\s*\|\s*(\d+)/(\d+)$',
        raw_cross.strip()
    )
    
    if not cross_match:
        # Couldn't parse, return what we have
        return (raw_cross, "—")
    
    cross_type = cross_match.group(1)
    p_sun = int(cross_match.group(2))
    d_sun = int(cross_match.group(3))
    p_earth = int(cross_match.group(4))
    d_earth = int(cross_match.group(5))
    
    # Format gates with bullet separator
    gates_str = f"{p_sun}/{d_sun} • {p_earth}/{d_earth}"
    
    # Abbreviate cross type for label
    type_abbrev = {
        "Right Angle Cross": "RAX",
        "Left Angle Cross": "LAX",
        "Juxtaposition Cross": "JX"
    }
    abbrev = type_abbrev.get(cross_type, cross_type)
    
    # Look up cross name based on personality Sun gate
    # Note: Full cross names depend on the 4-gate combination
    # For simplicity, we use the personality Sun gate as the primary key
    # A full implementation would map all 768 combinations
    cross_name = get_cross_name(p_sun, d_sun, p_earth, d_earth, abbrev)
    
    if cross_name:
        label = f"{abbrev} {cross_name}"
    else:
        # Fallback to type + gates if no name found
        label = f"{abbrev} ({p_sun}/{d_sun})"
    
    return (label, gates_str)


def get_cross_name(p_sun: int, d_sun: int, p_earth: int, d_earth: int, cross_type: str) -> Optional[str]:
    """
    Get the traditional name for an incarnation cross based on its gates.
    
    The cross name is primarily determined by the personality Sun gate.
    Some crosses have numbered variants (1, 2, 3, 4) based on the quarter.
    
    This is a simplified mapping - full HD system has 768 named crosses.
    """
    # Partial cross name database keyed by personality Sun gate
    # Format: {p_sun: {d_sun: name}} or {p_sun: name} for single variants
    CROSS_NAMES = {
        # Gate 1: Self-Expression
        1: "Self-Expression",
        # Gate 2: The Driver
        2: "The Driver",
        # Gate 3: Mutation
        3: "Mutation",
        # Gate 4: Explanation
        4: {
            49: "Explanation",
            63: "Explanation 2"
        },
        # Gate 5: Universal Rhythms
        5: "Universal Rhythms",
        # Gate 6: Conflict (Intimacy)
        6: "Intimacy",
        # Gate 7: The Role of the Self
        7: "The Sphinx",
        # Gate 8: Contribution
        8: "Contribution",
        # Gate 9: Focus
        9: "Focus",
        # Gate 10: Behavior of the Self
        10: "Behavior",
        # Gate 11: Ideas
        11: "Ideas",
        # Gate 12: Caution
        12: "Caution",
        # Gate 13: The Listener
        13: "The Listener",
        # Gate 14: Power Skills
        14: "Power Skills",
        # Gate 15: Extremes
        15: "Extremes",
        # Gate 16: Skills (Experimentation)
        16: "Experimentation",
        # Gate 17: Opinions
        17: "Opinions",
        # Gate 18: Correction
        18: "Correction",
        # Gate 19: Wanting
        19: "Approach",
        # Gate 20: The Now
        20: "The Now",
        # Gate 21: Control
        21: "Control",
        # Gate 22: Openness
        22: "Grace",
        # Gate 23: Assimilation
        23: "Assimilation",
        # Gate 24: Rationalization
        24: "Rationalization",
        # Gate 25: Innocence
        25: "Healing",
        # Gate 26: The Trickster
        26: "Confrontation",
        # Gate 27: Caring
        27: "Caring",
        # Gate 28: The Game Player
        28: "Game Playing",
        # Gate 29: Saying Yes
        29: "Commitment",
        # Gate 30: Feelings (Recognition)
        30: "Fates",
        # Gate 31: Influence
        31: "Influence",
        # Gate 32: Duration
        32: "Duration",
        # Gate 33: Privacy
        33: "Privacy",
        # Gate 34: Power
        34: "Power",
        # Gate 35: Progress (Change)
        35: "Change",
        # Gate 36: Crisis
        36: "Crisis",
        # Gate 37: Friendship
        37: "Migration",
        # Gate 38: The Fighter
        38: "Struggle",
        # Gate 39: Provocation
        39: "Provocation",
        # Gate 40: Aloneness
        40: "Aloneness",
        # Gate 41: Decrease (Fantasy)
        41: "Fantasy",
        # Gate 42: Increase
        42: "Completion",
        # Gate 43: Insight
        43: "Insight",
        # Gate 44: Alertness
        44: "Alertness",
        # Gate 45: The King/Queen
        45: "Rulership",
        # Gate 46: Determination (Serendipity)
        46: "Discovery",
        # Gate 47: Realization
        47: "Realization",
        # Gate 48: Depth
        48: "Depth",
        # Gate 49: Principles (Revolution)
        49: "Principles",
        # Gate 50: Values
        50: "Values",
        # Gate 51: Shock
        51: "Shock",
        # Gate 52: Inaction
        52: "Stillness",
        # Gate 53: Beginnings
        53: "Beginnings",
        # Gate 54: Ambition
        54: "Ambition",
        # Gate 55: Spirit
        55: "Spirit",
        # Gate 56: Stimulation
        56: "Stimulation",
        # Gate 57: Intuition
        57: "Intuition",
        # Gate 58: Vitality (Joy)
        58: "Vitality",
        # Gate 59: Sexuality (Dispersion)
        59: "Dispersion",
        # Gate 60: Limitation
        60: "Limitation",
        # Gate 61: Mystery
        61: "Mystery",
        # Gate 62: Detail
        62: "Detail",
        # Gate 63: Doubt (After Completion)
        63: "Doubt",
        # Gate 64: Confusion (Before Completion)
        64: "Confusion",
    }
    
    name_entry = CROSS_NAMES.get(p_sun)
    
    if name_entry is None:
        return None
    
    if isinstance(name_entry, dict):
        # Has variants based on design Sun
        return name_entry.get(d_sun, list(name_entry.values())[0])
    
    return name_entry


def extract_human_design_data(chart: dict) -> dict:
    """Extract Human Design data from chart."""
    hd = chart.get('human_design', {})
    
    # Format channels consistently: sort by first gate, use en-dash
    channels = hd.get('defined_channels', [])
    formatted_channels = []
    for ch in channels:
        if isinstance(ch, dict):
            g1, g2 = ch.get('gate1', 0), ch.get('gate2', 0)
            # Ensure smaller gate comes first for consistency
            if g1 > g2:
                g1, g2 = g2, g1
            formatted_channels.append(f"{g1}–{g2}")
        elif isinstance(ch, str):
            # Already formatted string
            formatted_channels.append(ch.replace('-', '–'))
    
    # Sort channels by first gate number
    formatted_channels.sort(key=lambda x: int(x.split('–')[0]) if x.split('–')[0].isdigit() else 0)
    
    # Parse incarnation cross into label and gates
    raw_cross = hd.get('incarnation_cross', 'Unknown')
    cross_label, cross_gates = parse_incarnation_cross(raw_cross)
    
    return {
        "type": hd.get('type', 'Unknown'),
        "strategy": hd.get('strategy', 'Unknown'),
        "authority": hd.get('authority', 'Unknown'),
        "profile": hd.get('profile', 'Unknown'),
        "definition": hd.get('definition', 'Unknown'),
        # Keep original for backwards compatibility
        "incarnation_cross": raw_cross,
        # New split fields
        "incarnation_cross_label": cross_label,
        "incarnation_cross_gates": cross_gates,
        "channels": formatted_channels,
        "defined_centers": hd.get('defined_centers', []),
        "gates": hd.get('gates', [])
    }


# Strategy descriptions for context
HD_STRATEGY_DESCRIPTIONS = {
    "Generator": "Wait to respond - let life bring things to you, then notice your gut response",
    "Manifesting Generator": "Wait to respond, then inform before acting - your efficiency comes from responding, not initiating",
    "Projector": "Wait for recognition and invitation - your guidance lands when it's truly received",
    "Manifestor": "Inform before acting - this creates flow and reduces resistance",
    "Reflector": "Wait a lunar cycle for major decisions - your clarity comes from consistent patterns over time"
}

# Authority descriptions for context  
HD_AUTHORITY_DESCRIPTIONS = {
    "Sacral": "Listen for gut sounds and sensations - the immediate 'uh-huh' or 'unh-unh'",
    "Emotional": "Ride the emotional wave - clarity comes after the highs and lows settle",
    "Splenic": "Trust spontaneous intuitive hits - they come once and don't repeat",
    "Ego": "Ask 'Do I have the will/desire for this?' - commitment must feel real",
    "Self-Projected": "Talk it out - hear your own voice to find clarity",
    "Mental": "Discuss with trusted others - your clarity comes through processing externally",
    "Lunar": "Wait 28+ days - notice what remains consistent across the whole cycle",
    "None": "Environment matters - notice what feels right in different spaces"
}


@api_router.get("/human-design/summary/{user_id}")
async def get_human_design_summary(user_id: str):
    """
    Generate Human Design summary - high-level mechanics synthesis.
    NO gates, NO channels, NO mystical language.
    """
    import json as json_module
    
    try:
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        # Fetch user first to validate birth data
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # PRECONDITION CHECK: Validate birth data before computation
        is_valid, missing_fields = validate_birth_data(user)
        if not is_valid:
            return get_incomplete_birth_data_response(missing_fields)
        
        user, chart = await get_user_astrology_data(user_id)  # Reuse the same helper
        hd_data = extract_human_design_data(chart)
        
        if hd_data['type'] == 'Unknown':
            raise HTTPException(status_code=404, detail="Human Design data not found")
        
        # Build compact profile context
        strategy_desc = HD_STRATEGY_DESCRIPTIONS.get(hd_data['type'], 'Unique engagement pattern')
        authority_desc = HD_AUTHORITY_DESCRIPTIONS.get(hd_data['authority'], 'Unique clarity process')
        
        profile_context = f"""
Type: {hd_data['type']} - {strategy_desc}
Authority: {hd_data['authority']} - {authority_desc}
Profile: {hd_data['profile']}
"""
        
        # Build full prompt
        system_prompt = HUMAN_DESIGN_GLOBAL_PROMPT + "\n\n" + HUMAN_DESIGN_SUMMARY_PROMPT.format(
            profile_context=profile_context
        )
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"hd_summary_{user_id}_{datetime.now().strftime('%Y%m%d')}",
            system_message=system_prompt
        )
        chat.with_model("openai", "gpt-5.2")
        
        message = UserMessage(text="Generate the Human Design summary. Return ONLY valid JSON.")
        response_text = await chat.send_message(message)
        
        # Parse JSON response
        try:
            clean_response = response_text.strip()
            if clean_response.startswith("```"):
                lines = clean_response.split("\n")
                clean_response = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            
            result = json_module.loads(clean_response)
            
            # Apply guardrails
            for section in result.get("sections", []):
                section["body"] = apply_human_design_guardrails(section["body"])
            
            result["mirror_prompt"] = apply_human_design_guardrails(result.get("mirror_prompt", ""))
            
            return result
            
        except json_module.JSONDecodeError as e:
            logger.error(f"Failed to parse HD summary JSON: {e}")
            return {
                "title": "Your Human Design Profile",
                "sections": [
                    {"label": "Your Energy Pattern", "body": f"As a {hd_data['type']}, your energy tends to operate in a particular rhythm that may feel natural once you recognise it."},
                    {"label": "Engaging with Life", "body": f"Your design suggests a pattern of {strategy_desc.lower()}."},
                    {"label": "Decision Texture", "body": f"With {hd_data['authority']} authority, {authority_desc.lower()}."}
                ],
                "mirror_prompt": "What in this description matches how you already experience yourself?"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Human Design summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/human-design/today/{user_id}")
async def get_human_design_today(user_id: str):
    """
    Generate Today's Experiment - practical, low-stakes noticing prompt.
    ONE experiment, grounded in their mechanics.
    """
    import json as json_module
    
    try:
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        # Fetch user first to validate birth data
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # PRECONDITION CHECK: Validate birth data before computation
        is_valid, missing_fields = validate_birth_data(user)
        if not is_valid:
            return get_incomplete_birth_data_response(missing_fields)
        
        user, chart = await get_user_astrology_data(user_id)
        hd_data = extract_human_design_data(chart)
        
        if hd_data['type'] == 'Unknown':
            raise HTTPException(status_code=404, detail="Human Design data not found")
        
        today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Build mechanics context
        strategy_desc = HD_STRATEGY_DESCRIPTIONS.get(hd_data['type'], 'Unique engagement pattern')
        authority_desc = HD_AUTHORITY_DESCRIPTIONS.get(hd_data['authority'], 'Unique clarity process')
        
        mechanics_context = f"""
Type: {hd_data['type']}
Strategy: {strategy_desc}
Authority: {hd_data['authority']} - {authority_desc}
Profile: {hd_data['profile']}
"""
        
        # Build full prompt
        system_prompt = HUMAN_DESIGN_GLOBAL_PROMPT + "\n\n" + HUMAN_DESIGN_TODAY_PROMPT.format(
            today_date=today_date,
            mechanics_context=mechanics_context
        )
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"hd_today_{user_id}_{today_date}",
            system_message=system_prompt
        )
        chat.with_model("openai", "gpt-5.2")
        
        message = UserMessage(text="Generate Today's Experiment. Return ONLY valid JSON.")
        response_text = await chat.send_message(message)
        
        # Parse JSON response
        try:
            clean_response = response_text.strip()
            if clean_response.startswith("```"):
                lines = clean_response.split("\n")
                clean_response = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            
            result = json_module.loads(clean_response)
            
            # Apply guardrails
            for section in result.get("sections", []):
                section["body"] = apply_human_design_guardrails(section["body"])
            
            result["mirror_prompt"] = apply_human_design_guardrails(result.get("mirror_prompt", ""))
            result["date"] = today_date
            
            return result
            
        except json_module.JSONDecodeError as e:
            logger.error(f"Failed to parse HD today JSON: {e}")
            return {
                "title": "Today's Experiment",
                "date": today_date,
                "sections": [
                    {"label": "Today's Focus", "body": f"Notice when decisions feel easy versus forced."},
                    {"label": "A Small Experiment", "body": f"Before saying yes to something today, pause and notice what your body does."},
                    {"label": "What to Notice", "body": "Is there an immediate pull toward or away? Does clarity come right away or need time?"}
                ],
                "mirror_prompt": "What did you notice about how decisions felt today?"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Human Design today error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/human-design/deep-dive/{user_id}")
async def get_human_design_deep_dive(user_id: str):
    """
    Generate Deep Dive - Type, Strategy, Authority only.
    Mechanics, not mysticism. Experimentation, not prescription.
    """
    import json as json_module
    
    try:
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        # Fetch user first to validate birth data
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # PRECONDITION CHECK: Validate birth data before computation
        is_valid, missing_fields = validate_birth_data(user)
        if not is_valid:
            return get_incomplete_birth_data_response(missing_fields)
        
        user, chart = await get_user_astrology_data(user_id)
        hd_data = extract_human_design_data(chart)
        
        if hd_data['type'] == 'Unknown':
            raise HTTPException(status_code=404, detail="Human Design data not found")
        
        strategy_desc = HD_STRATEGY_DESCRIPTIONS.get(hd_data['type'], 'Unique engagement pattern')
        
        # Build full prompt
        system_prompt = HUMAN_DESIGN_GLOBAL_PROMPT + "\n\n" + HUMAN_DESIGN_DEEP_DIVE_PROMPT.format(
            hd_type=hd_data['type'],
            strategy=strategy_desc,
            authority=hd_data['authority'],
            profile=hd_data['profile']
        )
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"hd_deep_{user_id}_{datetime.now().strftime('%Y%m%d')}",
            system_message=system_prompt
        )
        chat.with_model("openai", "gpt-5.2")
        
        message = UserMessage(text="Generate the Deep Dive for this user's Human Design mechanics. Return ONLY valid JSON.")
        response_text = await chat.send_message(message)
        
        # Parse JSON response
        try:
            clean_response = response_text.strip()
            if clean_response.startswith("```"):
                lines = clean_response.split("\n")
                clean_response = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            
            result = json_module.loads(clean_response)
            
            # Apply guardrails
            for section in result.get("sections", []):
                section["body"] = apply_human_design_guardrails(section["body"])
            
            result["mirror_prompt"] = apply_human_design_guardrails(result.get("mirror_prompt", ""))
            
            # Ensure core_mechanics is included with all fields
            if "core_mechanics" not in result:
                result["core_mechanics"] = {
                    "type": hd_data['type'],
                    "strategy": strategy_desc,
                    "authority": hd_data['authority'],
                    "profile": hd_data['profile'],
                    "definition": hd_data['definition'],
                    "incarnation_cross": hd_data['incarnation_cross'],
                    "channels": hd_data['channels']
                }
            else:
                # Ensure all fields are present even if LLM returned partial
                result["core_mechanics"]["type"] = result["core_mechanics"].get("type") or hd_data['type']
                result["core_mechanics"]["strategy"] = result["core_mechanics"].get("strategy") or strategy_desc
                result["core_mechanics"]["authority"] = result["core_mechanics"].get("authority") or hd_data['authority']
                result["core_mechanics"]["profile"] = result["core_mechanics"].get("profile") or hd_data['profile']
                result["core_mechanics"]["definition"] = result["core_mechanics"].get("definition") or hd_data['definition']
                result["core_mechanics"]["incarnation_cross"] = result["core_mechanics"].get("incarnation_cross") or hd_data['incarnation_cross']
                result["core_mechanics"]["channels"] = result["core_mechanics"].get("channels") or hd_data['channels']
            
            # Add success flag
            result["success"] = True
            
            return result
            
        except json_module.JSONDecodeError as e:
            logger.error(f"Failed to parse HD deep dive JSON: {e}")
            return {
                "success": True,  # Data is valid, just LLM parsing failed
                "title": "Your Core Mechanics",
                "core_mechanics": {
                    "type": hd_data['type'],
                    "strategy": strategy_desc,
                    "authority": hd_data['authority'],
                    "profile": hd_data['profile'],
                    "definition": hd_data['definition'],
                    "incarnation_cross": hd_data['incarnation_cross'],
                    "channels": hd_data['channels']
                },
                "sections": [
                    {"label": "Type: Your Energy Architecture", "body": f"As a {hd_data['type']}, there's a particular way energy tends to move through you."},
                    {"label": "Strategy: Your Engagement Pattern", "body": f"Your design suggests {strategy_desc.lower()}."},
                    {"label": "Authority: Your Clarity Process", "body": f"With {hd_data['authority']} authority, clarity tends to come in a specific way."}
                ],
                "mirror_prompt": "What would be a small, low-stakes way to experiment with this today?"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Human Design deep dive error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# NUMEROLOGY LENS ENDPOINTS
# =====================================================================

async def get_user_numerology_data(user_id: str):
    """Helper to fetch user and chart numerology data."""
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    chart = await db.charts.find_one({"user_id": user_id})
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found. Please calculate chart first.")
    
    return user, chart


def extract_numerology_data(chart: dict, user: dict) -> dict:
    """Extract and structure numerology data from chart."""
    numerology = chart.get("numerology", {})
    
    # Helper to safely extract number
    def get_number(data, default=None):
        if data is None:
            return default
        if isinstance(data, int):
            return data
        if isinstance(data, dict):
            return data.get("number", default)
        return default
    
    # Helper to safely extract description
    def get_desc(data, default=""):
        if isinstance(data, dict):
            return data.get("description", default)
        return default
    
    # Always available
    life_path = numerology.get("life_path")
    birthday = numerology.get("birthday")
    
    # Name-based (optional)
    expression = numerology.get("expression")
    soul_urge = numerology.get("soul_urge")
    personality = numerology.get("personality")
    has_name_numbers = numerology.get("has_name_numbers", bool(expression or soul_urge or personality))
    
    return {
        "life_path_number": get_number(life_path, "Unknown"),
        "life_path_description": get_desc(life_path),
        "birthday_number": get_number(birthday),
        "birthday_description": get_desc(birthday),
        "expression_number": get_number(expression),
        "expression_description": get_desc(expression),
        "soul_urge_number": get_number(soul_urge),
        "soul_urge_description": get_desc(soul_urge),
        "personality_number": get_number(personality),
        "personality_description": get_desc(personality),
        "has_name_numbers": has_name_numbers,
        "user_birth_date": user.get("birth_date")
    }


@api_router.get("/numerology/summary/{user_id}")
async def get_numerology_summary(user_id: str):
    """
    Generate numerology summary - high-level profile synthesis.
    NO cycles, NO timing, NO dates.
    """
    import json as json_module
    
    try:
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        # Fetch user first to validate birth data (numerology needs birth_date)
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # PRECONDITION CHECK: For numerology, we only require birth_date
        if not user.get('birth_date'):
            return {
                "success": False,
                "error": "INCOMPLETE_BIRTH_DATA",
                "missing_fields": ["birth_date"],
                "message": "Birth date is required for numerology calculations.",
                "required_fields": ["birth_date"]
            }
        
        user, chart = await get_user_numerology_data(user_id)
        data = extract_numerology_data(chart, user)
        
        # Build name numbers context
        if data["has_name_numbers"]:
            name_numbers_context = f"""- expression_number: {data['expression_number']} ({data['expression_description']})
- soul_urge_number: {data['soul_urge_number']} ({data['soul_urge_description']})
- personality_number: {data['personality_number']} ({data['personality_description']})"""
        else:
            name_numbers_context = "- Name-based numbers: NOT PROVIDED (Expression, Soul Urge, Personality unavailable)"
        
        # Build full prompt
        system_prompt = NUMEROLOGY_GLOBAL_PROMPT + "\n\n" + NUMEROLOGY_SUMMARY_PROMPT.format(
            life_path_number=data["life_path_number"],
            birthday_number=data["birthday_number"] or "Not available",
            name_numbers_context=name_numbers_context
        )
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"numerology_summary_{user_id}_{datetime.now().strftime('%Y%m%d')}",
            system_message=system_prompt
        )
        chat.with_model("openai", "gpt-5.2")
        
        message = UserMessage(text="Generate the numerology summary for this user. Return ONLY valid JSON.")
        response_text = await chat.send_message(message)
        
        # Parse JSON response
        try:
            clean_response = response_text.strip()
            if clean_response.startswith("```"):
                lines = clean_response.split("\n")
                clean_response = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            
            result = json_module.loads(clean_response)
            
            # Apply guardrails
            for section in result.get("sections", []):
                section["body"] = apply_numerology_guardrails(section["body"])
            
            result["mirror_prompt"] = apply_numerology_guardrails(result.get("mirror_prompt", ""))
            
            # Add unlock prompt if needed
            if not data["has_name_numbers"]:
                result["unlock_prompt"] = "Add your full birth name to unlock deeper numerology (Expression, Soul Urge, Personality)."
            else:
                result["unlock_prompt"] = None
            
            return result
            
        except json_module.JSONDecodeError as e:
            logger.error(f"Failed to parse numerology summary JSON: {e}")
            return {
                "title": "Your Numerology Profile",
                "sections": [
                    {"label": "How Numerology Works (Here)", "body": "Numerology in Project Mirror is used as a lens for noticing patterns, not predicting outcomes. Numbers describe symbolic themes and rhythms — recurring emphases that may feel familiar, not fixed truths about who you are."},
                    {"label": "Your Numerology Snapshot", "body": f"Your Life Path {data['life_path_number']} often correlates with a particular kind of learning journey — themes that tend to recur over time as opportunities for growth and awareness."}
                ],
                "unlock_prompt": None if data["has_name_numbers"] else "Add your full birth name to unlock deeper numerology (Expression, Soul Urge, Personality).",
                "mirror_prompt": "What recurring themes do you notice in your own life?"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Numerology summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/numerology/today/{user_id}")
async def get_numerology_today(user_id: str):
    """
    Generate Today's Snapshot using numerology cycles.
    Focus on Personal Day, with Month/Year as background.
    """
    import json as json_module
    
    try:
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        # Fetch user first to validate birth data (numerology needs birth_date)
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # PRECONDITION CHECK: For numerology, we only require birth_date
        if not user.get('birth_date'):
            return {
                "success": False,
                "error": "INCOMPLETE_BIRTH_DATA",
                "missing_fields": ["birth_date"],
                "message": "Birth date is required for numerology calculations.",
                "required_fields": ["birth_date"]
            }
        
        user, chart = await get_user_numerology_data(user_id)
        data = extract_numerology_data(chart, user)
        
        # Calculate current cycles
        birth_date = user.get("birth_date")
        if not birth_date:
            raise HTTPException(status_code=400, detail="Birth date not found")
        
        today = datetime.now()
        cycles = get_numerology_cycles(birth_date, today)
        
        today_date = today.strftime("%Y-%m-%d")
        
        # Build full prompt
        system_prompt = NUMEROLOGY_GLOBAL_PROMPT + "\n\n" + NUMEROLOGY_TODAY_PROMPT.format(
            personal_day_number=cycles["personal_day"]["number"],
            personal_month_number=cycles["personal_month"]["number"],
            personal_year_number=cycles["personal_year"]["number"],
            life_path_number=data["life_path_number"],
            today_date=today_date
        )
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"numerology_today_{user_id}_{today_date}",
            system_message=system_prompt
        )
        chat.with_model("openai", "gpt-5.2")
        
        message = UserMessage(text="Generate Today's Snapshot for this user. Return ONLY valid JSON.")
        response_text = await chat.send_message(message)
        
        # Parse JSON response
        try:
            clean_response = response_text.strip()
            if clean_response.startswith("```"):
                lines = clean_response.split("\n")
                clean_response = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            
            result = json_module.loads(clean_response)
            
            # Apply guardrails
            for section in result.get("sections", []):
                section["body"] = apply_numerology_guardrails(section["body"])
            
            result["mirror_prompt"] = apply_numerology_guardrails(result.get("mirror_prompt", ""))
            
            # Ensure cycles are in response
            result["cycles"] = {
                "personal_day": cycles["personal_day"]["number"],
                "personal_month": cycles["personal_month"]["number"],
                "personal_year": cycles["personal_year"]["number"]
            }
            result["date"] = today_date
            
            return result
            
        except json_module.JSONDecodeError as e:
            logger.error(f"Failed to parse numerology today JSON: {e}")
            return {
                "title": "Today's Snapshot",
                "date": today_date,
                "cycles": {
                    "personal_day": cycles["personal_day"]["number"],
                    "personal_month": cycles["personal_month"]["number"],
                    "personal_year": cycles["personal_year"]["number"]
                },
                "sections": [
                    {"label": "Today", "body": f"Personal Day {cycles['personal_day']['number']} often brings a particular quality of attention. Notice what themes feel present."},
                    {"label": "Background tone", "body": f"This sits within a Personal Year {cycles['personal_year']['number']} and Month {cycles['personal_month']['number']}."},
                    {"label": "2-minute experiment", "body": "At some point today, pause and notice what you're drawn toward. No action needed—just noticing."}
                ],
                "mirror_prompt": "What feels most present for you today?"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Numerology today error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/numerology/deep-dive/{user_id}")
async def get_numerology_deep_dive(user_id: str):
    """
    Generate Numerology Deep Dive - expanded exploration of core numbers.
    NO cycles/timing. Focus on Life Path, Birthday, and name-based numbers if available.
    """
    import json as json_module
    
    try:
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        # Fetch user first to validate birth data (numerology needs birth_date)
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # PRECONDITION CHECK: For numerology, we only require birth_date
        if not user.get('birth_date'):
            return {
                "success": False,
                "error": "INCOMPLETE_BIRTH_DATA",
                "missing_fields": ["birth_date"],
                "message": "Birth date is required for numerology calculations.",
                "required_fields": ["birth_date"]
            }
        
        user, chart = await get_user_numerology_data(user_id)
        data = extract_numerology_data(chart, user)
        
        # Build name numbers context
        if data["has_name_numbers"]:
            name_numbers_context = f"""- expression_number: {data['expression_number']} ({data['expression_description']})
- soul_urge_number: {data['soul_urge_number']} ({data['soul_urge_description']})
- personality_number: {data['personality_number']} ({data['personality_description']})"""
            expression_for_prompt = data['expression_number']
            soul_urge_for_prompt = data['soul_urge_number']
        else:
            name_numbers_context = "- Name-based numbers: NOT PROVIDED (Expression, Soul Urge, Personality unavailable)"
            expression_for_prompt = '"locked"'
            soul_urge_for_prompt = '"locked"'
        
        # Build full prompt
        system_prompt = NUMEROLOGY_GLOBAL_PROMPT + "\n\n" + NUMEROLOGY_DEEP_DIVE_PROMPT.format(
            life_path_number=data["life_path_number"],
            birthday_number=data["birthday_number"] or "Not available",
            expression_number=expression_for_prompt,
            soul_urge_number=soul_urge_for_prompt,
            name_numbers_context=name_numbers_context
        )
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"numerology_deepdive_{user_id}_{datetime.now().strftime('%Y%m%d')}",
            system_message=system_prompt
        )
        chat.with_model("openai", "gpt-5.2")
        
        message = UserMessage(text="Generate the Numerology Deep Dive for this user. Return ONLY valid JSON.")
        response_text = await chat.send_message(message)
        
        # Parse JSON response
        try:
            clean_response = response_text.strip()
            if clean_response.startswith("```"):
                lines = clean_response.split("\n")
                clean_response = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            
            result = json_module.loads(clean_response)
            
            # Apply guardrails
            for section in result.get("sections", []):
                section["body"] = apply_numerology_guardrails(section["body"])
            
            result["mirror_prompt"] = apply_numerology_guardrails(result.get("mirror_prompt", ""))
            
            # Ensure core numbers are present
            result["core_numbers"] = {
                "life_path": data["life_path_number"],
                "expression": data["expression_number"] if data["has_name_numbers"] else "locked",
                "soul_urge": data["soul_urge_number"] if data["has_name_numbers"] else "locked"
            }
            
            # Add unlock prompt if needed
            if not data["has_name_numbers"]:
                result["unlock_prompt"] = "Add your full birth name to unlock deeper numerology (Expression, Soul Urge, Personality)."
            else:
                result["unlock_prompt"] = None
            
            return result
            
        except json_module.JSONDecodeError as e:
            logger.error(f"Failed to parse numerology deep dive JSON: {e}")
            return {
                "title": "Your Core Numbers",
                "core_numbers": {
                    "life_path": data["life_path_number"],
                    "expression": data["expression_number"] if data["has_name_numbers"] else "locked",
                    "soul_urge": data["soul_urge_number"] if data["has_name_numbers"] else "locked"
                },
                "sections": [
                    {"label": "Life Path: Your Learning Theme", "body": f"Life Path {data['life_path_number']} often describes a recurring theme of learning and growth. This isn't about who you are, but about what tends to show up as territory for exploration."},
                    {"label": "Birthday: Your Secondary Flavour", "body": f"Birthday number {data['birthday_number'] or 'unknown'} adds a secondary emphasis — a flavour that colours how you approach things."}
                ],
                "unlock_prompt": None if data["has_name_numbers"] else "Add your full birth name to unlock deeper numerology (Expression, Soul Urge, Personality).",
                "mirror_prompt": "What recurring themes do you notice in your own journey?"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Numerology deep dive error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# NUMEROLOGY NAME UNLOCK ENDPOINT
# =====================================================================

class NumerologyUnlockRequest(BaseModel):
    full_birth_name: str


@api_router.post("/numerology/unlock-name/{user_id}")
async def unlock_numerology_name(user_id: str, request: NumerologyUnlockRequest):
    """
    Optional endpoint to unlock name-based numerology numbers.
    Calculates Expression, Soul Urge, and Personality from the full birth name.
    
    This is consent-based and entirely optional.
    """
    from calculations.numerology import (
        calculate_expression_number,
        calculate_soul_urge,
        calculate_personality_number
    )
    
    try:
        # Validate user exists
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        chart = await db.charts.find_one({"user_id": user_id})
        if not chart:
            raise HTTPException(status_code=404, detail="Chart not found")
        
        full_name = request.full_birth_name.strip()
        if not full_name or len(full_name) < 2:
            raise HTTPException(status_code=400, detail="Please provide a valid name")
        
        # Calculate name-based numbers
        expression = calculate_expression_number(full_name)
        soul_urge = calculate_soul_urge(full_name)
        personality = calculate_personality_number(full_name)
        
        # Update chart with new numerology data
        numerology_update = {
            "numerology.expression": expression,
            "numerology.soul_urge": soul_urge,
            "numerology.personality": personality,
            "numerology.has_name_numbers": True,
            "numerology.name_unlocked_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.charts.update_one(
            {"user_id": user_id},
            {"$set": numerology_update}
        )
        
        logger.info(f"[Numerology] Name-based numbers unlocked for user {user_id}")
        
        # Return the new numbers (without echoing the name back)
        return {
            "success": True,
            "message": "Deeper numerology has been unlocked.",
            "unlocked_numbers": {
                "expression": {
                    "number": expression["number"],
                    "description": expression["description"]
                },
                "soul_urge": {
                    "number": soul_urge["number"],
                    "description": soul_urge["description"]
                },
                "personality": {
                    "number": personality["number"],
                    "description": personality["description"]
                }
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Numerology unlock error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Include the router in the main app (MUST BE AFTER ALL @api_router decorators)
app.include_router(api_router)


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown():
    """Clean up resources"""
    client.close()
    close_ephemeris()
