"""The standalone speedometer mod: two runtime unit slots, both read from the body.

The point of the mod is that the number must not come from the HUD's own speed path - that value
has already been through the game's speed_to_multiplier curve, measured at 1.92x (17 s/km read as
113) and 2.06x (277 km/h read as 572).
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REDS = ROOT / "Phoenix_true_speedometer/r6/scripts/phoenix_true_speedometer/phoenix_true_speedometer.reds"


class SpeedometerModTests(unittest.TestCase):
    def setUp(self):
        self.text = REDS.read_text(encoding="utf-8")

    def test_the_mod_exists_and_is_self_contained(self):
        self.assertTrue(REDS.is_file())
        self.assertTrue(self.text.startswith("module PhoenixTrueSpeedometer"))
        # it must not depend on the car mod
        self.assertNotIn("PhoenixAMV", self.text)

    def test_two_unit_slots_exist(self):
        for field in ("slot1:", "slot1Custom:", "slot2:", "slot2Custom:", "showSlot2:", "decimals:"):
            self.assertIn(field, self.text, field)

    def test_six_units_are_offered_in_both_slots(self):
        for unit in ("MPS", "KMH", "MPH", "KNOTS", "FPS", "CUSTOM"):
            self.assertEqual(self.text.count(f'"ModSettings.displayValues.{unit}"'), 2,
                             f"{unit} should be offered for both slots")

    def test_conversion_factors_are_the_real_ones(self):
        expected = {"KMH": "3.6", "MPH": "2.23694", "KNOTS": "1.94384", "FPS": "3.28084"}
        for unit, factor in expected.items():
            block = re.search(rf"PhoenixTS_Unit\.{unit}\) \{{\s*return ({factor});", self.text)
            self.assertIsNotNone(block, f"{unit} should convert by {factor}")

    def test_custom_slot_is_a_free_multiplier_and_is_clamped(self):
        self.assertIn("ClampF(custom, 0.0001, 1000.0)", self.text)
        self.assertIn('@runtimeProperty("ModSettings.max", "1000.0")', self.text)

    def test_the_speed_comes_from_the_body_not_the_callback(self):
        self.assertIn("Vector4.Dot(vehicle.GetLinearVelocity(), vehicle.GetWorldForward())", self.text)
        # the wrapper may use the argument only to forward it
        self.assertIn("wrappedMethod(speedValue)", self.text)
        self.assertNotIn("AbsF(speedValue)", self.text)

    def test_hud_writes_both_slots_joined(self):
        self.assertIn('first + " | " + second', self.text)


class ConversionMathTests(unittest.TestCase):
    """The numbers the redscript claims, checked in Python."""

    def test_known_factors(self):
        for factor, label in ((3.6, "km/h"), (2.23694, "mph"), (1.94384, "knots"), (3.28084, "ft/s")):
            self.assertAlmostEqual(factor, {"km/h": 3.6, "mph": 2.236936, "knots": 1.943844,
                                            "ft/s": 3.280840}[label], places=4)

    def test_the_owner_measurement_is_consistent(self):
        # 17 s per km -> 58.8 m/s; the dial said 113
        mps = 1000.0 / 17.0
        self.assertAlmostEqual(mps, 58.8, places=1)
        self.assertAlmostEqual(113 / mps, 1.92, places=2)
        self.assertAlmostEqual(58.8 * 3.6, 211.7, places=0)


if __name__ == "__main__":
    unittest.main()
