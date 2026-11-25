-- Phoenix True Speedometer - standalone CET HUD
--
-- Why this exists: replacing the game's HUD speed number means fighting a widget built for about
-- four characters, next to a km/h label that belongs to the game and cannot be changed. This draws
-- its own HUD instead - no redscript, no compile step, and nothing of the vanilla HUD is touched.
--
-- Requires: Cyber Engine Tweaks only. If Native Settings UI is installed the same options appear in
-- the game's Mods menu; the CET overlay always has them.
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

local function settingsPath()
  local ok, src = pcall(function()
    return debug.getinfo(1, "S").source
  end)
  if not ok or type(src) ~= "string" then
    return nil
  end
  src = src:gsub("^@", "")
  local dir = src:match("^(.*[/\\])")
  return dir and (dir .. "settings.ini") or nil
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
  local path = settingsPath()
  if not path then
    return false
  end
  local ok, file = pcall(io.open, path, "w")
  if not ok or not file then
    return false
  end
  for k, v in pairs(cfg) do
    file:write(k .. "=" .. encodeValue(v) .. "\n")
  end
  file:close()
  return true
end

function M.loadSettings()
  local path = settingsPath()
  if not path then
    return false
  end
  local ok, file = pcall(io.open, path, "r")
  if not ok or not file then
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
    return M.format(mps) .. " m/s"
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
  if not veh or not dt or dt <= 0 or dt > 0.5 then
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

function M.isFirstPerson(veh)
  if not veh then
    return false
  end
  local ok, cam = pcall(function()
    return veh:GetCameraManager()
  end)
  if not ok or not cam then
    return false
  end
  local okTpp, tpp = pcall(function()
    return cam:IsTPPActive()
  end)
  if not okTpp then
    return false
  end
  return not tpp
end

-- ---------------------------------------------------------------------------
-- CET glue
-- ---------------------------------------------------------------------------
local overlayOpen = false
local lastMps = 0

local function stub(name)
  -- the file must be loadable outside the game (tests load it with stubs already in place)
  if _G["registerForEvent"] == nil then
    _G["registerForEvent"] = function() end
  end
  if _G["registerHotkey"] == nil then
    _G["registerHotkey"] = function() end
  end
end

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
  if not cfg.enabled then
    return nil
  end
  local mps, veh = M.currentMps(dt)
  if mps == nil then
    return nil
  end
  if cfg.fppOnly and not M.isFirstPerson(veh) then
    return nil
  end
  lastMps = mps
  return M.render(mps, cfg)
end

-- ---------------------------------------------------------------------------
-- ImGui
-- ---------------------------------------------------------------------------
local function flag(name)
  local ok, value = pcall(function()
    return ImGuiWindowFlags[name]
  end)
  if ok then
    return value or 0
  end
  return 0
end

local function hudFlags()
  return flag("NoTitleBar") + flag("NoResize") + flag("NoMove") + flag("NoScrollbar")
    + flag("NoCollapse") + flag("AlwaysAutoResize") + flag("NoSavedSettings")
    + flag("NoFocusOnAppearing") + flag("NoNav")
end

local function displaySize()
  local ok, io = pcall(function()
    return ImGui.GetIO()
  end)
  if ok and io and io.DisplaySize then
    return io.DisplaySize.x, io.DisplaySize.y
  end
  return nil, nil
end

function M.drawHud(dt)
  local text = M.hudText(dt)
  if text == nil then
    return false
  end
  local x, y = displaySize()
  if x and y then
    pcall(function()
      ImGui.SetNextWindowPos(x * cfg.posX, y * cfg.posY)
    end)
  end
  local visible = true
  local okBegin, result = pcall(function()
    return ImGui.Begin("##phoenix_speedometer_hud", hudFlags())
  end)
  if not okBegin then
    return false
  end
  if result == false then
    visible = false
  end
  if visible then
    pcall(function()
      ImGui.PushStyleColor(ImGuiCol.Text, cfg.colorR, cfg.colorG, cfg.colorB, 1.0)
    end)
    pcall(function()
      ImGui.SetWindowFontScale(cfg.scale)
    end)
    pcall(function()
      ImGui.Text(text)
    end)
    pcall(function()
      ImGui.PopStyleColor(1)
    end)
    pcall(function()
      ImGui.End()
    end)
  end
  return true
end

local function selector(label, current, onPick)
  if ImGui.BeginCombo then
    if ImGui.BeginCombo(label, current) then
      for i = 1, #UNIT_ORDER do
        local unit = UNIT_ORDER[i]
        local selected = (unit == current)
        if ImGui.Selectable(unit, selected) then
          onPick(unit)
        end
        if selected then
          ImGui.SetItemDefaultFocus()
        end
      end
      ImGui.EndCombo()
    end
    return
  end
  -- older ImGui bindings: cycle with a button
  if ImGui.Button(label .. ": " .. current) then
    local index = 1
    for i = 1, #UNIT_ORDER do
      if UNIT_ORDER[i] == current then
        index = i
      end
    end
    index = index % #UNIT_ORDER + 1
    onPick(UNIT_ORDER[index])
  end
end

function M.drawSettings()
  ImGui.Begin("Phoenix True Speedometer")
  ImGui.Text("CET HUD - nothing of the game's own HUD is touched.")
  local changed
  changed, cfg.enabled = ImGui.Checkbox("Show the HUD", cfg.enabled)
  if changed then
    M.saveSettings()
  end
  changed, cfg.showLabels = ImGui.Checkbox("Print the units", cfg.showLabels)
  if changed then
    M.saveSettings()
  end
  changed, cfg.fppOnly = ImGui.Checkbox("First person only", cfg.fppOnly)
  if changed then
    M.saveSettings()
  end

  ImGui.Separator()
  selector("Slot 1 unit", cfg.slot1, function(unit)
    cfg.slot1 = unit
    M.saveSettings()
  end)
  changed, cfg.custom1 = ImGui.DragFloat("Slot 1 custom multiplier", cfg.custom1, 0.001, 0.0001, 1000.0)
  if changed then
    M.saveSettings()
  end
  selector("Slot 2 unit (off = empty)", cfg.slot2, function(unit)
    cfg.slot2 = unit
    M.saveSettings()
  end)
  changed, cfg.custom2 = ImGui.DragFloat("Slot 2 custom multiplier", cfg.custom2, 0.001, 0.0001, 1000.0)
  if changed then
    M.saveSettings()
  end

  ImGui.Separator()
  changed, cfg.scale = ImGui.DragFloat("Text size", cfg.scale, 0.05, 0.5, 6.0)
  if changed then
    M.saveSettings()
  end
  changed, cfg.posX = ImGui.DragFloat("Horizontal position (0-1 of screen)", cfg.posX, 0.002, 0.0, 1.0)
  if changed then
    M.saveSettings()
  end
  changed, cfg.posY = ImGui.DragFloat("Vertical position (0-1 of screen)", cfg.posY, 0.002, 0.0, 1.0)
  if changed then
    M.saveSettings()
  end
  changed, cfg.colorR = ImGui.DragFloat("Colour red", cfg.colorR, 0.01, 0.0, 1.0)
  if changed then
    M.saveSettings()
  end
  changed, cfg.colorG = ImGui.DragFloat("Colour green", cfg.colorG, 0.01, 0.0, 1.0)
  if changed then
    M.saveSettings()
  end
  changed, cfg.colorB = ImGui.DragFloat("Colour blue", cfg.colorB, 0.01, 0.0, 1.0)
  if changed then
    M.saveSettings()
  end
  changed, cfg.smooth = ImGui.DragFloat("Position-fallback smoothing", cfg.smooth, 0.01, 0.02, 1.0)
  if changed then
    M.saveSettings()
  end

  ImGui.Separator()
  local veh = getVehicle()
  if veh and lastMps then
    ImGui.Text("Reading: " .. M.format(lastMps) .. " m/s (" .. M.render(lastMps, cfg) .. ")")
  else
    ImGui.Text("Reading: no vehicle")
  end
  if ImGui.Button("Reset to defaults") then
    for k, v in pairs(DEFAULTS) do
      cfg[k] = v
    end
    M.saveSettings()
  end
  ImGui.End()
end

-- ---------------------------------------------------------------------------
-- optional Native Settings UI tab (in the game's Mods menu, like V's Vehicle Computer)
-- ---------------------------------------------------------------------------
local function addNativeSettings()
  local ok, nativeSettings = pcall(function()
    return GetMod("nativeSettings")
  end)
  if not ok or type(nativeSettings) ~= "table" or not nativeSettings.addTab then
    return false
  end
  local path = "/phoenix_speedometer"
  pcall(function()
    nativeSettings.addTab(path, "Phoenix Speedometer")
  end)
  pcall(function()
    nativeSettings.addSubcategory(path .. "/hud", "HUD")
  end)
  pcall(function()
    nativeSettings.addToggle(path .. "/hud", "Show the HUD", "Draws its own speed readout; the game's HUD is untouched.", cfg.enabled, function(state)
      cfg.enabled = state
      M.saveSettings()
    end)
  end)
  pcall(function()
    nativeSettings.addToggle(path .. "/hud", "Print the units", "Append the unit to each number.", cfg.showLabels, function(state)
      cfg.showLabels = state
      M.saveSettings()
    end)
  end)
  pcall(function()
    nativeSettings.addToggle(path .. "/hud", "First person only", "Hide in third person and photo mode.", cfg.fppOnly, function(state)
      cfg.fppOnly = state
      M.saveSettings()
    end)
  end)
  pcall(function()
    nativeSettings.addSubcategory(path .. "/units", "Units")
  end)
  pcall(function()
    nativeSettings.addSelectorString(path .. "/units", "Slot 1 unit", "The main number.", UNIT_ORDER, cfg.slot1, function(unit)
      cfg.slot1 = unit
      M.saveSettings()
    end)
  end)
  pcall(function()
    nativeSettings.addSelectorString(path .. "/units", "Slot 2 unit", "Second number; pick custom for your own multiplier.", UNIT_ORDER, cfg.slot2, function(unit)
      cfg.slot2 = unit
      M.saveSettings()
    end)
  end)
  return true
end

-- ---------------------------------------------------------------------------
-- registration
-- ---------------------------------------------------------------------------
local listeners = {}

function M.start()
  stub(name)
  M.loadSettings()
  M.saveSettings()          -- first run: put the defaults on disk so they can be edited by hand
  addNativeSettings()

  registerForEvent("onInit", function()
    M.saveSettings()
  end)

  registerForEvent("onOverlayOpen", function()
    overlayOpen = true
  end)

  registerForEvent("onOverlayClose", function()
    overlayOpen = false
  end)

  registerForEvent("onDraw", function(dt)
    if overlayOpen then
      local ok = pcall(M.drawSettings)
      if not ok then
        overlayOpen = false
      end
    end
    pcall(M.drawHud, dt or 0.016)
  end)

  registerHotkey("PhoenixSpeedometer_ToggleHud", "Toggle speedometer HUD", function()
    cfg.enabled = not cfg.enabled
    M.saveSettings()
  end)

  registerHotkey("PhoenixSpeedometer_ToggleLabels", "Toggle speedometer unit labels", function()
    cfg.showLabels = not cfg.showLabels
    M.saveSettings()
  end)

  print("[Phoenix True Speedometer] HUD ready - bind the toggle in CET > Bindings")
  return true
end

listeners.cfg = cfg
M.listeners = listeners

_G.PhoenixSpeedometer = M
return M
