"""The CET HUD is Lua, so it can be executed here under stubbed CET APIs.

This is the first part of this project that is testable for real: the redscript could only be
inspected, so every mistake cost a restart. These tests load the actual init.lua with a fake
CET/ImGui/Game surface, drive it frame by frame, and assert on what it would draw.

Run with a Lua-capable Python (pip install lupa); skipped otherwise.
"""
import pathlib
import shutil
import tempfile
import unittest

try:
    from lupa import LuaRuntime
    HAVE_LUA = True
except Exception:                                    # pragma: no cover
    HAVE_LUA = False

ROOT = pathlib.Path(__file__).resolve().parents[1]
INIT = ROOT / "Phoenix_true_speedometer/mods/phoenix_true_speedometer/init.lua"

STUBS = r"""
_G.__events = {}
_G.__hotkeys = {}
_G.__texts = {}
_G.__frames = 0

registerForEvent = function(event, fn) _G.__events[event] = fn end
registerHotkey = function(id, label, fn) _G.__hotkeys[id] = { label = label, fn = fn } end

ImGuiWindowFlags = {
  NoTitleBar = 1, NoResize = 2, NoMove = 4, NoScrollbar = 8, NoCollapse = 16,
  AlwaysAutoResize = 32, NoSavedSettings = 64, NoFocusOnAppearing = 128, NoNav = 256,
}
ImGuiCol = { Text = 0 }

ImGui = {
  Begin = function(name, flags) _G.__begin = { name = name, flags = flags }; return true end,
  End = function() _G.__frames = _G.__frames + 1 end,
  Text = function(s) _G.__texts[#_G.__texts + 1] = s end,
  SetNextWindowPos = function(x, y) _G.__pos = { x = x, y = y } end,
  SetWindowFontScale = function(s) _G.__scale = s end,
  PushStyleColor = function() end,
  PopStyleColor = function() end,
  GetIO = function() return { DisplaySize = { x = 1920, y = 1080 } } end,
  Separator = function() end,
  Checkbox = function(label, v) return false, v end,
  DragFloat = function(label, v) return false, v end,
  Button = function() return false end,
  Selectable = function() return false end,
  BeginCombo = function() return false end,
  EndCombo = function() end,
  SetItemDefaultFocus = function() end,
}

-- a vehicle whose body speed is exactly 58.8 m/s forward
_G.__velocity = 58.8
_G.__vehicle = nil
function makeVehicle()
  return {
    GetLinearVelocity = function() return { x = _G.__velocity, y = 0, z = 0, w = 0 } end,
    GetWorldForward = function() return { x = 1, y = 1e-9, z = 0, w = 0 } end,
    IsPlayerDriver = function() return true end,
    GetWorldPosition = function() return { x = _G.__px or 0, y = 0, z = 0 } end,
    GetCameraManager = function() return { IsTPPActive = function() return _G.__tpp end } end,
  }
end

Game = {
  GetPlayer = function() return {} end,
  ["GetMountedVehicle;GameObject"] = function() return _G.__vehicle end,
}
GetMod = function() return nil end
"""


@unittest.skipUnless(HAVE_LUA, "lupa not installed - Lua tests need it")
class HudLuaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        shutil.copy(INIT, self.tmp / "init.lua")
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(STUBS)
        self.mod = self.lua.execute(f'return dofile("{self.tmp / "init.lua"}")')
        self.mod.start()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # -- registration ------------------------------------------------------
    def test_it_registers_the_cet_events_and_both_hotkeys(self):
        events = self.lua.eval("_G.__events")
        for name in ("onInit", "onDraw", "onOverlayOpen", "onOverlayClose"):
            self.assertIn(name, events, name)
        hotkeys = self.lua.eval("_G.__hotkeys")
        self.assertIn("PhoenixSpeedometer_ToggleHud", hotkeys)
        self.assertIn("PhoenixSpeedometer_ToggleLabels", hotkeys)

    def test_settings_are_written_next_to_the_mod(self):
        self.assertTrue((self.tmp / "settings.ini").is_file())
        text = (self.tmp / "settings.ini").read_text()
        self.assertIn("slot1=", text)
        self.assertIn("enabled=", text)

    # -- digits ------------------------------------------------------------
    def test_three_significant_figures_whole_above_100(self):
        cases = {212.4: "212", 100.0: "100", 58.83: "58.8", 9.876: "9.88",
                 0.1714: "0.171", 0.01714: "0.0171", 0.0: "0", 999.6: "1000"}
        for value, expected in cases.items():
            got = self.mod.format(value)
            self.assertEqual(got, expected, f"format({value}) = {got!r}, want {expected!r}")

    # -- conversion --------------------------------------------------------
    def test_unit_factors_and_labels(self):
        expected = {"m/s": (1.0, "m/s"), "km/h": (3.6, "km/h"), "mph": (2.23694, "mph"),
                    "knots": (1.94384, "kn"), "ft/s": (3.28084, "ft/s"), "Mach": (1 / 343.0, "Mach")}
        for unit, (factor, label) in expected.items():
            self.assertAlmostEqual(self.mod.factor(unit, 1.0), factor, places=6, msg=unit)
            self.assertEqual(self.mod.label(unit, 1.0), label, unit)

    def test_custom_factor_is_clamped(self):
        self.assertAlmostEqual(self.mod.factor("custom", 0.00001), 0.0001, places=9)
        self.assertAlmostEqual(self.mod.factor("custom", 5000.0), 1000.0, places=6)
        self.assertEqual(self.mod.label("custom", 0.06), "x0.06")

    def test_default_readout_is_kmh_and_ms(self):
        cfg = self.mod.config()
        text = self.mod.render(58.8, cfg)
        self.assertEqual(text, "212 km/h   58.8 m/s")

    def test_units_can_be_hidden_and_a_slot_emptied(self):
        cfg = self.mod.config()
        cfg.showLabels = False
        self.assertEqual(self.mod.render(58.8, cfg), "212   58.8")
        cfg.slot2 = ""
        self.assertEqual(self.mod.render(58.8, cfg), "212")

    # -- speed -------------------------------------------------------------
    def test_speed_comes_from_body_velocity(self):
        veh = self.lua.eval("makeVehicle()")
        self.assertAlmostEqual(self.mod.mpsFromVelocity(veh), 58.8, places=3)

    def test_reverse_travel_reads_positive(self):
        self.lua.execute("_G.__velocity = -30.0")
        veh = self.lua.eval("makeVehicle()")
        self.assertAlmostEqual(self.mod.mpsFromVelocity(veh), 30.0, places=3)

    def test_position_fallback_derives_speed(self):
        veh = self.lua.eval("makeVehicle()")
        self.lua.execute("_G.__px = 0")
        self.mod.mpsFromPosition(veh, 0.1)
        self.lua.execute("_G.__px = 5.88")          # 5.88 m in 0.1 s = 58.8 m/s
        got = self.mod.mpsFromPosition(veh, 0.1)
        self.assertAlmostEqual(got, 58.8, places=1)

    def test_first_person_detection(self):
        veh = self.lua.eval("makeVehicle()")
        self.lua.execute("_G.__tpp = false")
        self.assertTrue(self.mod.isFirstPerson(veh))
        self.lua.execute("_G.__tpp = true")
        self.assertFalse(self.mod.isFirstPerson(veh))

    # -- HUD ---------------------------------------------------------------
    def test_hud_draws_the_text_when_driving(self):
        self.lua.execute("_G.__vehicle = makeVehicle()")
        draw = self.lua.eval("_G.__events['onDraw']")
        draw(0.016)
        texts = self.lua.eval("_G.__texts")
        self.assertIn("212 km/h   58.8 m/s", list(texts.values()))

    def test_hud_is_silent_when_no_vehicle(self):
        self.lua.execute("_G.__vehicle = nil")
        draw = self.lua.eval("_G.__events['onDraw']")
        before = len(self.lua.eval("_G.__texts"))
        draw(0.016)
        self.assertEqual(len(self.lua.eval("_G.__texts")), before)

    def test_hotkey_toggles_the_hud_and_persists(self):
        self.lua.execute("_G.__vehicle = makeVehicle()")
        hotkeys = self.lua.eval("_G.__hotkeys")
        hotkeys["PhoenixSpeedometer_ToggleHud"].fn()
        self.assertFalse(self.mod.config().enabled)
        draw = self.lua.eval("_G.__events['onDraw']")
        before = len(self.lua.eval("_G.__texts"))
        draw(0.016)
        self.assertEqual(len(self.lua.eval("_G.__texts")), before, "hidden HUD must draw nothing")
        text = (self.tmp / "settings.ini").read_text()
        self.assertIn("enabled=false", text)

    def test_hud_uses_configured_position_and_scale(self):
        self.lua.execute("_G.__vehicle = makeVehicle()")
        self.lua.eval("_G.__events['onDraw']")(0.016)
        pos = self.lua.eval("_G.__pos")
        self.assertAlmostEqual(pos["x"], 1920 * 0.60, places=1)
        self.assertAlmostEqual(pos["y"], 1080 * 0.78, places=1)
        self.assertAlmostEqual(self.lua.eval("_G.__scale"), 2.2, places=2)

    # -- persistence -------------------------------------------------------
    def test_settings_round_trip(self):
        self.mod.config().slot1 = "knots"
        self.mod.config().scale = 3.1
        self.mod.saveSettings()
        self.mod.config().slot1 = "m/s"
        self.mod.config().scale = 1.0
        self.mod.loadSettings()
        self.assertEqual(self.mod.config().slot1, "knots")
        self.assertAlmostEqual(self.mod.config().scale, 3.1, places=3)

    def test_a_corrupt_settings_line_is_ignored(self):
        (self.tmp / "settings.ini").write_text("slot1=knots\nbogus\nscale=notanumber\n")
        self.mod.loadSettings()
        self.assertEqual(self.mod.config().slot1, "knots")
        self.assertAlmostEqual(self.mod.config().scale, 2.2, places=2)   # default kept

    def test_missing_native_settings_ui_is_not_fatal(self):
        # GetMod returns nil in the stubs; start() must still have completed
        self.assertTrue(self.mod.config().enabled is not None)


class HudStaticTests(unittest.TestCase):
    """Checks that need no interpreter, so they also run without lupa."""

    def setUp(self):
        self.text = INIT.read_text(encoding="utf-8")

    def test_it_is_a_cet_mod_and_not_redscript(self):
        self.assertTrue(INIT.is_file())
        self.assertIn('registerForEvent("onDraw"', self.text)
        self.assertIn("registerHotkey(", self.text)
        self.assertIn('Game["GetMountedVehicle;GameObject"]', self.text)
        self.assertNotIn("runtimeProperty", self.text)
        self.assertNotIn("wrapMethod", self.text)

    def test_every_risky_cet_call_is_guarded(self):
        """A nil CET or game function must degrade, never throw out of onDraw."""
        for snippet in ("pcall(function()\n    return veh:GetLinearVelocity()",
                        "pcall(function()\n    return veh:GetCameraManager()",
                        "pcall(function()\n    return ImGui.Begin(",
                        "pcall(function()\n      ImGui.Text(text)"):
            self.assertIn(snippet, self.text, snippet)

    def test_units_match_the_documented_factors(self):
        for pair in ('["m/s"] = 1.0', '["km/h"] = 3.6', '["mph"] = 2.23694',
                     '["knots"] = 1.94384', '["ft/s"] = 3.28084', '["Mach"] = 1.0 / 343.0'):
            self.assertIn(pair, self.text, pair)

    def test_lua_is_5_1_safe_for_cet(self):
        """CET runs LuaJIT: no integer division, no bitwise operators, no goto."""
        for banned in (" // ", "<<", ">>", "goto "):
            self.assertNotIn(banned, self.text, banned)

    def test_it_lives_where_cet_expects(self):
        self.assertEqual(INIT.parent.name, "phoenix_true_speedometer")
        self.assertEqual(INIT.parent.parent.name, "mods")


if __name__ == "__main__":
    unittest.main()
