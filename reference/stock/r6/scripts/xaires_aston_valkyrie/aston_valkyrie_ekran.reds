// Peugeot 9X8 (xaires): direksiyon simidi ekranı (aston_valkyrie_main.inkwidget, wkit\make_inkwidget.py; Sesto ekran reds'i kopyası).
// Üstte vites ışıkları (amvRev, seg_00..seg_14 hücreler, 5000-8000 devir), ortada vites (amvGear/amvGearImg, g_1..g_7 / g_N / g_R),
// solda hız (speed/amvSpd0..2, s_0..s_9 rakam görselleri, km/h).
// Devir ve vites motor sesinin sanal şanzımanından (aston_valkyrie_audio.reds XairesAMVEngineState: vrpm / vgear): ekran sesle
// aynı devri ve vitesi gösterir. Oyuncu bu araçta değilse oyunun devri / vitesi. Geri vites R, boş N (oyunun vitesi).
// Hız kancası araç kaydına bakar; devir kancası ağaçta amvRev olan (bizim) ekranı arar -> diğer araçlara dokunmaz.

public static func XairesAMV_DashMinRpm() -> Float { return 5000.0; }      // ilk vites ışığı (make_screen_ui DASH_MIN)
public static func XairesAMV_DashMaxRpm() -> Float { return 8000.0; }      // son (mavi) ışık; vites tavanı 8100

// vites görseli: oyunun vitesi < 0 R, 0 N; ileri viteste sanal vites (ses) ya da oyunun vitesi
public static func XairesAMV_DashGear(root: ref<inkCompoundWidget>, vehicle: wref<VehicleObject>) -> Void {
  if !IsDefined(root) || !XairesAMV_IsTarget(vehicle) {
    return;
  }
  let img = root.GetWidgetByPathName(n"amvGear/amvGearImg") as inkImage;
  if !IsDefined(img) {
    return;
  }
  let g: Int32 = vehicle.GetBlackboard().GetInt(GetAllBlackboardDefs().Vehicle.GearValue);
  g = XairesAMV_GearSign(vehicle, g);
  let part: CName = n"g_N";
  if g < 0 {
    part = n"g_R";
  } else {
    if g > 0 {
      let state = XairesAMVEngineState.Get();
      if IsDefined(state) && state.active {
        g = state.vgear;
      }
      part = StringToName("g_" + IntToString(Clamp(g, 1, 7)));
    }
  }
  img.SetTexturePart(part);
}

// hız rakamları: sağa yaslı 3 yuva, baştaki sıfırlar gizli
public static func XairesAMV_DashSpeed(root: ref<inkCompoundWidget>, kmh: Int32) -> Void {
  let v: Int32 = Clamp(kmh, 0, 999);
  let d0 = root.GetWidgetByPathName(n"speed/amvSpd0") as inkImage;
  let d1 = root.GetWidgetByPathName(n"speed/amvSpd1") as inkImage;
  let d2 = root.GetWidgetByPathName(n"speed/amvSpd2") as inkImage;
  if !IsDefined(d0) || !IsDefined(d1) || !IsDefined(d2) {
    return;
  }
  d0.SetTexturePart(StringToName("s_" + IntToString(v / 100)));
  d1.SetTexturePart(StringToName("s_" + IntToString((v / 10) % 10)));
  d2.SetTexturePart(StringToName("s_" + IntToString(v % 10)));
  d0.SetVisible(v >= 100);
  d1.SetVisible(v >= 10);
  d2.SetVisible(true);
}

@wrapMethod(speedometerLogicController)
public final func OnSpeedValueChanged(speed: Float) -> Void {
  wrappedMethod(speed);
  if XairesAMV_IsTarget(this.m_vehicle) {
    let parent = this.GetRootWidget().GetParentWidget() as inkCompoundWidget;
    if IsDefined(parent) && IsDefined(parent.GetWidgetByPathName(n"amvGear")) {
      XairesAMV_DashSpeed(parent, RoundMath(AbsF(speed) * 3.6));
      XairesAMV_DashGear(parent, this.m_vehicle);
    }
  }
}

@wrapMethod(tachometerLogicController)
public final func OnRpmValueChanged(newRPM: Float) -> Void {
  wrappedMethod(newRPM);
  let own = this.GetRootWidget() as inkCompoundWidget;
  if !IsDefined(own) {
    return;
  }
  let parent = own.GetParentWidget() as inkCompoundWidget;
  if !IsDefined(parent) {
    return;
  }
  let rev = parent.GetWidgetByPathName(n"amvRev") as inkCompoundWidget;
  if !IsDefined(rev) {
    return;                                       // bizim ekranımız değil
  }
  let rpm: Float = newRPM;
  let state = XairesAMVEngineState.Get();
  if IsDefined(state) && state.active {
    rpm = state.vrpm;
  }
  let n: Int32 = rev.GetNumChildren();
  let lit: Int32 = RoundMath(ClampF((rpm - XairesAMV_DashMinRpm()) / (XairesAMV_DashMaxRpm() - XairesAMV_DashMinRpm()), 0.0, 1.0) * Cast<Float>(n));
  let i: Int32 = 0;
  while i < n {
    let seg = rev.GetWidgetByIndex(i);
    if IsDefined(seg) {
      seg.SetOpacity(i < lit ? 1.0 : 0.0);
    }
    i += 1;
  }
  let player = GetPlayer(GetGameInstance());
  if IsDefined(player) {
    XairesAMV_DashGear(parent, GetMountedVehicle(player));
  }
}


// ---------- vites göstergesi: frende R düzeltmesi (Nexus yorumu 2026-11-06) ----------
// Oyun frene basılınca araç hâlâ ileri giderken vitesi hemen R'ye düşürüyor. Ekran ve ses ileri hıza göre karar verir:
// dururken N, geri giderken R, ileri giderken (oyun R'de olsa da) ileri vites.
public static func XairesAMV_FwdSpeed(vehicle: wref<VehicleObject>) -> Float {
  return Vector4.Dot(vehicle.GetLinearVelocity(), vehicle.GetWorldForward());
}

public static func XairesAMV_GearSign(vehicle: wref<VehicleObject>, g: Int32) -> Int32 {
  let fs: Float = XairesAMV_FwdSpeed(vehicle);
  if AbsF(fs) < 0.5 {
    return 0;
  }
  if fs < 0.0 {
    return -1;
  }
  return g < 0 ? 1 : g;
}
