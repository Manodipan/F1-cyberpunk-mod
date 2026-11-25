local DebugModule = { isEnabled = true }

local function GetSystem() return DebugModule.systemClassName and Game and Game.GetScriptableSystemsContainer() and Game.GetScriptableSystemsContainer():Get(DebugModule.systemClassName) end

-- DrawTypeの列挙は onInit でやった方が良いかもだけど, もしonInit呼ばれなくても動作するように, 独立させておく.
local systemDrawTypes = nil
local function GetDrawType()
  local system = GetSystem()
  if not systemDrawTypes and system then
    systemDrawTypes = {}
    local max = tonumber(EnumGetMax(system:DrawTypeName()))
    for i = 0, max do
      local name = EnumValueToName(system:DrawTypeName(), i)
      if name then systemDrawTypes[NameToString(name)] = i end
    end
  end
  return systemDrawTypes
end

function DebugModule:setup(systemClassName)
  self.systemClassName = systemClassName
  return self
end

function DebugModule:initialize()
  -- onDraw で可能な限りネイティブコールしたくないので, EnabledChanged を Observe してローカルに保持.
  -- もしonInitで呼ばれなくても, 一応 requests さえ入らなければ描画はされない.
  Observe(self.systemClassName, "OnEnabledChanged", function(this, enabled) self.isEnabled = enabled end)
  self.isEnabled = GetSystem() and GetSystem():IsEnabled()
  return self
end

-- debug.lua 側で勝手に onDraw を登録するモード
function DebugModule:registerEvents()
  registerForEvent("onDraw", function()
    local resX, resY = GetDisplayResolution()
    self:draw(resX, resY)
  end)
  registerForEvent("onInit", function() self:initialize() end)
  return self
end

-- 3D空間でのクリッピング描画関数
-- 【3Dクリッピングの肝】
-- 1. カメラの後ろ(Z<=0)に突き抜けた線は、そのまま投影すると画面内で反転して暴れる
-- 2. なので、カメラのレンズ面（の10cm前方）で線分をパツンと切る「新しい終点」を作る
-- 3. その「切った点」のワールド座標を算出し、改めてスクリーンへ投影する
-- これにより、線が画面の端まで綺麗に繋がり、消失や反転バグを防げる
local function drawClippedLine(drawList, v1, v2, camera, cX, cY, col, thickness)
  -- 1. カメラの位置と前方ベクトルを確実に取得
  local transform = Transform.new()
  camera:GetActiveCameraWorldTransform(transform)
  local camPos = transform.position
  local camFwd = camera:GetActiveCameraForward()

  -- 2. Dot Product で「本当の奥行き（メートル）」を出す
  -- ProjectPoint の Z=0 をこれでバイパスする
  local function getZ(v)
    return (v.x - camPos.x) * camFwd.x + (v.y - camPos.y) * camFwd.y + (v.z - camPos.z) * camFwd.z
  end

  local z1 = getZ(v1)
  local z2 = getZ(v2)

  -- 両方カメラの後ろなら描画不要
  if z1 <= 0 and z2 <= 0 then return end

  -- 3. スクリーン投影（前方にある点は正しく投影される）
  local n1 = camera:ProjectPoint(v1)
  local n2 = camera:ProjectPoint(v2)

  -- 両方前方(z > 0)なら、そのまま描画
  if z1 > 0 and z2 > 0 then
    ImGui.ImDrawListAddLine(drawList, cX + (n1.x * cX), cY - (n1.y * cY), cX + (n2.x * cX), cY - (n2.y * cY), col, thickness)
    return
  end

  -- 4. 【肝】片方が後ろに回った場合のクリッピング
  local fV, bV, fZ, bZ, fN = v1, v2, z1, z2, n1
  if z1 < z2 then
    fV, bV, fZ, bZ, fN = v2, v1, z2, z1, n2
  end

  -- 正確な距離（fZ と bZ）を使って、線分がレンズ面(Z=0)を横切る比率 t を出す
  -- bZ は負の値なので、(fZ - bZ) は「点間のZ距離」になる
  local t = fZ / (fZ - bZ)
  
  -- Near Plane（消失点）より少し手前で止めるための比率
  -- fzから10cmを引いた距離とfzの距離の比率を出してtにかける. ただし, 近すぎも考慮
  local ratio = (fZ > 0.11) and (1.0 - 0.1 / fZ) or 0.9
  local clipT = t * ratio

  -- ワールド空間上で新しい「終点」を作成
  local clippedV = Vector4.new(
    fV.x + clipT * (bV.x - fV.x),
    fV.y + clipT * (bV.y - fV.y),
    fV.z + clipT * (bV.z - fV.z),
    1.0
  )

  -- 「切った点」は必ずカメラの前方にあるので、ProjectPoint が正しく動作する
  local nC = camera:ProjectPoint(clippedV)
  if nC.z > 0 then
    ImGui.ImDrawListAddLine(drawList, cX + (fN.x * cX), cY - (fN.y * cY), cX + (nC.x * cX), cY - (nC.y * cY), col, thickness)
  end
end

-- 明示的に呼び出すためのメイン描画関数
function DebugModule:draw(resX, resY)
  if not self.isEnabled then return end;

  local DrawType = GetDrawType()
  local system = GetSystem()
  if not DrawType or not system or not system:IsEnabled() then return end

  local requests = system:GetAllRequests()
  if #requests == 0 then return end

  local camera = Game.GetCameraSystem()
  local drawList = ImGui.GetBackgroundDrawList()
  local cX, cY = resX / 2, resY / 2
  local TextAlignment = gameDebugViewETextAlignment

  for _, req in ipairs(requests) do
    local col = ImGui.ColorConvertFloat4ToU32({
      req.color.Red / 255, req.color.Green / 255, req.color.Blue / 255, req.color.Alpha / 255
    })

    local typeInt = tonumber(EnumInt(req.type))

    if typeInt == DrawType.Text or typeInt == DrawType.Text2D then
      -- 2D Text
      local posX, posY

      if typeInt == DrawType.Text2D then
        -- 0.0 ~ 1.0 の正規化座標をピクセルに変換
        posX = req.screenPos.X * resX
        posY = req.screenPos.Y * resY
      else
        -- 既にピクセル座標（500.0, 690.0等）なのでそのまま使う
        posX = req.screenPos.X
        posY = req.screenPos.Y
      end

      -- Align の計算 (gameDebugViewETextAlignment を想定)
      -- 0: Left, 1: Center, 2: Right
      if req.textAlign == TextAlignment.Center or req.textAlign == TextAlignment.Right then
        local textWidth = ImGui.CalcTextSize(req.text)
        if req.textAlign == TextAlignment.Center then
          posX = posX - (textWidth / 2)
        else
          posX = posX - textWidth
        end
      end
      ImGui.ImDrawListAddText(drawList, posX, posY, col, req.text)
    elseif typeInt == DrawType.Line and #req.vertices >= 2 then
      -- Line
      drawClippedLine(drawList, req.vertices[1], req.vertices[2], camera, cX, cY, col, 2.0)
    elseif typeInt == DrawType.Rect and #req.vertices == 4 then
      -- Rect
      local edges = {{1,2}, {2,3}, {3,4}, {4,1}}
      for _, e in ipairs(edges) do
        drawClippedLine(drawList, req.vertices[e[1]], req.vertices[e[2]], camera, cX, cY, col, 2.0)
      end
    elseif typeInt == DrawType.Box and #req.vertices == 8 then
      -- Box
      local edges = {
        {1,2}, {2,3}, {3,4}, {4,1},
        {5,6}, {6,7}, {7,8}, {8,5},
        {1,5}, {2,6}, {3,7}, {4,8}
      }
      for _, e in ipairs(edges) do
        drawClippedLine(drawList, req.vertices[e[1]], req.vertices[e[2]], camera, cX, cY, col, 1.0)
      end
    end
  end
end

return DebugModule