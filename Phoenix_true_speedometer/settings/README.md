# Parked: the three-significant-digit formatter

`PhoenixTS_Settings.reds.pending` is the old v2 build. Only its formatter is still unshipped:

```redscript
PhoenixTS_SigDigits(value: Float) -> Int32    // 100 -> 0 places, 10 -> 1, 1 -> 2, 0.1 -> 3 ...
PhoenixTS_Format(value: Float, decimals: Int32) -> String
```

Nothing here is installed: the extension is `.pending`, so redscript never sees it and
`tools/update.ps1` never copies it.

## Why it is still parked

v3 shipped this formatter and the game refused the file. The settings layer has since been proven
separately (step B booted), so the formatter is the last unproven piece of code in the project.
When it goes back in, it goes in alone, with every statement on one line.

## What has already been taken from it

The ConfigVar reader. The old draft read settings out of Mod Settings' ConfigVars; that is now the
shipped mechanism for reading settings, because the framework writes a chosen value into the class
**default** (`ModSettings.cpp:133 SetDefaultValue`) rather than into a live instance.
