-- Phoenix speed HUD, probe architecture.
--
-- This is the probe that was proven to draw, with exactly one feature added: a dropdown to pick the
-- speed unit. Nothing is conditional. There is no settings window, no hotkey, no vehicle gate, no
-- second mod, no per-frame state machine. Begin/Text/End, every frame, unconditionally - the shape
-- that already worked on the user's install.
--
-- The choice is remembered in unit.txt beside this file, so it survives a restart. If that file
-- cannot be written the dropdown still works for the session.

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

local chosen = 1                        -- km/h by default

local SETTINGS_FILE = "unit.txt"

local function loadUnit()
  local ok, file = pcall(io.open, SETTINGS_FILE, "r")
  if not ok or not file then
    return
  end
  local name = file:read("*l")
  file:close()
  if not name then
    return
  end
  for i = 1, #UNITS do
    if UNITS[i].name == name then
      chosen = i
      return
    end
  end
end

local function saveUnit()
  local ok, file = pcall(io.open, SETTINGS_FILE, "w")
  if not ok or not file then
    return
  end
  file:write(UNITS[chosen].name .. "\n")
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
-- draw
-- ---------------------------------------------------------------------------
loadUnit()

local frames = 0

registerForEvent("onDraw", function()
  frames = frames + 1

  local veh = getVehicle()
  local mps = readSpeed(veh)

  -- drawing is wrapped so a failure cannot leave a window open on ImGui's stack
  pcall(function()
    ImGui.SetNextWindowPos(20, 20)
    ImGui.Begin("Phoenix speed")

    if mps then
      ImGui.Text(formatSpeed(mps * UNITS[chosen].factor) .. " " .. UNITS[chosen].name)
    else
      ImGui.Text("-- " .. UNITS[chosen].name)
    end

    if ImGui.BeginCombo("Unit", UNITS[chosen].name) then
      for i = 1, #UNITS do
        if ImGui.Selectable(UNITS[i].name, i == chosen) then
          chosen = i
          saveUnit()
        end
      end
      ImGui.EndCombo()
    end

    ImGui.Text("PHOENIX PROBE OK   frames=" .. frames)
    ImGui.End()
  end)

  if frames == 120 then
    print("[PhoenixSpeed] 2 s in: vehicle=" .. tostring(veh ~= nil)
      .. " speed=" .. tostring(mps)
      .. " unit=" .. UNITS[chosen].name)
  end
end)
