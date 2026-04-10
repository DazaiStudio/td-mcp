# td-mcp

**A TouchDesigner MCP server built for agents that need to see the network, not just guess at it.**

[![Version](https://img.shields.io/npm/v/td-mcp?style=flat&colorA=000000&colorB=000000)](https://www.npmjs.com/package/td-mcp)
[![License](https://img.shields.io/github/license/DazaiStudio/td-mcp?style=flat&colorA=000000&colorB=000000)](LICENSE)

`td-mcp` lets Claude, Cursor, Claude Desktop, and any stdio-compatible MCP client drive a running TouchDesigner project — creating and wiring nodes, running Python, **capturing viewport screenshots**, **authoring GLSL shaders**, **scaffolding entire scenes**, and handling the nested-baseCOMP cooking weirdness that trips up every real project.

Built and maintained by **Dazai (Tatsan) Chen** — Lighting Technician at **NYU 370J Media Commons**, where this project drives the live DMX lighting rigs across the Ballrooms, Black Box, and Audio Lab spaces.

---

## Why this exists

I spend my days in TouchDesigner. As AI agents became genuinely useful, I wanted one that could actually collaborate with me in TD — not just stringify some Python and hope it compiles, but *see* what it just built, understand that `radx` and `radius` are different things on different SOPs, and avoid the cook-scope landmines I hit in production.

The existing MCP servers for TouchDesigner get the CRUD surface right but stop there. They can create a `glslTOP`, but they can't read back the viewer to tell whether the shader compiled. They can write a Python script, but they can't verify that a nested base COMP actually cooked after the edit. They treat the agent as a code executor, not a collaborator.

`td-mcp` is my answer. It's designed around two principles:

1. **See the network before acting on it.** Every mutation tool is paired with a way to inspect the result — viewport captures, parameter reads, error checks, cook-state introspection.
2. **Assume the LLM's memory is unreliable.** TD parameter names are notoriously non-obvious. Tools push the agent toward verification (`get_td_node_parameters`, `describe_td_tools`) before setting anything, backed by a skill that says so explicitly.

The architecture, transport, and packaging build on [8beeeaaat/touchdesigner-mcp](https://github.com/8beeeaaat/touchdesigner-mcp) (see [Credits](#credits) for the full story); the authoring surface — viewport capture, GLSL editing, scene scaffolding, cook control, layout intelligence, and the Python helper library — is new.

## Capabilities

### Available today (from the inherited base)

| Area | Tools |
|---|---|
| Node CRUD | `create_td_node`, `delete_td_node`, `get_td_nodes`, `get_td_node_parameters`, `update_td_node_parameters` |
| Python | `execute_python_script`, `exec_node_method` |
| Introspection | `get_td_info`, `get_td_node_errors`, `get_td_classes`, `get_td_class_details`, `get_module_help` |
| Meta | `describe_td_tools` (filesystem-style tool manifest for code-mode agents) |
| Transports | stdio + Streamable HTTP/SSE |
| Packaging | npm package, Claude Desktop `.mcpb` bundle, Docker image, MCP Registry listing |
| Discipline | `detailLevel` / `responseFormat` / `limit` on every tool to keep context windows sane |

### Landing next (see [`docs/roadmap.md`](docs/roadmap.md))

- **`td_pane` / `td_selection`** — editor context. Tell the agent where the user is looking and what's already selected.
- **`td_viewport`** — PNG capture of any TOP, COMP viewer, or the network editor pane. The single highest-ROI addition.
- **`td_cook`** — recursive force-cook that fixes the nested-baseCOMP staleness bug.
- **`td_glsl`** — first-class GLSL editing that respects docked `_pixel` / `_vertex` DATs instead of orphaning them.
- **`td_scaffold`** — one-shot templates for render pipelines, feedback loops, instanced particles, audio-reactive setups, projection mapping.
- **`td_connect` / `td_layout`** — wiring and layout with overlap-aware placement.
- **`op.TDAPI` Python helper library** — layout intelligence, docked-op awareness, cook-aware error handling, exposed globally inside TD so `execute_python_script` has them without imports.
- **`td-guide` skill** — bundled with the Claude Code plugin, with an opening line the agent cannot ignore: *"Your prior knowledge of TouchDesigner parameter names is unreliable. Use `get_td_node_parameters` before setting any parameter."*

## Installation

> 📦 **Not yet published.** The rebrand is in place and Phase 3 implementation is underway. For the inherited base, the upstream [installation guide](https://github.com/8beeeaaat/touchdesigner-mcp/blob/main/docs/installation.md) still works today. Once published to npm, the flow will be:

```bash
# For any stdio-compatible MCP client
npx -y td-mcp@latest --stdio

# For Claude Code
/plugin install DazaiStudio/td-mcp

# For Claude Desktop
# Download td-mcp.mcpb from releases and double-click to install.
```

Full per-client setup (Claude Code, Claude Desktop, Cursor, Codex, VS Code MCP, Docker) will live in [`docs/installation.md`](docs/installation.md).

## Developer Guide

Local setup, architecture, release workflow, and troubleshooting live in:

- [`docs/development.md`](docs/development.md)
- [`docs/architecture.md`](docs/architecture.md)
- [`docs/roadmap.md`](docs/roadmap.md) — phased delivery plan and per-tool specifications

## Context

This project comes out of real production work at NYU Media Commons. For the companion lighting project that originally motivated `td-mcp` — the TouchDesigner-based DMX control system for the Ballrooms, Black Box, and Audio Lab — see [`DazaiStudio/nyu-mc-touchdesigner-template`](https://github.com/DazaiStudio/nyu-mc-touchdesigner-template).

## Credits

`td-mcp` is a fork of and builds directly on two excellent open-source projects. Both are credited in code, in documentation, and here:

- **[@8beeeaaat](https://github.com/8beeeaaat)** — author of [`touchdesigner-mcp`](https://github.com/8beeeaaat/touchdesigner-mcp), the base this project inherits from. The transport layer (stdio + Streamable HTTP), `.mcpb` packaging, MCP Registry listing, semver handshake, context-window discipline, and the entire current tool surface are theirs. `td-mcp` takes no credit for that work and exists only to extend it.
- **[@satoruhiga](https://github.com/satoruhiga)** — author of [`claude-touchdesigner`](https://github.com/satoruhiga/claude-touchdesigner), whose `op.TDAPI` Python helper library and `td-guide` skill design directly inspired (and will be ported, with attribution, into) this project.

Upstream `main` is tracked as the `upstream` git remote and periodically merged.

## Maintainer

**Dazai (Tatsan) Chen** — Lighting Technician, NYU 370J Media Commons. GitHub: [@DazaiStudio](https://github.com/DazaiStudio).

## License

MIT — same as both upstream projects. See [LICENSE](LICENSE).
