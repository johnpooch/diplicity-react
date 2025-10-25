# Diplicity React - Release Notes

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