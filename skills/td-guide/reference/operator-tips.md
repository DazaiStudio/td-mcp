# Operator tips and parameter gotchas

A hand-picked list of the most common "that isn't the parameter name" mistakes. Always verify with `get_td_node_parameters` — this file is a starter set, not an authoritative reference.

## SOPs

| Op | Common guess | Actual name |
|---|---|---|
| `sphereSOP` | `radius` | `radx`, `rady`, `radz` |
| `boxSOP` | `size` | `sizex`, `sizey`, `sizez` |
| `gridSOP` | `width` / `height` | `sizex`, `sizey` |
| `transformSOP` | `translate` | `tx`, `ty`, `tz` |
| `transformSOP` | `rotate` | `rx`, `ry`, `rz` |
| `transformSOP` | `scale` | `sx`, `sy`, `sz` |

## TOPs

| Op | Common guess | Actual name |
|---|---|---|
| `noiseTOP` | `amplitude` | `amp` |
| `noiseTOP` | `frequency` | `period` (yes, period not frequency) |
| `levelTOP` | `gain` / `exposure` | depends on TD version — check `get_td_node_parameters` |
| `textTOP` | `fontSize` | `fontsizex` |
| `renderTOP` | `cam` | `camera` |

## CHOPs

| Op | Common guess | Actual name |
|---|---|---|
| `lfoCHOP` | `frequency` | `rate` (cycles per second) |
| `audiofileinCHOP` | `file` | `file` (correct — but `play`, `playmode` also matter) |
| `constantCHOP` | `value1` | `value0` (0-indexed) |

## COMPs

| Op | Common guess | Actual name |
|---|---|---|
| `cameraCOMP` | `position` | `tx`, `ty`, `tz` |
| `cameraCOMP` | `target` / `lookat` | use `par.lookat` or manually set rotation |
| `lightCOMP` | `color` | `colorr`, `colorg`, `colorb` |
| `geometryCOMP` | `scale` | `sx`, `sy`, `sz` (on the transform, not the geo itself) |

## When in doubt

- `tdapi.GetParameterList(op_type)` returns the full list of parameter names for an op type.
- `tdapi.GetParameterHelp(op_type, param_name)` returns TD's built-in help entry for a specific parameter.
- `get_td_node_parameters(nodePath)` returns the current parameter values on an existing op — useful for reading defaults you're about to override.
- `describe_td_tools({filter: "noise"})` finds operators by fuzzy match on name, family, or type.

## Vector parameters are usually split

TouchDesigner almost always splits 2- or 3-component vector parameters into individual scalar parameters with an `x`/`y`/`z` suffix (or `0`/`1`/`2` for higher-dimensional). Do not try to set a parameter to a tuple — set each component individually:

```python
# Wrong
op("/project1/box1").par.size = (1, 2, 3)

# Right
op("/project1/box1").par.sizex = 1
op("/project1/box1").par.sizey = 2
op("/project1/box1").par.sizez = 3
```

If the parameter is genuinely a tuple (rare), `par.val` accepts one.
