import { defineConfig } from "orval";

export default defineConfig({
  diplicity: {
    input: "../../service/openapi-schema.yaml",
    output: {
      mode: "single",
      target: "./src/api/generated/endpoints.ts",
      client: "react-query",
      httpClient: "axios",
      mock: true,
      override: {
        query: {
          useSuspenseQuery: true,
        },
        mutator: {
          path: "./src/api/axiosInstance.ts",
          name: "customInstance",
        },
      },
    },
    hooks: {
      afterAllFilesWrite: "prettier --write",
    },
  },
});
