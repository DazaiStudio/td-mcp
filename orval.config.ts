import { defineConfig } from "orval";

export default defineConfig({
	api: {
		input: {
			target: "./src/api/index.yml",
		},
		output: {
			baseUrl: {
				getBaseUrlFromSpecification: true,
			},
			biome: false,
			clean: true,
			mock: false,
			mode: "single",
			namingConvention: "PascalCase",
			override: {
				mutator: {
					extension: ".js",
					name: "customInstance",
					path: "./src/api/customInstance.ts",
				},
			},
			target: "src/gen/endpoints",
		},
	},
	mcpZod: {
		input: {
			target: "./src/api/index.yml",
		},
		output: {
			biome: false,
			clean: true,
			client: "zod",
			fileExtension: ".zod.ts",
			mode: "single",
			namingConvention: "camelCase",
			target: "src/gen/mcp",
		},
	},
});
