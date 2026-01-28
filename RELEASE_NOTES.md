# Diplicity React - Release Notes

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
- [Diplomacy Discord](https://discord.gg/QETtwGR)
- [Play now](https://diplicity.com)

---