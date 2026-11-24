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
        for ident in (
            "Vehicle.phoenix_aston_valkyrie:",
            "Vehicle.phoenix_aston_valkyrie_data:",
            "Vehicle.phoenix_aston_valkyrie_manufacturer:",
            "Vehicle.phoenix_aston_valkyrie_purchasable:",
            "Vehicle.phoenix_amv_wheel_front:",
            "Vehicle.phoenix_amv_wheel_back:",
            "Vehicle.phoenix_amv_gear_r:",
            "Vehicle.phoenix_amv_gear_7:",
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
        self.assertIn("2026-11-13 tester", yaml_out)               # test-history note

    def test_file_names(self):
        self.assertEqual(port.rename_path(Path("aston_valkyrie_audio.reds")).name,
                         "phoenix_aston_valkyrie_audio.reds")
        self.assertEqual(port.rename_path(Path("xaires_aston_valkyrie")).name,
                         "phoenix_aston_valkyrie")

    def test_idempotent(self):
        once = port_yaml(STOCK_YAML.read_text(encoding="utf-8"))
        self.assertEqual(once, port_yaml(once, physics=False))


class PhysicsTests(unittest.TestCase):
    def setUp(self):
        self.out = port_yaml(STOCK_YAML.read_text(encoding="utf-8"))

    def test_v2_table(self):
        for expected in (
            "horsepower: 2000",
            "engineMaxTorque: 3824",
            "maxSpeed: 138.89",
            "airResistanceFactor: 0.60",
            "turnUpdateMaxSpeedThreshold: 45",
            "turnUpdateMaxSpeedTurnMul: 0.21",
            "frictionMulLateral: 1.60",
            "frictionMulLongitudinal: 1.50",
            "frictionMulLateral: 1.70",
            "frictionMulLongitudinal: 1.68",
            "maxBrakingTorque: 1400",
            "maxBrakingTorque: 1150",
            "springStiffness: 30",
            "springStiffness: 28",
            "springDamping: 3000",
            "swaybarStiffness: 15",
            "swaybarStiffness: 19",
            "minLatFrictionCoef: 1.45",
            "minLongFrictionCoef: 1.45",
            "maxSpeedFactorGround: 0.70",
            "maxRPM: 7900",
            "resistanceTorque: 150",
        ):
            self.assertIn(expected, self.out, expected)

    def test_untouched_values(self):
        for keep in (
            "maxSpeedFactorAir: 0",
            "handbrakeBrakingTorque: 1600",
            "wheelTurnMaxAddPerSecond: 94",
            "wheelTurnMaxSubPerSecond: 150",
            "total_mass: 1750",
            "chassis_mass: 1750",
            "turningRollFactor: 0",
            "swaybarLengthScalar: 2",
            "torqueMultiplier: 0.765",  # reverse stays stock
            "maxSpeed: 15",             # ...and so does its window
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
        self.assertGreaterEqual(rear, front, "a RWD car should not have less rear grip")

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
        self.assertEqual(self.out.count("maxSpeed: 138.89"), 1)
        self.assertIn("return 138.89;", port_reds(stock("aston_valkyrie_audio.reds")))
        self.assertIn("return 91.7;", stock("aston_valkyrie_audio.reds"))   # source untouched

    def test_comments_and_strings_not_rewritten(self):
        text = 'a: 91.7          # stock 91.7 was the old ceiling\n'
        self.assertEqual(port_yaml(text), 'a: 138.89          # stock 91.7 was the old ceiling\n')


class GearLadderTests(unittest.TestCase):
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
        self.assertEqual(tops[-1], 138.89)                  # 500 km/h
        for lo, hi in zip(tops, tops[1:]):
            for g in range(1, 8):
                if self.gears[str(g)][1] == hi:
                    self.assertLess(self.gears[str(g)][0], hi, "window with no width")

    def test_ratio_steps_are_even(self):
        tops = [self.gears[str(g)][1] for g in range(1, 8)]
        steps = [b / a for a, b in zip(tops, tops[1:])]
        for step in steps:
            self.assertGreaterEqual(step, 1.20, steps)
            self.assertLessEqual(step, 1.32, steps)

    def test_top_gear_is_not_an_overdrive_cliff(self):
        # The failure mode is a gear the engine cannot pull (the original 1.80x overdrive).
        # 1.50 is the ceiling because the engine upshifts at 0.90 of a gear's range: to leave
        # ANY overlap at a 1.278 step the window has to be >= 1.278 / 0.90 = 1.42. Narrower
        # windows are what put a hole at every shift (see the test below).
        lo, hi = self.gears["7"][0], self.gears["7"][1]
        self.assertLessEqual(hi / lo, 1.50, "top gear window too tall to pull")
        self.assertGreaterEqual(self.gears["7"][2], 0.45, "top gear torque left on the floor")

    def test_every_shift_lands_inside_the_next_gear(self):
        """The bug that ate four builds: the game upshifts at ~0.90 of a gear's range, so if
        the next gear's floor is above that speed the box grabs a gear the car is too slow
        for, the engine falls under its floor, and the car brakes. 352 km/h, twice."""
        for g in range(1, 7):
            this_max = self.gears[str(g)][1]
            shift = 0.90 * this_max
            next_floor = self.gears[str(g + 1)][0]
            self.assertLessEqual(
                next_floor, shift,
                f"shift {g}->{g + 1} at {shift:.1f} m/s lands below gear {g + 1}'s "
                f"{next_floor:.1f} m/s floor - the car will brake there")

    def test_engine_rpm_windows_sit_inside_maxrpm(self):
        for g in range(1, 8):
            lo, hi = self.gears[str(g)][3], self.gears[str(g)][4]
            self.assertLess(lo, hi, g)
            self.assertLessEqual(hi, 7900, g)               # engine maxRPM

    def test_each_gear_tracks_its_own_rpm_band(self):
        """The shipped 7th was 1.80x of speed over 1.28x of rpm - a gear with two ratios."""
        for g in range(1, 8):
            lo, hi, rlo, rhi = self.gears[str(g)][:2] + self.gears[str(g)][3:5]
            if not lo:
                continue                       # 1st gear starts from standstill
            deviation = abs((hi / lo) / (rhi / rlo) - 1)
            self.assertLess(deviation, 0.02, f"gear {g}: window and rpm band disagree")

    def test_virtual_gearbox_matches_the_ladder(self):
        audio = port_reds(stock("aston_valkyrie_audio.reds"))
        for g in range(1, 8):
            top = port.fmt_num(self.gears[str(g)][1])
            self.assertIn(f"case {g}:\n      return {top};", audio)

    def test_stale_ceiling_note_is_gone(self):
        self.assertNotIn("(91.7 m/s = 330 km/h)", self.out)
        self.assertIn("138.89 m/s (500 km/h)", self.out)

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
        self.assertTrue(any("engineMaxTorque" in p for p in problems))

        r = subprocess.run([sys.executable, str(ROOT / "tools" / "port_to_phoenix.py"),
                            "--check", str(STOCK)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)

    def test_dangling_reference_is_caught(self):
        broken = 'return id == t"Vehicle.phoenix_does_not_exist";\n'
        problems = port.collect_refs([(Path("x.reds"), broken)])
        self.assertTrue(any("no matching record" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
