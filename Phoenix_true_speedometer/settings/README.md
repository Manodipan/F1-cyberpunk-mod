# Parked: the three-significant-digit formatter

`PhoenixTS_Settings.reds.pending` is the v2 build. The settings layer it contains has been ported
back into the shipped file as step B, **without** the formatter - that is what step C adds.

Nothing here is installed: the extension is `.pending`, so redscript never sees it and
`tools/update.ps1` never copies it (it copies `*.reds` from `r6/scripts/phoenix_true_speedometer/`
only).

## What is parked, exactly

```redscript
PhoenixTS_SigDigits(value: Float) -> Int32    // 100 -> 0 places, 10 -> 1, 1 -> 2, 0.1 -> 3 ...
PhoenixTS_Format(value: Float, decimals: Int32) -> String
```

The arithmetic is `IntToString(RoundMath(value * scale))` split into whole and fractional parts,
zero padded from a literal ladder. `RoundMath` returning `Int32`, and `let` locals being
reassignable, are both proven in the car mod and ADE - so the remaining risk is size, not style.

## How step C ships

1. Copy both functions in unchanged, every statement on one line.
2. Replace `IntToString(RoundMath(value))` in `PhoenixTS_Number` with
   `PhoenixTS_Format(value, PhoenixTS_SigDigits(value))`.
3. Restart. Expected: `58.8 m/s | 212 km/h`, `0.171 Mach`, `0.0171` for a slow crawl.
4. If that pops the compile window, the formatter is the cause and the fallback is to keep whole
   numbers and print the fractional digits by hand as two integer halves.
