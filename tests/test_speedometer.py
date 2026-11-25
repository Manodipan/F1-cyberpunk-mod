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
        for field in ("slot1:", "slot1Custom:", "slot2:", "slot2Custom:", "showSlot2:", "showUnits:"):
            self.assertIn(field, self.text, field)

    def test_seven_units_are_offered_in_both_slots(self):
        for unit in ("MPS", "KMH", "MPH", "KNOTS", "FPS", "MACH", "CUSTOM"):
            self.assertEqual(self.text.count(f'"ModSettings.displayValues.{unit}"'), 2,
                             f"{unit} should be offered for both slots")

    def test_conversion_factors_are_the_real_ones(self):
        expected = {"KMH": "3.6", "MPH": "2.23694", "KNOTS": "1.94384", "FPS": "3.28084"}
        for unit, factor in expected.items():
            block = re.search(rf"PhoenixTS_Unit\.{unit}\) \{{\s*return ({factor});", self.text)
            self.assertIsNotNone(block, f"{unit} should convert by {factor}")

    def test_mach_is_one_over_343(self):
        # Mach 1 = 343 m/s, so the multiplier is 1/343 - expressed as arithmetic, not a magic number
        self.assertIn("return 1.0 / 343.0;", self.text)
        self.assertIn('@runtimeProperty("ModSettings.displayValues.MACH", "Mach")', self.text)
        self.assertIn('return "Mach";', self.text)
        # 58.8 m/s is Mach 0.17 - the significant-digit rule keeps three digits by itself
        self.assertIn('return "Mach";', self.text)
        self.assertAlmostEqual(58.8 / 343.0 * 1000, 171.4, places=1)

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

    def test_the_hud_names_the_unit_it_is_printing(self):
        # the point of the labels: nobody should have to remember which slot is which
        self.assertIn("public let showUnits: Bool = true;", self.text)
        self.assertIn('return number + " " + PhoenixTS_Label(unit, custom);', self.text)
        for label in ('"m/s"', '"km/h"', '"mph"', '"kn"', '"ft/s"'):
            self.assertIn(label, self.text, label)
        # a custom slot cannot be named, so it shows the multiplier it is using
        self.assertIn('return "x" + PhoenixTS_Format', self.text)

    def test_each_slot_tooltip_carries_the_factor_table(self):
        self.assertEqual(self.text.count("x2.23694"), 2)   # one per slot dropdown tooltip
        self.assertIn("3600 divided by the unit's length in metres", self.text)
        self.assertIn("58.8 m/s | 212 km/h", self.text)

    def test_no_newline_escapes(self):
        # Mod Settings tooltips are plain text; a literal \n would show up as characters
        self.assertNotIn("\\n", self.text)


class SignificantDigitTests(unittest.TestCase):
    """Three significant digits, whole numbers above 100 - the owner's rule."""

    THRESHOLDS = [(100.0, 0), (10.0, 1), (1.0, 2), (0.1, 3), (0.01, 4), (0.0, 5)]

    def places(self, value):
        v = abs(value)
        for floor, places in self.THRESHOLDS:
            if v >= floor:
                return places
        return 5

    def render(self, value):
        places = self.places(value)
        return f"{value:.{places}f}"

    def test_above_100_is_whole(self):
        self.assertEqual(self.render(212.4), "212")
        self.assertEqual(self.render(100.0), "100")
        self.assertEqual(self.render(361.9), "362")

    def test_three_significant_digits_below_100(self):
        self.assertEqual(self.render(58.83), "58.8")
        self.assertEqual(self.render(9.876), "9.88")
        self.assertEqual(self.render(0.1714), "0.171")
        self.assertEqual(self.render(0.01714), "0.0171")

    def test_the_rule_matches_the_redscript_thresholds(self):
        text = REDS.read_text(encoding="utf-8")
        for floor, places in ((100.0, 0), (10.0, 1), (1.0, 2), (0.1, 3), (0.01, 4)):
            self.assertIn(f"if v >= {floor} {{\n        return {places};", text, f"threshold {floor}")
        self.assertIn("return 5;", text)

    def test_the_formatter_pads_zeros(self):
        text = REDS.read_text(encoding="utf-8")
        # 0.005 must not render as "0.5"
        self.assertIn('pad = pad + "0";', text)


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
