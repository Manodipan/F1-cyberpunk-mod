-- Phoenix True Speedometer - standalone CET HUD
--
-- Why this exists: replacing the game's HUD speed number means fighting a widget built for about
-- four characters, next to a km/h label that belongs to the game and cannot be changed. This draws
-- its own HUD instead - no redscript, no compile step, and nothing of the vanilla HUD is touched.
--
-- Requires: Cyber Engine Tweaks only. If Native Settings UI is installed the same options appear in
-- the game's Mods menu; the CET overlay always has them.
--
-- CET API shapes here are copied from shipping CET mods, not guessed:
--   ImGui.Checkbox / ImGui.DragFloat  return  value, changed   (BetterVehicleFirstPerson,
--                                     CyberpunkVRPort_WristHud - both assign the FIRST return)
--   GetDisplayResolution()            returns screen width, height   (psiberx GameUI-WhereAmI)
--   registerForEvent("onUpdate", fn)  fn receives the frame delta    (BetterVehicleFirstPerson)
--   ImGuiWindowFlags.<Name> / ImGuiCol.<Name>   table-style enums    (BetterVehicleFirstPerson)
--
-- And from CET's own source, which is what a mod actually runs inside:
--   src/scripting/LuaSandbox.cpp   the sandbox exposes no `debug` library at all, so nothing here
--                                  may call debug.getinfo/debug.traceback; `io.open` is replaced
--                                  with one that resolves relative paths against THIS mod's folder
--   src/scripting/ScriptContext.cpp onDraw is called with no arguments; onUpdate gets the delta;
--                                  only onHook/onTweak/onInit/onShutdown/onUpdate/onDraw/
--                                  onOverlayOpen/onOverlayClose exist - any other name is an error
--
-- Exposed as the global PhoenixSpeedometer for inspection from the CET console.

local M = {}

-- ---------------------------------------------------------------------------
-- units
-- ---------------------------------------------------------------------------
local UNIT_ORDER = { "m/s", "km/h", "mph", "knots", "ft/s", "Mach", "custom" }

local FACTORS = {
  ["m/s"] = 1.0,
  ["km/h"] = 3.6,
  ["mph"] = 2.23694,
  ["knots"] = 1.94384,
  ["ft/s"] = 3.28084,
  ["Mach"] = 1.0 / 343.0,          -- Mach 1 = 343 m/s at sea level
}

local LABELS = {
  ["m/s"] = "m/s",
  ["km/h"] = "km/h",
  ["mph"] = "mph",
  ["knots"] = "kn",
  ["ft/s"] = "ft/s",
  ["Mach"] = "Mach",
}

-- ---------------------------------------------------------------------------
-- settings
-- ---------------------------------------------------------------------------
-- Defaults: the two numbers this mod was asked for in the first place, now that there is room for
-- them. Labels on, because nothing else on screen says which unit is which.
local DEFAULTS = {
  enabled = true,
  slot1 = "km/h",
  custom1 = 1.0,
  slot2 = "m/s",
  custom2 = 1.0,
  showLabels = true,
  fppOnly = false,
  scale = 2.2,
  posX = 0.60,
  posY = 0.78,
  colorR = 0.35,
  colorG = 0.95,
  colorB = 1.00,
  smooth = 0.25,
}

local cfg = {}
for k, v in pairs(DEFAULTS) do
  cfg[k] = v
end

local function reported(message)
  print("[Phoenix True Speedometer] " .. message)
end

local lastError = nil

-- runs fn, reports a distinct failure once: the CET console names it without spamming every frame
local function guard(what, fn)
  local ok, err = xpcall(fn, function(message)
    return tostring(message)               -- CET's sandbox has no debug library for traceback
  end)
  if not ok then
    if err ~= lastError then
      lastError = err
      reported(what .. " failed: " .. tostring(err))
    end
    return false
  end
  lastError = nil
  return true
end

-- CET's sandbox has no `debug` library and replaces io.open with one that resolves relative paths
-- against this mod's own folder, so a bare filename is both the simplest and the correct choice.
local SETTINGS_FILE = "settings.ini"

local function openSettings(mode)
  local ok, file = pcall(io.open, SETTINGS_FILE, mode)
  if ok and file then
    return file
  end
  return nil
end

local function encodeValue(v)
  if type(v) == "boolean" then
    return v and "true" or "false"
  end
  if type(v) == "number" then
    return string.format("%.6f", v)
  end
  return tostring(v)
end

function M.saveSettings()
  local file = openSettings("w")
  if not file then
    return false
  end
  for k, v in pairs(cfg) do
    file:write(k .. "=" .. encodeValue(v) .. "\n")
  end
  file:close()
  return true
end

local NUMERIC_LIMITS = {
  scale = { 0.5, 6.0 },
  posX = { 0.0, 1.0 },
  posY = { 0.0, 1.0 },
  colorR = { 0.0, 1.0 },
  colorG = { 0.0, 1.0 },
  colorB = { 0.0, 1.0 },
  smooth = { 0.02, 1.0 },
  custom1 = { 0.0001, 1000.0 },
  custom2 = { 0.0001, 1000.0 },
}

-- a typo in settings.ini should cost a colour, not an invisible HUD in the wrong place
local function clampSettings()
  for key, limits in pairs(NUMERIC_LIMITS) do
    local value = cfg[key]
    if type(value) ~= "number" or value ~= value then
      cfg[key] = DEFAULTS[key]
    else
      if value < limits[1] then
        cfg[key] = limits[1]
      elseif value > limits[2] then
        cfg[key] = limits[2]
      end
    end
  end
  -- "" (off) is a real setting for either slot: clamping it back to the default silently undid the
  -- user's choice on every restart
  if cfg.slot1 ~= "" and cfg.slot1 ~= "custom" and FACTORS[cfg.slot1] == nil then
    cfg.slot1 = DEFAULTS.slot1
  end
  if cfg.slot2 ~= "" and cfg.slot2 ~= "custom" and FACTORS[cfg.slot2] == nil then
    cfg.slot2 = DEFAULTS.slot2
  end
end

function M.loadSettings()
  local file = openSettings("r")
  if not file then
    return false
  end
  for line in file:lines() do
    local key, value = line:match("^([%w_]+)=(.*)$")
    if key and DEFAULTS[key] ~= nil then
      local default = DEFAULTS[key]
      if type(default) == "number" then
        local n = tonumber(value)
        if n then
          cfg[key] = n
        end
      elseif type(default) == "boolean" then
        cfg[key] = (value == "true")
      else
        cfg[key] = value
      end
    end
  end
  file:close()
  clampSettings()
  return true
end

function M.config()
  return cfg
end

function M.defaults()
  return DEFAULTS
end

-- ---------------------------------------------------------------------------
-- digits: three significant figures, whole numbers above 100
--   212.4 -> "212"   58.83 -> "58.8"   9.876 -> "9.88"   0.1714 -> "0.171"   0 -> "0"
-- ---------------------------------------------------------------------------
function M.format(value)
  local v = value
  if type(v) ~= "number" then
    return "0"
  end
  if v ~= v then                    -- NaN: never let "nan" reach the screen
    return "0"
  end
  if v < 0 then
    v = -v
  end
  if v >= 100 then
    return tostring(math.floor(v + 0.5))
  end
  local s = string.format("%.3g", v)
  if s:find("[eE]") then
    -- %.3g switches to exponent form for very small values; plain decimals read better
    s = string.format("%.5f", v)
  end
  return s
end

-- ---------------------------------------------------------------------------
-- conversion
-- ---------------------------------------------------------------------------
function M.factor(unit, custom)
  if unit == "custom" then
    local c = tonumber(custom) or 1.0
    if c < 0.0001 then
      c = 0.0001
    end
    if c > 1000 then
      c = 1000
    end
    return c
  end
  return FACTORS[unit] or 1.0
end

function M.label(unit, custom)
  if unit == "custom" then
    return "x" .. M.format(M.factor("custom", custom))
  end
  return LABELS[unit] or "m/s"
end

function M.slotText(mps, unit, custom, withLabel)
  if not unit or unit == "" then
    return nil
  end
  local number = M.format(mps * M.factor(unit, custom))
  if withLabel then
    return number .. " " .. M.label(unit, custom)
  end
  return number
end

function M.render(mps, c)
  local parts = {}
  local first = M.slotText(mps, c.slot1, c.custom1, c.showLabels)
  if first then
    parts[#parts + 1] = first
  end
  local second = M.slotText(mps, c.slot2, c.custom2, c.showLabels)
  if second then
    parts[#parts + 1] = second
  end
  if #parts == 0 then
    -- both slots deliberately blanked: honour that instead of quietly printing m/s, which made the
    -- unit look stuck. The caller still gets nil so nothing is drawn.
    return nil
  end
  return table.concat(parts, "   ")
end

-- ---------------------------------------------------------------------------
-- speed: the body's own velocity, not the game's curve-warped HUD number
-- ---------------------------------------------------------------------------
function M.mpsFromVelocity(veh)
  if not veh then
    return nil
  end
  local okV, vel = pcall(function()
    return veh:GetLinearVelocity()
  end)
  local okF, fwd = pcall(function()
    return veh:GetWorldForward()
  end)
  if not (okV and okF and vel and fwd) then
    return nil
  end
  local okDot, dot = pcall(function()
    return vel.x * fwd.x + vel.y * fwd.y + vel.z * fwd.z + vel.w * fwd.w
  end)
  if not okDot or type(dot) ~= "number" then
    return nil
  end
  if dot < 0 then
    dot = -dot
  end
  return dot
end

-- Fallback for the case where the velocity methods are not exposed to Lua: differentiate position.
local lastPos, smoothed = nil, nil

function M.mpsFromPosition(veh, dt)
  if not veh or type(dt) ~= "number" or dt <= 0 or dt > 0.5 then
    lastPos = nil
    return nil
  end
  local ok, pos = pcall(function()
    return veh:GetWorldPosition()
  end)
  if not ok or not pos then
    return nil
  end
  local mps = nil
  if lastPos then
    local dx, dy, dz = pos.x - lastPos.x, pos.y - lastPos.y, pos.z - lastPos.z
    local dist = math.sqrt(dx * dx + dy * dy + dz * dz)
    mps = dist / dt
  end
  lastPos = { x = pos.x, y = pos.y, z = pos.z }
  if mps then
    local a = cfg.smooth
    if type(a) ~= "number" then
      a = DEFAULTS.smooth
    end
    if a < 0.02 then
      a = 0.02
    end
    if a > 1 then
      a = 1
    end
    if smoothed then
      smoothed = smoothed + (mps - smoothed) * a
    else
      smoothed = mps
    end
  end
  return smoothed
end

-- true = first person, false = third person, nil = cannot tell (callers treat nil as "show")
function M.isFirstPerson(veh)
  if not veh then
    return nil
  end
  local ok, cam = pcall(function()
    return veh:GetCameraManager()
  end)
  if not ok or not cam then
    return nil
  end
  local okTpp, tpp = pcall(function()
    return cam:IsTPPActive()
  end)
  if not okTpp then
    return nil
  end
  return not tpp
end

-- ---------------------------------------------------------------------------
-- CET glue
-- ---------------------------------------------------------------------------
local overlayOpen = false
local lastMps = nil
local frameDt = 1.0 / 60.0

local function getVehicle()
  local ok, player = pcall(function()
    return Game.GetPlayer()
  end)
  if not ok or not player then
    return nil
  end
  local okVeh, veh = pcall(function()
    return Game["GetMountedVehicle;GameObject"](player)
  end)
  if not okVeh then
    return nil
  end
  return veh
end

local function isDriving(veh)
  if not veh then
    return false
  end
  local ok, driver = pcall(function()
    return veh:IsPlayerDriver()
  end)
  if ok then
    return driver and true or false
  end
  return true
end

function M.currentMps(dt)
  local veh = getVehicle()
  if not veh or not isDriving(veh) then
    return nil, nil
  end
  local mps = M.mpsFromVelocity(veh)
  if mps == nil then
    mps = M.mpsFromPosition(veh, dt)
  end
  if mps == nil then
    return nil, veh
  end
  return mps, veh
end

function M.hudText(dt)
  if cfg.enabled ~= true then
    return nil
  end
  local mps, veh = M.currentMps(dt or frameDt)
  if mps == nil then
    return nil
  end
  if cfg.fppOnly then
    local firstPerson = M.isFirstPerson(veh)
    -- nil means the camera query is unavailable: show the HUD rather than silently hiding it
    if firstPerson == false then
      return nil
    end
  end
  lastMps = mps
  return M.render(mps, cfg)
end

-- ---------------------------------------------------------------------------
-- ImGui
-- ---------------------------------------------------------------------------
local windowFlags = {}
-- CET whitelists ImGuiWindowFlags and ImGuiCol as tables (LuaSandbox.cpp), and every shipping mod
-- uses that spelling. Nothing here reaches through _G: the sandbox does not whitelist it.
local function windowFlag(name)
  local flags = ImGuiWindowFlags
  if type(flags) == "table" and type(flags[name]) == "number" then
    return flags[name]
  end
  return 0
end

local function flag(name)
  if windowFlags[name] == nil then
    windowFlags[name] = windowFlag(name)
  end
  return windowFlags[name]
end

local function hudFlags()
  -- NoInputs matters: it makes the readout provably click-through, so it can never eat a click or
  -- a keystroke even if some other CET mod or a future version changes how input is routed.
  return flag("NoDecoration") + flag("NoTitleBar") + flag("NoResize") + flag("NoMove")
    + flag("NoScrollbar") + flag("NoCollapse") + flag("AlwaysAutoResize")
    + flag("NoSavedSettings") + flag("NoFocusOnAppearing") + flag("NoNav") + flag("NoInputs")
end

local function screenSize()
  local ok, w, h = pcall(GetDisplayResolution)          -- CET global, used by shipping HUD mods
  if ok and type(w) == "number" and type(h) == "number" and w > 0 and h > 0 then
    return w, h
  end
  local okIo, io = pcall(function()
    return ImGui.GetIO()
  end)
  if okIo and io and io.DisplaySize then
    local size = io.DisplaySize
    if type(size.x) == "number" and type(size.y) == "number" then
      return size.x, size.y
    end
  end
  return nil, nil
end

local function textIndex()
  local colours = ImGuiCol
  if type(colours) == "table" and type(colours.Text) == "number" then
    return colours.Text
  end
  return nil
end

-- CET takes either 4 floats (BetterVehicleFirstPerson) or one packed 0xAABBGGRR (GameUI-WhereAmI).
local function pushTextColour()
  local index = textIndex()
  if index == nil then
    return false
  end
  local r, g, b = cfg.colorR, cfg.colorG, cfg.colorB
  if type(r) ~= "number" or type(g) ~= "number" or type(b) ~= "number" then
    r, g, b = DEFAULTS.colorR, DEFAULTS.colorG, DEFAULTS.colorB
  end
  if pcall(function()
    ImGui.PushStyleColor(index, r, g, b, 1.0)
  end) then
    return true
  end
  local packed = math.floor(r * 255) + math.floor(g * 255) * 256 + math.floor(b * 255) * 65536
    + 0xFF000000
  return (pcall(function()
    ImGui.PushStyleColor(index, packed)
  end))
end

local function popTextColour()
  pcall(function()
    ImGui.PopStyleColor(1)
  end)
end

function M.drawHud(dt)
  local text = M.hudText(dt or frameDt)
  if text == nil then
    return false
  end
  local w, h = screenSize()
  if w and h then
    pcall(function()
      ImGui.SetNextWindowPos(w * cfg.posX, h * cfg.posY)
    end)
  end
  local okBegin, visible = pcall(function()
    return ImGui.Begin("##phoenix_speedometer_hud", hudFlags())
  end)
  if not okBegin then
    return false
  end
  if visible == false then
    pcall(function()
      ImGui.End()
    end)
    return false
  end
  local coloured = pushTextColour()
  pcall(function()
    ImGui.SetWindowFontScale(cfg.scale)
  end)
  pcall(function()
    ImGui.Text(text)
  end)
  if coloured then
    popTextColour()
  end
  pcall(function()
    ImGui.End()
  end)
  return true
end

-- widgets. CET returns (value, changed) - the first value is the setting, the second a flag.
local function uiCheckbox(key, label)
  local before = cfg[key] and true or false
  local value, changed = ImGui.Checkbox(label, before)
  if type(value) ~= "boolean" then
    value = before                       -- never let an odd binding nil a setting out
  end
  cfg[key] = value
  if changed or value ~= before then
    M.saveSettings()
  end
end

local function uiDragFloat(key, label, step, low, high)
  local before = cfg[key]
  if type(before) ~= "number" then
    before = DEFAULTS[key]
  end
  local value, changed = ImGui.DragFloat(label, before, step, low, high)
  if type(value) ~= "number" then
    value = before
  end
  if low and value < low then
    value = low
  end
  if high and value > high then
    value = high
  end
  cfg[key] = value
  if changed or value ~= before then
    M.saveSettings()
  end
end

-- accepts a unit name, "" for a blank slot, or a 1-based index (Native Settings UI sends indices)
local function setSlot(key, unit)
  if type(unit) == "number" then
    unit = UNIT_ORDER[unit]
  end
  if type(unit) ~= "string" then
    return false
  end
  if unit ~= "" and unit ~= "custom" and FACTORS[unit] == nil then
    reported("ignored an unknown unit for " .. tostring(key) .. ": " .. tostring(unit))
    return false
  end
  if cfg[key] == unit then
    return true
  end
  cfg[key] = unit
  M.saveSettings()
  return true
end

function M.setSlot(key, unit)
  return setSlot(key, unit)
end

-- the overlay offers an explicit "off" so a second number can be dropped without editing the ini
local OVERLAY_UNITS = { "m/s", "km/h", "mph", "knots", "ft/s", "Mach", "custom", "off" }

local function uiUnitSelector(label, key)
  local current = cfg[key]
  local preview = (current == "" or current == nil) and "off" or current
  if type(ImGui.BeginCombo) == "function" and type(ImGui.Selectable) == "function" then
    if ImGui.BeginCombo(label, preview) then
      for i = 1, #OVERLAY_UNITS do
        local entry = OVERLAY_UNITS[i]
        if ImGui.Selectable(entry, entry == preview) then
          setSlot(key, entry == "off" and "" or entry)
        end
        if entry == preview and type(ImGui.SetItemDefaultFocus) == "function" then
          ImGui.SetItemDefaultFocus()
        end
      end
      ImGui.EndCombo()
    end
    return
  end
  -- binding without combo boxes: cycle with a button
  if ImGui.Button(label .. ": " .. preview) then
    local index = 1
    for i = 1, #OVERLAY_UNITS do
      if OVERLAY_UNITS[i] == preview then
        index = i
      end
    end
    local next = OVERLAY_UNITS[index % #OVERLAY_UNITS + 1]
    setSlot(key, next == "off" and "" or next)
  end
end

local function settingsBody()
  ImGui.Text("CET HUD - nothing of the game's own HUD is touched.")
  uiCheckbox("enabled", "Show the HUD")
  uiCheckbox("showLabels", "Print the units")
  uiCheckbox("fppOnly", "First person only")

  ImGui.Separator()
  uiUnitSelector("Slot 1 unit", "slot1")
  uiDragFloat("custom1", "Slot 1 custom multiplier", 0.001, 0.0001, 1000.0)
  uiUnitSelector("Slot 2 unit", "slot2")
  uiDragFloat("custom2", "Slot 2 custom multiplier", 0.001, 0.0001, 1000.0)

  ImGui.Separator()
  uiDragFloat("scale", "Text size", 0.05, 0.5, 6.0)
  uiDragFloat("posX", "Horizontal position (0-1 of the screen)", 0.002, 0.0, 1.0)
  uiDragFloat("posY", "Vertical position (0-1 of the screen)", 0.002, 0.0, 1.0)
  uiDragFloat("colorR", "Colour red", 0.01, 0.0, 1.0)
  uiDragFloat("colorG", "Colour green", 0.01, 0.0, 1.0)
  uiDragFloat("colorB", "Colour blue", 0.01, 0.0, 1.0)
  uiDragFloat("smooth", "Position-fallback smoothing", 0.01, 0.02, 1.0)

  ImGui.Separator()
  local veh = getVehicle()
  if veh and lastMps then
    ImGui.Text("Reading: " .. M.format(lastMps) .. " m/s (" .. M.render(lastMps, cfg) .. ")")
  else
    ImGui.Text("Reading: no vehicle")
  end
  if ImGui.Button("Reset to defaults") then
    M.resetToDefaults()
  end
end

-- Begin and End are deliberately outside the guarded body: a widget that throws must not leave a
-- window open on ImGui's stack, which would corrupt every later frame.
function M.drawSettings()
  local okBegin, visible = pcall(function()
    return ImGui.Begin("Phoenix True Speedometer")
  end)
  if not okBegin then
    return false
  end
  local okBody = true
  if visible ~= false then
    okBody = guard("settings window", settingsBody)
  end
  pcall(function()
    ImGui.End()
  end)
  return okBody
end

-- ---------------------------------------------------------------------------
-- optional Native Settings UI tab (in the game's Mods menu, like V's Vehicle Computer)
-- ---------------------------------------------------------------------------
local function unitIndex(unit)
  for i = 1, #UNIT_ORDER do
    if UNIT_ORDER[i] == unit then
      return i
    end
  end
  return nil
end

-- Native Settings UI, from its own source and official example:
--   addTab(path, label)                      addSubcategory(path, label)
--   addSwitch(path, label, desc, current, default, cb)
--   addSelectorString(path, label, desc, elements, index, defaultIndex, cb)   cb receives the index
--   addRangeFloat(path, label, desc, min, max, step, format, current, default, cb)
--   addButton(path, label, desc, buttonText, textSize, cb)
--   setOption(optionTable, value)             switch: bool, range: number, selector: index
--   registerRestoreDefaultsCallback(path, override, cb)
local nativeOptions = {}
local nativeSettingsRef = nil

local function nsValue(entry)
  if entry.kind == "selector" then
    if cfg[entry.key] == "" or cfg[entry.key] == "off" then
      for i = 1, #OVERLAY_UNITS do
        if OVERLAY_UNITS[i] == "off" then
          return i
        end
      end
    end
    return unitIndex(cfg[entry.key]) or 1
  end
  return cfg[entry.key]
end

-- one reset for both surfaces, so the Mods tab widgets never go stale behind the overlay's button
function M.resetToDefaults()
  for k, v in pairs(DEFAULTS) do
    cfg[k] = v
  end
  M.saveSettings()
  local settings = nativeSettingsRef
  if settings and type(settings.setOption) == "function" then
    for _, entry in ipairs(nativeOptions) do
      pcall(settings.setOption, entry.option, nsValue(entry))
    end
  end
end

local function addNativeSettings()
  local ok, nativeSettings = pcall(function()
    return GetMod("nativeSettings")
  end)
  if not ok or type(nativeSettings) ~= "table" or type(nativeSettings.addTab) ~= "function" then
    return false
  end
  local path = "/phoenix_speedometer"

  nativeSettingsRef = nativeSettings
  local resetToDefaults = M.resetToDefaults

  pcall(nativeSettings.addTab, path, "Phoenix Speedometer")

  -- HUD -------------------------------------------------------------------
  pcall(nativeSettings.addSubcategory, path .. "/hud", "HUD")
  local toggles = {
    { "Show the HUD", "Draws its own readout; the game's HUD is untouched.", "enabled" },
    { "Print the units", "Append the unit to each number.", "showLabels" },
    { "First person only", "Hide in third person and photo mode.", "fppOnly" },
  }
  for _, row in ipairs(toggles) do
    local label, description, key = row[1], row[2], row[3]
    pcall(function()
      local option = nativeSettings.addSwitch(path .. "/hud", label, description, cfg[key],
        DEFAULTS[key], function(state)
          if type(state) == "boolean" then
            cfg[key] = state
            M.saveSettings()
          end
        end)
      nativeOptions[#nativeOptions + 1] = { option = option, kind = "switch", key = key }
    end)
  end

  -- units -----------------------------------------------------------------
  pcall(nativeSettings.addSubcategory, path .. "/units", "Units")
  for _, row in ipairs({ { "Slot 1 unit", "slot1" }, { "Slot 2 unit", "slot2" } }) do
    local label, key = row[1], row[2]
    pcall(function()
      local option = nativeSettings.addSelectorString(path .. "/units", label,
        "The numbers on the HUD. Pick off to leave that slot empty.",
        OVERLAY_UNITS, nsValue({ kind = "selector", key = key }), unitIndex(DEFAULTS[key]) or 1,
        function(index)
          local unit = (type(index) == "number") and OVERLAY_UNITS[index] or index
          setSlot(key, unit == "off" and "" or unit)
        end)
      nativeOptions[#nativeOptions + 1] = { option = option, kind = "selector", key = key }
    end)
  end

  local ranges = {
    { path .. "/units", "Slot 1 custom multiplier", "custom1", 0.0001, 1000.0, 0.01, "%.3f",
      "Used when Slot 1 is custom: speed x this." },
    { path .. "/units", "Slot 2 custom multiplier", "custom2", 0.0001, 1000.0, 0.01, "%.3f",
      "Used when Slot 2 is custom: speed x this." },
    { path .. "/look", "Text size", "scale", 0.5, 6.0, 0.05, "%.2f", "Font scale of the readout." },
    { path .. "/look", "Horizontal position", "posX", 0.0, 1.0, 0.01, "%.2f",
      "0 is the left edge of the screen, 1 the right." },
    { path .. "/look", "Vertical position", "posY", 0.0, 1.0, 0.01, "%.2f",
      "0 is the top edge of the screen, 1 the bottom." },
    { path .. "/look", "Colour red", "colorR", 0.0, 1.0, 0.01, "%.2f", "Text colour." },
    { path .. "/look", "Colour green", "colorG", 0.0, 1.0, 0.01, "%.2f", "Text colour." },
    { path .. "/look", "Colour blue", "colorB", 0.0, 1.0, 0.01, "%.2f", "Text colour." },
    { path .. "/look", "Fallback smoothing", "smooth", 0.02, 1.0, 0.01, "%.2f",
      "Only used if the velocity methods are unavailable." },
  }
  pcall(nativeSettings.addSubcategory, path .. "/look", "Position and look")
  for _, row in ipairs(ranges) do
    local where, label, key = row[1], row[2], row[3]
    local low, high, step, format = row[4], row[5], row[6], row[7]
    local description = row[8]
    pcall(function()
      local option = nativeSettings.addRangeFloat(where, label, description, low, high, step,
        format, cfg[key], DEFAULTS[key], function(value)
          if type(value) == "number" then
            cfg[key] = value
            M.saveSettings()
          end
        end)
      nativeOptions[#nativeOptions + 1] = { option = option, kind = "range", key = key }
    end)
  end

  -- reset -----------------------------------------------------------------
  pcall(function()
    nativeSettings.addButton(path, "Reset to defaults",
      "Put every option back to its shipped value.", "Reset", 45, function()
        resetToDefaults()
      end)
  end)
  pcall(function()
    nativeSettings.registerRestoreDefaultsCallback(path, false, function()
      resetToDefaults()
    end)
  end)
  return true
end

local function installStubs()
  -- the file must also load outside the game (the tests load it with stubs in place)
  if type(registerForEvent) ~= "function" then
    registerForEvent = function() end
  end
  if type(registerHotkey) ~= "function" then
    registerHotkey = function() end
  end
end

function M.start()
  installStubs()
  M.loadSettings()
  local wrote = M.saveSettings()          -- first run: put the defaults on disk to edit by hand
  if not wrote then
    reported("settings.ini is not writable - options work but will not persist")
  end

  registerForEvent("onInit", function()
    M.saveSettings()
    addNativeSettings()                  -- Native Settings UI expects mods to add their tab here
  end)

  registerForEvent("onUpdate", function(delta)
    if type(delta) == "number" and delta > 0 and delta < 1 then
      frameDt = delta
    end
  end)

  registerForEvent("onOverlayOpen", function()
    overlayOpen = true
  end)

  registerForEvent("onOverlayClose", function()
    overlayOpen = false
  end)

  local frames = 0
  registerForEvent("onDraw", function()
    frames = frames + 1
    if overlayOpen then
      guard("settings window", M.drawSettings)
    end
    guard("HUD", function()
      M.drawHud(frameDt)
    end)
    if frames == 60 then
      -- one line, one second in, every launch. If it never appears, onDraw is not being called at
      -- all; if it appears with vehicle=false, the mod is running and just has nothing to read.
      local mps, veh = M.currentMps(frameDt)
      reported("1 s in: hud=" .. tostring(cfg.enabled)
        .. " vehicle=" .. tostring(veh ~= nil)
        .. " driver=" .. tostring(veh ~= nil and isDriving(veh) or false)
        .. " speed=" .. tostring(mps)
        .. " | slot1=" .. tostring(cfg.slot1 == "" and "off" or cfg.slot1)
        .. " slot2=" .. tostring(cfg.slot2 == "" and "off" or cfg.slot2)
        .. " labels=" .. tostring(cfg.showLabels)
        .. " text=\"" .. tostring(M.render(mps or 0, cfg)) .. "\"")
    end
  end)

  registerHotkey("PhoenixSpeedometer_ToggleHud", "Toggle speedometer HUD", function()
    cfg.enabled = not (cfg.enabled == true)
    M.saveSettings()
  end)

  registerHotkey("PhoenixSpeedometer_ToggleLabels", "Toggle speedometer unit labels", function()
    cfg.showLabels = not (cfg.showLabels == true)
    M.saveSettings()
  end)

  reported("HUD ready - bind the toggle in CET > Bindings")
  return true
end

PhoenixSpeedometer = M   -- visible in the CET console

-- CET loads this file and then calls nothing: the mod has to start itself, and onInit fires after
-- the mods are loaded. Without this line the file would load cleanly and register no handlers at all.
guard("start", M.start)

return M
