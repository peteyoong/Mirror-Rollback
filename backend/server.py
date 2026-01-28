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
    date_key: str  # YYYY-MM-DD format
    todays_insight: str
    reflect_on: str
    another_perspective: str
    closing_line: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DailyReflectionResponse(BaseModel):
    id: str
    user_id: str
    date_key: str
    todays_insight: str
    reflect_on: str
    another_perspective: str
    closing_line: str
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

LENSES_CONTENT = [
    {
        "id": "inner-observer",
        "title": "The Inner Observer",
        "icon": "eye",
        "summary": "The part of you that watches without judgment. This lens invites you to step back and notice your thoughts and feelings as they pass, like clouds moving across the sky.",
        "deep_dive": {
            "description": "The Inner Observer is a perspective rooted in mindfulness traditions. It represents metacognition—the ability to think about your own thinking. When you engage this lens, you're practicing witness consciousness, observing your mental and emotional landscape without attachment.",
            "practices": [
                "Notice when you're lost in thought versus aware of thinking",
                "Label emotions without becoming them",
                "Watch reactions before responding"
            ],
            "invitation": "What would you notice if you watched yourself for a day?"
        }
    },
    {
        "id": "body-wisdom",
        "title": "Body Wisdom",
        "icon": "body",
        "summary": "Your body holds knowledge that words sometimes can't capture. This lens helps you tune into physical sensations as a source of insight and guidance.",
        "deep_dive": {
            "description": "Body Wisdom draws from somatic awareness practices. The body often registers truth before the mind catches up—a gut feeling, a tension in the shoulders, an expansion in the chest. This lens honors the intelligence of embodied experience.",
            "practices": [
                "Scan your body before making decisions",
                "Notice where emotions live physically",
                "Trust the signals your body sends"
            ],
            "invitation": "What is your body telling you right now?"
        }
    },
    {
        "id": "compassionate-witness",
        "title": "The Compassionate Witness",
        "icon": "heart",
        "summary": "A gentle presence that sees your struggles and successes with equal kindness. This lens softens self-criticism and nurtures self-acceptance.",
        "deep_dive": {
            "description": "The Compassionate Witness combines elements of self-compassion research with contemplative practices. It's the voice that says 'this is hard' without adding 'and you're failing.' This lens helps rewire patterns of harsh self-judgment.",
            "practices": [
                "Speak to yourself as you would a dear friend",
                "Acknowledge difficulty without dramatizing it",
                "Celebrate small steps alongside big ones"
            ],
            "invitation": "How would you comfort yourself if you were someone you loved?"
        }
    },
    {
        "id": "curious-explorer",
        "title": "The Curious Explorer",
        "icon": "search",
        "summary": "Approaching life with wonder instead of worry. This lens transforms problems into puzzles and fears into fascinations.",
        "deep_dive": {
            "description": "The Curious Explorer embodies beginner's mind—approaching experiences as if for the first time. Curiosity deactivates the threat response and opens neural pathways for creative thinking. This lens replaces 'why is this happening to me' with 'what is this teaching me.'",
            "practices": [
                "Ask 'what if' instead of 'what's wrong'",
                "Treat setbacks as experiments",
                "Stay open to being surprised"
            ],
            "invitation": "What would you explore if you weren't afraid of looking foolish?"
        }
    },
    {
        "id": "present-moment",
        "title": "Present Moment Awareness",
        "icon": "time",
        "summary": "The only moment that truly exists is now. This lens anchors you in the present, releasing the grip of past regrets and future anxieties.",
        "deep_dive": {
            "description": "Present Moment Awareness is central to mindfulness and contemplative traditions worldwide. It recognizes that suffering often comes from mental time travel—reliving the past or rehearsing the future. This lens practices arrival, coming home to now.",
            "practices": [
                "Notice five things you can sense right now",
                "Catch yourself when you drift to past or future",
                "Find one thing to appreciate in this moment"
            ],
            "invitation": "What is available to you right now that you might be missing?"
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
    
    Personalizes based on:
    - desired_depth: 'deep' vs 'surface' content length/complexity
    - uncertainty_relationship: adds grounding language if challenging
    - reflection_style: adds pattern or somatic language
    - intention: adds clarity-focused language if seeking clarity
    
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

def generate_random_reflection(onboarding_answers: dict = None) -> dict:
    """Generate a reflection, personalized if onboarding answers available"""
    return generate_personalized_reflection(onboarding_answers)

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
    date_key: str  # YYYY-MM-DD format from client's local time

@api_router.post("/reflection/today", response_model=DailyReflectionResponse)
async def get_or_create_daily_reflection(date_input: DateKeyInput, user = Depends(get_current_user)):
    """Get today's reflection or create one if it doesn't exist"""
    date_key = date_input.date_key
    user_id = user["id"]
    
    # Check if reflection exists for today
    existing = await db.daily_reflections.find_one({
        "user_id": user_id,
        "date_key": date_key
    })
    
    if existing:
        return DailyReflectionResponse(**existing)
    
    # Generate new reflection
    reflection_content = generate_random_reflection()
    
    reflection = DailyReflection(
        user_id=user_id,
        date_key=date_key,
        **reflection_content
    )
    
    await db.daily_reflections.insert_one(reflection.dict())
    return DailyReflectionResponse(**reflection.dict())

@api_router.post("/reflection/regenerate", response_model=DailyReflectionResponse)
async def regenerate_daily_reflection(date_input: DateKeyInput, user = Depends(get_current_user)):
    """Regenerate today's reflection (overwrites existing)"""
    date_key = date_input.date_key
    user_id = user["id"]
    
    # Generate new reflection content
    reflection_content = generate_random_reflection()
    
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
        "summary": lens["summary"]
    } for lens in LENSES_CONTENT]

@api_router.get("/lenses/{lens_id}")
async def get_lens_detail(lens_id: str, user = Depends(get_current_user)):
    lens = next((l for l in LENSES_CONTENT if l["id"] == lens_id), None)
    if not lens:
        raise HTTPException(status_code=404, detail="Lens not found")
    return lens

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
