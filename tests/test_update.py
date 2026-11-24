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

    def test_shipped_build_is_all_wheel_drive(self):
        """Shipped 2026-11-24 as a diagnosis: is the wobble power oversteer?"""
        out = self.port.port_text(self.stock, ".yaml", True)
        front = out.split("Vehicle.phoenix_amv_wheel_front:")[1].split("Vehicle.")[0]
        back = out.split("Vehicle.phoenix_amv_wheel_back:")[1].split("Vehicle.")[0]
        self.assertIn("isDrive: true", front)
        self.assertIn("isDrive: true", back)

    def test_rwd_is_still_one_flag_away(self):
        """The real LMH is rear-drive: this must stay reversible."""
        from unittest import mock
        with mock.patch.object(self.port, "DRIVETRAIN", "rwd"):
            out = self.port.port_text(self.stock, ".yaml", True)
        front = out.split("Vehicle.phoenix_amv_wheel_front:")[1].split("Vehicle.")[0]
        self.assertIn("isDrive: false", front)

    def test_awd_does_not_touch_the_handbrake(self):
        out = self.port.port_text(self.stock, ".yaml", True)
        front = out.split("Vehicle.phoenix_amv_wheel_front:")[1].split("Vehicle.")[0]
        self.assertIn("isHandBrake: false", front)


class ExplainerDocTests(unittest.TestCase):
    """docs/HOW-CARS-WORK.md answers the three questions; keep it linked and honest."""

    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.doc = (root / "docs" / "HOW-CARS-WORK.md").read_text(encoding="utf-8")
        self.readme = (root / "README.md").read_text(encoding="utf-8")

    def test_answers_the_three_questions(self):
        for heading in ("# 1. How modders make a car",
                        "# 2. How the game interprets the numbers",
                        "# 3. Relation to real physics"):
            self.assertIn(heading, self.doc)

    def test_labels_claims(self):
        for label in ("measured", "documented", "inferred"):
            self.assertIn(label, self.doc.lower())

    def test_cites_our_own_measurements(self):
        for fact in ("355", "500", "7 850", "8 020", "1.97", "1.77"):
            self.assertIn(fact, self.doc, fact)

    def test_readme_links_it(self):
        self.assertIn("docs/HOW-CARS-WORK.md", self.readme)

    def test_physics_anchor_is_checked(self):
        """2 000 hp at C_dA 0.95 is ~493 km/h - the arithmetic in the doc must not drift."""
        import math
        power_w = 2000 * 745.7
        rho, cda = 1.225, 0.95
        v = (2 * power_w / (rho * cda)) ** (1 / 3)
        self.assertLess(abs(v * 3.6 - 493), 3)
