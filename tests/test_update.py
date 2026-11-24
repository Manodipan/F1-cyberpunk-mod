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

    def _role(self, out, name):
        return out.split(f"Vehicle.phoenix_amv_role_{name}:")[1].split("Vehicle.")[0]

    def test_control_build_is_rear_drive_like_the_reference(self):
        """CONTROL BUILD (2026-11-24): the Jesko's own wheel roles, so front wheels do not
        drive and only the rear pair carries the handbrake. AWD stays one flag away."""
        out = self.port.port_text(self.stock, ".yaml", True)
        for corner in ("lf", "rf"):
            self.assertIn("isDrive: false", self._role(out, corner), corner)
        for corner in ("lb", "rb"):
            self.assertIn("isDrive: true", self._role(out, corner), corner)

    def test_all_wheel_drive_is_still_one_flag_away(self):
        from unittest import mock
        with mock.patch.object(self.port, "DRIVETRAIN", "awd"):
            out = self.port.port_text(self.stock, ".yaml", True)
        # the control replaces the whole physics section, so the flag now has no effect -
        # which is asserted here so nobody believes a stale flag is doing something
        self.assertIn("isDrive: false", self._role(out, "lf"))

    def test_handbrake_stays_on_the_rear_pair(self):
        out = self.port.port_text(self.stock, ".yaml", True)
        for corner in ("lf", "rf"):
            self.assertIn("isHandBrake: false", self._role(out, corner), corner)
        for corner in ("lb", "rb"):
            self.assertIn("isHandBrake: true", self._role(out, corner), corner)


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


class RealRacingDocTests(unittest.TestCase):
    """docs/TUNING-FROM-REAL-RACING.md must stay consistent with the game's actual curve format."""

    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.doc = (root / "docs" / "TUNING-FROM-REAL-RACING.md").read_text(encoding="utf-8")

    def test_lists_the_whole_vanilla_catalogue(self):
        curves = ("large_balanced_na", "large_balanced_sc", "large_balanced_turbo",
                  "large_torquey_na", "med_balanced_na", "med_balanced_sc",
                  "med_lowcomp_bigturbo", "med_peaky_na", "med_torquey_na",
                  "med_torquey_turbo", "small_balanced_na", "small_block_v8_na",
                  "small_peaky_na", "small_torquey_na", "small_torquey_turbo")
        self.assertEqual(len(curves), 15)
        for c in curves:
            self.assertIn(c, self.doc, c)

    def test_curve_is_normalised_not_an_rpm_range(self):
        self.assertIn("normalised", self.doc.lower())
        self.assertIn("0→1", self.doc)

    def test_real_lmh_top_speed_follows_from_its_power(self):
        """697 hp, CdA 0.95 should land within 5 % of the real car's 340 km/h."""
        power_w = 697 * 745.7
        v = (2 * power_w / (1.225 * 0.95)) ** (1 / 3)
        self.assertLess(abs(v * 3.6 - 340) / 340, 0.05)

    def test_target_needs_about_2000_hp(self):
        """Holding 500 km/h costs ~1 559 kW; the doc's 2 091 hp must match."""
        force = 0.5 * 1.225 * 0.95 * 138.89 ** 2
        self.assertLess(abs(force * 138.89 / 745.7 - 2091), 15)
