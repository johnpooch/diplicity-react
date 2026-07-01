---
name: android
description: Android Capacitor guidance for diplicity-react — build workflow, ADB setup, Firebase Cloud Messaging, Google Sign-In, keystore management, SHA-1 fingerprints, and Fastlane releases. Use when building, deploying, or debugging the Android app, or managing Android credentials.
allowed-tools: Bash, Read, Glob, Grep
---

# Android Development (Capacitor)

## Target Device

**Always use the physical Pixel 8a — do not use the emulator** (too much RAM).

- **Application ID**: `com.diplicityreact.app`
- **Android Project**: `packages/web/android/`
- **Connected device UDID**: `46101JEKB13333`

## Prerequisites

- **JDK 21**: `sudo apt install openjdk-21-jdk` (Java 17 is not sufficient for Capacitor Android 8)
- **Android Studio**: `sudo snap install android-studio --classic` (includes SDK, build-tools, ADB)
- **`ANDROID_HOME`**: add to `~/.bashrc`:
  ```bash
  export ANDROID_HOME="$HOME/Android/Sdk"
  export PATH="$ANDROID_HOME/platform-tools:$PATH"
  ```

## ADB Device Setup (Linux)

```bash
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="18d1", MODE="0664", GROUP="plugdev"' | sudo tee /etc/udev/rules.d/51-android.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
sudo usermod -aG plugdev $USER
# Log out and back in, then unplug/replug device
adb kill-server && adb devices
# Accept "Allow USB debugging" on the phone
```

## Build & Deploy

**All Capacitor commands must run from `packages/web/`** — `capacitor.config.ts` is there.

```bash
cd packages/web
npm run build
ANDROID_HOME=$HOME/Android/Sdk npx cap sync android
ANDROID_HOME=$HOME/Android/Sdk npx cap run android --target 46101JEKB13333
```

**Version management**: `versionName` comes from `package.json` `version` field; `versionCode` is a Unix timestamp auto-generated per build. Both set in `android/app/build.gradle` — no manual editing needed.

## Firebase Cloud Messaging

Uses `@capacitor-firebase/messaging`. Requires `google-services.json` at `packages/web/android/app/google-services.json` (gitignored).

Setup: Firebase console → project `diplicity-react` → Project settings → Add app → Android → package name `com.diplicityreact.app` → download `google-services.json`.

`android/app/build.gradle` conditionally applies `com.google.gms.google-services` when the file exists. Runtime `POST_NOTIFICATIONS` permission (Android 13+) is handled by `FirebaseMessaging.requestPermissions()` in `messaging-native.ts`.

## Google Sign-In

Uses `VITE_GOOGLE_CLIENT_ID` (web client ID) as `webClientId` in `SocialLogin.initialize()`. No separate Android client ID needed in app code.

An **Android OAuth client must be registered in Google Cloud Console** (Credentials page, same project as web client) with package name `com.diplicityreact.app` and the appropriate SHA-1 fingerprint.

### SHA-1 Fingerprints

| Keystore | SHA-1 | Purpose |
|---|---|---|
| `~/.android/debug.keystore` (`androiddebugkey`) | `6F:9D:E2:20:2F:35:17:10:8C:41:28:B2:61:F5:4F:DE:7F:B1:0E:38` | Local dev / debug builds |
| `diplicity-android-upload.keystore` (`upload`) | `6A:39:8D:D3:B4:43:12:22:0C:4C:FA:08:93:B7:AD:19:58:D2:E0:0E` | Release builds |
| Play App Signing certificate | `17:CF:46:81:F1:B2:95:8E:16:25:4A:9E:3E:85:F9:84:17:42:AD:58` | Play Store / CI |

```bash
# Re-extract debug SHA-1
keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android
```

## Upload Keystore

| Item | Value |
|---|---|
| File | `diplicity-android-upload.keystore` (repo root, gitignored) |
| Alias | `upload` |
| Validity | 10,000 days (expires 2053-10-11) |
| Password | See password manager: "diplicity-android-upload.keystore" |

Required env vars for release builds:
```bash
ANDROID_KEYSTORE_PATH=/path/to/diplicity-android-upload.keystore
ANDROID_KEYSTORE_PASSWORD=<password>
ANDROID_KEY_ALIAS=upload
ANDROID_KEY_PASSWORD=<password>
```

Local release build:
```bash
cd packages/web/android
ANDROID_HOME=$HOME/Android/Sdk \
  ANDROID_KEYSTORE_PATH="$(git rev-parse --show-toplevel)/diplicity-android-upload.keystore" \
  ANDROID_KEYSTORE_PASSWORD="..." \
  ANDROID_KEY_ALIAS="upload" \
  ANDROID_KEY_PASSWORD="..." \
  ./gradlew bundleRelease
```

If the keystore is lost, generate a new one and submit via "Upload new key" in Play Console App Signing settings — Google holds the actual distribution signing key.

## Fastlane

Run from `packages/web/`:
```bash
# Full release to Play Console internal track
VITE_DIPLICITY_API_BASE_URL=https://diplicity-react-production.up.railway.app \
  npm run build && npx cap sync android && bundle exec fastlane android release

# PR build
PR_NUMBER=42 PR_TITLE="My feature" bundle exec fastlane android pr_build
```

Required env vars: `ANDROID_KEYSTORE_PATH`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`, `PLAY_SERVICE_ACCOUNT_JSON` (optional — upload skipped if unset).

### GitHub Actions

- **`android-release.yml`** (or similar): triggers on push to `main` when `packages/web/**` changes
- Required GitHub secrets: `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`, `PLAY_SERVICE_ACCOUNT_JSON`

## Gitignored Credential Files

| File | Purpose |
|---|---|
| `diplicity-android-upload.keystore` | Android upload keystore |
| `packages/web/android/app/google-services.json` | Firebase Android config |
