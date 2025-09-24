// Load environment variables from root .env file
import { config } from 'dotenv';
import { resolve } from 'path';

// Load .env file from project root (two directories up from packages/native)
config({ path: resolve(__dirname, '../../.env') });

// Helper function to get iOS URL scheme from Google OAuth Client ID
const getIosUrlScheme = () => {
  const clientId = process.env.GOOGLE_OAUTH_CLIENT_ID;
  if (!clientId) {
    throw new Error(
      'GOOGLE_OAUTH_CLIENT_ID not found in environment variables'
    );
  }
  // Extract the client ID part and add the required prefix
  const clientIdOnly = clientId.replace('.apps.googleusercontent.com', '');
  return `com.googleusercontent.apps.${clientIdOnly}`;
};

export default {
  expo: {
    name: 'diplicity-react-native',
    slug: 'diplicity-react-native',
    version: '1.0.0',
    orientation: 'portrait',
    icon: './assets/images/icon.png',
    scheme: 'myapp',
    userInterfaceStyle: 'automatic',
    newArchEnabled: true,
    ios: {
      supportsTablet: true,
      bundleIdentifier: 'com.diplicity.app',
      googleServicesFile: './GoogleService-Info.plist',
    },
    android: {
      adaptiveIcon: {
        foregroundImage: './assets/images/adaptive-icon.png',
        backgroundColor: '#ffffff',
      },
      package: 'com.diplicity.app',
      googleServicesFile: './google-services.json',
    },
    web: {
      bundler: 'metro',
      output: 'static',
      favicon: './assets/images/favicon.png',
    },
    plugins: [
      'expo-router',
      [
        'expo-splash-screen',
        {
          image: './assets/images/splash-icon.png',
          imageWidth: 200,
          resizeMode: 'contain',
          backgroundColor: '#ffffff',
        },
      ],
      [
        '@react-native-google-signin/google-signin',
        {
          iosUrlScheme: getIosUrlScheme(),
        },
      ],
    ],
    experiments: {
      typedRoutes: true,
    },
    extra: {
      router: {
        origin: false,
      },
      eas: {
        projectId: '9d511a57-60e6-44ed-9a59-e47841b1a0ec',
      },
      googleClientId: process.env.GOOGLE_OAUTH_CLIENT_ID,
    },
  },
};
