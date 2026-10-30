# Kinara Town — DS-ready assets

Converted from the 8x-scale sheets in `D:\Rom hack project\Tiles` (exact 1/8 downscale, no pixels lost).
All PNGs are indexed: palette index 0 = transparent (#F800F8), at most 15 other colours, every colour DS-safe (multiples of 8).

| Folder / file | What it is |
| --- | --- |
| `ground/kinara_ground_sheet.png` | 128x128 ground sheet, 8x8 grid of 16x16 tiles, 15 colours |
| `ground/tile_RC.png` | each non-empty ground tile on its own (R = row, C = column on the sheet) |
| `water/water_frame_1-4.png` | 16x16 backwater animation, loops 4 -> 1 |
| `props/*.png` | one texture per prop, power-of-two size, art bottom-centred; `manifest.json` lists sizes and colour counts |
| `kinara_mockup_1x.png` | the full town at true size (512x512 = 32x32 tiles), reference for building the map |
| `kinara_layout_grid.png` | the mockup at 2x with a numbered 32x32 grid (x across, y down) |
| `kinara_collision_draft.png` / `.json` | first-pass collision: blocked, water (Surf), tall grass, jetty; untinted = walkable |

Notes
- Banyan shrine was 19 colours; the 4 closest shades were merged to fit 15.
- The building sheet is concept art for 3D modelling, not a texture, so it is not converted.
- Collision is a draft generated from the mockup; check doors and the paddy fields (left walkable).
