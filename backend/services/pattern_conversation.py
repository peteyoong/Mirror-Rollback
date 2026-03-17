"""
Pattern Conversation Service v1.0

Task 76: Conversational Intelligence Layer

Transforms Mirror from descriptive insights into an interactive thinking partner.

Response style:
- Direct, not hedged
- Specific, not generic
- Grounded in user data
- Slightly challenging
- No spiritual fluff
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import os

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# =============================================================================
# CONVERSATION SYSTEM PROMPTS
# =============================================================================

CONVERSATION_SYSTEM_PROMPT = """You are Mirror's conversational intelligence layer. You help users explore their patterns through direct, grounded dialogue.

RULES:
1. NEVER hedge. No "may", "might", "could", "tends to", "suggests", "appears to"
2. Be direct. State what you observe.
3. Be specific. Reference their actual data.
4. Be slightly challenging. Push them to see clearly.
5. No spiritual fluff. No generic affirmations.
6. Keep responses concise—3-4 sentences max for most turns.
7. Always end with a question that moves the conversation forward.

YOUR VOICE:
- Like a sharp friend who knows your history
- Direct but not harsh
- Observational, not prescriptive
- Grounded in their timeline and patterns

WHAT YOU KNOW ABOUT THIS USER:
{user_context}

THEIR PRIMARY ARCHETYPE: {archetype_name}
{archetype_summary}

RESPOND to their message with insight drawn from their actual data. Challenge them to see what they might be avoiding."""

INITIAL_PROMPT_TEMPLATE = """Where is your {archetype_name} pattern showing up most in your life right now?"""

FOLLOW_UP_QUESTIONS = [
    "What would happen if you stopped fighting this?",
    "When have you been here before?",
    "What are you pretending not to know?",
    "What's the cost of staying where you are?",
    "Who would you disappoint by changing?",
    "What decision are you avoiding?",
    "What truth are you dancing around?",
    "What would the version of you from five years ago say about this?",
    "What are you building that you haven't named yet?",
    "Where is the pattern breaking down?",
]

# =============================================================================
# CONVERSATION SERVICE
# =============================================================================

class PatternConversationService:
    """Service for managing pattern-based conversations."""
    
    def __init__(self, db):
        self.db = db
        
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Gather all relevant user data for conversation context."""
        context = {
            "archetype": None,
            "lifeline_events": [],
            "strongest_signals": [],
            "recent_journal": [],
            "pattern_domains": []
        }
        
        try:
            # Get archetype data
            from services.pattern_archetype import get_user_archetype
            archetype_result = await get_user_archetype(self.db, user_id)
            if archetype_result and archetype_result.get("primary_archetype"):
                context["archetype"] = archetype_result["primary_archetype"]
            
            # Get lifeline events (last 10)
            lifeline_events = await self.db.lifeline_events.find(
                {"user_id": user_id}
            ).sort("year", -1).limit(10).to_list(length=10)
            
            context["lifeline_events"] = [
                {
                    "year": e.get("year"),
                    "title": e.get("title"),
                    "category": e.get("category"),
                    "significance": e.get("significance")
                }
                for e in lifeline_events
            ]
            
            # Get pattern signals
            signals = await self.db.pattern_signals.find(
                {"user_id": user_id}
            ).sort("strength", -1).limit(5).to_list(length=5)
            
            context["strongest_signals"] = [
                {
                    "domain": s.get("domain"),
                    "label": s.get("label"),
                    "strength": s.get("strength")
                }
                for s in signals
            ]
            
            # Get recent journal entries
            journal_entries = await self.db.journal_entries.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(3).to_list(length=3)
            
            context["recent_journal"] = [
                {
                    "date": str(e.get("created_at", ""))[:10],
                    "content_preview": (e.get("content", "")[:100] + "...") if len(e.get("content", "")) > 100 else e.get("content", "")
                }
                for e in journal_entries
            ]
            
            # Get active pattern domains
            patterns = await self.db.pattern_graph.find_one({"user_id": user_id})
            if patterns and patterns.get("domains"):
                context["pattern_domains"] = [
                    {
                        "name": d.get("name"),
                        "strength": d.get("strength"),
                        "state": d.get("state")
                    }
                    for d in patterns["domains"]
                    if d.get("strength", 0) > 0.3
                ]
            
        except Exception as e:
            logger.error(f"[PatternConversation] Error gathering context: {e}")
        
        return context
    
    def format_user_context(self, context: Dict[str, Any]) -> str:
        """Format user context into readable prompt content."""
        parts = []
        
        # Lifeline events
        if context.get("lifeline_events"):
            events_text = "LIFELINE EVENTS:\n"
            for e in context["lifeline_events"][:5]:
                events_text += f"- {e.get('year', 'N/A')}: {e.get('title', 'Unknown')} ({e.get('category', 'Other')})\n"
            parts.append(events_text)
        
        # Active patterns
        if context.get("pattern_domains"):
            patterns_text = "ACTIVE PATTERNS:\n"
            for p in context["pattern_domains"][:4]:
                state = p.get("state", "unknown")
                strength = p.get("strength", 0)
                patterns_text += f"- {p.get('name', 'Unknown')}: {state} (strength: {strength:.1%})\n"
            parts.append(patterns_text)
        
        # Strongest signals
        if context.get("strongest_signals"):
            signals_text = "STRONGEST SIGNALS:\n"
            for s in context["strongest_signals"][:3]:
                signals_text += f"- {s.get('label', 'Unknown')} in {s.get('domain', 'unknown')}\n"
            parts.append(signals_text)
        
        # Recent reflections
        if context.get("recent_journal"):
            journal_text = "RECENT REFLECTIONS:\n"
            for j in context["recent_journal"][:2]:
                journal_text += f"- {j.get('date', 'Unknown')}: \"{j.get('content_preview', '')}\"\n"
            parts.append(journal_text)
        
        return "\n".join(parts) if parts else "Limited data available for this user."
    
    def select_follow_up_question(self, archetype: Dict[str, Any], message: str, response: str) -> str:
        """Select an appropriate follow-up question based on context."""
        import random
        
        # Use archetype's reflection question sometimes
        if archetype and random.random() < 0.3:
            narrative = archetype.get("narrative", {})
            if narrative.get("reflection_question"):
                return narrative["reflection_question"]
        
        # Otherwise select from pool
        return random.choice(FOLLOW_UP_QUESTIONS)
    
    async def generate_response(
        self,
        user_id: str,
        message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Generate a conversational response grounded in user data."""
        
        # Get user context
        context = await self.get_user_context(user_id)
        archetype = context.get("archetype")
        
        if not archetype:
            return {
                "success": False,
                "error": "Unable to generate response - archetype not available",
                "response": "I need more data to have this conversation. Add some lifeline events or journal entries first."
            }
        
        # Format context for prompt
        user_context_text = self.format_user_context(context)
        archetype_name = archetype.get("name", "Unknown")
        archetype_summary = archetype.get("narrative", {}).get("summary", "")
        
        # Build system prompt
        system_prompt = CONVERSATION_SYSTEM_PROMPT.format(
            user_context=user_context_text,
            archetype_name=archetype_name,
            archetype_summary=archetype_summary
        )
        
        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        if conversation_history:
            for turn in conversation_history[-6:]:  # Last 6 turns
                messages.append({
                    "role": turn.get("role", "user"),
                    "content": turn.get("content", "")
                })
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        try:
            # Generate response using LLM
            from emergentintegrations.llm.chat import chat, UserMessage, SystemMessage
            
            emergent_key = os.getenv("EMERGENT_LLM_KEY")
            if not emergent_key:
                logger.error("[PatternConversation] EMERGENT_LLM_KEY not found")
                return self._generate_fallback_response(archetype, message, context)
            
            # Convert to emergent format
            emergent_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    emergent_messages.append(SystemMessage(content=msg["content"]))
                else:
                    emergent_messages.append(UserMessage(content=msg["content"]))
            
            response = await chat(
                api_key=emergent_key,
                model="gpt-4.1-mini",
                messages=emergent_messages,
                max_tokens=500,
                temperature=0.7
            )
            
            response_text = response.message if hasattr(response, 'message') else str(response)
            
            # Select follow-up question
            follow_up = self.select_follow_up_question(archetype, message, response_text)
            
            # Extract referenced events
            referenced_events = self._extract_referenced_events(
                response_text, 
                context.get("lifeline_events", [])
            )
            
            return {
                "success": True,
                "response": response_text,
                "referenced_archetype": archetype_name,
                "referenced_events": referenced_events,
                "follow_up_question": follow_up,
                "archetype_icon": archetype.get("icon", "◈")
            }
            
        except Exception as e:
            logger.error(f"[PatternConversation] LLM error: {e}")
            return self._generate_fallback_response(archetype, message, context)
    
    def _generate_fallback_response(
        self, 
        archetype: Dict[str, Any], 
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a fallback response when LLM is unavailable."""
        
        archetype_name = archetype.get("name", "your pattern")
        narrative = archetype.get("narrative", {})
        
        # Build response from archetype data
        summary = narrative.get("summary", "")
        current = narrative.get("current_expression", "")
        
        # Check for keywords in message
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["work", "career", "job"]):
            response = f"Your {archetype_name} pattern runs through your work life. {narrative.get('how_this_shows_up', [''])[0] if narrative.get('how_this_shows_up') else ''}"
        elif any(word in message_lower for word in ["relationship", "partner", "friend"]):
            response = f"This pattern shapes your relationships too. {narrative.get('how_this_shows_up', ['', ''])[1] if len(narrative.get('how_this_shows_up', [])) > 1 else ''}"
        elif any(word in message_lower for word in ["stuck", "lost", "confused"]):
            response = f"You're not stuck—you're in transition. {current}"
        else:
            response = f"{summary}\n\n{current}"
        
        return {
            "success": True,
            "response": response,
            "referenced_archetype": archetype_name,
            "referenced_events": [],
            "follow_up_question": narrative.get("reflection_question", "What are you noticing?"),
            "archetype_icon": archetype.get("icon", "◈"),
            "fallback": True
        }
    
    def _extract_referenced_events(
        self, 
        response: str, 
        events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract events that were referenced in the response."""
        referenced = []
        response_lower = response.lower()
        
        for event in events:
            title = event.get("title", "").lower()
            year = str(event.get("year", ""))
            
            # Check if event title or year appears in response
            if title and len(title) > 3 and title in response_lower:
                referenced.append(event)
            elif year and year in response:
                referenced.append(event)
        
        return referenced[:3]  # Max 3 references
    
    async def get_initial_prompt(self, user_id: str) -> Dict[str, Any]:
        """Get the initial conversation prompt based on user's archetype."""
        
        context = await self.get_user_context(user_id)
        archetype = context.get("archetype")
        
        if not archetype:
            return {
                "success": False,
                "prompt": "Tell me about a pattern you've noticed in your life.",
                "archetype": None
            }
        
        archetype_name = archetype.get("name", "this pattern")
        
        return {
            "success": True,
            "prompt": INITIAL_PROMPT_TEMPLATE.format(archetype_name=archetype_name),
            "archetype": {
                "name": archetype_name,
                "icon": archetype.get("icon", "◈"),
                "summary": archetype.get("narrative", {}).get("summary", "")
            }
        }


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

async def generate_pattern_response(
    db,
    user_id: str,
    message: str,
    conversation_history: List[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Generate a pattern-based conversational response."""
    service = PatternConversationService(db)
    return await service.generate_response(user_id, message, conversation_history)


async def get_conversation_starter(db, user_id: str) -> Dict[str, Any]:
    """Get the initial prompt to start a pattern conversation."""
    service = PatternConversationService(db)
    return await service.get_initial_prompt(user_id)
