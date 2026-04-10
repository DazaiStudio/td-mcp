# `tdapi` — TouchDesigner helper library

Python module loaded inside TouchDesigner (via the MCP `.tox`) that provides
three categories of helpers aimed at AI agents and the Python code they run:

- **Creation & movement that handle docked operators correctly.** `CreateOp`,
  `MoveOp`, `CreateGeometryComp`, `ChainOperators`.
- **Layout intelligence.** `FindEmptyArea`, `CheckOverlap`, `GetBounds`,
  `GetAllBounds`, `FindTypeConversionPosition`, plus the `AABB` type.
- **Introspection that pushes the LLM toward verifying parameter names.**
  `GetOperatorInfo`, `GetParameterList`, `GetParameterHelp`, `PrintLayout`.
- **Error inspection with frame-boundary awareness.** `CheckErrors`.
- **Cook control** (fork addition). `ForceCook` — recursive force-cook that
  fixes the nested-`baseCOMP` staleness bug documented in
  [`docs/roadmap.md#td_cook`](../../../docs/roadmap.md#td_cook).

## How to use it

### From an `execute_python_script` call

The module is on `sys.path` as soon as the MCP WebServer DAT initializes
(see `td/import_modules.py`). Import and use directly:

```python
import tdapi

# Layout-aware creation:
x, y = tdapi.FindEmptyArea(op("/project1"), 200, 200)
box = tdapi.CreateOp(op("/project1"), boxSOP, "box1", x, y)

# Verify parameter names before setting them:
params = tdapi.GetParameterList("boxSOP")
# → ['size', 'sizex', 'sizey', 'sizez', ...]

# Recursive cook to fix nested baseCOMP staleness:
result = tdapi.ForceCook("/project1/base1", recurse=True)
# → {"cooked": 12, "totalCookTimeMs": 3.4, "errors": []}
```

### As a COMP extension (`op.TDAPI.*` pattern)

`extension.py` provides `TDAPIExtension`, a class wrapper that binds every
function as a method. Attach it as an extension on a COMP named `TDAPI`
inside `mcp_webserver_base.tox` to enable the short-form:

```python
op("/mcp_webserver_base/TDAPI").CreateOp(op("/project1"), boxSOP, "box1")
```

The `.tox` integration is a **Phase 3.1 follow-up** — the Python code is in
place but the `.tox` itself has not yet been updated to ship a `TDAPI` COMP
with the extension attached. Until then, prefer `import tdapi`.

## Attribution

Most of this module is ported from
[satoruhiga/claude-touchdesigner](https://github.com/satoruhiga/claude-touchdesigner)
(`touchdesigner/toe/src/td_utils.py`, MIT License). The functions retain
upstream semantics; the main change is dropping the `self` parameter that
upstream required because it bound helpers to a class via `setattr` at
import time.

Fork additions (not in upstream):

- `ForceCook(target, recurse=True)` — recursive force-cook for the
  `td_cook` MCP tool.

The `AABB` named tuple and `FindTypeConversionPosition` come from upstream
unchanged (modulo the `self` strip).

## Files

- [`__init__.py`](__init__.py) — public API, module-level functions.
- [`extension.py`](extension.py) — `TDAPIExtension` class wrapper for
  COMP-extension-style access.
- [`README.md`](README.md) — this file.

## Tracked by

GitHub issue [#2: Phase 3.1 — Port op.TDAPI Python helper library](https://github.com/DazaiStudio/td-mcp/issues/2).

## License

MIT (same as upstream and the fork). See repository [`LICENSE`](../../../LICENSE).
