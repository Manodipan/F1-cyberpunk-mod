module PhoenixTrueSpeedometer

// README: docs/SPEEDOMETER-MOD.md
//
// One job: put the vehicle's actual velocity on the HUD, in the unit you pick.
//
// The game feeds the HUD speed through a `speed_to_multiplier` curve that is about 2x at the top of
// its range (measured: 277 km/h shown as 572, and 17 s/km = 58.8 m/s shown as 110-117). The body
// velocity - GetLinearVelocity projected on the forward axis - is the only figure the game does not
// derive, so that is what gets displayed.
//
// v2 (2.5): every API here appears in a file this game already compiles on 2.5 - the car mod and
// ADE - because this sandbox cannot compile redscript and a single bad symbol disables *all*
// scripts. What v1 got wrong: IsPlayerDriven(), AbsI() and this.GetGame() do not exist on this
// path, and the formatter leaned on them. NameOf<T>() is fine (ADE debug.reds:56).

public enum PhoenixTS_Unit {
    MPS = 0,
    KMH = 1,
    MPH = 2,
    KNOTS = 3,
    FPS = 4,
    MACH = 5,
    CUSTOM = 6
}

public class PhoenixTS_Settings extends ScriptableSystem {

    // ------------------------------------------------------------------ slot 1
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

    // ------------------------------------------------------------------ slot 2
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

    // ------------------------------------------------------------------ format
    @runtimeProperty("ModSettings.mod", "Phoenix True Speedometer")
    @runtimeProperty("ModSettings.displayName", "Print the unit next to the number")
    @runtimeProperty("ModSettings.description", "On: 58.8 m/s | 212 km/h - the HUD names the unit, so nothing has to be remembered. Off: 58.8 | 212 - shorter, if the label overflows your HUD scale. Custom slots are labelled x<multiplier>. Numbers always carry three significant digits, or whole numbers above 100.")
    @runtimeProperty("ModSettings.category", "Format")
    @runtimeProperty("ModSettings.category.order", "30")
    public let showUnits: Bool = true;
}

// ---------------------------------------------------------------------------
// conversion
// ---------------------------------------------------------------------------
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
        // Mach 1 = 343 m/s at sea level, 15 C
        return 1.0 / 343.0;
    }
    if Equals(unit, PhoenixTS_Unit.CUSTOM) {
        return ClampF(custom, 0.0001, 1000.0);
    }
    return 1.0;
}

// Short labels, because the HUD speed field is one line and not very wide.
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

// Three significant digits, whole numbers above 100 (owner's rule).
//   212 -> "212"   58.83 -> "58.8"   5.883 -> "5.88"   0.1714 -> "0.171"   0.01714 -> "0.0171"
public static func PhoenixTS_SigDigits(value: Float) -> Int32 {
    let v: Float = AbsF(value);
    if v >= 100.0 {
        return 0;
    }
    if v >= 10.0 {
        return 1;
    }
    if v >= 1.0 {
        return 2;
    }
    if v >= 0.1 {
        return 3;
    }
    if v >= 0.01 {
        return 4;
    }
    return 5;
}

// Fixed point to `decimals` places, zero padded. No AbsI and no Cast: both are avoided here because
// the first version of this file did not compile.
public static func PhoenixTS_Format(value: Float, decimals: Int32) -> String {
    if decimals <= 0 {
        return IntToString(RoundMath(value));
    }
    let scale: Int32 = 10;
    let scaleF: Float = 10.0;
    if decimals == 2 {
        scale = 100;
        scaleF = 100.0;
    } else if decimals == 3 {
        scale = 1000;
        scaleF = 1000.0;
    } else if decimals == 4 {
        scale = 10000;
        scaleF = 10000.0;
    } else if decimals >= 5 {
        scale = 100000;
        scaleF = 100000.0;
    }
    let scaled: Int32 = RoundMath(value * scaleF);
    let whole: Int32 = scaled / scale;
    let frac: Int32 = scaled - (whole * scale);
    if frac < 0 {
        return IntToString(whole);
    }
    let pad: String = "";
    if decimals == 2 {
        if frac < 10 {
            pad = "0";
        }
    } else if decimals == 3 {
        if frac < 10 {
            pad = "00";
        } else if frac < 100 {
            pad = "0";
        }
    } else if decimals == 4 {
        if frac < 10 {
            pad = "000";
        } else if frac < 100 {
            pad = "00";
        } else if frac < 1000 {
            pad = "0";
        }
    } else if decimals >= 5 {
        if frac < 10 {
            pad = "0000";
        } else if frac < 100 {
            pad = "000";
        } else if frac < 1000 {
            pad = "00";
        } else if frac < 10000 {
            pad = "0";
        }
    }
    return IntToString(whole) + "." + pad + IntToString(frac);
}

// one slot rendered: the number, then the unit it is actually in
public static func PhoenixTS_Number(mps: Float, unit: PhoenixTS_Unit, custom: Float, withUnit: Bool) -> String {
    let value: Float = mps * PhoenixTS_Factor(unit, custom);
    let number: String = PhoenixTS_Format(value, PhoenixTS_SigDigits(value));
    if !withUnit {
        return number;
    }
    return number + " " + PhoenixTS_Label(unit, custom);
}

// the game's dial value is curve-warped; the body is not
public static func PhoenixTS_BodyMps(vehicle: wref<VehicleObject>) -> Float {
    return AbsF(Vector4.Dot(vehicle.GetLinearVelocity(), vehicle.GetWorldForward()));
}

public static func PhoenixTS_Settings() -> ref<PhoenixTS_Settings> {
    return GameInstance.GetScriptableSystemsContainer(GetGameInstance()).Get(NameOf<PhoenixTS_Settings>()) as PhoenixTS_Settings;
}

// Defaults if the settings system cannot be reached: m/s | km/h, the arrangement this mod ships with.
public static func PhoenixTS_HudText(vehicle: wref<VehicleObject>) -> String {
    let mps: Float = PhoenixTS_BodyMps(vehicle);
    let s: ref<PhoenixTS_Settings> = PhoenixTS_Settings();
    if !IsDefined(s) {
        return PhoenixTS_Number(mps, PhoenixTS_Unit.MPS, 1.0, true) + " | " + PhoenixTS_Number(mps, PhoenixTS_Unit.KMH, 3.6, true);
    }
    let first: String = PhoenixTS_Number(mps, s.slot1, s.slot1Custom, s.showUnits);
    if !s.showSlot2 {
        return first;
    }
    let second: String = PhoenixTS_Number(mps, s.slot2, s.slot2Custom, s.showUnits);
    return first + " | " + second;
}

// ---------------------------------------------------------------------------
// the HUD
// ---------------------------------------------------------------------------
@wrapMethod(hudCarController)
protected cb func OnSpeedValueChanged(speedValue: Float) -> Bool {
    let result: Bool = wrappedMethod(speedValue);
    let vehicle: wref<VehicleObject> = this.m_activeVehicle;
    if !IsDefined(vehicle) {
        return result;
    }
    let text: String = PhoenixTS_HudText(vehicle);
    if NotEquals(text, "") {
        inkTextRef.SetText(this.m_SpeedValue, text);
    }
    return result;
}
