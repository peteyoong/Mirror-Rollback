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
from calculations.numerology import get_full_numerology
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


class MirrorChatRequest(BaseModel):
    user_id: str
    message: str
    lens: Optional[str] = None  # None = generalist, "astrology", "human_design", "numerology"
    session_id: Optional[str] = None  # For conversation continuity
    include_journal: bool = True  # Include recent journal entries
    include_history: bool = True  # Include chat history


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
You are currently in NUMEROLOGY lens mode. Focus primarily on:
- Life Path number and its themes
- Expression number
- Soul Urge number
- Current cycles and personal year

Stay grounded in numerology unless the user explicitly asks to switch lenses.
Do not explain numerological calculations unless asked - focus on the meaning and resonance.
"""
}


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
        
        # Get recent journal entries
        journal_entries = await db.journal.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(5).to_list(5)
        
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
        input_birth_time = birth_time if birth_time else None
        input_timezone_raw = user_timezone if user_timezone else None
        
        # STRICT TIMEZONE VALIDATION - No silent defaults
        if not user_timezone:
            raise HTTPException(
                status_code=400, 
                detail="Timezone is required. Please update user profile with timezone (e.g., '+07:30')."
            )
        
        if not birth_time:
            raise HTTPException(
                status_code=400,
                detail="Birth time is required. Please update user profile with birth time (e.g., '07:25')."
            )
        
        # Resolve birth datetime to UTC using proper timezone handling
        try:
            birth_datetime_utc, resolved_birth_utc_iso, parsed_timezone_minutes, _ = resolve_birth_utc(
                birth_date_str=input_birth_local,
                birth_time_str=birth_time,
                timezone_str=user_timezone
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
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
        
        # Create debug stamp
        debug_stamp = {
            "request_id": request_id,
            "profile_id": request.user_id,
            "user_id": request.user_id,
            "input_birth_local": input_birth_local,
            "input_birth_time": input_birth_time,
            "input_timezone_raw": input_timezone_raw,
            "parsed_timezone_minutes": parsed_timezone_minutes,
            "resolved_birth_utc_iso": resolved_birth_utc_iso,
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
                context_parts.append("\n--- NUMEROLOGY ---")
                context_parts.append(f"Life Path: {numerology.get('life_path', 'Unknown')}")
                context_parts.append(f"Expression: {numerology.get('expression', 'Unknown')}")
                context_parts.append(f"Soul Urge: {numerology.get('soul_urge', 'Unknown')}")
        
        # Get recent journal entries for context
        if request.include_journal:
            journal_entries = await db.journal.find(
                {"user_id": request.user_id}
            ).sort("timestamp", -1).limit(5).to_list(5)
            
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
        
        # Add context
        system_prompt += "\n\n--- USER CONTEXT ---\n" + "\n".join(context_parts)
        
        # Get or create chat history for session
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
        
        history = chat_sessions[session_id]
        
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
        
        # ===== GUARDRAIL ENFORCEMENT =====
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
        
        # Limit history size
        if len(history) > 50:
            chat_sessions[session_id] = history[-50:]
        
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
            
            # Add journal entries if available
            if request.include_journal:
                journal_entries = await db.journal.find(
                    {"user_id": request.user_id}
                ).sort("timestamp", -1).limit(10).to_list(10)
                
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
                    "event_type": "mirror_chat_turn",
                    "inferred_state": memory_update.inferred_state,
                    "confidence": memory_update.confidence,
                    "themes": memory_update.themes[:2],  # max 2 themes
                    "tension": memory_update.recurring_tensions[0] if memory_update.recurring_tensions else None,
                    "source": "mirror_chat",
                    "version": "v1"
                }
                
                await db.user_timeline.insert_one(timeline_event)
                logger.info(f"Timeline event recorded for user {request.user_id}: state={memory_update.inferred_state}")
                
            except Exception as timeline_error:
                logger.warning(f"Timeline event write failed: {timeline_error}")
                # Continue without timeline - don't fail the request
            
        except Exception as mem_error:
            logger.warning(f"Memory update generation failed: {mem_error}")
            # Continue without memory update - don't fail the whole request
        
        return MirrorChatResponse(
            response=response_text,
            session_id=session_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            memory_update=memory_update
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
