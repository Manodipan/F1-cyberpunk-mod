# Car modlist — 2.5, updated 22 Oct 2026 or later

Snapshot 2026-11-23, Nexus `Vehicles` category sorted by **Last Updated**. On Nexus those listings
show two dates: the relative one is *last updated*, the absolute one is *uploaded*. Everything below
is in the window on the **last-updated** date, which is the one that matters for "does it survive 2.5".

Why 22 Oct is the right cutoff: ADE 0.0.0.21's changelog reads "Fixed compatibility with 2.50", and
0.0.0.22 is dated 30 Oct 2026 — so 2.5 shipped in late October. A mod touched after that has been
looked at by its author under 2.5. Older-but-updated counts too: a 2025 car re-uploaded in November
is *more* current than a 2026 car that was never revisited.

## Track and race cars — the ones with downforce

| car | author | updated | upload | end. / DL | note |
|---|---|---|---|---|---|
| **Ferrari 599 XX EVO** | wzaa0921 | 18 Nov | 16 Nov 2026 | 9 / 1.6 k | **track-only Ferrari**, no road-car compromise — closest thing here to an LMH |
| **Porsche 992 GT3 R** | xa1res | 04 Nov | — | — | GT3 racer, race ratios, ~285 km/h so it never touches the wall |
| **Mitsubishi Lancer Evo X Final Edition** | Pryme7 | 21 Nov | 21 Nov 2026 | 14 / 1.2 k | live gauges, centre screen, **windscreen HUD**, neons follow CrystalCoat |

## ⚠ Do not install the Jesko Attack — it is this project's reference car

`reference/vehicles/jesko_attack.yaml` (995 lines) is the file the Phoenix build was ported from, and
`docs/STABILITY.md` measured what that chassis actually does:

| car | ADE wobble | manual hold |
|---|---|---|
| stock Aston mod (xaires) | **80 m/s** | **85 m/s** |
| **the Jesko** | **63 m/s** | **77 m/s** |

It is **the worst of the three** — 8 m/s below the stock Aston on the same road, same driver, same
session — and the project reverted out of it rather than keep tuning it. Eight builds got it to 72 at
best. Installing it means buying a car whose stability ceiling is the number this repo spent weeks
trying to escape.

Same author, same pipeline: **Ferrari 296 Speciale** (bob1479512). If you install it, open its YAML and
search for `useAlternativeTurnUpdate` and `turnUpdateMaxSpeedTurnChangeMul` — that family is
**Jesko-only** and is what `STABILITY.md` identified as the weave source. If they are there, expect the
same behaviour.

## Hypercars

| car | author | updated | upload | end. / DL | note |
|---|---|---|---|---|---|
| **Ferrari LaFerrari** | wzaa0921 | 19 Nov | 11 Nov 2026 | 9 / 1.2 k | V12 hybrid, the classic |
| **Pagani Zonda Revolucion** | wzaa0921 | 12 Nov | 12 Nov 2026 | — | the loudest car in the game, by reputation |
| **Lamborghini Sesto Elemento** | xa1res | 04 Nov | — | — | 999 kg, AWD, the lightest hypercar here |
| **Lamborghini Fenomeno** | STNGXRR | 22 Nov | 22 Nov 2026 | 34 / 2.3 k | newest Lambo, decent traction already |
| **Lamborghini Countach LPI 800-4 Liberty Walk** | xa1res | 04 Nov | — | — | 140+ colours, bodykit |
| **Ferrari 296 Speciale** | bob1479512 | 23 Nov | 20 Nov 2026 | 21 / 1.7 k | newest Ferrari here; also "vibe-coded" |

## Supercars and sports

| car | author | updated | upload | end. / DL | note |
|---|---|---|---|---|---|
| **Lamborghini Huracán EVO** | MAXSA5 | 10 Nov | 10 Nov 2026 | 42 / 6.1 k | five bodies, police and weaponised variants |
| **Maserati MC20** | soliqt | 25 Nov | 25 Nov 2026 | **0 / 13** | brand new — effectively untested by anyone |
| **Toyota GR GT** | Morpheus9436 | 15 Nov | 15 Nov 2026 | 63 / 7 k | Virtual Car Dealer + CrystalCoat |
| **Mercedes-Benz SL 65 AMG Black Series** | wzaa0921 | 20 Nov | 20 Nov 2026 | 5 / 967 | 6.0 V12, the widest car here |
| **BMW M5 E60** | BATOUFL | 15 Nov | 15 Nov 2026 | 25 / 1.9 k | V10, opening bonnet for the engine bay, optional real S85 audio |
| **Renault Clio V6** | BATOUFL | 09 Nov | 09 Nov 2026 | 23 / 1.8 k | mid-engine hatch, 6-speed, working **analog gauges in km/h** |

## JDM, muscle, everything else

| car | author | updated | upload | end. / DL | note |
|---|---|---|---|---|---|
| **Dodge Challenger SRT Hellcat Widebody** | Kingospawno | 25 Nov | 25 Nov 2026 | 0 / 113 | 717 hp RWD, working analog cluster, full engine bay |
| **Ford Hoonitruck** | Jacksonum913 | 22 Nov | 22 Nov 2026 | 6 / 469 | 900 hp drift truck, deliberately absurd |
| **Mercedes-Benz S-Class W223 Brabus 850** | Kingospawno | 15 Nov | — | — | 850 PS AWD limousine |
| **Pininfarina Battista Anniversario** | Kingospawno | Nov | — | — | 1 900 PS EV, author claims ~350 km/h |
| **Ferrari F40 (Garage)** | SDH0 | 16 Nov | Feb 2025 | 624 / 147 k | the proven one: 147 k downloads, Garage + Live Tuning |
| **Nissan Skyline R33 / R32** | yellingintothevoid | Nov | — | 507 / 314 k | 80+ tuning parts, 16 appearances |

## Filters, honestly applied

- **"Vibe-coded"** is the author's own label on the Jesko Attack and the 296 Speciale — AI-assisted
  build tooling, human direction and in-game testing. They are the two newest and the ones that
  address high-speed behaviour directly. Flagged, not disqualified.
- **Zero-endorsement cars** (MC20, Hellcat, Hoonitruck) are days old. They are the riskiest
  installs on the list and the most likely to have a broken record.
- **The 360 km/h wall still applies** (`MODS-LIST.md` §1). LaFerrari, Jesko, Zonda and Sesto all top
  out identically in game. The ones that feel different are the ones with ratios below the wall —
  599 XX, GT3 R, Evo X — because they use their whole range instead of parking on it.
- Add-on cars need **ArchiveXL + TweakXL** (and **Virtual Car Dealer** to buy them). Those four
  have been 2.5-ready since release; it is the car archive that needs to be current.

## What I would install, in order

1. **Ferrari 599 XX EVO** — a real track car, ~1.6 k downloads, updated 18 Nov. This is the one whose
   behaviour at 300 km/h will feel like the Valkyrie was supposed to.
2. **Porsche 992 GT3 R** — the same idea with a roof and a wing, from an author (xa1res) whose files
   this repo already ports from. Lowest risk on the list.
3. **Pagani Zonda Revolucion** — `STABILITY.md` used a Pagani as its **stable control** when ranking
   the Jesko and the Aston. If you want a hypercar that does not weave, that is the only chassis in
   this repo with evidence behind it.
4. **Mitsubishi Lancer Evo X** — not fast, but it has a windscreen HUD and live gauges, which is the
   same problem this repo solved for one car.
5. **Ferrari F40 (Garage)** — 147 k downloads and two years of updates. If one car on this page is
   guaranteed to load and behave, it is this one.

---

# Batch 2 — every row has a link

Second pass, same filter (last updated **≥ 22 Oct 2026**), read from the live listing pages. Links are
the canonical Nexus URLs.

## Motorsport — the standout group

All by **xa1res**, the author this repo ports the Aston from, all updated 04–05 Nov 2026. Real race
cars, so the gearing sits *below* the 360 wall and the cars use their range instead of parking on it.

| car | author | updated | end. / DL | link |
|---|---|---|---|---|
| **Ferrari 296 GT3** | xa1res | 04 Nov | 20 / 3.4 k | https://www.nexusmods.com/cyberpunk2077/mods/37227 |
| **Porsche 992 GT3 R** | xa1res | 04 Nov | 31 / 6.2 k | https://www.nexusmods.com/cyberpunk2077/mods/37229 |
| **Porsche Mission R** | xa1res | 04 Nov | 9 / 1.5 k | https://www.nexusmods.com/cyberpunk2077/mods/37224 |
| **Bugatti Bolide** | xa1res | 04 Nov | 40 / 7.7 k | https://www.nexusmods.com/cyberpunk2077/mods/37232 |
| **Apollo Intensa Emozione** | xa1res | 04 Nov | 30 / 12.2 k | https://www.nexusmods.com/cyberpunk2077/mods/37233 |
| **Lamborghini Sesto Elemento** | xa1res | 05 Nov | 32 / 17.4 k | https://www.nexusmods.com/cyberpunk2077/mods/37349 |

## Hypercars and GTs

| car | author | updated | end. / DL | link |
|---|---|---|---|---|
| **Ferrari 599 XX EVO** | wzaa0921 | 18 Nov | 9 / 1.6 k | https://www.nexusmods.com/cyberpunk2077/mods/38661 |
| **Pagani Zonda Revolucion** | wzaa0921 | 12 Nov | 4 / 1.8 k | https://www.nexusmods.com/cyberpunk2077/mods/38215 |
| **Ferrari LaFerrari** | wzaa0921 | 19 Nov | 9 / 1.2 k | https://www.nexusmods.com/cyberpunk2077/mods/38174 |
| **Ferrari 365 GTB/4 Competizione** | wzaa0921 | 23 Oct | 8 / 1.6 k | https://www.nexusmods.com/cyberpunk2077/mods/35665 |
| **Mercedes-Benz SL 65 AMG Black Series** | wzaa0921 | 20 Nov | 5 / 967 | https://www.nexusmods.com/cyberpunk2077/mods/39091 |
| **Pininfarina Battista Anniversario** | Kingospawno | 13 Nov | 7 / 1.1 k | https://www.nexusmods.com/cyberpunk2077/mods/38317 |
| **Mercedes-Benz SLS AMG Black Series** | 9Mimon9 | 09 Nov | 33 / 3.5 k | https://www.nexusmods.com/cyberpunk2077/mods/37906 |
| **Lamborghini Fenomeno (Customizable)** | 9Mimon9 | 10 Nov | 39 / 3.8 k | https://www.nexusmods.com/cyberpunk2077/mods/38017 |
| **Lamborghini Countach Liberty Walk** | xa1res | 04 Nov | 22 / 3.3 k | https://www.nexusmods.com/cyberpunk2077/mods/37235 |
| **Lamborghini Countach LPI 800-4** | xa1res | 04 Nov | 13 / 2.7 k | https://www.nexusmods.com/cyberpunk2077/mods/37234 |

## Sports, GT and proven classics

| car | author | updated | end. / DL | link |
|---|---|---|---|---|
| **Ferrari F40 (Garage)** | SDH0 | 16 Nov | 625 / 147 k | https://www.nexusmods.com/cyberpunk2077/mods/19954 |
| **Ferrari F40 ZEPHYR Custom** | SDH0 | 16 Nov | 451 / 76 k | https://www.nexusmods.com/cyberpunk2077/mods/20786 |
| **Nissan GT-R 'Lone Wanderer'** | ctxrlsec | 16 Nov | **1.3 k / 337 k** | https://www.nexusmods.com/cyberpunk2077/mods/20237 |
| **Nissan Skyline R32** | yellingintothevoid | 16 Nov | 466 / 189 k | https://www.nexusmods.com/cyberpunk2077/mods/23136 |
| **Nissan GT-R50** | MAXSA5 | 15 Nov | 44 / 5.2 k | https://www.nexusmods.com/cyberpunk2077/mods/38219 |
| **Mercedes-AMG GT 63 Coupé** | Carryhan | 14 Nov | 20 / 2.8 k | https://www.nexusmods.com/cyberpunk2077/mods/38452 |
| **Audi RS7 Sportback** | Kingospawno | 11 Nov | 600 PS quattro | https://www.nexusmods.com/cyberpunk2077/mods/38130 |
| **BMW M5 E60 (V10)** | BATOUFL | 16 Nov | 27 / 2 k | https://www.nexusmods.com/cyberpunk2077/mods/38650 |
| **Renault Clio V6** | BATOUFL | 10 Nov | 23 / 1.8 k | https://www.nexusmods.com/cyberpunk2077/mods/37941 |
| **Toyota GR GT** | Morpheus9436 | 15 Nov | 65 / 7.1 k | https://www.nexusmods.com/cyberpunk2077/mods/38591 |
| **Shion Fastbird** | lachdotco | 16 Nov | 46 / 5.2 k | https://www.nexusmods.com/cyberpunk2077/mods/26531 |
| **Quadra Turbo-R V-TECH Afterburn** | CliffJL | 14 Nov | 12 / 536 | https://www.nexusmods.com/cyberpunk2077/mods/38394 |

## Days old — unproven

| car | author | updated | end. / DL | link |
|---|---|---|---|---|
| **Ferrari 296 Speciale** *(same author as the Jesko — check the YAML)* | bob1479512 | 23 Nov | 21 / 1.7 k | https://www.nexusmods.com/cyberpunk2077/mods/39109 |
| **Maserati MC20** | soliqt | 25 Nov | **0 / 13** | https://www.nexusmods.com/cyberpunk2077/mods/39635 |
| **Dodge Challenger SRT Hellcat Widebody** | Kingospawno | 25 Nov | **0 / 113** | https://www.nexusmods.com/cyberpunk2077/mods/39622 |
| **Lamborghini Fenomeno** | STNGXRR | 22 Nov | 34 / 2.3 k | https://www.nexusmods.com/cyberpunk2077/mods/38809 |
| **Mitsubishi Lancer Evo X Final Edition** | Pryme7 | 21 Nov | 14 / 1.2 k | https://www.nexusmods.com/cyberpunk2077/mods/39153 |
| **Ford Hoonitruck** | Jacksonum913 | 22 Nov | 6 / 469 | https://www.nexusmods.com/cyberpunk2077/mods/39281 |

## What batch 2 changes

The first list leaned on hypercars, which the wall makes identical. This one leans on **motorsport**:
296 GT3, 992 GT3 R, Mission R, Bolide, Apollo IE. They are the only cars in either list whose gearing
is designed for a circuit rather than a top-speed number, and all six come from one author whose
files this repo has already read. If the goal is "a car that behaves at 300 km/h", that is the set.
