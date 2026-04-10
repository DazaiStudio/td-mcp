# GLSL authoring in TouchDesigner

TouchDesigner supports GLSL shaders in three places:

- **`glslTOP`** — fragment shader producing a 2D texture. Inputs are other TOPs sampled as `sTD2DInputs[i]`.
- **`glslMAT`** — a material applied to geometry in a render pipeline. Vertex and pixel stages.
- **`glslPOP`** — a compute-style operator for point-cloud processing.

## The docked-DAT gotcha

When you create any GLSL op, TD auto-creates *docked* DATs for the shader source:

- A `glslTOP` gets a docked DAT (by default named `glsl1_pixel` or similar) referenced by `par.pixelshader`.
- A `glslMAT` gets two docked DATs referenced by `par.vertexsrc` and `par.pixelsrc`.
- A `glslPOP` gets a docked compute shader DAT.

These docked DATs are **separate operators** in the network; the GLSL op just holds a reference. That means:

- Setting `glsl1.par.pixelshader = some_text` won't work — the parameter is a DAT *reference*, not a text field.
- Calling `MoveOp(glsl1, 100, 100)` via raw `nodeX`/`nodeY` assignment leaves the docked DAT behind. Use `tdapi.MoveOp` which re-parents docked ops.
- If you delete and recreate the docked DAT manually, the link to the parent breaks — don't do that.

## Using `td_glsl`

`td_glsl` is the right way to read or write shader source. It resolves the docked DAT for the requested stage automatically.

```
# Read the current pixel shader:
td_glsl({path: '/project1/glsl1', stage: 'pixel'})
# → { stage: 'pixel', docked_dat_path: '/project1/glsl1_pixel', code: '...', errors: null }

# Write new code and re-cook:
td_glsl({
  path: '/project1/glsl1',
  stage: 'pixel',
  code: '#version 330\nout vec4 fragColor;\nvoid main() { fragColor = vec4(1.0); }',
  returnCompiled: true,
})
# → { ..., errors: null (or [{line, msg}, ...]) }
```

Stages: `'pixel'` (fragment), `'vertex'`, or `'compute'`.

## Minimum viable fragment shader

```glsl
#version 330

out vec4 fragColor;

void main() {
    fragColor = vec4(1.0, 0.5, 0.25, 1.0);
}
```

## Reading input textures

```glsl
#version 330

uniform sampler2D sTD2DInputs[1];
in vec2 vUV;
out vec4 fragColor;

void main() {
    vec4 color = texture(sTD2DInputs[0], vUV.st);
    fragColor = color;
}
```

`sTD2DInputs` is a built-in uniform array — TD maps each connected input TOP to an index.

## Debugging compile errors

Pass `returnCompiled: true` to `td_glsl` when writing. TD's error string comes back in the `errors` array. If you get "link failed" errors with no details, check the DAT's `errors` via `get_td_node_errors({path: '/project1/glsl1_pixel'})`.

Remember [Rule 7 — Frame-boundary error cache](../SKILL.md#rule-7--frame-boundary-error-cache): the error check must happen in a *separate* call from the write, otherwise you'll read stale cached errors.
