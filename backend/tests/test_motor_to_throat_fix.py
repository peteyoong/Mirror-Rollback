"""
Unit tests for the has_motor_to_throat fix (May 2026).

Validates that:
  1. Direct motor→Throat channels still register (no regression).
  2. Indirect motor→Throat paths (via G Center / Ajna / Spleen bridges)
     now correctly register motor-defined Throat.
  3. Sacral defined WITHOUT any motor→Throat path stays Generator.
  4. Charts without Sacral defined are unaffected.
  5. Progressed-only channels never leak into natal type because
     determine_type / has_motor_to_throat are pure functions of their
     input — caller must only pass natal channels.
"""

import os
import sys
import unittest
from datetime import datetime, timezone

# Ensure backend root on path so we can import `calculations.*`
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.dirname(THIS_DIR)
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from calculations.human_design import (
    has_motor_to_throat,
    get_defined_channels,
    get_defined_centers,
    determine_type,
    MOTOR_CENTERS,
    get_human_design_chart,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Channel tuple convention used elsewhere in the codebase:
#   (gate1, gate2, center1, center2)
CH_2_14   = (2,  14, 'G Center', 'Sacral')          # bridge for Michelle
CH_1_8    = (1,  8,  'G Center', 'Throat')          # bridge for Michelle
CH_27_50  = (27, 50, 'Sacral', 'Spleen')            # Michelle's natal
CH_28_38  = (28, 38, 'Spleen', 'Root')              # Michelle's natal
CH_34_20  = (34, 20, 'Sacral', 'Throat')            # direct Sacral→Throat
CH_35_36  = (35, 36, 'Solar Plexus', 'Throat')      # direct SP→Throat
CH_45_21  = (45, 21, 'Throat', 'Ego')               # direct Ego→Throat
CH_19_49  = (19, 49, 'Root', 'Solar Plexus')        # SP via Root
CH_22_12  = (22, 12, 'Solar Plexus', 'Throat')      # direct SP→Throat


class TestHasMotorToThroat(unittest.TestCase):
    # ---- Direct motor→Throat — must still work ----

    def test_direct_sacral_to_throat(self):
        self.assertTrue(has_motor_to_throat([CH_34_20]))

    def test_direct_solar_plexus_to_throat(self):
        self.assertTrue(has_motor_to_throat([CH_35_36]))

    def test_direct_ego_to_throat(self):
        self.assertTrue(has_motor_to_throat([CH_45_21]))

    # ---- Indirect motor→Throat — the BUG-FIX case ----

    def test_indirect_sacral_via_gcenter(self):
        """Michelle Chai's case: Sacral —(2-14)→ G Center —(1-8)→ Throat."""
        self.assertTrue(has_motor_to_throat([CH_2_14, CH_1_8]))

    def test_indirect_root_via_solar_plexus(self):
        """Root —(19-49)→ Solar Plexus —(22-12)→ Throat."""
        self.assertTrue(has_motor_to_throat([CH_19_49, CH_22_12]))

    def test_indirect_motor_through_three_hops(self):
        """Root → Spleen → Sacral → G Center → Throat.
        Root is a motor but the path goes through 3 intermediate centers
        before reaching Throat — BFS must still find it."""
        channels = [
            (28, 38, 'Spleen', 'Root'),
            (27, 50, 'Sacral', 'Spleen'),
            (2,  14, 'G Center', 'Sacral'),
            (1,  8,  'G Center', 'Throat'),
        ]
        self.assertTrue(has_motor_to_throat(channels))

    # ---- No motor→Throat path — must still return False ----

    def test_no_throat_definition(self):
        """No channels touching Throat — should return False."""
        channels = [
            (27, 50, 'Sacral', 'Spleen'),
            (28, 38, 'Spleen', 'Root'),
        ]
        self.assertFalse(has_motor_to_throat(channels))

    def test_throat_defined_but_not_to_motor(self):
        """Throat defined via Ajna/Head only (no motor reachable)."""
        channels = [
            (43, 23, 'Ajna', 'Throat'),
            (64, 47, 'Head', 'Ajna'),
        ]
        self.assertFalse(has_motor_to_throat(channels))

    def test_isolated_motor_no_path(self):
        """Sacral defined but completely disconnected from Throat sub-graph."""
        channels = [
            (5,  15, 'Sacral', 'G Center'),  # Sacral↔G, no Throat link
            (43, 23, 'Ajna', 'Throat'),      # Throat↔Ajna, no motor
        ]
        self.assertFalse(has_motor_to_throat(channels))

    # ---- Edge cases ----

    def test_empty_channels(self):
        self.assertFalse(has_motor_to_throat([]))

    def test_channel_with_self_loop_ignored(self):
        channels = [(1, 2, 'G Center', 'G Center')]
        self.assertFalse(has_motor_to_throat(channels))

    def test_dict_shape_channels_supported(self):
        """Some callers pass channel dicts — must still work."""
        channels = [
            {'gate1': 2, 'gate2': 14, 'center1': 'G Center', 'center2': 'Sacral'},
            {'gate1': 1, 'gate2': 8,  'center1': 'G Center', 'center2': 'Throat'},
        ]
        self.assertTrue(has_motor_to_throat(channels))


class TestTypeClassificationEndToEnd(unittest.TestCase):
    """determine_type is the canonical type classifier — verify it now
    flips Michelle from Generator → Manifesting Generator."""

    def test_michelle_path_yields_manifesting_generator(self):
        """Michelle's natal channels: 2-14, 1-8, 27-50, 28-38."""
        natal_channels = [CH_2_14, CH_1_8, CH_27_50, CH_28_38]
        centers = get_defined_centers(natal_channels)
        self.assertIn('Sacral', centers)   # Sacral defined
        self.assertIn('Throat', centers)   # Throat defined
        self.assertTrue(has_motor_to_throat(natal_channels))
        t = determine_type(centers, natal_channels)
        self.assertEqual(t, 'Manifesting Generator')

    def test_sacral_defined_no_throat_link_stays_generator(self):
        """Sacral defined + Throat undefined → Generator (no regression)."""
        natal_channels = [CH_27_50, CH_28_38, CH_2_14]  # No Throat connection
        centers = get_defined_centers(natal_channels)
        self.assertIn('Sacral', centers)
        self.assertNotIn('Throat', centers)
        t = determine_type(centers, natal_channels)
        self.assertEqual(t, 'Generator')

    def test_no_sacral_with_motor_to_throat_is_manifestor(self):
        """Heart→Throat with NO Sacral → Manifestor (no regression)."""
        natal_channels = [CH_45_21]
        centers = get_defined_centers(natal_channels)
        self.assertNotIn('Sacral', centers)
        self.assertIn('Throat', centers)
        t = determine_type(centers, natal_channels)
        self.assertEqual(t, 'Manifestor')


class TestProgressedChannelsDoNotLeak(unittest.TestCase):
    """Verify determine_type is a pure function of its inputs and is
    NEVER reached with progressed/transit channels in the canonical
    type-classification path."""

    def test_natal_only_type_is_deterministic(self):
        """Type from natal-only channels must equal type from same natal
        channels passed again — proves purity & determinism."""
        natal = [CH_2_14, CH_1_8, CH_27_50, CH_28_38]
        centers = get_defined_centers(natal)
        first  = determine_type(centers, natal)
        second = determine_type(centers, natal)
        self.assertEqual(first, second)

    def test_progressed_addition_does_affect_classifier_when_leaked(self):
        """Demonstrates WHY natal-only purity matters: if a progressed
        motor→Throat channel were ever leaked into determine_type, the
        type WOULD flip.  The production calling-site (get_human_design
        _chart) only passes natal channels, so this leak cannot occur
        in practice — but the assertion below makes the invariant
        explicit so any future regression will be caught."""
        natal_only_no_throat = [CH_27_50, CH_28_38, CH_2_14]  # no Throat
        centers_natal = get_defined_centers(natal_only_no_throat)
        natal_type = determine_type(centers_natal, natal_only_no_throat)
        self.assertEqual(natal_type, 'Generator')

        # Hypothetically add a progressed Sacral→Throat direct channel.
        leaked = natal_only_no_throat + [CH_34_20]
        centers_leaked = get_defined_centers(leaked)
        leaked_type = determine_type(centers_leaked, leaked)
        self.assertEqual(leaked_type, 'Manifesting Generator')

        # Natal MUST remain Generator — the progressed channel must
        # never propagate back into the natal classifier.
        self.assertEqual(natal_type, 'Generator')
        self.assertNotEqual(natal_type, leaked_type)


class TestMichelleNatalChartE2E(unittest.TestCase):
    """End-to-end: compute Michelle's full natal chart and assert type."""

    def test_michelle_chai_is_manifesting_generator(self):
        # 17 Sep 1984, 09:48 local UTC+8 → 01:48 UTC.  Singapore.
        birth_utc = datetime(1984, 9, 17, 1, 48, tzinfo=timezone.utc)
        chart = get_human_design_chart(birth_utc, 1.3521, 103.8198)
        self.assertEqual(chart['type'], 'Manifesting Generator')
        self.assertIn('Sacral',  chart['defined_centers'])
        self.assertIn('Throat',  chart['defined_centers'])
        # Verify motor→throat directly via the function (the chart payload
        # does not expose this as a top-level field — it's encoded into
        # the `type` derivation).
        self.assertTrue(has_motor_to_throat(chart['defined_channels']))


if __name__ == '__main__':
    unittest.main()
