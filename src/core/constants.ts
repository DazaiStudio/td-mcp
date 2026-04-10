/**
 * Reference URLs for TouchDesigner Python documentation
 */
export const TD_PYTHON_CLASS_REFERENCE_BASE_URL = "https://docs.derivative.ca";
export const TD_PYTHON_CLASS_REFERENCE_INDEX_URL = `${TD_PYTHON_CLASS_REFERENCE_BASE_URL}/Python_Classes_and_Modules`;

/**
 * Reference Tool Names for TouchDesigner MCP
 *
 * The first block is inherited from upstream (8beeeaaat/touchdesigner-mcp).
 * The second block is fork-specific and lives in src/features/tools/handlers/forkTools.ts.
 */
export const TOOL_NAMES = {
	// ---- upstream tools ----
	CREATE_TD_NODE: "create_td_node",
	DELETE_TD_NODE: "delete_td_node",
	DESCRIBE_TD_TOOLS: "describe_td_tools",
	EXECUTE_NODE_METHOD: "exec_node_method",
	EXECUTE_PYTHON_SCRIPT: "execute_python_script",
	GET_TD_CLASS_DETAILS: "get_td_class_details",
	GET_TD_CLASSES: "get_td_classes",
	GET_TD_INFO: "get_td_info",
	GET_TD_MODULE_HELP: "get_td_module_help",
	GET_TD_NODE_ERRORS: "get_td_node_errors",
	GET_TD_NODE_PARAMETERS: "get_td_node_parameters",
	GET_TD_NODES: "get_td_nodes",
	UPDATE_TD_NODE_PARAMETERS: "update_td_node_parameters",

	// ---- td-mcp fork tools (Phase 3.2 – 3.7) ----
	TD_PANE: "td_pane",
	TD_SELECTION: "td_selection",
	TD_COOK: "td_cook",
	TD_VIEWPORT: "td_viewport",
	TD_CONNECT: "td_connect",
	TD_LAYOUT: "td_layout",
	TD_GLSL: "td_glsl",
	TD_SCAFFOLD: "td_scaffold",
} as const;

/**
 * Subset of TOOL_NAMES that are fork-specific. Used by forkTools.ts to
 * group its registrations and by the tests to assert which tools belong
 * to the fork vs. upstream surface.
 */
export const FORK_TOOL_NAMES = {
	TD_PANE: TOOL_NAMES.TD_PANE,
	TD_SELECTION: TOOL_NAMES.TD_SELECTION,
	TD_COOK: TOOL_NAMES.TD_COOK,
	TD_VIEWPORT: TOOL_NAMES.TD_VIEWPORT,
	TD_CONNECT: TOOL_NAMES.TD_CONNECT,
	TD_LAYOUT: TOOL_NAMES.TD_LAYOUT,
	TD_GLSL: TOOL_NAMES.TD_GLSL,
	TD_SCAFFOLD: TOOL_NAMES.TD_SCAFFOLD,
} as const;

export const REFERENCE_COMMENT = `Check reference resources: ${TD_PYTHON_CLASS_REFERENCE_INDEX_URL}`;

export const PROMPT_NAMES = {
	CHECK_NODE_ERRORS: "Check node errors",
	NODE_CONNECTION: "Node connection",
	SEARCH_NODE: "Search node",
} as const;
