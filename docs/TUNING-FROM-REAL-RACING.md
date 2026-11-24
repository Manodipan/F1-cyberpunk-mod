# Tuning from real racing: what the Valkyrie LMH actually is, and what of it we can encode

Researched 2026-11-24, after the shift-hole fix made the car pass 350 km/h. This page exists
to stop us tuning by guesswork: every number below is either **real engineering data** (with a
source), **measured in this install**, or **derived arithmetic** that anyone can re-check.

---

## 1. The real car, and the real class

| | Valkyrie LMH (race) | Valkyrie (road) |
|---|---|---|
| Engine | 6.5 L **naturally aspirated** V12 (Cosworth) | same |
| Power | 520 kW / **697 hp** (BoP) | 1,000 hp @ 10,500 rpm, 1,160 hp hybrid |
| Torque | ~900 Nm class figure | **740 Nm @ 7,000 rpm** |
| Redline | endurance-trimmed | **11,100 rpm** |
| Gearbox | **7-speed Xtrac sequential** | 7-speed single-clutch automated manual |
| Drive | **rear-wheel drive**, mechanical diff | RWD |
| Weight | ~1,030 kg | 1,030 kg dry |
| Top speed | 340 km/h (BoP-limited) | 400+ km/h |

Two facts that matter for us:

1. **It is naturally aspirated.** Its torque curve does not fall off a cliff at the top — NA
   engines hold torque to the redline. That is exactly what a top-speed run needs.
2. **Peak power is at 95 % of redline** (10,500 of 11,100). Peak torque at **63 %** (7,000).
   So the powerband is the top half of the range, and the correct shift point is high.

## 2. The torque curve is a *shape*, not an rpm range

Read from the format documentation in `jcoetzee/cp2077-ev-conversion` (`tools/curveset.py`,
which reproduces vanilla `.curveset` files byte for byte):

```
uint32 point_count
point_count × (float x, float y)      x = normalised RPM 0..1,  y = torque fraction
uint32 interpolation
```

**x runs 0→1, not 0→rpm.** So a curve is stretched over the engine record's
`[minRPM, maxRPM]`, and swapping curves never changes the rev range — only the shape. This
also retires an earlier theory of ours (see §6).

### The 15 vanilla curves

`large_balanced_na`, `large_balanced_sc`, `large_balanced_turbo`, `large_torquey_na`,
`med_balanced_na`, `med_balanced_sc`, `med_lowcomp_bigturbo`, `med_peaky_na`,
`med_torquey_na`, `med_torquey_turbo`, `small_balanced_na`, `small_block_v8_na`,
`small_peaky_na`, `small_torquey_na`, `small_torquey_turbo`.

Naming is `{size}_{character}_{induction}`, referenced as
`base\gameplay\vehicles\curves\engine_torque\<name>.curveset`.

| Field | For us |
|---|---|
| size | small / med / large — displacement |
| character | `balanced` = flat, `torquey` = low-end biased, `peaky` = narrow powerband, `lowcomp_bigturbo` = boost cliff |
| induction | `na` holds torque to redline; `sc`/`turbo` tail off at the top |

**Our car should be on `large_balanced_na`.** It is a big, naturally aspirated, flat-curve
engine: the closest vanilla analogue to a 6.5 L NA V12, and the shape that keeps making torque
at 0.9 of redline, which is where a 500 km/h run lives. Today we inherit the SuperSport's
curve — a turbo-shaped curve, i.e. the one profile the real car does *not* have.

## 3. Shift point: the game already does the right thing

The physics upshifts at ≈ **0.90 of a gear's maxEngineRPM**. Real data: power peak at
**0.946** of redline on the Valkyrie. So the game under-shifts by about 5 % — conservative,
never harmful, and within the range real race engineers use (they shift at peak-power rpm, or
slightly past it when the next gear is close).

Nothing to change. It also means the ladder must be built *around* 0.90 — which is what the
overlap rule in [`YAML-FIELDS.md`](YAML-FIELDS.md) now enforces.

## 4. Gear steps: ours are already race-correct

| Car | Speeds | Typical step |
|---|---|---|
| F1 (modern) | 8 | ~1.13 |
| LMH / LMP1 | 6–7 | ~1.22–1.28 |
| Road car | 6–8 | ~1.30–1.40 |
| **Phoenix** | **7** | **1.278** |

Our step is right for a 7-speed LMH. Do not "fix" it.

## 5. Aero: the arithmetic that says 500 km/h is honest

Power-limited top speed, from `P = ½ρ·C_dA·v³`:

```
v_max = (2P / (ρ · C_dA))^(1/3)
```

| Case | Numbers | Result |
|---|---|---|
| Real Valkyrie LMH | 697 hp, C_dA = 0.95 m² | **347 km/h** — against a BoP-limited 340 ✓ |
| Our target | 2,000 hp, C_dA = 0.95 | **493 km/h** |
| Our target, exactly | 2,000 hp, 500 km/h | needs **C_dA = 0.91 m²** |
| Power to *hold* 500 km/h | 11,200 N at 138.89 m/s | **1,559 kW = 2,091 hp** |

So the model is consistent with reality to within 2 %, and "2,000 hp for 500 km/h" is not a
fantasy number — it is the class ceiling, which is why it feels like the right target.

## 6. What this retires

The "the inherited torque curve ends at ~7,850 rpm and that is the wall" theory (TOPSPEED-TEST
§3g) **does not survive the format**: curve x is normalised, so a curve cannot impose an
absolute rpm ceiling — `maxRPM` stretches it. The two plateaus we measured (308, 352 km/h) are
fully explained by the shift-hole (§3j), and the rpm coincidence was a consequence of the shift
point, not of a curve ending.

What survives from that episode: the **shift point is 0.90 of a gear's range**, and gear
ladders must be built around it. That is now a test.

## 7. Build B — the tuning this research implies

To be applied once the shift-hole build is measured, so the two changes never share a test:

| Change | From | To | Why |
|---|---|---|---|
| `gearCurvesPath` | inherited (turbo-shaped) | **`large_balanced_na`** | the real car is a big NA V12; NA holds torque to 0.9 of redline, which is where 500 km/h lives |
| gear 7 `torqueMultiplier` | 0.50 (weakest gear in the box) | **0.62** | in a real box the top gear is chosen so that v_max happens at peak power; multiplying torque *down* in top gear is the opposite of how a race car is geared |
| gear 6 `torqueMultiplier` | 0.53 | 0.62 | keeps the box's force curve flat instead of tapering (close-ratio boxes are near-constant wheel force) |
| `maxRPM` | 7900 | **7900** (unchanged) | the shift happens at 7,020; nothing above that is ever visited |

Expected effect: more force in the two gears that actually matter for the run to 500, with no
change to launch feel or to the ladder geometry. If it overshoots 500, drag comes up
(`airResistanceFactor` 0.60 → 0.70) rather than gearing coming down.

## 8. If we ever want a curve of our own

The format is simple enough to author: keyframes of `(rpm%, torque%)`. What we cannot do from
this repo is *cook* a `.curveset` — that needs a CR2W writer plus a vanilla file as a template,
both of which live on the game machine (`cr2w_edit.py` in that repo does exactly this). A
custom V12 curve is therefore a real option, but it is a Windows-side project, not a YAML one,
and it is not needed while `large_balanced_na` exists.

---

### Sources

* Aston Martin media centre — Valkyrie powertrain: 1,000 bhp @ 10,500 rpm, 740 Nm @ 7,000 rpm,
  11,100 rpm maximum.
* Aston Martin Valkyrie LM (LMH) specification: 520 kW / 697 hp, 7-speed Xtrac, RWD, 1,030 kg,
  340 km/h.
* `jcoetzee/cp2077-ev-conversion` — `tools/curveset.py` (curve layout: normalised x, torque
  fraction y) and `tools/curvewriter.py` (byte-exact vanilla reproduction).
* `DoctorPresto/Cyberpunk-File-Types` — `curveset.txt`, the file list this catalogue came from.
* `reference/vehicles/jesko_attack.yaml` — the only working car in our corpus that names a
  curve (`large_balanced_turbo`), and it does 500+ km/h.
