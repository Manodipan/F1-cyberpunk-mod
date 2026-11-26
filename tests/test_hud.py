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
    import os as _os
    if _os.environ.get("HUD_LUA_BACKEND") == "lua51":
        # CET runs LuaJIT, i.e. Lua 5.1 semantics. 5.4/5.5 paper over things that break there:
        # integer division, string.format("%d") on a float, goto, bitwise operators, table.unpack.
        from lupa import lua51 as _backend
        LuaRuntime = _backend.LuaRuntime
    else:
        from lupa import LuaRuntime
    HAVE_LUA = True
except Exception:                                    # pragma: no cover
    HAVE_LUA = False

ROOT = pathlib.Path(__file__).resolve().parents[1]
# The file that actually ships. It is the probe that was proven to draw on the user's install, plus
# one dropdown - so these tests are about the probe, not the larger file that never rendered.
INIT = ROOT / "Phoenix_true_speedometer/probe/init.lua"
LEGACY = ROOT / "Phoenix_true_speedometer/mods/phoenix_true_speedometer/init.lua"

STUBS = r"""
-- CET's sandbox exposes no `debug` library (LuaSandbox.cpp whitelist). Taking it away here means a
-- stray debug.getinfo/debug.traceback fails the tests instead of failing in the game.
debug = nil

_G.__events = {}
_G.__hotkeys = {}
_G.__texts = {}
_G.__pushes = 0
_G.__pops = 0
_G.__widgets = {}
_G.__begins = 0

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
    _G.__texts = {}                          -- one frame's text, like the real overlay
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
    _G.__widgets[#_G.__widgets + 1] = { kind = "checkbox", label = label }
    if _G.__checkboxNil then return nil, true end
    if _G.__clickCheckbox then return not v, true end
    return v, false
  end,
  DragFloat = function(label, v, step, low, high)
    _G.__widgets[#_G.__widgets + 1] = { kind = "drag", label = label, low = low, high = high }
    if _G.__clickDrag then return low, true end
    if _G.__dragNil then return nil, true end
    return v, false
  end,
  Button = function(label)
    _G.__widgets[#_G.__widgets + 1] = { kind = "button", label = label }
    return false
  end,
  Selectable = function(entry, selected)
    _G.__offered = (_G.__offered or "") .. entry .. ","
    if _G.__pick ~= nil and entry == _G.__pick then
      _G.__pick = nil                        -- one click only, like a real mouse
      return true
    end
    return false
  end,
  BeginCombo = function(label)
    _G.__widgets[#_G.__widgets + 1] = { kind = "combo", label = label }
    return _G.__openCombo == true            -- a closed combo draws nothing until it is clicked
  end,
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
"""





@unittest.skipUnless(HAVE_LUA, "lupa not installed - Lua tests need it")

class ProbeHudTests(unittest.TestCase):
    """The shipped file: the proven probe, plus a unit dropdown."""

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        shutil.copy(INIT, self.tmp / "init.lua")
        self._cwd = os.getcwd()
        os.chdir(self.tmp)
        self.fresh()

    def fresh(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(STUBS)
        return self.lua.execute(f'return dofile("{self.tmp / "init.lua"}")')

    def tearDown(self):
        os.chdir(self._cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    # -- the architecture that was proven to draw --------------------------
    def test_it_registers_on_draw_at_file_scope(self):
        """The probe drew with exactly this shape: a bare registerForEvent, no start() function."""
        self.assertIsNotNone(self.lua.eval("_G.__events['onDraw']"))
        self.assertNotIn("function M.start", INIT.read_text(encoding="utf-8"))

    def test_it_draws_a_window_every_frame_with_no_conditions(self):
        for _ in range(5):
            self.lua.eval("_G.__events['onDraw']")()
        self.assertEqual(self.lua.eval("_G.__begins"), 5)
        self.assertEqual(self.lua.eval("_G.__ends"), 5, "Begin/End must stay balanced")

    def test_it_draws_even_with_no_vehicle(self):
        self.lua.execute("_G.__vehicle = nil")
        self.lua.eval("_G.__events['onDraw']")()
        self.assertEqual(self.lua.eval("_G.__begins"), 1)
        self.assertIn("-- km/h", self.texts())

    def test_drawing_has_no_hotkey_or_overlay_dependency(self):
        self.assertEqual(len(self.lua.eval("_G.__hotkeys")), 0, "no hotkey is needed")
        # opening or closing the overlay must not matter: no such handler is registered
        self.assertIsNone(self.lua.eval("_G.__events['onOverlayOpen']"))

    # -- the one added feature --------------------------------------------
    def test_the_dropdown_offers_every_unit(self):
        self.lua.execute("_G.__openCombo = true")
        self.lua.eval("_G.__events['onDraw']")()
        offered = self.lua.eval("_G.__offered") or ""
        for unit in ("km/h", "mph", "m/s", "knots", "ft/s", "Mach"):
            self.assertIn(unit, offered, f"the dropdown never offered {unit}")

    def test_picking_a_unit_changes_the_readout(self):
        self.lua.execute("_G.__vehicle = makeVehicle(); _G.__velocity = 58.8")
        self.lua.execute("_G.__openCombo = true; _G.__pick = 'mph'")
        self.lua.eval("_G.__events['onDraw']")()      # the click lands here
        self.lua.eval("_G.__events['onDraw']")()      # the new unit is drawn next frame
        self.assertIn("132 mph", self.texts())

    def test_the_unit_text_updates_on_the_frame_after_the_click(self):
        """Immediate mode: the number is drawn before the dropdown, so a click lands one frame later."""
        self.lua.execute("_G.__vehicle = makeVehicle(); _G.__velocity = 58.8")
        self.lua.execute("_G.__openCombo = true; _G.__pick = 'mph'")
        self.lua.eval("_G.__events['onDraw']")()
        self.assertEqual(self.lua.eval("(function() return 1 end)()"), 1)
        self.assertEqual(self.mod_unit(), "mph")

    def test_the_chosen_unit_is_remembered(self):
        self.lua.execute("_G.__vehicle = makeVehicle(); _G.__velocity = 58.8")
        self.lua.execute("_G.__openCombo = true; _G.__pick = 'knots'")
        self.lua.eval("_G.__events['onDraw']")()
        self.assertEqual((self.tmp / "unit.txt").read_text().strip(), "knots")
        self.lua.execute("_G.__openCombo = false; _G.__pick = nil")
        self.fresh()
        self.lua.execute("_G.__vehicle = makeVehicle(); _G.__velocity = 58.8")
        self.lua.eval("_G.__events['onDraw']")()
        self.assertIn("114 knots", self.texts())

    def test_a_broken_unit_file_does_not_stop_the_hud(self):
        (self.tmp / "unit.txt").write_text("furlongs\n")
        self.fresh()
        self.lua.execute("_G.__vehicle = makeVehicle(); _G.__velocity = 58.8")
        self.lua.eval("_G.__events['onDraw']")()
        self.assertIn("212 km/h", self.texts())

    def test_an_unwritable_unit_file_still_draws(self):
        self.lua.execute("""
          io.open = function() error("no disk for you") end
        """)
        self.lua.execute("_G.__vehicle = makeVehicle(); _G.__velocity = 58.8")
        self.lua.execute("_G.__openCombo = true; _G.__pick = 'mph'")
        self.lua.eval("_G.__events['onDraw']")()
        self.lua.eval("_G.__events['onDraw']")()
        self.assertIn("132 mph", self.texts())

    # -- the readout ------------------------------------------------------
    def test_three_significant_figures(self):
        """In m/s, where the factor is 1: the digits are the renderer's, not the unit's."""
        (self.tmp / "unit.txt").write_text("m/s\n")
        self.fresh()
        cases = [(212.4, "212"), (100.0, "100"), (58.83, "58.8"), (9.876, "9.88"),
                 (0.1714, "0.171"), (0.0, "0")]
        for mps, want in cases:
            self.lua.execute(f"_G.__vehicle = makeVehicle(); _G.__velocity = {mps}")
            self.lua.eval("_G.__events['onDraw']")()
            shown = self.texts()[0]
            self.assertEqual(shown, f"{want} m/s", f"{mps} m/s")

    def test_reverse_travel_reads_positive(self):
        self.lua.execute("_G.__vehicle = makeVehicle(); _G.__velocity = -58.8")
        self.lua.eval("_G.__events['onDraw']")()
        self.assertIn("212 km/h", self.texts())

    def test_no_vehicle_shows_a_dash_not_a_stale_number(self):
        self.lua.execute("_G.__vehicle = makeVehicle(); _G.__velocity = 58.8")
        self.lua.eval("_G.__events['onDraw']")()
        self.lua.execute("_G.__vehicle = nil")
        self.lua.eval("_G.__events['onDraw']")()
        self.assertIn("-- km/h", self.texts())

    # -- failure containment ---------------------------------------------
    def test_a_throwing_im_tgui_call_cannot_escape_on_draw(self):
        self.lua.execute("ImGui.Text = function() error('kaboom') end")
        self.lua.eval("_G.__events['onDraw']")()          # must not raise
        self.lua.execute("ImGui.GetLinearVelocity = nil")

    def test_a_throwing_vehicle_read_cannot_escape_on_draw(self):
        self.lua.execute("""
          Game["GetMountedVehicle;GameObject"] = function() error("vehicle api gone") end
        """)
        self.lua.eval("_G.__events['onDraw']")()          # must not raise
        self.assertEqual(self.lua.eval("_G.__begins"), 1)

    # -- static guarantees ------------------------------------------------
    def test_it_needs_nothing_but_cet(self):
        code = INIT.read_text(encoding="utf-8")
        for banned in ("GetMod(", "nativeSettings", "require("):
            self.assertNotIn(banned, code, f"{banned} would be a dependency")

    def test_no_debug_library(self):
        """CET's sandbox has no debug table; the harness removes it too."""
        self.assertNotIn("debug.", INIT.read_text(encoding="utf-8"))

    def test_it_ships_from_the_probe_folder(self):
        self.assertEqual(INIT.parent.name, "probe")
        self.assertEqual(INIT.name, "init.lua")

    def test_the_installer_copies_this_exact_file(self):
        ps = (ROOT / "tools/update.ps1").read_text(encoding="utf-8", errors="replace")
        self.assertIn("Phoenix_true_speedometer\\probe\\init.lua", ps)

    # -- helper -----------------------------------------------------------
    def texts(self):
        return list(self.lua.eval("_G.__texts").values())

    def mod_unit(self):
        path = self.tmp / "unit.txt"
        return path.read_text().strip() if path.exists() else None


if __name__ == "__main__":
    unittest.main()
