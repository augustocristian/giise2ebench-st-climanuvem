import { useState, useRef } from 'react';
import { router } from 'expo-router';
import { TextInput } from 'react-native';
import { AuthService } from '@/src/services/AuthService';
import { useTranslation } from 'react-i18next';
import { useStatusModal } from '@/src/hooks/useStatusModal';

import { EMAIL_REGEX, getAuthErrorMessage } from '@/src/utils/authUtils';

export const useRegister = () => {
  const { t } = useTranslation();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { modalVisible, modalConfig, showModal, hideModal } = useStatusModal();

  // Referencias para el foco de los inputs
  const emailInputRef = useRef<TextInput>(null);
  const passwordInputRef = useRef<TextInput>(null);
  const confirmPasswordInputRef = useRef<TextInput>(null);

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const toggleConfirmPasswordVisibility = () => {
    setShowConfirmPassword(!showConfirmPassword);
  };

  const handleRegister = async () => {
    // Validaciones
    if (username.length < 3 || username.length > 20) {
      showModal('error', t('common.error'), t('auth.usernameLength'));
      return;
    }

    if (!EMAIL_REGEX.test(email)) {
      showModal('error', t('common.error'), t('auth.invalidEmail'));
      return;
    }

    if (password.length < 6) {
      showModal('error', t('common.error'), t('auth.passwordLength'));
      return;
    }

    if (password !== confirmPassword) {
      showModal('error', t('common.error'), t('auth.passwordsDoNotMatch'));
      return;
    }

    setLoading(true);

    const response = await AuthService.register(username, email, password);

    setLoading(false);

    if (response.success) {
      showModal(
        'success',
        t('auth.registrationSuccess'),
        t('auth.verificationEmailSent'),
        () => {
          hideModal();
          handleNavigateToLogin();
        }
      );
    } else {
      // Si falla, se podría borrar la contraseña por seguridad
      setPassword('');
      setConfirmPassword('');
      const message = getAuthErrorMessage(response.error ?? '');
      showModal('error', t('common.error'), message);
    }
  };

  const handleNavigateToLogin = () => {
    // router.back() or push to / depending on history. 
    // Usually back() works if we pushed from login.
    // However, if we replace, we should use root:
    if (router.canGoBack()) {
      router.back();
    } else {
      router.replace('/');
    }
  };

  return {
    username,
    setUsername,
    email,
    setEmail,
    password,
    setPassword,
    confirmPassword,
    setConfirmPassword,
    showPassword,
    togglePasswordVisibility,
    showConfirmPassword,
    toggleConfirmPasswordVisibility,
    loading,
    handleRegister,
    handleNavigateToLogin,
    emailInputRef,
    passwordInputRef,
    confirmPasswordInputRef,
    modalVisible,
    modalConfig,
    hideModal,
  };
};

