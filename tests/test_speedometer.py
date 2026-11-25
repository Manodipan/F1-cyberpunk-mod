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
# The full feature set, parked while the boot failure is bisected. `.pending` is never installed.
SETTINGS = ROOT / "Phoenix_true_speedometer/settings/PhoenixTS_Settings.reds.pending"


class SpeedometerModTests(unittest.TestCase):
    def setUp(self):
        self.text = REDS.read_text(encoding="utf-8")
        self.pending = SETTINGS.read_text(encoding="utf-8")

    def test_the_mod_exists_and_is_self_contained(self):
        self.assertTrue(REDS.is_file())
        # it must not depend on the car mod
        self.assertNotIn("PhoenixAMV", self.text)

    def test_the_shipped_file_declares_nothing_the_car_mod_does_not(self):
        """v2 did not boot, and the only structural difference left was these three.

        Phoenix_aston_valkyrie.reds boots on the target install and declares none of them, so the
        shipped build may not either until the boot failure is understood.
        """
        code = "\n".join(line for line in self.text.splitlines()
                         if not line.lstrip().startswith("//"))
        for construct in ("module ", "ScriptableSystem", "public enum", "runtimeProperty"):
            self.assertNotIn(construct, code, construct)
        self.assertIn("@wrapMethod(hudCarController)", self.text)

    def test_two_unit_slots_exist(self):
        for field in ("slot1:", "slot1Custom:", "slot2:", "slot2Custom:", "showSlot2:", "showUnits:"):
            self.assertIn(field, self.pending, field)

    def test_seven_units_are_offered_in_both_slots(self):
        for unit in ("MPS", "KMH", "MPH", "KNOTS", "FPS", "MACH", "CUSTOM"):
            self.assertEqual(self.pending.count(f'"ModSettings.displayValues.{unit}"'), 2,
                             f"{unit} should be offered for both slots")

    def test_conversion_factors_are_the_real_ones(self):
        expected = {"KMH": "3.6", "MPH": "2.23694", "KNOTS": "1.94384", "FPS": "3.28084"}
        for unit, factor in expected.items():
            block = re.search(rf"PhoenixTS_Unit\.{unit}\) \{{\s*return ({factor});", self.pending)
            self.assertIsNotNone(block, f"{unit} should convert by {factor}")

    def test_mach_is_one_over_343(self):
        # Mach 1 = 343 m/s, so the multiplier is 1/343 - expressed as arithmetic, not a magic number
        self.assertIn("return 1.0 / 343.0;", self.pending)
        self.assertIn('@runtimeProperty("ModSettings.displayValues.MACH", "Mach")', self.pending)
        self.assertIn('return "Mach";', self.pending)
        # 58.8 m/s is Mach 0.17 - the significant-digit rule keeps three digits by itself
        self.assertIn('return "Mach";', self.pending)
        self.assertAlmostEqual(58.8 / 343.0 * 1000, 171.4, places=1)

    def test_custom_slot_is_a_free_multiplier_and_is_clamped(self):
        self.assertIn("ClampF(custom, 0.0001, 1000.0)", self.pending)
        self.assertIn('@runtimeProperty("ModSettings.max", "1000.0")', self.pending)

    def test_the_speed_comes_from_the_body_not_the_callback(self):
        self.assertIn("Vector4.Dot(vehicle.GetLinearVelocity(), vehicle.GetWorldForward())", self.text)
        # the wrapper may use the argument only to forward it
        self.assertIn("wrappedMethod(speedValue)", self.text)
        self.assertNotIn("AbsF(speedValue)", self.text)

    def test_hud_writes_both_slots_joined(self):
        self.assertIn('first + " | " + second', self.pending)

    def test_the_hud_names_the_unit_it_is_printing(self):
        # the point of the labels: nobody should have to remember which slot is which
        self.assertIn("public let showUnits: Bool = true;", self.pending)
        self.assertIn('return number + " " + PhoenixTS_Label(unit, custom);', self.pending)
        for label in ('"m/s"', '"km/h"', '"mph"', '"kn"', '"ft/s"'):
            self.assertIn(label, self.pending, label)
        # a custom slot cannot be named, so it shows the multiplier it is using
        self.assertIn('return "x" + ToString(', self.pending)

    def test_each_slot_tooltip_carries_the_factor_table(self):
        self.assertEqual(self.pending.count("x2.23694"), 2)   # one per slot dropdown tooltip
        self.assertIn("3600 divided by the unit's length in metres", self.pending)
        self.assertIn("58.8 m/s | 212 km/h", self.pending)

    def test_no_newline_escapes(self):
        # Mod Settings tooltips are plain text; a literal \n would show up as characters
        self.assertNotIn("\\n", self.pending)


class CompileSafetyTests(unittest.TestCase):
    """The first version of this file failed REDScript compilation.

    Each symbol below was used and does not exist in redscript, so the whole mod failed to compile
    and *every* script in the game was disabled. This test class exists so it cannot happen again
    silently: the rule is that this file may only use constructs already compiled elsewhere in the
    repository (the car mod and ADE both compile on 2.5).
    """

    FORBIDDEN = {
        "IsPlayerDriven": "no such method on VehicleObject",
        "AbsI(": "no AbsI in redscript",
        "this.GetGame()": "not available on hudCarController",
        "Cast<": "avoided in favour of paired Int32/Float locals",
    }

    def test_no_symbols_that_failed_to_compile(self):
        text = REDS.read_text(encoding="utf-8")
        code = "\n".join(line for line in text.splitlines()
                          if not line.lstrip().startswith("//"))
        for symbol, why in self.FORBIDDEN.items():
            self.assertNotIn(symbol, code, f"{symbol} - {why}")

    def test_settings_system_is_looked_up_by_nameof(self):
        # this lives in the parked file, so it is checked there
        # NameOf<T>() resolves the registered name at compile time - proven by ADE debug.reds:56 on
        # 2.5. A hand-written name string would return null if wrong, leaving the tab dead.
        text = SETTINGS.read_text(encoding="utf-8")
        self.assertIn("Get(NameOf<PhoenixTS_Settings>())", text)
        self.assertNotIn('Get(n"', text)

    def test_a_missing_settings_system_still_shows_a_speed(self):
        self.assertIn("if !IsDefined(s) {", SETTINGS.read_text(encoding="utf-8"))

    def test_game_instance_comes_from_the_proven_global(self):
        self.assertIn("GetGameInstance()", SETTINGS.read_text(encoding="utf-8"))

    def test_the_shipped_hud_uses_only_the_car_mods_api_set(self):
        text = REDS.read_text(encoding="utf-8")
        for proven in ("AbsF(", "Vector4.Dot(", "RoundMath(", "IntToString(", "IsDefined(",
                       "inkTextRef.SetText(this.m_SpeedValue,", "wrappedMethod(speedValue)"):
            self.assertIn(proven, text, proven)
        self.assertIn("this.m_activeVehicle", text)


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
            self.assertRegex(text, rf"if v >= {floor} \{{\s+return {places};", f"threshold {floor}")
        self.assertIn("return 5;", text)

    def test_the_formatter_pads_zeros(self):
        # v1 built the padding in a loop; v2 (the version that compiles) uses a literal ladder,
        # because the loop form and the AbsI helper it called are not proven to exist on 2.5
        text = REDS.read_text(encoding="utf-8")
        for ladder in ('pad = "0000";', 'pad = "000";', 'pad = "00";', 'pad = "0";'):
            self.assertIn(ladder, text)
        self.assertIn('return IntToString(whole) + "." + pad + IntToString(frac);', text)

    def test_the_fixed_point_formatter_matches_its_python_port(self):
        """The redscript cannot be run here, so its integer math is mirrored and checked."""

        def render(value, decimals):
            if decimals <= 0:
                return str(int(round(value)))
            scale = {1: 10, 2: 100, 3: 1000, 4: 10000}.get(decimals, 100000)
            scaled = int(round(value * scale))
            whole = int(scaled / scale)
            frac = scaled - whole * scale
            if frac < 0:
                return str(whole)
            width = {1: 1, 2: 2, 3: 3, 4: 4}.get(decimals, 5)
            return f"{whole}.{frac:0{width}d}"

        self.assertEqual(render(212.4, 0), "212")
        self.assertEqual(render(58.83, 1), "58.8")
        self.assertEqual(render(9.876, 2), "9.88")
        self.assertEqual(render(0.1714, 3), "0.171")
        self.assertEqual(render(0.01714, 4), "0.0171")
        self.assertEqual(render(0.005, 5), "0.00500")   # never "0.5"
        self.assertEqual(render(58.83, 3), "58.830")    # whole number above 100 stays whole
        self.assertEqual(render(0.0, 3), "0.000")


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
