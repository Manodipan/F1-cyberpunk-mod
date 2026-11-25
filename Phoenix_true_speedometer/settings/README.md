# Parked: the Mod Settings layer

`PhoenixTS_Settings.reds.pending` is the full v2 feature set - two unit slots, seven units
including Mach, custom multipliers, unit labels, tooltips.

It is **parked, not installed**: the extension is `.pending`, so redscript never sees it and
`tools/update.ps1` never copies it. The game must boot with the plain HUD build first.

## Why it is parked

v2 declared a `module`, a `public enum` and a `public class ... extends ScriptableSystem`, and the
game did not boot. `Phoenix_aston_valkyrie.reds` - which boots on the same install - declares none
of the three. Until the boot question is answered, none of them ships.

## How to bring it back, one piece at a time

1. Rename to `.reds`, install, restart. Still no boot? The `ScriptableSystem` is the culprit.
2. If it boots, open the Mod Settings tab. No tab? The `runtimeProperty` keys are wrong for 2.5.
3. Only then wire the HUD to read the settings instead of printing m/s | km/h.

Each step gets a restart. Do not combine them - the whole point is that exactly one variable moves
per test.
