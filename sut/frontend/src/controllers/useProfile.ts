import { useState, useEffect } from 'react';
import { router } from 'expo-router';
import { AuthService } from '@/src/services/AuthService';
import { BackendService } from '@/src/services/BackendService';
import { useTranslation } from 'react-i18next';
import { Logger } from '@/src/services/LoggerService';
import { useStatusModal } from '@/src/hooks/useStatusModal';
import { isTestMode } from '@/src/utils/environment';
import { getAuthErrorMessage } from '@/src/utils/authUtils';

const MIN_USERNAME_LENGTH = 3;
const MAX_USERNAME_LENGTH = 20;

export const useProfile = () => {
  const { t } = useTranslation();
  const initialUser = AuthService.getCurrentUser();
  const initialIsGuest = initialUser ? initialUser.isAnonymous : isTestMode();
  const initialName = initialUser?.isAnonymous ? '' : (initialUser?.displayName || '');
  const [userName, setUserName] = useState<string>(initialName);
  const [userEmail, setUserEmail] = useState<string>(initialUser?.email || '');
  const [newName, setNewName] = useState<string>(initialName);
  const [isGuest, setIsGuest] = useState<boolean>(initialIsGuest);
  
  const [saving, setSaving] = useState<boolean>(false);
  const [deleting, setDeleting] = useState<boolean>(false);
  const { modalVisible, modalConfig, showModal, hideModal } = useStatusModal();

  const trimmedName = newName.trim();
  const hasValidNameLength = trimmedName.length >= MIN_USERNAME_LENGTH && trimmedName.length <= MAX_USERNAME_LENGTH;
  const hasNameChanged = trimmedName !== userName;
  const canSaveName = !isGuest && hasNameChanged && hasValidNameLength && !saving;

  useEffect(() => {
    const unsubscribe = AuthService.onAuthChange((user) => {
      if (!user) {
        if (isTestMode()) {
          setIsGuest(true);
          setUserName('');
          setNewName('');
          setUserEmail('');
          return;
        }

        router.replace('/home' as any);
        return;
      }

      if (user.isAnonymous) {
        setIsGuest(true);
        setUserName('');
        setNewName('');
        setUserEmail('');
        return;
      }

      setIsGuest(false);
      setUserName(user.displayName || '');
      setNewName(user.displayName || '');
      setUserEmail(user.email || '');
    });
    return unsubscribe;
  }, []);

  const handleUpdateName = async () => {
    if (isGuest || !trimmedName || trimmedName === userName) return;

    if (!hasValidNameLength) {
      showModal('error', t('common.error'), t('auth.usernameLength'));
      return;
    }
    
    setSaving(true);
    const result = await AuthService.updateUserName(trimmedName);
    setSaving(false);
    
    if (result.success) {
      setUserName(trimmedName);
      setNewName(trimmedName);
      showModal('success', t('profile.updated'), t('profile.updatedDesc'));
    } else {
      showModal('error', t('common.error'), getAuthErrorMessage(result.error ?? ''));
    }
  };

  const confirmDeleteAccount = () => {
    if (isGuest) return;
    showModal(
      'confirm',
      t('profile.deleteConfirmTitle'),
      t('profile.deleteConfirmBody'),
      proceedWithDelete,
      hideModal,
    );
  };

  const proceedWithDelete = async () => {
    if (isGuest) return;

    hideModal();
    setDeleting(true);
    
    try {
      await BackendService.deleteUserData();
      
      const result = await AuthService.deleteAccount();
      setDeleting(false);
      
      if (result.success) {
        await AuthService.logout();
        router.replace('/' as any);
      } else {
        showModal('error', t('profile.securityFail'), t('profile.reauthRequired'));
      }
    } catch (error) {
      Logger.error('Error al eliminar datos del usuario', error);
      setDeleting(false);
      showModal('error', t('profile.deleteDataError'), t('profile.deleteDataErrorDesc'));
    }
  };

  const handleGoBack = () => {
    router.back();
  };

  return {
    userName,
    userEmail,
    newName,
    isGuest,
    setNewName,
    saving,
    deleting,
    canSaveName,
    hasNameChanged,
    handleUpdateName,
    confirmDeleteAccount,
    proceedWithDelete,
    handleGoBack,
    modalVisible,
    modalConfig,
    closeModal: hideModal,
  };
};
