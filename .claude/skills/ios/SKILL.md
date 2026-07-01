---
name: ios
description: iOS Capacitor guidance for diplicity-react — build workflow, Xcode project setup, APNs and ASC credentials, code signing strategy, Fastlane releases, and GitHub Actions. Use when building, deploying, or debugging the iOS app, or managing iOS credentials.
allowed-tools: Bash, Read, Glob, Grep
---

# iOS Development (Capacitor)

## Target Device

**Always use the physical iPhone — do not use simulators** (too much RAM).

The XcodeBuildMCP session defaults target the real device (profile: `real-device`, persisted in `.xcodebuildmcp/config.yaml`).

- **Bundle ID**: `com.diplicity.app`
- **Xcode Project**: `packages/web/ios/App/App.xcodeproj` (no `.xcworkspace`)
- **Scheme**: `App`
- **Team ID**: `G76UP8FNMS` (also in `.env` as `CAPACITOR_IOS_TEAM_ID`)

## MCP Tools

- **XcodeBuildMCP**: only simulator tools enabled by default. Device workflows require explicit configuration — until enabled, use `xcodebuild` CLI directly.
- **mobile-mcp**: use for UI interaction (screenshots, taps, swipes, text input) on the real device.

## Build & Deploy

**`npx cap sync` must run from `packages/web/`** — `capacitor.config.ts` is there.

```bash
cd packages/web
npm run build
npx cap sync ios

# Build for device via CLI (when XcodeBuildMCP device tools are unavailable)
xcodebuild -project ios/App/App.xcodeproj -scheme App \
  -destination 'id=<DEVICE_UDID>' \
  -allowProvisioningUpdates \
  DEVELOPMENT_TEAM=G76UP8FNMS CODE_SIGN_STYLE=Automatic \
  build
```

## Credentials

Gitignored files in repo root:
- `AuthKey_C6JM6K4J2X.p8` — APNs authentication key (Key ID: `C6JM6K4J2X`). Used by Firebase for iOS push notifications. Independent of distribution certificates — does not need rotation when certs change.
- `AuthKey_WVUV6626PT.p8` — App Store Connect API key (Key ID: `WVUV6626PT`, Issuer ID: `988659a4-ba96-4fb1-8ad7-bccc72aa219f`). Used by Fastlane for TestFlight uploads. Key ID and issuer ID also in `.env` as `ASC_KEY_ID` and `ASC_ISSUER_ID`.

Code signing uses **Xcode automatic signing** — Xcode manages provisioning profiles automatically. No manual `.mobileprovision` file needed.

Signing certificates in local macOS Keychain:
- Apple Development: John McDowell (`P96LAJ7FF8`) — device builds
- Apple Distribution: John McDowell (`G76UP8FNMS`) — App Store distribution (created Feb 2026, expires Feb 2027)

## Fastlane

Run from `packages/web/`:
```bash
# Full release to TestFlight
npm run build && npx cap sync ios && bundle exec fastlane ios release

# PR validation build
PR_NUMBER=42 PR_TITLE="My feature" bundle exec fastlane ios pr_build
```

Requires `ASC_KEY_ID` and `ASC_ISSUER_ID` in `.env`, and the `.p8` key file in the repo root.

### Signing strategy

- **Local dev**: Xcode automatic signing (`CODE_SIGN_STYLE=Automatic`)
- **CI / Fastlane**: manual signing via `match` + `update_code_signing_settings` (App target only — not global like `xcargs`)
- **Certificates**: stored in private Git repo (`ios-certificates`), managed by `match`

On local runs, signing is automatically restored to Automatic after the build via an `ensure` block.

### Version management

- `MARKETING_VERSION`: from `packages/web/package.json` `version` field
- `CURRENT_PROJECT_VERSION`: Unix timestamp, auto-generated per build
- Both passed via `xcargs` — no `agvtool` or project file edits needed

### GitHub Actions workflows

- **`ios-release.yml`**: triggers on push to `main` when `packages/web/**` changes — builds web, syncs Capacitor, runs `fastlane ios release` to upload to TestFlight
- **`ios-pr-build.yml`**: manual `workflow_dispatch` with `pr_number` input — checks out PR branch, builds, uploads to TestFlight, comments on the PR

### Required GitHub Secrets (iOS)

| Secret | Description |
|---|---|
| `ASC_KEY_ID` | App Store Connect API key ID (`WVUV6626PT`) |
| `ASC_ISSUER_ID` | App Store Connect issuer ID |
| `ASC_KEY_CONTENT` | Base64-encoded `.p8` key file content |
| `MATCH_GIT_URL` | URL to the `ios-certificates` Git repo |
| `MATCH_PASSWORD` | Encryption password for match certificates |
| `MATCH_GIT_BASIC_AUTHORIZATION` | Base64-encoded `user:token` for HTTPS Git auth |
| `VITE_GOOGLE_IOS_CLIENT_ID` | Google OAuth iOS client ID |
