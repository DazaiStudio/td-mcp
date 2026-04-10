/**
 * forkTools — td-mcp fork's additional MCP tool handlers.
 *
 * These tools are NOT in upstream (8beeeaaat/touchdesigner-mcp). They live
 * in their own handler file so that upstream sync merges stay clean.
 *
 * Each tool uses inline Zod schemas (no dependency on the orval codegen
 * output in src/gen/) and delegates HTTP transport to ``ForkClient``,
 * which talks to the /fork/* routes served by
 * ``td/modules/mcp/controllers/fork_controller.py``.
 *
 * All tools follow the upstream formatting contract by accepting
 * ``detailLevel`` and ``responseFormat`` query params (though the
 * current presenters are minimal — they simply JSON-stringify or
 * key/value-format the result).
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { FORK_TOOL_NAMES } from "../../../core/constants.js";
import { handleToolError } from "../../../core/errorHandling.js";
import type { ILogger } from "../../../core/logger.js";
import { ForkClient } from "../../../tdClient/forkClient.js";

// -----------------------------------------------------------------------------
// Shared formatting schema (local copy so this file has no gen/ dependency)
// -----------------------------------------------------------------------------

const detailLevelSchema = z
	.enum(["minimal", "summary", "detailed"])
	.optional()
	.describe(
		"Response detail: 'minimal' for IDs only, 'summary' for key fields, 'detailed' for everything.",
	);

const responseFormatSchema = z
	.enum(["json", "yaml", "markdown"])
	.optional()
	.describe("Output format wrapping for the tool result. Defaults to JSON.");

const formattingSchema = z.object({
	detailLevel: detailLevelSchema,
	responseFormat: responseFormatSchema,
});

// -----------------------------------------------------------------------------
// Per-tool schemas
// -----------------------------------------------------------------------------

const paneSchema = formattingSchema;

const selectionSchema = formattingSchema;

const cookSchema = formattingSchema.extend({
	path: z.string().describe("Op path, or '/' for the whole project."),
	recurse: z
		.boolean()
		.optional()
		.default(true)
		.describe("Force-cook all descendants (default true)."),
});

const viewportSchema = formattingSchema.extend({
	format: z.enum(["png", "jpg"]).optional().default("png"),
	height: z.number().int().positive().optional(),
	quality: z
		.number()
		.int()
		.min(1)
		.max(100)
		.optional()
		.default(85)
		.describe("JPEG quality (1-100). Ignored for PNG."),
	returnAs: z
		.enum(["base64", "path"])
		.optional()
		.default("base64")
		.describe(
			"'base64' inlines the image; 'path' returns a temp file path. Captures >256KB are always returned as a path.",
		),
	target: z
		.string()
		.describe(
			"TOP path, COMP path (looks up viewer TOP), or the literal 'pane' for the current network editor pane.",
		),
	width: z.number().int().positive().optional(),
});

const connectSchema = formattingSchema.extend({
	from: z.string().describe("Source op path."),
	fromOutlet: z.number().int().nonnegative().optional().default(0),
	to: z.string().describe("Destination op path."),
	toInlet: z.number().int().nonnegative().optional().default(0),
});

const layoutSchema = formattingSchema.extend({
	action: z
		.enum(["find_empty_area", "check_overlap", "chain"])
		.describe(
			"Which layout action to run. 'find_empty_area' returns (x, y). 'check_overlap' checks whether an op overlaps siblings. 'chain' wires a list of ops in sequence with auto-layout.",
		),
	base: z
		.string()
		.optional()
		.default("/project1")
		.describe("Container op (find_empty_area)."),
	height: z.number().int().positive().optional().default(200),
	margin: z.number().int().nonnegative().optional().default(50),
	op: z.string().optional().describe("Op to overlap-check (check_overlap)."),
	ops: z
		.array(z.string())
		.optional()
		.describe("List of op paths to chain (chain)."),
	spacing: z.number().int().positive().optional().default(200),
	startX: z.number().int().optional().default(0),
	startY: z.number().int().optional().default(0),
	width: z.number().int().positive().optional().default(200),
});

const glslSchema = formattingSchema.extend({
	code: z
		.string()
		.optional()
		.describe(
			"If present, writes this code to the docked shader DAT. Omit for a read-only call.",
		),
	path: z.string().describe("GLSL TOP / MAT / POP path."),
	returnCompiled: z
		.boolean()
		.optional()
		.default(false)
		.describe(
			"When writing, include any compile errors reported by TD after re-cook.",
		),
	stage: z
		.enum(["pixel", "vertex", "compute"])
		.describe("Which shader stage to read or write."),
});

const scaffoldSchema = formattingSchema.extend({
	base: z
		.string()
		.optional()
		.default("/project1")
		.describe("Container op to scaffold inside."),
	name: z
		.string()
		.optional()
		.describe(
			"Optional prefix for created op names (defaults to the template name).",
		),
	template: z
		.enum([
			"render_pipeline",
			"feedback_loop",
			"instanced_particles",
			"audio_reactive",
			"projection_mapping",
		])
		.describe("Which scene template to scaffold."),
});

// -----------------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------------

function formatResult(
	data: unknown,
	responseFormat: "json" | "yaml" | "markdown" | undefined,
): string {
	if (responseFormat === "markdown") {
		return "```json\n" + JSON.stringify(data, null, 2) + "\n```";
	}
	// yaml output is not worth adding a new dep for Phase 3;
	// the upstream presenter will eventually handle it.
	return JSON.stringify(data, null, 2);
}

function toContent(text: string) {
	return {
		content: [{ text, type: "text" as const }],
	};
}

// -----------------------------------------------------------------------------
// Registration
// -----------------------------------------------------------------------------

export function registerForkTools(server: McpServer, logger: ILogger): void {
	const client = new ForkClient();

	// --- td_pane ----------------------------------------------------------
	server.tool(
		FORK_TOOL_NAMES.TD_PANE,
		"Return the current TouchDesigner network editor pane state (path, pan, zoom, viewport size).",
		paneSchema.strict().shape,
		async (params) => {
			try {
				const result = await client.getPane();
				if (!result.success) throw result.error;
				return toContent(formatResult(result.data, params?.responseFormat));
			} catch (error) {
				return handleToolError(error, logger, FORK_TOOL_NAMES.TD_PANE);
			}
		},
	);

	// --- td_selection -----------------------------------------------------
	server.tool(
		FORK_TOOL_NAMES.TD_SELECTION,
		"Return the operators currently selected in the active network editor pane.",
		selectionSchema.strict().shape,
		async (params) => {
			try {
				const result = await client.getSelection();
				if (!result.success) throw result.error;
				return toContent(formatResult(result.data, params?.responseFormat));
			} catch (error) {
				return handleToolError(error, logger, FORK_TOOL_NAMES.TD_SELECTION);
			}
		},
	);

	// --- td_cook ----------------------------------------------------------
	server.tool(
		FORK_TOOL_NAMES.TD_COOK,
		"Force-cook an operator (and optionally its descendants). Use this to fix nested baseCOMP staleness — operators inside a base/tox COMP that reference parameters indirectly do not always cook automatically.",
		cookSchema.strict().shape,
		async (params) => {
			try {
				const result = await client.forceCook({
					path: params.path,
					recurse: params.recurse,
				});
				if (!result.success) throw result.error;
				return toContent(formatResult(result.data, params.responseFormat));
			} catch (error) {
				return handleToolError(error, logger, FORK_TOOL_NAMES.TD_COOK);
			}
		},
	);

	// --- td_viewport ------------------------------------------------------
	server.tool(
		FORK_TOOL_NAMES.TD_VIEWPORT,
		"Capture a PNG/JPG of a TOP viewer, COMP viewer, or the current network editor pane so the agent can see the result of its edits.",
		viewportSchema.strict().shape,
		async (params) => {
			try {
				const result = await client.captureViewport({
					format: params.format,
					height: params.height,
					quality: params.quality,
					returnAs: params.returnAs,
					target: params.target,
					width: params.width,
				});
				if (!result.success) throw result.error;
				// For base64 encoded images, strip the payload from the
				// textual response to avoid blowing up context windows.
				// The caller should pass returnAs='path' for anything large.
				const data = result.data;
				const terse = {
					data:
						data.encoding === "base64"
							? `${data.data.slice(0, 80)}…[${data.sizeBytes}B]`
							: data.data,
					encoding: data.encoding,
					format: data.format,
					height: data.height,
					sizeBytes: data.sizeBytes,
					width: data.width,
				};
				return toContent(formatResult(terse, params.responseFormat));
			} catch (error) {
				return handleToolError(error, logger, FORK_TOOL_NAMES.TD_VIEWPORT);
			}
		},
	);

	// --- td_connect -------------------------------------------------------
	server.tool(
		FORK_TOOL_NAMES.TD_CONNECT,
		"Wire one operator's outlet to another operator's inlet. Validates family compatibility server-side before hitting TouchDesigner.",
		connectSchema.strict().shape,
		async (params) => {
			try {
				const result = await client.connect({
					from: params.from,
					fromOutlet: params.fromOutlet,
					to: params.to,
					toInlet: params.toInlet,
				});
				if (!result.success) throw result.error;
				return toContent(formatResult(result.data, params.responseFormat));
			} catch (error) {
				return handleToolError(error, logger, FORK_TOOL_NAMES.TD_CONNECT);
			}
		},
	);

	// --- td_layout --------------------------------------------------------
	server.tool(
		FORK_TOOL_NAMES.TD_LAYOUT,
		"Layout intelligence — find_empty_area, check_overlap, or chain operators with auto-placement. Delegates to op.TDAPI helpers inside TouchDesigner.",
		layoutSchema.strict().shape,
		async (params) => {
			try {
				if (params.action === "find_empty_area") {
					const r = await client.layoutFindEmptyArea({
						base: params.base,
						height: params.height,
						margin: params.margin,
						startX: params.startX,
						startY: params.startY,
						width: params.width,
					});
					if (!r.success) throw r.error;
					return toContent(formatResult(r.data, params.responseFormat));
				}
				if (params.action === "check_overlap") {
					if (!params.op) throw new Error("check_overlap requires 'op'");
					const r = await client.layoutCheckOverlap({ op: params.op });
					if (!r.success) throw r.error;
					return toContent(formatResult(r.data, params.responseFormat));
				}
				if (params.action === "chain") {
					if (!params.ops || params.ops.length === 0)
						throw new Error("chain requires a non-empty 'ops' list");
					const r = await client.layoutChain({
						ops: params.ops,
						spacing: params.spacing,
					});
					if (!r.success) throw r.error;
					return toContent(formatResult(r.data, params.responseFormat));
				}
				throw new Error(`Unknown layout action: ${params.action}`);
			} catch (error) {
				return handleToolError(error, logger, FORK_TOOL_NAMES.TD_LAYOUT);
			}
		},
	);

	// --- td_glsl ----------------------------------------------------------
	server.tool(
		FORK_TOOL_NAMES.TD_GLSL,
		"Read or write a GLSL shader stage (pixel / vertex / compute) on a GLSL TOP/MAT/POP. Respects docked _pixel_shader / _vertex_shader DATs rather than orphaning them.",
		glslSchema.strict().shape,
		async (params) => {
			try {
				const result = params.code
					? await client.glslWrite({
							code: params.code,
							path: params.path,
							returnCompiled: params.returnCompiled,
							stage: params.stage,
						})
					: await client.glslRead({
							path: params.path,
							stage: params.stage,
						});
				if (!result.success) throw result.error;
				return toContent(formatResult(result.data, params.responseFormat));
			} catch (error) {
				return handleToolError(error, logger, FORK_TOOL_NAMES.TD_GLSL);
			}
		},
	);

	// --- td_scaffold ------------------------------------------------------
	server.tool(
		FORK_TOOL_NAMES.TD_SCAFFOLD,
		"Scaffold a complete scene template — render_pipeline / feedback_loop / instanced_particles / audio_reactive / projection_mapping — as a working set of connected nodes.",
		scaffoldSchema.strict().shape,
		async (params) => {
			try {
				const result = await client.scaffold({
					base: params.base,
					name: params.name,
					template: params.template,
				});
				if (!result.success) throw result.error;
				return toContent(formatResult(result.data, params.responseFormat));
			} catch (error) {
				return handleToolError(error, logger, FORK_TOOL_NAMES.TD_SCAFFOLD);
			}
		},
	);
}
