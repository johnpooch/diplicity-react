---
paths:
  - "service/**/serializers.py"
  - "service/**/views.py"
  - "service/**/urls.py"
  - "service/openapi-schema*.yaml"
  - "packages/web/src/api/generated/**"
---

# Codegen reproducibility

`docker compose up codegen` runs `manage.py spectacular` + `orval`. To reproduce committed output byte-for-byte, the generating environment must match production config:

- `DJANGO_DEBUG` must be **off**, otherwise `/api/test-sentry/` is added
- `FIREBASE_PROJECT_ID` must be **set**, otherwise `/devices/` and `FCMDevice` are removed

In a cloud session (no Firebase, DEBUG off), a clean `git diff` shows only the `/devices/` + `FCMDevice` removal — that is environmental, not a stale-checkout signal. Do not commit that removal: satisfy the `_FIREBASE_PROJECT_ID` guard first with a throwaway service account (any `FIREBASE_PROJECT_ID` plus a locally generated RSA key in `FIREBASE_PRIVATE_KEY`), which `credentials.Certificate` accepts without contacting Google, and the generated schema then matches production.

After codegen, always run `npx tsc -b --noEmit` in `packages/web`. When codegen adds required fields to an existing type, grep `packages/web/src/` for inline objects of that type — especially in `src/mocks/` and test files — and add the new fields.

Serializer class names become OpenAPI component names, which become type names in `endpoints.ts` and `harness/generated/api.py`. Renaming a serializer is a codegen change — rerun codegen and `npx tsc -b --noEmit` in the same commit. Renaming a URL path or `name=` is a wire change and breaks shipped mobile builds; treat it separately.
