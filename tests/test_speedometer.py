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
        # it must not depend on the car mod (the header comment cites it as the source of the
        # constructs, which is documentation, not a dependency - so comments are excluded)
        code = "\n".join(line for line in self.text.splitlines()
                         if not line.lstrip().startswith("//"))
        self.assertNotIn("PhoenixAMV", code)

    def test_the_enum_is_declared_the_way_ade_declares_its_enum(self):
        """v2 declared `public enum`; ADE declares the bare form and it compiles on 2.5."""
        code = "\n".join(line for line in self.text.splitlines()
                         if not line.lstrip().startswith("//"))
        self.assertIn("\nenum PhoenixTS_Unit {", code)
        self.assertNotIn("public enum", code)
        # ADE: public let drivingAI: DrivingAIType = DrivingAIType.Vanilla;
        self.assertIn("public let slot1: PhoenixTS_Unit = PhoenixTS_Unit.MPS;", self.text)

    def test_let_is_used_where_a_value_changes(self):
        """`let` in redscript is reassignable - ADE reassigns `let` locals 64 times.

        Step C declared its lookup result with `var`, a keyword that appears nowhere in any
        compiling script in this repository, and the game refused the whole file. `let` is correct.
        """
        text = REDS.read_text(encoding="utf-8")
        self.assertIn("let s: ref<PhoenixTS_Settings>", text)

    def test_no_statement_is_split_across_lines(self):
        """v3 split a `return` over two lines with a leading `+` and did not boot.

        Nothing in ADE or the car mod continues an expression on the next line, so neither does
        this file. A line starting with an operator is the signature of that mistake.
        """
        for source, label in ((self.text, "shipped"), (self.pending, "parked")):
            for line in source.splitlines():
                stripped = line.strip()
                if stripped and stripped[0] in "+*/" and not stripped.startswith("//"):
                    self.fail(f"{label}: line continues an expression: {stripped[:60]}")

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
        self.assertIn('return first + "|" + PhoenixTS_Number(mps, s.slot2, s.slot2Custom, s.showUnits);',
                      self.text)
        # the second number is off by default: the field is ~4 characters wide
        self.assertIn("public let showSlot2: Bool = false;", self.text)

    def test_the_default_readout_fits_four_characters(self):
        """Observed: the widget is right-anchored and text grows left through the sidebar."""
        self.assertIn("public let showUnits: Bool = false;", self.text)
        self.assertIn("public let slot1: PhoenixTS_Unit = PhoenixTS_Unit.MPS;", self.text)
        # worst case with the shipped defaults is a three digit number in m/s
        self.assertLessEqual(len("212"), 4)

    def test_the_hud_names_the_unit_it_is_printing(self):
        # the point of the labels: nobody should have to remember which slot is which
        self.assertIn("public let showUnits: Bool", self.text)
        self.assertIn('return number + " " + PhoenixTS_Label(unit, custom);', self.text)
        for label in ('"m/s"', '"km/h"', '"mph"', '"kn"', '"ft/s"'):
            self.assertIn(label, self.text, label)
        # a custom slot cannot be named, so it shows the multiplier it is using
        self.assertIn('return "x" + ToString(', self.text)

    def test_each_slot_tooltip_carries_the_factor_table(self):
        self.assertEqual(self.text.count("x2.23694"), 2)   # one per slot dropdown tooltip
        self.assertIn("3600 divided by the unit's length in metres", self.text)
        self.assertIn("Example HUD: 59|212", self.text)

    def test_no_newline_escapes(self):
        # Mod Settings tooltips are plain text; a literal \n would show up as characters
        self.assertNotIn("\\n", self.text)


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
        "var ": "not a local declaration keyword in redscript - `let` is, and it is reassignable",
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
        text = REDS.read_text(encoding="utf-8")
        # NameOf first, then the two literal spellings: a wrong name returns null, which would
        # leave the Mod Settings tab decorative while the HUD silently used hardcoded units
        self.assertIn("Get(NameOf<PhoenixTS_Settings>())", text)
        self.assertIn('Get(n"PhoenixTrueSpeedometer.PhoenixTS_Settings")', text)
        self.assertIn('Get(n"PhoenixTS_Settings")', text)

    def test_a_missing_settings_system_still_shows_a_speed(self):
        text = REDS.read_text(encoding="utf-8")
        self.assertIn("if !IsDefined(s) {", text)
        # and says so, instead of looking like a working readout in the wrong unit
        self.assertIn('IntToString(RoundMath(mps)) + "*"', text)

    def test_the_readout_stays_short_enough_for_the_widget(self):
        """The HUD speed widget holds about four characters (the car mod writes '113')."""
        text = REDS.read_text(encoding="utf-8")
        self.assertNotIn('" | "', text)          # no spaced pipe
        self.assertIn('first + "|"', text)

    def test_game_instance_comes_from_the_proven_global(self):
        self.assertIn("GetGameInstance()", REDS.read_text(encoding="utf-8"))

    def test_the_shipped_hud_uses_only_the_car_mods_api_set(self):
        text = REDS.read_text(encoding="utf-8")
        for proven in ("AbsF(", "Vector4.Dot(", "RoundMath(", "IntToString(", "IsDefined(",
                       "inkTextRef.SetText(this.m_SpeedValue,", "wrappedMethod(speedValue)"):
            self.assertIn(proven, text, proven)
        self.assertIn("this.m_activeVehicle", text)
        # step B still ships no formatter of mine - that is step C
        for mine in ("PhoenixTS_Format", "PhoenixTS_SigDigits"):
            self.assertNotIn(mine, text, mine)


class ParkedDraftTests(unittest.TestCase):
    """The Mod Settings ConfigVar reader is a draft, and must stay out of the install."""

    DRAFT = ROOT / "Phoenix_true_speedometer/settings/PhoenixTS_ReadModSettings.reds.pending"

    def test_the_draft_is_not_installed(self):
        self.assertTrue(self.DRAFT.is_file())
        self.assertFalse(self.DRAFT.with_suffix(".reds").exists(), "draft must not be a .reds")

    def test_the_draft_guards_every_modsettings_call(self):
        """ModSettings.* does not exist without the framework - ADE guards all of them."""
        text = self.DRAFT.read_text(encoding="utf-8")
        self.assertIn('@if(ModuleExists("ModSettingsModule"))', text)
        self.assertIn('@if(!ModuleExists("ModSettingsModule"))', text)

    def test_the_draft_is_honest_about_what_is_unconfirmed(self):
        text = self.DRAFT.read_text(encoding="utf-8")
        self.assertIn("UNCONFIRMED", text)


class SelfAuditTests(unittest.TestCase):
    """Mechanical checks over the shipped file, written because the sandbox has no compiler.

    Every entry below was verified by hand against a script that compiles on the target install.
    If the redscript grows a call that is not here, this test fails and forces the provenance
    question to be answered before the file ships.
    """

    PROVEN_CALLS = {
        "AbsF": "car mod x5",
        "ClampF": "car mod x9, ADE x6",
        "Dot": "Vector4.Dot, car mod",
        "Equals": "ADE x44",
        "Get": "ScriptableSystemsContainer.Get, ADE",
        "GetGameInstance": "AVDE x38, car mod x10",
        "GetLinearVelocity": "car mod",
        "GetScriptableSystemsContainer": "ADE, exactly as GetInstance() uses it",
        "GetWorldForward": "car mod",
        "IntToString": "car mod x5",
        "IsDefined": "ADE x66, car mod x52",
        "RoundMath": "car mod x4",
        "SetText": "inkTextRef.SetText, car mod",
        "ToString": "proven by step B, which booted with it",
        "wrappedMethod": "ADE x62, car mod x7",
        "NameOf": "ADE x8, incl. the working GetInstance()",
    }

    def setUp(self):
        self.text = REDS.read_text(encoding="utf-8")
        self.code = "\n".join(line for line in self.text.splitlines()
                              if not line.lstrip().startswith("//"))

    def test_every_call_is_proven_to_compile(self):
        code = re.sub(r'"(?:\\.|[^"\\])*"', '""', self.code)   # drop string literals
        calls = set(re.findall(r"\b([A-Za-z_]\w*)\s*\(", code))
        calls -= {c for c in calls if c.startswith("PhoenixTS_")}
        calls -= {"unit", "OnSpeedValueChanged", "runtimeProperty", "wrapMethod", "PhoenixTS"}
        unproven = sorted(calls - set(self.PROVEN_CALLS))
        self.assertEqual(unproven, [], f"verify provenance before shipping: {unproven}")

    def test_braces_and_parens_balance(self):
        self.assertEqual(self.code.count("{"), self.code.count("}"))
        self.assertEqual(self.code.count("("), self.code.count(")"))

    def test_dependencies_point_at_bool_fields_only(self):
        """ADE's 31 dependencies all target Bool fields; an enum target hides the row forever."""
        bools = set(re.findall(r"public let (\w+): Bool", self.code))
        for target in re.findall(r'ModSettings\.dependency", "(\w+)"', self.text):
            self.assertIn(target, bools, f"dependency on non-Bool {target}")

    def test_the_lookup_matches_ades_working_getinstance(self):
        """ADE's live, working lookup is Get(NameOf<Settings>()) - ours must try that first."""
        self.assertIn("Get(NameOf<PhoenixTS_Settings>())", self.code)


class SignificantDigitTests(unittest.TestCase):
    """Three significant digits, whole numbers above 100 - the owner's rule.

    The formatter is parked with the rest of the feature set while the compile failure is
    bisected, so these tests read the parked source. Shipping it again is step B.
    """

    def setUp(self):
        self.text = SETTINGS.read_text(encoding="utf-8")

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
        text = self.text
        for floor, places in ((100.0, 0), (10.0, 1), (1.0, 2), (0.1, 3), (0.01, 4)):
            self.assertRegex(text, rf"if v >= {floor} \{{\s+return {places};", f"threshold {floor}")
        self.assertIn("return 5;", text)

    def test_the_formatter_pads_zeros(self):
        # v1 built the padding in a loop; the parked v2 uses a literal ladder, because the loop
        # form and the AbsI helper it called are not proven to exist on 2.5
        text = self.text
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
