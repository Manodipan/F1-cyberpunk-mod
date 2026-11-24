#!/usr/bin/env python3
"""
Guards for the Xaires's Car Manager compat patch (compat/xaires_car_manager/).

Two bugs shipped from this repo that a test would have caught:

  * v1 appended a bare `phoenix_aston_valkyrie`; `carOf()` hashes the string with
    TweakDBID.new() and compares it to the vehicle's GetRecordID(), which is the
    TweakDBID of the *full* name, so the Phoenix never resolved.
  * v2 was applied by a regex that replaced only `records = rec('xaires_aston_valkyrie')`
    and left the line's own comma behind, producing `end)(),,` — a Lua syntax error that
    stopped the whole manager from loading.

Both are cheap to check statically, so they get a test.

Run:  python3 -m unittest discover -s tests -v
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPAT = ROOT / "compat" / "xaires_car_manager"
REPATCH = COMPAT / "repatch.ps1"
README = COMPAT / "README.md"
DUMP = ROOT / "tools" / "dump-car-manager.ps1"


def canonical_from_script() -> str:
    text = REPATCH.read_text(encoding="utf-8")
    m = re.search(r'^\$canonical = "(.*)"\s*$', text, re.MULTILINE)
    assert m, "repatch.ps1 has no $canonical line"
    return m.group(1)


def canonical_from_readme() -> str:
    text = README.read_text(encoding="utf-8")
    for block in re.findall(r"```lua\n(.*?)```", text, re.DOTALL):
        line = block.strip()
        if "rec('phoenix_aston_valkyrie')" in line and "'Vehicle.phoenix_aston_valkyrie'" in line:
            return line
    raise AssertionError("README has no v3 lua block")


class TestCanonicalLine(unittest.TestCase):
    def setUp(self):
        self.line = canonical_from_script()

    def test_same_line_in_script_and_readme(self):
        """A doc that tells the user a different line than the script applies is a trap."""
        self.assertEqual(self.line, canonical_from_readme())

    def test_no_double_comma(self):
        """v2's failure mode: `end)(),,` is a Lua syntax error, the file stops loading."""
        self.assertTrue(self.line.endswith("),"), self.line[-40:])
        self.assertNotIn("),,", self.line)
        self.assertFalse(re.search(r",\s*,$", self.line))

    def test_balanced_parens_and_quotes(self):
        for open_c, close_c in (("(", ")"), ("[", "]")):
            self.assertEqual(self.line.count(open_c), self.line.count(close_c), open_c)
        self.assertEqual(self.line.count("'") % 2, 0, "unbalanced single quotes")

    def test_carries_both_id_forms(self):
        """rec() gives whatever convention the manager uses; the literal is the full name."""
        self.assertIn("rec('phoenix_aston_valkyrie')", self.line)
        self.assertIn("'Vehicle.phoenix_aston_valkyrie'", self.line)

    def test_keeps_the_stock_record(self):
        self.assertIn("rec('xaires_aston_valkyrie')", self.line)


class TestRepatchScript(unittest.TestCase):
    def setUp(self):
        self.text = REPATCH.read_text(encoding="utf-8")

    def test_refuses_to_write_a_double_comma(self):
        self.assertIn("),,", self.text, "the guard against v2's bug is gone")

    def test_rewrites_the_whole_line_not_a_slice(self):
        """v2 matched only the middle of the line; the trailing comma survived."""
        self.assertIn("$reStock", self.text)
        self.assertIn("$rePatched", self.text)
        self.assertIn("$lines[$i] = $indent + $canonical", self.text)

    def test_writes_utf8_without_bom(self):
        self.assertIn("UTF8Encoding($false)", self.text)

    def test_keeps_a_backup(self):
        self.assertIn("init.lua.prev", self.text)


class TestReadmeAdvice(unittest.TestCase):
    def setUp(self):
        self.text = README.read_text(encoding="utf-8")

    def test_does_not_hand_out_the_v1_one_liner(self):
        """v1's string is what made the stock Aston paint and the Phoenix not."""
        self.assertNotIn("$new = \"records = (function() local t = rec('xaires_aston_valkyrie') t[#t+1]", self.text)

    def test_points_at_the_script(self):
        self.assertIn("repatch.ps1", self.text)

    def test_warns_about_the_comma(self):
        self.assertIn(",,", self.text)


class TestDumpScript(unittest.TestCase):
    def setUp(self):
        self.text = DUMP.read_text(encoding="utf-8")

    def test_has_the_paint_sections(self):
        for section in ("PAINT APPLY CODE", "ARE THE TWO COLOURS IN THE PALETTE?",
                        "EVERY MENTION OF THE ASTON", "the rec() helper"):
            self.assertIn(section, self.text)

    def test_writes_the_small_paste_file(self):
        self.assertIn("paint_dump.txt", self.text)


if __name__ == "__main__":
    unittest.main()
