# Google Services Setup

This document explains how to set up Google Services for the React Native app.

## Required Files

- `GoogleService-Info.plist` (iOS) - **DO NOT COMMIT TO GIT**
- `google-services.json` (Android) - Already configured

## Local Development Setup

1. **Get GoogleService-Info.plist from Firebase Console:**
   - Go to [Firebase Console](https://console.firebase.google.com)
   - Select your project (or create one)
   - Add an iOS app with bundle ID: `com.diplicity.app`
   - Download the `GoogleService-Info.plist` file
   - Place it in this directory: `packages/native/GoogleService-Info.plist`

2. **Verify the configuration:**
   - The `CLIENT_ID` should match your `GOOGLE_OAUTH_CLIENT_ID` environment variable
   - The `BUNDLE_ID` should be `com.diplicity.app`

## GitHub Actions Setup

For CI/CD deployment, you need to provide the GoogleService-Info.plist content as a GitHub secret:

1. **Create a GitHub Secret:**
   - Go to your GitHub repository
   - Navigate to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `GOOGLE_SERVICE_INFO_PLIST`
   - Value: Copy the entire content of your `GoogleService-Info.plist` file

2. **Update your GitHub Actions workflow:**
   ```yaml
   - name: Create GoogleService-Info.plist
     run: |
       echo '${{ secrets.GOOGLE_SERVICE_INFO_PLIST }}' > packages/native/GoogleService-Info.plist
   ```

## Template File

Use `GoogleService-Info.plist.template` as a reference for the required structure. Replace the placeholder values with your actual Firebase project values.

## Security Notes

- Never commit the actual `GoogleService-Info.plist` file to git
- The file contains sensitive API keys and project information
- Use GitHub Secrets for CI/CD environments
- Rotate API keys regularly for security
