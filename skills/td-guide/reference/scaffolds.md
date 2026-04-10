# `td_scaffold` template catalog

The `td_scaffold` MCP tool creates complete working scenes in one call. Each template is a vetted network that cooks on creation — no missing connections, no wrong parameter names, no wasted tool calls iterating on wiring.

Use `td_scaffold` whenever the user asks for something that fits one of these templates. It's always faster and more reliable than building the same thing op-by-op.

## Templates

### `render_pipeline`

The canonical 3D render pipeline: camera + geometry + light + render TOP + out TOP.

```
td_scaffold({template: 'render_pipeline', base: '/project1', name: 'scene'})
```

Creates:
- `scene_cam` — `cameraCOMP`
- `scene_geo` — `geometryCOMP` with default torus
- `scene_light` — `lightCOMP`
- `scene_render` — `renderTOP` wired to cam / geo / light
- `scene_out` — `outTOP` wired to render

Use when: the user wants to render 3D content, start a new scene, or get a clean baseline to iterate from.

---

### `feedback_loop`

Classic feedback effect: noise → composite → feedback TOP → null, with the null looped back into the feedback source.

```
td_scaffold({template: 'feedback_loop', base: '/project1'})
```

Creates:
- `feedback_loop_noise` — `noiseTOP` (initial input)
- `feedback_loop_fb` — `feedbackTOP`
- `feedback_loop_comp` — `compositeTOP` combining noise + feedback
- `feedback_loop_out` — `nullTOP` that's both the output and the feedback source

Use when: the user wants visual trails, decay effects, or iterative visual processes.

---

### `instanced_particles`

Grid SOP driving a Geo COMP with instancing enabled, rendered through a camera + render TOP.

```
td_scaffold({template: 'instanced_particles', base: '/project1'})
```

Creates:
- `instanced_particles_grid` — `gridSOP` supplying instance positions
- `instanced_particles_geo` — `geometryCOMP` with `par.instanceop = <grid path>`
- `instanced_particles_cam` — `cameraCOMP`
- `instanced_particles_render` — `renderTOP`
- `instanced_particles_out` — `outTOP`

Use when: the user wants to render thousands of instances of simple geometry, point clouds, particle effects.

---

### `audio_reactive`

Audio Device In → Analyze CHOP → Null CHOP pipeline. The null CHOP becomes the reference point for any TOP parameter that wants to react to audio.

```
td_scaffold({template: 'audio_reactive', base: '/project1'})
```

Creates:
- `audio_reactive_audio` — `audiodeviceinCHOP`
- `audio_reactive_analyze` — `analyzeCHOP`
- `audio_reactive_out` — `nullCHOP`

Use when: the user wants to drive visuals from microphone / line-in / audio file. Reference the null's channels from any TOP parameter (e.g. `par.amp.expr = "op('audio_reactive_out')['chan1']"`) to make parameters react.

---

### `projection_mapping`

Minimal starting point for projection mapping workflows: constant TOP → transform TOP → out TOP.

```
td_scaffold({template: 'projection_mapping', base: '/project1'})
```

Creates:
- `projection_mapping_content` — `constantTOP` (replace with your real content source)
- `projection_mapping_xform` — `transformTOP` (drive from a mapping UI)
- `projection_mapping_out` — `outTOP`

Use when: the user asks about projection mapping, keystone correction, or mapping content onto a physical surface. This template is intentionally minimal — the expectation is that you'll swap the `constantTOP` for real content and drive the `transformTOP` from a mapping UI or a kantan mapper COMP.

---

## Idempotency

Running `td_scaffold` twice with the same `base` and `name` produces two independent sets of ops (TD auto-increments colliding names: `scene_cam`, `scene_cam1`, etc.). It never overwrites existing work.

## After scaffolding

Every template cooks on creation via an implicit `tdapi.ForceCook(base, recurse=True)`. You can confirm with `td_viewport({target: entryPoint})` where `entryPoint` is the `entryPoint` field returned by the scaffold call.
