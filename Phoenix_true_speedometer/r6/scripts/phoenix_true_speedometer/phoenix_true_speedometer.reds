module PhoenixTrueSpeedometer

// README: docs/SPEEDOMETER-MOD.md
//
// STEP B - the settings layer, with step A's proven number formatting.
//
// History, because each step is one variable:
//   v1  IsPlayerDriven()/AbsI()/this.GetGame()      -> popup
//   v2  those fixed + module + public enum + ScriptableSystem + my formatter -> popup
//   v3  settings removed, my formatter kept         -> popup
//   A   settings and formatter both removed         -> boots
//   B   this file: settings back, formatter still out
//
// Two suspects are now isolated and both are addressed here:
//   1. v3 failed with no settings at all, so its formatter was at fault. This build has none.
//      The one thing v3 did that nothing in ADE does: it split a `return` over two lines with a
//      leading `+`. Every statement here is on one line.
//   2. v2 declared `public enum`; ADE declares `enum DrivingAIType` (plain) and then
//      `public let drivingAI: DrivingAIType`. This file copies that exactly.
//
// Numbers are whole, borrowed verbatim from the build that boots:
//   IntToString(RoundMath(mps * 3.6))   <- Phoenix_aston_valkyrie.reds:30
// Three significant digits come back in step C, once this boots.

enum PhoenixTS_Unit {
    MPS = 0,
    KMH = 1,
    MPH = 2,
    KNOTS = 3,
    FPS = 4,
    MACH = 5,
    CUSTOM = 6
}

public class PhoenixTS_Settings extends ScriptableSystem {

    @runtimeProperty("ModSettings.mod", "Phoenix True Speedometer")
    @runtimeProperty("ModSettings.displayName", "Slot 1 - unit (main number)")
    @runtimeProperty("ModSettings.description", "The unit of the main HUD number. m/s = x1.0  |  km/h = x3.6  |  mph = x2.23694  |  knots = x1.94384  |  ft/s = x3.28084  |  Mach = 1/343 (Mach 1 = 343 m/s). Pick CUSTOM to type your own multiplier. The HUD prints the unit next to the number, so what you pick is what you see.")
    @runtimeProperty("ModSettings.category", "Units")
    @runtimeProperty("ModSettings.category.order", "10")
    @runtimeProperty("ModSettings.displayValues.MPS", "m/s")
    @runtimeProperty("ModSettings.displayValues.KMH", "km/h")
    @runtimeProperty("ModSettings.displayValues.MPH", "mph")
    @runtimeProperty("ModSettings.displayValues.KNOTS", "knots")
    @runtimeProperty("ModSettings.displayValues.FPS", "ft/s")
    @runtimeProperty("ModSettings.displayValues.MACH", "Mach")
    @runtimeProperty("ModSettings.displayValues.CUSTOM", "custom")
    public let slot1: PhoenixTS_Unit = PhoenixTS_Unit.MPS;

    @runtimeProperty("ModSettings.mod", "Phoenix True Speedometer")
    @runtimeProperty("ModSettings.displayName", "Slot 1 - custom multiplier")
    @runtimeProperty("ModSettings.description", "How many of your unit per metre per second - only used when slot 1 is CUSTOM. m/s 1.0  |  km/h 3.6  |  mph 2.23694  |  knots 1.94384  |  ft/s 3.28084  |  Mach 0.00291545 (= 1/343)  |  km/min 0.06  |  yards/s 1.09361  |  furlongs/fortnight 6012.9. Rule: 3600 divided by the unit's length in metres. A custom slot is labelled x<multiplier> on the HUD.")
    @runtimeProperty("ModSettings.category", "Units")
    @runtimeProperty("ModSettings.category.order", "11")
    @runtimeProperty("ModSettings.step", "0.0001")
    @runtimeProperty("ModSettings.min", "0.0001")
    @runtimeProperty("ModSettings.max", "1000.0")
    @runtimeProperty("ModSettings.dependency", "slot1")
    public let slot1Custom: Float = 1.0;

    @runtimeProperty("ModSettings.mod", "Phoenix True Speedometer")
    @runtimeProperty("ModSettings.displayName", "Slot 2 - show a second unit")
    @runtimeProperty("ModSettings.description", "Appends a second number after slot 1, e.g. '58.8 m/s | 212 km/h'. Turn off for one number only.")
    @runtimeProperty("ModSettings.category", "Units")
    @runtimeProperty("ModSettings.category.order", "20")
    public let showSlot2: Bool = true;

    @runtimeProperty("ModSettings.mod", "Phoenix True Speedometer")
    @runtimeProperty("ModSettings.displayName", "Slot 2 - unit")
    @runtimeProperty("ModSettings.description", "The unit of the second number. m/s = x1.0  |  km/h = x3.6  |  mph = x2.23694  |  knots = x1.94384  |  ft/s = x3.28084  |  Mach = 1/343. Example HUD: 58.8 m/s | 212 km/h")
    @runtimeProperty("ModSettings.category", "Units")
    @runtimeProperty("ModSettings.category.order", "21")
    @runtimeProperty("ModSettings.displayValues.MPS", "m/s")
    @runtimeProperty("ModSettings.displayValues.KMH", "km/h")
    @runtimeProperty("ModSettings.displayValues.MPH", "mph")
    @runtimeProperty("ModSettings.displayValues.KNOTS", "knots")
    @runtimeProperty("ModSettings.displayValues.FPS", "ft/s")
    @runtimeProperty("ModSettings.displayValues.MACH", "Mach")
    @runtimeProperty("ModSettings.displayValues.CUSTOM", "custom")
    @runtimeProperty("ModSettings.dependency", "showSlot2")
    public let slot2: PhoenixTS_Unit = PhoenixTS_Unit.KMH;

    @runtimeProperty("ModSettings.mod", "Phoenix True Speedometer")
    @runtimeProperty("ModSettings.displayName", "Slot 2 - custom multiplier")
    @runtimeProperty("ModSettings.description", "How many of your unit per metre per second - only used when slot 2 is CUSTOM. m/s 1.0  |  km/h 3.6  |  mph 2.23694  |  knots 1.94384  |  ft/s 3.28084  |  Mach 0.00291545 (= 1/343)  |  km/min 0.06  |  yards/s 1.09361. Rule: 3600 divided by the unit's length in metres.")
    @runtimeProperty("ModSettings.category", "Units")
    @runtimeProperty("ModSettings.category.order", "22")
    @runtimeProperty("ModSettings.step", "0.0001")
    @runtimeProperty("ModSettings.min", "0.0001")
    @runtimeProperty("ModSettings.max", "1000.0")
    @runtimeProperty("ModSettings.dependency", "slot2")
    public let slot2Custom: Float = 3.6;

    @runtimeProperty("ModSettings.mod", "Phoenix True Speedometer")
    @runtimeProperty("ModSettings.displayName", "Print the unit next to the number")
    @runtimeProperty("ModSettings.description", "On: 58.8 m/s | 212 km/h - the HUD names the unit, so nothing has to be remembered. Off: 58.8 | 212 - shorter, if the label overflows your HUD scale. Custom slots are labelled x<multiplier>.")
    @runtimeProperty("ModSettings.category", "Format")
    @runtimeProperty("ModSettings.category.order", "30")
    public let showUnits: Bool = true;
}

public static func PhoenixTS_Factor(unit: PhoenixTS_Unit, custom: Float) -> Float {
    if Equals(unit, PhoenixTS_Unit.KMH) {
        return 3.6;
    }
    if Equals(unit, PhoenixTS_Unit.MPH) {
        return 2.23694;
    }
    if Equals(unit, PhoenixTS_Unit.KNOTS) {
        return 1.94384;
    }
    if Equals(unit, PhoenixTS_Unit.FPS) {
        return 3.28084;
    }
    if Equals(unit, PhoenixTS_Unit.MACH) {
        return 1.0 / 343.0;
    }
    if Equals(unit, PhoenixTS_Unit.CUSTOM) {
        return ClampF(custom, 0.0001, 1000.0);
    }
    return 1.0;
}

public static func PhoenixTS_Label(unit: PhoenixTS_Unit, custom: Float) -> String {
    if Equals(unit, PhoenixTS_Unit.KMH) {
        return "km/h";
    }
    if Equals(unit, PhoenixTS_Unit.MPH) {
        return "mph";
    }
    if Equals(unit, PhoenixTS_Unit.KNOTS) {
        return "kn";
    }
    if Equals(unit, PhoenixTS_Unit.FPS) {
        return "ft/s";
    }
    if Equals(unit, PhoenixTS_Unit.MACH) {
        return "Mach";
    }
    if Equals(unit, PhoenixTS_Unit.CUSTOM) {
        return "x" + ToString(ClampF(custom, 0.0001, 1000.0));
    }
    return "m/s";
}

// whole numbers for now - the exact expression that boots in step A
public static func PhoenixTS_Number(mps: Float, unit: PhoenixTS_Unit, custom: Float, withUnit: Bool) -> String {
    let value: Float = mps * PhoenixTS_Factor(unit, custom);
    let number: String = IntToString(RoundMath(value));
    if !withUnit {
        return number;
    }
    return number + " " + PhoenixTS_Label(unit, custom);
}

public static func PhoenixTS_SettingsOf() -> ref<PhoenixTS_Settings> {
    return GameInstance.GetScriptableSystemsContainer(GetGameInstance()).Get(NameOf<PhoenixTS_Settings>()) as PhoenixTS_Settings;
}

public static func PhoenixTS_HudText(vehicle: wref<VehicleObject>) -> String {
    let mps: Float = AbsF(Vector4.Dot(vehicle.GetLinearVelocity(), vehicle.GetWorldForward()));
    let s: ref<PhoenixTS_Settings> = PhoenixTS_SettingsOf();
    if !IsDefined(s) {
        return IntToString(RoundMath(mps * 3.6)) + " km/h | " + IntToString(RoundMath(mps)) + " m/s";
    }
    let first: String = PhoenixTS_Number(mps, s.slot1, s.slot1Custom, s.showUnits);
    if !s.showSlot2 {
        return first;
    }
    return first + " | " + PhoenixTS_Number(mps, s.slot2, s.slot2Custom, s.showUnits);
}

@wrapMethod(hudCarController)
protected cb func OnSpeedValueChanged(speedValue: Float) -> Bool {
    let result: Bool = wrappedMethod(speedValue);
    if IsDefined(this.m_activeVehicle) {
        inkTextRef.SetText(this.m_SpeedValue, PhoenixTS_HudText(this.m_activeVehicle));
    }
    return result;
}
