// README: docs/SPEEDOMETER-MOD.md
//
// v3 - BISECT BUILD. The game must boot before it gets a settings tab.
//
// v1 and v2 did not boot. v1 used IsPlayerDriven()/AbsI()/this.GetGame(), which do not exist.
// v2 fixed those but still did not boot, so v2's *structure* is now suspect: it declared a
// `module`, a `public enum` and a `public class ... extends ScriptableSystem`. This file declares
// none of those. The only structural difference left between this file and
// Phoenix_aston_valkyrie.reds - which boots on this machine right now - is the arithmetic, and
// that arithmetic is AbsF/RoundMath/IntToString, all of which that same file already calls.
//
// Shipped behaviour until the boot question is settled: "58.8 m/s | 212 km/h".
// Units, Mach, custom multipliers and the Mod Settings tab live in
// settings/PhoenixTS_Settings.reds.pending - not installed, not compiled, added back one piece at
// a time once the game boots.

// Fixed point to `decimals` places. No AbsI, no Cast, no loop.
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

// The body's own speed, not the HUD's curve-warped value: the game feeds this callback a number
// that has already been through speed_to_multiplier (measured 1.92x at 17 s/km, 2.06x at 572).
public static func PhoenixTS_SpeedText(vehicle: wref<VehicleObject>) -> String {
  let mps: Float = AbsF(Vector4.Dot(vehicle.GetLinearVelocity(), vehicle.GetWorldForward()));
  let kmh: Float = mps * 3.6;
  return PhoenixTS_Format(mps, PhoenixTS_SigDigits(mps)) + " m/s | "
       + PhoenixTS_Format(kmh, PhoenixTS_SigDigits(kmh)) + " km/h";
}

@wrapMethod(hudCarController)
protected cb func OnSpeedValueChanged(speedValue: Float) -> Bool {
  let result: Bool = wrappedMethod(speedValue);
  if IsDefined(this.m_activeVehicle) {
    inkTextRef.SetText(this.m_SpeedValue, PhoenixTS_SpeedText(this.m_activeVehicle));
  }
  return result;
}
