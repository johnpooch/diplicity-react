---
paths:
  - "packages/web/capacitor.config.ts"
  - ".github/workflows/ios-release.yml"
  - ".github/workflows/ios-pr-build.yml"
  - ".github/workflows/android-release.yml"
  - ".github/workflows/bundle-release.yml"
  - "packages/web/index.html"
  - "packages/web/src/components/UpdateGate.tsx"
---

# OTA updates in the app

`@capgo/capacitor-updater` is configured under `plugins.CapacitorUpdater` in
`packages/web/capacitor.config.ts` and talks to the endpoint in `service/update/`.

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

## A bundle can start without the splash screen

With `autoUpdate: "atBackground"` the plugin applies a bundle by reloading the WebView while the app is
backgrounded, so the new page boots with no splash in front of it and with its first requests issued
as iOS suspends the app. Anything that holds up the first render shows as a blank screen. Hence:

- `index.html` puts no render-blocking resource from a third-party origin ahead of the app. Fonts are
  self-hosted through `@fontsource`; a stylesheet from a CDN stalls the whole page if it hangs.
- `UpdateGate` bounds its checks with a timeout and fails open, and it is what hides the splash screen,
  once it has settled. Do not hide the splash on `App` mount: that uncovers a page the gate is still
  holding blank.

## Native builds report to Sentry

Every workflow that builds the web app for a store release or an OTA bundle passes `VITE_SENTRY_DSN`;
without it `src/sentry.ts` skips initialisation and native failures are invisible.
`src/utils/otaBundle.ts` tags events with the running bundle version (every bundle shares the store
build's `__APP_VERSION__`) and reports a bundle the plugin rolled back.
