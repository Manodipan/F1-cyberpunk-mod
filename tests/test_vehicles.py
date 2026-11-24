#!/usr/bin/env python3
"""
Tests for tools/collect_vehicles.py — the vehicle reference corpus.

The self-checks run against the Phoenix's own YAML (always present). The corpus check
only runs when a corpus exists, so a fresh clone stays green.

Run:  python3 -m unittest discover -s tests -v
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import collect_vehicles as cv  # noqa: E402

PHOENIX = ROOT / "Phoenix_aston_cheats" / "r6" / "tweaks" / "phoenix" / "phoenix_aston_valkyrie.yaml"
CORPUS = ROOT / "reference" / "vehicles"


class TestProfile(unittest.TestCase):
    """The extractor must read the deliverable's own numbers correctly."""

    def setUp(self):
        self.row = cv.profile(PHOENIX)

    def test_finds_the_car(self):
        self.assertIsNotNone(self.row)

    def test_top_gear_is_the_500_kmh_ceiling(self):
        self.assertAlmostEqual(self.row["top"], 138.89, places=2)
        self.assertEqual(round(self.row["top"] * 3.6), 500)

    def test_gear_count(self):
        self.assertEqual(self.row["gears"], 8, "7 forward + reverse")

    def test_the_deciding_fields(self):
        self.assertEqual(self.row["airResistanceFactor"], "0.66")
        self.assertEqual(self.row["engineMaxTorque"], "1500")
        self.assertEqual(self.row["total_mass"], "1750")
        self.assertEqual(self.row["wheelTurnMaxAddPerSecond"], "137")
        self.assertEqual(self.row["turnUpdateMaxSpeedTurnMul"], "0.21")

    def test_vehicle_record_not_its_satellites(self):
        self.assertEqual(self.row["records"], ["Vehicle.phoenix_aston_valkyrie"])

    def test_ignores_non_vehicle_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "onscreens.yaml"
            p.write_text("localization:\n  onscreens: {}\n", encoding="utf-8")
            self.assertIsNone(cv.profile(p))


class TestIndex(unittest.TestCase):
    def test_writes_a_sorted_markdown_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            rows = cv.collect(ROOT / "Phoenix_aston_cheats" / "r6" / "tweaks", copy=True, dest=tmp)
            out = cv.write_index(rows, tmp)
            text = out.read_text(encoding="utf-8")
            self.assertIn("| km/h | m/s | gears |", text)
            self.assertIn("phoenix_aston_valkyrie", text)
            self.assertTrue((tmp / "phoenix" / "phoenix_aston_valkyrie.yaml").is_file(),
                            "--copy must keep the YAML")
            self.assertEqual(len(rows), 1)

    def test_index_from_corpus_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            cv.write_index(cv.collect(ROOT / "Phoenix_aston_cheats" / "r6" / "tweaks", True, tmp), tmp)
            again = cv.index_from_corpus(tmp)
            self.assertEqual(len(again), 1)
            self.assertAlmostEqual(again[0]["top"], 138.89, places=2)


class TestCommittedCorpus(unittest.TestCase):
    """Only meaningful once somebody has run the collector against a real game."""

    def test_committed_index_matches_the_corpus(self):
        if not any(CORPUS.rglob("*.yaml")):
            self.skipTest("no local corpus (run tools/collect_vehicles.py --copy)")
        index = CORPUS / "INDEX.md"
        self.assertTrue(index.is_file(), "corpus without INDEX.md - run make vehicles-index")
        r = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "collect_vehicles.py"), "--index-only", str(CORPUS)],
            capture_output=True, text=True, check=True,
        )
        self.assertIn("indexed", r.stdout)


if __name__ == "__main__":
    unittest.main()
