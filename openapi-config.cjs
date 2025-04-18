const config = {
  schemaFile: "../diplicity-django/diplicity/openapi-schema.yaml",
  apiFile: "./src/store/api.ts",
  apiImport: "api",
  outputFile: "./src/store/service.ts",
  exportName: "service",
  hooks: true,
};

module.exports = config;
