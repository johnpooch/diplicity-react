# Capacitor iOS Integration: Work Overview

## Background

Diplicity React is a React Vite TypeScript web app backed by a Django REST API with Google Auth. This document describes the work required to produce a native iOS app using Capacitor JS.

Significant progress was made on this integration previously, including creating the App Store distribution profile, app metadata, privacy labels, and uploading a build to the Apple Developer Portal. The source changes were lost due to a machine wipe. This document captures the known scope of work to guide re-implementation.

---

## Sequencing Constraints

The following ordering must be strictly respected:

1. **Push notification Playwright tests** must be written before the push notification refactor begins, so that the refactor can be validated against them
2. **Push notification frontend refactor** must be completed before iOS push notification work begins, so that the iOS changes are built on a clean foundation
3. **iOS simulator MCP tooling** must be fully working and validated before any iOS implementation work begins, so that agents can self-validate their changes
4. All **external prerequisites** (credentials, tokens, Apple configuration) must be resolved before implementation agents are launched

---

## Sub-Issues

### Group A: Push Notifications (Must Complete Before iOS Work)

**A1: Playwright tests for push notifications**

Write end-to-end Playwright tests covering the push notification flow as thoroughly as possible:
- User enables push notifications
- User disables push notifications
- User receives a push notification

Investigation required: browser permission dialog handling, Firebase emulator or stub setup, service worker lifecycle in test environment, FCM token handling. These tests must pass before A2 begins.

**A2: Push notifications frontend refactor**

The current push notification implementation uses a messaging context component that is overly complex and tightly coupled. Replace it with a simple custom hook. The refactor must not break any of the Playwright tests introduced in A1.

Investigation required: full audit of the messaging context component's responsibilities, what state it manages, what it exposes, what depends on it, and what the clean hook interface should look like.

*Dependencies: A1 must be merged first*

---

### Group B: iOS Simulator Tooling (Hard Prerequisite for Group C)

**B1: iOS simulator MCP tooling setup and validation**

Investigate, configure, and validate MCP (Model Context Protocol) tooling that allows Claude Code agents to interact directly with the iOS simulator. This must be fully working before any iOS implementation work begins.

Required capabilities:
- Launch the iOS simulator
- Install a build
- Interact with the running app
- Observe logs and output from within a Claude Code session

Produce a validation checklist demonstrating each capability works end-to-end. This issue is not complete until a Claude Code agent has successfully used the tooling to inspect a running simulator session.

*Dependencies: none, but must be merged before any Group C issue begins*

---

### Group C: Capacitor JS Integration

**C1: Capacitor JS build pipeline and configuration**

Integrate Capacitor JS into the React Vite TypeScript project. Cover:
- Installing and configuring Capacitor
- `capacitor.config.ts` setup
- `vite.config.ts` changes required for Capacitor compatibility
- `package.json` scripts for `cap sync`, `cap open`, `cap run`
- iOS platform initialisation
- Verifying a basic build runs in the simulator

*Dependencies: B1*

**C2: Dockerised Capacitor dependency installation**

Create a Docker-based flow for running `npm install` and `npx cap sync` so that Capacitor native dependency installation is reproducible and does not require specific local versions of Xcode tooling or CocoaPods. This ensures any new environment can reach a working state reliably.

Investigation required: whether the full CocoaPods install step needs to happen inside the container, volume mounting strategy for the iOS platform directory, CI/CD compatibility.

*Dependencies: C1*

**C3: Native Google Auth endpoint on the Django backend**

The existing Google Auth flow used by the Django backend does not work natively on iOS. A new endpoint and auth flow is required to support native sign-in from a Capacitor app.

Investigation required: what the native Google Sign-In flow looks like for Capacitor (likely using a native plugin), what new endpoint the Django backend needs to expose, how tokens are exchanged, how this interacts with the existing session/auth model.

*Dependencies: C1*

**C4: Frontend native auth integration**

Integrate the native Google Auth flow on the frontend. The app should detect whether it is running as a native iOS app or in a browser and use the appropriate auth method.

Investigation required: Capacitor platform detection, native sign-in plugin integration, how to handle the transition between web and native auth flows gracefully.

*Dependencies: C3*

**C5: Firebase and push notifications for Capacitor**

Integrate Capacitor's push notification plugin with the existing Firebase/FCM setup. The refactored custom hook from A2 should make this integration significantly cleaner.

Investigation required: how the Capacitor push notification plugin interacts with or replaces the existing FCM web setup, APNs configuration, FCM token handling differences between web and native, entitlements and capabilities in Xcode.

Prerequisites: APNs key, APNs key ID, Apple Team ID must be available as environment variables.

*Dependencies: A2, B1, C1*

**C6: Safe area and viewport styling for iOS**

Ensure the app respects iOS safe area boundaries — notch, Dynamic Island, home indicator — so that no UI is obscured on any supported device.

Investigation required: which components and layouts are currently affected, what CSS changes are needed (`env(safe-area-inset-*)`, `viewport-fit=cover`), whether any Capacitor-specific configuration is needed, how to validate in the simulator across different device sizes.

*Dependencies: C1*

**C7: Deep linking and URL scheme handling**

Investigate whether the app requires deep linking or custom URL scheme handling for the iOS build, and implement if necessary. This is particularly relevant for the OAuth redirect flow.

*Dependencies: C3, C4*

---

### Group D: App Store Preparation

**D1: App Store metadata, privacy labels, and distribution profile**

Note: significant work was already completed here in the Apple Developer Portal (distribution profile, app metadata, privacy labels, build upload). This issue should begin by auditing what already exists in the portal and identifying what still needs to be done.

Investigation required: current state of the App Store Connect record, whether the existing distribution profile and provisioning profile are still valid, what screenshots and preview assets are still needed, whether privacy label declarations are complete and accurate.

*Dependencies: C1 (a valid build must exist to verify upload pipeline)*

---

## External Prerequisites Checklist

The following must be resolved before any Group C or D implementation begins. These will be surfaced and documented during the scoping phase:

- [ ] Firebase project config values (API key, project ID, app ID, messaging sender ID)
- [ ] Google OAuth native client ID for iOS
- [ ] APNs key and APNs key ID
- [ ] Apple Team ID
- [ ] Apple Developer distribution certificate (valid on new machine)
- [ ] Provisioning profile (valid and downloaded on new machine)
- [ ] Django backend environment variables for new machine
- [ ] All values from `.env.example` recovered and populated

---

## Dependency Graph Summary

```
A1 → A2 ↘
B1      → C5
C1 → C2
C1 → C3 → C4 → C7
C1 → C5
C1 → C6
C1 → D1
```

Issues with no inbound dependencies (can start immediately once workflow is ready): A1, B1

Issues that unlock the most downstream work: A2, B1, C1

---

## Notes on Previous Progress

The following work was completed before the machine wipe and does not need to be redone:
- App Store Connect record created with metadata and privacy labels
- Distribution profile and provisioning profile created in Apple Developer Portal
- At least one build successfully uploaded to App Store Connect

When scoping Group D issues, agents should audit the current state of the portal rather than assuming everything needs to be created from scratch.
