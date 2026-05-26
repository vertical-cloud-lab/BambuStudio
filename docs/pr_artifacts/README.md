# PR artifacts: G-code visualizations for vertical-cloud-lab/BambuStudio PR `copilot/fix-slicing-issue-cli-h2d`

These PNGs and the accompanying `render_gcode.py` script demonstrate the patched
CLI successfully slicing the failing H2D PLA+TPU 3MFs from
`vertical-cloud-lab/tensegrity-optimization` PR #35.

Rendered with the BambuStudio CLI built by
`.github/workflows/copilot_build_artifact.yml` (run `26338104126`,
sha `b437953`) on Ubuntu 22.04.

## Files

- `single_specimen.xy.png` / `single_specimen.iso.png` — single specimen
  (input: `t3-prism.H2D-MM-PLAstruts-TPUcables.single.3mf`, ~46 MB G-code,
  17,666 PLA segments + 16,018 TPU segments).
- `batch.xy.png` / `batch.iso.png` — batch (input:
  `t3-prism.H2D-MM-PLAstruts-TPUcables.batch.3mf`, ~59 MB G-code, 14,491 PLA
  segments + 20,906 TPU segments).
- `render_gcode.py` — standalone matplotlib parser/renderer used to produce
  the PNGs from `Metadata/plate_1.gcode`. Colors each extrusion segment by the
  active extruder (`M1020 S0` → T0/PLA green `#00AE42`, `M1020 S1` → T1/TPU
  light blue `#76D9F4`). Run as:
  ```
  python3 render_gcode.py path/to/plate_1.gcode out_prefix
  ```

## How the slices were obtained

Tweaks vs. the raw 3MFs from PR #35 needed because of pre-existing H2D Pro vs.
H2D differences in the bundled profiles (unrelated to the OOB fix in this PR):

1. Per-extruder `nozzle_volume_type` patched to `["Standard","TPU High Flow"]`
   (TPU needs the High-Flow nozzle variant on extruder 2).
2. `flush_volumes_matrix` / `flush_volumes_vector` resized from the 4-filament
   (16/8) source to 2-filament (4/4).
3. Machine override: `--load-settings "Bambu Lab H2D Pro 0.4 nozzle.json"`
   (the 3MFs were authored against the H2D Pro variant — see
   `upward_compatible_machine` in their `result.json`).
4. Batch only: `--no-check` to bypass an unrelated wipe-tower / specimen
   gcode-path conflict.

The OOB fix in this PR was exercised cleanly: the validator no longer crashes
or logs the bogus `extruder 21842` and runs to completion for the happy path,
and now emits the new clean `CLI_INVALID_PARAMS` error when invoked with a
mismatched `--filament-map` size (e.g. `--load-filaments` with 2 filaments and
`--filament-map "1"`).
