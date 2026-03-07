"""
=============================================================================
PROJECT MIRROR - TRUE SIDEREAL-M HUMAN DESIGN COMPUTATION AUDIT
=============================================================================
Date: 2026-02-09
Auditor: AI Agent
Calibration Target: Genetic Matrix Compatible

Benchmark Settings:
- Swiss Ephemeris user-defined sidereal mode
- J2000 epoch = 2451545.0
- Sidereal Vernal Point (SVP) = 31.2836
- Reference year = 2000
- Yearly Incremental SVP = 0.00
- Use Swiss Ephemeris files, not fallback analytic models
- Use sidereal calculations with topocentric precision where applicable
=============================================================================
"""

# =============================================================================
# TASK 1: AUDIT - FILES AND FUNCTIONS
# =============================================================================

AUDIT_FINDINGS = {
    "files_analyzed": [
        "/app/backend/calculations/astrology.py",
        "/app/backend/calculations/human_design.py",
        "/app/backend/calculations/symbolic_compute_contract.py",
    ],
    
    "1_swiss_ephemeris_initialization": {
        "file": "/app/backend/calculations/astrology.py",
        "line": 43,
        "code": "swe.set_ephe_path(None)",
        "what_it_does": "Sets ephemeris path to None, which tells Swiss Ephemeris to use built-in Moshier analytical ephemeris instead of Swiss Ephemeris files",
        "issue": "CRITICAL - Using Moshier fallback instead of Swiss Ephemeris files (SE files not loaded)",
        "uses_SEFLG_SWIEPH": False,  # Not explicitly set
        "uses_SE_files": False,  # Uses Moshier fallback
    },
    
    "2_sidereal_mode_setup": {
        "file": "/app/backend/calculations/astrology.py",
        "functions": ["tropical_to_sidereal()", "calculate_planet_position_sidereal()"],
        "what_it_does": "Manual subtraction: sidereal = tropical - SVP. Does NOT use Swiss Ephemeris sidereal mode (SE_SIDM_USER)",
        "uses_SE_SIDM_USER": False,
        "uses_SEFLG_SIDEREAL": False,
        "issue": "NOT using Swiss Ephemeris built-in sidereal mode. Using manual subtraction instead.",
        "code_sample": """
# Line 89-103 in astrology.py
def tropical_to_sidereal(tropical_longitude: float, svp_degrees: float) -> float:
    sidereal = tropical_longitude - svp_degrees
    return normalize_degrees(sidereal)
        """
    },
    
    "3_ayanamsa_svp_settings": {
        "file": "/app/backend/calculations/astrology.py",
        "location": "get_full_natal_chart() defaults, line 379-384",
        "default_svp": 31.2836,
        "default_reference_year": 2000,
        "default_yearly_increment": 0.0,
        "uses_epoch_2451545": "NOT EXPLICITLY - J2000 epoch not referenced",
        "what_it_does": "Uses fixed SVP=31.2836 with no precession. SVP is subtracted from tropical to get sidereal.",
        "issue": "SVP value matches benchmark but implementation is manual, not using SE ayanamsa system",
        "code_sample": """
# Line 379-384 in astrology.py
final_settings = {
    "mode": sidereal_settings.get("mode", "true_sidereal_user_defined"),
    "svp_degrees": sidereal_settings.get("svp_degrees", 31.2836),
    "reference_year": sidereal_settings.get("reference_year", 2000),
    "yearly_increment": sidereal_settings.get("yearly_increment", 0.0)
}
        """
    },
    
    "4_thirteen_sign_constellation_output": {
        "file": "/app/backend/calculations/astrology.py",
        "function": "longitude_to_sign_degree()",
        "what_it_does": "Uses standard 12-sign zodiac (30° per sign). Ophiuchus is NOT implemented.",
        "thirteen_sign_implemented": False,
        "ophiuchus_in_logic": False,
        "ophiuchus_in_ui_only": "Unknown - would need frontend audit",
        "issue": "NO 13-sign constellation support. Uses traditional 12-sign 30° division.",
        "code_sample": """
# Line 61-65 in astrology.py
ZODIAC_SIGNS = [
    'Aries', 'Taurus', 'Gemini', 'Cancer',
    'Leo', 'Virgo', 'Libra', 'Scorpio',
    'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]
        """
    },
    
    "5_human_design_gate_mapping": {
        "file": "/app/backend/calculations/human_design.py",
        "function": "longitude_to_gate()",
        "line_range": "239-295",
        "what_it_does": "Maps sidereal longitude to I-Ching gate using HD_GATE_WHEEL lookup table with specific degree boundaries",
        "input_type": "Sidereal longitude (from manual tropical - SVP)",
        "mapping_basis": "Raw sidereal longitude mapped to HD Rave Mandala wheel positions",
        "issue": "Gate mapping uses sidereal longitude. If sidereal calculation is wrong, gates will be wrong.",
        "gate_wheel_source": "HD_GATE_WHEEL constant with 64 gates mapped to zodiac degree ranges",
    },
    
    "6_human_design_line_mapping": {
        "file": "/app/backend/calculations/human_design.py",
        "function": "longitude_to_gate()",
        "line_range": "283-289",
        "what_it_does": "Divides each gate into 6 equal parts. Line = position within gate / 6",
        "calculation": "line = int((pos_in_gate / gate_size) * 6) + 1",
        "issue": "Lines are evenly distributed within gates. Some HD systems use unequal line divisions.",
    },
    
    "7_design_date_calculation": {
        "file": "/app/backend/calculations/human_design.py",
        "function": "calculate_design_date()",
        "line_range": "297-381",
        "what_it_does": "Binary search to find moment when Sun was 88° before birth Sun position",
        "algorithm": """
1. Get birth Sun sidereal position
2. Target = birth_sun - 88° (normalized)
3. Binary search in 70-110 day window before birth
4. Find timestamp where Sun is within 0.01° of target
        """,
        "uses_solar_arc": False,  # Uses actual Sun position, not arc
        "issue": "Design date calculation looks correct algorithmically, but depends on correct sidereal Sun position",
    },
    
    "8_profile_derivation": {
        "file": "/app/backend/calculations/human_design.py",
        "function": "calculate_profile()",
        "line_range": "741-754",
        "what_it_does": "Profile = personality_sun_line / design_sun_line",
        "formula": "return f'{personality_sun_line}/{design_sun_line}'",
        "issue": "Profile derivation is correct. Just uses Sun lines from both charts.",
    },
    
    "9_type_authority_channel_center_logic": {
        "file": "/app/backend/calculations/human_design.py",
        "functions": {
            "type": "determine_type() - lines 612-652",
            "authority": "determine_authority() - lines 705-738",
            "channels": "get_defined_channels() - lines 549-566",
            "centers": "get_defined_centers() - lines 569-586",
            "definition": "determine_definition() - lines 655-702",
        },
        "type_logic": """
1. Reflector: NO defined centers
2. Generator: Sacral defined AND no motor-to-throat
3. Manifesting Generator: Sacral defined AND motor-to-throat
4. Manifestor: motor-to-throat AND Sacral undefined
5. Projector: everything else
        """,
        "authority_hierarchy": "Emotional > Sacral > Splenic > Ego > G > Mental/Environment",
        "channel_logic": "Channel defined if BOTH gates present in combined personality+design gates",
        "center_logic": "Center defined if it has at least one FULL channel connected",
        "issue": "Logic appears correct for standard HD. Depends on correct gate calculations upstream.",
    },
}

# =============================================================================
# TASK 2: DETAILED ANALYSIS OF EACH FUNCTION
# =============================================================================

DETAILED_ANALYSIS = {
    "swiss_ephemeris_flags_used": {
        "SEFLG_SWIEPH": {
            "used": False,
            "explanation": "Not explicitly set. swe.calc_ut() called with flags=0, which defaults to Moshier"
        },
        "SEFLG_SIDEREAL": {
            "used": False,
            "explanation": "Never used. Sidereal conversion is done manually via tropical - SVP"
        },
        "SEFLG_TOPOCTR": {
            "used": False,
            "explanation": "Not used. All calculations are geocentric, not topocentric"
        },
        "SE_SIDM_USER": {
            "used": False,
            "explanation": "Not used. Should be used with swe.set_sid_mode() for proper sidereal setup"
        },
        "epoch_2451545": {
            "used": False,
            "explanation": "J2000 epoch not explicitly referenced. SVP value 31.2836 is used directly without epoch context"
        },
    },
    
    "planet_calculation_flow": """
1. swe.calc_ut(jd, planet_id, 0)  <- flags=0, no sidereal flag
   Returns: tropical longitude
   
2. tropical_to_sidereal(tropical, svp_degrees)
   Returns: tropical - 31.2836 = sidereal
   
3. longitude_to_gate(sidereal)
   Returns: HD gate and line
    """,
    
    "13_sign_analysis": {
        "zodiac_signs_count": 12,
        "ophiuchus_present": False,
        "constellation_boundaries": "Fixed 30° per sign, not IAU constellation boundaries",
        "issue": "Traditional 12-sign system. 13-sign would require different boundaries."
    },
    
    "hd_mapping_input": {
        "input_type": "Sidereal longitude from manual calculation",
        "transformation": "None - direct sidereal longitude to gate mapping",
        "gate_wheel_reference": "HD_GATE_WHEEL constant with I-Ching sequence"
    },
}

# =============================================================================
# TASK 3: DEBUG OUTPUT TEMPLATE
# =============================================================================

DEBUG_OUTPUT_TEMPLATE = """
To generate debug output for a single chart, run:

from datetime import datetime, timezone
from backend.calculations.astrology import get_full_natal_chart
from backend.calculations.human_design import get_human_design_chart, longitude_to_gate

# Example: Birth data
birth_utc = datetime(YYYY, MM, DD, HH, MM, SS, tzinfo=timezone.utc)
lat = XX.XXXX
lon = XX.XXXX

# Get both charts
astro_chart = get_full_natal_chart(birth_utc, lat, lon)
hd_chart = get_human_design_chart(birth_utc, lat, lon)

# Debug output will include:
# - birth_local_datetime (input)
# - birth_utc
# - design_utc (from hd_chart['design_datetime_utc_iso'])
# - For each planet:
#   - tropical_longitude (from astro_chart['planets'][planet]['tropical_longitude'])
#   - sidereal_longitude (from astro_chart['planets'][planet]['longitude'])
#   - sign (12-sign, not 13-sign)
#   - hd_gate (from longitude_to_gate())
#   - hd_line
# - Profile (from hd_chart['profile'])
# - Type (from hd_chart['type'])
# - Authority (from hd_chart['authority'])
# - Definition (from hd_chart['definition'])
# - Active channels (from hd_chart['defined_channels'])
# - Defined centers (from hd_chart['defined_centers'])
"""

# =============================================================================
# TASK 4: DISCREPANCIES FROM GENETIC MATRIX BENCHMARK
# =============================================================================

DISCREPANCIES = [
    {
        "id": "D1",
        "severity": "CRITICAL",
        "area": "Swiss Ephemeris Files",
        "benchmark": "Use Swiss Ephemeris files (SEFLG_SWIEPH)",
        "current": "Uses Moshier analytical ephemeris (fallback) via swe.set_ephe_path(None)",
        "impact": "Moshier is less accurate than Swiss Ephemeris files, especially for outer planets and historical dates",
        "fix": "Download and configure SE files, add SEFLG_SWIEPH to calc_ut() calls"
    },
    {
        "id": "D2", 
        "severity": "HIGH",
        "area": "Sidereal Mode Setup",
        "benchmark": "Use SE_SIDM_USER with swe.set_sid_mode()",
        "current": "Manual subtraction: sidereal = tropical - SVP",
        "impact": "Manual calculation may not account for all SE precision features",
        "fix": "Use swe.set_sid_mode(SE_SIDM_USER, t0, ayan_t0) before calculations"
    },
    {
        "id": "D3",
        "severity": "HIGH", 
        "area": "SEFLG_SIDEREAL Flag",
        "benchmark": "Use SEFLG_SIDEREAL in calc_ut() for native sidereal positions",
        "current": "Tropical calculation with manual sidereal conversion",
        "impact": "Bypasses SE's built-in sidereal handling which may be more accurate",
        "fix": "Add swe.FLG_SIDEREAL to calc_ut() flags after setting sid_mode"
    },
    {
        "id": "D4",
        "severity": "MEDIUM",
        "area": "J2000 Epoch",
        "benchmark": "Reference epoch 2451545.0 (J2000)",
        "current": "No explicit epoch reference. SVP 31.2836 used as fixed constant",
        "impact": "SVP value is for year 2000 but not tied to J2000 JD epoch explicitly",
        "fix": "Use swe.set_sid_mode() with t0=2451545.0 (J2000)"
    },
    {
        "id": "D5",
        "severity": "LOW",
        "area": "Topocentric Precision",
        "benchmark": "SEFLG_TOPOCTR for topocentric positions where applicable",
        "current": "All positions are geocentric",
        "impact": "Minor position differences (up to ~0.003° for Moon) for location-specific charts",
        "fix": "Add SEFLG_TOPOCTR and swe.set_topo() for Moon and angles if needed"
    },
    {
        "id": "D6",
        "severity": "INFO",
        "area": "13-Sign Constellation Output",
        "benchmark": "Not explicitly required by Genetic Matrix",
        "current": "Uses 12-sign zodiac only",
        "impact": "No 13-sign support. Ophiuchus not in logic or output",
        "fix": "Not required unless explicitly requested"
    },
]

# =============================================================================
# TASK 5: OUTPUT SUMMARY
# =============================================================================

AUDIT_SUMMARY = """
=============================================================================
A. AUDIT FINDINGS
=============================================================================

1. SWISS EPHEMERIS INITIALIZATION
   - File: /app/backend/calculations/astrology.py, line 43
   - Status: ⚠️ ISSUE - Using Moshier fallback, not SE files
   - swe.set_ephe_path(None) tells SE to use built-in Moshier

2. SIDEREAL MODE SETUP
   - Status: ⚠️ ISSUE - Manual calculation, not using SE sidereal mode
   - Current: tropical - SVP = sidereal
   - Should use: swe.set_sid_mode(SE_SIDM_USER, t0, ayan_t0)

3. AYANAMSA / SVP SETTINGS
   - SVP = 31.2836° ✓ MATCHES benchmark
   - Reference year = 2000 ✓ MATCHES benchmark  
   - Yearly increment = 0.0 ✓ MATCHES benchmark
   - Issue: Not using SE's ayanamsa system

4. 13-SIGN OUTPUT
   - Status: ❌ NOT IMPLEMENTED
   - Uses standard 12-sign zodiac (30° per sign)
   - Ophiuchus is not in code

5. HD GATE MAPPING
   - Status: ✓ CORRECT (if sidereal input is correct)
   - Uses HD_GATE_WHEEL with I-Ching sequence
   - Maps raw sidereal longitude to gates

6. HD LINE MAPPING
   - Status: ✓ CORRECT
   - 6 equal divisions per gate

7. DESIGN DATE CALCULATION
   - Status: ✓ CORRECT algorithm
   - Binary search for Sun at birth_sun - 88°

8. PROFILE DERIVATION
   - Status: ✓ CORRECT
   - personality_sun_line / design_sun_line

9. TYPE/AUTHORITY/CHANNEL/CENTER
   - Status: ✓ CORRECT logic
   - Standard HD determination rules

=============================================================================
B. DISCREPANCIES FROM GENETIC MATRIX BENCHMARK
=============================================================================

| ID | Severity | Issue | Fix Required |
|----|----------|-------|--------------|
| D1 | CRITICAL | Using Moshier, not SE files | Load SE ephemeris files |
| D2 | HIGH | Manual sidereal calc | Use SE_SIDM_USER |
| D3 | HIGH | No SEFLG_SIDEREAL | Add flag to calc_ut() |
| D4 | MEDIUM | No J2000 epoch ref | Use t0=2451545.0 |
| D5 | LOW | No topocentric | Add SEFLG_TOPOCTR |
| D6 | INFO | No 13-sign | Not required |

=============================================================================
C. MINIMAL FIX PLAN
=============================================================================

Phase 1 - Critical (Must Fix):
1. Download Swiss Ephemeris files to /app/backend/ephe/
2. Update swe.set_ephe_path('/app/backend/ephe')
3. Add SEFLG_SWIEPH to all swe.calc_ut() calls

Phase 2 - High Priority:
4. Implement proper sidereal setup:
   swe.set_sid_mode(swe.SIDM_USER, 2451545.0, 31.2836)
5. Add SEFLG_SIDEREAL to calc_ut() flags
6. Remove manual tropical_to_sidereal() calls
7. Update all position calculations to use native sidereal

Phase 3 - Optional:
8. Add SEFLG_TOPOCTR for Moon/angles if needed
9. Implement 13-sign if explicitly requested

=============================================================================
D. BLOCKERS / AMBIGUITIES REQUIRING DECISION
=============================================================================

1. EPHEMERIS FILES
   Q: Where should SE files be stored and are they included in deployment?
   Options: 
   a) Bundle with app (adds ~50MB)
   b) Download at runtime
   c) Accept Moshier precision (not recommended for production)

2. 13-SIGN ZODIAC
   Q: Is 13-sign constellation output actually required?
   Current status: NOT implemented
   Impact: Would require significant changes to sign logic

3. TOPOCENTRIC PRECISION
   Q: Is topocentric positioning required for any calculations?
   Current: All geocentric
   Impact: Minor for most planets, more significant for Moon

4. REGRESSION TESTING
   Q: What test cases should be used to verify changes?
   Recommendation: Use known Genetic Matrix outputs for comparison

5. VERSION BUMP
   Q: Current computation_version is 'mirror-deterministic-v1'
   Changes will require new version and migration plan

=============================================================================
"""

if __name__ == "__main__":
    print(AUDIT_SUMMARY)
