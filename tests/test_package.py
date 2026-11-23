#!/usr/bin/env python3
"""
Tests for tools/package.py — the installable folder must look like a normal
Cyberpunk 2077 mod (game-root mirror, nothing else).

Run:  python3 -m unittest discover -s tests -v
"""

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import package as pkg  # noqa: E402

DELIVERABLE = ROOT / "Phoenix_aston_cheats"

MINIMAL = {
    "archive/pc/mod/phoenix_aston_valkyrie.archive": b"RDAR",
    "archive/pc/mod/phoenix_aston_valkyrie.archive.xl": b"localization:\n",
    "r6/tweaks/phoenix/phoenix_aston_valkyrie.yaml": b"Vehicle.phoenix_x:\n",
    "r6/scripts/phoenix_aston_valkyrie/phoenix_aston_valkyrie.reds": b"// ok\n",
}


def make_mod(tmp: Path, files: dict[str, bytes]) -> Path:
    mod = tmp / "Mod"
    for rel, data in files.items():
        path = mod / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return mod


def errors_for(files: dict[str, bytes]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        mod = make_mod(Path(tmp), files)
        errors, _warnings = pkg.validate(mod)
        return errors


class ShippedLayoutTests(unittest.TestCase):
    def test_deliverable_is_norm_clean(self):
        errors, warnings = pkg.validate(DELIVERABLE)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_only_game_root_folders(self):
        top = sorted(p.name for p in DELIVERABLE.iterdir())
        self.assertEqual(top, ["archive", "r6"])

    def test_no_red4ext_bank_duplicate(self):
        self.assertFalse((DELIVERABLE / "red4ext").exists(),
                         "the stock AudioXL bank is shared on purpose")

    def test_archive_pair_named_alike(self):
        mod_dir = DELIVERABLE / "archive" / "pc" / "mod"
        self.assertEqual(sorted(p.name for p in mod_dir.iterdir()),
                         ["phoenix_aston_valkyrie.archive",
                          "phoenix_aston_valkyrie.archive.xl"])


class ViolationTests(unittest.TestCase):
    def test_minimal_tree_is_valid(self):
        self.assertEqual(errors_for(dict(MINIMAL)), [])

    def test_note_inside_payload_is_an_error(self):
        files = dict(MINIMAL)
        files["archive/pc/mod/NOTE.md"] = b"hello"
        self.assertTrue(any("documentation inside the payload" in e
                            for e in errors_for(files)))

    def test_readme_at_root_is_an_error(self):
        files = dict(MINIMAL)
        files["README.txt"] = b"hello"
        self.assertTrue(any("would be copied into the game root" in e
                            for e in errors_for(files)))

    def test_tweak_must_be_in_author_folder(self):
        files = {k: v for k, v in MINIMAL.items() if "r6/tweaks" not in k}
        files["r6/tweaks/phoenix_aston_valkyrie.yaml"] = b"x: 1\n"
        self.assertTrue(any("tweak must be r6/tweaks" in e for e in errors_for(files)))

    def test_scripts_must_be_in_mod_folder(self):
        files = {k: v for k, v in MINIMAL.items() if "r6/scripts" not in k}
        files["r6/scripts/phoenix_aston_valkyrie.reds"] = b"// x\n"
        self.assertTrue(any("script must be r6/scripts" in e for e in errors_for(files)))

    def test_archive_without_xl_is_an_error(self):
        files = {k: v for k, v in MINIMAL.items() if not k.endswith(".archive.xl")}
        self.assertTrue(any("no matching .archive.xl" in e for e in errors_for(files)))

    def test_junk_and_tooling_rejected(self):
        files = dict(MINIMAL)
        files["r6/scripts/phoenix_aston_valkyrie/__pycache__/x.pyc"] = b"x"
        self.assertTrue(any("junk/tooling" in e for e in errors_for(files)))

    def test_empty_directory_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            mod = make_mod(Path(tmp), dict(MINIMAL))
            (mod / "r6" / "empty").mkdir()
            errors, _ = pkg.validate(mod)
            self.assertTrue(any("empty directory" in e for e in errors))

    def test_uppercase_name_warns(self):
        files = {k: v for k, v in MINIMAL.items() if "r6/tweaks" not in k}
        files["r6/tweaks/phoenix/Phoenix_Name.yaml"] = b"x: 1\n"
        with tempfile.TemporaryDirectory() as tmp:
            mod = make_mod(Path(tmp), files)
            errors, warnings = pkg.validate(mod)
            self.assertEqual(errors, [])
            self.assertTrue(any("lowercase ASCII" in w for w in warnings))


class ZipTests(unittest.TestCase):
    def test_zip_contains_exact_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "mod.zip"
            entries = pkg.build_zip(DELIVERABLE, out)
            with zipfile.ZipFile(out) as zf:
                names = sorted(zf.namelist())
            self.assertEqual(names, sorted(entries))
            self.assertTrue(all("\\" not in n for n in names))
            self.assertIn("archive/pc/mod/phoenix_aston_valkyrie.archive", names)
            self.assertIn("r6/tweaks/phoenix/phoenix_aston_valkyrie.yaml", names)
            self.assertFalse(any(n.endswith((".md", ".txt")) for n in names))

    def test_zip_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.zip", Path(tmp) / "b.zip"
            pkg.build_zip(DELIVERABLE, a)
            pkg.build_zip(DELIVERABLE, b)
            self.assertEqual(a.read_bytes(), b.read_bytes())


if __name__ == "__main__":
    unittest.main()
