// ===========================================================================
//  Aston Martin Valkyrie — V12 audio binding        (pre-rename source)
//  Install path: r6/scripts/xaires_aston_valkyrie/
//  Requires: redscript + AudioXL (bank xaires_amv.bnk, shared with stock mod)
// ===========================================================================
//  The car's engine sound is a *copy* of a vanilla audio metadata record under a
//  mod-owned name, so the vehicle record can reference it through
//  `player_audio_resource` without touching vanilla data.
//
//  Phoenix rename (PORT.md §4): class/module -> PhoenixAMV, resource name ->
//  phoenix_amv_engine. Wwise events (xamw_*) and the bank stay shared.
// ===========================================================================
module XairesAMVF1

public class XairesAMVF1_Audio {
  // Metadata record name referenced by the YAML (`player_audio_resource`).
  public static func Resource() -> CName {
    return n"xaires_amv_engine";
  }

  // Vanilla record the metadata is cloned from. Same bank, same xamw_* events.
  public static func Donor() -> CName {
    return n"v_car_rayfield_caliburn";
  }
}

// Clone an audio metadata record under a mod-owned name.
@addMethod(VehicleComponent)
public func VC_DeepCopyAudioMetadata(src: CName, dst: CName) -> Bool {
  if Equals(src, dst) {
    return false;
  }
  // >>> PORT-BODY-START >>>
  // Engine-internal audio binding (record reflection + Wwise metadata clone).
  // Restored verbatim from the stock mod by tools/port_to_phoenix.py.
  // See docs/STATUS.md, section "Script bodies".
  // <<< PORT-BODY-END <<<
  return false;
}
