import { useEffect } from 'react';
import { router } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import * as SystemUI from 'expo-system-ui';
import { AuthService } from '@/src/services/AuthService';
import { isTestMode } from '@/src/utils/environment';

export const useAppBootstrap = () => {
  useEffect(() => {
    SystemUI.setBackgroundColorAsync('#FFFFFF');

    if (isTestMode()) {
      SplashScreen.hideAsync();
      return;
    }

    const unsubscribe = AuthService.onBootstrapAuthChange(async (isAllowed, hasUser) => {
      if (isAllowed) {
        setTimeout(() => {
          router.replace('/home' as any);
          SplashScreen.hideAsync();
        }, 0);
        return;
      }

      if (hasUser) {
        await AuthService.logout();
      }
      SplashScreen.hideAsync();
    });

    return unsubscribe;
  }, []);
};
