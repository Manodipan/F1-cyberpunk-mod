// README: docs/SPEEDOMETER-MOD.md
//
// STEP A - the smallest file that can show a live speed.
//
// Three builds have now failed to compile (or at least shown the error popup): v1 with
// IsPlayerDriven()/AbsI()/this.GetGame(), v2 with the same fixed but adding a module, an enum and a
// ScriptableSystem, v3 with those removed but keeping my own fixed-point formatter.
//
// So this build contains *nothing* of mine. Every line below already exists, verbatim, in
// Phoenix_aston_valkyrie.reds - which compiles on the target install today:
//
//   PhoenixAMV_FwdSpeed      -> AbsF(Vector4.Dot(v.GetLinearVelocity(), v.GetWorldForward()))
//   OnSpeedValueChanged wrap -> @wrapMethod(hudCarController) + protected cb func ... -> Bool
//   HUD write                -> inkTextRef.SetText(this.m_SpeedValue, IntToString(RoundMath(x)))
//   guard                    -> IsDefined(this.m_activeVehicle)
//
// The output is whole numbers only: "212 km/h | 58 m/s". No three-significant-digit rule yet -
// that arithmetic (my own integer formatting) is the next thing to add, and only after this boots.

public static func PhoenixTS_SpeedText(vehicle: wref<VehicleObject>) -> String {
  let mps: Float = AbsF(Vector4.Dot(vehicle.GetLinearVelocity(), vehicle.GetWorldForward()));
  return IntToString(RoundMath(mps * 3.6)) + " km/h | " + IntToString(RoundMath(mps)) + " m/s";
}

@wrapMethod(hudCarController)
protected cb func OnSpeedValueChanged(speedValue: Float) -> Bool {
  let result: Bool = wrappedMethod(speedValue);
  if IsDefined(this.m_activeVehicle) {
    inkTextRef.SetText(this.m_SpeedValue, PhoenixTS_SpeedText(this.m_activeVehicle));
  }
  return result;
}
