# Android Development Learnings

Working notes for the Android app implementation (#298 and sub-issues). Used to resume context across sessions.

---

## Environment Setup (completed)

- **JDK**: Must be **JDK 21** — Capacitor Android 8 requires Java 21. JDK 17 fails with `invalid source release: 21` during Gradle compile.
- **Android Studio**: Installed via `sudo snap install android-studio --classic`. Run once to complete SDK wizard (downloads SDK, build-tools, platform-tools).
- **ADB on Linux (Pixel 8a)**: Required a udev rule with vendor ID `18d1` (Google/Pixel). Wildcard vendor rules (`*`) don't work. Exact rule:
  ```
  SUBSYSTEM=="usb", ATTR{idVendor}=="18d1", MODE="0664", GROUP="plugdev"
  ```
  File: `/etc/udev/rules.d/51-android.rules`. After adding: `sudo udevadm control --reload-rules && sudo udevadm trigger`, then `adb kill-server` and unplug/replug device.
- **PATH**: `ANDROID_HOME` and platform-tools added to `~/.bashrc`.
- **Device**: Pixel 8a, UDID `46101JEKB13333`, USB debugging enabled.

---

## Issue #299 — Scaffold (completed)

### What was done
- `npm install @capacitor/android@^8.3.4`
- `ANDROID_HOME=$HOME/Android/Sdk npx cap add android`
- `applicationId` set to `com.diplicityreact.app` in `android/app/build.gradle` (canonical Android package name; `capacitor.config.ts` retains `com.diplicity.app` for iOS)
- `versionName` wired from `package.json`, `versionCode` from Unix timestamp in `android/app/build.gradle`
- `android: { webContentsDebuggingEnabled: true }` added to `capacitor.config.ts`
- Permissions added to `AndroidManifest.xml`: `ACCESS_NETWORK_STATE`, `POST_NOTIFICATIONS`
- All 4 Capacitor plugins confirmed Android-compatible: `@capacitor-firebase/messaging`, `@capacitor/app`, `@capacitor/splash-screen`, `@capgo/capacitor-social-login`
- Adaptive icon already scaffolded by Capacitor (`mipmap-anydpi-v26/ic_launcher.xml`)

### Key learnings
- `versionCode = file('../../package.json')` resolves relative to **root Gradle project dir** (`android/`), not the subproject dir (`android/app/`). Use `new File(rootProject.projectDir, '../package.json')` instead.
- `versionCode (expression)` is ambiguous Groovy syntax — use `versionCode = (int)(...)` with explicit `=` and cast.
- The root `.env` has no `version` field; `packages/web/package.json` is the correct source.
- `npx cap sync` and `npx cap run` must be run from `packages/web/`, not repo root.
- Build command: `ANDROID_HOME=$HOME/Android/Sdk npx cap run android --target 46101JEKB13333`

---

## Issue #301 — Google Sign-In / Apple hidden (completed ✅)

### What was done
- `isIosPlatform()` added to `src/utils/platform.ts`
- Apple Sign-In button hidden on Android in `Login.tsx` using `isIosPlatform()`
- App Store badges (both desktop and mobile variants) hidden on Android using `!isNativePlatform() || isIosPlatform()`
- `initializeNativeSocialLogin()` fixed to only pass `apple` config on iOS
- Android OAuth client registered in Google Cloud project `394867503899` ("Diplicity Android 2"):
  - Package name: `com.diplicityreact.app`
  - SHA-1: `6F:9D:E2:20:2F:35:17:10:8C:41:28:B2:61:F5:4F:DE:7F:B1:0E:38` (debug keystore)
- `applicationId` renamed from `com.diplicity.app` → `com.diplicityreact.app` (canonical Android package name)
- `https://localhost` added to Django `CORS_ALLOWED_ORIGINS` default — Android Capacitor WebView uses this origin; without it CORS blocked the `/auth/login/` preflight
- Google Sign-In verified working end-to-end on Pixel 8a (debug build, local backend)

### Bug found and fixed: `apple: {}` crashes Android initialization
The `@capgo/capacitor-social-login` plugin processes Apple **before** Google in `SocialLoginPlugin.java`. Passing `apple: {}` (an empty object) passes the `apple != null` check, then immediately rejects with `"apple.android.redirectUrl is null or empty"` — causing the entire `SocialLogin.initialize()` call to reject. Because Apple is processed first, Google is never registered, so all subsequent `SocialLogin.login({ provider: 'google' })` calls fail with `"Cannot find provider 'google'. Provider was not initialized."`.

Fix in `nativeGoogleAuth.ts`:
```ts
await SocialLogin.initialize({
  google: { ... },
  ...(Capacitor.getPlatform() === "ios" ? { apple: {} } : {}),
});
```

### Android WebView CORS origin
The Capacitor Android WebView serves the app at `https://localhost`. API calls to `http://localhost:8000` are cross-origin, so Django needs `https://localhost` in `CORS_ALLOWED_ORIGINS`. This is included in the default value in `service/project/settings.py` — no env var change needed for local dev.

### Plugin internals (useful for debugging)
- Android plugin reads `webClientId` (not `androidClientId`) — confirmed in `SocialLoginPlugin.java:82`
- `SocialLogin.initialize()` rejects the **entire call** if any provider config is invalid, even if other providers were already set up earlier in the method
- Error `"Cannot find provider 'google'. Provider was not initialized."` = initialize was never called OR it rejected silently

### Play App Signing SHA-1
After first upload (#304), the Play App Signing SHA-1 `17:CF:46:81:F1:B2:95:8E:16:25:4A:9E:3E:85:F9:84:17:42:AD:58` was registered as a new Android OAuth client ("Android (Play Store)") in Google Cloud Console project `diplicity-django` (= project number `394867503899`). Two Android clients now exist — one for the debug keystore, one for the Play signing certificate.

### Production Google Sign-In — client ID mismatch

**Root cause discovered during Play Store testing:** The local `.env` has `VITE_GOOGLE_CLIENT_ID` set to the dev web client (`394867503899-0q69...`, "Diplicity Web (Development)"). Netlify production and the Railway Django backend both use the production web client (`394867503899-9kv1...`, "Diplicity Django Web"). When an Android build is made locally without overriding `VITE_GOOGLE_CLIENT_ID`, the Google ID token has `aud = 0q69...` but the backend's `GOOGLE_CLIENT_ID` expects `9kv1...` → backend returns `{"detail": "Invalid token audience"}`.

**How the backend validates:** `service/login/utils.py` decodes the Google ID token and checks that `id_info["aud"]` is in the list of `[GOOGLE_CLIENT_ID, GOOGLE_IOS_CLIENT_ID]` from Django settings. If `aud` doesn't match, login fails with 401.

**Fix:** Always pass the production client ID when building for the Play Store (see Production Release Build below).

---

## Issue #300 — Firebase Cloud Messaging (completed ✅)

### What was done
- `messaging-ios.ts` renamed to `messaging-native.ts` — the `@capacitor-firebase/messaging` plugin works on both iOS and Android; the old name was misleading
- `useMessaging.ts` updated:
  - Imports now reference `messaging-native` instead of `messaging-ios`
  - Device type was hardcoded to `"ios"` for all native platforms — fixed via `getNativeDeviceType()` helper that returns `"ios"` on iOS and `"android"` on Android
  - Effect 1 rename: `initIos` → `initNative` (cosmetic)
  - Effect 3 comment: "iOS only" → "native only"
- `isAndroidPlatform()` added to `src/utils/platform.ts`
- `android/**` added to ESLint ignore list in `eslint.config.js` (Android build artifacts were causing spurious lint errors)
- `CLAUDE.md` updated with Firebase/Android FCM setup instructions (google-services.json path, setup steps)
- `google-services.json` added to `packages/web/android/app/` (gitignored) — Android app registered in Firebase project `diplicity-react`, package name `com.diplicityreact.app`

### Verified end-to-end on Pixel 8a
1. App prompts for `POST_NOTIFICATIONS` permission on first enable
2. FCM token obtained via `FirebaseMessaging.getToken()`
3. Token registered in backend as `FCMDevice(type='android', active=True)`
4. Firebase console "Send test message" delivered notification to device ✅
5. Backend sends to Android via same `FCMDevice.objects.filter(...).send_message()` path used for iOS — no additional code needed

### google-services.json setup (for future reference)
- Firebase console → project `diplicity-react` → DevOps and engagement → Messaging → New campaign → compose a notification → "Send test message" link
- The file lives at `packages/web/android/app/google-services.json` (gitignored)
- The `build.gradle` conditional plugin wiring picks it up automatically:
  ```groovy
  try {
    def servicesJSON = file('google-services.json')
    if (servicesJSON.text) { apply plugin: 'com.google.gms.google-services' }
  } catch(Exception e) { ... }
  ```

Runtime `POST_NOTIFICATIONS` permission (Android 13+) is handled by `FirebaseMessaging.requestPermissions()` in `messaging-native.ts` — no additional code needed.

### FCM logcat filter
```bash
adb logcat | grep -iE "firebase|FCM|messaging|capacitor-firebase"
```

---

## Build & Run Quick Reference

### Local dev build (Pixel 8a, local backend)

```bash
cd packages/web
npm run build
ANDROID_HOME=$HOME/Android/Sdk npx cap sync android
ANDROID_HOME=$HOME/Android/Sdk npx cap run android --target 46101JEKB13333
```

### Production release build (Play Store)

Both `VITE_DIPLICITY_API_BASE_URL` and `VITE_GOOGLE_CLIENT_ID` must be set to production values at build time — they are baked into the JS bundle by Vite and cannot be changed at runtime.

```bash
cd packages/web
VITE_DIPLICITY_API_BASE_URL=https://diplicity-react-production.up.railway.app \
VITE_GOOGLE_CLIENT_ID=394867503899-9kv1fpoc3rthregsg5qd5goj9ul9mfdj.apps.googleusercontent.com \
npm run build && \
ANDROID_HOME=$HOME/Android/Sdk npx cap sync android && \
bundle exec fastlane android release
```

`VITE_GOOGLE_CLIENT_ID` here is the "Diplicity Django Web" client — the same one used by the Netlify production frontend and the Railway backend's `GOOGLE_CLIENT_ID`. Using the local dev value (`0q69...`) causes `{"detail": "Invalid token audience"}` on login.

### Testing against the local backend

The app is built with `VITE_DIPLICITY_API_BASE_URL=http://localhost:8000`. On the physical device, `localhost` resolves to the device itself — not the dev machine. Use `adb reverse` to forward the device's port 8000 to the host's port 8000:

```bash
adb reverse tcp:8000 tcp:8000
```

Run this **after every ADB reconnect** (it drops when USB resets). Docker must be running (`docker compose up`).

The Android WebView makes cross-origin requests from `https://localhost` to `http://localhost:8000`, so `https://localhost` must be in Django's `CORS_ALLOWED_ORIGINS` — already included in the default in `service/project/settings.py`.

For logcat debugging (run first, then trigger the action on device, then Ctrl+C):
```bash
# Google Sign-In debugging
adb logcat -c && adb logcat | grep -iE "SocialLogin|GoogleProvider|GetCredential|CredentialManager|DEVELOPER_ERROR|ApiException|capacitor|com.diplicityreact"

# WebView network + JS errors (broader — use when logcat isn't enough)
adb logcat -c && adb logcat | grep -iE "SocialLogin|GoogleProvider|capacitor|Chromium|SystemWebChromeClient|console|diplicity|Error|Exception"

# FCM / push notification debugging
adb logcat | grep -iE "firebase|FCM|messaging|capacitor-firebase|PushNotif"
```

Note: `adb logcat -d` (dump mode) exits before you can trigger the action. Use streaming mode (no `-d`) and Ctrl+C after.

### Verifying which build is installed

The `versionCode` is a Unix timestamp. Use this to confirm the device has the build you think it does before debugging:

```bash
adb shell dumpsys package com.diplicityreact.app | grep versionCode
# Then convert: python3 -c "import datetime; print(datetime.datetime.fromtimestamp(<versionCode>))"
```

### Chrome DevTools for WebView debugging

`webContentsDebuggingEnabled: true` in `capacitor.config.ts` enables Chrome DevTools against the WebView, even in release builds. This gives full Network tab visibility into HTTP requests/responses — far more useful than logcat for diagnosing backend errors.

1. Connect device via USB
2. Open Chrome on the dev machine → `chrome://inspect`
3. Find **Diplicity React** under Remote Targets → click **inspect**
4. Network tab shows all requests from the WebView, including status codes and response bodies

Use this when logcat shows the Android-side flow succeeding (e.g. `GoogleProvider: handleSignInResult`) but the login still fails — the issue is then in the backend call, visible in DevTools.
