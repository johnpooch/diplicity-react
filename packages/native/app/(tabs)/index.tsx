import { Image, StyleSheet, Platform, View, Text } from 'react-native';

import { HelloWave } from '@/components/HelloWave';
import ParallaxScrollView from '@/components/ParallaxScrollView';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import { GoogleSigninButton } from '@react-native-google-signin/google-signin';
import { authService, telemetry } from '@/services';
import { useTheme } from '@/src/theme';

export default function HomeScreen() {
  const theme = useTheme();

  const onPressSignIn = async () => {
    telemetry.logInfo('Sign in button pressed');
    authService.getServerAuthCode().then((serverAuthCode) => {
      authService.getCallbackUrl(serverAuthCode).then((callbackUrl) => {
        telemetry.logInfo(`Navigating to ${callbackUrl}`);
      });
    });
  };

  return (
    <View
      style={[styles.container, { backgroundColor: theme.colors.background }]}
    >
      <Text
        style={[
          styles.title,
          { color: theme.colors.text, ...theme.typography.title },
        ]}
      >
        Diplomacy Mobile
      </Text>
      <Text
        style={[
          styles.subtitle,
          { color: theme.colors.textSecondary, ...theme.typography.body },
        ]}
      >
        Development environment ready!
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
  },
  title: {
    marginBottom: 16,
    textAlign: 'center',
  },
  subtitle: {
    textAlign: 'center',
  },
});
