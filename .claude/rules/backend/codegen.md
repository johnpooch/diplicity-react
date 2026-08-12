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

In a cloud session (no Firebase, DEBUG off), a clean `git diff` shows only the `/devices/` + `FCMDevice` removal — that is environmental, not a stale-checkout signal.

After codegen, always run `npx tsc -b --noEmit` in `packages/web`. When codegen adds required fields to an existing type, grep `packages/web/src/` for inline objects of that type — especially in `src/mocks/` and test files — and add the new fields.
