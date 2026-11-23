#!/usr/bin/env python3
"""
Tests for tools/port_to_phoenix.py (PORT.md §4 rename + §3 physics port).

Run:  python3 -m unittest discover -s tests -v
"""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import port_to_phoenix as port  # noqa: E402

F1_YAML = ROOT / "reference" / "aston_valkyrie_f1.yaml"
STOCK_YAML = ROOT / "reference" / "aston_valkyrie_stock.yaml"
SCRIPTS = ROOT / "reference" / "clone_f1"
DELIVERABLE = ROOT / "Phoenix_aston_cheats"


def port_yaml(text, physics=False, keep_method_names=False):
    return port.port_text(text, ".yaml", physics, keep_method_names)


def port_reds(text, physics=False, keep_method_names=False):
    return port.port_text(text, ".reds", physics, keep_method_names)


class RenameTests(unittest.TestCase):
    def test_vehicle_ids(self):
        out = port_yaml(F1_YAML.read_text())
        self.assertIn("Vehicle.phoenix_aston_valkyrie:", out)
        self.assertIn("Vehicle.phoenix_aston_valkyrie_purchasable:", out)
        self.assertIn("Vehicle.phoenix_aston_valkyrie_data:", out)
        self.assertIn("Vehicle.phoenix_aston_valkyrie_manufacturer:", out)
        for stale in ("Vehicle.xaires_aston_valkyrie", "Vehicle.xaires_amv", "UIIcon.xaires"):
            self.assertNotIn(stale, out)

    def test_sub_records_and_registration(self):
        out = port_yaml(F1_YAML.read_text())
        for ident in (
            "Vehicle.phoenix_amv_gear:",
            "Vehicle.phoenix_amv_wheel:",
            "Vehicle.phoenix_amv_wheel_front:",
            "Vehicle.phoenix_amv_drive:",
            "Vehicle.phoenix_amv_gear_inline6.maxSpeed",
            "- !append Vehicle.phoenix_aston_valkyrie",
        ):
            self.assertIn(ident, out)

    def test_ui_enum_renamed_but_atlas_kept(self):
        out = port_yaml(F1_YAML.read_text())
        self.assertIn("enumName: phoenix_aston_valkyrie_logo", out)
        # texture core is shared, so atlas names must NOT move
        self.assertIn("atlasResourcePath: xaires\\aston_valkyrie\\ui\\xaires_aston_valkyrie.inkatlas", out)
        self.assertIn("atlasPartName: xaires_aston_valkyrie_logo", out)

    def test_shared_audio_and_assets_kept(self):
        out = port_yaml(F1_YAML.read_text())
        self.assertIn("player_audio_resource: phoenix_amv_engine", out)
        self.assertIn("entityTemplatePath: xaires\\aston_valkyrie\\aston_valkyrie.ent", out)
        self.assertIn("appearanceName: aston_valkyrie", out)
        self.assertIn("displayName: xaires_aston_valkyrie_name", out)   # LocKey until §6
        self.assertIn("LocKey#xaires_aston_valkyrie_info", out)

    def test_reds_module_class_and_resource(self):
        out = port_reds((SCRIPTS / "xaires_aston_valkyrie_f1_audio.reds").read_text())
        self.assertIn("module PhoenixAMV", out)
        self.assertIn("class PhoenixAMV_Audio", out)
        self.assertIn('n"phoenix_amv_engine"', out)

    def test_method_prefix_avoids_addmethod_collision(self):
        out = port_reds((SCRIPTS / "xaires_aston_valkyrie_f1_audio.reds").read_text())
        self.assertIn("func PHX_DeepCopyAudioMetadata", out)
        kept = port_reds(
            (SCRIPTS / "xaires_aston_valkyrie_f1_audio.reds").read_text(),
            keep_method_names=True,
        )
        self.assertIn("func VC_DeepCopyAudioMetadata", kept)

    def test_file_names(self):
        self.assertEqual(
            port.rename_path(Path("xaires_aston_valkyrie_f1_audio.reds")).name,
            "phoenix_aston_valkyrie_audio.reds",
        )
        self.assertEqual(
            port.rename_path(Path("xaires_aston_valkyrie")).name,
            "phoenix_aston_valkyrie",
        )

    def test_idempotent(self):
        once = port_yaml(F1_YAML.read_text())
        self.assertEqual(once, port_yaml(once))


class PhysicsTests(unittest.TestCase):
    def test_stock_to_phoenix_table(self):
        out = port_yaml(STOCK_YAML.read_text(), physics=True)
        expectations = [
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
            "downforceFactor: 1.40",
            "multiplier: 1.45",
        ]
        for e in expectations:
            self.assertIn(e, out, e)

    def test_unchanged_values_stay(self):
        out = port_yaml(STOCK_YAML.read_text(), physics=True)
        for keep in ("wheelTurnMaxAddPerSecond: 94", "wheelTurnMaxSubPerSecond: 26",
                     "maxRPM: 10100", "total_mass: 1750", "turningRollFactor: 0"):
            self.assertIn(keep, out)

    def test_gear7_in_reds(self):
        text = (SCRIPTS / "xaires_aston_valkyrie_f1_gearspeed.reds").read_text()
        self.assertIn("return 91.7;", text)          # source still stock
        self.assertIn("return 138.89;", port_reds(text))

    def test_comments_are_not_rewritten(self):
        text = "value: 91.7          # stock 91.7 was the old ceiling\n"
        self.assertEqual(port_yaml(text), "value: 138.89          # stock 91.7 was the old ceiling\n")


class CheckTests(unittest.TestCase):
    def test_deliverable_is_clean(self):
        problems = []
        for path in DELIVERABLE.rglob("*"):
            if path.is_file() and path.suffix in port.TEXT_SUFFIXES:
                problems += port.check_text(path.read_text(), str(path))
        self.assertEqual(problems, [])

    def test_source_is_flagged(self):
        problems = port.check_text(F1_YAML.read_text(), "f1.yaml")
        self.assertTrue(problems)

    def test_cli_check_exit_codes(self):
        clean = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "port_to_phoenix.py"), "--check", str(DELIVERABLE)],
            capture_output=True, text=True,
        )
        self.assertEqual(clean.returncode, 0, clean.stderr)
        dirty = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "port_to_phoenix.py"), "--check", str(SCRIPTS)],
            capture_output=True, text=True,
        )
        self.assertEqual(dirty.returncode, 1)


if __name__ == "__main__":
    unittest.main()
