// ===========================================================================
//  Aston Martin Valkyrie — service / logging         (pre-rename source)
//  Install path: r6/scripts/xaires_aston_valkyrie/
// ===========================================================================
//  Boot-time registration and log tagging. The tag is what you grep for in
//  cyber_engine_tweaks.log when the scanner shows TEST / one car only
//  (PORT.md §7 troubleshooting).
// ===========================================================================
module XairesAMVF1

public class XairesAMVF1_Service {
  public static func Build() -> String {
    return "F1-interim-v2";
  }

  public static func Tag() -> String {
    return "[XairesAMVF1] ";
  }

  public static func Log(msg: String) -> Void {
    FTLog(XairesAMVF1_Service.Tag() + msg);
  }
}

// Registration hook. Called from the audio path after the metadata copy.
// NOTE: @addMethod is used instead of @wrapMethod on purpose - adding a new
// method always compiles, while wrapping a method that does not exist on this
// game build is a hard redscript error.
@addMethod(VehicleComponent)
public func VC_RegisterAMVService() -> Void {
  // >>> PORT-BODY-START >>>
  // Service registration / audio resource binding after the metadata copy.
  // Restored verbatim from the stock mod by tools/port_to_phoenix.py.
  // See docs/STATUS.md, section "Script bodies".
  // <<< PORT-BODY-END <<<
}
