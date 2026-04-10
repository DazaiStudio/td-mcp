# Geometry COMP

A `geometryCOMP` is the bridge between the SOP/POP world (geometry data) and the TOP world (rendered textures). It's a sub-network that holds SOP/POP operators internally and exposes a rendered surface via a render TOP.

## Minimum viable Geo COMP

A usable Geo COMP needs:

1. An input SOP (or POP) inside the COMP (use `inSOP`)
2. Something to render (could just be the input)
3. An output SOP that sets its `display` and `render` flags to `True` (use `outSOP`)
4. Wiring: `in1 → ... → out1`

`tdapi.CreateGeometryComp` scaffolds exactly this in one call:

```python
import tdapi

grid = tdapi.CreateOp(op("/project1"), gridSOP, "grid1", 100, 100)
geo, in_op, out_op = tdapi.CreateGeometryComp(
    op("/project1"), name="geo1", input_op=grid, x=300, y=100
)
# geo has grid connected, internal in→out wired, out displayed and rendered.
```

The helper:

- Creates the `geometryCOMP`
- Removes the default torus
- Creates `in1` and `out1` (as `inSOP`/`outSOP` or `inPOP`/`outPOP` depending on the family of `input_op`)
- Wires `out1.inputConnectors[0].connect(in1)`
- Sets `out1.display = True` and `out1.render = True`
- If `input_op` was passed, wires `geo.inputConnectors[0].connect(input_op)` on the outside

## Instancing

Geo COMPs support instancing: place many copies of the contained geometry using data from another operator. Set `geo.par.instanceop = <sop path>` — the Geo COMP will use the source SOP's points as instance positions.

See `td_scaffold({template: 'instanced_particles'})` for a ready-made instancing setup.

## Rendering a Geo COMP

Wire it into a `renderTOP`:

```python
geo = op("/project1/geo1")
cam = tdapi.CreateOp(op("/project1"), cameraCOMP, "cam1")
render = tdapi.CreateOp(op("/project1"), renderTOP, "render1")
render.par.geometry = geo.path
render.par.camera = cam.path
```

Or use `td_scaffold({template: 'render_pipeline'})` to get the whole thing at once.

## Common mistakes

- **Forgetting `out1.render = True`** — the geometry won't show up in the render TOP.
- **Forgetting `out1.display = True`** — you won't see it in the Geo COMP's viewer.
- **Wiring the external input without creating `in1` first** — TD will happily make an implicit `in1` for you but the internal network won't see the data.
- **Setting `geo.par.instanceop` to a COMP path instead of a SOP path** — instancing needs point data from a SOP.
