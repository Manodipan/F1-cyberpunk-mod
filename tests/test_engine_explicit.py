#!/usr/bin/env python3
"""
The experimental YAML must stay in sync with the tool that produces it, and must differ
from the deliverable in exactly one way. Same discipline as the port tool: generated file
== tool output, or the build is lying.

Run:  python3 -m unittest discover -s tests -v
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import engine_explicit as ee  # noqa: E402

EXPERIMENT = ROOT / "experiments" / "phoenix_engine_explicit.yaml"


def body_of(path: Path) -> str:
    """The generated file starts with a 6-line header."""
    return "\n".join(path.read_text(encoding="utf-8").split("\n")[6:])


class TestExplicitGears(unittest.TestCase):
    def setUp(self):
        self.src = ee.SRC.read_text(encoding="utf-8")
        self.out = ee.transform(self.src)

    def test_generated_file_is_current(self):
        self.assertTrue(EXPERIMENT.is_file(), "run `make experiment`")
        self.assertEqual(body_of(EXPERIMENT), self.out)

    def test_no_remove_or_append_left_in_the_engine(self):
        self.assertNotIn("!remove", self.out)
        engine = self.out[self.out.index("vehEngineData:"):]
        self.assertNotIn("!append", engine.split("\n\n")[0])

    def test_explicit_list_of_eight_gears(self):
        self.assertIn("gears: [ Vehicle.phoenix_amv_gear_r", self.out)
        line = [l for l in self.out.split("\n") if "gears: [" in l][0]
        self.assertEqual(line.count("Vehicle.phoenix_amv_gear_"), 8)

    def test_dealer_registration_survives(self):
        self.assertIn("- !append Vehicle.phoenix_aston_valkyrie", self.out)
        self.assertIn("- !append Vehicle.phoenix_aston_valkyrie_purchasable", self.out)

    def test_everything_outside_the_engine_block_is_identical(self):
        def outside_engine(text: str) -> list[str]:
            lines = text.split("\n")
            i = next(k for k, l in enumerate(lines) if "vehEngineData:" in l)
            j = next(k for k in range(i + 1, len(lines))
                     if lines[k] and not lines[k].startswith((" ", "#")))
            return lines[:i] + lines[j:]

        self.assertEqual(outside_engine(self.src), outside_engine(self.out))

    def test_deliverable_keeps_the_append_form(self):
        """The experiment must not leak into the shipped file."""
        self.assertIn("!append Vehicle.phoenix_amv_gear_7",
                      (ROOT / "Phoenix_aston_cheats" / "r6" / "tweaks" / "phoenix"
                       / "phoenix_aston_valkyrie.yaml").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
