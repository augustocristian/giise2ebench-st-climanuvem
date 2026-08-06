import { useState, useCallback } from 'react';
import { router, useFocusEffect } from 'expo-router';
import { AuthService } from '@/src/services/AuthService';
import { useAnalysisHistory } from '@/hooks/useAnalysisHistory';
import { isTestMode } from '@/src/utils/environment';

export const useHome = () => {
  const historyHook = useAnalysisHistory();
  const [userDisplayName, setUserDisplayName] = useState<string | undefined>();
  const [userEmail, setUserEmail] = useState<string>('');
  const [isGuest, setIsGuest] = useState<boolean>(false);

  useFocusEffect(
    useCallback(() => {
      if (isTestMode()) {
        setIsGuest(true);
        setUserDisplayName(undefined);
        setUserEmail('');
        return;
      }

      const unsubscribe = AuthService.onAuthChange((user) => {
        if (user) {
          setIsGuest(user.isAnonymous);
          setUserDisplayName(user.displayName);
          setUserEmail(user.email);
        } else {
          router.replace('/' as any);
        }
      });

      return unsubscribe;
    }, [])
  );


  const handleLogout = async () => {
    if (isTestMode()) {
      router.replace('/');
      return;
    }

    await AuthService.logout();
    router.replace('/');
  };

  const handleNavigateToCapture = () => {
    router.push('/capture' as any);
  };

  const handleNavigateToProfile = () => {
    router.push('/profile' as any);
  };

  return {
    handleLogout,
    handleNavigateToCapture,
    handleNavigateToProfile,
    userDisplayName,
    userEmail,
    isGuest,
    ...historyHook,
  };
};
