// Peugeot 9X8 (xaires): oyunun ekran (HUD) hız göstergesinde gerçek hız (Sesto sesto_elemento.reds kopyası).
// Oyun hızı "speed_to_multiplier" eğrisiyle gösteriyor; yüksek hızda sayı şişiyor.
// Sadece bu araçta Vehicle.SpeedValue (m/s) x 3.6 yazılır, oyunun km/mph ayarına (m_kmOn) uyar. Diğer araçlara dokunmaz.
// Diğer araç betikleri de aynı fonksiyonu sarar; redscript sarmalayıcıları zincirler, her biri kendi aracını kontrol eder.

public static func XairesAMV_IsTarget(vehicle: wref<VehicleObject>) -> Bool {
  if !IsDefined(vehicle) {
    return false;
  }
  let record: ref<Vehicle_Record>;
  VehicleComponent.GetVehicleRecord(vehicle, record);
  if !IsDefined(record) {
    return false;
  }
  let id: TweakDBID = record.GetID();
  return id == t"Vehicle.xaires_aston_valkyrie" || id == t"Vehicle.xaires_aston_valkyrie_purchasable";
}

@wrapMethod(hudCarController)
protected cb func OnSpeedValueChanged(speedValue: Float) -> Bool {
  let result: Bool = wrappedMethod(speedValue);
  if XairesAMV_IsTarget(this.m_activeVehicle) {
    let kmh: Float = AbsF(speedValue) * 3.6;
    inkTextRef.SetText(this.m_SpeedValue, IntToString(RoundMath(this.m_kmOn ? kmh : kmh / 1.609344)));
  }
  return result;
}
