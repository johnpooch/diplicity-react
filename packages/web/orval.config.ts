import { defineConfig } from "orval";
import { faker } from "@faker-js/faker";

export default defineConfig({
  diplicity: {
    input: "../../service/openapi-schema.yaml",
    output: {
      mode: "single",
      target: "./src/api/generated/endpoints.ts",
      client: "react-query",
      override: {
        query: {
          useSuspenseQuery: true,
        },
        mutator: {
          path: "./src/api/axiosInstance.ts",
          name: "customInstance",
        },
      },
      mock: {
        type: "msw",
        delay: 80,
      },
    },
    hooks: {
      afterAllFilesWrite: "prettier --write",
    },
  },
});
