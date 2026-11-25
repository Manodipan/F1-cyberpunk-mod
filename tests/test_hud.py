"""The CET HUD is Lua, so it can be executed here under stubbed CET APIs.

This is the first part of this project that is testable for real: the redscript could only be
inspected, so every mistake cost a restart. These tests load the actual init.lua with a fake
CET/ImGui/Game surface, drive it frame by frame, and assert on what it would draw - including the
failure modes (missing binding, missing method, unwritable settings).

The stubs copy the return shapes of shipping CET mods on purpose:
    ImGui.Checkbox / ImGui.DragFloat  ->  value, changed
    GetDisplayResolution()            ->  width, height
Getting that order wrong is a real bug the stubs now catch.

Run with a Lua-capable Python (pip install lupa); skipped otherwise.
"""
import os
import pathlib
import re
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
-- CET's sandbox exposes no `debug` library (LuaSandbox.cpp whitelist). Taking it away here means a
-- stray debug.getinfo/debug.traceback fails the tests instead of failing in the game.
debug = nil

_G.__events = {}
_G.__hotkeys = {}
_G.__texts = {}
_G.__pushes = 0
_G.__pops = 0
_G.__begins = 0
_G.__nativeSettings = nil

registerForEvent = function(event, fn) _G.__events[event] = fn end
registerHotkey = function(id, label, fn) _G.__hotkeys[id] = { label = label, fn = fn } end

GetDisplayResolution = function() return 1920, 1080 end

ImGuiWindowFlags = {
  NoDecoration = 1, NoTitleBar = 2, NoResize = 4, NoMove = 8, NoScrollbar = 16, NoCollapse = 32,
  AlwaysAutoResize = 64, NoSavedSettings = 128, NoFocusOnAppearing = 256, NoNav = 512,
  NoInputs = 1024,
}
ImGuiCol = { Text = 0 }

ImGui = {
  Begin = function(name, flags)
    _G.__begins = _G.__begins + 1
    _G.__begin = { name = name, flags = flags }
    return _G.__beginVisible ~= false
  end,
  End = function() _G.__ends = (_G.__ends or 0) + 1 end,
  Text = function(s) _G.__texts[#_G.__texts + 1] = s end,
  SetNextWindowPos = function(x, y) _G.__pos = { x = x, y = y } end,
  SetWindowFontScale = function(s) _G.__scale = s end,
  PushStyleColor = function(index, a, b, c, d)
    if _G.__failColour then error("no colour for you") end
    if type(index) ~= "number" then error("bad colour index") end
    if d ~= nil then _G.__pushes = _G.__pushes + 1 return end     -- 4-float form (BVFP)
    if type(a) == "number" then _G.__pushes = _G.__pushes + 1 return end  -- packed form
    error("bad colour args")
  end,
  PopStyleColor = function(n) _G.__pops = _G.__pops + (n or 1) end,
  GetIO = function() return { DisplaySize = { x = 1920, y = 1080 } } end,
  Separator = function() end,
  -- CET order: value first, changed second
  Checkbox = function(label, v)
    if _G.__checkboxNil then return nil, true end
    if _G.__clickCheckbox then return not v, true end
    return v, false
  end,
  DragFloat = function(label, v, step, low, high)
    if _G.__clickDrag then return low, true end
    if _G.__dragNil then return nil, true end
    return v, false
  end,
  Button = function() return false end,
  Selectable = function() return false end,
  BeginCombo = function() return false end,
  EndCombo = function() end,
  SetItemDefaultFocus = function() end,
}

_G.__velocity = 58.8
_G.__tpp = false
_G.__noVelocityMethods = false
_G.__noCameraManager = false
function makeVehicle()
  local veh = {
    IsPlayerDriver = function() return true end,
    GetWorldPosition = function() return { x = _G.__px or 0, y = 0, z = 0 } end,
  }
  if not _G.__noVelocityMethods then
    veh.GetLinearVelocity = function() return { x = _G.__velocity, y = 0, z = 0, w = 0 } end
    veh.GetWorldForward = function() return { x = 1, y = 1e-9, z = 0, w = 0 } end
  end
  if not _G.__noCameraManager then
    veh.GetCameraManager = function() return { IsTPPActive = function() return _G.__tpp end } end
  end
  return veh
end

Game = {
  GetPlayer = function() return {} end,
  ["GetMountedVehicle;GameObject"] = function() return _G.__vehicle end,
}
GetMod = function(name) return _G.__nativeSettings end
"""


@unittest.skipUnless(HAVE_LUA, "lupa not installed - Lua tests need it")
class HudLuaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        shutil.copy(INIT, self.tmp / "init.lua")
        # CET replaces io.open with one that resolves relative paths against the mod's own folder;
        # running from that folder reproduces the same resolution.
        self._cwd = os.getcwd()
        os.chdir(self.tmp)
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(STUBS)
        self.mod = self.lua.execute(f'return dofile("{self.tmp / "init.lua"}")')
        self.mod.start()

    def tearDown(self):
        os.chdir(self._cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def draw(self):
        self.lua.eval("_G.__events['onDraw']")()

    def texts(self):
        return [v for _, v in sorted(self.lua.eval("_G.__texts").items())]

    def ini(self):
        return (self.tmp / "settings.ini").read_text()

    # -- registration ------------------------------------------------------
    def test_it_registers_the_cet_events_and_both_hotkeys(self):
        events = self.lua.eval("_G.__events")
        for name in ("onInit", "onUpdate", "onDraw", "onOverlayOpen", "onOverlayClose"):
            self.assertIn(name, events, name)
        hotkeys = self.lua.eval("_G.__hotkeys")
        self.assertIn("PhoenixSpeedometer_ToggleHud", hotkeys)
        self.assertIn("PhoenixSpeedometer_ToggleLabels", hotkeys)

    def test_settings_are_written_next_to_the_mod_on_first_run(self):
        self.assertTrue((self.tmp / "settings.ini").is_file())
        text = self.ini()
        self.assertIn("slot1=", text)
        self.assertIn("enabled=", text)

    # -- digits ------------------------------------------------------------
    def test_three_significant_figures_whole_above_100(self):
        cases = {212.4: "212", 100.0: "100", 58.83: "58.8", 9.876: "9.88",
                 0.1714: "0.171", 0.01714: "0.0171", 0.0: "0", 999.6: "1000"}
        for value, expected in cases.items():
            got = self.mod.format(value)
            self.assertEqual(got, expected, f"format({value}) = {got!r}, want {expected!r}")

    def test_format_survives_a_non_number_and_nan(self):
        self.assertEqual(self.mod.format(None), "0")
        self.assertEqual(self.mod.format("banana"), "0")
        self.assertEqual(self.mod.format(float("nan")), "0")

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
        self.assertEqual(self.mod.render(58.8, self.mod.config()), "212 km/h   58.8 m/s")

    def test_units_can_be_hidden_and_a_slot_emptied(self):
        cfg = self.mod.config()
        cfg.showLabels = False
        self.assertEqual(self.mod.render(58.8, cfg), "212   58.8")
        cfg.slot2 = ""
        self.assertEqual(self.mod.render(58.8, cfg), "212")

    def test_an_unknown_unit_falls_back_to_ms(self):
        cfg = self.mod.config()
        cfg.slot1 = "furlongs"
        self.assertAlmostEqual(self.mod.factor("furlongs", 1.0), 1.0)

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
        self.assertIsNone(self.mod.mpsFromPosition(veh, 0.1))      # first sample: no delta yet
        self.lua.execute("_G.__px = 5.88")                        # 5.88 m in 0.1 s = 58.8 m/s
        self.assertAlmostEqual(self.mod.mpsFromPosition(veh, 0.1), 58.8, places=1)

    def test_a_bad_frame_delta_does_not_produce_a_speed(self):
        veh = self.lua.eval("makeVehicle()")
        self.assertIsNone(self.mod.mpsFromPosition(veh, 0))
        self.assertIsNone(self.mod.mpsFromPosition(veh, 2.0))

    def test_missing_velocity_methods_fall_through_to_the_fallback(self):
        self.lua.execute("_G.__noVelocityMethods = true; _G.__vehicle = makeVehicle(); _G.__px = 0")
        self.assertIsNone(self.mod.mpsFromVelocity(self.lua.eval("_G.__vehicle")))
        dt = 1 / 60
        self.mod.currentMps(dt)
        self.lua.execute("_G.__px = 1.0")                          # 1 m in one frame ~ 60 m/s
        mps = self.mod.currentMps(dt)
        mps = mps[0] if isinstance(mps, tuple) else mps      # (mps, vehicle)
        self.assertIsNotNone(mps)
        self.assertGreater(float(mps), 1.0)

    def test_first_person_detection(self):
        veh = self.lua.eval("makeVehicle()")
        self.lua.execute("_G.__tpp = false")
        self.assertTrue(self.mod.isFirstPerson(veh))
        self.lua.execute("_G.__tpp = true")
        self.assertFalse(self.mod.isFirstPerson(veh))

    def test_first_person_unknown_shows_rather_than_hides(self):
        self.lua.execute("_G.__noCameraManager = true")
        veh = self.lua.eval("makeVehicle()")
        self.assertIsNone(self.mod.isFirstPerson(veh))

    # -- HUD ---------------------------------------------------------------
    def test_hud_draws_the_text_when_driving(self):
        self.lua.execute("_G.__vehicle = makeVehicle()")
        self.draw()
        self.assertIn("212 km/h   58.8 m/s", self.texts())

    def test_hud_is_silent_when_no_vehicle(self):
        self.lua.execute("_G.__vehicle = nil")
        before = len(self.texts())
        self.draw()
        self.assertEqual(len(self.texts()), before)

    def test_hud_is_silent_when_parked_as_a_passenger(self):
        self.lua.execute("""_G.__vehicle = makeVehicle()
            _G.__vehicle.IsPlayerDriver = function() return false end""")
        before = len(self.texts())
        self.draw()
        self.assertEqual(len(self.texts()), before)

    def test_first_person_only_hides_in_third_person(self):
        self.lua.execute("_G.__vehicle = makeVehicle()")
        self.mod.config().fppOnly = True
        self.lua.execute("_G.__tpp = true")
        before = len(self.texts())
        self.draw()
        self.assertEqual(len(self.texts()), before)
        self.lua.execute("_G.__tpp = false")
        self.draw()
        self.assertIn("212 km/h   58.8 m/s", self.texts())

    def test_hotkey_toggles_the_hud_and_persists(self):
        self.lua.execute("_G.__vehicle = makeVehicle()")
        self.lua.eval("_G.__hotkeys")["PhoenixSpeedometer_ToggleHud"].fn()
        self.assertFalse(self.mod.config().enabled)
        before = len(self.texts())
        self.draw()
        self.assertEqual(len(self.texts()), before, "hidden HUD must draw nothing")
        self.assertIn("enabled=false", self.ini())

    def test_the_hud_window_cannot_take_input(self):
        """The readout is click-through: NoInputs must be part of the window flags."""
        self.lua.execute("_G.__vehicle = makeVehicle()")
        self.draw()
        flags = self.lua.eval("_G.__begin.flags")
        noinputs = self.lua.eval("ImGuiWindowFlags.NoInputs")
        self.assertEqual(int(flags) & int(noinputs), int(noinputs), "NoInputs missing from HUD flags")

    def test_hud_uses_the_cet_display_resolution(self):
        self.lua.execute("_G.__vehicle = makeVehicle()")
        self.draw()
        pos = self.lua.eval("_G.__pos")
        self.assertAlmostEqual(pos["x"], 1920 * 0.60, places=1)
        self.assertAlmostEqual(pos["y"], 1080 * 0.78, places=1)
        self.assertAlmostEqual(self.lua.eval("_G.__scale"), 2.2, places=2)

    def test_hud_still_draws_without_any_resolution_query(self):
        self.lua.execute("""_G.__vehicle = makeVehicle()
            GetDisplayResolution = nil
            ImGui.GetIO = function() return nil end""")
        self.draw()
        self.assertIn("212 km/h   58.8 m/s", self.texts(), "no position is better than no readout")

    def test_colour_pushes_and_pops_stay_balanced(self):
        self.lua.execute("_G.__vehicle = makeVehicle()")
        self.draw()
        self.assertEqual(self.lua.eval("_G.__pushes"), self.lua.eval("_G.__pops"))

    def test_a_failing_colour_api_does_not_leak_or_break_the_text(self):
        self.lua.execute("_G.__vehicle = makeVehicle(); _G.__failColour = true")
        self.draw()
        self.assertEqual(self.lua.eval("_G.__pushes"), 0)
        self.assertEqual(self.lua.eval("_G.__pops"), 0, "popping what was never pushed corrupts the style stack")
        self.assertIn("212 km/h   58.8 m/s", self.texts())

    def test_a_throwing_widget_still_closes_both_windows(self):
        """An ImGui window left open corrupts every later frame, so End must always run."""
        self.lua.execute("""_G.__vehicle = makeVehicle()
            ImGui.DragFloat = function() error("boom") end""")
        self.lua.eval("_G.__events['onOverlayOpen']")()
        self.draw()
        self.assertEqual(self.lua.eval("_G.__ends"), self.lua.eval("_G.__begins"))

    def test_a_throwing_imgui_does_not_escape_on_draw(self):
        self.lua.execute("""_G.__vehicle = makeVehicle()
            ImGui.Begin = function() error("no window") end""")
        self.draw()            # must not raise out of the event handler
        self.assertEqual(self.lua.eval("_G.__pushes"), self.lua.eval("_G.__pops"))

    # -- settings window ---------------------------------------------------
    def test_the_settings_window_only_draws_while_the_overlay_is_open(self):
        begins = self.lua.eval("_G.__begins")
        self.draw()
        self.assertEqual(self.lua.eval("_G.__begins"), begins)
        self.lua.eval("_G.__events['onOverlayOpen']")()
        self.draw()
        self.assertGreater(self.lua.eval("_G.__begins"), begins)

    def test_checkbox_uses_the_cet_value_first_order(self):
        """A click must write the new value, not the 'changed' flag."""
        self.lua.eval("_G.__events['onOverlayOpen']")()
        self.lua.execute("_G.__clickCheckbox = true")     # stub returns (not v, true)
        self.draw()
        self.assertFalse(self.mod.config().enabled, "clicking 'Show the HUD' should turn it off")
        self.lua.execute("_G.__clickCheckbox = false")

    def test_a_nil_returning_checkbox_never_nils_a_setting(self):
        self.lua.eval("_G.__events['onOverlayOpen']")()
        self.lua.execute("_G.__checkboxNil = true")
        self.draw()
        self.assertIsInstance(self.mod.config().enabled, bool)

    def test_a_nil_returning_drag_float_never_nils_a_setting(self):
        self.lua.eval("_G.__events['onOverlayOpen']")()
        self.lua.execute("_G.__dragNil = true")
        self.draw()
        self.assertIsInstance(self.mod.config().scale, float)
        self.assertGreater(self.mod.config().scale, 0)

    def test_drag_float_is_clamped_to_its_range(self):
        self.lua.eval("_G.__events['onOverlayOpen']")()
        self.lua.execute("_G.__clickDrag = true")         # stub returns the low bound
        self.draw()
        self.assertGreaterEqual(self.mod.config().scale, 0.5)
        self.assertGreaterEqual(self.mod.config().posX, 0.0)
        self.assertLessEqual(self.mod.config().posX, 1.0)

    def test_a_second_number_can_be_switched_off(self):
        self.assertTrue(self.mod.setSlot("slot2", ""))
        self.assertEqual(self.mod.config().slot2, "")
        self.assertEqual(self.mod.render(58.8, self.mod.config()), "212 km/h")

    def test_slot_setter_accepts_a_name_or_an_index(self):
        self.assertTrue(self.mod.setSlot("slot1", "knots"))
        self.assertEqual(self.mod.config().slot1, "knots")
        self.assertTrue(self.mod.setSlot("slot1", 2))       # Native Settings UI may pass an index
        self.assertEqual(self.mod.config().slot1, "km/h")
        self.assertFalse(self.mod.setSlot("slot1", "furlongs"))
        self.assertEqual(self.mod.config().slot1, "km/h")

    def test_native_settings_ui_is_optional_and_lenient(self):
        self.lua.execute("""_G.__nativeSettings = {
            addTab = function() end,
            addSubcategory = function() end,
            addToggle = function() end,
            addSelectorString = function(path, label, desc, values, default, cb)
                _G.__selectorCb = cb
            end,
        }""")
        mod = self.lua.execute(f'return dofile("{self.tmp / "init.lua"}")')
        mod.start()
        mod.setSlot("slot1", 3)                              # index form, as a guard
        self.assertEqual(mod.config().slot1, "mph")

    # -- persistence -------------------------------------------------------
    def test_settings_round_trip(self):
        cfg = self.mod.config()
        cfg.slot1 = "knots"
        cfg.scale = 3.1
        self.assertTrue(self.mod.saveSettings())
        cfg.slot1 = "m/s"
        cfg.scale = 1.0
        self.mod.loadSettings()
        self.assertEqual(cfg.slot1, "knots")
        self.assertAlmostEqual(cfg.scale, 3.1, places=3)

    def test_a_hand_edited_settings_file_cannot_hide_the_hud(self):
        (self.tmp / "settings.ini").write_text(
            "scale=99\nposX=5.5\nposY=-3\ncolorR=9\nslot1=furlongs\nslot2=nonsense\n")
        self.mod.loadSettings()
        cfg = self.mod.config()
        self.assertAlmostEqual(cfg.scale, 6.0, places=3)
        self.assertAlmostEqual(cfg.posX, 1.0, places=3)
        self.assertAlmostEqual(cfg.posY, 0.0, places=3)
        self.assertAlmostEqual(cfg.colorR, 1.0, places=3)
        self.assertEqual(cfg.slot1, "km/h", "unknown unit falls back instead of blanking the readout")
        self.assertEqual(cfg.slot2, "m/s")

    def test_a_corrupt_settings_line_is_ignored(self):
        (self.tmp / "settings.ini").write_text("slot1=knots\nbogus\nscale=notanumber\n")
        self.mod.loadSettings()
        self.assertEqual(self.mod.config().slot1, "knots")
        self.assertAlmostEqual(self.mod.config().scale, 2.2, places=2)   # default kept

    def test_an_unwritable_settings_file_is_reported_not_fatal(self):
        os.remove(self.tmp / "settings.ini")
        os.mkdir(self.tmp / "settings.ini")                 # a directory in the way: io.open fails
        self.assertFalse(self.mod.saveSettings())
        self.assertIsInstance(self.mod.config().enabled, bool)


class HudStaticTests(unittest.TestCase):
    """Checks that need no interpreter, so they also run without lupa."""

    def setUp(self):
        self.text = INIT.read_text(encoding="utf-8")
        stripped = []
        for line in self.text.splitlines():
            stripped.append(line.split("--")[0] if "--" in line else line)
        self.code = "\n".join(stripped)

    def test_it_is_a_cet_mod_and_not_redscript(self):
        self.assertTrue(INIT.is_file())
        self.assertIn('registerForEvent("onDraw"', self.text)
        self.assertIn("registerHotkey(", self.text)
        self.assertIn('Game["GetMountedVehicle;GameObject"]', self.text)
        self.assertNotIn("runtimeProperty", self.text)
        self.assertNotIn("wrapMethod", self.text)

    def test_the_widget_return_order_is_the_cet_one(self):
        """CET returns (value, changed). Assigning them the other way round breaks every control."""
        self.assertIn("local value, changed = ImGui.Checkbox(", self.text)
        self.assertIn("local value, changed = ImGui.DragFloat(", self.text)
        self.assertNotIn("changed, cfg.", self.text)

    def test_units_match_the_documented_factors(self):
        for pair in ('["m/s"] = 1.0', '["km/h"] = 3.6', '["mph"] = 2.23694',
                     '["knots"] = 1.94384', '["ft/s"] = 3.28084', '["Mach"] = 1.0 / 343.0'):
            self.assertIn(pair, self.text, pair)

    def test_lua_is_5_1_safe_for_cet(self):
        """CET runs LuaJIT: no integer division, no bitwise operators, no goto, no %d on floats."""
        for banned in (" // ", "<<", ">>", "goto ", "%d"):
            self.assertNotIn(banned, self.text, banned)

    def test_it_never_uses_the_debug_library(self):
        """CET's sandbox does not provide `debug`; guard() and the settings path must not need it."""
        code = self.code
        self.assertNotIn("debug.", code)
        self.assertNotIn("debug(", code)

    def test_it_only_uses_globals_cet_whitelists(self):
        """Derived from LuaSandbox.cpp: these are simply not in a CET mod's sandbox."""
        code = self.code
        # word boundaries matter: "os." would otherwise match "pos.x"
        for pattern in (r"\bos\s*\.", r"\brequire\s*\(", r"\bloadstring\b", r"\bloadfile\s*\(",
                        r"\bdofile\s*\(", r"\bgetfenv\b", r"\bsetfenv\b", r"\b_G\b",
                        r"\bpackage\s*\.", r"\bcoroutine\s*\.", r"\butf8\s*\.",
                        r"\bcollectgarbage\b"):
            self.assertIsNone(re.search(pattern, code), pattern)

    def test_the_overlay_can_blank_a_slot(self):
        self.assertIn('"off"', self.code.replace(" ", ""), "the selector needs an off entry")

    def test_the_enum_tables_are_the_cet_ones(self):
        """CET whitelists ImGuiWindowFlags and ImGuiCol; the C-style globals are not guaranteed."""
        self.assertIn("ImGuiWindowFlags", self.code)
        self.assertIn("ImGuiCol", self.code)
        self.assertNotIn("ImGuiCol_", self.code)
        self.assertNotIn("ImGuiWindowFlags_", self.code)

    def test_no_lua_5_2_only_functions(self):
        for banned in ("table.unpack(", "math.type(", "utf8."):
            self.assertNotIn(banned, self.text, banned)

    def test_it_lives_where_cet_expects(self):
        self.assertEqual(INIT.parent.name, "phoenix_true_speedometer")
        self.assertEqual(INIT.parent.parent.name, "mods")
        self.assertEqual(INIT.name, "init.lua")


if __name__ == "__main__":
    unittest.main()
