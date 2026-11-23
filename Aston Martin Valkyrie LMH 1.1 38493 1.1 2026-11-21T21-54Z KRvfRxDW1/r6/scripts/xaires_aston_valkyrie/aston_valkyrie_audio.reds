// Üretici: aston-valkyrie/audio/wwise_reds_amv.py (Valkyrie betiğinden; elle düzenleme yerine onu çalıştır).
// Aston Martin Valkyrie LMH: motor sesi (Wwise bankası xaires_amv) + sanal şanzıman (ses + kokpit göstergesi; oyunun fiziği değişmez).
// BU DOSYA audio/wwise_reds.py İLE ÜRETİLİR; elle düzenleme.
// 2026-11-09 model baştan: ses (Mercedes F1 V6):
//   20 Acc (gaz) + 20 Dec (gaz kesik) döngüsü + rölanti; karışım / perde / geçişler bankada (aston-valkyrie/audio/model_amv.py ->
//   aston-valkyrie/audio/proje_kur_amv.py, ayrı Wwise projesi wwise_amv). Betik yalnız sanal devri (xamw_rpm = devir / 1000) ve gazı (xamw_gas 0..1) gönderir;
//   genel ses xcm_vol (Xaires's Car Manager).
// Oyunun motor ses kaydı: 911 kopyası "xaires_amv_engine" (tweak player_audio_resource); motor döngüsü / vites / marş boş,
// engineStartEvent / engineStopEvent = xamw_engine_on / xamw_engine_off (oyun aracın üstünde çalar). Kapı, lastik, rüzgâr, korna 911.
// XairesAMV_IsTarget / XairesAMV_FwdSpeed: aston_valkyrie.reds / aston_valkyrie_ekran.reds.

@if(ModuleExists("AudioXL"))
import AudioXL.*
@if(ModuleExists("VehicleCore"))
import VehicleCore.*

public class XairesAMVEngineState extends ScriptableService {
  public let playing: Bool;
  public let ticking: Bool;
  public let grace: Int32;
  public let miss: Int32;
  public let lastRpm: Float;
  public let thr: Float;
  public let on: array<Bool>;   // ses (katman) şu an çalıyor mu (bölgesinde mi)
  public let bfArmed: Bool;     // yüksek devirde gaz açıktı: gaz kesilince patlama
  // sanal şanzıman (ses + kokpit göstergesi; oyunun fiziği değişmez). active: oyuncu bu araçta, değerler geçerli
  public let active: Bool;
  public let vgear: Int32;
  public let vrpm: Float;
  public let vgas: Float;
  public let since: Float;
  public let shifted: Bool;     // bu adımda büyütme oldu
  public let downshifted: Bool; // bu adımda küçültme oldu
  public let input: ref<XairesAMVInput>;
  public let gen: Int32;        // ticker kuşağı: eski zincirden (önceki oturum) kalan adım kendini düşürür
  public let revLatch: Bool;    // el freni duran araçta basıldı: bırakılana kadar serbest devir (yerinde gaz)

  public static func Get() -> ref<XairesAMVEngineState> {
    return GameInstance.GetScriptableServiceContainer().GetService(n"XairesAMVEngineState") as XairesAMVEngineState;
  }

  // ScriptableService save yüklemede yaşamaya devam eder; ses zinciri (DelaySystem) ve gaz dinleyicisi (eski oyuncu) ölür
  // ama ticking / playing / on / input kalırdı -> ikinci save'de ticker hiç başlamıyordu: ses yok, devir gaza tepki vermiyor
  // (2026-11-05 oyun testi). Oturum biterken sıfırla; save araç içinde açıldıysa oturum hazır olunca ticker'ı başlat.
  private cb func OnLoad() {
    GameInstance.GetCallbackSystem()
      .RegisterCallback(n"Session/BeforeEnd", this, n"OnSessionEnd")
      .SetLifetime(CallbackLifetime.Forever);
    GameInstance.GetCallbackSystem()
      .RegisterCallback(n"Session/Ready", this, n"OnSessionReady")
      .SetLifetime(CallbackLifetime.Forever);
  }

  private cb func OnSessionEnd(event: ref<GameSessionEvent>) {
    XairesAMV_EngineReset();
  }

  private cb func OnSessionReady(event: ref<GameSessionEvent>) {
    let player = GetPlayer(GetGameInstance());
    if IsDefined(player) && XairesAMV_IsTarget(GetMountedVehicle(player)) {
      XairesAMV_EngineStartTicker();
    }
  }
}

// gaz / fren girdisi (oyunun Accelerate / Decelerate eksenleri; klavyede 0/1, kolda analog). Tüketmez, oyuna da gider.
public class XairesAMVInput {
  public let gas: Float;
  public let brake: Float;
  public let seen: Bool;
  public let hb: Bool;          // el freni (Handbrake: boşluk / kolda A) basılı

  protected cb func OnAction(action: ListenerAction, consumer: ListenerActionConsumer) -> Bool {
    let name: CName = ListenerAction.GetName(action);
    if Equals(name, n"Accelerate") {
      this.gas = ClampF(ListenerAction.GetValue(action), 0.0, 1.0);
      this.seen = true;
    } else {
      if Equals(name, n"Decelerate") {
        this.brake = ClampF(ListenerAction.GetValue(action), 0.0, 1.0);
      } else {
        if Equals(name, n"Handbrake") {
          // 2026-11-05 (oyun testi 'rev atamıyorum'): yalnız JustPressed olayına güvenme, basılı tutmada değer de 1
          if ListenerAction.IsButtonJustReleased(action) {
            this.hb = false;
          } else {
            if ListenerAction.IsButtonJustPressed(action) || ListenerAction.GetValue(action) > 0.5 {
              this.hb = true;
            }
          }
        }
      }
    }
    return false;
  }
}

@wrapMethod(VehicleComponent)
protected cb func OnMountingEvent(evt: ref<MountingEvent>) -> Bool {
  let result: Bool = wrappedMethod(evt);
  if XairesAMV_IsTarget(this.GetVehicle()) {
    XairesAMV_EngineStartTicker();
  }
  return result;
}

// rölanti (sanal devir). Wwise modeli bunu kayıt devrine eşler: 2000 -> 2046 (kayıt rölantisi), 10000 -> 9914 (Acc üst döngü)
public static func XairesAMV_Idle() -> Float {
  return 2000.0;
}

// sanal şanzıman tavanı (Valkyrie LMH devir sınırı 10000; yol aracı 11100)
public static func XairesAMV_MaxRpm() -> Float {
  return 10000.0;
}

public static func XairesAMV_EngineStartTicker() -> Void {
  let state = XairesAMVEngineState.Get();
  if !IsDefined(state) || state.ticking {
    return;
  }
  state.ticking = true;
  state.gen += 1;
  state.grace = 60;
  state.miss = 0;
  state.vgear = 1;
  state.vrpm = XairesAMV_Idle();
  state.vgas = 0.0;
  state.since = 9.0;
  state.shifted = false;
  state.downshifted = false;
  state.bfArmed = false;
  state.revLatch = false;
  let player = GetPlayer(GetGameInstance());
  if IsDefined(player) && !IsDefined(state.input) {
    state.input = new XairesAMVInput();
    player.RegisterInputListener(state.input, n"Accelerate");
    player.RegisterInputListener(state.input, n"Decelerate");
    player.RegisterInputListener(state.input, n"Handbrake");
  }
  XairesAMV_NextTick(state);
}

// sonraki adım (50 ms), bu kuşağın numarasıyla
public static func XairesAMV_NextTick(state: ref<XairesAMVEngineState>) -> Void {
  let tick = new XairesAMVEngineTick();
  tick.gen = state.gen;
  GameInstance.GetDelaySystem(GetGameInstance()).DelayCallback(tick, 0.05, false);
}

// oturum sonu (save yükleme / ana menü): sesi kapat, dinleyiciyi bırak, durumu ilk hâline getir
public static func XairesAMV_EngineReset() -> Void {
  let state = XairesAMVEngineState.Get();
  if !IsDefined(state) {
    return;
  }
  XairesAMV_EngineStop();
  let player = GetPlayer(GetGameInstance());
  if IsDefined(player) && IsDefined(state.input) {
    player.UnregisterInputListener(state.input);
  }
  state.input = null;
  state.ticking = false;
  state.playing = false;
  state.active = false;
  state.lastRpm = 0.0;
  state.gen += 1;
  ArrayClear(state.on);
}

// sanal vitesin 8100 devirdeki hızı (m/s) = tweak'teki vites maxSpeed değerleri (gen_yaml.py GEARS, 7 ileri sıralı)
public static func XairesAMV_GearSpeed(g: Int32) -> Float {
  switch g {
    case 1:
      return 25.0;
    case 2:
      return 36.1;
    case 3:
      return 47.2;
    case 4:
      return 58.3;
    case 5:
      return 69.4;
    case 6:
      return 80.6;
    default:
      return 91.7;
  }
}

// Sanal şanzıman adımı (50 ms): hafif gazda ~4800'de büyütür, tam gazda ~9700'e kadar çevirir, kickdown yok;
// gaz kesince vitesi tutar (motor freni), frende ~4500'de küçültür. Boşta tam gaz limitere (10000) kadar çıkar.
// Devir = hız x vites oranı; kalkışta debriyaj kayması. gameGear: oyunun vitesi (< 0 R, 0 N).
public static func XairesAMV_GearboxStep(state: ref<XairesAMVEngineState>, v: Float, gasIn: Float, brake: Float, gameGear: Int32) -> Void {
  state.vgas += (gasIn - state.vgas) * 0.18127;             // 1 - exp(-0.05 / 0.25)
  let g: Float = state.vgas;
  let idle: Float = XairesAMV_Idle();
  state.since += 0.05;
  let target: Float;
  let k: Float;
  if gameGear == 0 {
    target = idle + g * (XairesAMV_MaxRpm() - idle);      // boş: serbest devir
    k = 0.18127;
    state.vgear = 1;
  } else {
    if gameGear < 0 {
      state.vgear = 1;
    } else {
      if state.since >= 0.6 {
        let r: Float = v * 9900.0 / XairesAMV_GearSpeed(state.vgear);
        let up: Float = 4800.0 + 4900.0 * PowF(g, 1.6);
        let dn: Float = brake > 0.3 ? 4500.0 : (gasIn > 0.05 ? idle : 4200.0);   // 2026-11-07 Plan2 Oturum 1: gazdayken küçültme yok (eski 2200+3000*g*g tam gazda 5200 = gizli kickdown)
        if state.vgear < 7 && ((gasIn > 0.05 && r > up) || r > 9200.0) {
          state.vgear += 1;
          state.since = 0.0;
          state.shifted = true;
        } else {
          if state.vgear > 1 && r < dn {
            state.vgear -= 1;
            state.since = 0.0;
            state.downshifted = true;
          }   // 2026-11-07 Oturum 1: tam gazda kickdown kaldırıldı (kullanıcı: kökleyince vites düşürmesin)
        }
      }
    }
    target = v * 9900.0 / XairesAMV_GearSpeed(state.vgear);
    if state.vgear == 1 && v < 6.0 {
      target = MaxF(target, idle + 2800.0 * g);             // kalkış: debriyaj kayması
    }
    k = target > state.vrpm ? 0.56540 : 0.46474;            // 1 - exp(-0.05 / 0.06), 1 - exp(-0.05 / 0.08)
  }
  target = ClampF(target, idle, XairesAMV_MaxRpm());
  state.vrpm += (target - state.vrpm) * k;
}

// 50 ms'de bir: oyuncu bu araçta mı -> hız/gaz/kamera oku, sanal şanzıman, sesi güncelle; inince sesi kapat ve dur.
// Ses ancak 10 ardışık kaçırmada (0.5 s) kapanır (Bolide oyun testi: tek karelik okuma hatası sesi kesiyordu).
public class XairesAMVEngineTick extends DelayCallback {
  public let gen: Int32;

  public func Call() -> Void {
    let gi = GetGameInstance();
    let state = XairesAMVEngineState.Get();
    if !IsDefined(state) || this.gen != state.gen {
      return;
    }
    let player = GetPlayer(gi);
    let vehicle: wref<VehicleObject> = IsDefined(player) ? GetMountedVehicle(player) : null;
    if !XairesAMV_IsTarget(vehicle) {
      if state.grace > 0 && !state.playing {        // binme animasyonu sürüyor olabilir
        state.grace -= 1;
        XairesAMV_NextTick(state);
        return;
      }
      state.miss += 1;
      if state.miss < 10 {
        XairesAMV_NextTick(state);
        return;
      }
      XairesAMV_EngineStop();
      state.ticking = false;
      state.active = false;
      if IsDefined(player) && IsDefined(state.input) {
        player.UnregisterInputListener(state.input);
      }
      state.input = null;
      return;
    }
    state.miss = 0;
    let bb = vehicle.GetBlackboard();
    let v: Float = AbsF(bb.GetFloat(GetAllBlackboardDefs().Vehicle.SpeedValue));
    let gameGear: Int32 = bb.GetInt(GetAllBlackboardDefs().Vehicle.GearValue);
    let rawGear: Int32 = gameGear;   // teşhis: oyunun ham vitesi (ileri vites düzeltmesinden önce)
    let gameRpm: Float = bb.GetFloat(GetAllBlackboardDefs().Vehicle.RPMValue);
    // frende oyunun vitesi araç hâlâ ileri giderken R'ye düşüyor: ileri vites say (sanal şanzıman küçültür, fren gaz sayılmaz)
    if gameGear < 0 && XairesAMV_FwdSpeed(vehicle) > 0.5 {
      gameGear = 1;
    }
    // girdi yoksa (dinleyici olay almadıysa) eski yöntem: gaz oranı oyun devrinin değişim hızından
    if state.lastRpm <= 0.0 {
      state.lastRpm = gameRpm;
      state.thr = 0.0;
    }
    let slope: Float = (gameRpm - state.lastRpm) / 0.05;
    // 2026-11-07 Oturum 6 (oyun testi: ilk binişte motor max devirde gibi): tahmin 0.5'ten başlıyordu, binişte marşla oyun
    // devri yükselince 1'e çıkıp boştaki sanal devri tavana götürüyordu -> tahmin 0'dan, yalnız araç giderken (> 1 m/s)
    let thrT: Float = v > 1.0 ? ClampF(0.5 + slope / 1500.0, 0.0, 1.0) : 0.0;
    state.thr += (thrT - state.thr) * 0.3;
    state.lastRpm = gameRpm;
    let gas: Float = state.thr;
    let brake: Float = 0.0;
    if IsDefined(state.input) && state.input.seen {
      gas = gameGear < 0 ? state.input.brake : state.input.gas;    // geri viteste Decelerate = gaz
      brake = gameGear < 0 ? 0.0 : state.input.brake;
    }
    // yerinde gaz (Sesto oyun testi 2026-11-05: el freni + gaz duran araçta 1. vitesin debriyaj kaymasıyla ~4000'de kalıyordu,
    // oyunun göstergesi yükselirken ses / kadran yükselmiyordu): boştaki gibi serbest devir, limitere kadar.
    // Dinleyici el frenini kaçırırsa: duran araçta oyunun devri yüksekse de (gaz oyunun devrinden).
    let hb: Bool = IsDefined(state.input) && state.input.hb;
    // 2026-11-05: el freni + gazda araç patinajla kayıyor, v 1.5 m/s'yi aşınca vites hesabına (kayma tavanı ~4900)
    // dönüyordu -> el freniyle 5 m/s (18 km/h) altı serbest devir; dinleyici kaçırırsa 1 m/s altı + yüksek oyun devri.
    // 2026-11-06 (oyun testi 'hâlâ rev atamıyorum'): dört çeker, el freni yalnız arkada -> el freni + gazda ön tekerler aracı
    // çekiyor, hız 5 m/s'yi geçince vites hesabına dönüyordu. Mandal: el freni duran araçta (< 1.5 m/s) basılınca kurulur,
    // el freni bırakılana kadar hızdan bağımsız serbest devir. Hızda çekilen el freni (drift) mandalı kurmaz.
    if !hb {
      state.revLatch = false;
    } else {
      if v < 1.5 {
        state.revLatch = true;
      }
    }
    let rev: Bool = state.revLatch || (gameGear >= 0 && v < 1.0 && gameRpm > 3000.0 && (!IsDefined(state.input) || !state.input.seen || state.input.gas > 0.05));   // 2026-11-07 Oturum 6: gaza basılıyken (dinleyici varsa)
    if state.revLatch {
      gas = MaxF(gas, state.input.gas);
      brake = 0.0;
    } else {
      if rev {
        gas = MaxF(gas, ClampF((gameRpm - 1000.0) / 7650.0, 0.0, 1.0));
      }
    }
    XairesAMV_GearboxStep(state, v, gas, brake, rev ? 0 : gameGear);
    state.active = true;
    // kamera: araçtan uzaksa 3. şahıs (dış ses), değilse kokpit (iç ses); açı aracın arka yönüne göre
    let cam: Transform;
    GameInstance.GetCameraSystem(gi).GetActiveCameraWorldTransform(cam);
    let d: Vector4 = cam.position - vehicle.GetWorldPosition();
    let dist: Float = Vector4.Length(d);
    let cone: Float = 0.0;
    if dist > 0.01 {
      cone = AcosF(ClampF(-Vector4.Dot(vehicle.GetWorldForward(), d) / dist, -1.0, 1.0)) * 57.29578;
    }
    XairesAMV_EngineUpdate(state.vrpm, state.vgas, cone, dist, dist > 2.5);
    XairesAMV_NextTick(state);
  }
}

// kokpit devir çubuğu: oyunun devri yerine sanal devir (bu araçtayken)
@wrapMethod(tachometerLogicController)
public final func OnRpmValueChanged(newRPM: Float) -> Void {
  let state = XairesAMVEngineState.Get();
  if IsDefined(state) && state.active {
    wrappedMethod(state.vrpm);
  } else {
    wrappedMethod(newRPM);
  }
}

@if(ModuleExists("AudioXL"))
public static func XairesAMV_EngineUpdate(r: Float, t: Float, cone: Float, dist: Float, tpp: Bool) -> Void {
  let state = XairesAMVEngineState.Get();
  if IsDefined(state) {
    state.playing = true;
  }
  XairesAMV_WwiseSend(r, t);
}

@if(!ModuleExists("AudioXL"))
public static func XairesAMV_EngineUpdate(r: Float, t: Float, cone: Float, dist: Float, tpp: Bool) -> Void {}

@if(ModuleExists("AudioXL"))
public static func XairesAMV_EngineStop() -> Void {
  let state = XairesAMVEngineState.Get();
  if !IsDefined(state) || !state.playing {
    return;
  }
  state.playing = false;
  state.lastRpm = 0.0;
  // araçtan inince motor açık kalırsa rölantide dursun (döngüleri motor kapanınca oyun xamw_engine_off ile durdurur)
  XairesAMV_WwiseSend(XairesAMV_Idle(), 0.0);
  ArrayClear(state.on);
}

@if(!ModuleExists("AudioXL"))
public static func XairesAMV_EngineStop() -> Void {}

// ---------- sessiz motor ses kaydı (911 kopyası) + Wwise motor olayları ----------
@if(ModuleExists("VehicleCore") && ModuleExists("AudioXL"))
public class XairesAMVAudioMetadata extends ScriptableService {
  private let m_token: ref<ResourceToken>;

  private cb func OnLoad() {
    GameInstance.GetCallbackSystem().RegisterCallback(n"Resource/Load", this, n"OnMetadata")
      .AddTarget(ResourceTarget.Path(r"base\\sound\\metadata\\cooked_metadata.audio_metadata"));
    if AudioXLNative.IsResourceRequested(r"base\\sound\\metadata\\cooked_metadata.audio_metadata") {
      this.m_token = GameInstance.GetResourceDepot().LoadResource(r"base\\sound\\metadata\\cooked_metadata.audio_metadata");
      if IsDefined(this.m_token) {
        this.m_token.RegisterCallback(this, n"OnMetadataReady");
      }
    }
  }

  private cb func OnMetadata(event: ref<ResourceEvent>) {
    this.AddEntry(event.GetResource() as audioCookedMetadataResource);
  }

  private cb func OnMetadataReady(token: ref<ResourceToken>) {
    this.AddEntry(token.GetResource() as audioCookedMetadataResource);
  }

  private func AddEntry(metadata: ref<audioCookedMetadataResource>) -> Void {
    if !IsDefined(metadata) {
      return;
    }
    let source: ref<audioVehicleMetadata>;
    for entry in metadata.entries {
      let vehicle = entry as audioVehicleMetadata;
      if IsDefined(vehicle) {
        if Equals(vehicle.name, n"xaires_amv_engine") {
          return;
        }
        if Equals(vehicle.name, n"v_car_porsche_911_turbo") {
          source = vehicle;
        }
      }
    }
    if !IsDefined(source) {
      return;
    }
    let audio = VC_DeepCopyAudioMetadata(source, n"xaires_amv_engine");
    audio.generalData.revSoundbankName = n"";
    audio.generalData.revElectricSoundbankName = n"";
    audio.generalData.ignitionStartEvent = n"";
    audio.generalData.ignitionEndEvent = n"";
    audio.mechanicalData.engineStartEvent = n"";
    audio.mechanicalData.engineStopEvent = n"";
    audio.mechanicalData.gearUpBeginEvent = n"";
    audio.mechanicalData.gearDownBeginEvent = n"";
    if XairesAMV_Wwise() {
      audio.mechanicalData.engineStartEvent = n"xamw_engine_on";
      audio.mechanicalData.engineStopEvent = n"xamw_engine_off";
    }
    ArrayPush(metadata.entries, audio);
  }
}

// ---------- 2026-11-07 Wwise bankası (audio_wwise\proje_kur.py): yükleme, olay / parametre kaydı (SDH0 EngineAudio yöntemi) ----------
// true: motor döngüleri bankadan; false: eski AudioXL döngüleri (oyundaki AudioXL paketi yerinde).
public static func XairesAMV_Wwise() -> Bool {
  return true;
}

// genel ses (Xaires's Car Manager, 2026-11-07): quest fact xaires_cm_vol = yüzde - 100; yazılmamışsa 0 -> 1.0
public static func XairesAMV_Vol() -> Float {
  let qs = GameInstance.GetQuestsSystem(GetGameInstance());
  if !IsDefined(qs) {
    return 1.0;
  }
  return ClampF(Cast<Float>(qs.GetFact(n"xaires_cm_vol") + 100) / 100.0, 0.0, 3.0);
}

@if(ModuleExists("AudioXL"))
public class XairesAMVWwise extends ScriptableService {
  private let eventsRegistered: Bool;
  private let bankLoaded: Bool;
  private let namesToken: ref<ResourceToken>;

  private cb func OnLoad() {
    if !XairesAMV_Wwise() {
      return;
    }
    GameInstance.GetCallbackSystem().RegisterCallback(n"Resource/Load", this, n"OnNames")
      .AddTarget(ResourceTarget.Path(r"base\\sound\\event\\eventsmetadata.json"));
    if AudioXLNative.IsResourceRequested(r"base\\sound\\event\\eventsmetadata.json") {
      this.namesToken = GameInstance.GetResourceDepot().LoadResource(r"base\\sound\\event\\eventsmetadata.json");
      if IsDefined(this.namesToken) {
        this.namesToken.RegisterCallback(this, n"OnNamesReady");
      }
    }
    GameInstance.GetCallbackSystem().RegisterCallback(n"Session/Ready", this, n"OnSessionReady");
    this.RegisterEvents();
  }

  private cb func OnInitialize() {
    this.RegisterEvents();
  }

  private cb func OnNames(event: ref<ResourceEvent>) {
    this.RegisterParams(event.GetResource() as JsonResource);
  }

  private cb func OnNamesReady(token: ref<ResourceToken>) {
    this.RegisterParams(token.GetResource() as JsonResource);
  }

  // betiğin verdiği parametreler oyunun ad tablosunda yok: ad -> Wwise kimliği (FNV-1, küçük harf) eklenir (yoksa oyun iletmez)
  private func RegisterParams(resource: ref<JsonResource>) -> Void {
    if !IsDefined(resource) {
      return;
    }
    let root = resource.root as audioAudioEventArray;
    if !IsDefined(root) {
      return;
    }
    this.AddParam(root, n"xamw_rpm", 2034183246u);
    this.AddParam(root, n"xamw_gas", 2082397506u);
    this.AddParam(root, n"xcm_vol", 2442497969u);
  }

  private func AddParam(root: ref<audioAudioEventArray>, name: CName, id: Uint32) -> Void {
    let i = ArraySize(root.gameParameter) - 1;
    while i >= 0 {
      if Equals(root.gameParameter[i].redId, name) {
        return;
      }
      i -= 1;
    }
    let row: audioAudioEventMetadataArrayElement;
    row.redId = name;
    row.wwiseId = id;
    ArrayPush(root.gameParameter, row);
    root.isSortedByRedHash = false;
  }

  private func RegisterEvents() -> Void {
    if this.eventsRegistered || !IsDefined(AudioXLSystem.Get()) {
      return;
    }
    AudioXLAPI.RegisterEvent(n"xamw_engine_on");
    AudioXLAPI.RegisterEvent(n"xamw_engine_off");
    this.eventsRegistered = true;
  }

  private cb func OnSessionReady(event: ref<GameSessionEvent>) {
    this.RegisterEvents();
    if !this.bankLoaded {
      let loaded = AudioXLNative.LoadBank("red4ext/plugins/AudioXL/sounds/XairesAMV_Wwise/xaires_amv.bnk");
      this.bankLoaded = loaded == 1 || loaded == 69;
    }
  }
}

// Wwise parametreleri (global; yalnız oyuncu aracı bu bankayı kullanır)
public static func XairesAMV_WwiseSend(r: Float, t: Float) -> Void {
  let audio = GameInstance.GetAudioSystem(GetGameInstance());
  if IsDefined(audio) {
    audio.GlobalParameter(n"xamw_rpm", r / 1000.0);
    audio.GlobalParameter(n"xamw_gas", ClampF(t, 0.0, 1.0));
    audio.GlobalParameter(n"xcm_vol", XairesAMV_Vol() * 100.0 - 100.0);
  }
}
