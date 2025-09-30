# Feature: Notification Permission Error Handling and User Feedback

**Date:** 2025-09-30
**Session:** Fix notification toggle broken state for users with denied permissions

## Summary
Enhanced the push notification system to properly handle browser permission states, provide clear error feedback, and prevent the notification banner from flashing on page load. Users with blocked permissions now see helpful guidance instead of a non-functional toggle.

## Problem Solved
Users reported that the notification toggle on the profile screen appeared inactive and did nothing when clicked. This occurred when:
1. Browser permission was already denied (e.g., previously blocked or in browsers like Edge)
2. `Notification.requestPermission()` returns `"denied"` immediately without showing prompt
3. Errors were logged to console but not surfaced to users
4. NotificationBanner would flash briefly on every page load before state was determined

## Implementation Details

**Files Modified:**
- `packages/web/src/context/MessagingContext.tsx`
  - Added `permissionDenied` boolean to track `Notification.permission === "denied"`
  - Added `error` state for user-facing error messages
  - Added `isLoading` state to prevent premature UI rendering
  - Enhanced `enableMessaging()` to check permission before requesting
  - Modified initial useEffect to only get token if permission already granted
  - Set `isCheckingToken` state to track initialization completion

- `packages/web/src/screens/Home/Profile.tsx`
  - Added error Alert banner for displaying error messages
  - Added warning Alert with instructions when permission is permanently denied
  - Disabled toggle switch when `permissionDenied` is true
  - Consumed new `permissionDenied`, `error` context values

- `packages/web/src/components/NotificationBanner.tsx`
  - Returns `null` while `isLoading` to prevent flash
  - Removed unnecessary `query.isSuccess` check (simplified to just `!enabled`)

## Rationale

**Permission State Check First:** Checking `Notification.permission` before calling `requestPermission()` allows us to:
- Detect already-denied state and show instructions
- Avoid silent failures that confused users
- Disable UI elements that won't work

**Loading State:** Without tracking initialization state, the banner would always appear briefly because:
- `enabled` starts as `false`
- Token retrieval and device list loading are async
- Banner would render before state determination completed

**Error State in Context:** Centralizing error state in the context (rather than component-level) allows:
- Consistent error handling across enable/disable flows
- Errors from async token operations to surface to UI
- Clear communication about what went wrong

**Initial Token Check:** On mount, we check if permission is `"granted"` and get token silently. This:
- Preserves existing user sessions (no re-prompt needed)
- Allows NotificationBanner to show correctly for users who haven't enabled
- Doesn't trigger errors for users with denied permissions
- No unexpected permission prompts on page load

## Testing
Manual testing performed across browsers:
- **Chrome (working case):** Toggle and banner behave correctly
- **Edge (broken case reproduced):** Permission denied error properly caught and displayed
- **Fresh browser:** Permission prompt shown, correct feedback for allow/deny
- **Permission already denied:** Warning banner + disabled toggle shown with instructions

## Notes

**Future Considerations:**
- Consider adding a "retry" or "refresh" button after user enables permission in browser settings
- Could add toast notifications instead of/in addition to Alert banners
- The `onClose` handler in Profile.tsx error Alert is currently a no-op (no way to clear error from component)

**Browser Compatibility:**
- `Notification.permission` is standard across modern browsers
- Service worker requirement means notifications only work on HTTPS (except localhost)
- iOS Safari has limited PWA notification support

**Related Files:**
- `packages/web/src/messaging.ts` - Firebase setup and token management
- `packages/web/public/firebase-messaging-sw.js` - Service worker for background notifications