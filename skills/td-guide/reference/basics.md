# TouchDesigner basics

TouchDesigner is a visual programming environment built around **operators** (nodes) that process data in real time. Every frame, TD walks its dependency graph and **cooks** (evaluates) operators whose inputs have changed. Everything you build is a network of operators wired together with typed connections.

## Core concepts

- **Operator (op).** A single node in the network. Every op has a family (SOP, POP, TOP, CHOP, DAT, MAT, COMP), a type within that family (`boxSOP`, `noiseTOP`, `audiofileinCHOP`, etc.), inputs, outputs, parameters, and an internal state.
- **Family.** Operators are grouped by the kind of data they produce. Families can only be wired to operators of the same family with standard connectors; to cross families you use conversion operators (`tdu` functions, references, or specific bridge operators like `dataDAT`).
- **Network.** A COMP (component) that contains other operators. The root project lives at `/project1`. You can nest COMPs arbitrarily.
- **Cook.** The act of evaluating an operator. Cooks are normally demand-driven — TD only cooks what's needed to produce the current output — but you can force a cook with `op.cook(force=True)` or via `td_cook`.
- **Viewer.** Every op has an optional thumbnail view in the network editor. Set `op.viewer = True` or pass `viewer=True` to `tdapi.CreateOp`.

## Parameter access

Parameters live under `op.par`:

```python
op("/project1/box1").par.sizex = 2
op("/project1/box1").par.sizex.eval()          # get current value
op("/project1/box1").par.sizex.expr = "absTime.frame * 0.1"  # parameter expression
op("/project1/box1").par.sizex.mode = ParMode.EXPRESSION      # CONSTANT / EXPRESSION / EXPORT / BIND
```

**Always verify parameter names first.** Parameter names frequently differ from their visible label. `get_td_node_parameters` or `tdapi.GetParameterList(op_type)` is authoritative.

## Coordinate system

Node positions in the network editor use `(nodeX, nodeY)`. Positive Y is **up** in the network editor (unlike screen coordinates). Docked DATs (e.g. `_pixel_shader`) are positioned relative to their parent and should be moved *together* — that's what `tdapi.MoveOp` does for you.

## Built-in globals

TD's Python environment provides several globals without imports:

- `op(path)` — look up an operator by absolute or relative path
- `parent()` — the containing COMP of the current execution scope
- `me` — the currently-executing operator (in a DAT or callback)
- `ui` — UI controller (panes, dialogs, etc.)
- `td` — the main TD module; most classes are under here
- `absTime` / `root` — time and project root references
- Operator type constants like `boxSOP`, `noiseTOP`, `nullCHOP`

Inside an `execute_python_script` call, all of these are available without imports. `tdapi` is also available (imported at server startup).
