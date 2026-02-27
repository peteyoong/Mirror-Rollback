"""
Enneagram Assessment V4 - Ground-up Rebuild
============================================
108-question assessment (12 per type) with weighted scoring,
consistency checks, and gaming detection.

Version: 4.1.0
Author: Project Mirror Team
"""

import logging
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import expanded question bank
from enneagram_v4_questions import QUESTION_BANK

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================

# Scoring weights - REFINED based on testing
SCORING_WEIGHTS = {
    "primary": 1.0,       # 100% for primary type match
    "wing": 0.25,         # 25% for adjacent wing types (bumped from 20%)
    "stress_growth": 0.10, # 10% for stress/growth lines
    "same_triad": 0.05,   # 5% for same triad types
}

# Enneagram type relationships
TYPE_WINGS = {
    1: [9, 2], 2: [1, 3], 3: [2, 4], 4: [3, 5], 5: [4, 6],
    6: [5, 7], 7: [6, 8], 8: [7, 9], 9: [8, 1]
}

TYPE_STRESS_GROWTH = {
    1: {"stress": 4, "growth": 7},
    2: {"stress": 8, "growth": 4},
    3: {"stress": 9, "growth": 6},
    4: {"stress": 2, "growth": 1},
    5: {"stress": 7, "growth": 8},
    6: {"stress": 3, "growth": 9},
    7: {"stress": 1, "growth": 5},
    8: {"stress": 5, "growth": 2},
    9: {"stress": 6, "growth": 3},
}

TYPE_TRIADS = {
    "body": [8, 9, 1],    # Gut/Instinctive triad
    "heart": [2, 3, 4],   # Feeling triad
    "head": [5, 6, 7],    # Thinking triad
}

TRIAD_FOR_TYPE = {
    8: "body", 9: "body", 1: "body",
    2: "heart", 3: "heart", 4: "heart",
    5: "head", 6: "head", 7: "head",
}

# Gaming detection thresholds
MIN_RESPONSE_TIME_MS = 2000   # Minimum 2 seconds per question
MAX_RESPONSE_TIME_MS = 60000  # Maximum 60 seconds per question
CONTRADICTION_THRESHOLD = 2   # Max difference for reverse-coded pairs

# Session configuration
SESSION_TTL_HOURS = 24
QUESTIONS_PER_BATCH = 12

# =============================================================================
# TYPE DESCRIPTIONS
# =============================================================================

TYPE_DESCRIPTIONS = {
    1: {
        "name": "The Reformer",
        "core_desire": "To be good, right, and ethical",
        "core_fear": "Being corrupt, evil, or defective",
        "brief": "Principled, purposeful, self-controlled, and perfectionistic"
    },
    2: {
        "name": "The Helper",
        "core_desire": "To be loved and needed",
        "core_fear": "Being unwanted or unworthy of love",
        "brief": "Generous, demonstrative, people-pleasing, and possessive"
    },
    3: {
        "name": "The Achiever",
        "core_desire": "To be valuable and worthwhile",
        "core_fear": "Being worthless or without value",
        "brief": "Adaptable, excelling, driven, and image-conscious"
    },
    4: {
        "name": "The Individualist",
        "core_desire": "To find their identity and significance",
        "core_fear": "Having no identity or personal significance",
        "brief": "Expressive, dramatic, self-absorbed, and temperamental"
    },
    5: {
        "name": "The Investigator",
        "core_desire": "To be capable and competent",
        "core_fear": "Being useless, incompetent, or overwhelmed",
        "brief": "Perceptive, innovative, secretive, and isolated"
    },
    6: {
        "name": "The Loyalist",
        "core_desire": "To have security and support",
        "core_fear": "Being without support or guidance",
        "brief": "Engaging, responsible, anxious, and suspicious"
    },
    7: {
        "name": "The Enthusiast",
        "core_desire": "To be satisfied and content",
        "core_fear": "Being deprived or trapped in pain",
        "brief": "Spontaneous, versatile, acquisitive, and scattered"
    },
    8: {
        "name": "The Challenger",
        "core_desire": "To protect themselves and control their destiny",
        "core_fear": "Being harmed or controlled by others",
        "brief": "Self-confident, decisive, willful, and confrontational"
    },
    9: {
        "name": "The Peacemaker",
        "core_desire": "To have inner stability and peace of mind",
        "core_fear": "Loss, separation, and fragmentation",
        "brief": "Receptive, reassuring, complacent, and resigned"
    },
}

# =============================================================================
# QUESTION BANK - Imported from enneagram_v4_questions.py
# Total: 132 questions (108 core + 24 validation)
# =============================================================================

# QUESTION_BANK is imported at the top of this file

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class QuestionResponse:
    question_id: str
    answer_value: int
    response_time_ms: int
    timestamp: str

@dataclass
class ConsistencyCheck:
    pair_id: str
    question_1: str
    question_2: str
    answer_1: int
    answer_2: int
    difference: int
    is_consistent: bool

@dataclass
class GamingIndicators:
    avg_response_time_ms: float
    fast_responses_count: int  # < 2 seconds
    slow_responses_count: int  # > 60 seconds
    variance_score: float
    all_same_value: bool
    randomness_score: float
    consistency_failures: int
    is_suspicious: bool
    flags: List[str]

@dataclass
class TypeScore:
    type_number: int
    raw_score: float
    normalized_percentage: float
    question_count: int

@dataclass
class AssessmentResult:
    primary_type: int
    primary_percentage: float
    secondary_type: int
    secondary_percentage: float
    suggested_wing: int
    all_scores: List[TypeScore]
    confidence_level: str  # "high", "medium", "low"
    confidence_score: int  # 0-100 numeric confidence
    is_unclear: bool  # True if top 2 within 10%
    gaming_indicators: GamingIndicators
    consistency_checks: List[ConsistencyCheck]

# =============================================================================
# SCORING ENGINE
# =============================================================================

class ScoringEngine:
    """Calculates type scores with weighted relationships and consistency checks."""
    
    def __init__(self):
        self.question_map = {q["id"]: q for q in QUESTION_BANK}
    
    def calculate_scores(self, responses: List[QuestionResponse]) -> Dict[int, float]:
        """Calculate raw scores for all 9 types based on responses."""
        scores = {t: 0.0 for t in range(1, 10)}
        question_counts = {t: 0 for t in range(1, 10)}
        
        for response in responses:
            question = self.question_map.get(response.question_id)
            if not question:
                continue
            
            primary_type = question["primary_type"]
            secondary_type = question.get("secondary_influence")
            answer = response.answer_value
            difficulty = question.get("difficulty_weight", 1.0)
            is_reverse = question.get("reverse_coded", False)
            
            # For reverse-coded questions, invert the score
            if is_reverse:
                answer = 6 - answer  # Converts 1->5, 2->4, 3->3, 4->2, 5->1
            
            # Primary type gets full points
            primary_points = answer * difficulty * SCORING_WEIGHTS["primary"]
            scores[primary_type] += primary_points
            question_counts[primary_type] += 1
            
            # Wing types get partial points
            for wing_type in TYPE_WINGS.get(primary_type, []):
                wing_points = answer * difficulty * SCORING_WEIGHTS["wing"]
                scores[wing_type] += wing_points
            
            # Stress/growth lines get partial points
            stress_growth = TYPE_STRESS_GROWTH.get(primary_type, {})
            for line_type in [stress_growth.get("stress"), stress_growth.get("growth")]:
                if line_type:
                    line_points = answer * difficulty * SCORING_WEIGHTS["stress_growth"]
                    scores[line_type] += line_points
            
            # Same triad types get small bonus
            triad = TRIAD_FOR_TYPE.get(primary_type)
            if triad:
                for triad_type in TYPE_TRIADS.get(triad, []):
                    if triad_type != primary_type:
                        triad_points = answer * difficulty * SCORING_WEIGHTS["same_triad"]
                        scores[triad_type] += triad_points
            
            # Secondary influence gets small bonus if present
            if secondary_type and secondary_type != primary_type:
                secondary_points = answer * difficulty * 0.05
                scores[secondary_type] += secondary_points
        
        return scores, question_counts
    
    def normalize_scores(self, raw_scores: Dict[int, float]) -> Dict[int, float]:
        """Convert raw scores to percentages (0-100)."""
        total = sum(raw_scores.values())
        if total == 0:
            return {t: 0.0 for t in range(1, 10)}
        
        return {t: (score / total) * 100 for t, score in raw_scores.items()}
    
    def get_top_types(self, normalized_scores: Dict[int, float]) -> Tuple[int, int]:
        """Return the top 2 types by score."""
        sorted_types = sorted(normalized_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_types[0][0], sorted_types[1][0]
    
    def suggest_wing(self, primary_type: int, normalized_scores: Dict[int, float]) -> int:
        """Suggest the most likely wing based on scores."""
        wings = TYPE_WINGS.get(primary_type, [])
        if not wings:
            return primary_type
        
        wing_scores = {w: normalized_scores.get(w, 0) for w in wings}
        return max(wing_scores.items(), key=lambda x: x[1])[0]
    
    def check_result_clarity(self, primary_pct: float, secondary_pct: float) -> bool:
        """Check if result is unclear (top 2 within 10%)."""
        return abs(primary_pct - secondary_pct) <= 10

# =============================================================================
# GAMING DETECTION
# =============================================================================

class GamingDetector:
    """Detects suspicious response patterns that suggest gaming or random answers."""
    
    def __init__(self):
        self.question_map = {q["id"]: q for q in QUESTION_BANK}
    
    def analyze(self, responses: List[QuestionResponse]) -> GamingIndicators:
        """Analyze responses for gaming indicators."""
        if not responses:
            return GamingIndicators(
                avg_response_time_ms=0,
                fast_responses_count=0,
                slow_responses_count=0,
                variance_score=0,
                all_same_value=False,
                randomness_score=0,
                consistency_failures=0,
                is_suspicious=False,
                flags=[]
            )
        
        flags = []
        
        # Response time analysis
        times = [r.response_time_ms for r in responses]
        avg_time = sum(times) / len(times)
        fast_count = sum(1 for t in times if t < MIN_RESPONSE_TIME_MS)
        slow_count = sum(1 for t in times if t > MAX_RESPONSE_TIME_MS)
        
        if fast_count > len(responses) * 0.3:
            flags.append("HIGH_FAST_RESPONSE_RATE")
        if slow_count > len(responses) * 0.3:
            flags.append("HIGH_SLOW_RESPONSE_RATE")
        
        # Answer variance analysis
        answers = [r.answer_value for r in responses]
        all_same = len(set(answers)) == 1
        if all_same:
            flags.append("ALL_SAME_ANSWERS")
        
        # Calculate variance (higher variance = more random)
        mean_answer = sum(answers) / len(answers)
        variance = sum((a - mean_answer) ** 2 for a in answers) / len(answers)
        
        # Randomness score: check for alternating or patterned responses
        randomness = self._calculate_randomness(answers)
        if randomness > 0.8:
            flags.append("HIGH_RANDOMNESS")
        
        # Consistency check for validation pairs
        consistency_failures = self._check_validation_pairs(responses)
        if consistency_failures > 2:
            flags.append("CONSISTENCY_FAILURES")
        
        is_suspicious = len(flags) >= 2 or all_same or consistency_failures > 2
        
        return GamingIndicators(
            avg_response_time_ms=avg_time,
            fast_responses_count=fast_count,
            slow_responses_count=slow_count,
            variance_score=variance,
            all_same_value=all_same,
            randomness_score=randomness,
            consistency_failures=consistency_failures,
            is_suspicious=is_suspicious,
            flags=flags
        )
    
    def _calculate_randomness(self, answers: List[int]) -> float:
        """Calculate how random the answer pattern appears (0-1)."""
        if len(answers) < 3:
            return 0.0
        
        # Check for sequential patterns
        alternations = 0
        for i in range(1, len(answers)):
            if answers[i] != answers[i-1]:
                alternations += 1
        
        # Perfect alternation would be suspicious
        alternation_rate = alternations / (len(answers) - 1)
        
        # Check distribution across all options
        value_counts = {}
        for a in answers:
            value_counts[a] = value_counts.get(a, 0) + 1
        
        # If all options used roughly equally, might be random
        expected_per_value = len(answers) / 5
        deviation = sum(abs(count - expected_per_value) for count in value_counts.values())
        normalized_deviation = deviation / len(answers)
        
        # Combine metrics (lower deviation + high alternation = more random)
        randomness = (1 - normalized_deviation) * 0.5 + (alternation_rate * 0.5 if alternation_rate > 0.7 else 0)
        
        return min(1.0, randomness)
    
    def _check_validation_pairs(self, responses: List[QuestionResponse]) -> int:
        """Check reverse-coded validation pairs for contradictions."""
        failures = 0
        response_map = {r.question_id: r.answer_value for r in responses}
        
        for question in QUESTION_BANK:
            pair_id = question.get("validation_pair")
            if not pair_id or question.get("reverse_coded"):
                continue
            
            q1_answer = response_map.get(question["id"])
            q2_answer = response_map.get(pair_id)
            
            if q1_answer is None or q2_answer is None:
                continue
            
            # For validation pairs, answers should correlate
            # Q1 high (5) should mean Q2 high (5) after reverse coding
            # If Q1=5 and Q2=1 (reverse coded), that's consistent
            # If Q1=5 and Q2=5 (reverse coded to 1), that's inconsistent
            difference = abs(q1_answer - q2_answer)
            if difference > CONTRADICTION_THRESHOLD:
                failures += 1
        
        return failures
    
    def get_consistency_details(self, responses: List[QuestionResponse]) -> List[ConsistencyCheck]:
        """Get detailed consistency check results."""
        checks = []
        response_map = {r.question_id: r.answer_value for r in responses}
        
        for question in QUESTION_BANK:
            pair_id = question.get("validation_pair")
            if not pair_id or question.get("reverse_coded"):
                continue
            
            q1_answer = response_map.get(question["id"])
            q2_answer = response_map.get(pair_id)
            
            if q1_answer is None or q2_answer is None:
                continue
            
            difference = abs(q1_answer - q2_answer)
            is_consistent = difference <= CONTRADICTION_THRESHOLD
            
            checks.append(ConsistencyCheck(
                pair_id=f"{question['id']}-{pair_id}",
                question_1=question["id"],
                question_2=pair_id,
                answer_1=q1_answer,
                answer_2=q2_answer,
                difference=difference,
                is_consistent=is_consistent
            ))
        
        return checks

# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

class SessionManager:
    """Manages assessment sessions with persistence and resume capability."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["v4_sessions"]
        self.results_collection = db["v4_results"]
    
    async def create_session(self, user_id: str) -> Dict:
        """Create a new assessment session."""
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "status": "in_progress",
            "current_question_index": 0,
            "current_section": "body",  # body -> heart -> head
            "responses": [],
            "start_time": now.isoformat(),
            "last_activity": now.isoformat(),
            "expires_at": (now + timedelta(hours=SESSION_TTL_HOURS)).isoformat(),
            "completed_sections": [],
            "created_at": now.isoformat(),
        }
        
        await self.collection.insert_one(session)
        logger.info(f"[V4Assessment] Created session {session_id} for user {user_id}")
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve a session by ID."""
        session = await self.collection.find_one({"session_id": session_id})
        if session:
            session.pop("_id", None)
        return session
    
    async def get_user_session(self, user_id: str) -> Optional[Dict]:
        """Get active session for a user."""
        now = datetime.utcnow().isoformat()
        session = await self.collection.find_one({
            "user_id": user_id,
            "status": "in_progress",
            "expires_at": {"$gt": now}
        })
        if session:
            session.pop("_id", None)
        return session
    
    async def update_session(self, session_id: str, updates: Dict) -> bool:
        """Update session with new data."""
        updates["last_activity"] = datetime.utcnow().isoformat()
        result = await self.collection.update_one(
            {"session_id": session_id},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    async def add_response(self, session_id: str, response: QuestionResponse) -> bool:
        """Add a question response to the session."""
        result = await self.collection.update_one(
            {"session_id": session_id},
            {
                "$push": {"responses": asdict(response)},
                "$inc": {"current_question_index": 1},
                "$set": {"last_activity": datetime.utcnow().isoformat()}
            }
        )
        return result.modified_count > 0
    
    async def complete_session(self, session_id: str, result: AssessmentResult) -> bool:
        """Mark session as complete and store results."""
        now = datetime.utcnow().isoformat()
        
        # Update session status
        await self.collection.update_one(
            {"session_id": session_id},
            {"$set": {
                "status": "completed",
                "completed_at": now,
                "last_activity": now
            }}
        )
        
        # Store result
        result_doc = {
            "session_id": session_id,
            "primary_type": result.primary_type,
            "primary_percentage": result.primary_percentage,
            "secondary_type": result.secondary_type,
            "secondary_percentage": result.secondary_percentage,
            "suggested_wing": result.suggested_wing,
            "all_scores": [asdict(s) for s in result.all_scores],
            "confidence_level": result.confidence_level,
            "is_unclear": result.is_unclear,
            "gaming_indicators": asdict(result.gaming_indicators),
            "created_at": now
        }
        
        await self.results_collection.insert_one(result_doc)
        logger.info(f"[V4Assessment] Completed session {session_id}")
        
        return True
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        result = await self.collection.delete_one({"session_id": session_id})
        return result.deleted_count > 0

# =============================================================================
# MAIN ASSESSMENT CLASS
# =============================================================================

class EnneagramAssessmentV4:
    """Main assessment class coordinating all components."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.session_manager = SessionManager(db)
        self.scoring_engine = ScoringEngine()
        self.gaming_detector = GamingDetector()
        self.questions = QUESTION_BANK
    
    async def start_assessment(self, user_id: str) -> Dict:
        """Start a new assessment or resume existing one."""
        # Check for existing session
        existing = await self.session_manager.get_user_session(user_id)
        if existing:
            return {
                "status": "resumed",
                "session_id": existing["session_id"],
                "current_index": existing["current_question_index"],
                "total_questions": len(self.questions),
                "next_batch": self._get_question_batch(existing["current_question_index"])
            }
        
        # Create new session
        session = await self.session_manager.create_session(user_id)
        
        return {
            "status": "started",
            "session_id": session["session_id"],
            "current_index": 0,
            "total_questions": len(self.questions),
            "next_batch": self._get_question_batch(0)
        }
    
    def _get_question_batch(self, start_index: int) -> List[Dict]:
        """Get a batch of questions starting from index."""
        end_index = min(start_index + QUESTIONS_PER_BATCH, len(self.questions))
        batch = []
        
        for i in range(start_index, end_index):
            q = self.questions[i].copy()
            q["index"] = i
            # Remove internal fields from client response
            q.pop("validation_pair", None)
            batch.append(q)
        
        return batch
    
    async def submit_answer(
        self,
        session_id: str,
        question_id: str,
        answer_value: int,
        response_time_ms: int
    ) -> Dict:
        """Submit an answer and get progress/next question."""
        session = await self.session_manager.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        
        if session["status"] != "in_progress":
            raise ValueError("Session is not active")
        
        # Validate answer
        if not 1 <= answer_value <= 5:
            raise ValueError("Answer must be between 1 and 5")
        
        # Create response record
        response = QuestionResponse(
            question_id=question_id,
            answer_value=answer_value,
            response_time_ms=response_time_ms,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Save response
        await self.session_manager.add_response(session_id, response)
        
        # Get updated session
        session = await self.session_manager.get_session(session_id)
        current_index = session["current_question_index"]
        
        # Check if assessment is complete
        if current_index >= len(self.questions):
            # Calculate final results
            result = await self.calculate_results(session_id)
            return {
                "status": "completed",
                "result": self._format_result(result)
            }
        
        # Determine section progress
        section = self._get_section_for_index(current_index)
        section_progress = self._get_section_progress(current_index)
        
        return {
            "status": "in_progress",
            "current_index": current_index,
            "total_questions": len(self.questions),
            "section": section,
            "section_progress": section_progress,
            "next_batch": self._get_question_batch(current_index) if current_index % QUESTIONS_PER_BATCH == 0 else None
        }
    
    def _get_section_for_index(self, index: int) -> str:
        """Determine which section (triad) for question index."""
        if index < 12:
            return "body"
        elif index < 24:
            return "heart"
        elif index < 36:
            return "head"
        else:
            return "validation"
    
    def _get_section_progress(self, index: int) -> Dict:
        """Get progress within current section."""
        section = self._get_section_for_index(index)
        if section == "body":
            return {"section": "body", "current": index + 1, "total": 12}
        elif section == "heart":
            return {"section": "heart", "current": index - 11, "total": 12}
        elif section == "head":
            return {"section": "head", "current": index - 23, "total": 12}
        else:
            return {"section": "validation", "current": index - 35, "total": 6}
    
    async def calculate_results(self, session_id: str) -> AssessmentResult:
        """Calculate final assessment results."""
        session = await self.session_manager.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Convert stored responses to QuestionResponse objects
        responses = [
            QuestionResponse(**r) for r in session["responses"]
        ]
        
        # Calculate scores
        raw_scores, question_counts = self.scoring_engine.calculate_scores(responses)
        normalized_scores = self.scoring_engine.normalize_scores(raw_scores)
        
        # Get top types
        primary_type, secondary_type = self.scoring_engine.get_top_types(normalized_scores)
        primary_pct = normalized_scores[primary_type]
        secondary_pct = normalized_scores[secondary_type]
        
        # Check clarity
        is_unclear = self.scoring_engine.check_result_clarity(primary_pct, secondary_pct)
        
        # Suggest wing
        suggested_wing = self.scoring_engine.suggest_wing(primary_type, normalized_scores)
        
        # Gaming detection
        gaming_indicators = self.gaming_detector.analyze(responses)
        consistency_checks = self.gaming_detector.get_consistency_details(responses)
        
        # Calculate confidence score (0-100)
        confidence_score = 100
        
        # Reduce for unclear result (top 2 within 10%)
        if is_unclear:
            confidence_score -= 25
        
        # Reduce for gaming indicators
        if gaming_indicators.is_suspicious:
            confidence_score -= 30
        if gaming_indicators.consistency_failures > 0:
            confidence_score -= (gaming_indicators.consistency_failures * 5)
        if gaming_indicators.fast_responses_count > len(responses) * 0.2:
            confidence_score -= 10
        if gaming_indicators.all_same_value:
            confidence_score -= 40
        
        # Boost for good response patterns
        avg_time = gaming_indicators.avg_response_time_ms
        if 3000 < avg_time < 30000:  # 3-30 seconds is ideal
            confidence_score += 5
        
        # Ensure score stays in range
        confidence_score = max(0, min(100, confidence_score))
        
        # Determine confidence level
        if confidence_score >= 75:
            confidence = "high"
        elif confidence_score >= 50:
            confidence = "medium"
        else:
            confidence = "low"
        
        # Build type scores list
        all_scores = [
            TypeScore(
                type_number=t,
                raw_score=raw_scores[t],
                normalized_percentage=round(normalized_scores[t], 2),
                question_count=question_counts.get(t, 0)
            )
            for t in range(1, 10)
        ]
        all_scores.sort(key=lambda x: x.normalized_percentage, reverse=True)
        
        result = AssessmentResult(
            primary_type=primary_type,
            primary_percentage=round(primary_pct, 2),
            secondary_type=secondary_type,
            secondary_percentage=round(secondary_pct, 2),
            suggested_wing=suggested_wing,
            all_scores=all_scores,
            confidence_level=confidence,
            confidence_score=confidence_score,
            is_unclear=is_unclear,
            gaming_indicators=gaming_indicators,
            consistency_checks=consistency_checks
        )
        
        # Save result
        await self.session_manager.complete_session(session_id, result)
        
        return result
    
    def _format_result(self, result: AssessmentResult) -> Dict:
        """Format result for API response."""
        primary_desc = TYPE_DESCRIPTIONS.get(result.primary_type, {})
        secondary_desc = TYPE_DESCRIPTIONS.get(result.secondary_type, {})
        
        return {
            "primary_type": {
                "number": result.primary_type,
                "name": primary_desc.get("name", f"Type {result.primary_type}"),
                "percentage": result.primary_percentage,
                "core_desire": primary_desc.get("core_desire", ""),
                "core_fear": primary_desc.get("core_fear", ""),
                "brief": primary_desc.get("brief", "")
            },
            "secondary_type": {
                "number": result.secondary_type,
                "name": secondary_desc.get("name", f"Type {result.secondary_type}"),
                "percentage": result.secondary_percentage
            },
            "suggested_wing": result.suggested_wing,
            "full_type_string": f"{result.primary_type}w{result.suggested_wing}",
            "all_scores": [
                {
                    "type": s.type_number,
                    "name": TYPE_DESCRIPTIONS.get(s.type_number, {}).get("name", f"Type {s.type_number}"),
                    "percentage": s.normalized_percentage
                }
                for s in result.all_scores
            ],
            "confidence_level": result.confidence_level,
            "is_unclear": result.is_unclear,
            "flags": result.gaming_indicators.flags if result.gaming_indicators.is_suspicious else []
        }
    
    async def get_results(self, session_id: str) -> Optional[Dict]:
        """Get results for a completed session."""
        session = await self.session_manager.get_session(session_id)
        if not session or session["status"] != "completed":
            return None
        
        result_doc = await self.session_manager.results_collection.find_one(
            {"session_id": session_id}
        )
        if result_doc:
            result_doc.pop("_id", None)
        return result_doc
    
    async def resume_session(self, user_id: str) -> Optional[Dict]:
        """Resume an existing session for a user."""
        session = await self.session_manager.get_user_session(user_id)
        if not session:
            return None
        
        return {
            "status": "resumed",
            "session_id": session["session_id"],
            "current_index": session["current_question_index"],
            "total_questions": len(self.questions),
            "responses_count": len(session["responses"]),
            "next_batch": self._get_question_batch(session["current_question_index"])
        }

# =============================================================================
# API HELPER FUNCTIONS
# =============================================================================

def get_all_questions() -> List[Dict]:
    """Get all questions (for admin/testing)."""
    return QUESTION_BANK

def get_question_batch(start_index: int) -> List[Dict]:
    """Get a batch of questions."""
    end_index = min(start_index + QUESTIONS_PER_BATCH, len(QUESTION_BANK))
    return QUESTION_BANK[start_index:end_index]

def get_type_description(type_number: int) -> Dict:
    """Get description for a type."""
    return TYPE_DESCRIPTIONS.get(type_number, {})
