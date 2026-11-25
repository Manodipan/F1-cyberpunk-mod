module PhoenixTrueSpeedometer

// ============================================================================
// Phoenix True Speedometer - final build
// README: docs/SPEEDOMETER-MOD.md
//
// WHAT IT DOES
//   Replaces the HUD's speed number with the vehicle body's real velocity, in the unit chosen in
//   Mod Settings. The game's own number has been through `speed_to_multiplier`, measured about 2x
//   at the top of its range (277 km/h displayed as 572; 17 s/km = 58.8 m/s displayed as 110-117).
//
// HOW THE SETTINGS WORK  (learned from the framework's own source, not by guessing)
//   Mod Settings writes the chosen value into the class's DEFAULT value in script data:
//       ModSettings.cpp:133  modClass->SetDefaultValue(name, runtimeVar->GetAcceptedValue())
//   A live instance therefore keeps whatever it was constructed with - reading an instance never
//   sees a change. The authoritative store is the ConfigVars the UI edits, and those are readable:
//       ModSettings.GetCategories(mod) / GetVars(mod, category)      ModSettings.reds:4-5
//       ConfigVar.GetName()                                          base class
//       ModConfigVarEnum.GetIndex()  -> Int32                        ModSettings.reds:81
//       ModConfigVarFloat.GetValue() -> Float                        ModSettings.reds:61
//       ModConfigVarBool.GetValue()  -> Bool                         ModSettings.reds:28
//   Every ModSettings call sits behind @if(ModuleExists("ModSettingsModule")) with a no-op twin,
//   because ModSettings.* does not exist when the framework is absent and an unguarded call fails
//   to compile. That is ADE's pattern (settings.reds:610-666).
//
// PROVENANCE OF EVERY CONSTRUCT IN THIS FILE
//   @wrapMethod(hudCarController) / protected cb func OnSpeedValueChanged(...) -> Bool
//                                          Phoenix_aston_valkyrie.reds:23-33 (boots on 2.5)
//   this.m_activeVehicle, this.m_SpeedValue, wrappedMethod, inkTextRef.SetText   same file
//   AbsF, Vector4.Dot, GetLinearVelocity, GetWorldForward                        same file
//   RoundMath, IntToString                                                       same file:30
//   IsDefined, Equals, ClampF, MaxF                                              ADE / car mod
//   FloorF  -> Int32, and Cast<Float>(FloorF(x))                                 ADE:427
//   module <Name> + top-level public static func + plain enum + public let fields ADE settings.reds
//   @runtimeProperty(...) incl. dependency/step/min/max/displayValues             ADE (360 uses)
//   @if(ModuleExists(...)) twins                                                 ADE:610-666
//   for x in array, let reassignment                                             ADE (64 reassigned lets)
//
// DELIBERATELY NOT USED (each one cost a restart to learn)
//   IsPlayerDriven()  - no such method      AbsI()   - not in redscript
//   this.GetGame()    - not on hudCarController         var NAME  - not a local keyword
//   Int32 / Int32     - appears nowhere in compiling code; the formatter uses FloorF instead
//   ToString(Float)   - only ever proven by accident; the formatter replaces it
// ============================================================================

enum PhoenixTS_Unit {
    MPS = 0,
    KMH = 1,
    MPH = 2,
    KNOTS = 3,
    FPS = 4,
    MACH = 5,
    CUSTOM = 6
}

// This class exists ONLY so Mod Settings has fields to render into the tab. Nothing reads it:
// the values are read from the ConfigVars below, which is where the UI actually writes.
// The "ModSettings.mod" value must stay identical to the string used in PhoenixTS_UnitOf & co.
public class PhoenixTS_Settings extends ScriptableSystem {

    @runtimeProperty("ModSettings.mod", "Phoenix True Speedometer")
    @runtimeProperty("ModSettings.displayName", "Slot 1 - unit (the main number)")
    @runtimeProperty("ModSettings.description", "Unit of the main HUD number. m/s = x1.0, km/h = x3.6, mph = x2.23694, knots = x1.94384, ft/s = x3.28084, Mach = 1/343 (Mach 1 = 343 m/s at sea level), custom = your own multiplier. Example: at 58.8 m/s the HUD reads 58.8 for m/s and 212 for km/h.")
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
    @runtimeProperty("ModSettings.description", "How many of your unit per metre per second, used only when slot 1 is custom. m/s 1.0, km/h 3.6, mph 2.23694, knots 1.94384, ft/s 3.28084, Mach 0.00291545 (= 1/343), km/min 0.06, yards/s 1.09361, furlongs/fortnight 6012.9. Rule: 3600 divided by the unit's length in metres. Shown on the HUD as x<multiplier>.")
    @runtimeProperty("ModSettings.category", "Units")
    @runtimeProperty("ModSettings.category.order", "11")
    @runtimeProperty("ModSettings.step", "0.0001")
    @runtimeProperty("ModSettings.min", "0.0001")
    @runtimeProperty("ModSettings.max", "1000.0")
    public let slot1Custom: Float = 1.0;

    @runtimeProperty("ModSettings.mod", "Phoenix True Speedometer")
    @runtimeProperty("ModSettings.displayName", "Slot 2 - show a second unit")
    @runtimeProperty("ModSettings.description", "Adds a second number after slot 1, as 58.8|212. OFF by default: the HUD speed widget holds about four characters, and a second number pushes the text left through the sidebar.")
    @runtimeProperty("ModSettings.category", "Units")
    @runtimeProperty("ModSettings.category.order", "20")
    public let showSlot2: Bool = false;

    @runtimeProperty("ModSettings.mod", "Phoenix True Speedometer")
    @runtimeProperty("ModSettings.displayName", "Slot 2 - unit")
    @runtimeProperty("ModSettings.description", "Unit of the second number. m/s = x1.0, km/h = x3.6, mph = x2.23694, knots = x1.94384, ft/s = x3.28084, Mach = 1/343, custom = the multiplier below.")
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
    @runtimeProperty("ModSettings.description", "How many of your unit per metre per second, used only when slot 2 is custom. m/s 1.0, km/h 3.6, mph 2.23694, knots 1.94384, ft/s 3.28084, Mach 0.00291545 (= 1/343). Rule: 3600 divided by the unit's length in metres.")
    @runtimeProperty("ModSettings.category", "Units")
    @runtimeProperty("ModSettings.category.order", "22")
    @runtimeProperty("ModSettings.step", "0.0001")
    @runtimeProperty("ModSettings.min", "0.0001")
    @runtimeProperty("ModSettings.max", "1000.0")
    public let slot2Custom: Float = 3.6;

    @runtimeProperty("ModSettings.mod", "Phoenix True Speedometer")
    @runtimeProperty("ModSettings.displayName", "Print the unit next to the number")
    @runtimeProperty("ModSettings.description", "OFF by default because the widget holds about four characters (the Aston mod writes 113 into it). ON gives 58.8 m/s, which may clip a character on the left. OFF gives 58.8.")
    @runtimeProperty("ModSettings.category", "Format")
    @runtimeProperty("ModSettings.category.order", "30")
    public let showUnits: Bool = false;
}

// ---------------------------------------------------------------------------
// reading the settings the UI actually wrote (see the header)
// ---------------------------------------------------------------------------
@if(ModuleExists("ModSettingsModule"))
public static func PhoenixTS_ModSettingsPresent() -> Bool {
    return true;
}

@if(!ModuleExists("ModSettingsModule"))
public static func PhoenixTS_ModSettingsPresent() -> Bool {
    return false;
}

@if(ModuleExists("ModSettingsModule"))
public static func PhoenixTS_AnyVar() -> Bool {
    let found: Bool = false;
    for cate in ModSettings.GetCategories(n"Phoenix True Speedometer") {
        for v in ModSettings.GetVars(n"Phoenix True Speedometer", cate) {
            found = true;
        }
    }
    return found;
}

@if(!ModuleExists("ModSettingsModule"))
public static func PhoenixTS_AnyVar() -> Bool {
    return false;
}

@if(ModuleExists("ModSettingsModule"))
public static func PhoenixTS_UnitOf(name: CName, fallback: PhoenixTS_Unit) -> PhoenixTS_Unit {
    for cate in ModSettings.GetCategories(n"Phoenix True Speedometer") {
        for v in ModSettings.GetVars(n"Phoenix True Speedometer", cate) {
            if Equals(name, v.GetName()) {
                let e = v as ModConfigVarEnum;
                if IsDefined(e) {
                    let i: Int32 = e.GetIndex();
                    if i == 1 {
                        return PhoenixTS_Unit.KMH;
                    }
                    if i == 2 {
                        return PhoenixTS_Unit.MPH;
                    }
                    if i == 3 {
                        return PhoenixTS_Unit.KNOTS;
                    }
                    if i == 4 {
                        return PhoenixTS_Unit.FPS;
                    }
                    if i == 5 {
                        return PhoenixTS_Unit.MACH;
                    }
                    if i == 6 {
                        return PhoenixTS_Unit.CUSTOM;
                    }
                    return PhoenixTS_Unit.MPS;
                }
            }
        }
    }
    return fallback;
}

@if(!ModuleExists("ModSettingsModule"))
public static func PhoenixTS_UnitOf(name: CName, fallback: PhoenixTS_Unit) -> PhoenixTS_Unit {
    return fallback;
}

@if(ModuleExists("ModSettingsModule"))
public static func PhoenixTS_FloatOf(name: CName, fallback: Float) -> Float {
    for cate in ModSettings.GetCategories(n"Phoenix True Speedometer") {
        for v in ModSettings.GetVars(n"Phoenix True Speedometer", cate) {
            if Equals(name, v.GetName()) {
                let f = v as ModConfigVarFloat;
                if IsDefined(f) {
                    return f.GetValue();
                }
            }
        }
    }
    return fallback;
}

@if(!ModuleExists("ModSettingsModule"))
public static func PhoenixTS_FloatOf(name: CName, fallback: Float) -> Float {
    return fallback;
}

@if(ModuleExists("ModSettingsModule"))
public static func PhoenixTS_BoolOf(name: CName, fallback: Bool) -> Bool {
    for cate in ModSettings.GetCategories(n"Phoenix True Speedometer") {
        for v in ModSettings.GetVars(n"Phoenix True Speedometer", cate) {
            if Equals(name, v.GetName()) {
                let b = v as ModConfigVarBool;
                if IsDefined(b) {
                    return b.GetValue();
                }
            }
        }
    }
    return fallback;
}

@if(!ModuleExists("ModSettingsModule"))
public static func PhoenixTS_BoolOf(name: CName, fallback: Bool) -> Bool {
    return fallback;
}

// ---------------------------------------------------------------------------
// digits: three significant figures, whole numbers above 100 (owner's rule)
//   212.4 -> "212"   58.83 -> "58.8"   9.876 -> "9.88"   0.1714 -> "0.171"   0.01714 -> "0.0171"
//
// Built with FloorF (Int32) and Cast<Float>(...) only. No Int32 division and no modulo: neither
// appears in any script that compiles on this install, and the last attempt at this function is
// what broke the build.
// ---------------------------------------------------------------------------
public static func PhoenixTS_SigDigits(value: Float) -> Int32 {
    let v: Float = AbsF(value);
    // standing still prints "0", not "0.00000"
    if v < 0.0001 {
        return 0;
    }
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

public static func PhoenixTS_Format(value: Float, decimals: Int32) -> String {
    if decimals <= 0 {
        return IntToString(RoundMath(value));
    }
    let scale: Float = 10.0;
    let scaleI: Int32 = 10;
    if decimals == 2 {
        scale = 100.0;
        scaleI = 100;
    } else if decimals == 3 {
        scale = 1000.0;
        scaleI = 1000;
    } else if decimals == 4 {
        scale = 10000.0;
        scaleI = 10000;
    } else if decimals >= 5 {
        scale = 100000.0;
        scaleI = 100000;
    }
    let whole: Int32 = FloorF(value);
    let frac: Int32 = RoundMath((value - Cast<Float>(whole)) * scale);
    if frac >= scaleI {
        whole = whole + 1;
        frac = frac - scaleI;
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
        let c: Float = ClampF(custom, 0.0001, 1000.0);
        return "x" + PhoenixTS_Format(c, PhoenixTS_SigDigits(c));
    }
    return "m/s";
}

// One slot rendered: the number, then the unit it is really in.
public static func PhoenixTS_Number(mps: Float, unit: PhoenixTS_Unit, custom: Float, withUnit: Bool) -> String {
    let value: Float = mps * PhoenixTS_Factor(unit, custom);
    let number: String = PhoenixTS_Format(value, PhoenixTS_SigDigits(value));
    if !withUnit {
        return number;
    }
    return number + " " + PhoenixTS_Label(unit, custom);
}

// ---------------------------------------------------------------------------
// the HUD
// ---------------------------------------------------------------------------
public static func PhoenixTS_HudText(vehicle: wref<VehicleObject>) -> String {
    let mps: Float = AbsF(Vector4.Dot(vehicle.GetLinearVelocity(), vehicle.GetWorldForward()));
    let unit1: PhoenixTS_Unit = PhoenixTS_UnitOf(n"slot1", PhoenixTS_Unit.MPS);
    let custom1: Float = PhoenixTS_FloatOf(n"slot1Custom", 1.0);
    let labels: Bool = PhoenixTS_BoolOf(n"showUnits", false);
    let slot2on: Bool = PhoenixTS_BoolOf(n"showSlot2", false);
    let slot2: PhoenixTS_Unit = PhoenixTS_UnitOf(n"slot2", PhoenixTS_Unit.KMH);
    let custom2: Float = PhoenixTS_FloatOf(n"slot2Custom", 3.6);
    let first: String = PhoenixTS_Number(mps, unit1, custom1, labels);
    if PhoenixTS_ModSettingsPresent() && !PhoenixTS_AnyVar() {
        return first + "*";
    }
    if !slot2on {
        return first;
    }
    return first + "|" + PhoenixTS_Number(mps, slot2, custom2, labels);
}

@wrapMethod(hudCarController)
protected cb func OnSpeedValueChanged(speedValue: Float) -> Bool {
    let result: Bool = wrappedMethod(speedValue);
    if IsDefined(this.m_activeVehicle) {
        inkTextRef.SetText(this.m_SpeedValue, PhoenixTS_HudText(this.m_activeVehicle));
    }
    return result;
}
