# The nested baseCOMP cooking bug

**TL;DR** — operators inside a nested `baseCOMP` (or `containerCOMP`, or `.tox` COMP) don't always cook automatically when referenced indirectly. Their cached output goes stale even though their inputs have changed. Call `td_cook` on the parent COMP to force a fresh cook.

## What goes wrong

TD's cooking scheduler is demand-driven. When you request the output of an op, TD walks backward through the dependency graph and cooks whatever's dirty. That works for most cases, but it breaks when:

1. You have a base COMP with internal ops.
2. Something outside the COMP reads an internal op via a path reference or expression, *not* via a standard input wire.
3. The internal op's own inputs change.

In this case, TD's scheduler may not notice the dependency chain crosses the COMP boundary, and the internal op keeps serving stale data from its last cook. The symptom is: you updated something, but the downstream data still looks old.

## How to confirm it

- Change a parameter inside the nested COMP.
- Read the affected output from outside the COMP.
- If the output is stale, it's this bug.

You can also check `op(path).cookTime` and `op(path).numCooks` — if the cook count hasn't gone up since your change, the op is stale.

## The fix

### Option A — `td_cook` tool (brute force hammer)

```
td_cook({path: '/project1/base1', recurse: true})
```

This recursively force-cooks every descendant of `/project1/base1`. Use this whenever things look stale. It's the most reliable mitigation.

### Option B — Python-side `tdapi.ForceCook`

Inside an `execute_python_script` call:

```python
import tdapi
result = tdapi.ForceCook("/project1/base1", recurse=True)
# → {"cooked": N, "totalCookTimeMs": ms, "errors": [...]}
```

Same effect as the MCP tool, but usable inline from a larger Python script.

### Option C — Auto-cook-nested server flag

`td-mcp` can fire an automatic cook pass after every mutation that lands inside a base COMP. Start the server with:

```
npx td-mcp --stdio --auto-cook-nested=true
```

This is enabled by default. It makes the tool surface feel more "natural" — mutations Just Work — but it comes at the cost of extra cook work after every edit. Disable with `--auto-cook-nested=false` if you're doing bulk edits and will manually cook at the end.

### Option D — Always-on cook-type on the output

For production projects, put a `nullCHOP` or `nullSOP` (or `nullTOP`) at the internal boundary of your base COMP with `par.cooktype = 'Always'`. This forces the output chain to cook every frame, at the cost of a little performance.

## Why does this happen at all?

TouchDesigner's dependency tracking is designed for a flat network where every connection is a wire. Cross-COMP *references* — path strings, parameter expressions, export binds — are logically edges in the graph but the scheduler doesn't treat them identically. When the reference is a string, there's no cheap way to walk it backward on every frame.

The Derivative team has acknowledged this edge case in community threads but considers it "working as designed" for performance reasons. The explicit cook tool is the official workaround.

## Related

- [`tdapi.ForceCook` source](../../../td/modules/tdapi/__init__.py) — the Python implementation this tool wraps
- [`td_cook` MCP tool](../../../docs/roadmap.md#td_cook) — the roadmap spec for the tool
- The maintainer hit this on a real production project; see the DMX lighting rig at [`DazaiStudio/nyu-mc-touchdesigner-template`](https://github.com/DazaiStudio/nyu-mc-touchdesigner-template) where the `dmxoutCHOP` had to be kept at project level for exactly this reason.
