-- Phoenix speed HUD, probe architecture.
--
-- This is the probe that was proven to draw, plus two features: a unit dropdown and a movable
-- window. Nothing is conditional about the drawing itself - Begin/Text/End every frame, as before.
--
-- Positioning has three modes:
--   free    - drag it wherever you like. Dragging works while the CET overlay is open (~), because
--             that is when CET lets a window receive the mouse. The place you put it is remembered.
--   top     - pinned, horizontally centred, near the top edge.
--   bottom  - pinned, horizontally centred, near the bottom edge.
--
-- While the overlay is open the window also shows the controls and a frame counter, so there is
-- always a sign the mod is running. Closed, it is just the number.

print("[PhoenixSpeed] init.lua executed")

-- ---------------------------------------------------------------------------
-- units
-- ---------------------------------------------------------------------------
-- 1 m/s is the speed the game reports, so every factor is "multiply the m/s value".
local UNITS = {
  { name = "km/h",  factor = 3.6 },
  { name = "mph",   factor = 2.23694 },
  { name = "m/s",   factor = 1.0 },
  { name = "knots", factor = 1.94384 },
  { name = "ft/s",  factor = 3.28084 },
  { name = "Mach",  factor = 1.0 / 343.0 },
}

local chosen = 1                        -- km/h
local POSITIONS = { "free", "top", "bottom" }
-- free by default: something that cannot be dragged is worse than something that is out of the way,
-- and the first run has no remembered place to restore
local position = 1                      -- free
local posX, posY = nil, nil             -- last free position, in screen pixels

-- one small file beside init.lua. Lines are key=value; a bare line is read as the legacy unit name
-- written by the previous build, so an existing unit.txt keeps working.
local SETTINGS_FILE = "unit.txt"

local function loadSettings()
  local ok, file = pcall(io.open, SETTINGS_FILE, "r")
  if not ok or not file then
    return
  end
  for line in file:lines() do
    local key, value = line:match("^([%w_]+)=(.*)$")
    if key == "unit" then
      for i = 1, #UNITS do
        if UNITS[i].name == value then chosen = i end
      end
    elseif key == "position" then
      for i = 1, #POSITIONS do
        if POSITIONS[i] == value then position = i end
      end
    elseif key == "x" then
      posX = tonumber(value)
    elseif key == "y" then
      posY = tonumber(value)
    elseif key == nil and line ~= "" then
      for i = 1, #UNITS do                        -- legacy: the whole line is a unit name
        if UNITS[i].name == line then chosen = i end
      end
    end
  end
  file:close()
end

local function saveSettings()
  local ok, file = pcall(io.open, SETTINGS_FILE, "w")
  if not ok or not file then
    return
  end
  file:write("unit=" .. UNITS[chosen].name .. "\n")
  file:write("position=" .. POSITIONS[position] .. "\n")
  if posX and posY then
    file:write(string.format("x=%.1f\ny=%.1f\n", posX, posY))
  end
  file:close()
end

-- ---------------------------------------------------------------------------
-- formatting: three significant figures, whole numbers from 100 up
-- ---------------------------------------------------------------------------
local function formatSpeed(value)
  if type(value) ~= "number" or value ~= value then
    return "0"
  end
  if value < 0 then
    value = -value
  end
  if value >= 100 then
    return tostring(math.floor(value + 0.5))
  end
  local text = string.format("%.3g", value)
  if text:find("[eE]") then
    text = string.format("%.5f", value)
  end
  return text
end

-- ---------------------------------------------------------------------------
-- speed, exactly as the probe read it
-- ---------------------------------------------------------------------------
local function getVehicle()
  local ok, veh = pcall(function()
    return Game["GetMountedVehicle;GameObject"](Game.GetPlayer())
  end)
  if not ok then
    return nil
  end
  return veh
end

local function readSpeed(veh)
  if not veh then
    return nil
  end
  local ok, value = pcall(function()
    local vel = veh:GetLinearVelocity()
    local fwd = veh:GetWorldForward()
    return vel.x * fwd.x + vel.y * fwd.y + vel.z * fwd.z + vel.w * fwd.w
  end)
  if ok and type(value) == "number" then
    if value < 0 then
      value = -value
    end
    return value
  end
  return nil
end

-- ---------------------------------------------------------------------------
-- window geometry
-- ---------------------------------------------------------------------------
local overlayOpen = false
local restorePos = true                 -- apply the remembered position once, then leave it alone
-- the size from the previous frame. Seeded with a plausible box so the very first frame is already
-- in the right place instead of jumping 24 px once the real size is known.
local lastW, lastH = 120, 24
local curX, curY = nil, nil             -- where the window actually is

local function screenSize()
  local ok, w, h = pcall(GetDisplayResolution)
  if ok and type(w) == "number" and type(h) == "number" and w > 0 and h > 0 then
    return w, h
  end
  return 1920, 1080
end

-- flag values come from the whitelisted table; anything missing is simply left out
local function flag(name)
  local flags = ImGuiWindowFlags
  if type(flags) == "table" and type(flags[name]) == "number" then
    return flags[name]
  end
  return 0
end

-- Distinct bits only: NoDecoration already carries NoTitleBar/NoResize/NoScrollbar/NoCollapse, so
-- adding them again would corrupt the mask.
local function hudFlags()
  local flags = flag("AlwaysAutoResize") + flag("NoSavedSettings")
  if overlayOpen then
    -- movable and able to receive the mouse: this is the only state a drag can happen in, because
    -- CET only routes input to ImGui while its overlay is open
    flags = flags + flag("NoCollapse")
  else
    flags = flags + flag("NoDecoration") + flag("NoMove") + flag("NoInputs")
  end
  return flags
end

-- Explicit drag handling. ImGui can move a window by itself, but that depends on the window being
-- hit-tested the way ImGui expects; doing it by hand with the mouse delta works regardless and is
-- what makes dragging reliable here. Only active while the CET overlay is open (that is when input
-- reaches ImGui at all).
local dragging = false
local grabX, grabY = nil, nil           -- where the window was when the drag started

local function mouseDown()
  local button = ImGuiMouseButton
  if type(button) == "table" and type(button.Left) == "number" then
    button = button.Left
  else
    button = 0
  end
  local ok, down = pcall(ImGui.IsMouseDown, button)
  return ok and down == true
end

local function dragWindow()
  if not overlayOpen or POSITIONS[position] ~= "free" then
    dragging = false
    return
  end
  local okHover, hovered = pcall(ImGui.IsWindowHovered)
  if not okHover then
    hovered = false
  end
  local down = mouseDown()
  local okDelta, dx, dy = pcall(ImGui.GetMouseDragDelta)
  if not okDelta or type(dx) ~= "number" then
    dx, dy = 0, 0
  end

  if down and (dragging or hovered) then
    if not dragging then
      -- first frame of the grab: anchor the window's position and measure the drag from there.
      -- GetMouseDragDelta is cumulative since the button went down, so it must not be added to a
      -- position that has already been moved by a previous frame's delta.
      dragging = true
      grabX = curX or posX or 0
      grabY = curY or posY or 0
    end
    if dx * dx + dy * dy > 0 then
      posX = grabX + dx
      posY = grabY + dy
      ImGui.SetWindowPos(posX, posY)
      restorePos = false
      curX, curY = posX, posY
    end
  end
  if not down then
    dragging = false
    grabX, grabY = nil, nil
  end
end

local function condAlways()
  local cond = ImGuiCond
  if type(cond) == "table" and type(cond.Always) == "number" then
    return cond.Always
  end
  return 1
end

local function applyPosition()
  if POSITIONS[position] == "free" then
    -- A free window is never given a position except once, to restore the place the user dragged it
    -- to last time. Forcing it every frame is what made dragging impossible.
    if restorePos and posX and posY then
      ImGui.SetNextWindowPos(posX, posY, condAlways())
      restorePos = false                 -- applied once, then the window is the user's
    end
    return
  end
  local sw, sh = screenSize()
  local x = (sw - lastW) / 2
  local y = (POSITIONS[position] == "top") and 20 or (sh - lastH - 20)
  if y < 20 then
    y = 20
  end
  ImGui.SetNextWindowPos(x, y, condAlways())
end

-- ---------------------------------------------------------------------------
-- controls, drawn only while the overlay is open
-- ---------------------------------------------------------------------------
local function unitSelector()
  if ImGui.BeginCombo("Unit", UNITS[chosen].name) then
    for i = 1, #UNITS do
      if ImGui.Selectable(UNITS[i].name, i == chosen) then
        chosen = i
        saveSettings()
      end
    end
    ImGui.EndCombo()
  end
end

local function positionSelector()
  if ImGui.BeginCombo("Position", POSITIONS[position]) then
    for i = 1, #POSITIONS do
      if ImGui.Selectable(POSITIONS[i], i == position) then
        position = i
        if POSITIONS[i] ~= "free" then
          -- a pin owns the position from now on
        elseif curX and curY then
          posX, posY = curX, curY       -- unpinning keeps the window exactly where it is
          restorePos = true             -- ...and applies it for exactly one frame
        end
        saveSettings()
      end
    end
    ImGui.EndCombo()
  end
end

-- ---------------------------------------------------------------------------
-- draw
-- ---------------------------------------------------------------------------
loadSettings()

local frames = 0

registerForEvent("onOverlayOpen", function()
  overlayOpen = true
end)

registerForEvent("onOverlayClose", function()
  overlayOpen = false
  posX, posY = curX or posX, curY or posY   -- remember where the drag left it
  saveSettings()
end)

registerForEvent("onDraw", function()
  frames = frames + 1

  local veh = getVehicle()
  local mps = readSpeed(veh)

  -- drawing is wrapped so a failure cannot leave a window open on ImGui's stack
  pcall(function()
    applyPosition()
    ImGui.Begin("Phoenix speed", hudFlags())

    if mps then
      ImGui.Text(formatSpeed(mps * UNITS[chosen].factor) .. " " .. UNITS[chosen].name)
    else
      ImGui.Text("-- " .. UNITS[chosen].name)
    end

    -- where the window actually is, read before the drag so a grab on the very first frame still
    -- has a sensible anchor
    local okPre, px, py = pcall(ImGui.GetWindowPos)
    if okPre and type(px) == "number" then
      curX, curY = px, py
    end

    dragWindow()

    if overlayOpen then
      unitSelector()
      positionSelector()
      ImGui.Text("PHOENIX PROBE OK   frames=" .. frames)
    end

    -- ImGui only reports these after Begin. curX/curY is where the window really is; the remembered
    -- posX/posY is only written on a real drag (overlay open), never by just existing - otherwise the
    -- first frame overwrites a restored position before it has been applied.
    local okPos, wx, wy = pcall(ImGui.GetWindowPos)
    if okPos and type(wx) == "number" then
      curX, curY = wx, wy
      if overlayOpen and POSITIONS[position] == "free" then
        posX, posY = wx, wy
      end
    end
    local okSize, ww, wh = pcall(ImGui.GetWindowSize)
    if okSize and type(ww) == "number" then
      lastW, lastH = ww, wh
    end

    ImGui.End()
  end)

  if frames == 120 then
    print("[PhoenixSpeed] 2 s in: vehicle=" .. tostring(veh ~= nil)
      .. " speed=" .. tostring(mps)
      .. " unit=" .. UNITS[chosen].name
      .. " position=" .. POSITIONS[position])
  end
end)
