module PhoenixTrueSpeedometer

// README: docs/SPEEDOMETER-MOD.md
//
// One job: put the vehicle's actual velocity on the HUD, in the unit you pick.
//
// Why this exists at all: the game feeds the HUD speed through a `speed_to_multiplier` curve, and
// at the top of its range that curve is about 2x. Measured twice in this repo - 277 km/h real shown
// as 572 (2.06x), and a car timed at 17 s/km (58.8 m/s) whose dial read 110-117 (1.92x). The dial
// is not a speed; it is a curve. The body velocity (GetLinearVelocity projected on the forward
// axis) is the only figure the game does not derive, so that is what gets displayed.
//
// The unit is configurable at runtime through Mod Settings, twice: two independent slots, each with
// a unit and a custom multiplier. Slot 1 is the HUD number. Slot 2 is appended after it, so you can
// see both at once (e.g. "58.8 | 212").

public enum PhoenixTS_Unit {
    MPS = 0,
    KMH = 1,
    MPH = 2,
    KNOTS = 3,
    FPS = 4,
    CUSTOM = 5
}

public class PhoenixTS_Settings extends ScriptableSystem {

    // ------------------------------------------------------------------ slot 1
    @runtimeProperty("ModSettings.mod", "Phoenix True Speedometer")
    @runtimeProperty("ModSettings.displayName", "Slot 1 - unit (main number)")
    @runtimeProperty("ModSettings.description", "The unit of the HUD speed number. CUSTOM uses slot 1's multiplier below.")
    @runtimeProperty("ModSettings.category", "Units")
    @runtimeProperty("ModSettings.category.order", "10")
    @runtimeProperty("ModSettings.displayValues.MPS", "m/s")
    @runtimeProperty("ModSettings.displayValues.KMH", "km/h")
    @runtimeProperty("ModSettings.displayValues.MPH", "mph")
    @runtimeProperty("ModSettings.displayValues.KNOTS", "knots")
    @runtimeProperty("ModSettings.displayValues.FPS", "ft/s")
    @runtimeProperty("ModSettings.displayValues.CUSTOM", "custom")
    public let slot1: PhoenixTS_Unit = PhoenixTS_Unit.MPS;

    @runtimeProperty("ModSettings.mod", "Phoenix True Speedometer")
    @runtimeProperty("ModSettings.displayName", "Slot 1 - custom multiplier")
    @runtimeProperty("ModSettings.description", "How many of your unit per m/s. km/h = 3.6, mph = 2.23694, knots = 1.94384, ft/s = 3.28084, km/min = 0.06. Only used when slot 1 is CUSTOM.")
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
    @runtimeProperty("ModSettings.description", "Appends a second number after slot 1, e.g. '58.8 | 212'. Turn off for one number only.")
    @runtimeProperty("ModSettings.category", "Units")
    @runtimeProperty("ModSettings.category.order", "20")
    public let showSlot2: Bool = true;

    @runtimeProperty("ModSettings.mod", "Phoenix True Speedometer")
    @runtimeProperty("ModSettings.displayName", "Slot 2 - unit")
    @runtimeProperty("ModSettings.description", "The unit of the second number.")
    @runtimeProperty("ModSettings.category", "Units")
    @runtimeProperty("ModSettings.category.order", "21")
    @runtimeProperty("ModSettings.displayValues.MPS", "m/s")
    @runtimeProperty("ModSettings.displayValues.KMH", "km/h")
    @runtimeProperty("ModSettings.displayValues.MPH", "mph")
    @runtimeProperty("ModSettings.displayValues.KNOTS", "knots")
    @runtimeProperty("ModSettings.displayValues.FPS", "ft/s")
    @runtimeProperty("ModSettings.displayValues.CUSTOM", "custom")
    @runtimeProperty("ModSettings.dependency", "showSlot2")
    public let slot2: PhoenixTS_Unit = PhoenixTS_Unit.KMH;

    @runtimeProperty("ModSettings.mod", "Phoenix True Speedometer")
    @runtimeProperty("ModSettings.displayName", "Slot 2 - custom multiplier")
    @runtimeProperty("ModSettings.description", "How many of your unit per m/s. Only used when slot 2 is CUSTOM.")
    @runtimeProperty("ModSettings.category", "Units")
    @runtimeProperty("ModSettings.category.order", "22")
    @runtimeProperty("ModSettings.step", "0.0001")
    @runtimeProperty("ModSettings.min", "0.0001")
    @runtimeProperty("ModSettings.max", "1000.0")
    @runtimeProperty("ModSettings.dependency", "slot2")
    public let slot2Custom: Float = 3.6;

    // ------------------------------------------------------------------ format
    @runtimeProperty("ModSettings.mod", "Phoenix True Speedometer")
    @runtimeProperty("ModSettings.displayName", "Decimal places")
    @runtimeProperty("ModSettings.description", "0 = whole numbers, 1 = one decimal (58.8), 2 = two (58.75).")
    @runtimeProperty("ModSettings.category", "Format")
    @runtimeProperty("ModSettings.category.order", "30")
    @runtimeProperty("ModSettings.step", "1")
    @runtimeProperty("ModSettings.min", "0")
    @runtimeProperty("ModSettings.max", "2")
    public let decimals: Int32 = 1;

    @runtimeProperty("ModSettings.mod", "Phoenix True Speedometer")
    @runtimeProperty("ModSettings.displayName", "Only in player vehicles")
    @runtimeProperty("ModSettings.description", "Leave the HUD alone when the vehicle is not driven by the player (passenger seats, cutscenes, AVs).")
    @runtimeProperty("ModSettings.category", "Format")
    @runtimeProperty("ModSettings.category.order", "31")
    public let playerVehiclesOnly: Bool = true;
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
    if Equals(unit, PhoenixTS_Unit.CUSTOM) {
        return ClampF(custom, 0.0001, 1000.0);
    }
    return 1.0;
}

public static func PhoenixTS_Format(value: Float, decimals: Int32) -> String {
    if decimals <= 0 {
        return IntToString(RoundMath(value));
    }
    let scale: Int32 = 10;
    if decimals >= 2 {
        scale = 100;
    }
    let scaled: Int32 = RoundMath(value * Cast<Float>(scale));
    let whole: Int32 = scaled / scale;
    let frac: Int32 = AbsI(scaled % scale);
    let pad: String = "";
    if (decimals >= 2) && (frac < 10) {
        pad = "0";
    }
    return IntToString(whole) + "." + pad + IntToString(frac);
}

// the game's dial value is curve-warped; the body is not
public static func PhoenixTS_BodyMps(vehicle: wref<VehicleObject>) -> Float {
    return AbsF(Vector4.Dot(vehicle.GetLinearVelocity(), vehicle.GetWorldForward()));
}

public static func PhoenixTS_SettingsOf(game: GameInstance) -> ref<PhoenixTS_Settings> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(NameOf<PhoenixTS_Settings>()) as PhoenixTS_Settings;
}

public static func PhoenixTS_HudText(game: GameInstance, vehicle: wref<VehicleObject>) -> String {
    let s: ref<PhoenixTS_Settings> = PhoenixTS_SettingsOf(game);
    if !IsDefined(s) {
        return "";
    }
    let mps: Float = PhoenixTS_BodyMps(vehicle);
    let first: String = PhoenixTS_Format(mps * PhoenixTS_Factor(s.slot1, s.slot1Custom), s.decimals);
    if !s.showSlot2 {
        return first;
    }
    let second: String = PhoenixTS_Format(mps * PhoenixTS_Factor(s.slot2, s.slot2Custom), s.decimals);
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
    let s: ref<PhoenixTS_Settings> = PhoenixTS_SettingsOf(this.GetGame());
    if IsDefined(s) && s.playerVehiclesOnly && !vehicle.IsPlayerDriven() {
        return result;
    }
    let text: String = PhoenixTS_HudText(this.GetGame(), vehicle);
    if NotEquals(text, "") {
        inkTextRef.SetText(this.m_SpeedValue, text);
    }
    return result;
}
