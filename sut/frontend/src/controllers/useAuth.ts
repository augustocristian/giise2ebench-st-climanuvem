import { useState, useRef, useEffect } from 'react';
import { router } from 'expo-router';
import { TextInput, Platform } from 'react-native';
import { AuthService } from '@/src/services/AuthService';
import { EMAIL_REGEX, getAuthErrorMessage } from '@/src/utils/authUtils';
import { Logger } from '@/src/services/LoggerService';
import { useTranslation } from 'react-i18next';

import { GoogleSignin } from '@react-native-google-signin/google-signin';


export const useAuth = () => {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  // Estado para el modal de estado (moderno)
  const [modalVisible, setModalVisible] = useState(false);
  const [modalConfig, setModalConfig] = useState<{
    type: 'loading' | 'success' | 'error' | 'info';
    title: string;
    message: string;
    onClose?: () => void;
  }>({
    type: 'loading',
    title: '',
    message: '',
  });

  const showModal = (type: 'loading' | 'success' | 'error' | 'info', title: string, message: string, onClose?: () => void) => {
    setModalConfig({ type, title, message, onClose });
    setModalVisible(true);
  };

  const hideModal = () => {
    setModalVisible(false);
  };

  // Configuración de Google Sign-In Nativo
  useEffect(() => {
    if (GoogleSignin && Platform.OS !== 'web') {
      try {
        GoogleSignin.configure({
          webClientId: '404226456428-6kqoq5ic42g0g4k0qe9cur5qt85spu25.apps.googleusercontent.com',
        });
      } catch (error) {
        Logger.error('Error al configurar Google Sign-in', error);
      }
    }
  }, []);

  const promptAsync = async () => {
    if (!GoogleSignin) {
      showModal('error', t('auth.googleNotAvailable'), t('auth.googleNotAvailableDesc'));
      return;
    }

    try {
      await GoogleSignin.hasPlayServices();
      const userInfo = await GoogleSignin.signIn();
      const idToken = userInfo.data?.idToken;
      
      if (idToken) {
        handleGoogleLogin(idToken);
      } else {
        showModal('error', t('common.error'), t('auth.googleErrorDesc'));
      }
    } catch (error: any) {
      Logger.error('Error Google Native', error);
      // Manejar cancelaciones o errores específicos si es necesario
      if (error.code !== 'SIGN_IN_CANCELLED') {
        showModal('error', t('auth.googleError'), t('auth.googleErrorDesc'));
      }
    }
  };

  const handleGoogleLogin = async (idToken: string) => {
    setLoading(true);
    const result = await AuthService.loginWithGoogle(idToken);
    setLoading(false);

    if (result.success) {
      router.replace('/home' as any);
    } else {
      const message = getAuthErrorMessage(result.error ?? '');
      showModal('error', t('auth.googleError'), message);
    }
  };

  // Creamos una referencia para poder apuntar al campo de contraseña
  const passwordInputRef = useRef<TextInput>(null);

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const handleLogin = async () => {
    // Validar formato de email
    if (!EMAIL_REGEX.test(email)) {
      showModal('error', t('common.error'), t('auth.invalidEmail'));
      return;
    }

    setLoading(true);

    const response = await AuthService.login(email, password);

    setLoading(false);

    if (response.success) {
      router.replace('/home' as any);
    } else {
      setPassword('');
      const message = getAuthErrorMessage(response.error ?? '');
      showModal('error', t('common.error'), message);
    }
  };

  const handleNavigateToRegister = () => {
    // @ts-ignore typed routes latency
    router.push('/register');
  };

  const handleResetPassword = async () => {
    if (!email) {
      showModal('error', t('common.error'), t('auth.resetPasswordFirst'));
      return;
    }

    if (!EMAIL_REGEX.test(email)) {
      showModal('error', t('common.error'), t('auth.invalidEmail'));
      return;
    }

    setLoading(true);
    const response = await AuthService.resetPassword(email);
    setLoading(false);

    if (response.success) {
      showModal(
        'success',
        t('auth.emailSent'),
        t('auth.resetPasswordEmailSent')
      );
    } else {
      const message = getAuthErrorMessage(response.error ?? '');
      showModal('error', t('auth.resetError'), message);
    }
  };

  return {
    email,
    setEmail,
    password,
    setPassword,
    showPassword,
    togglePasswordVisibility,
    loading,
    handleLogin,
    handleNavigateToRegister,
    handleResetPassword,
    passwordInputRef,
    promptAsync,
    modalVisible,
    modalConfig,
    hideModal,
  };
};

