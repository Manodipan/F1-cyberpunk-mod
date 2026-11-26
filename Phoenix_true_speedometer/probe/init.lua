-- Phoenix CET probe.
--
-- This exists to answer one question and nothing else: is CET loading Lua mods and calling onDraw
-- on this install? It draws unconditionally - no vehicle check, no settings, no conditions - so if
-- CET is running mods at all, something appears on screen.
--
-- Two independent signals:
--   1. a line in the CET console / log at load:   [PhoenixProbe] init.lua executed
--   2. a box top-left with the frame counter      PHOENIX PROBE OK frames=...
--
-- Install with:  .\tools\update.ps1 -Probe
-- Remove with:   .\tools\update.ps1          (the probe is deleted unless -Probe is passed)

print("[PhoenixProbe] init.lua executed")

local frames = 0
local reported = false
local lastSpeed = nil

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

registerForEvent("onInit", function()
  local ok, version = pcall(GetVersion)
  print("[PhoenixProbe] onInit - CET version " .. (ok and tostring(version) or "unknown"))
end)

registerForEvent("onDraw", function()
  frames = frames + 1
  local veh = getVehicle()
  lastSpeed = readSpeed(veh)

  pcall(function()
    ImGui.SetNextWindowPos(20, 20)
    ImGui.Begin("Phoenix probe")
    ImGui.Text("PHOENIX PROBE OK   frames=" .. frames)
    ImGui.Text("vehicle=" .. tostring(veh ~= nil) .. "   speed=" .. tostring(lastSpeed))
    ImGui.End()
  end)

  if frames == 120 and not reported then
    reported = true
    print("[PhoenixProbe] 2 s in: vehicle=" .. tostring(veh ~= nil)
      .. " speed=" .. tostring(lastSpeed))
  end
end)
