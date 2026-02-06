"""
===============================================================================
SYMBOLIC COMPUTE CONTRACT — Global Interface for All Symbolic Systems
===============================================================================
Project Mirror's unified compute integrity interface.

This module enforces:
- Deterministic completeness
- Predictable LLM handoff
- Identical failure behavior
- Zero "missing data" hallucinations

CORE PRINCIPLE:
    Interpretation is optional.
    Computation is not.
    Integrity is non-negotiable.

Every symbolic system (Astrology, Human Design, Numerology, and future systems
such as Gene Keys) must return a payload conforming to this contract.

===============================================================================
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, TypeVar, Generic
import hashlib
import json


# =============================================================================
# COMPUTE INTEGRITY ERROR (Shared Exception)
# =============================================================================

class ComputeIntegrityError(Exception):
    """Raised when a symbolic system's compute contract validation fails.
    
    This exception contains structured error information that can be
    serialized to JSON for API responses.
    
    Usage:
        raise ComputeIntegrityError(["Nodes: north missing sign", "Planets: Sun missing"])
    """
    
    def __init__(self, errors: List[str], partial_data: Optional[Dict] = None, system: str = "unknown"):
        self.errors = errors
        self.partial_data = partial_data
        self.system = system
        super().__init__(f"[{system}] Compute Integrity Error: {'; '.join(errors)}")
    
    def to_dict(self) -> Dict:
        """Return standardized compute integrity error object."""
        return {
            "system": self.system,
            "compute_integrity": {
                "valid": False,
                "errors": self.errors,
                "error_count": len(self.errors),
                "message": f"{self.system.title()} computation failed integrity checks. Do not interpret partial data."
            },
            "partial_data": self.partial_data
        }
    
    def to_api_response(self) -> Dict:
        """Return API-friendly error response."""
        return {
            "success": False,
            "error": "compute_integrity_error",
            "title": "Compute Integrity Error",
            "system": self.system,
            "missing": self.errors,
            "action": f"{self.system.title()} deep dive paused until compute payload is complete.",
            "sections": [],
            "mirror_prompt": None,
            "partial_data": self.partial_data
        }


# =============================================================================
# COMPUTE INTEGRITY RESULT (Shared Validation Result)
# =============================================================================

@dataclass
class ComputeIntegrityResult:
    """Result of compute integrity validation."""
    valid: bool
    missing: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "valid": self.valid,
            "missing": self.missing,
            "warnings": self.warnings,
            "error_count": len(self.missing)
        }


# =============================================================================
# SYMBOLIC PAYLOAD WRAPPER (Canonical Payload Structure)
# =============================================================================

@dataclass
class SymbolicPayload:
    """Canonical payload structure for all symbolic systems.
    
    Every symbolic system must wrap its output in this structure.
    
    Example:
        payload = SymbolicPayload(
            system="astrology",
            canonical_payload=chart_data,
            inputs={"birth_date": "1968-04-01", "lat": 3.1073, "lon": 101.6070}
        )
    """
    system: str
    canonical_payload: Dict[str, Any]
    inputs: Dict[str, Any] = field(default_factory=dict)
    compute_integrity: ComputeIntegrityResult = field(default_factory=lambda: ComputeIntegrityResult(valid=True))
    version: str = "v1"
    compute_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __post_init__(self):
        """Generate inputs hash after initialization."""
        self._inputs_hash = self._generate_inputs_hash()
    
    def _generate_inputs_hash(self) -> str:
        """Generate deterministic hash of inputs for caching/comparison."""
        inputs_str = json.dumps(self.inputs, sort_keys=True, default=str)
        return hashlib.md5(inputs_str.encode()).hexdigest()[:12]
    
    @property
    def inputs_hash(self) -> str:
        return self._inputs_hash
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "system": self.system,
            "canonical_payload": self.canonical_payload,
            "metadata": {
                "version": self.version,
                "compute_timestamp": self.compute_timestamp,
                "inputs_hash": self.inputs_hash
            },
            "compute_integrity": self.compute_integrity.to_dict()
        }
    
    def is_valid(self) -> bool:
        """Check if payload passed integrity validation."""
        return self.compute_integrity.valid
    
    def assert_valid(self):
        """Assert payload is valid, raise ComputeIntegrityError if not."""
        if not self.is_valid():
            raise ComputeIntegrityError(
                errors=self.compute_integrity.missing,
                system=self.system
            )


# =============================================================================
# SYMBOLIC COMPUTE CONTRACT (Abstract Base Class)
# =============================================================================

T = TypeVar('T', bound=Dict[str, Any])

class SymbolicComputeContract(ABC, Generic[T]):
    """Abstract base class for all symbolic system compute contracts.
    
    Every symbolic system (Astrology, Human Design, Numerology, Gene Keys, etc.)
    must implement this contract.
    
    Required implementations:
        - system_name: The canonical name of the system
        - required_keys: List of keys that MUST be present in the payload
        - compute(): The main computation function
        - validate(): Validation of the computed payload
    
    Example implementation:
        class AstrologyContract(SymbolicComputeContract):
            system_name = "astrology"
            required_keys = ["planets", "nodes", "angles", "houses", "aspects", "sect"]
            
            def compute(self, birth_datetime, lat, lon, **kwargs) -> SymbolicPayload:
                # ... implementation
                
            def validate(self, payload: Dict) -> ComputeIntegrityResult:
                # ... implementation
    """
    
    @property
    @abstractmethod
    def system_name(self) -> str:
        """Canonical name of this symbolic system (e.g., 'astrology')."""
        pass
    
    @property
    @abstractmethod
    def required_keys(self) -> List[str]:
        """List of keys that MUST be present in the canonical payload."""
        pass
    
    @abstractmethod
    def compute(self, **kwargs) -> SymbolicPayload:
        """Compute the symbolic system payload.
        
        Must return a SymbolicPayload with compute_integrity set.
        Must NOT return partial payloads.
        
        Raises:
            ComputeIntegrityError: If computation fails integrity checks
        """
        pass
    
    @abstractmethod
    def validate(self, payload: Dict[str, Any]) -> ComputeIntegrityResult:
        """Validate a computed payload against required keys.
        
        Args:
            payload: The canonical payload to validate
            
        Returns:
            ComputeIntegrityResult with valid=True if all checks pass
        """
        pass
    
    def validate_required_keys(self, payload: Dict[str, Any]) -> List[str]:
        """Check that all required keys exist in the payload.
        
        Returns list of missing keys (empty if all present).
        """
        missing = []
        for key in self.required_keys:
            if key not in payload:
                missing.append(f"{self.system_name}: {key} missing")
            elif payload[key] is None:
                # Key exists but is None - might be OK for some systems
                # Override validate() for system-specific rules
                pass
        return missing
    
    def wrap_payload(
        self,
        canonical_payload: Dict[str, Any],
        inputs: Dict[str, Any],
        integrity_result: Optional[ComputeIntegrityResult] = None
    ) -> SymbolicPayload:
        """Wrap a raw payload in the SymbolicPayload structure.
        
        Automatically validates if integrity_result not provided.
        """
        if integrity_result is None:
            integrity_result = self.validate(canonical_payload)
        
        return SymbolicPayload(
            system=self.system_name,
            canonical_payload=canonical_payload,
            inputs=inputs,
            compute_integrity=integrity_result
        )


# =============================================================================
# LLM HANDOFF VALIDATION
# =============================================================================

def assert_handoff_ready(payload: SymbolicPayload) -> bool:
    """Assert that a payload is ready for LLM handoff.
    
    GLOBAL LLM HANDOFF RULE:
    Before invoking any LLM:
    - Assert compute_integrity.valid == true
    - Inject canonical_payload verbatim (no summarization)
    - If assertion fails: Return compute_integrity_error, do not interpret
    
    Args:
        payload: The SymbolicPayload to check
        
    Returns:
        True if ready for handoff
        
    Raises:
        ComputeIntegrityError: If payload is not valid
    """
    if not payload.is_valid():
        raise ComputeIntegrityError(
            errors=payload.compute_integrity.missing,
            system=payload.system,
            partial_data={"canonical_payload_keys": list(payload.canonical_payload.keys())}
        )
    return True


def validate_handoff(payload_dict: Dict[str, Any], system: str) -> bool:
    """Validate a raw dictionary payload for LLM handoff.
    
    Use this when you have a dict instead of a SymbolicPayload object.
    
    Args:
        payload_dict: Raw payload dictionary
        system: System name for error context
        
    Returns:
        True if valid
        
    Raises:
        ComputeIntegrityError: If payload is not valid
    """
    compute_integrity = payload_dict.get("compute_integrity", {})
    
    if not compute_integrity.get("valid", False):
        raise ComputeIntegrityError(
            errors=compute_integrity.get("missing", ["Unknown validation failure"]),
            system=system
        )
    
    return True


# =============================================================================
# SYSTEM REGISTRY (For Future Systems)
# =============================================================================

class SymbolicSystemRegistry:
    """Registry of all symbolic systems implementing the compute contract.
    
    New systems must register here to ensure they meet the contract requirements.
    """
    
    _systems: Dict[str, 'SymbolicComputeContract'] = {}
    
    @classmethod
    def register(cls, contract: 'SymbolicComputeContract') -> None:
        """Register a symbolic system contract."""
        cls._systems[contract.system_name] = contract
    
    @classmethod
    def get(cls, system_name: str) -> Optional['SymbolicComputeContract']:
        """Get a registered contract by system name."""
        return cls._systems.get(system_name)
    
    @classmethod
    def list_systems(cls) -> List[str]:
        """List all registered system names."""
        return list(cls._systems.keys())
    
    @classmethod
    def validate_all(cls) -> Dict[str, bool]:
        """Validate all registered systems have required methods."""
        results = {}
        for name, contract in cls._systems.items():
            try:
                # Check required properties/methods exist
                assert hasattr(contract, 'system_name')
                assert hasattr(contract, 'required_keys')
                assert hasattr(contract, 'compute')
                assert hasattr(contract, 'validate')
                results[name] = True
            except AssertionError:
                results[name] = False
        return results


# =============================================================================
# REQUIRED KEYS BY SYSTEM (Reference)
# =============================================================================

# These are the required keys for each symbolic system.
# Systems must validate against these keys.

ASTROLOGY_REQUIRED_KEYS = [
    "metadata",
    "planets",
    "nodes",
    "angles",
    "houses",
    "aspects",
    "sect",
    "compute_integrity"
]

HUMAN_DESIGN_REQUIRED_KEYS = [
    "type",
    "strategy",
    "authority",
    "profile",
    "definition",
    "incarnation_cross",
    "defined_centers",
    "undefined_centers",
    "defined_channels",
    "active_gates",
    "compute_integrity"
]

NUMEROLOGY_REQUIRED_KEYS = [
    "core",  # Contains life_path, birthday_number, expression, soul_urge, personality
    "cycles",  # Contains personal_year, personal_month, personal_day
    "inputs",
    "compute_integrity"
]

# Future systems will add their required keys here
GENE_KEYS_REQUIRED_KEYS = [
    # To be defined when Gene Keys is implemented
    "profile_spheres",
    "activation_sequence",
    "venus_sequence",
    "pearl_sequence",
    "compute_integrity"
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_compute_integrity_error(
    errors: List[str],
    system: str,
    partial_data: Optional[Dict] = None
) -> Dict:
    """Return a standardized compute integrity error dict.
    
    Use this when you need to return an error dict instead of raising.
    """
    return {
        "system": system,
        "compute_integrity": {
            "valid": False,
            "errors": errors,
            "error_count": len(errors),
            "message": f"{system.title()} computation failed integrity checks."
        },
        "partial_data": partial_data
    }


def create_api_error_response(
    system: str,
    errors: List[str],
    partial_data: Optional[Dict] = None
) -> Dict:
    """Create a standardized API error response for compute integrity failures."""
    return {
        "success": False,
        "error": "compute_integrity_error",
        "title": "Compute Integrity Error",
        "system": system,
        "missing": errors,
        "action": f"{system.title()} deep dive paused until compute payload is complete.",
        "sections": [],
        "mirror_prompt": None,
        "partial_data": partial_data
    }


# =============================================================================
# FORBIDDEN BEHAVIOR ASSERTIONS
# =============================================================================

FORBIDDEN_PHRASES = [
    # Claims of missing data
    r"I don't have your",
    r"I can't see your",
    r"I don't have access to your",
    r"need your .* to calculate",
    r"aren't available",
    r"is not available",
    r"I don't have enough information",
    r"can't access your",
    r"without your",
    # Requests to re-enter data
    r"please provide your",
    r"please enter your",
    r"can you share your",
    r"I need you to",
]


def check_forbidden_language(text: str) -> List[str]:
    """Check if text contains forbidden language patterns.
    
    The assistant must NEVER:
    - Claim symbolic data is missing if keys exist
    - Ask user to re-enter data already computed
    - Guess or infer missing values
    - Interpret partial payloads
    
    Returns list of forbidden phrases found.
    """
    import re
    found = []
    for pattern in FORBIDDEN_PHRASES:
        if re.search(pattern, text, re.IGNORECASE):
            found.append(pattern)
    return found


# =============================================================================
# CONTRACT VERSION
# =============================================================================

CONTRACT_VERSION = "v1.0.0"
CONTRACT_LAST_UPDATED = "2026-02-06"


def get_contract_info() -> Dict:
    """Get contract version and metadata."""
    return {
        "version": CONTRACT_VERSION,
        "last_updated": CONTRACT_LAST_UPDATED,
        "registered_systems": SymbolicSystemRegistry.list_systems(),
        "required_keys": {
            "astrology": ASTROLOGY_REQUIRED_KEYS,
            "human_design": HUMAN_DESIGN_REQUIRED_KEYS,
            "numerology": NUMEROLOGY_REQUIRED_KEYS,
            "gene_keys": GENE_KEYS_REQUIRED_KEYS,
        }
    }
