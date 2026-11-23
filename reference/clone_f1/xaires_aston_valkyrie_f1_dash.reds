// ===========================================================================
//  Aston Martin Valkyrie — dashboard widgets        (pre-rename source)
//  Install path: r6/scripts/xaires_aston_valkyrie/
// ===========================================================================
//  Widget names come from the car's own dashboard .inkwidget inside the shared
//  .archive. They are NOT renamed for Phoenix (PORT.md §4 "Keep shared").
// ===========================================================================
module XairesAMVF1

public class XairesAMVF1_Widgets {
  public static func Gear() -> CName {
    return n"amvGear";
  }

  public static func Led() -> CName {
    return n"amvLed";
  }

  public static func Rev() -> CName {
    return n"amvRev";
  }
}

// Push speed / gear / redline state into the Valkyrie dashboard.
@addMethod(VehicleComponent)
public func VC_UpdateAMVDash(speed: Float, gear: Int32, redline: Bool) -> Void {
  // >>> PORT-BODY-START >>>
  // HUD widget lookup + per-frame update of amvGear / amvLed / amvRev.
  // Restored verbatim from the stock mod by tools/port_to_phoenix.py.
  // See docs/STATUS.md, section "Script bodies".
  // <<< PORT-BODY-END <<<
}
