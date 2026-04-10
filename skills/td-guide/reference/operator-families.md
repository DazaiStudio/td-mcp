# Operator families

TouchDesigner groups operators into seven families. Operators can only be **directly wired** to operators in the same family — crossing families requires a conversion step.

| Family | Full name | Contains | Examples |
|---|---|---|---|
| **SOP** | Surface Operators | 3D geometry (points, polygons, particles) | `boxSOP`, `gridSOP`, `noiseSOP`, `copySOP` |
| **POP** | Point Operators | GPU-accelerated point-cloud pipeline (newer) | `spherePOP`, `forcePOP`, `advectPOP` |
| **TOP** | Texture Operators | 2D image/video/render textures | `noiseTOP`, `moviefileinTOP`, `renderTOP`, `glslTOP` |
| **CHOP** | Channel Operators | Time-series data (audio, midi, animation) | `audiofileinCHOP`, `lfoCHOP`, `analyzeCHOP`, `nullCHOP` |
| **DAT** | Data Operators | Text, tables, scripts, network data | `tableDAT`, `executeDAT`, `textDAT`, `webDAT` |
| **MAT** | Material Operators | Shading materials for rendering | `phongMAT`, `pbrMAT`, `constantMAT`, `glslMAT` |
| **COMP** | Components | Containers, cameras, lights, UI panels | `baseCOMP`, `containerCOMP`, `cameraCOMP`, `lightCOMP`, `geometryCOMP` |

## Crossing families

You cross families by using a reference or an explicit conversion operator:

- **SOP → TOP** — use a render pipeline: `cameraCOMP` + `geometryCOMP` + `renderTOP`
- **CHOP → TOP** — `chopToTOP`
- **TOP → CHOP** — `topToCHOP`
- **CHOP → DAT** — `chopToDAT`
- **DAT → CHOP** — `datToCHOP`
- **Anything → parameter** — set `par.mode = ParMode.EXPORT` and export from a CHOP/DAT cell, or write a parameter expression

When wiring via the generic connector API (`inputConnectors[0].connect(...)`), a family mismatch will fail silently. Use `td_connect` — it validates families server-side before hitting TD and returns an actionable error.

## When to use each family

- **Geometry you can point-edit or generate procedurally** → SOP
- **Millions of points with GPU physics, forces, advection** → POP
- **Images, textures, video, render output, GPU compute** → TOP
- **Anything that varies over time, including audio, control values, animation** → CHOP
- **Script callbacks, parsed data, tables, UI state** → DAT
- **How a surface shades** → MAT
- **Containers, cameras, lights, panels, re-usable sub-networks** → COMP

## Naming convention

TD uses camelCase names suffixed with the family: `boxSOP`, `noiseTOP`, `audiofileinCHOP`. These are the values you pass to `create_td_node` or `tdapi.CreateOp`. Common abbreviations people guess wrong:

- "Noise" → `noiseSOP`, `noiseTOP`, or `noiseCHOP` depending on family
- "Null" → `nullSOP`, `nullTOP`, `nullCHOP`, `nullDAT` — pick the family
- "Constant" → `constantCHOP`, `constantTOP`, `constantMAT`, `constantDAT`
- "In"/"Out" — these are used inside Geometry COMPs as `inSOP` / `outSOP`, `inTOP` / `outTOP`, etc.

Use `describe_td_tools` with `filter="noise"` (or similar) to find operators by fuzzy match.
