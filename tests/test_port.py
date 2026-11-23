#!/usr/bin/env python3
"""
Tests for tools/port_to_phoenix.py against the REAL stock mod (as uploaded to main).

Run:  python3 -m unittest discover -s tests -v
"""

import json
import subprocess
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
            "airResistanceFactor: 0.90",
            "frictionMulLateral: 1.60",
            "frictionMulLongitudinal: 1.50",
            "frictionMulLateral: 2.00",
            "frictionMulLongitudinal: 1.85",
            "maxBrakingTorque: 1850",
            "maxBrakingTorque: 1550",
            "springStiffness: 30",
            "springStiffness: 28",
            "springDamping: 3000",
            "swaybarStiffness: 15",
            "swaybarStiffness: 19",
            "minLatFrictionCoef: 1.45",
            "minLongFrictionCoef: 1.45",
            "maxSpeedFactorGround: 1.40",
        ):
            self.assertIn(expected, self.out, expected)

    def test_untouched_values(self):
        for keep in (
            "maxSpeedFactorAir: 0",
            "handbrakeBrakingTorque: 2600",
            "wheelTurnMaxAddPerSecond: 94",
            "turnUpdateMaxSpeedThreshold: 26",
            "turnUpdateMaxSpeedTurnMul: 0.33",
            "maxRPM: 10100",
            "total_mass: 1750",
            "chassis_mass: 1750",
            "turningRollFactor: 0",
            "swaybarLengthScalar: 2",
            "torqueMultiplier: 0.782",
            "minSpeed: 22",
            "maxSpeed: 80.6",          # gear 6 stays (PORT.md §3)
            "maxSpeed: 25",            # gear 1 stays
        ):
            self.assertIn(keep, self.out, keep)

    def test_gear7_in_both_places(self):
        self.assertEqual(self.out.count("maxSpeed: 138.89"), 1)
        self.assertIn("return 138.89;", port_reds(stock("aston_valkyrie_audio.reds")))
        self.assertIn("return 91.7;", stock("aston_valkyrie_audio.reds"))   # source untouched

    def test_comments_and_strings_not_rewritten(self):
        text = 'a: 91.7          # stock 91.7 was the old ceiling\n'
        self.assertEqual(port_yaml(text), 'a: 138.89          # stock 91.7 was the old ceiling\n')


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
