# Diplicity React - Release Notes

## Game Master for Private Games (June 2026)

### Feature: Run a private game as a non-playing Game Master

When creating a private game, you can now choose to act as its Game Master. As Game
Master you don't take a nation — all player slots go to other players — but you can
pause and resume the game, extend deadlines, remove players before the game starts,
and delete the game while it's still gathering players. You receive game notifications
(game start, phase resolutions, civil disorder, and more) so you can keep an eye on
things. When a game has a Game Master, the players — including the game's creator —
do not have these management powers. The Game Master appears at the top of the player
roster with a "Game Master" badge.

## Game Creator Rename (June 2026)

### Change: "Game Master" badge is now "Game Creator"

The player who created a game is now labelled "Game Creator" instead of "Game Master" in
the player roster. Their powers are unchanged (pause/resume the game, extend deadlines,
remove players from a game that hasn't started). This prepares for an upcoming non-playing
Game Master role for private games.

## Player Profiles (June 2026)

### Feature: Public player profiles with reliability stats

Every player now has a public profile showing their name, avatar, reliability badge, NMR
rate, CD rate, solo wins, draws, losses, and total games played. Player names in the player
roster are tappable — tap any name to see that player's profile and stats. Players with
strong reliability earn a "Reliable" badge; new players with fewer than 10 games show a
"New" badge.

## Civil Disorder Retreat Fix (June 5, 2026)

**Release Date:** June 5, 2026

### Fix: Civil Disorder units now automatically disband during Retreat phases

Units belonging to a nation in Civil Disorder are now automatically disbanded when a
Retreat phase begins. Previously, games with a Civil Disorder player could stall waiting
for a manual resolution step. The game now advances immediately to the next interactive
phase without requiring any action.

## Sign in with Apple on the Web (June 2, 2026)

**Release Date:** June 2, 2026

### Feature: Sign in with Apple now works in the browser

"Sign in with Apple" is now available on the web app, alongside Google sign-in. Previously
it was only offered in the iOS app. Web and iOS Apple sign-ins resolve to the same account.

## Faster Phase Resolution (June 1, 2026)

**Release Date:** June 1, 2026

### Improvement: Phases resolve within seconds

Phase resolution now runs on a background worker triggered the moment the last player
confirms or the deadline arrives, instead of waiting for a once-a-minute check. A phase
resolves within a couple of seconds of the last confirmation and within a few seconds of
its deadline. A once-a-minute safety net still catches anything a trigger misses, so
nothing gets stuck.

### Improvement: Deadline reminders are sent once per deadline

The "Deadline Approaching" reminder is now sent at most once per deadline to each player
who still has orders to give. If a deadline is later extended, players who still haven't
confirmed get a fresh reminder before the new deadline. Push notifications are now all
sent in the background, so posting a message or starting a game responds immediately.

## Android Push Notifications (May 26, 2026)

**Release Date:** May 26, 2026

### Feature: Push notifications now work on Android

The Android app now supports push notifications via Firebase Cloud Messaging. After granting notification permission, the app registers your device with the backend and you'll receive game alerts (phase changes, chat messages, etc.) just like on iOS. Notifications received while the app is open also refresh the game data automatically.

## Per-Nation Flag Uploads for Variants (May 26, 2026)

**Release Date:** May 26, 2026

### Feature: Upload a flag for each nation in your draft variant

The variant edit screen (`/variants/<id>/edit`) now has a per-nation flag uploader. Each nation in your draft variant gets a row with its current flag preview, an SVG file picker, and a Remove button. Flags are served from the backend with a content-hashed URL and immutable caching, so they replace the static frontend bundle that previously held flags for only four hardcoded variants. Re-uploading a dvar preserves flags whose nation id is unchanged; flags for removed or renamed nations are dropped. Flags are optional — nations without one render no flag in game UI.

## Skip Empty Phases (May 25, 2026)

**Release Date:** May 25, 2026

### Improvement: Retreat and adjustment phases with nothing to do are skipped

When a turn dislodges no units, or when everyone's builds and disbands are balanced, the game now advances straight to the next phase that actually needs orders instead of creating an empty retreat or adjustment phase. Previously these empty phases were created and sat waiting — in fixed-time games an empty retreat would hold for the full deadline (up to 24 hours) before resolving, even though no one had anything to do. Spring movement with no retreats now goes directly to fall movement.
## Fleet Orders from Named Coasts (May 24, 2026)

**Release Date:** May 24, 2026

### Bug Fix: Moving a fleet off a named coast

Issuing a move order for a fleet sitting on a named coast (for example a fleet on Spain's south coast) toward a destination that itself has named coasts failed with a server error, so the order could not be submitted. The order wizard now correctly recognises the fleet and lets you pick the destination coast.
## Faster "Clone to Sandbox" (May 24, 2026)

**Release Date:** May 24, 2026

### Improvement: Cloning a game to a sandbox is quicker

Cloning a game into a sandbox copied the board one database lookup at a time, which added up to hundreds of queries and a noticeable wait. The copy now loads the units and supply centers in two queries instead, so the sandbox opens faster.

## Sandbox Games for Uploaded Variants (May 21, 2026)

**Release Date:** May 21, 2026

### Bug Fix: Starting a sandbox game with a user-uploaded variant

Starting a sandbox game on a draft variant you uploaded yourself now works. The previous adjudicator only knew about the variants it shipped with, so kicking off a game for anything else (e.g. Spice Islands) failed with a 404 the moment you hit Start. The adjudicator has been switched to an in-process Python implementation that runs against whatever variant data is in your draft, so any uploaded variant is playable as soon as it's saved.

## Creation Intervention: Suggest Joining a Similar Game (May 5, 2026)

**Release Date:** May 5, 2026

### New Feature: Suggested Similar Game on Create

When you submit Create Game, if a similar public staging game already exists (same variant and movement phase duration), a prompt now asks whether you'd rather join that game instead. Pick "Join Them?" to head to its Game Info page, or "Continue" to create your own as before. Private games and fixed-time deadlines skip this check.
## Find Games: "Fastest Start" highlight (May 5, 2026)

**Release Date:** May 5, 2026

### Improvement: Find Games surfaces the joinable game closest to starting

The Find Games list now sorts joinable games by how close they are to filling, so the staging game with the fewest open slots appears first. When the top game already has at least three players, it's marked with a "Fastest Start" header and badge — a clear signal of where to join if you want to start playing as soon as possible. Filtering by variant or duration still works the same way; the highlight applies within whatever filters you've set.

---

## Order Wizard Overhaul & Bug Fixes (March 19, 2026)

**Release Date:** March 19, 2026

### Major Improvement: Client-Side Order Wizard

The order wizard has been completely reworked to run client-side. Previously, each step of order creation required a separate API call, making the process feel sluggish — especially on slow connections. Now, all valid orders are fetched in a single request and the wizard runs locally in your browser, with just one final request to submit. The result is a noticeably faster and more responsive ordering experience.

### Bug Fix: Retreat Phase Showing Wrong Unit

During retreat phases, the orders screen was sometimes displaying the attacking unit instead of the dislodged unit that needs to retreat. This has been fixed on both the backend and frontend — you'll now always see the correct unit when issuing retreat orders.

### Bug Fix: Phase Navigation Arrows on Map Screen

The left/right arrows for navigating between phases were silently failing on the Map screen. This has been fixed — phase navigation now works reliably across all screens.

### Bug Fix: Sheet Close Button Registering as "Hold" on Mobile

On mobile, the close button on order sheets had a tiny tap target that overlapped with the first menu item (typically "Hold"), causing accidental order submissions. The redundant close button has been removed — tap outside the sheet to dismiss it.

### Improvement: Chat Drafts Persist Across Navigation

Chat message drafts are no longer lost when you navigate away from a channel. Your in-progress messages are saved for the duration of your browser session, so you can switch between channels without losing what you were typing.

### Improvement: Navigation Icon Clarity

Primary game screens (Map, Orders, Chat) now show an X icon instead of a back arrow on mobile, better indicating that they navigate to the home page rather than a previous screen.

---

## Flexible Deadlines & Game Master Controls (February 6, 2026)

**Release Date:** February 6, 2026

### New Feature: Game Master Role

The player who creates a game is now the Game Master. Game Masters have exclusive access to game management controls including pausing, resuming, and extending deadlines.

### New Feature: Pause & Resume Games

Game Masters can pause an active game, freezing the deadline timer. When resumed, the deadline adjusts to account for the paused time. All players are notified when a game is paused or resumed.

### New Feature: Extend Deadlines

Game Masters can extend the current phase deadline by a chosen duration (1 hour to 2 weeks). All players are notified when a deadline is extended.

### New Feature: NMR Automatic Extensions

Games can be configured with automatic extensions (1 or 2 per player) that activate when a player misses the deadline. This gives players a safety net for unexpected absences. The extension count is visible in Player Info.

### New Feature: Fixed-Time Deadline Mode

In addition to duration-based deadlines, games can now use fixed-time deadlines that resolve at a specific time of day on a set frequency (hourly, daily, every 2 days, or weekly). This is ideal for games where players want a predictable daily deadline.

### New Feature: Deadline Warning Notifications

Players who haven't confirmed their orders receive a notification as the deadline approaches, helping prevent missed turns.

### Improved: More Duration Options

Game creation now supports durations from 1 hour to 2 weeks, giving more flexibility for both fast-paced and slow-paced games.

---

## Auto-detect Abandoned Games (January 28, 2026)

**Release Date:** January 28, 2026

### New Feature: Abandoned Game Detection

Games are now automatically marked as abandoned when no orders are submitted by any player for 2 consecutive phases. This helps keep the game list clean and provides closure for games where players have stopped participating.

#### How it Works:
- After 2 consecutive phases with zero orders from any player, the game is marked as "Abandoned"
- Abandoned games appear in the "Finished" tab alongside completed games
- An alert is displayed in abandoned games explaining they were ended due to inactivity
- Sandbox games are excluded from abandonment detection (you can take as long as you want)
- If any player submits even one order in either of the two most recent phases, the game continues

---

## Draw Screens Now Display Nation Flags (January 28, 2026)

**Release Date:** January 28, 2026

### Improvement: Nation Flags in Draw Proposals

The Draw Proposals and Propose Draw screens now display nation flags instead of user profile pictures. This maintains consistency with the rest of the in-game experience where players are represented by their nation's flag rather than their personal avatar.

---

## UI Overhaul and Supply Center Display (January 24, 2026)

**Release Date:** January 24, 2026

### Major UI Migration: Material UI to ShadCN

We've completed a significant migration of the entire UI framework from Material UI to ShadCN. This brings a more modern, consistent look and feel across the app, along with improved performance and accessibility.

**Please note:** Due to the scope of this migration, there may be visual bugs or unexpected behavior in some areas of the app. We've tested extensively, but with so many changes, some issues may have slipped through. If you encounter any problems, please let us know on Discord. We appreciate your patience as we iron out any remaining issues!

### New Feature: Supply Center Count on Orders Screen

The Orders screen now displays each nation's supply center count directly in the accordion header, making it easier to see standings at a glance without navigating to Player Info.

### New Feature: Phase Guidance Text

A new guidance line appears below the phase selector showing what actions are required and your progress. Messages like "2 of 3 orders submitted · not confirmed" help you understand exactly what's needed to advance to the next phase.

### Improvement: Game Creation Redirect

After creating a game, you're now taken directly to the game instead of back to the home screen. Standard games redirect to the Game Info screen where you can share the link and wait for players, while Sandbox games take you straight into the game.

---

## Solo Victory Conditions & Performance Updates (December 1, 2025)

**Release Date:** December 1, 2025

### 🏆 New Feature: Solo Victory Conditions

Games now automatically end when a player achieves a solo victory by controlling 18 or more supply centers! This long-awaited feature ensures games conclude properly when dominance is achieved.

#### How it Works:
- When any player controls 18+ supply centers at the end of a phase, the game immediately ends
- The winning player is clearly marked in the game status
- All other players are notified of the solo victory
- The game moves to the "Finished" tab with the victor displayed

### 🐛 Critical Bug Fix: Dislodged Units

Fixed a critical issue where dislodged units weren't being handled correctly during phase resolution. Units that were dislodged in combat now properly:
- Show as dislodged in the UI
- Must retreat or disband in the subsequent retreat phase
- Cannot participate in moves until properly retreated

This fix ensures the game follows proper Diplomacy rules for unit displacement.

### ⚡ Performance Improvements

Multiple backend optimizations have been implemented to significantly improve app responsiveness:
- **Faster game loading**: Optimized database queries reduce initial game load time by ~40%
- **Smoother order processing**: Order list rendering and updates are now much more responsive
- **Reduced server load**: Better query optimization means less waiting for data

### 🛠️ Under the Hood

Added professional monitoring and error tracking tools to help identify and fix issues faster. This means we can proactively address problems before they impact your games.

---

## Map Improvements and New Variant (October 25, 2025)

**Release Date:** October 25, 2025

### 🗺️ Feature: Hundred Variant

A new variant is now available to play! You can select the **Hundred** variant when creating a new game.

### 🔍 Improvement: Enhanced Map Interaction

The game map now supports **zoom and pan functionality**, making it easier to navigate maps and view detailed province information. This is especially useful on mobile devices and when playing variants with many provinces.

**Note, this feels a bit sluggish on mobile. There is some optimization to be done here. Thanks for your patience!**

#### How to Use:
- **Zoom**: Pinch to zoom on touch devices, or use scroll wheel on desktop
- **Pan**: Drag to move around the map

### ⚡ Performance Improvements

Several behind-the-scenes optimizations have been made to improve app performance:
- Fixed database query issues that were causing slow load times when viewing your games list
- Optimized variant data loading for faster browsing
- Added performance monitoring to help identify and fix slowdowns faster

**There's a lot more performance work to be done which I am only becoming aware of as more users join the platform. Thanks for your patience. It will be super snappy soon!**

### 🐛 Bug Fixes

- Fixed an issue where users without profile pictures were not able to sign in
- Removed warning from login screen.

## Sandbox Games and other requested features (October 18, 2025)

**Release Date:** October 18, 2025  

### 🎯 Feature: Sandbox Games

Diplicity now supports **Sandbox Games** - this allows players to create and manage single-player Diplomacy games for learning, testing strategies, and exploring different scenarios without time constraints.

#### What are Sandbox Games?

Sandbox Games are special single-player games where:
- **No time limits**: Phases don't automatically resolve - you control when to advance
- **Full control**: You play all 7 nations yourself
- **Private by default**: These games are not visible to other players
- **No diplomacy**: No channels or messaging (focus on pure strategy)
- **Immediate start**: Games begin right away without waiting for other players

#### 🎮 How to Use Sandbox Games

### Creating a Sandbox Game
1. Navigate to the main menu
2. Click "Create Game" 
3. Select "Sandbox Game" tab
4. Choose your preferred variant
5. Enter a game name
6. Click "Create Game" - your game will appear in the "Sandbox" tab on the home screen

### 🔧 Feature: Changes to how users' names are presented

Users' names are automatically set using their Google login. Some users want to be able to change their names. Users can now edit their display names directly from their profile. Their Google username is not exposed. The user's Google profile picture is still used. If there is the ask, we could allow users to replace their profile image, but that would require setting up image storage.

### ⚡ Improvement

Database queries for variant data have been optimized, reducing load times when browsing games and variants.

## 🙏 Community

Thanks to the Diplomacy community for trying the beta version of the app and sharing their feedback!

**Join the conversation:**
- [Diplomacy Discord](https://discord.gg/2TkZbBRPW)
- [Play now](https://diplicity.com)

---