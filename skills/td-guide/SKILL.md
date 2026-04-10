---
name: td-guide
description: Guidance for AI agents using td-mcp to work inside TouchDesigner — forces parameter-name verification, warns about cook-scope landmines, points to the right tool for each task. Use when any td_* tool is about to be called or when editing a TouchDesigner network.
---

# td-guide

You are about to modify a TouchDesigner network via the `td-mcp` tool surface. Read this before you mutate anything.

## Rule 1 — Your prior knowledge of TouchDesigner parameter names is unreliable

Assume your memory of TD parameter names is **completely unreliable**. TD parameters frequently differ from their visible label, and common-sense guesses are usually wrong:

- A Sphere SOP's radius is `radx` / `rady` / `radz`, not `radius`.
- A Noise TOP's period parameter is `period`, but the amplitude is `amp`, not `amplitude`.
- Translate is `tx` / `ty` / `tz`; rotate is `rx` / `ry` / `rz`; scale is `sx` / `sy` / `sz`.

**Before setting any parameter on an operator you just created or have not inspected, call `get_td_node_parameters` (or inside an `execute_python_script` call, `tdapi.GetParameterList(op_type)`).** Read the actual parameter names back from TD, then update. Do not skip this step to save a tool call — it's cheaper than a silent no-op bug the user has to debug.

## Rule 2 — See the network, don't guess at it

`td-mcp` gives you tools to *see* the network state before and after a change. Use them.

| Question | Tool |
|---|---|
| Where is the user currently looking? | `td_pane` |
| What is selected right now? | `td_selection` |
| What does this TOP's output actually look like? | `td_viewport(target=<top path>)` |
| What does the current network editor pane look like? | `td_viewport(target='pane')` |
| What children does this op have? | `get_td_nodes(parent=<path>)` |
| What parameters does this node currently hold? | `get_td_node_parameters` |
| Are there errors on this op or its children? | `get_td_node_errors` |

Every mutation that isn't a trivial parameter tweak should be followed by a `td_viewport` or `get_td_node_errors` check so you can confirm what happened instead of asserting it.

## Rule 3 — Nested baseCOMP cooking is a landmine

Operators inside a nested `baseCOMP` do not always cook automatically when referenced indirectly. The cached buffer goes stale. This is a known TouchDesigner gotcha.

**If you edit an op inside a base/tox COMP and the result seems wrong, call `td_cook` on the parent COMP before debugging anything else:**

```
td_cook({path: '/project1/base1', recurse: true})
```

This is the brute-force hammer. Use it whenever things look stale. The `--auto-cook-nested` server flag tries to fire this automatically after every mutation inside a base COMP, but it's not a substitute for manual calls when you're debugging.

## Rule 4 — GLSL shaders live in docked DATs

When you create a `glslTOP` (or `glslMAT`, `glslPOP`), TD auto-creates `_pixel_shader` and `_vertex_shader` DATs docked to the parent. They are separate operators; the parent only holds references to them.

**To read or write shader code, use `td_glsl` — never set `text` on a DAT you guessed at, and never `MoveOp` the parent with raw `nodeX`/`nodeY` assignments (that orphans the docked DATs).** The `td_glsl` tool resolves the docked DAT path for the requested stage and writes to it correctly; `op.TDAPI.MoveOp` (inside Python) handles the move case.

```
td_glsl({path: '/project1/glsl1', stage: 'pixel'})
# → returns { stage, docked_dat_path, code, errors }

td_glsl({path: '/project1/glsl1', stage: 'pixel', code: '#version 330 ...', returnCompiled: true})
# → writes + recooks + returns any compile errors
```

## Rule 5 — Prefer `td_scaffold` over writing networks by hand

If you want a render pipeline, a feedback loop, instanced particles, an audio-reactive rig, or a projection mapping starting point, **use `td_scaffold`** instead of creating nodes one at a time and wiring them yourself. The templates handle connector compatibility, naming, layout, and the first force-cook for you.

```
td_scaffold({template: 'render_pipeline', base: '/project1', name: 'scene'})
td_scaffold({template: 'feedback_loop', base: '/project1'})
td_scaffold({template: 'instanced_particles'})
td_scaffold({template: 'audio_reactive'})
td_scaffold({template: 'projection_mapping'})
```

## Rule 6 — Use `op.TDAPI` inside Python, not raw `op.create`

When you *do* need to drop into `execute_python_script`, prefer the `tdapi` helper library over raw TD calls:

```python
import tdapi

# Docked-DAT aware creation:
box = tdapi.CreateOp(op("/project1"), boxSOP, "box1", x=100, y=200)

# Layout-aware placement:
x, y = tdapi.FindEmptyArea(op("/project1"), 200, 200)
null = tdapi.CreateOp(op("/project1"), nullSOP, "null1", x, y)

# Parameter introspection (use before setting anything):
params = tdapi.GetParameterList("boxSOP")
help = tdapi.GetParameterHelp("boxSOP", "sizex")

# Recursive force-cook for nested baseCOMPs:
tdapi.ForceCook("/project1/base1", recurse=True)
```

`tdapi` is always imported at server startup — you can just `import tdapi` and go.

## Rule 7 — Frame-boundary error cache

TouchDesigner updates its error cache **only on frame boundaries**. A sequence of "mutate the op, then immediately check errors" in a single `execute_python_script` call may return stale data.

**Safe pattern:** mutate in one `execute_python_script` call, check errors in a separate subsequent call (or use the separate `get_td_node_errors` tool, which runs in its own request).

## Reference material

For deeper dives on specific topics:

- [`reference/basics.md`](reference/basics.md) — operator families, network editor concepts
- [`reference/operator-families.md`](reference/operator-families.md) — SOP / POP / TOP / CHOP / DAT / MAT / COMP
- [`reference/geometry-comp.md`](reference/geometry-comp.md) — Geometry COMP scaffolding
- [`reference/rendering.md`](reference/rendering.md) — camera + render TOP + out pipeline
- [`reference/glsl.md`](reference/glsl.md) — GLSL TOP/MAT/POP + docked-DAT handling
- [`reference/operator-tips.md`](reference/operator-tips.md) — parameter name gotchas, fuzzy matching
- [`reference/cooking-nested-comps.md`](reference/cooking-nested-comps.md) — the nested baseCOMP bug + `td_cook` workaround
- [`reference/scaffolds.md`](reference/scaffolds.md) — catalog of `td_scaffold` templates

## Attribution

Core patterns ported from [satoruhiga/claude-touchdesigner](https://github.com/satoruhiga/claude-touchdesigner/blob/main/touchdesigner/skills/td-guide/SKILL.md) (MIT). The "your prior knowledge is unreliable" framing is theirs; the fork extends it with the nested-COMP and scaffolding rules specific to td-mcp.
