import { router } from 'expo-router';
import { AuthService } from '@/src/services/AuthService';
import { Logger } from '@/src/services/LoggerService';
import { useTranslation } from 'react-i18next';
import { useStatusModal } from '@/src/hooks/useStatusModal';
import { isTestMode } from '@/src/utils/environment';

export const useWelcome = () => {
  const { t } = useTranslation();
  const { modalVisible, modalConfig, showModal, hideModal } = useStatusModal();

  const handleNavigateToLogin = () => {
    router.push('/login' as any);
  };

  const handleContinueAsGuest = async () => {
    if (isTestMode()) {
      router.replace('/home' as any);
      return;
    }

    const response = await AuthService.loginAnonymously();
    if (response.success) {
      router.replace('/home' as any);
    } else {
      Logger.error('Failed to login as guest', response.error);
      showModal('error', t('common.error'), response.error ?? t('auth.googleErrorDesc'));
    }
  };

  return {
    handleNavigateToLogin,
    handleContinueAsGuest,
    modalVisible,
    modalConfig,
    hideModal,
  };
};
