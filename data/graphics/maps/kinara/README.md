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

## In-game map (v1)

- `model/` — Kinara map source: `kinara.obj/.mtl` + textures (PDSMS conventions, 1 unit per tile, z up, ground at height 1),
  `kinara.imd` (map, via PDSMS `ImdModel`) and `texset_kinara.imd` (HGSS map texture set 2 + the Kinara textures).
- Ground is rebuilt from the DS-ready tileset, not the painted mockup: each cell is classed (grass, road, sand, dry earth,
  field, paddy, water, jetty; see `model/sem_grid.txt`), plain areas use 2x2 variant blocks of the tileset on merged quads,
  and road/shore edges are autotiled from the tileset's edge tiles into 64x64 atlases. Keep the map NSBMD small:
  vanilla HGSS maps stay under ~61 KB, and a 65 KB Kinara model corrupted the map geometry after re-entering the town.
- Props and buildings are camera-facing quads leaning back ~50° (HGSS tree calibration), cut from the mockup art.
- `g3dcvtr kinara.imd -emdl` -> `kinara.nsbmd`; `g3dcvtr texset_kinara.imd -etex` -> `texset_kinara.nsbtx`.
- `rawdata/maps/land_data/5_000` = New Bark's map slot (land_data 0): Kinara permissions + model + flat BDHC (height 16, from Route 29) + New Bark's BGS.
- `rawdata/maps/map_tex/4_002` = map texture set 2 (shared by all Johto outdoor maps) with the Kinara textures appended, so Route 29 next door still renders.
- Doors: player (11,11), Kabir (18,11), lab (25,11), neighbour (9,22), lab side door (27,11). Events moved in `data/eventdata/zone_event/057_T20.json`.
