#!/usr/bin/env python3
"""The 500 km/h design doc must match what the model actually computes."""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import land_speed_design as design  # noqa: E402


class DesignModelTests(unittest.TestCase):
    def test_model_reproduces_a_verified_record_within_twelve_percent(self):
        # SSC Tuatara: 1,750 hp, CdA 0.279 x 1.672, 532.93 km/h one-way.
        v = design.v_for_power(1305e3, 0.279 * 1.672, 1247) * 3.6
        self.assertLess(abs(v - 532.93) / 532.93, 0.12)

    def test_more_drag_costs_more_power_cubed(self):
        v = 500 / 3.6
        a = design.drag_power(v, 0.52, 1800)
        b = design.drag_power(v, 0.52 * 1.1, 1800)
        aero_a = a - design.CRR * 1800 * design.G * v
        aero_b = b - design.CRR * 1800 * design.G * v
        self.assertAlmostEqual(aero_b / aero_a, 1.1, places=3)

    def test_design_point_has_margin_over_500(self):
        # CdA 0.523 at 1,600 hp should sit above 500, so 500 is a plateau and not a cliff.
        v = design.v_for_power(1193e3, 0.278 * 1.88, 1800) * 3.6
        self.assertGreater(v, 500)
        self.assertLess(v, 600)

    def test_committed_doc_is_current(self):
        out = subprocess.run([sys.executable, str(ROOT / "tools" / "land_speed_design.py"), "--check"],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)


if __name__ == "__main__":
    unittest.main()
