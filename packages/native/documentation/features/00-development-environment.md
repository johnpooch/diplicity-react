# React Native Development Environment Setup Guide

## Overview

This guide establishes the complete development environment for a React Native Diplomacy game client. The app will connect to an existing Django backend service and deploy to both iOS and Android app stores.

## Prerequisites

- macOS (required for iOS development)
- Xcode installed and configured
- Android Studio installed and configured
- Node.js 18+ installed
- Git configured

## Step 1: Initialize React Native Project

### Study existing codebase (native package)

Understand the existing `/packages/native` package.

### Install Additional Dependencies

If any of the following dependencies are not installed, install them:

```bash
# Development and testing dependencies
npm install --save-dev @types/react @types/react-native
npm install --save-dev eslint @typescript-eslint/eslint-plugin @typescript-eslint/parser
npm install --save-dev prettier eslint-config-prettier eslint-plugin-prettier
npm install --save-dev detox jest

# Production dependencies (will be needed later)
npm install @reduxjs/toolkit react-redux
npm install react-navigation/native react-navigation/native-stack
npm install react-native-svg
```

### Configure ESLint and Prettier

Create `.eslintrc.js`:

```javascript
module.exports = {
  extends: ['@expo/eslint-config', 'prettier'],
  plugins: ['prettier'],
  rules: {
    'prettier/prettier': 'error',
  },
};
```

Create `.prettierrc`:

```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2
}
```

### **HUMAN VERIFICATION POINT 1**

Run the following commands and verify output:

```bash
npm run lint
npm run format  # Add this script to package.json if needed
```

Expected: No linting errors, code properly formatted

## Step 2: Configure Development Environment

### Set up iOS Simulator

```bash
# Start iOS simulator (iPhone 14 recommended)
npx expo run:ios
```

### **HUMAN VERIFICATION POINT 2**

- iOS Simulator should launch with iPhone 14
- App should display "Open up App.js to start working on your app!"
- Hot reload should work when you modify App.tsx

### Set up Android Emulator

```bash
# Ensure Android emulator is running (Pixel 4 API 31 recommended)
# Then start Android app
npx expo run:android
```

### **HUMAN VERIFICATION POINT 3**

- Android Emulator should launch with Pixel 4
- App should display same hello world content as iOS
- Hot reload should work on Android

## Step 3: Basic Project Structure

### Create Directory Structure

```bash
mkdir -p src/{components,screens,services,utils,types}
mkdir -p src/components/{ui,navigation}
mkdir -p assets/{images,fonts}
mkdir -p __tests__/{components,screens,services}
```

### Create Basic Theme System

Create `src/theme/index.ts`:

```typescript
import React, { createContext, useContext } from 'react';

export const theme = {
  colors: {
    primary: '#007AFF',
    secondary: '#5856D6',
    background: '#FFFFFF',
    surface: '#F2F2F7',
    text: '#000000',
    textSecondary: '#8E8E93',
    border: '#C6C6C8',
    success: '#34C759',
    warning: '#FF9500',
    error: '#FF3B30',
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
  },
  typography: {
    title: { fontSize: 20, fontWeight: 'bold' as const },
    body: { fontSize: 16, fontWeight: 'normal' as const },
    caption: { fontSize: 14, fontWeight: 'normal' as const },
  },
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 16,
  },
} as const;

export type Theme = typeof theme;

const ThemeContext = createContext<Theme>(theme);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <ThemeContext.Provider value={theme}>{children}</ThemeContext.Provider>;
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
```

### Update App.tsx to Use Theme

```typescript
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { ThemeProvider, useTheme } from './src/theme';

const AppContent = () => {
  const theme = useTheme();

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.colors.background,
      alignItems: 'center',
      justifyContent: 'center',
    },
    title: {
      ...theme.typography.title,
      color: theme.colors.text,
      marginBottom: theme.spacing.md,
    },
  });

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Diplomacy Mobile</Text>
      <Text>Development environment ready!</Text>
    </View>
  );
};

export default function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}
```

### **HUMAN VERIFICATION POINT 4**

- App should display "Diplomacy Mobile" title with proper theme styling
- Text should use theme colors and typography
- Both iOS and Android should show identical styling
- Hot reload should work with theme changes

## Step 4: Basic Detox Setup

### Install Detox Dependencies

```bash
# Install Detox
npm install --save-dev detox

# For iOS
npm install --save-dev detox[ios]

# For Android
npm install --save-dev detox[android]
```

### Configure Detox

Create `detox.config.js`:

```javascript
module.exports = {
  testRunner: {
    args: {
      $0: 'jest',
      config: 'detox/jest.config.js',
    },
  },
  apps: {
    'ios.debug': {
      type: 'ios.app',
      binaryPath:
        'ios/build/Build/Products/Debug-iphonesimulator/DiplomacyMobile.app',
      build:
        'xcodebuild -workspace ios/DiplomacyMobile.xcworkspace -scheme DiplomacyMobile -configuration Debug -sdk iphonesimulator -derivedDataPath ios/build',
    },
    'android.debug': {
      type: 'android.apk',
      binaryPath: 'android/app/build/outputs/apk/debug/app-debug.apk',
      build:
        'cd android && ./gradlew assembleDebug assembleAndroidTest -DtestBuildType=debug',
      reversePorts: [8081],
    },
  },
  devices: {
    simulator: {
      type: 'ios.simulator',
      device: {
        type: 'iPhone 14',
      },
    },
    emulator: {
      type: 'android.emulator',
      device: {
        avdName: 'Pixel_4_API_31',
      },
    },
  },
  configurations: {
    'ios.sim.debug': {
      device: 'simulator',
      app: 'ios.debug',
    },
    'android.emu.debug': {
      device: 'emulator',
      app: 'android.debug',
    },
  },
};
```

### Create Basic Detox Test

Create `detox/jest.config.js`:

```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  setupFilesAfterEnv: ['<rootDir>/detox/setup.ts'],
  testMatch: ['<rootDir>/**/*.e2e.ts'],
  verbose: true,
};
```

Create `detox/setup.ts`:

```typescript
const detox = require('detox');
const config = require('../detox.config');

beforeAll(async () => {
  await detox.init(config);
});

afterAll(async () => {
  await detox.cleanup();
});
```

Create `detox/app-launch.e2e.ts`:

```typescript
describe('App Launch', () => {
  beforeEach(async () => {
    await device.reloadReactNative();
  });

  it('should display welcome screen on launch', async () => {
    // Given the app launches
    await expect(element(by.text('Diplomacy Mobile'))).toBeVisible();
    await device.takeScreenshot('app-launched');

    // Then the welcome message is displayed
    await expect(
      element(by.text('Development environment ready!'))
    ).toBeVisible();
    await device.takeScreenshot('welcome-screen');
  });
});
```

### **HUMAN VERIFICATION POINT 5**

Run Detox tests and verify:

```bash
# Build the app for testing
detox build --configuration ios.sim.debug

# Run the tests
detox test --configuration ios.sim.debug
```

Expected results:

- Tests should pass
- Screenshots should be generated in `detox/artifacts`
- Console should show test execution details

## Step 5: Package.json Scripts

Add these scripts to `package.json`:

```json
{
  "scripts": {
    "start": "expo start",
    "ios": "expo run:ios",
    "android": "expo run:android",
    "web": "expo start --web",
    "lint": "eslint . --ext .js,.jsx,.ts,.tsx",
    "format": "prettier --write .",
    "test": "jest",
    "test:detox:ios": "detox test --configuration ios.sim.debug",
    "test:detox:android": "detox test --configuration android.emu.debug",
    "build:detox:ios": "detox build --configuration ios.sim.debug",
    "build:detox:android": "detox build --configuration android.emu.debug"
  }
}
```

## **FINAL HUMAN VERIFICATION**

Verify the complete development environment:

1. **Run all linting and formatting:**

   ```bash
   npm run lint
   npm run format
   ```

2. **Test iOS development:**

   ```bash
   npm run ios
   # Should launch simulator with themed app
   ```

3. **Test Android development:**

   ```bash
   npm run android
   # Should launch emulator with identical app
   ```

4. **Test Detox on both platforms:**

   ```bash
   npm run build:detox:ios && npm run test:detox:ios
   npm run build:detox:android && npm run test:detox:android
   ```

5. **Verify file structure:**
   ```
   DiplomacyMobile/
   ├── src/
   │   ├── theme/
   │   ├── components/
   │   ├── screens/
   │   └── services/
   ├── detox/
   ├── assets/
   └── __tests__/
   ```

## Success Criteria

- [ ] iOS Simulator running with themed hello world app
- [ ] Android Emulator running with identical app
- [ ] Hot reload working on both platforms
- [ ] ESLint and Prettier configured and working
- [ ] Detox tests passing on both platforms
- [ ] Screenshots being generated during tests
- [ ] All npm scripts working correctly
- [ ] Project structure established for future development

## Next Steps

Once this setup is complete, you're ready for:

1. Basic API integration with unauthenticated endpoint
2. RTK Query codegen setup
3. CI/CD pipeline configuration
4. Authentication and notification integration

## Troubleshooting Notes

- If iOS build fails, ensure Xcode Command Line Tools are installed
- If Android build fails, check Android SDK and emulator setup
- If Detox tests fail, verify simulator/emulator names match configuration
- All file paths assume project root as working directory
