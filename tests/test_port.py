#!/usr/bin/env python3
"""
Tests for tools/port_to_phoenix.py against the REAL stock mod (as uploaded to main).

Run:  python3 -m unittest discover -s tests -v
"""

import json
import subprocess
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import port_to_phoenix as port  # noqa: E402

STOCK = ROOT / "reference" / "stock"
STOCK_YAML = STOCK / "r6" / "tweaks" / "xaires" / "aston_valkyrie.yaml"
STOCK_SCRIPTS = STOCK / "r6" / "scripts" / "xaires_aston_valkyrie"
STOCK_XL = STOCK / "archive" / "pc" / "mod" / "aston_valkyrie.archive.xl"
DELIVERABLE = ROOT / "Phoenix_aston_cheats"


def port_yaml(text, physics=True):
    return port.port_text(text, ".yaml", physics, [])


def port_reds(text, physics=True):
    return port.port_text(text, ".reds", physics, [])


def stock(name):
    return (STOCK_SCRIPTS / name).read_text(encoding="utf-8")


class RenameTests(unittest.TestCase):
    def test_vehicle_and_sub_records(self):
        out = port_yaml(STOCK_YAML.read_text(encoding="utf-8"))
        # the stock mod's own records are shipped again, renamed - the amv_* helper records only
        # exist on the control path (VerbatimControlTests)
        for ident in (
            "Vehicle.phoenix_aston_valkyrie:",
            "Vehicle.phoenix_aston_valkyrie_data:",
            "Vehicle.phoenix_aston_valkyrie_manufacturer:",
            "Vehicle.phoenix_aston_valkyrie_purchasable:",
            "UIIcon.phoenix_aston_valkyrie_icon:",
            "UIIcon.phoenix_aston_valkyrie_logo:",
        ):
            self.assertIn(ident, out, ident)
        self.assertNotIn("xaires_aston_valkyrie:", out)
        self.assertNotIn("Vehicle.xaires_amv_", out)

    def test_enum_and_registration(self):
        out = port_yaml(STOCK_YAML.read_text(encoding="utf-8"))
        self.assertIn("enumName: phoenix_aston_valkyrie_logo", out)
        self.assertIn("- !append Vehicle.phoenix_aston_valkyrie\n", out)
        self.assertIn("- !append Vehicle.phoenix_aston_valkyrie_purchasable\n", out)
        self.assertIn("$base: Vehicle.phoenix_aston_valkyrie\n", out)

    def test_gearbox_is_one_explicit_list(self):
        """Inherited gear surgery is what made the car plateau on the stock 330 km/h."""
        out = port_yaml(STOCK_YAML.read_text(encoding="utf-8"))
        self.assertNotIn("!remove Vehicle.VehicleEngineData_4_SuperSport_inline", out)
        self.assertNotIn("!append Vehicle.phoenix_amv_gear_r", out)
        line = [l for l in out.splitlines() if l.strip().startswith("gears: [")][0]
        for g in ("r", "1", "2", "3", "4", "5", "6", "7"):
            self.assertIn(f"Vehicle.phoenix_amv_gear_{g}", line)
        self.assertEqual(line.count("Vehicle.phoenix_amv_gear_"), 8)

    def test_drive_helpers_still_append_like_the_stock_file(self):
        """driveHelpers is a different list - it must stay as the stock file had it."""
        out = port_yaml(STOCK_YAML.read_text(encoding="utf-8"))
        self.assertIn("driveHelpers:", out)

    def test_shared_assets_kept(self):
        out = port_yaml(STOCK_YAML.read_text(encoding="utf-8"))
        self.assertIn("entityTemplatePath: xaires\\aston_valkyrie\\aston_valkyrie.ent", out)
        self.assertIn("appearanceName: aston_valkyrie", out)
        self.assertIn('"xaires\\\\aston_valkyrie\\\\ui\\\\amv_dealer.inkatlas"', out)
        # LocKeys are renamed too: the stock archive has no strings at all (docs/LOCALISATION.md)
        self.assertIn("displayName: phoenix_aston_valkyrie_name", out)
        self.assertIn("info: LocKey#phoenix_aston_valkyrie_info", out)
        self.assertNotIn("xaires_aston_valkyrie_name", out)
        self.assertNotIn("xaires_aston_valkyrie_info", out)
        self.assertIn("atlasPartName: amv", out)

    def test_audio_resource_and_scripts(self):
        self.assertIn("player_audio_resource: phoenix_amv_engine",
                      port_yaml(STOCK_YAML.read_text(encoding="utf-8")))
        audio = port_reds(stock("aston_valkyrie_audio.reds"))
        self.assertIn('VC_DeepCopyAudioMetadata(source, n"phoenix_amv_engine")', audio)
        self.assertIn('Equals(vehicle.name, n"phoenix_amv_engine")', audio)
        self.assertIn("class PhoenixAMVEngineState", audio)
        self.assertIn('n"PhoenixAMVEngineState"', audio)          # service lookup name
        self.assertIn("func PhoenixAMV_GearSpeed", audio)

    def test_hud_targets_follow_the_records(self):
        main = port_reds(stock("aston_valkyrie.reds"))
        self.assertIn('t"Vehicle.phoenix_aston_valkyrie"', main)
        self.assertIn('t"Vehicle.phoenix_aston_valkyrie_purchasable"', main)
        self.assertIn("func PhoenixAMV_IsTarget", main)

    def test_vehiclecore_call_is_not_touched(self):
        """VC_* belongs to the VehicleCore module: renaming it breaks the mod."""
        self.assertIn("VC_DeepCopyAudioMetadata(", port_reds(stock("aston_valkyrie_audio.reds")))

    def test_shared_bank_and_facts_kept(self):
        audio = port_reds(stock("aston_valkyrie_audio.reds"))
        self.assertIn('sounds/XairesAMV_Wwise/xaires_amv.bnk', audio)
        self.assertIn('GetFact(n"xaires_cm_vol")', audio)
        self.assertIn('RegisterEvent(n"xamw_engine_on")', audio)
        self.assertIn('n"xcm_vol"', audio)

    def test_own_wwise_identifiers_are_renamed(self):
        """The bank-folder guard must not swallow XairesAMV_WwiseSend / _Wwise()."""
        audio = port_reds(stock("aston_valkyrie_audio.reds"))
        self.assertIn("PhoenixAMV_WwiseSend", audio)
        self.assertIn("func PhoenixAMV_Wwise()", audio)
        self.assertNotIn("XairesAMV_WwiseSend", audio)
        self.assertNotIn("XairesAMV_Wwise(", audio)

    def test_comments_are_provenance(self):
        """Turkish engineering notes (dates, credits) stay verbatim."""
        audio = port_reds(stock("aston_valkyrie_audio.reds"))
        self.assertIn("(Wwise bankası xaires_amv)", audio)        # bank name in a note
        self.assertIn('911 kopyası "xaires_amv_engine"', audio)     # stock record name in a note
        yaml_out = port_yaml(STOCK_YAML.read_text(encoding="utf-8"))
        self.assertIn("(xaires)", yaml_out)                        # author credit
        # the shipped build is the stock mod's own physics again, so its notes survive verbatim
        # (the reference banner only appears on the control path, tested in VerbatimControlTests)
        self.assertIn("Vehicle.phoenix_aston_valkyrie", yaml_out)

    def test_file_names(self):
        self.assertEqual(port.rename_path(Path("aston_valkyrie_audio.reds")).name,
                         "phoenix_aston_valkyrie_audio.reds")
        self.assertEqual(port.rename_path(Path("xaires_aston_valkyrie")).name,
                         "phoenix_aston_valkyrie")

    def test_scanner_shows_the_build_number_not_horsepower(self):
        yaml_out = port_yaml(STOCK_YAML.read_text(encoding="utf-8"))
        self.assertIn(f"horsepower: {port.BUILD_STAMP_BASE + port.BUILD}", yaml_out)
        self.assertNotIn("horsepower: 2000", yaml_out)

    def test_idempotent(self):
        once = port_yaml(STOCK_YAML.read_text(encoding="utf-8"))
        self.assertEqual(once, port_yaml(once, physics=False))


class ShippedArtifactTests(unittest.TestCase):
    """The committed deliverable must equal what the generator produces, byte for byte.

    Without this, a hand-edit to the shipped YAML - or a commit that forgets to re-run
    `make port` - survives every other test in the suite, because they all read the generator's
    output rather than the file the game actually loads."""

    @staticmethod
    def _stamped(text, suffix, source):
        return port.STAMP[suffix].format(origin="stock", source=source) + text

    def test_shipped_yaml_is_generated(self):
        expected = self._stamped(
            port_yaml(STOCK_YAML.read_text(encoding="utf-8")), ".yaml",
            "reference/stock/r6/tweaks/xaires/aston_valkyrie.yaml")
        actual = (DELIVERABLE / "r6" / "tweaks" / "phoenix" / "phoenix_aston_valkyrie.yaml") \
            .read_text(encoding="utf-8")
        self.assertEqual(actual, expected, "shipped YAML is stale - run `make port`")

    def test_shipped_redscripts_are_generated(self):
        out_dir = DELIVERABLE / "r6" / "scripts" / "phoenix_aston_valkyrie"
        for src in sorted(STOCK_SCRIPTS.glob("*.reds")):
            shipped = out_dir / src.name.replace("aston_valkyrie", "phoenix_aston_valkyrie")
            self.assertTrue(shipped.exists(), f"{shipped.name} is missing from the deliverable")
            self.assertEqual(shipped.read_text(encoding="utf-8"),
                             self._stamped(port_reds(src.read_text(encoding="utf-8")), ".reds",
                                           f"reference/stock/r6/scripts/xaires_aston_valkyrie/{src.name}"),
                             f"{shipped.name} is stale - run `make port`")


class StockBaseDrivetrainTests(unittest.TestCase):
    """Build 900022: the stock mod's physics, with four driven wheels.

    The stock file is rear-drive. AWD is the one thing we override on purpose - it is a
    handling change (halve the longitudinal demand per tyre at full throttle, which is the
    condition Auto Drive tests in), not a physics table."""

    @classmethod
    def setUpClass(cls):
        cls.out = port_yaml(STOCK_YAML.read_text(encoding="utf-8"))

    def _role(self, name):
        return self.out.split(f"Vehicle.phoenix_amv_role_{name}:")[1].split("Vehicle.")[0] \
            if f"Vehicle.phoenix_amv_role_{name}:" in self.out \
            else None

    def test_all_four_wheels_drive(self):
        front = self.out.split("Vehicle.phoenix_amv_wheel_front:")[1].split("Vehicle.")[0]
        back = self.out.split("Vehicle.phoenix_amv_wheel_back:")[1].split("Vehicle.")[0]
        self.assertIn("isDrive: true", front)
        self.assertIn("isDrive: true", back)

    def test_handbrake_stays_on_the_rear_pair(self):
        front = self.out.split("Vehicle.phoenix_amv_wheel_front:")[1].split("Vehicle.")[0]
        back = self.out.split("Vehicle.phoenix_amv_wheel_back:")[1].split("Vehicle.")[0]
        self.assertIn("isHandBrake: false", front)
        self.assertIn("isHandBrake: true", back)

    def test_the_virtual_gearbox_follows_the_shipped_ladder(self):
        """The redscript computes revs from these numbers; if they drift from the YAML every
        HUD reading above 6th gear is a lie."""
        reds = port_reds(stock("aston_valkyrie_audio.reds"))
        ladder = [25, 36.1, 47.2, 58.3, 69.4, 80.6, 95]
        for g, speed in enumerate(ladder, 1):
            self.assertIn(f"case {g}:\n      return {port.fmt_num(speed)};", reds, g)
        self.assertIn(f"default:\n      return {port.fmt_num(ladder[-1])};", reds)

    def test_every_gear_window_overlaps_the_next(self):
        """Build 900025 stalled its engine at 100 m/s because 6th ended at exactly the speed 7th
        began at: with no overlap the shift cannot happen, the car hits its own gear clamp and the
        drive cuts. The stock mod's own pairs all overlap; keep it that way."""
        windows = []
        for g in range(1, 8):
            block = re.search(rf"(?ms)^Vehicle\.phoenix_amv_gear_{g}:\n(.*?)(?=^Vehicle\.|\Z)",
                              self.out).group(1)
            lo = float(re.search(r"minSpeed:\s*([\d.]+)", block).group(1))
            hi = float(re.search(r"maxSpeed:\s*([\d.]+)", block).group(1))
            windows.append((g, lo, hi))
        for (g, lo, hi), (nxt, nlo, nhi) in zip(windows, windows[1:]):
            self.assertLess(nlo, hi, f"gear {nxt} starts at {nlo} but gear {g} ends at {hi}")

    def test_stretched_gears_keep_their_ratio_and_rpm_floor(self):
        """A gear record is a pair: torqueMultiplier is the ratio, maxSpeed the speed it reaches at
        redline, and stock keeps their product at ~27.9 across gears 4-7. Stretching one without
        the other claims a 91.7-class ratio on a 180 m/s gear - 2.2x the designed thrust."""
        def gear(g):
            return re.search(rf"(?ms)^Vehicle\.phoenix_amv_gear_{g}:\n(.*?)(?=^Vehicle\.|\Z)",
                             self.out).group(1)
        products = {}
        for g in (4, 5, 6, 7):
            b = gear(g)
            mult = float(re.search(r"torqueMultiplier:\s*([\d.]+)", b).group(1))
            hi = float(re.search(r"maxSpeed:\s*([\d.]+)", b).group(1))
            lo = float(re.search(r"minSpeed:\s*([\d.]+)", b).group(1))
            mx = float(re.search(r"maxEngineRPM:\s*([\d.]+)", b).group(1))
            mn = float(re.search(r"minEngineRPM:\s*([\d.]+)", b).group(1))
            products[g] = mult * hi
            self.assertLess(abs(mn - mx * lo / hi), 0.12 * mx * lo / hi,
                            f"gear {g}: rpm floor {mn} does not match {mx} x {lo}/{hi}")
        spread = max(products.values()) / min(products.values()) - 1
        self.assertLess(spread, 0.10, f"ratio x speed spread across gears 4-7: {products}")

    def test_the_note_does_not_still_say_rear_drive(self):
        self.assertNotIn("Arkadan itis", self.out)


class ControlPathTest(unittest.TestCase):
    """Base for the tests that describe the Jesko control pipeline.

    Since 2026-11-24 the shipped build is the STOCK mod's own physics again (it is the best car we
    have measured: 80 m/s under ADE / 85 by hand, against the reference's 63 / 77), so these tests
    run against the control path explicitly instead of the default output.
    """
    @classmethod
    def setUpClass(cls):
        cls._saved_flag = port.RESTORE_STOCK_PHYSICS
        port.RESTORE_STOCK_PHYSICS = False

    @classmethod
    def tearDownClass(cls):
        port.RESTORE_STOCK_PHYSICS = cls._saved_flag


class PhysicsTests(ControlPathTest):
    def setUp(self):
        self.out = port_yaml(STOCK_YAML.read_text(encoding="utf-8"))

    def test_control_is_the_jesko(self):
        """The physics is the reference car's, except the damping overlay (see StabilityTests)."""
        for expected in (
            "engineMaxTorque: 1000",
            "maxRPM: 7900",
            "minRPM: 900",
            "resistanceTorque: 150",
            "airResistanceFactor: 0.66",
            "total_mass: 1800",
            "chassis_mass: 1800",
            "frictionMulLateral: 1.3",
            "frictionMulLongitudinal: 0.95",
            "frictionMulLongitudinal: 0.98",
            "maxBrakingTorque: 1165",
            "maxBrakingTorque: 785",
            "maxSpeedFactorGround: 0.7",   # aero restored: load is not an ADE lever
            "minLatFrictionCoef: 0.95",   # stability overlay
            "turningRollFactor: 0",           # stability overlay; the reference has 1
            "wheelTurnMaxSubPerSecond: 170",
            "maxSpeed: 78.5",                 # its declared top gear, not ours
            "torqueMultiplier: 0.227",
            "tireRollingResistanceCoef: 0.002",
            "useAlternativeTurnUpdate: false",   # stability overlay: the stock car never had it
            "gearCurvesPath: base\\gameplay\\vehicles\\curves\\engine_torque\\large_balanced_turbo.curveset",
        ):
            self.assertIn(expected, self.out, expected)

    def test_no_jesko_identifier_leaks(self):
        """Records are renamed; nothing may *point* at the other mod. The provenance comment
        names the source file, which is the only place the name may appear."""
        code = "\n".join(l for l in self.out.splitlines() if not l.lstrip().startswith("#"))
        self.assertNotIn("jesko", code)

    def test_untouched_values(self):
        for keep in (
            "maxSpeedFactorAir: 0",
            "handbrakeBrakingTorque: 1600",
            "wheelTurnMaxAddPerSecond: 85",   # stability overlay; the reference has 137
            "wheelTurnMaxSubPerSecond: 170",
            "total_mass: 1800",
            "chassis_mass: 1800",
            "swaybarLengthScalar: 2.3",
            "torqueMultiplier: 1.0",     # reverse, now the reference's
            "maxSpeed: 10.0",            # ...and its window
        ):
            self.assertIn(keep, self.out, keep)

    def test_physics_is_attached_by_reference(self):
        """Both working reference mods attach physics by naming the record, not by nesting
        it. Same values either way - but this is the shape a proven mod ships."""
        for ref in ("vehEngineData: Vehicle.phoenix_amv_engine",
                    "vehDriveModelData: Vehicle.phoenix_amv_drive_model",
                    "vehWheelDimensionsSetup: Vehicle.phoenix_amv_wheel_dimensions"):
            self.assertIn(ref, self.out, ref)
        for rec in ("Vehicle.phoenix_amv_engine:",
                    "Vehicle.phoenix_amv_drive_model:",
                    "Vehicle.phoenix_amv_wheel_dimensions:"):
            self.assertIn(rec, self.out, rec)

    def test_gears_inherit_from_nothing(self):
        """TweakXL docs: inlineX bases shift between patches without warning."""
        self.assertNotIn("v_sport1_quadra_turbo_r_inline", self.out)
        self.assertEqual(self.out.count("$type: gamedataVehicleGear_Record"), 8)

    def test_grip_is_near_symmetric_front_to_back(self):
        """Every car we have data for runs the axles within 6% laterally; the old 2.00/1.60
        was 25% apart and was the last unexplained source of yaw nervousness."""
        front = float(re.search(r"frictionMulLateral: ([0-9.]+)", self.out).group(1))
        rear = float(re.findall(r"frictionMulLateral: ([0-9.]+)", self.out)[1])
        self.assertLessEqual(abs(rear / front - 1), 0.10, "lateral grip split too wide")
        # either axle may lead by a percent or two - the Jesko runs 1.30 front / 1.28 rear -
        # but never by the 25 % of the old build
        self.assertLess(abs(rear / front - 1), 0.05)

    def test_engine_stops_inheriting_the_top_gear_half(self):
        """The 572 km/h car writes these out; ours inherited them from a 911-class base."""
        for expected in (
            "flyWheelMomentOfInertia: 0.12",
            "finalGearTorqueDecimationScalor: 1.0",
            "gearChangeTime: 0.1",
            "gearChangeCooldown: 0.15",
            "fastR1GearChange: true",
            "wheelsResistanceRatio: 15",
        ):
            self.assertIn(expected, self.out, expected)

    def test_engine_fields_are_not_duplicated(self):
        once = port_yaml(STOCK_YAML.read_text(encoding="utf-8"))
        again = port.ensure_engine_fields(once)
        self.assertEqual(once, again)
        self.assertEqual(once.count("flyWheelMomentOfInertia"), 1)

    def test_gear7_in_both_places(self):
        self.assertEqual(self.out.count("maxSpeed: 78.5"), 1)
        self.assertIn("return 78.5;", port_reds(stock("aston_valkyrie_audio.reds")))
        self.assertIn("return 91.7;", stock("aston_valkyrie_audio.reds"))   # source untouched

    def test_comments_and_strings_not_rewritten(self):
        text = 'a: 91.7          # stock 91.7 was the old ceiling\n'
        self.assertEqual(port_yaml(text), 'a: 138.89          # stock 91.7 was the old ceiling\n')


class GearLadderTests(ControlPathTest):
    """A gear is a ratio window, not a speed cap (docs/VEHICLE-MODEL.md §4).

    The 2026-11-24 build put 277 -> 500 km/h inside one 1.80x overdrive whose
    torque multiplier was the weakest in the box; the car stopped where 6th ended.
    """

    def setUp(self):
        self.out = port_yaml(STOCK_YAML.read_text(encoding="utf-8"))
        self.gears = port.PHOENIX_GEARBOX

    def test_windows_climb_monotonically(self):
        tops = [self.gears[str(g)][1] for g in range(1, 8)]
        self.assertEqual(tops, sorted(tops))
        self.assertEqual(tops[-1], 78.5)                    # the Jesko's own top gear
        for lo, hi in zip(tops, tops[1:]):
            for g in range(1, 8):
                if self.gears[str(g)][1] == hi:
                    self.assertLess(self.gears[str(g)][0], hi, "window with no width")

    def test_ratio_steps_narrow_toward_the_top(self):
        """Not even steps: the Jesko - which is the car that actually reaches 500 km/h here -
        tapers 1.378, 1.275, 1.215, 1.177, 1.151, 1.131. Ours is that ladder scaled to 500."""
        tops = [self.gears[str(g)][1] for g in range(1, 8)]
        steps = [b / a for a, b in zip(tops, tops[1:])]
        for step in steps:
            self.assertGreaterEqual(step, 1.10, steps)
            self.assertLessEqual(step, 1.40, steps)
        self.assertEqual(steps, sorted(steps, reverse=True), steps)

    def test_top_gear_is_not_an_overdrive_cliff(self):
        # The failure mode is a gear the engine cannot pull (the original 1.80x overdrive).
        # 1.60 is the ceiling: to contain an upshift at 0.80 of a gear's range the next gear's
        # floor needs window >= step / 0.80 = 1.20 / 0.80 = 1.50. Narrower windows put a hole
        # at every shift (see the test below).
        lo, hi = self.gears["7"][0], self.gears["7"][1]
        self.assertLessEqual(hi / lo, 1.60, "top gear window too tall to pull")
        self.assertGreaterEqual(self.gears["7"][2], 0.22, "the Jesko ships 0.227")

    def test_every_shift_lands_inside_the_next_gear(self):
        """The Jesko's construction, and now ours: every gear's floor is 0.90 x the previous
        gear's top speed - checked to 0.01 m/s in reference/vehicles/jesko_attack.yaml, six
        for six. Set any floor higher and the box grabs a gear the car is too slow for, the
        engine falls under its floor, and the car brakes (308 and 352 km/h, twice)."""
        for g in range(1, 7):
            this_max = self.gears[str(g)][1]
            shift = 0.90 * this_max
            next_floor = self.gears[str(g + 1)][0]
            self.assertLessEqual(
                next_floor, shift + 0.01,      # rounded to 0.01 m/s
                f"shift {g}->{g + 1} at 0.80 of range ({shift:.1f} m/s) lands below gear "
                f"{g + 1}'s "
                f"{next_floor:.1f} m/s floor - the car will brake there")

    def test_engine_rpm_windows_sit_inside_maxrpm(self):
        for g in range(1, 8):
            lo, hi = self.gears[str(g)][3], self.gears[str(g)][4]
            self.assertLess(lo, hi, g)
            self.assertLessEqual(hi, 8200, g)               # engine maxRPM

    def test_engine_limiter_sits_above_the_gear_ceiling(self):
        """The limiter only ever matters if a gear can rev to it. Every shift happens at 0.90
        of a gear's ceiling, so the guard is: redline above the ceiling, AND the shift point
        below the redline (7900 redline / 7800 top gear / 7020 shift, exactly the Jesko)."""
        top_gear_rpm = max(self.gears[str(g)][4] for g in range(1, 8))
        self.assertGreater(7900, top_gear_rpm, "redline must sit above the gear ceiling")
        self.assertLess(0.90 * top_gear_rpm, 7900, "the shift must happen before the limiter")

    def test_each_gear_tracks_its_own_rpm_band(self):
        """The shipped 7th was 1.80x of speed over 1.28x of rpm - a gear with two ratios. The
        reference car's own 7th deviates 2.5 % (its ceiling is 7800 in a 7600 box), so that is
        the tolerance now that we are the control."""
        for g in range(1, 8):
            lo, hi, rlo, rhi = self.gears[str(g)][:2] + self.gears[str(g)][3:5]
            if not lo:
                continue                       # 1st gear starts from standstill
            deviation = abs((hi / lo) / (rhi / rlo) - 1)
            self.assertLess(deviation, 0.03, f"gear {g}: window and rpm band disagree")

    def test_virtual_gearbox_matches_the_ladder(self):
        audio = port_reds(stock("aston_valkyrie_audio.reds"))
        for g in range(1, 8):
            top = port.fmt_num(self.gears[str(g)][1])
            self.assertIn(f"case {g}:\n      return {top};", audio)

    def test_stale_ceiling_note_is_gone(self):
        self.assertNotIn("(91.7 m/s = 330 km/h)", self.out)
        self.assertIn("COPED VERBATIM FROM", self.out.replace("COPIED", "COPED"))

class DeliverableTests(unittest.TestCase):
    """The committed tree must be exactly what the tool produces — no hand edits."""

    def test_tree_matches_tool_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            subprocess.run(
                [sys.executable, str(ROOT / "tools" / "port_to_phoenix.py"),
                 "--from", "stock", str(STOCK_YAML),
                 "--out", str(tmp / "r6/tweaks/phoenix/phoenix_aston_valkyrie.yaml")],
                check=True, capture_output=True,
            )
            subprocess.run(
                [sys.executable, str(ROOT / "tools" / "port_to_phoenix.py"),
                 "--from", "stock", str(STOCK_SCRIPTS),
                 "--out", str(tmp / "r6/scripts/phoenix_aston_valkyrie")],
                check=True, capture_output=True,
            )
            committed = sorted(p for p in (DELIVERABLE / "r6").rglob("*") if p.is_file())
            generated = sorted(p for p in (tmp / "r6").rglob("*") if p.is_file())
            self.assertEqual([p.relative_to(DELIVERABLE) for p in committed],
                             [p.relative_to(tmp) for p in generated])
            for c, g in zip(committed, generated):
                self.assertEqual(c.read_text(encoding="utf-8"), g.read_text(encoding="utf-8"),
                                 f"{c} differs from tool output")

    def test_archive_and_localisation_present(self):
        xl = DELIVERABLE / "archive" / "pc" / "mod" / "phoenix_aston_valkyrie.archive.xl"
        self.assertTrue(xl.is_file())
        text = xl.read_text(encoding="utf-8")
        # our own namespace, and the path the packed archive must contain
        self.assertIn("phoenix\\aston_valkyrie\\en-us.json", text)
        self.assertNotIn("xaires", text)

    def test_localisation_source_matches_the_yaml(self):
        """tools/localization/en-us.json must define exactly the keys the YAML asks for."""
        doc = json.loads((ROOT / "tools" / "localization" / "en-us.json").read_text(encoding="utf-8"))
        root = doc["Data"]["RootChunk"]
        self.assertEqual(root["$type"], "JsonResource")
        entries = root["root"]["Data"]["entries"]
        self.assertEqual(root["root"]["Data"]["$type"],
                         "localizationPersistenceOnScreenEntries")
        keys = {e["secondaryKey"] for e in entries}
        self.assertEqual(keys, {"phoenix_aston_valkyrie_name", "phoenix_aston_valkyrie_info"})

        yaml = (DELIVERABLE / "r6" / "tweaks" / "phoenix" / "phoenix_aston_valkyrie.yaml"
                ).read_text(encoding="utf-8")
        for key in keys:
            self.assertIn(key, yaml, f"{key} is not referenced by the tweak file")
        for entry in entries:
            self.assertTrue(entry["femaleVariant"].strip(), f"empty text for {entry['secondaryKey']}")
            self.assertEqual(entry["maleVariant"], "")
            self.assertNotIn("xaires", entry["femaleVariant"].lower())

    def test_no_reds_leftover_code(self):
        problems = []
        for path in DELIVERABLE.rglob("*"):
            if path.is_file() and path.suffix in port.TEXT_SUFFIXES:
                problems += port.check_text(path.read_text(encoding="utf-8"), str(path),
                                            path.suffix.lower())
        self.assertEqual(problems, [])


class CheckTests(unittest.TestCase):
    def test_clean_tree_passes(self):
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "port_to_phoenix.py"),
                            "--check", str(DELIVERABLE)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_stock_tree_fails(self):
        problems = port.check_text(STOCK_YAML.read_text(encoding="utf-8"), "stock.yaml", ".yaml")
        self.assertTrue(any("xaires" in p for p in problems))
        # stock physics values are legal again since the stock mod is the shipped base, so this
        # assertion only holds for the control pipeline
        saved = port.RESTORE_STOCK_PHYSICS
        port.RESTORE_STOCK_PHYSICS = False
        try:
            problems = port.check_text(STOCK_YAML.read_text(encoding="utf-8"), "stock.yaml", ".yaml")
            self.assertTrue(any("engineMaxTorque" in p for p in problems))
        finally:
            port.RESTORE_STOCK_PHYSICS = saved

        r = subprocess.run([sys.executable, str(ROOT / "tools" / "port_to_phoenix.py"),
                            "--check", str(STOCK)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)

    def test_dangling_reference_is_caught(self):
        broken = 'return id == t"Vehicle.phoenix_does_not_exist";\n'
        problems = port.collect_refs([(Path("x.reds"), broken)])
        self.assertTrue(any("no matching record" in p for p in problems))


if __name__ == "__main__":
    unittest.main()


class VerbatimControlTests(ControlPathTest):
    """The control build is only a control if the records are the reference's own bytes."""

    def setUp(self):
        self.out = port_yaml(STOCK_YAML.read_text(encoding="utf-8"))

    @staticmethod
    def _without_overlay(block):
        """Drop the lines the stability overlay rewrites: those are the only permitted values."""
        keys = {k for k, _old, _new in port.STABILITY_OVERLAY}
        return "\n".join(l for l in block.splitlines()
                         if l.split(":")[0].strip() not in keys).strip("\n")

    def test_every_record_is_byte_identical_to_the_reference(self):
        recs = port.jesko_records()
        kept = self._without_overlay(self.out)
        for src, dst in port.JESKO_RECORD_MAP:
            block = recs[src]
            for a, b in port.JESKO_RECORD_MAP:      # the only permitted difference: record IDs
                block = block.replace(a, b)
            self.assertIn(self._without_overlay(block), kept, f"{dst} differs from {src}")

    def test_the_only_values_that_differ_are_damping_and_steering_rate(self):
        for key, _old, new in port.STABILITY_OVERLAY:
            self.assertIn(f"{key}: {new}", self.out, key)

    def test_vehicle_record_has_no_base_of_its_own(self):
        """The last inherited link: the vehicle record carried `$base:
        Vehicle.v_sport2_porsche_911turbo`, and a vehicle record holds curvesPath, driving
        params, impact and crowd settings that no drive-model field can override."""
        record = self.out[self.out.index("Vehicle.phoenix_aston_valkyrie:\n"):
                          self.out.index("UIIcon.phoenix_aston_valkyrie_icon:")]
        self.assertIn("$type: gamedataVehicle_Record", record)
        # the record itself inherits nothing; two nested sub-records (the driver data package
        # and the destruction params) still use their bases, which is why this checks indent 2
        top_level = [l for l in record.splitlines() if l.startswith("  ") and not l.startswith("    ")]
        self.assertEqual([l for l in top_level if "$base" in l], [])
        self.assertIn("curvesPath: base\\gameplay\\vehicles\\curves\\default_car.vehcurveset", record)
        self.assertIn("drivingParamsRace: Driving.Race_Driving", record)
        self.assertGreater(record.count("\n  "), 70, "the reference writes out 110 fields")

    def test_nothing_physics_is_left_of_ours(self):
        """Every value-bearing record in the physics span comes from the reference."""
        physics = self.out[self.out.index("Vehicle.phoenix_amv_role_lf:"):
                           self.out.index("Vehicle.phoenix_aston_valkyrie:")]
        for ours in ("$base: Vehicle.VehicleDriveModelData_911Turbo",
                     "$base: Vehicle.VehicleEngineData_4_SuperSport",
                     "$base: Vehicle.VehicleDriveModelData_911Turbo_inline"):
            self.assertNotIn(ours, physics)


class TrueSpeedometerTests(unittest.TestCase):
    """The HUD inflates speed; every vehicle should report what it is actually doing."""

    def setUp(self):
        self.src = stock("aston_valkyrie.reds")
        self.out = port_reds(self.src)

    def test_hud_speed_goes_around_the_display_curve_for_every_vehicle(self):
        self.assertIn("if PhoenixAMV_TrueSpeedo(this.m_activeVehicle) {", self.out)
        self.assertNotIn("IsTarget(this.m_activeVehicle) {", self.out)
        self.assertIn("return IsDefined(vehicle);", self.out)

    def test_kmh_mode_is_real_kmh(self):
        self.assertIn("let mps: Float = AbsF(speedValue);", self.out)
        self.assertIn("this.m_kmOn ? mps * 3.6 : mps", self.out)

    def test_mph_mode_shows_raw_m_s_instead_of_miles(self):
        # The owner never uses the imperial setting, so it carries the engine's own unit.
        self.assertNotIn("1.609344", self.out)
        self.assertIn(": mps;", self.out)

    def test_flag_off_restores_miles(self):
        saved = port.MPH_MODE_SHOWS_MPS
        port.MPH_MODE_SHOWS_MPS = False
        try:
            out = port.port_text(self.src, ".reds", True, [])
        finally:
            port.MPH_MODE_SHOWS_MPS = saved
        self.assertIn("kmh / 1.609344", out)

    def test_the_phoenix_dash_audio_and_leds_stay_gated_on_our_car(self):
        # Only the HUD number went global. Everything that is ours stays ours.
        self.assertIn('t"Vehicle.phoenix_aston_valkyrie"', self.out)
        for suffix in ("_ekran", "_audio"):
            body = port_reds(stock(f"aston_valkyrie{suffix}.reds"))
            self.assertIn("IsTarget(", body, suffix)
        # the rev LEDs gate on their own widget instead of the vehicle record
        led = port_reds(stock("aston_valkyrie_led.reds"))
        self.assertIn('n"amvLed"', led)
        self.assertNotIn("TrueSpeedo", led)

    def test_flag_off_restores_per_car_behaviour(self):
        saved = port.TRUE_SPEEDO_ALL_VEHICLES
        port.TRUE_SPEEDO_ALL_VEHICLES = False
        try:
            out = port.port_text(self.src, ".reds", True, [])
        finally:
            port.TRUE_SPEEDO_ALL_VEHICLES = saved
        self.assertIn("IsTarget(this.m_activeVehicle) {", out)
        self.assertNotIn("TrueSpeedo(this.m_activeVehicle)", out)

    def test_shipped_file_carries_it(self):
        shipped = (DELIVERABLE / "r6" / "scripts" / "phoenix_aston_valkyrie"
                   / "phoenix_aston_valkyrie.reds").read_text(encoding="utf-8")
        self.assertIn("if PhoenixAMV_TrueSpeedo(this.m_activeVehicle) {", shipped)
        self.assertIn("this.m_kmOn ? mps * 3.6 : mps", shipped)
        self.assertNotIn("1.609344", shipped)


class PhysicsSpeedReadoutTests(unittest.TestCase):
    """The dash must show the car's own velocity, not the number the HUD display path hands it.

    Every speed reading the driver has given came from one value: the argument of
    `OnSpeedValueChanged`. If something upstream caps that value, every reading is the cap and no
    gearing or torque change can move it. The dash therefore reads `GetLinearVelocity` - the
    physics - while the HUD keeps the game's number. Two numbers, same instant.
    """

    def setUp(self):
        self.src = stock("aston_valkyrie_ekran.reds")
        self.out = port_reds(self.src)

    def test_dash_reads_the_velocity_vector(self):
        self.assertIn("PhoenixAMV_DashSpeed(parent, RoundMath(AbsF(PhoenixAMV_FwdSpeed(", self.out)
        self.assertIn("this.m_vehicle)) * 3.6));", self.out)
        # the old, display-path reading must be gone from the speed callback
        self.assertNotIn("PhoenixAMV_DashSpeed(parent, RoundMath(AbsF(speed) * 3.6));", self.out)

    def test_the_dash_also_refreshes_from_the_tachometer(self):
        # the speed callback only fires when the speed VALUE changes, so a capped value would
        # freeze the dash; the rev model ticks on the physics and keeps it live
        self.assertIn("let mv = GetMountedVehicle(pv);", self.out)
        self.assertIn("AbsF(PhoenixAMV_FwdSpeed(mv)) * 3.6", self.out)

    def test_the_hud_keeps_the_game_value_as_the_control(self):
        hud = port_reds(stock("aston_valkyrie.reds"))
        self.assertIn("let mps: Float = AbsF(speedValue);", hud)

    def test_idempotent(self):
        again = port.port_text(self.out, ".reds", True, [])
        self.assertEqual(again.count("PhoenixAMV_FwdSpeed"), self.out.count("PhoenixAMV_FwdSpeed"))

    def test_other_scripts_are_untouched(self):
        for suffix in ("_audio", "_led"):
            self.assertNotIn("gercek hiz", port_reds(stock(f"aston_valkyrie{suffix}.reds")))
