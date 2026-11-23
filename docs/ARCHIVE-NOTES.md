# `phoenix_aston_valkyrie.archive` — provenance

| | |
|---|---|
| Source | `aston_valkyrie.archive` from `main` (Nexus "Aston Martin Valkyrie LMH 1.1", unpacked) |
| Size | 11,624,448 bytes — byte-identical copy, **contents unchanged** |
| Renamed | file name only (`aston_valkyrie` → `phoenix_aston_valkyrie`, same for `.archive.xl`) |
| Why unchanged | same model, livery, texture core (`amv_icon` / `amv_dealer` / `aston_valkyrie_logo` atlases), same `.ent`, same onscreens JSON — the Phoenix car is a second *registration* of the same assets |
| `.archive.xl` | copied verbatim; it declares the onscreens localisation files inside the archive |

```
localization:
  onscreens:
    en-us: xaires\aston_valkyrie\aston_valkyrie.json
    tr-tr: xaires\aston_valkyrie\aston_valkyrie_tr.json
```

Those paths must stay as-is: they point at files *inside* this archive. A distinct
Phoenix display name therefore needs the JSON edited and repacked — see
`LOCALISATION.md`.

No `red4ext/` here on purpose: the Phoenix scripts load the stock
`AudioXL/sounds/XairesAMV_Wwise/xaires_amv.bnk`. Two copies of one bank = duplicate
AudioXL load.
