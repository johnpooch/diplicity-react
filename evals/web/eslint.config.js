import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";

const OUTSIDE_EVALS =
  "The evals frontend must not import from packages/. Copy what you need into evals/web instead. See evals/CLAUDE.md.";

export default tseslint.config(
  { ignores: ["dist", "node_modules"] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": "off",
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            { group: ["**/packages/**"], message: OUTSIDE_EVALS },
            { group: ["**/web/src/**", "**/design-playground/**"], message: OUTSIDE_EVALS },
            { group: ["../../../**"], message: OUTSIDE_EVALS },
            { group: ["**/api/generated/**"], message: OUTSIDE_EVALS },
          ],
        },
      ],
    },
  }
);
