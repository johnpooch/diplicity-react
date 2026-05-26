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

## Issue #301 — Google Sign-In / Apple hidden (code complete, OAuth registration pending)

### What was done
- `isIosPlatform()` added to `src/utils/platform.ts`
- Apple Sign-In button hidden on Android in `Login.tsx` using `isIosPlatform()`
- App Store badges (both desktop and mobile variants) hidden on Android using `!isNativePlatform() || isIosPlatform()`
- `initializeNativeSocialLogin()` fixed to only pass `apple` config on iOS

### Bug found and fixed: `apple: {}` crashes Android initialization
The `@capgo/capacitor-social-login` plugin processes Apple **before** Google in `SocialLoginPlugin.java`. Passing `apple: {}` (an empty object) passes the `apple != null` check, then immediately rejects with `"apple.android.redirectUrl is null or empty"` — causing the entire `SocialLogin.initialize()` call to reject. Because Apple is processed first, Google is never registered, so all subsequent `SocialLogin.login({ provider: 'google' })` calls fail with `"Cannot find provider 'google'. Provider was not initialized."`.

Fix in `nativeGoogleAuth.ts`:
```ts
await SocialLogin.initialize({
  google: { ... },
  ...(Capacitor.getPlatform() === "ios" ? { apple: {} } : {}),
});
```

### Pending: Android OAuth client registration
Google Sign-In completes the account picker but then fails with `DEVELOPER_ERROR`. Cause: no Android OAuth client registered in the correct Google Cloud project.

- **Project**: `394867503899` (same project as `VITE_GOOGLE_CLIENT_ID`)
- **Project owner**: John McDowell (other developer, not available at time of writing)
- **Action needed**: Register an Android OAuth client in that project with:
  - Package name: `com.diplicityreact.app`
  - SHA-1: `6F:9D:E2:20:2F:35:17:10:8C:41:28:B2:61:F5:4F:DE:7F:B1:0E:38` (debug keystore)
- **No code change needed** — the plugin uses `webClientId` for Android, not a separate Android client ID. The registration is purely a Google Cloud Console configuration step.
- After Play App Signing (#304), the production SHA-1 from Play Console also needs to be added to the same OAuth client.

### Plugin internals (useful for debugging)
- Android plugin reads `webClientId` (not `androidClientId`) — confirmed in `SocialLoginPlugin.java:82`
- `SocialLogin.initialize()` rejects the **entire call** if any provider config is invalid, even if other providers were already set up earlier in the method
- Error `"Cannot find provider 'google'. Provider was not initialized."` = initialize was never called OR it rejected silently

---

## Issue #300 — Firebase Cloud Messaging (code done, blocked on google-services.json)

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

### Pending: google-services.json
FCM won't work until the Android app is registered in the Firebase project and `google-services.json` is in place.

Steps:
1. Go to Firebase console → project `diplicity-react` → Project settings → Add app → Android
2. Enter package name: `com.diplicityreact.app`
3. Download `google-services.json` → place at `packages/web/android/app/google-services.json`
4. Build and deploy to Pixel 8a, verify notification arrives

The `build.gradle` conditional plugin wiring is already in place:
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

```bash
cd packages/web
npm run build
ANDROID_HOME=$HOME/Android/Sdk npx cap sync android
ANDROID_HOME=$HOME/Android/Sdk npx cap run android --target 46101JEKB13333
```

For logcat debugging (run first, then trigger the action on device, then Ctrl+C):
```bash
# Google Sign-In debugging
adb logcat | grep -iE "SocialLogin|GoogleProvider|ApiException|DEVELOPER_ERROR|GetCredential|capacitor"

# FCM / push notification debugging
adb logcat | grep -iE "firebase|FCM|messaging|capacitor-firebase|PushNotif"
```

Note: `adb logcat -d` (dump mode) exits before you can trigger the action. Use streaming mode (no `-d`) and Ctrl+C after.
