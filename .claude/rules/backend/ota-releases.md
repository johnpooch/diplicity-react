---
paths:
  - "service/update/**/*.py"
  - ".github/workflows/bundle-release.yml"
---

# OTA bundle releases

Publishing an over-the-air web bundle is **both** a management command and a workflow, split at
the seam where the work changes machine:

- `release_bundle` (`service/update/management/commands/release_bundle.py`) owns everything the
  service knows about — zipping a built `dist`, hashing the zip, uploading it to R2, writing the
  `Bundle` rows. It never builds the web app; it takes an already-built directory via `--dist`.
- `.github/workflows/bundle-release.yml` owns everything the service does not — installing Node,
  building `packages/web`, then invoking the command once.

Put new release logic in the command, not the workflow. The workflow exists to hand the command a
`dist` directory and credentials; a step that makes a decision about what gets published belongs in
Python where it can be tested.

## The minimum native version is always stated, never inferred

`--minimum-native-version` is required on the command and a required `workflow_dispatch` input.
Do not give it a default and do not derive it from `package.json`. Serving a bundle that calls
native APIs the installed binary lacks is the failure this whole design exists to prevent, and a
default is how that failure happens quietly.

`--bundle-version` is required for the same reason — the version orders bundles for every installed
client. It is `--bundle-version`, not `--version`, because Django's `BaseCommand` already owns
`--version`.

## One zip, one object per platform

The zip is built once and uploaded under `bundles/<platform>/<version>.zip` for each requested
platform, so every `Bundle` row owns its object outright. iOS and Android get byte-identical
archives today; keeping the objects separate means deactivating or replacing one platform's bundle
can never disturb the other.

The build is shared, so the workflow passes every `VITE_*` variable either store release needs —
including `VITE_GOOGLE_IOS_CLIENT_ID`, which `android-release.yml` omits. An OTA bundle missing it
would break Google sign-in on iOS.

## The workflow reaches the database over the public URL

Railway's `DATABASE_URL` is an internal hostname that does not resolve from a GitHub runner. The
publish step therefore sets `DATABASE_CONNECTION_STRING` from the `DATABASE_PUBLIC_URL` secret,
which `service/project/settings.py` checks ahead of `DATABASE_URL`. `railway run` supplies the R2
credentials from the service's own variables. Both are needed; the step fails fast if the secret is
missing rather than letting Django parse an empty connection string.
