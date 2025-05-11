const config = {
  schemaFile: "./service/openapi-schema.yaml",
  apiFile: "./packages/web/src/store/api.ts",
  apiImport: "api",
  outputFile: "./packages/web/src/store/service.ts",
  exportName: "service",
  hooks: true,
};

module.exports = config;
