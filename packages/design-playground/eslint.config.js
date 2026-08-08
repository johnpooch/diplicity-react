import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";

const OUTSIDE_PACKAGE =
  "The design playground must not import from the main web app. Duplicate what you need into packages/design-playground instead. See packages/design-playground/CLAUDE.md.";

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
            { group: ["**/packages/web/**"], message: OUTSIDE_PACKAGE },
            { group: ["**/web/src/**"], message: OUTSIDE_PACKAGE },
            { group: ["../../web/**", "../../../**"], message: OUTSIDE_PACKAGE },
            { group: ["**/api/generated/**"], message: OUTSIDE_PACKAGE },
          ],
        },
      ],
    },
  }
);
