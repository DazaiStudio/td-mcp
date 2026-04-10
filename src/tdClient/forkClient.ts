/**
 * forkClient — axios wrapper for the td-mcp fork's /fork/* HTTP endpoints.
 *
 * The upstream TouchDesignerClient only knows about the OpenAPI-generated
 * endpoints under /api/*. Fork endpoints live under /fork/* and are
 * handled by `td/modules/mcp/controllers/fork_controller.py`. This module
 * provides a thin typed wrapper that the fork's MCP tool handlers call.
 *
 * The base URL is derived from the same TD_WEB_SERVER_HOST / TD_WEB_SERVER_PORT
 * environment variables the upstream client uses, so `cli.ts` continues to
 * own transport configuration.
 */

import axios, { type AxiosInstance, type AxiosRequestConfig } from "axios";

export type ForkPaneState = {
	path: string;
	tx: number;
	ty: number;
	zoom: number;
	viewportSize: [number, number];
} | null;

export type ForkSelectionOp = {
	path: string;
	name: string;
	type: string;
	opType: string;
	family: string;
	x: number;
	y: number;
};

export type ForkSelection = {
	count: number;
	ops: ForkSelectionOp[];
};

export type ForkCookResult = {
	cooked: number;
	totalCookTimeMs: number;
	errors: Array<{ path: string; msg: string }>;
};

export type ForkViewportResult = {
	format: "png" | "jpg";
	width: number;
	height: number;
	encoding: "base64" | "file";
	data: string;
	sizeBytes: number;
};

export type ForkConnectResult = {
	ok: true;
	from: string;
	to: string;
	fromOutlet: number;
	toInlet: number;
};

export type ForkLayoutXY = { x: number; y: number };
export type ForkLayoutOverlap = { overlaps: boolean };
export type ForkLayoutChain = { chained: string[]; spacing: number };

export type ForkGlslResult = {
	stage: "pixel" | "vertex" | "compute";
	docked_dat_path: string;
	code: string;
	errors: Array<{ line: number; msg: string }> | null;
};

export type ForkScaffoldResult = {
	template: string;
	createdOps: string[];
	wiring: Array<{ from: string; to: string }>;
	entryPoint: string;
	description: string;
};

type ForkEnvelope<T> =
	| { success: true; data: T }
	| { success: false; error: string };

export type ForkResult<T> =
	| { success: true; data: T }
	| { success: false; error: Error };

/**
 * Thin axios wrapper for /fork/* routes.
 *
 * Uses the same TD_WEB_SERVER_HOST/PORT env vars as the upstream generated
 * client, so no additional configuration is needed.
 */
export class ForkClient {
	private readonly http: AxiosInstance;

	constructor() {
		const host = process.env.TD_WEB_SERVER_HOST || "http://127.0.0.1";
		const port = process.env.TD_WEB_SERVER_PORT || "9981";
		const baseURL = `${host}:${port}`;
		this.http = axios.create({
			baseURL,
			headers: { "Content-Type": "application/json" },
			timeout: 30_000,
		});
	}

	private async call<T>(
		method: "get" | "post",
		path: string,
		body?: unknown,
		config?: AxiosRequestConfig,
	): Promise<ForkResult<T>> {
		try {
			const response =
				method === "get"
					? await this.http.get<ForkEnvelope<T>>(path, config)
					: await this.http.post<ForkEnvelope<T>>(path, body, config);
			const envelope = response.data;
			if (envelope?.success) {
				return { data: envelope.data, success: true };
			}
			const msg =
				envelope && !envelope.success ? envelope.error : "unknown fork error";
			return { error: new Error(msg), success: false };
		} catch (err) {
			const msg = err instanceof Error ? err.message : String(err);
			return { error: new Error(`fork call failed: ${msg}`), success: false };
		}
	}

	// --- editor context -----------------------------------------------------

	getPane(): Promise<ForkResult<ForkPaneState>> {
		return this.call<ForkPaneState>("get", "/fork/editor/pane");
	}

	getSelection(): Promise<ForkResult<ForkSelection>> {
		return this.call<ForkSelection>("get", "/fork/editor/selection");
	}

	// --- cook control -------------------------------------------------------

	forceCook(params: {
		path: string;
		recurse?: boolean;
	}): Promise<ForkResult<ForkCookResult>> {
		return this.call<ForkCookResult>("post", "/fork/cook", params);
	}

	// --- viewport capture ---------------------------------------------------

	captureViewport(params: {
		target: string;
		width?: number;
		height?: number;
		format?: "png" | "jpg";
		quality?: number;
		returnAs?: "base64" | "path";
	}): Promise<ForkResult<ForkViewportResult>> {
		return this.call<ForkViewportResult>("post", "/fork/viewport", params);
	}

	// --- wiring + layout ----------------------------------------------------

	connect(params: {
		from: string;
		to: string;
		fromOutlet?: number;
		toInlet?: number;
	}): Promise<ForkResult<ForkConnectResult>> {
		return this.call<ForkConnectResult>("post", "/fork/connect", params);
	}

	layoutFindEmptyArea(params: {
		base?: string;
		width?: number;
		height?: number;
		startX?: number;
		startY?: number;
		margin?: number;
	}): Promise<ForkResult<ForkLayoutXY>> {
		return this.call<ForkLayoutXY>("post", "/fork/layout/find_empty", params);
	}

	layoutCheckOverlap(params: {
		op: string;
	}): Promise<ForkResult<ForkLayoutOverlap>> {
		return this.call<ForkLayoutOverlap>("post", "/fork/layout/overlap", params);
	}

	layoutChain(params: {
		ops: string[];
		spacing?: number;
	}): Promise<ForkResult<ForkLayoutChain>> {
		return this.call<ForkLayoutChain>("post", "/fork/layout/chain", params);
	}

	// --- GLSL authoring -----------------------------------------------------

	glslRead(params: {
		path: string;
		stage: "pixel" | "vertex" | "compute";
	}): Promise<ForkResult<ForkGlslResult>> {
		return this.call<ForkGlslResult>("post", "/fork/glsl/read", params);
	}

	glslWrite(params: {
		path: string;
		stage: "pixel" | "vertex" | "compute";
		code: string;
		returnCompiled?: boolean;
	}): Promise<ForkResult<ForkGlslResult>> {
		return this.call<ForkGlslResult>("post", "/fork/glsl/write", params);
	}

	// --- scene scaffolding --------------------------------------------------

	scaffold(params: {
		template:
			| "render_pipeline"
			| "feedback_loop"
			| "instanced_particles"
			| "audio_reactive"
			| "projection_mapping";
		base?: string;
		name?: string;
	}): Promise<ForkResult<ForkScaffoldResult>> {
		return this.call<ForkScaffoldResult>("post", "/fork/scaffold", params);
	}
}
