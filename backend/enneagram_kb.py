"""
Enneagram Knowledge Base Module

Provides PDF-based retrieval for Enneagram Q&A using TF-IDF + cosine similarity.
Lightweight implementation without external vector databases.

Features:
- Loads and indexes PDF at server startup
- Chunks text with overlap for better retrieval
- Returns citations with page numbers
- Gracefully handles missing PDF
- Generates trait cards for Deep Dive UI
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# TF-IDF imports
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# PDF paths to try (in order of preference)
PDF_PATHS = [
    os.environ.get('ENNEAGRAM_PDF_PATH', '/app/backend/data/JOH_Book_1.pdf'),
    '/app/backend/data/JOH_Book_1.pdf',
    '/mnt/data/JOH Book 1.pdf',
    '/mnt/data/JOH_Book_1.pdf',
]

CHUNK_SIZE = 900  # Target chunk size in characters
CHUNK_OVERLAP = 120  # Overlap between chunks
MIN_CHUNK_SIZE = 200  # Minimum viable chunk size
ENNEAGRAM_KEYWORDS = ['enneagram', 'type', 'wing', 'center', 'instinct', 'fixation', 
                       'passion', 'virtue', 'holy idea', 'stress', 'growth', 'integration',
                       'disintegration', 'triads', 'hornevian', 'harmonic']

# Type name mappings for search enhancement
TYPE_NAMES = {
    1: ["one", "perfectionist", "reformer"],
    2: ["two", "helper", "giver"],
    3: ["three", "achiever", "performer"],
    4: ["four", "individualist", "romantic"],
    5: ["five", "investigator", "observer"],
    6: ["six", "loyalist", "questioner"],
    7: ["seven", "enthusiast", "epicure"],
    8: ["eight", "challenger", "protector"],
    9: ["nine", "peacemaker", "mediator"],
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Chunk:
    """A text chunk from the PDF with metadata."""
    text: str
    chunk_id: str
    pdf_page: int
    start_char: int = 0
    end_char: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "chunk_id": self.chunk_id,
            "pdf_page": self.pdf_page,
        }


@dataclass
class RetrievalResult:
    """Result from a retrieval query."""
    chunk: Chunk
    score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.chunk.text,
            "score": round(self.score, 4),
            "meta": {
                "pdf_page": self.chunk.pdf_page,
                "chunk_id": self.chunk.chunk_id,
            }
        }


@dataclass
class AnswerResult:
    """Result from an answer query."""
    answer_text: str
    citations: List[Dict[str, Any]]
    used_chunks: List[Dict[str, Any]]
    
    def to_dict(self, include_debug: bool = False) -> Dict[str, Any]:
        result = {
            "answer": self.answer_text,
            "citations": self.citations,
        }
        if include_debug:
            result["debug"] = {"used_chunks": self.used_chunks}
        return result


# ============================================================================
# ENNEAGRAM TYPE MAPPINGS (Deterministic)
# ============================================================================

# Center/Triad mappings
TYPE_CENTER = {
    1: "gut",    # Body/Instinctive center
    2: "heart",  # Feeling center
    3: "heart",
    4: "heart",
    5: "head",   # Thinking center
    6: "head",
    7: "head",
    8: "gut",
    9: "gut",
}

# Hornevian Groups (Social Styles)
TYPE_HORNEVIAN = {
    1: "compliant",   # Move toward people
    2: "compliant",
    6: "compliant",
    3: "assertive",   # Move against people
    7: "assertive",
    8: "assertive",
    4: "withdrawn",   # Move away from people
    5: "withdrawn",
    9: "withdrawn",
}

# Harmonic Groups (Conflict Styles)
TYPE_HARMONIC = {
    1: "competency",      # Focus on solving problems objectively
    3: "competency",
    5: "competency",
    2: "positive_outlook", # Focus on positive, avoid negative
    7: "positive_outlook",
    9: "positive_outlook",
    4: "reactive",         # React emotionally, need to process
    6: "reactive",
    8: "reactive",
}

# Object Relations (Hornevian x Harmonic intersection patterns)
TYPE_OBJECT_RELATIONS = {
    1: "frustration",
    2: "rejection",
    3: "attachment",
    4: "frustration",
    5: "rejection",
    6: "attachment",
    7: "frustration",
    8: "rejection",
    9: "attachment",
}

# Stress and Growth Lines
TYPE_STRESS_LINE = {
    1: 4, 2: 8, 3: 9, 4: 2, 5: 7, 6: 3, 7: 1, 8: 5, 9: 6
}

TYPE_GROWTH_LINE = {
    1: 7, 2: 4, 3: 6, 4: 1, 5: 8, 6: 9, 7: 5, 8: 2, 9: 3
}

# Wing adjacencies
TYPE_WINGS = {
    1: (9, 2), 2: (1, 3), 3: (2, 4), 4: (3, 5), 5: (4, 6),
    6: (5, 7), 7: (6, 8), 8: (7, 9), 9: (8, 1)
}

# Social style tags per type
TYPE_SOCIAL_TAGS = {
    1: ["principled", "reformer", "perfectionist", "idealist", "critic", "organized"],
    2: ["helper", "giver", "people-pleaser", "supportive", "caring", "warm"],
    3: ["achiever", "performer", "efficient", "driven", "image-conscious", "adaptable"],
    4: ["individualist", "romantic", "creative", "expressive", "melancholic", "authentic"],
    5: ["investigator", "observer", "analytical", "detached", "innovative", "private"],
    6: ["loyalist", "questioner", "responsible", "anxious", "prepared", "skeptical"],
    7: ["enthusiast", "epicure", "optimistic", "scattered", "adventurous", "versatile"],
    8: ["challenger", "protector", "powerful", "confrontational", "direct", "decisive"],
    9: ["peacemaker", "mediator", "receptive", "agreeable", "complacent", "steady"],
}


def compute_enneagram_details(
    core_type: int,
    wing: int,
    wing_left_score: float = 0.0,
    wing_right_score: float = 0.0,
    confidence: float = 0.0
) -> Dict[str, Any]:
    """
    Compute enriched Enneagram details from core type and wing.
    All mappings are deterministic (no LLM required).
    
    Returns a dictionary with triads, lines, groups, and other computed fields.
    """
    if core_type < 1 or core_type > 9:
        return {"error": "Invalid core type"}
    
    left_wing, right_wing = TYPE_WINGS.get(core_type, (0, 0))
    
    # Determine wing balance
    wing_diff = abs(wing_left_score - wing_right_score)
    if wing_diff < 0.3:
        wing_balance = "balanced"
        wing_hint = "Both wings seem accessible; you may draw from either depending on context."
    elif wing_left_score > wing_right_score:
        wing_balance = "left-dominant"
        wing_hint = f"Your {left_wing}-wing tends to be more active, adding its qualities to your core."
    else:
        wing_balance = "right-dominant"
        wing_hint = f"Your {right_wing}-wing tends to be more active, adding its qualities to your core."
    
    # Determine relevant knowledge base tags based on type patterns
    traits_tags = [
        f"type{core_type}-pattern",
        f"center-{TYPE_CENTER[core_type]}",
        f"{TYPE_HORNEVIAN[core_type]}-style",
    ]
    
    if wing and wing in [left_wing, right_wing]:
        traits_tags.append(f"wing-{wing}-influence")
    
    # Add integration/disintegration tags
    traits_tags.append("stress-growth-lines")
    
    # Add group-specific tags
    if TYPE_HARMONIC[core_type] == "reactive":
        traits_tags.append("emotional-processing")
    elif TYPE_HARMONIC[core_type] == "competency":
        traits_tags.append("problem-solving-focus")
    else:
        traits_tags.append("positive-reframing")
    
    return {
        # Core mappings
        "center": TYPE_CENTER[core_type],
        "hornevian_group": TYPE_HORNEVIAN[core_type],
        "harmonic_group": TYPE_HARMONIC[core_type],
        "object_relations": TYPE_OBJECT_RELATIONS[core_type],
        "social_style_tags": TYPE_SOCIAL_TAGS.get(core_type, [])[:6],
        
        # Lines
        "stress_line_to": TYPE_STRESS_LINE[core_type],
        "growth_line_to": TYPE_GROWTH_LINE[core_type],
        
        # Wing openness
        "wing_left_type": left_wing,
        "wing_right_type": right_wing,
        "wing_left_score": round(wing_left_score, 2),
        "wing_right_score": round(wing_right_score, 2),
        "wing_balance_label": wing_balance,
        "wing_openness_hint": wing_hint,
        
        # Knowledge base refs
        "traits_library_refs": traits_tags,
    }


# ============================================================================
# KNOWLEDGE BASE CLASS
# ============================================================================

class EnneagramKnowledgeBase:
    """
    Lightweight knowledge base for Enneagram content retrieval.
    Uses TF-IDF + cosine similarity for semantic search.
    """
    
    def __init__(self, pdf_path: str = PDF_PATH):
        self.pdf_path = pdf_path
        self.chunks: List[Chunk] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.is_ready = False
        self.load_error: Optional[str] = None
        
    def initialize(self) -> bool:
        """
        Load PDF, extract text, chunk, and build TF-IDF index.
        Returns True if successful, False otherwise.
        """
        try:
            # Check if PDF exists
            if not os.path.exists(self.pdf_path):
                self.load_error = f"PDF not found at {self.pdf_path}"
                logger.warning(f"[EnneagramKB] {self.load_error}")
                return False
            
            # Extract text from PDF
            logger.info(f"[EnneagramKB] Loading PDF from {self.pdf_path}")
            pages_text = self._extract_pdf_text()
            
            if not pages_text:
                self.load_error = "Failed to extract text from PDF"
                logger.warning(f"[EnneagramKB] {self.load_error}")
                return False
            
            # Filter to Enneagram-relevant pages
            relevant_pages = self._filter_relevant_pages(pages_text)
            logger.info(f"[EnneagramKB] Found {len(relevant_pages)} relevant pages")
            
            # Chunk the text
            self.chunks = self._chunk_pages(relevant_pages)
            logger.info(f"[EnneagramKB] Created {len(self.chunks)} chunks")
            
            if not self.chunks:
                self.load_error = "No chunks created from PDF"
                return False
            
            # Build TF-IDF index
            self._build_index()
            
            self.is_ready = True
            logger.info("[EnneagramKB] Knowledge base initialized successfully")
            return True
            
        except Exception as e:
            self.load_error = str(e)
            logger.error(f"[EnneagramKB] Initialization failed: {e}")
            return False
    
    def _extract_pdf_text(self) -> Dict[int, str]:
        """Extract text from PDF pages using PyMuPDF."""
        try:
            import fitz  # PyMuPDF
            
            pages_text = {}
            doc = fitz.open(self.pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")
                
                # Clean up text
                text = self._clean_text(text)
                
                if text and len(text) > 50:  # Skip near-empty pages
                    pages_text[page_num + 1] = text  # 1-indexed page numbers
            
            doc.close()
            return pages_text
            
        except Exception as e:
            logger.error(f"[EnneagramKB] PDF extraction error: {e}")
            return {}
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove page numbers and headers (common patterns)
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        return text.strip()
    
    def _filter_relevant_pages(self, pages_text: Dict[int, str]) -> Dict[int, str]:
        """Filter to pages containing Enneagram-related content."""
        relevant = {}
        
        for page_num, text in pages_text.items():
            text_lower = text.lower()
            
            # Check if page contains Enneagram keywords
            keyword_count = sum(1 for kw in ENNEAGRAM_KEYWORDS if kw in text_lower)
            
            # Include if has multiple keywords or is in expected page range (48-85)
            if keyword_count >= 2 or (48 <= page_num <= 85):
                relevant[page_num] = text
        
        # If filtering removed too much, fall back to all pages with any keyword
        if len(relevant) < 10 and len(pages_text) > 0:
            for page_num, text in pages_text.items():
                if any(kw in text.lower() for kw in ENNEAGRAM_KEYWORDS[:5]):
                    relevant[page_num] = text
        
        return relevant
    
    def _chunk_pages(self, pages_text: Dict[int, str]) -> List[Chunk]:
        """Chunk pages into overlapping text segments."""
        chunks = []
        chunk_counter = 0
        
        for page_num, text in sorted(pages_text.items()):
            # Split into sentences first
            sentences = re.split(r'(?<=[.!?])\s+', text)
            
            current_chunk = ""
            start_char = 0
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) <= CHUNK_SIZE:
                    current_chunk += " " + sentence if current_chunk else sentence
                else:
                    # Save current chunk if it's big enough
                    if len(current_chunk) >= MIN_CHUNK_SIZE:
                        chunk_id = f"p{page_num:02d}_c{chunk_counter:03d}"
                        chunks.append(Chunk(
                            text=current_chunk.strip(),
                            chunk_id=chunk_id,
                            pdf_page=page_num,
                            start_char=start_char,
                            end_char=start_char + len(current_chunk)
                        ))
                        chunk_counter += 1
                    
                    # Start new chunk with overlap
                    overlap_text = current_chunk[-CHUNK_OVERLAP:] if len(current_chunk) > CHUNK_OVERLAP else ""
                    start_char += len(current_chunk) - len(overlap_text)
                    current_chunk = overlap_text + " " + sentence
            
            # Don't forget the last chunk of the page
            if len(current_chunk) >= MIN_CHUNK_SIZE:
                chunk_id = f"p{page_num:02d}_c{chunk_counter:03d}"
                chunks.append(Chunk(
                    text=current_chunk.strip(),
                    chunk_id=chunk_id,
                    pdf_page=page_num,
                ))
                chunk_counter += 1
        
        return chunks
    
    def _build_index(self):
        """Build TF-IDF index from chunks."""
        if not self.chunks:
            return
        
        texts = [chunk.text for chunk in self.chunks]
        
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),  # Unigrams and bigrams
            max_df=0.85,  # Ignore very common terms
            min_df=1,
            max_features=5000
        )
        
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)
        logger.info(f"[EnneagramKB] TF-IDF matrix shape: {self.tfidf_matrix.shape}")
    
    def retrieve(self, query: str, k: int = 6) -> List[RetrievalResult]:
        """
        Retrieve top-k most relevant chunks for a query.
        
        Args:
            query: The search query
            k: Number of results to return
            
        Returns:
            List of RetrievalResult objects with chunks and scores
        """
        if not self.is_ready or self.vectorizer is None:
            return []
        
        try:
            # Vectorize query
            query_vec = self.vectorizer.transform([query])
            
            # Compute cosine similarity
            similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
            
            # Get top-k indices
            top_indices = np.argsort(similarities)[::-1][:k]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.01:  # Filter very low scores
                    results.append(RetrievalResult(
                        chunk=self.chunks[idx],
                        score=float(similarities[idx])
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"[EnneagramKB] Retrieval error: {e}")
            return []
    
    async def answer(
        self,
        query: str,
        user_profile: Optional[Dict[str, Any]] = None,
        llm_func = None
    ) -> AnswerResult:
        """
        Generate an answer using retrieved context and LLM.
        
        Args:
            query: The user's question
            user_profile: Optional user's Enneagram profile for context
            llm_func: Async function to call LLM (signature: async (system, user) -> str)
            
        Returns:
            AnswerResult with answer text and citations
        """
        # Retrieve relevant chunks
        retrieved = self.retrieve(query, k=6)
        
        if not retrieved and not self.is_ready:
            return AnswerResult(
                answer_text="The Enneagram knowledge base is currently unavailable. Please try again later.",
                citations=[],
                used_chunks=[]
            )
        
        # Build context from chunks
        chunk_context = ""
        citations = []
        used_chunks = []
        
        for i, result in enumerate(retrieved):
            chunk_context += f"\n[Source {i+1}, Page {result.chunk.pdf_page}]:\n{result.chunk.text}\n"
            citations.append({
                "pdf": "JOH Book 1.pdf",
                "page": result.chunk.pdf_page,
                "chunk_id": result.chunk.chunk_id,
                "score": round(result.score, 4)
            })
            used_chunks.append(result.to_dict())
        
        # Build user context if available
        user_context = ""
        if user_profile:
            user_context = f"""
USER ENNEAGRAM CONTEXT:
- Core Type: {user_profile.get('inferred_core', 'Unknown')}
- Wing: {user_profile.get('inferred_wing', 'Unknown')}
- Confidence: {user_profile.get('confidence_tier', 'Unknown')}
"""
            if 'enneagram_computed_details' in user_profile:
                details = user_profile['enneagram_computed_details']
                user_context += f"""- Center: {details.get('center', 'Unknown')}
- Hornevian Group: {details.get('hornevian_group', 'Unknown')}
- Harmonic Group: {details.get('harmonic_group', 'Unknown')}
- Stress Line: Goes to Type {details.get('stress_line_to', '?')}
- Growth Line: Goes to Type {details.get('growth_line_to', '?')}
"""
        
        # Build system prompt
        system_prompt = """You are the Enneagram lens in Project Mirror. Your role is to answer questions about the Enneagram system with depth and nuance.

RULES:
1. Use ONLY the provided Book Context to answer questions. Do not make up information.
2. If the context is insufficient, say "I don't have enough information in my sources to fully answer that."
3. Be reflective and exploratory, not prescriptive or diagnostic.
4. Reference specific concepts from the Enneagram tradition when relevant.
5. If the user has Enneagram context provided, tailor your answer to their type when appropriate.
6. Keep answers focused and concise (2-4 paragraphs max).
7. Never claim certainty about someone's type - use language like "those who resonate with Type X often..."

BOOK CONTEXT:
{chunks}

{user_ctx}
""".format(chunks=chunk_context if chunk_context else "(No relevant passages found)", user_ctx=user_context)
        
        # Call LLM if available
        if llm_func:
            try:
                answer_text = await llm_func(system_prompt, query)
            except Exception as e:
                logger.error(f"[EnneagramKB] LLM error: {e}")
                answer_text = "I encountered an issue generating a response. Please try again."
        else:
            # Fallback if no LLM provided
            if retrieved:
                answer_text = f"Based on the Enneagram sources, here's relevant context about your question:\n\n{retrieved[0].chunk.text[:500]}..."
            else:
                answer_text = "I couldn't find relevant information in the knowledge base for your question."
        
        return AnswerResult(
            answer_text=answer_text,
            citations=citations,
            used_chunks=used_chunks
        )


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

# Global knowledge base instance (initialized at server startup)
_kb_instance: Optional[EnneagramKnowledgeBase] = None


def get_knowledge_base() -> EnneagramKnowledgeBase:
    """Get the singleton knowledge base instance."""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = EnneagramKnowledgeBase()
    return _kb_instance


def initialize_knowledge_base(pdf_path: Optional[str] = None) -> bool:
    """
    Initialize the knowledge base at server startup.
    
    Args:
        pdf_path: Optional path to the PDF file
        
    Returns:
        True if initialization successful, False otherwise
    """
    global _kb_instance
    
    if pdf_path:
        _kb_instance = EnneagramKnowledgeBase(pdf_path)
    else:
        _kb_instance = EnneagramKnowledgeBase()
    
    return _kb_instance.initialize()


def is_knowledge_base_ready() -> bool:
    """Check if knowledge base is ready for queries."""
    return _kb_instance is not None and _kb_instance.is_ready


def get_kb_status() -> Dict[str, Any]:
    """Get knowledge base status for debugging."""
    if _kb_instance is None:
        return {"status": "not_initialized", "ready": False}
    
    return {
        "status": "ready" if _kb_instance.is_ready else "error",
        "ready": _kb_instance.is_ready,
        "chunks_count": len(_kb_instance.chunks),
        "error": _kb_instance.load_error,
        "pdf_path": _kb_instance.pdf_path
    }
