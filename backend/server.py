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
    birth_date: datetime
    birth_time: Optional[str] = None  # HH:MM format
    birth_location: Location
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserProfileCreate(BaseModel):
    name: Optional[str] = None
    birth_date: str  # YYYY-MM-DD
    birth_time: Optional[str] = None  # HH:MM
    city: str
    country: str
    timezone: str  # "+07:30" or "Asia/Kuala_Lumpur"


class UserProfileResponse(BaseModel):
    id: str
    name: Optional[str]
    birth_date: str
    birth_time: Optional[str]
    birth_location: Location
    has_chart: bool = False


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
    try:
        geolocator = Nominatim(user_agent="project_mirror", timeout=10)
        locations = geolocator.geocode(request.query, exactly_one=False, limit=5, addressdetails=True)
        
        if not locations:
            return {"results": []}
        
        results = []
        for loc in locations:
            address = loc.raw.get('address', {})
            
            # Try multiple fields for city name
            city = (
                address.get('city') or 
                address.get('town') or 
                address.get('village') or 
                address.get('county') or
                address.get('state') or
                address.get('municipality') or
                loc.address.split(',')[0].strip()
            )
            
            country = address.get('country', 'Unknown')
            
            results.append({
                "city": city,
                "country": country,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "display_name": loc.address
            })
        
        return {"results": results}
    except Exception as e:
        logger.error(f"Location search error: {e}")
        # Return empty results instead of error to allow retry
        return {"results": []}


@api_router.post("/users", response_model=UserProfileResponse)
async def create_user(profile: UserProfileCreate):
    """Create user profile"""
    try:
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
            birth_date=user["birth_date"].strftime("%Y-%m-%d"),
            birth_time=user.get("birth_time"),
            birth_location=Location(**user["birth_location"]),
            has_chart=chart is not None
        )
    except Exception as e:
        logger.error(f"Get user error: {e}")
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
        
        # Prepare datetime
        birth_date = user["birth_date"]
        birth_time = user.get("birth_time", "12:00")
        
        # Store original inputs for debug stamp
        input_birth_local = birth_date.strftime("%Y-%m-%d")
        input_timezone_raw = "UTC"  # V1: assuming UTC, should be enhanced with timezone
        
        # Parse and validate birth time
        try:
            if birth_time:
                # Clean the time string
                birth_time = birth_time.strip()
                # Validate format
                if ':' not in birth_time:
                    birth_time = "12:00"
                else:
                    parts = birth_time.split(":")
                    if len(parts) != 2:
                        birth_time = "12:00"
                    else:
                        # Validate hour and minute are integers
                        hour = int(parts[0])
                        minute = int(parts[1])
                        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                            birth_time = "12:00"
                            hour, minute = 12, 0
            else:
                birth_time = "12:00"
                hour, minute = 12, 0
            
            if birth_time != "12:00" or 'hour' not in locals():
                hour, minute = map(int, birth_time.split(":"))
            
            birth_datetime = birth_date.replace(hour=hour, minute=minute)
        except (ValueError, AttributeError) as e:
            logger.warning(f"Invalid birth time format: {birth_time}, using noon as default. Error: {e}")
            birth_datetime = birth_date.replace(hour=12, minute=0)
        
        location = user["birth_location"]
        lat = location["latitude"]
        lon = location["longitude"]
        
        # Prepare debug stamp data
        resolved_birth_utc_iso = birth_datetime.isoformat()
        parsed_timezone_minutes = 0  # V1: assuming UTC
        lat_used = lat
        lon_used = lon
        
        # Sidereal settings (from astrology.py)
        sidereal_settings_used = {
            "ayanamsa_key": "SIDM_LAHIRI",
            "svp_degrees": None,  # Not using SVP
            "reference_year": None,  # Lahiri handles this internally
            "yearly_increment": None
        }
        
        house_system_used = "Placidus"  # Default from astrology.py
        
        # Calculate input hash for debugging
        input_string = f"{resolved_birth_utc_iso}|{lat_used}|{lon_used}|{sidereal_settings_used}|{house_system_used}"
        input_hash = hashlib.sha256(input_string.encode()).hexdigest()
        
        # Create debug stamp
        debug_stamp = {
            "request_id": request_id,
            "profile_id": request.user_id,
            "user_id": request.user_id,
            "input_birth_local": input_birth_local,
            "input_birth_time": birth_time,
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
        
        # Calculate all frameworks
        logger.info(f"Calculating astrology chart for user {request.user_id}")
        astrology_chart = get_full_natal_chart(birth_datetime, lat, lon)
        
        logger.info(f"Calculating human design for user {request.user_id}")
        human_design = get_human_design_chart(birth_datetime, lat, lon)
        
        logger.info(f"Calculating numerology for user {request.user_id}")
        numerology = get_full_numerology(birth_date, user.get("name"))
        
        logger.info(f"Getting consciousness framework for user {request.user_id}")
        consciousness = get_consciousness_framework()
        
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
        
        # Return formatted chart data for Lenses
        return {
            "human_design": {
                "type": chart.get("human_design", {}).get("type"),
                "authority": chart.get("human_design", {}).get("authority"),
                "profile": chart.get("human_design", {}).get("profile"),
                "incarnation_cross": chart.get("human_design", {}).get("incarnation_cross"),
                "strategy": chart.get("human_design", {}).get("strategy"),
                "personality_sun": chart.get("human_design", {}).get("personality", {}).get("Sun"),
                "design_sun": chart.get("human_design", {}).get("design", {}).get("Sun"),
                "note": "V1 calculations use simplified gate-to-center mapping. Full channel analysis coming in future updates."
            },
            "astrology": {
                "sun": chart.get("astrology", {}).get("planets", {}).get("Sun"),
                "moon": chart.get("astrology", {}).get("planets", {}).get("Moon"),
                "rising": chart.get("astrology", {}).get("houses", {}).get("ascendant"),
                "note": "True Sidereal (Lahiri Ayanamsa) positions"
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
async def shutdown():
    """Clean up resources"""
    client.close()
    close_ephemeris()
