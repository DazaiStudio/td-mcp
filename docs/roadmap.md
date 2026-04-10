# td-mcp Roadmap

> Living document describing the fork's vision, phased delivery plan, and detailed tool specs. This file is the single source of truth for "what is this fork adding, and why?". Implementation tickets in GitHub Issues link back here.

**Status:** Phases 1–3 complete. Phase 4 (publish) is tracked in [#10](https://github.com/DazaiStudio/td-mcp/issues/10). Last updated 2026-04-10.

---

## Vision

`td-mcp` turns Claude and other MCP-compatible agents into competent TouchDesigner collaborators, not just code runners. Two design principles drive every decision:

1. **See the network before acting on it.** Visual programming environments punish blind edits. Every tool should give the agent a way to either *look at* or *introspect* the network before and after mutating it.
2. **Assume the LLM's memory is unreliable.** TD parameter names are wildly non-obvious (`radx` vs `radius`, `center` vs `centerx/y/z`). Tools must push the agent toward verification (`get_td_node_parameters`, `describe_td_tools`) before hallucinating.

The fork inherits 8beeeaaat's transport and packaging rigor and adds the *authoring surface* that both upstream and satoruhiga are missing: viewport capture, GLSL editing, scene scaffolds, cook control, layout intelligence, and a Python helper library that handles TD's weirder corners (docked DATs, nested baseCOMP cooking, frame-boundary error caching).

## Non-goals

- **Not a new MCP SDK.** We use `@modelcontextprotocol/sdk` as shipped.
- **Not a competing transport.** HTTP + WebServer DAT is fine; don't rebuild it on WebSocket or OSC.
- **Not a Python-first MCP.** Keep the Node.js MCP server; put TD-side code in Python modules loaded from a `.tox`.
- **Not a fork of the fork.** If upstream lands a feature we're building, we rebase and drop our version.

## Phases

### ✅ Phase 1 — Rebrand (complete, 2026-04-10)

Rename package, CLI, Docker image, MCP registry ID, `.mcpb` bundle. Rewrite README, CHANGELOG, and manifest to document the fork relationship. No code logic changed.

### ✅ Phase 2 — Docs & planning (complete, 2026-04-10)

- [x] `docs/roadmap.md` — this file
- [x] `docs/architecture-td-mcp.md` — fork architecture companion
- [x] GitHub Issues opened for every Phase 3 item ([#2](https://github.com/DazaiStudio/td-mcp/issues/2) – [#9](https://github.com/DazaiStudio/td-mcp/issues/9))
- [x] Portfolio-tone README rewrite, upstream tutorial assets and Japanese translations removed

### ✅ Phase 3 — Implementation (complete, 2026-04-10)

All eight items shipped in commits `f6cf8df` and `05f807d`; issues [#2](https://github.com/DazaiStudio/td-mcp/issues/2) – [#9](https://github.com/DazaiStudio/td-mcp/issues/9) closed.

1. [x] **`op.TDAPI` Python helper library** ([#2](https://github.com/DazaiStudio/td-mcp/issues/2)) — `td/modules/tdapi/`
2. [x] **`td_pane` + `td_selection`** ([#3](https://github.com/DazaiStudio/td-mcp/issues/3))
3. [x] **`td_cook` recursive** ([#4](https://github.com/DazaiStudio/td-mcp/issues/4))
4. [x] **`td_viewport`** ([#5](https://github.com/DazaiStudio/td-mcp/issues/5))
5. [x] **`td_connect` + `td_layout`** ([#6](https://github.com/DazaiStudio/td-mcp/issues/6))
6. [x] **`td_glsl`** ([#7](https://github.com/DazaiStudio/td-mcp/issues/7))
7. [x] **`td_scaffold`** ([#8](https://github.com/DazaiStudio/td-mcp/issues/8))
8. [x] **`td-guide` skill** ([#9](https://github.com/DazaiStudio/td-mcp/issues/9))

**Build & verification** (commit `fef1c46`):

- [x] `orval.config.ts` reads OpenAPI from `src/api/index.yml` (no Docker required for `gen:mcp`)
- [x] Upstream type-name drift fixed (`CreateNodeRequest` → `CreateNodeBody`, `Xxx200ResponseData` → `Xxx200Data`)
- [x] `npm run build:dist` passes
- [x] `npm run lint:biome` passes (0 errors)
- [x] `npm run lint:tsc` passes
- [x] `ruff check td/` passes
- [x] 231 unit tests pass

### 🚀 Phase 4 — Publishing (in progress, tracked in [#10](https://github.com/DazaiStudio/td-mcp/issues/10))

Requires the maintainer's environment (TD install, npm account, GitHub PR access to external repos) — cannot be automated.

- [x] `.claude-plugin/marketplace.json` scaffolded for `/plugin marketplace add DazaiStudio/td-mcp`
- [ ] Update `mcp_webserver_base.tox` inside TouchDesigner to import `fork_controller` (manual edit inside TD, then re-save the `.tox`)
- [ ] `npm publish td-mcp` under the DazaiStudio account with provenance
- [ ] Full release build with Docker (`npm run gen:webserver` + `npm run build:mcpb` → `td-mcp.mcpb` asset)
- [ ] GitHub Release with `td-mcp-td.zip` + `td-mcp.mcpb` attached
- [ ] Submit to `modelcontextprotocol/registry` as `io.github.dazaistudio/td-mcp`
- [ ] 60-second demo video (deferred by maintainer)
- [ ] Launch posts to r/TouchDesigner and Derivative Discord `#ai` channel (deferred by maintainer)

---

## Tool Specifications

### `op.TDAPI` Python helper library

A Python module loaded into TouchDesigner via the `.tox`, exposed as `op.TDAPI` so that *any* `execute_python_script` call can use it without importing. Ported (with attribution) from [satoruhiga/claude-touchdesigner](https://github.com/satoruhiga/claude-touchdesigner/blob/main/touchdesigner/toe/src/TouchDesignerAPI.py) with modifications.

**Functions:**

```python
# Creation — docked-DAT aware (GLSL TOPs auto-create _pixel/_vertex DATs)
op.TDAPI.CreateOp(base, op_type, name=None, x=0, y=0) -> Op
op.TDAPI.CreateGeometryComp(base, name, input_op) -> COMP   # scaffolds Geo COMP with in/out SOP
op.TDAPI.ChainOperators([op1, op2, op3], spacing=200) -> None

# Movement — respects docked ops
op.TDAPI.MoveOp(target, x, y) -> None

# Layout intelligence
op.TDAPI.GetBounds(ops) -> {x0, y0, x1, y1}
op.TDAPI.GetAllBounds(base) -> Bounds
op.TDAPI.CheckOverlap(op, area) -> bool
op.TDAPI.FindEmptyArea(base, width=100, height=100) -> (x, y)
op.TDAPI.FindTypeConversionPosition(base, op_type) -> (x, y)

# Introspection (pushes LLM away from hallucinating parameter names)
op.TDAPI.GetParameterList(op_type) -> list[{name, label, default, range, style}]
op.TDAPI.GetParameterHelp(op_type, par_name) -> str
op.TDAPI.GetOperatorInfo(op) -> dict

# Error handling with frame-boundary awareness
op.TDAPI.CheckErrors(op, recurse=True) -> list[{path, msg, frame}]
# NOTE: TD updates the error cache only on frame boundaries.
# Code that mutates, then checks errors, MUST do so in two separate td_execute calls.

# Cook control — fixes nested baseCOMP bug
op.TDAPI.ForceCook(path, recurse=True) -> {cooked_ops, cook_time_ms}

# Layout debugging
op.TDAPI.PrintLayout(base) -> str   # ASCII dump of network layout
```

**Acceptance:** Every function listed above callable from a single `execute_python_script` with no explicit import. `td_scaffold`, `td_connect`, `td_layout` all delegate to this library.

**Credit:** Upstream source is satoruhiga/claude-touchdesigner (MIT). We keep the attribution in the file header.

---

### `td_pane` / `td_selection`

Cheap, high-value context tools. These tell the agent *where the user is looking* and *what is already selected* so that mutations happen in the right place.

```typescript
td_pane(args: { detailLevel?: "minimal" | "summary" | "detailed" }): {
  path: string;           // e.g. "/project1/geo1"
  tx: number; ty: number; // pan
  zoom: number;
  viewportSize: [number, number];
}

td_selection(args: { detailLevel?: "minimal" | "summary" | "detailed" }): {
  count: number;
  ops: Array<{ path: string; type: string; x: number; y: number }>;
}
```

**TD-side endpoints** (via WebServer DAT):
- `GET /editor/pane` → current NetworkEditor state
- `GET /editor/selection` → array of selected operators in pane

**Acceptance:** When the user has a pane open at `/project1/geo1` and 2 ops selected, both tools return correct data. Tools respect the standard `detailLevel` / `responseFormat` / `limit` contract. Ported (with attribution) from satoruhiga.

---

### `td_cook`

Fixes the nested-baseCOMP cooking bug documented in [`feedback_td_cooking.md`](https://github.com/DazaiStudio/td-mcp/issues) (also mentioned in maintainer's lighting control repo). Operators *inside* a nested `baseCOMP` don't cook automatically when only referenced indirectly — the cached buffer goes stale.

```typescript
td_cook(args: {
  path: string;                   // op path, or "/" for the whole project
  recurse?: boolean;              // default: true — force-cook all descendants
  detailLevel?: "minimal" | "summary" | "detailed";
}): {
  cooked: number;                 // count of ops cooked
  skipped: number;
  totalCookTimeMs: number;
  errors: Array<{ path: string; msg: string }>;
}
```

**TD-side implementation:**
```python
def force_cook(path, recurse=True):
    target = op(path)
    if not target:
        raise ValueError(f"no op at {path}")
    cooked = 0; errs = []
    ops = target.findChildren(type=td.OP) if recurse else [target]
    for o in ops:
        try:
            o.cook(force=True)
            cooked += 1
        except Exception as e:
            errs.append({"path": o.path, "msg": str(e)})
    return {"cooked": cooked, "errors": errs, ...}
```

**Secondary behavior:** after every `create_td_node` / `update_td_node_parameters` targeting an op inside a base/tox COMP, auto-inject a cook pass on the parent COMP. Optional via server flag `--auto-cook-nested=true` (default on).

**Acceptance:** Reproduce the nested-baseCOMP staleness with a minimal test fixture, confirm `td_cook` resolves it. Add a `docs/troubleshooting.md` entry explaining the bug and the mitigation.

---

### `td_viewport`

The single highest-ROI new tool. Returns a PNG of a TOP, a COMP viewer, or the network editor pane. Claude can then *see* what it just built.

```typescript
td_viewport(args: {
  target: string;                 // TOP path ("/project1/out1"), COMP path, or "pane" for network editor
  width?: number; height?: number;// default: intrinsic for TOP, 1024 for pane
  format?: "png" | "jpg";         // default: "png"
  quality?: number;               // jpg only, 1-100, default 85
  returnAs?: "base64" | "path";   // default: "base64"
}): {
  format: "png" | "jpg";
  width: number; height: number;
  encoding: "base64" | "file";
  data: string;                   // base64 payload or temp file path
  sizeBytes: number;
}
```

**TD-side implementation strategies:**

- **TOP capture**: `op(path).save(filename)` or `saveByteArray()` into a `tempDAT` then base64-encode.
- **Network editor pane**: insert a temporary `panelCOMP` containing a `Panel Capture TOP`, save, delete. Or use `ui.panes[...].savePane()` if exposed.
- **COMP viewer**: look up the COMP's `viewerCOMP` reference, apply same TOP capture flow.

**Acceptance:** Calling `td_viewport({target: "/project1/noise1"})` returns a PNG that visually matches the noise1 viewer. `target: "pane"` returns a screenshot of the current network editor pane. Temp files cleaned up after response.

**Open questions:**
- Is `ui.panes[i].savePane(filename)` available in TD 2024? (verify during implementation)
- Should we stream large images as a temp file path by default to avoid context-window blowup?

---

### `td_connect` / `td_layout`

First-class wiring and layout. Both delegate to `op.TDAPI` under the hood but expose the capability directly so the agent doesn't need to write Python for every wire.

```typescript
td_connect(args: {
  from: string;        // op path
  to: string;          // op path
  fromOutlet?: number; // default 0
  toInlet?: number;    // default 0
}): { ok: true } | { ok: false; reason: string };

td_layout(args: {
  action: "find_empty_area" | "check_overlap" | "chain";
  base?: string;       // parent path (default: /project1)
  width?: number;      // find_empty_area
  height?: number;     // find_empty_area
  op?: string;         // check_overlap
  ops?: string[];      // chain
  spacing?: number;    // chain (default 200)
}): /* variant per action */
```

**Compatibility validation:** `td_connect` should check inlet/outlet compatibility server-side *before* hitting TD. `td_layout` should fail loudly if the base doesn't exist.

**Acceptance:** Connect a `noiseTOP` → `nullTOP`, confirm wire visible in TD. `td_layout(action: "find_empty_area", base: "/project1", width: 200, height: 200)` returns `(x, y)` that doesn't overlap any existing op.

---

### `td_glsl`

First-class GLSL shader authoring. Critical feature: **docked-DAT awareness**. When you create a `glslTOP`, TD auto-creates `_pixel_shader` and `_vertex_shader` DATs, docked to the parent. Most agent tools orphan these by setting `nodeX/nodeY` manually. This tool handles them correctly.

```typescript
td_glsl(args: {
  path: string;                              // GLSL TOP / MAT / POP path
  stage: "pixel" | "vertex" | "compute";
  code?: string;                             // write (omit for read)
  returnCompiled?: boolean;                  // include any TD compile errors
}): {
  stage: string;
  docked_dat_path: string;                   // e.g. "/project1/glsl1_pixel"
  code: string;                              // current or newly-set code
  errors: Array<{ line: number; msg: string }> | null;
}
```

**TD-side implementation:**
```python
def glsl_read(path, stage):
    target = op(path)
    dat = target.par.pixelshader.eval() if stage == "pixel" else target.par.vertexshader.eval()
    return {"docked_dat_path": dat.path, "code": dat.text}
```

**Acceptance:** Reading the default pixel shader of a fresh `glslTOP` returns the stub GLSL text. Writing new code updates the docked DAT (not a new unrelated DAT). Compile errors (if any) returned in the response.

---

### `td_scaffold`

One-shot scene templates. This is the *"zero-to-something"* accelerator — the kind of tool that wins demo videos.

```typescript
td_scaffold(args: {
  template:
    | "render_pipeline"       // cam + geo + render TOP + out
    | "feedback_loop"         // noise TOP → comp → feedback TOP → null → back
    | "instanced_particles"   // point SOP → instance COMP → render
    | "audio_reactive"        // audio CHOP → analyze → drive TOP params
    | "projection_mapping";   // kantan mapper / mapping COMP setup
  base?: string;              // parent path, default /project1
  name?: string;              // prefix for created ops
  params?: Record<string, any>;// template-specific options
}): {
  createdOps: string[];       // list of paths created
  wiring: Array<{ from: string; to: string }>;
  entryPoint: string;         // the "use this" op path
  description: string;        // human-readable summary of what was scaffolded
}
```

**Acceptance:** Each template creates a working network that cooks without errors. Templates are idempotent (running twice produces `_1`, `_2` suffix). Every template ships with a matching example under `examples/`.

---

### `td-guide` skill

A [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills) that bundles patterns and gotchas for working with TD. Ported from [satoruhiga/claude-touchdesigner](https://github.com/satoruhiga/claude-touchdesigner/blob/main/touchdesigner/skills/td-guide/SKILL.md) with extensions.

**Structure:**

```
skills/td-guide/
├── SKILL.md                         # main skill file, loaded when agent needs TD patterns
└── reference/
    ├── basics.md                    # operator families, network editor concepts
    ├── operator-families.md         # SOP / POP / TOP / CHOP / DAT / MAT / COMP
    ├── geometry-comp.md             # Geo COMP, SOP-to-DAT scaffolding
    ├── rendering.md                 # cam + render TOP + out pipeline
    ├── glsl.md                      # GLSL TOP/MAT/POP + docked-DAT handling
    ├── operator-tips.md             # parameter name gotchas, fuzzy matching
    ├── cooking-nested-comps.md      # NEW: the nested baseCOMP bug + td_cook workaround
    └── scaffolds.md                 # NEW: catalog of td_scaffold templates
```

**SKILL.md opening line** (mandatory): "Your prior knowledge of TouchDesigner parameter names is unreliable. Assume your memory is completely unreliable. Use `get_td_node_parameters` or `op.TDAPI.GetParameterList` before setting any parameter."

**Acceptance:** `/plugin install DazaiStudio/td-mcp` in Claude Code loads the skill. The agent calls `get_td_node_parameters` before setting any parameter on an op it just created.

---

## Open Questions / Deferred Decisions

1. **Cross-client plugin marketplace.** Claude Code plugins use `.claude-plugin/marketplace.json`. Is there a similar format for Cursor/Continue/Windsurf? → Defer to Phase 4.
2. **Python helper library packaging.** Should `op.TDAPI` live inside the existing `mcp_webserver_base.tox` or as a separate `td_api.tox` that other projects can use standalone? → Phase 3 decision.
3. **Nested baseCOMP auto-cook scope.** Should auto-cook only fire on tools that mutate (create/update), or also on read tools that return stale data? → Start with mutation-only, revisit after testing.
4. **Upstream sync cadence.** Weekly? Per upstream release? Manual? → Manual for now; automate in Phase 4.
5. **License header for ported satoruhiga code.** MIT-compatible, need to preserve upstream attribution. → Phase 3: add `# Based on satoruhiga/claude-touchdesigner (MIT)` header to every ported file.

---

## Traceability

Every tool above corresponds to a GitHub Issue in `DazaiStudio/td-mcp`. Issues link back to the section anchors in this file. PRs that implement a tool must reference both the Issue and the anchor.

## Changelog for this document

- 2026-04-10 — Initial Phase 2 roadmap. Covers all Phase 3 tools and Phase 4 publishing plan.
