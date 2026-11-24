#!/usr/bin/env python3
"""The update path is part of the product: one command, and it must stay correct."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "update.ps1"
DOC = ROOT / "docs" / "UPDATE.md"


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.script = SCRIPT.read_text(encoding="utf-8")
        self.doc = DOC.read_text(encoding="utf-8")

    def test_script_and_doc_exist(self):
        self.assertTrue(SCRIPT.is_file())
        self.assertTrue(DOC.is_file())

    def test_script_copies_what_the_mod_needs(self):
        """Both halves travel: physics in the YAML, audio/HUD in the scripts."""
        self.assertIn(r"Phoenix_aston_cheats\r6\tweaks\phoenix\phoenix_aston_valkyrie.yaml", self.script)
        self.assertIn(r"Phoenix_aston_cheats\r6\scripts\phoenix_aston_valkyrie", self.script)
        for target in (r"r6\tweaks\phoenix", r"r6\scripts\phoenix_aston_valkyrie"):
            self.assertIn(target, self.script, target)

    def test_the_copied_paths_are_real(self):
        self.assertTrue((ROOT / "Phoenix_aston_cheats/r6/tweaks/phoenix/phoenix_aston_valkyrie.yaml").is_file())
        reds = list((ROOT / "Phoenix_aston_cheats/r6/scripts/phoenix_aston_valkyrie").glob("*.reds"))
        self.assertEqual(len(reds), 4)

    def test_script_clears_generated_files_before_pulling(self):
        """These two conflict on every pull because both sides regenerate them."""
        checkout = self.script.index("git checkout -- $generated")
        pull = self.script.index("git pull --rebase")
        self.assertLess(checkout, pull)
        for generated in ("reference/vehicles/INDEX.md", "docs/VEHICLE-COMPARISON.md"):
            self.assertIn(generated, self.script)

    def test_script_verifies_the_install(self):
        self.assertIn("Get-FileHash", self.script)
        self.assertIn("DIFFERS", self.script)

    def test_script_says_a_restart_is_needed(self):
        self.assertRegex(self.script, r"restart")

    def test_doc_matches_the_script_name(self):
        self.assertIn("tools\\update.ps1", self.doc)
        self.assertIn("restart", self.doc.lower())

    def test_doc_has_the_by_hand_fallback(self):
        for needle in ("git pull --rebase", "Copy-Item", "Select-String"):
            self.assertIn(needle, self.doc, needle)

    def test_readme_points_at_the_update_doc(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("docs/UPDATE.md", readme)
        self.assertIn("tools\\update.ps1", readme)


if __name__ == "__main__":
    unittest.main()


class DrivetrainTests(unittest.TestCase):
    """AWD is a prepared switch, not a shipped change - see docs/TOPSPEED-TEST.md 3f."""

    def setUp(self):
        import sys
        from pathlib import Path as _P
        root = _P(__file__).resolve().parents[1]
        sys.path.insert(0, str(root / "tools"))
        import port_to_phoenix as port
        self.port = port
        self.stock = (root / "reference/stock/r6/tweaks/xaires/aston_valkyrie.yaml").read_text(encoding="utf-8")

    def test_shipped_build_is_rear_drive(self):
        out = self.port.port_text(self.stock, ".yaml", True)
        front = out.split("Vehicle.phoenix_amv_wheel_front:")[1].split("Vehicle.")[0]
        back = out.split("Vehicle.phoenix_amv_wheel_back:")[1].split("Vehicle.")[0]
        self.assertIn("isDrive: false", front)
        self.assertIn("isDrive: true", back)

    def test_awd_flag_drives_all_four(self):
        from unittest import mock
        with mock.patch.object(self.port, "DRIVETRAIN", "awd"):
            out = self.port.port_text(self.stock, ".yaml", True)
        front = out.split("Vehicle.phoenix_amv_wheel_front:")[1].split("Vehicle.")[0]
        back = out.split("Vehicle.phoenix_amv_wheel_back:")[1].split("Vehicle.")[0]
        self.assertIn("isDrive: true", front)
        self.assertIn("isDrive: true", back)
        self.assertNotIn("isDrive: false", front + back)

    def test_awd_does_not_touch_the_handbrake(self):
        from unittest import mock
        with mock.patch.object(self.port, "DRIVETRAIN", "awd"):
            out = self.port.port_text(self.stock, ".yaml", True)
        front = out.split("Vehicle.phoenix_amv_wheel_front:")[1].split("Vehicle.")[0]
        self.assertIn("isHandBrake: false", front)
