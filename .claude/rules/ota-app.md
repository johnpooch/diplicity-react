---
paths:
  - "packages/web/capacitor.config.ts"
  - ".github/workflows/ios-release.yml"
  - ".github/workflows/ios-pr-build.yml"
  - ".github/workflows/android-release.yml"
---

# OTA updates in the app

`@capgo/capacitor-updater` is configured under `plugins.CapacitorUpdater` in
`packages/web/capacitor.config.ts` and talks to the endpoint in `service/update/`. The service side
is covered by `.claude/rules/backend/ota-releases.md`.

## The update URL is resolved at sync time, not build time

`capacitor.config.ts` is evaluated by `npx cap sync`, not by Vite, so `import.meta.env` is unavailable
and a `VITE_*` value set only on the build step never reaches the config. Every workflow that runs
`cap sync` passes `VITE_DIPLICITY_API_BASE_URL` on the sync step as well as the build step;
`packages/web/scripts/release-android.sh` gets there instead by sourcing `.env.release` under
`set -a`. Add both whenever a new sync site appears — a missing variable does not fail the build, it
ships a binary that checks for updates at the fallback URL and never finds any.

The fallback is `http://localhost:8000`, matching `src/api/axiosInstance.ts`. Keep it a URL that
cannot reach production: a developer's `cap sync` pointing at the production endpoint would pull a
production bundle over the local build's assets.

## `statsUrl` and `channelUrl` must stay set

Both default to Capgo's own servers. Empty strings disable them and keep every request on our
endpoint. Deleting either key reintroduces the third-party dependency the self-hosted design exists
to avoid; neither is a redundant line.

## `notifyAppReady()` is what stops a rollback

The plugin rolls back to the previous bundle unless `notifyAppReady()` is called within
`appReadyTimeout` (10s by default). `src/App.tsx` calls it from a native-guarded mount effect, so a
bundle that crashes *before* `App` mounts rolls back and one that crashes after it does not. Moving
the call later — after auth, or after a first screen renders — widens the net but puts more work
inside the timeout. If you move it, re-verify the rollback on a device: it is the only safety net
between a bad bundle and every installed app.
