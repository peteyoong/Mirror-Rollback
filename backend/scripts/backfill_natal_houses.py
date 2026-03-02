"""
Natal House Backfill Script - Project Mirror Phase 5
=====================================================
Backfills natal house data for existing charts that have birth datetime + location
but are missing house placements.

Usage:
    python scripts/backfill_natal_houses.py [--dry-run] [--user-id USER_ID]

Options:
    --dry-run       Preview changes without writing to database
    --user-id       Process only a specific user_id
"""

import asyncio
import argparse
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import swisseph as swe

load_dotenv()

# Import from existing astrology module
from calculations.astrology import (
    tropical_to_sidereal,
    DEFAULT_SVP_DEGREES,
)

# Set ephemeris path
swe.set_ephe_path(None)


def normalize_degrees(degrees: float) -> float:
    """Normalize degrees to 0-360 range"""
    degrees = degrees % 360
    if degrees < 0:
        degrees += 360
    return degrees


def calculate_equal_house_cusps(asc_longitude: float) -> list:
    """Calculate 12 equal house cusps from Ascendant longitude
    
    Equal House System: Each house is exactly 30° wide.
    House 1 cusp = Ascendant
    House N cusp = Ascendant + ((N-1) * 30°)
    """
    cusps = []
    for i in range(12):
        cusp = normalize_degrees(asc_longitude + (i * 30))
        cusps.append(cusp)
    return cusps


def get_house_for_longitude(longitude: float, house_cusps: list) -> int:
    """Determine which house a longitude falls in (1-12)"""
    longitude = normalize_degrees(longitude)
    
    for i in range(12):
        cusp_current = house_cusps[i]
        cusp_next = house_cusps[(i + 1) % 12]
        
        # Handle wrap around 0° Aries
        if cusp_next < cusp_current:
            if longitude >= cusp_current or longitude < cusp_next:
                return i + 1
        else:
            if cusp_current <= longitude < cusp_next:
                return i + 1
    
    return 1  # Fallback


def compute_natal_houses_for_chart(chart_data: dict) -> dict:
    """
    Compute natal house data for a chart.
    
    Returns dict with:
    - houses_enabled: bool
    - houses_reason: str (if disabled)
    - angles: dict with asc/mc/dc/ic longitudes
    - house_cusps: list of 12 cusp longitudes
    - planet_house_positions: dict mapping planet name -> house number
    """
    astrology = chart_data.get('astrology', {})
    
    # Check if we have the required data
    input_dt = astrology.get('input_datetime_utc')
    coords = astrology.get('coordinates', {})
    
    if not input_dt or not coords.get('lat') or not coords.get('lon'):
        return {
            'houses_enabled': False,
            'houses_reason': 'missing_birth_data',
        }
    
    # Check if houses already exist and are valid
    existing_angles = astrology.get('angles', {})
    existing_houses = astrology.get('houses', {})
    planets = astrology.get('planets', {})
    
    # If angles exist with longitude, we can derive houses
    asc_data = existing_angles.get('asc', {})
    asc_longitude = asc_data.get('longitude')
    
    if asc_longitude is None:
        return {
            'houses_enabled': False,
            'houses_reason': 'no_ascendant_computed',
        }
    
    # Calculate equal house cusps
    house_cusps = calculate_equal_house_cusps(asc_longitude)
    
    # Get other angles
    mc_longitude = existing_angles.get('mc', {}).get('longitude')
    dc_longitude = existing_angles.get('dc', {}).get('longitude')
    ic_longitude = existing_angles.get('ic', {}).get('longitude')
    
    # Calculate house for each planet
    planet_house_positions = {}
    for planet_name, planet_data in planets.items():
        planet_long = planet_data.get('longitude')
        if planet_long is not None:
            house = get_house_for_longitude(planet_long, house_cusps)
            planet_house_positions[planet_name] = house
    
    return {
        'houses_enabled': True,
        'angles': {
            'ascendant_longitude': asc_longitude,
            'mc_longitude': mc_longitude,
            'dc_longitude': dc_longitude,
            'ic_longitude': ic_longitude,
        },
        'house_cusps': {
            'system': 'Equal',
            'cusps': house_cusps,
        },
        'planet_house_positions': planet_house_positions,
    }


async def backfill_chart(db, chart: dict, dry_run: bool = False) -> dict:
    """
    Backfill house data for a single chart.
    
    Returns status dict with:
    - user_id
    - status: 'updated', 'skipped', 'error'
    - reason
    """
    user_id = chart.get('user_id')
    astrology = chart.get('astrology', {})
    planets = astrology.get('planets', {})
    
    # Check if houses already exist
    first_planet = list(planets.values())[0] if planets else {}
    if first_planet.get('house') is not None:
        return {
            'user_id': user_id,
            'status': 'skipped',
            'reason': 'houses_already_exist',
        }
    
    # Compute house data
    house_data = compute_natal_houses_for_chart(chart)
    
    if not house_data.get('houses_enabled'):
        return {
            'user_id': user_id,
            'status': 'skipped',
            'reason': house_data.get('houses_reason', 'unknown'),
        }
    
    # Build update
    planet_updates = {}
    for planet_name, house in house_data['planet_house_positions'].items():
        planet_updates[f'astrology.planets.{planet_name}.house'] = house
    
    update_doc = {
        '$set': {
            'astrology.natal_houses_enabled': True,
            'astrology.houses.system': 'Equal',
            'astrology.houses.cusps': house_data['house_cusps']['cusps'],
            **planet_updates,
        }
    }
    
    if dry_run:
        print(f"  [DRY RUN] Would update chart for user {user_id}")
        print(f"    House cusps: {house_data['house_cusps']['cusps'][:3]}...")
        print(f"    Planet houses: {list(house_data['planet_house_positions'].items())[:3]}...")
        return {
            'user_id': user_id,
            'status': 'would_update',
            'planet_houses': house_data['planet_house_positions'],
        }
    
    # Apply update
    result = await db.charts.update_one(
        {'user_id': user_id},
        update_doc
    )
    
    if result.modified_count > 0:
        return {
            'user_id': user_id,
            'status': 'updated',
            'planet_houses': house_data['planet_house_positions'],
        }
    else:
        return {
            'user_id': user_id,
            'status': 'no_change',
            'reason': 'update_did_not_modify',
        }


async def main(dry_run: bool = False, user_id: str = None):
    """Main backfill function"""
    
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME')
    
    if not mongo_url or not db_name:
        print("ERROR: MONGO_URL and DB_NAME must be set")
        return
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("=" * 60)
    print("Natal House Backfill Script")
    print("=" * 60)
    print(f"Database: {db_name}")
    print(f"Dry run: {dry_run}")
    if user_id:
        print(f"Single user: {user_id}")
    print()
    
    # Build query
    query = {}
    if user_id:
        query['user_id'] = user_id
    
    # Count charts
    total_count = await db.charts.count_documents(query)
    print(f"Total charts to process: {total_count}")
    print()
    
    # Process charts
    stats = {
        'updated': 0,
        'would_update': 0,
        'skipped': 0,
        'error': 0,
    }
    
    async for chart in db.charts.find(query):
        try:
            result = await backfill_chart(db, chart, dry_run)
            status = result.get('status', 'unknown')
            
            if status in stats:
                stats[status] += 1
            
            if status in ['updated', 'would_update']:
                print(f"✓ {result['user_id']}: {status}")
                if result.get('planet_houses'):
                    sample = list(result['planet_houses'].items())[:3]
                    print(f"    Houses: {sample}")
            elif status == 'skipped':
                print(f"- {result['user_id']}: skipped ({result.get('reason')})")
            
        except Exception as e:
            print(f"✗ Error processing chart: {e}")
            stats['error'] += 1
    
    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for status, count in stats.items():
        print(f"  {status}: {count}")
    print()
    
    if dry_run:
        print("This was a DRY RUN. No changes were made.")
        print("Run without --dry-run to apply changes.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backfill natal house data')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing')
    parser.add_argument('--user-id', type=str, help='Process single user')
    
    args = parser.parse_args()
    
    asyncio.run(main(dry_run=args.dry_run, user_id=args.user_id))
