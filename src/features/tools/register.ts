import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { ILogger } from "../../core/logger.js";
import type { TouchDesignerClient } from "../../tdClient/index.js";
import { registerForkTools } from "./handlers/forkTools.js";
import { registerTdTools } from "./handlers/tdTools.js";

/**
 * Register resource handlers with MCP server.
 *
 * Upstream tools are registered first, then fork tools (td_pane,
 * td_selection, td_cook, td_viewport, td_connect, td_layout, td_glsl,
 * td_scaffold). Fork tools talk to their own /fork/* endpoints via
 * ForkClient and are independent of the generated TouchDesignerClient.
 */
export function registerTools(
	server: McpServer,
	logger: ILogger,
	tdClient: TouchDesignerClient,
): void {
	registerTdTools(server, logger, tdClient);
	registerForkTools(server, logger);
}
