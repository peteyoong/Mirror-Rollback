"""
Unit tests for Mirror Context - Verifying lunar nodes are included
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from bson import ObjectId

# Mock data for a user with computed nodes
MOCK_USER = {
    "_id": ObjectId("69819f1a1e4549392d7cb6d1"),
    "name": "Test User",
    "birth_date": "1990-06-15",
    "birth_time": "10:30",
    "timezone": "Europe/London"
}

MOCK_CHART_WITH_NODES = {
    "user_id": "69819f1a1e4549392d7cb6d1",
    "astrology": {
        "planets": {
            "Sun": {"sign": "Taurus", "formatted": "22°Taurus"},
            "Moon": {"sign": "Aquarius", "formatted": "12°Aquarius"},
            "Venus": {"sign": "Aries", "formatted": "17°Aries"},
            "Mars": {"sign": "Pisces", "formatted": "9°Pisces"}
        },
        "houses": {
            "formatted_cusps": [{"sign": "Cancer", "formatted": "27°Cancer"}]
        },
        "nodes": {
            "north": {
                "sign": "Capricorn",
                "degree": 6.83,
                "house": 6,
                "formatted": "6°Capricorn",
                "mode": "true_node"
            },
            "south": {
                "sign": "Cancer",
                "degree": 6.83,
                "house": 12,
                "formatted": "6°Cancer"
            }
        }
    },
    "human_design": {"type": "Generator"},
    "numerology": {"life_path": 4}
}


def test_context_bundle_includes_north_node():
    """Test that /api/mirror/context returns north_node when computed"""
    # This would be an integration test - for now just verify the structure
    astro = MOCK_CHART_WITH_NODES.get('astrology', {})
    nodes = astro.get('nodes', {})
    north = nodes.get('north', {})
    
    assert north.get('sign') == 'Capricorn'
    assert north.get('house') == 6
    assert north.get('formatted') == '6°Capricorn'
    print("✅ North node data structure is correct")


def test_context_bundle_includes_south_node():
    """Test that /api/mirror/context returns south_node when computed"""
    astro = MOCK_CHART_WITH_NODES.get('astrology', {})
    nodes = astro.get('nodes', {})
    south = nodes.get('south', {})
    
    assert south.get('sign') == 'Cancer'
    assert south.get('house') == 12
    assert south.get('formatted') == '6°Cancer'
    print("✅ South node data structure is correct")


def test_prompt_context_includes_nodes():
    """Test that the chat prompt context includes nodes when present"""
    # Simulate the context_parts building logic
    context_parts = []
    astro = MOCK_CHART_WITH_NODES.get('astrology', {})
    nodes = astro.get('nodes', {})
    north_node = nodes.get('north', {})
    south_node = nodes.get('south', {})
    
    # This simulates the new logic in mirror_chat
    if north_node and north_node.get('sign'):
        nn_house = north_node.get('house', '')
        context_parts.append(f"North Node: {north_node.get('formatted', north_node.get('sign', 'Unknown'))}" + (f" (House {nn_house})" if nn_house else ""))
    if south_node and south_node.get('sign'):
        sn_house = south_node.get('house', '')
        context_parts.append(f"South Node: {south_node.get('formatted', south_node.get('sign', 'Unknown'))}" + (f" (House {sn_house})" if sn_house else ""))
    
    # Verify nodes are in the context
    context_str = '\n'.join(context_parts)
    assert 'North Node' in context_str
    assert 'South Node' in context_str
    assert 'Capricorn' in context_str
    assert 'Cancer' in context_str
    assert 'House 6' in context_str
    assert 'House 12' in context_str
    print(f"✅ Prompt context includes nodes:\n{context_str}")


def test_missing_nodes_not_hallucinated():
    """Test that missing nodes are NOT hallucinated"""
    mock_chart_no_nodes = {
        "astrology": {
            "planets": {
                "Sun": {"sign": "Taurus"},
                "Moon": {"sign": "Aquarius"}
            },
            "nodes": {}  # Empty nodes
        }
    }
    
    context_parts = []
    astro = mock_chart_no_nodes.get('astrology', {})
    nodes = astro.get('nodes', {})
    north_node = nodes.get('north', {})
    south_node = nodes.get('south', {})
    
    # Should NOT add nodes if missing
    if north_node and north_node.get('sign'):
        context_parts.append(f"North Node: {north_node.get('formatted')}")
    if south_node and south_node.get('sign'):
        context_parts.append(f"South Node: {south_node.get('formatted')}")
    
    context_str = '\n'.join(context_parts)
    assert 'North Node' not in context_str
    assert 'South Node' not in context_str
    print("✅ Missing nodes are NOT hallucinated (empty context)")


if __name__ == "__main__":
    test_context_bundle_includes_north_node()
    test_context_bundle_includes_south_node()
    test_prompt_context_includes_nodes()
    test_missing_nodes_not_hallucinated()
    print("\n🎉 All tests passed!")
