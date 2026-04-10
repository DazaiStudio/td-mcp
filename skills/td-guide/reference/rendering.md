# Rendering pipeline

The canonical TouchDesigner render pipeline is five operators:

```
cameraCOMP ─┐
            │
geometryCOMP┼─── renderTOP ─── outTOP
            │
lightCOMP ──┘
```

## What each piece does

- **`cameraCOMP`** — The virtual camera. Position, rotation, FOV, clipping planes. Place it at e.g. `(0, 2, 5)` looking at origin to see a default-sized geometry.
- **`geometryCOMP`** — The thing being rendered. Needs at least one internal SOP wired to `out1` with `out1.render = True`. See [`geometry-comp.md`](geometry-comp.md).
- **`lightCOMP`** — One or more light sources. Type = `Directional`, `Point`, or `Cone`. A single directional light pointing at the geometry is enough for basics.
- **`renderTOP`** — The actual rendering. Wire it to the three COMPs via parameters (`par.camera`, `par.geometry`, `par.lights`). The output is a 2D texture you can further composite with other TOPs.
- **`outTOP`** — The sink TOP. Not strictly required, but gives you a clean named output for downstream consumption and makes the network easier to read.

## One-shot scaffold

```
td_scaffold({template: 'render_pipeline', base: '/project1', name: 'scene'})
```

This creates all five ops, wires the render TOP to the camera/geo/light COMPs, and connects the render → out. The returned `entryPoint` is the out TOP path — use that for any downstream composition.

## Manual construction

```python
import tdapi

base = op("/project1")
cam = tdapi.CreateOp(base, cameraCOMP, "cam1", 100, 200)
geo = tdapi.CreateOp(base, geometryCOMP, "geo1", 100, 0)
light = tdapi.CreateOp(base, lightCOMP, "light1", 100, -200)
render = tdapi.CreateOp(base, renderTOP, "render1", 400, 100)
out = tdapi.CreateOp(base, outTOP, "out1", 700, 100)

render.par.camera = cam.path
render.par.geometry = geo.path
render.par.lights = light.path
out.inputConnectors[0].connect(render)
```

## Common mistakes

- **Empty Geo COMP** — the render TOP runs but you see nothing. Confirm with `td_viewport({target: '/project1/geo1'})` — the Geo COMP viewer should show your geometry.
- **Light too far away** — if you're using point lights, make sure the light position is near the geometry; otherwise the scene will look black.
- **Camera inside the geometry** — default sphere SOP has radius 1, so a camera at `(0, 0, 0)` is inside it and clipped. Move the camera out.
- **Forgetting to wire `par.camera`** — the render TOP needs to know which camera to render from. There's no sensible default.
