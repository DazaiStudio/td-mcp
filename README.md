# td-mcp

> **TouchDesigner MCP server** with node CRUD, Python execution, and an extended tool surface for **viewport capture**, **GLSL authoring**, **scene scaffolding**, and **layout intelligence** — built for Claude Code, Claude Desktop, Cursor, and any stdio-compatible MCP client.

[![Version](https://img.shields.io/npm/v/td-mcp?style=flat&colorA=000000&colorB=000000)](https://www.npmjs.com/package/td-mcp)
[![License](https://img.shields.io/github/license/DazaiStudio/td-mcp?style=flat&colorA=000000&colorB=000000)](LICENSE)
[![Upstream](https://img.shields.io/badge/forked_from-8beeeaaat%2Ftouchdesigner--mcp-000000?style=flat)](https://github.com/8beeeaaat/touchdesigner-mcp)

---

## About

`td-mcp` is a [Model Context Protocol](https://modelcontextprotocol.io/) server that gives AI agents first-class control of a running TouchDesigner project. It speaks stdio and Streamable HTTP, ships as an npm package, a Claude Desktop `.mcpb` bundle, and a Claude Code plugin, and includes a TouchDesigner-side `.tox` that exposes a JSON/HTTP API via a WebServer DAT.

This project is a **fork of [8beeeaaat/touchdesigner-mcp](https://github.com/8beeeaaat/touchdesigner-mcp)** — full credit to [@8beeeaaat](https://github.com/8beeeaaat) for the transport layer, context-window discipline, semver handshake, `.mcpb` packaging, and the original tool surface. This fork extends that foundation with tools focused on what MCP agents need most in a visual programming environment: **seeing the network**, **authoring shaders**, **scaffolding scenes**, and **not hallucinating parameter names**.

Maintained by **Dazai (Tatsan) Chen** — Lighting Technician at NYU Media Commons ([@DazaiStudio](https://github.com/DazaiStudio)).

## Why fork?

| | Upstream | This fork (planned) |
|---|:-:|:-:|
| Node CRUD (create / delete / list / params) | ✅ | ✅ (unchanged) |
| Python script execution | ✅ | ✅ (unchanged) |
| Error inspection / class/module docs | ✅ | ✅ (unchanged) |
| stdio + Streamable HTTP transport | ✅ | ✅ (unchanged) |
| Context-window discipline (`detailLevel` / `responseFormat` / `limit`) | ✅ | ✅ (unchanged) |
| `.mcpb` bundle / MCP Registry / Docker | ✅ | ✅ (unchanged) |
| **Editor context** (current pane, selection) | ❌ | 🚧 `td_pane` / `td_selection` |
| **Viewport capture** (TOP screenshots, network editor image) | ❌ | 🚧 `td_viewport` |
| **GLSL shader authoring** (docked-DAT aware) | ❌ | 🚧 `td_glsl` |
| **Scene scaffolding** (render pipelines, feedback, particles, audio-reactive) | ❌ | 🚧 `td_scaffold` |
| **Recursive cook control** (fixes nested baseCOMP cooking) | ❌ | 🚧 `td_cook` |
| **Layout intelligence** (find-empty-area, overlap-aware placement) | ❌ | 🚧 `td_layout` |
| **First-class node wiring** | ❌ | 🚧 `td_connect` |
| **`op.TDAPI` Python helper library** (ported from satoruhiga/claude-touchdesigner) | ❌ | 🚧 |
| **`td-guide` skill** ("your prior knowledge is unreliable") | ❌ | 🚧 |

🚧 = planned for the `td-mcp` fork. See [docs/roadmap.md](docs/roadmap.md) for details.

## Installation

> 📦 **Not yet published to npm.** Rebranding is in progress. For now, see the [upstream installation guide](https://github.com/8beeeaaat/touchdesigner-mcp/blob/main/docs/installation.md) for the base setup. New tools and the `td-mcp` package will be published once Phase 3 of the roadmap is complete.

Once published, the install flow will be:

```bash
# For any stdio-compatible MCP client
npx -y td-mcp@latest --stdio

# For Claude Code
/plugin install DazaiStudio/td-mcp

# For Claude Desktop
# Download td-mcp.mcpb from releases, double-click to install.
```

## MCP Tools (current)

All of these come directly from upstream. See the table above for the planned additions.

| Tool | Description |
|---|---|
| `create_td_node` | Creates a new node |
| `delete_td_node` | Deletes an existing node |
| `exec_node_method` | Calls a Python method on a node |
| `execute_python_script` | Executes arbitrary Python in TouchDesigner |
| `get_td_info` | Server environment info |
| `get_td_classes` / `get_td_class_details` / `get_module_help` | TD Python class & module docs |
| `get_td_nodes` / `get_td_node_parameters` / `get_td_node_errors` | Node introspection |
| `update_td_node_parameters` | Parameter updates |
| `describe_td_tools` | Filesystem-style tool manifest for code-mode agents |

### Prompts

| Prompt | Description |
|---|---|
| `Search node` | Fuzzy search for nodes by name / family / type |
| `Node connection` | Guidance for wiring TD nodes |
| `Check node errors` | Recursive error inspection |

## Developer Guide

See the [Developer Guide](docs/development.md) for local setup, client configuration, project structure, and release workflow notes. That guide is still the upstream document — Dazai-maintained sections will be added as the fork diverges.

## Troubleshooting

The upstream [Troubleshooting section](https://github.com/8beeeaaat/touchdesigner-mcp/blob/main/README.md#troubleshooting) is authoritative for version compatibility, connection errors, and the `mcp_webserver_base.tox` setup. This README will grow its own troubleshooting section as fork-specific tools land.

## Upstream Sync

This fork preserves upstream commit history and periodically merges from `8beeeaaat/touchdesigner-mcp` (tracked as remote `upstream`). To sync:

```bash
git fetch upstream
git merge upstream/main
```

## Credits

- **[@8beeeaaat](https://github.com/8beeeaaat)** — original author of `touchdesigner-mcp`. The transport, packaging, tooling, and context-window design decisions in this repo are theirs. This fork stands on their shoulders.
- **[@satoruhiga](https://github.com/satoruhiga)** — author of `claude-touchdesigner`, whose `op.TDAPI` Python helper library and `td-guide` skill design are the inspiration for the new Python-side helpers in this fork.
- **Dazai (Tatsan) Chen** — fork maintainer. Lighting Technician at NYU 370 Jay Street Media Commons.

## License

MIT — same as upstream. See [LICENSE](LICENSE).
