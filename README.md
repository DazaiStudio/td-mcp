# td-mcp

**TouchDesigner ↔ AI agents, done right.**

An [MCP](https://modelcontextprotocol.io/) server that lets Claude, Cursor, Claude Desktop, and any stdio-compatible MCP client drive a running TouchDesigner project — create nodes, run Python, capture what the viewer sees, author GLSL shaders, scaffold whole scenes in one call.

[![License](https://img.shields.io/github/license/DazaiStudio/td-mcp?style=flat&colorA=000000&colorB=000000)](LICENSE)
[![TouchDesigner](https://img.shields.io/badge/TouchDesigner-2024+-000000?style=flat)](https://derivative.ca/)
[![MCP](https://img.shields.io/badge/MCP-1.27+-000000?style=flat)](https://modelcontextprotocol.io/)

---

## What it does

`td-mcp` gives an AI agent **21 tools** for driving TouchDesigner. They fall into four groups:

### See the network

| Tool | What it does |
|---|---|
| `td_pane` | Where is the user looking? (current network editor pane) |
| `td_selection` | What's selected right now? |
| `td_viewport` | Capture a PNG of a TOP, COMP viewer, or the pane — so the agent can *see* its output |
| `get_td_nodes` | List children at a path |
| `get_td_node_parameters` | Read an op's parameters |
| `get_td_node_errors` | Check for errors on an op and its children |

### Mutate the network

| Tool | What it does |
|---|---|
| `create_td_node` | Create a node |
| `delete_td_node` | Delete a node |
| `update_td_node_parameters` | Set parameter values |
| `td_connect` | Wire two ops — with family-compatibility validation |
| `td_layout` | Find an empty area, check overlap, or chain-layout a list of ops |

### Author content

| Tool | What it does |
|---|---|
| `execute_python_script` | Run arbitrary Python in TD, with the `tdapi` helper lib pre-loaded |
| `exec_node_method` | Call a method on a node (`cook`, `pulse`, `reset`, …) |
| `td_glsl` | Read / write a GLSL shader stage — respects docked `_pixel` / `_vertex` DATs |
| `td_scaffold` | One-shot templates: `render_pipeline`, `feedback_loop`, `instanced_particles`, `audio_reactive`, `projection_mapping` |
| `td_cook` | Recursive force-cook — fixes the nested `baseCOMP` staleness bug |

### Introspect TD itself

| Tool | What it does |
|---|---|
| `get_td_info` | TD version, OS, build |
| `get_td_classes` / `get_td_class_details` | Look up TD Python classes |
| `get_td_module_help` | Python `help()` for a TD module |
| `describe_td_tools` | Self-describing filesystem manifest for code-mode agents |

All tools accept `detailLevel` (`minimal` / `summary` / `detailed`) and `responseFormat` (`json` / `yaml` / `markdown`) to keep context windows from exploding.

## Quick start

### Claude Code

```bash
/plugin marketplace add DazaiStudio/td-mcp
/plugin install td-mcp
```

That installs both the MCP server and the bundled **`td-guide`** skill, which teaches the agent *not* to hallucinate TD parameter names.

### Claude Desktop / Cursor / others

```bash
# Works with anything that supports stdio MCP:
npx -y td-mcp@latest --stdio
```

Add to your MCP client config:

```jsonc
{
  "mcpServers": {
    "td-mcp": {
      "command": "npx",
      "args": ["-y", "td-mcp@latest", "--stdio"]
    }
  }
}
```

### TouchDesigner side

1. Grab the latest `td-mcp-td.zip` from the [releases page](https://github.com/DazaiStudio/td-mcp/releases).
2. Unzip it somewhere stable.
3. Drag `mcp_webserver_base.tox` into your TouchDesigner project — usually at `/project1/mcp_webserver_base`.
4. Save the project. The WebServer DAT inside the `.tox` listens on `127.0.0.1:9981`.

That's it. The Node-side MCP server (step above) talks to the TD-side WebServer DAT over HTTP; your AI agent talks to the Node-side server over stdio.

## Example

```
you: create a feedback loop scene for me

agent uses td_scaffold({template: "feedback_loop"}):
  ✓ feedback_loop_noise (noiseTOP)
  ✓ feedback_loop_fb    (feedbackTOP)
  ✓ feedback_loop_comp  (compositeTOP)
  ✓ feedback_loop_out   (nullTOP)
  → wired, cooked, ready to view

agent uses td_viewport({target: "/project1/feedback_loop_out"}):
  [returns PNG of the rendered output]
```

The agent sees what it built and can iterate on it — change a parameter, re-capture, keep going — without guessing.

## Why a fork?

`td-mcp` builds on [**8beeeaaat/touchdesigner-mcp**](https://github.com/8beeeaaat/touchdesigner-mcp), which provides a solid stdio + HTTP transport, `.mcpb` packaging, MCP Registry listing, and semver handshake. That foundation is excellent and stays unchanged in this fork.

What this fork adds:

- **Viewport capture** (`td_viewport`) — the single biggest missing piece for AI agents working in a visual environment
- **GLSL authoring** (`td_glsl`) — handles the docked `_pixel_shader` / `_vertex_shader` DATs correctly
- **Scene scaffolds** (`td_scaffold`) — five production-ready templates
- **Recursive cook control** (`td_cook`) — fixes the nested `baseCOMP` staleness bug that trips up real projects
- **Layout intelligence** (`td_layout`) — find empty area, check overlap, chain operators
- **First-class wiring** (`td_connect`) — with family-compatibility validation
- **Editor context** (`td_pane`, `td_selection`) — where is the user looking?
- **`tdapi` Python helper library** inside TD — ported from [satoruhiga/claude-touchdesigner](https://github.com/satoruhiga/claude-touchdesigner), exposes layout-aware creation, docked-DAT-safe movement, parameter introspection
- **`td-guide` skill** bundled with the Claude Code plugin — forces the agent to verify parameter names before setting them

The full roadmap and tool specs live in [`docs/roadmap.md`](docs/roadmap.md).

## Project layout

```
td-mcp/
├── src/                       # Node.js MCP server (TypeScript)
│   ├── features/tools/
│   │   └── handlers/
│   │       ├── tdTools.ts     # Upstream 13 tools
│   │       └── forkTools.ts   # Fork 8 tools
│   ├── tdClient/
│   │   ├── touchDesignerClient.ts  # Upstream HTTP client
│   │   └── forkClient.ts           # Fork HTTP client
│   └── ...
├── td/                        # TouchDesigner-side Python
│   ├── mcp_webserver_base.tox # Drop into your TD project
│   └── modules/
│       ├── mcp/               # Upstream MCP services + controllers
│       │   ├── services/
│       │   │   ├── api_service.py
│       │   │   └── fork_service.py    # Fork business logic
│       │   └── controllers/
│       │       ├── api_controller.py
│       │       └── fork_controller.py # /fork/* routing
│       └── tdapi/             # Fork: ported op.TDAPI helpers
├── skills/
│   └── td-guide/              # Claude Code skill
├── docs/
│   ├── roadmap.md             # Phased delivery plan + tool specs
│   ├── architecture.md        # Inherited upstream architecture
│   ├── architecture-td-mcp.md # Fork architecture extensions
│   └── installation.md
└── mcpb/                      # Claude Desktop bundle manifest
```

## Development

```bash
git clone https://github.com/DazaiStudio/td-mcp
cd td-mcp
npm install
npm run gen:mcp        # Generate TypeScript Zod schemas from OpenAPI spec
npm run build:dist     # Compile TypeScript → dist/
npm run test           # Run vitest
npm run lint           # Biome + tsc + ruff
```

For a full release build (including the Docker-based OpenAPI Python codegen and the `.mcpb` bundle), use `npm run build` — which requires Docker.

## Author

Built and maintained by **Dazai (Tatsan) Chen** — Lighting Technician at [NYU 370 Jay Street Media Commons](https://www.instagram.com/370jmediacommons/), where a companion project ([`nyu-mc-touchdesigner-template`](https://github.com/DazaiStudio/nyu-mc-touchdesigner-template)) uses TouchDesigner to drive the DMX lighting rigs across the Ballrooms, Black Box, and Audio Lab.

## Credits

- **[@8beeeaaat](https://github.com/8beeeaaat)** — author of [`touchdesigner-mcp`](https://github.com/8beeeaaat/touchdesigner-mcp), the upstream base. Every piece of transport, packaging, and tooling rigor in this fork is theirs.
- **[@satoruhiga](https://github.com/satoruhiga)** — author of [`claude-touchdesigner`](https://github.com/satoruhiga/claude-touchdesigner), whose `op.TDAPI` Python helper library and `td-guide` skill inspired (and are ported into) this project.

Upstream `main` is tracked via the `upstream` git remote and periodically merged.

## License

MIT — same as both upstream projects. See [LICENSE](LICENSE).
