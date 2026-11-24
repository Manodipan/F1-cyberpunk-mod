#!/usr/bin/env python3
"""The comparison table is generated: keep it true, and keep the cars in it parsed."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import compare_vehicles as cv


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.cars = [(name, cv.load(ROOT / rel), note) for name, rel, note in cv.CARS]
        self.doc = cv.build()

    def test_every_car_parses(self):
        for name, row, _note in self.cars:
            self.assertIsNotNone(row, f"{name} did not parse as a vehicle tweak")
            self.assertTrue(row["ladder"], f"{name} has no forward gears")
            self.assertGreater(float(row["top"]), 0)

    def test_forward_ladder_excludes_reverse(self):
        for name, row, _note in self.cars:
            self.assertIsNotNone(row["reverse"], f"{name}: reverse not found")
            for gear in row["ladder"]:
                self.assertNotRegex(gear["name"], r"(_|gear)(r|0)$", name)

    def test_every_reference_car_is_in_the_table(self):
        names = [name for name, _rel, _note in cv.CARS]
        self.assertEqual(len(names), 5)
        for name in names:
            self.assertIn(name, self.doc)

    def test_committed_doc_is_current(self):
        committed = (ROOT / "docs" / "VEHICLE-COMPARISON.md").read_text(encoding="utf-8")
        self.assertEqual(committed, self.doc,
                         "docs/VEHICLE-COMPARISON.md is stale - run `make compare`")

    def test_phoenix_top_window_is_within_reference_range(self):
        """1.80x is what failed; 1.43 is what the shift-overlap rule requires (see test_port).

        AUDIT FIX (2026-11-24): this used to demand `torqueMultiplier >= 0.22` on the grounds that
        "the Jesko ships 0.227". That was a category error - a multiplier is only meaningful as a
        *ratio against that gear's own maxSpeed*, and the constant is per car (Aston ~27.9,
        Jesko ~18). A 215 m/s top gear on an Aston therefore wants ~0.13, and demanding 0.22 would
        have shipped 1.7x the designed thrust. The invariant that matters is the product, and
        `test_port.StockBaseDrivetrainTests` pins it against gears 4-7."""
        phoenix = dict((n, r) for n, r, _ in self.cars)["Phoenix AMV LMH"]
        top = phoenix["ladder"][-1]
        self.assertLessEqual(top["maxSpeed"] / top["minSpeed"], 1.60)
        product = top["torqueMultiplier"] * top["maxSpeed"]
        self.assertGreater(product, 20.0)     # the Aston's own family is 26.8-28.0
        self.assertLess(product, 32.0)


if __name__ == "__main__":
    unittest.main()
