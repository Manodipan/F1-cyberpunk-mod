#!/usr/bin/env python3
"""
Tests for tools/package.py — the installable folder must look like a normal
Cyberpunk 2077 mod (game-root mirror, nothing else).

Run:  python3 -m unittest discover -s tests -v
"""

import subprocess
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
    return check(files)[0]


def check(files: dict[str, bytes]) -> tuple[list[str], list[str]]:
    with tempfile.TemporaryDirectory() as tmp:
        mod = make_mod(Path(tmp), files)
        return pkg.validate(mod)


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

    def test_archive_without_xl_warns_but_is_legal(self):
        """Asset-only archives (the packed onscreens file) need no loader config."""
        files = {k: v for k, v in MINIMAL.items() if not k.endswith(".archive.xl")}
        errors, warnings = check(files)
        self.assertEqual(errors, [])
        self.assertTrue(any("no matching .archive.xl" in w for w in warnings))

    def test_xl_without_archive_is_still_an_error(self):
        files = {k: v for k, v in MINIMAL.items() if not k.endswith(".archive")}
        self.assertTrue(any("has no matching .archive" in e for e in errors_for(files)))

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


class InspectArchiveTests(unittest.TestCase):
    """tools/inspect_archive.py is the no-WolvenKit proof that the strings landed."""

    B = "\\"

    def run_tool(self, archive: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(ROOT / "tools" / "inspect_archive.py"),
                               str(archive), *args], capture_output=True, text=True)

    def test_shipped_archive_has_no_onscreens_yet(self):
        """Documents today's state: the texture archive carries no .json resource."""
        r = self.run_tool(DELIVERABLE / "archive" / "pc" / "mod" / "phoenix_aston_valkyrie.archive",
                          "--json-only")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("0 of them .json", r.stdout)

    def test_expected_path_found_and_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "phoenix_strings.archive"
            want = self.B.join(["phoenix", "aston_valkyrie", "en-us.json"])
            fake.write_bytes(b"RDAR" + b"\x00" * 16 + want.encode())
            ok = self.run_tool(fake, "--json-only", "--expect", want)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertIn("is in the archive", ok.stdout)
            bad = self.run_tool(fake, "--expect", want.replace("en-us", "de-de"))
            self.assertEqual(bad.returncode, 1)
            self.assertIn("MISSING", bad.stderr)

    def test_grep_finds_and_reports_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            cr2w = Path(tmp) / "en-us.json"     # a bare CR2W, not an archive
            cr2w.write_bytes(b"CR2W" + b"\x00" * 8 + b"phoenix_aston_valkyrie_name")
            hit = self.run_tool(cr2w, "--grep", "phoenix_aston_valkyrie_name")
            self.assertEqual(hit.returncode, 0, hit.stderr)
            self.assertIn("1 hit(s)", hit.stdout)
            miss = self.run_tool(cr2w, "--grep", "nope_missing")
            self.assertEqual(miss.returncode, 1)
            self.assertIn("not found", miss.stderr)

    def test_not_an_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            junk = Path(tmp) / "nope.archive"
            junk.write_bytes(b"not an archive")
            self.assertEqual(self.run_tool(junk).returncode, 2)


if __name__ == "__main__":
    unittest.main()
