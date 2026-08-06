import React from 'react';
import { View, Text, TextInput, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { useTheme } from '@/src/contexts/ThemeContext';
import { getAuthViewStyles } from '@/src/styles/globalStyles';
import { ThemedText } from '@/components/themed-text';
import { AuthInput } from '@/components/ui/AuthInput';
import { AuthButton } from '@/components/ui/AuthButton';
import { AppHeader } from '@/components/ui/AppHeader';
import { StatusModal } from '@/components/ui/StatusModal';
import { useTranslation } from 'react-i18next';

interface AuthViewProps {
  readonly controller: {
    readonly email: string;
    readonly setEmail: (val: string) => void;
    readonly password: string;
    readonly setPassword: (val: string) => void;
    readonly showPassword: boolean;
    readonly togglePasswordVisibility: () => void;
    readonly loading: boolean;
    readonly handleLogin: () => void;
    readonly handleNavigateToRegister: () => void;
    readonly handleResetPassword: () => void;
    readonly passwordInputRef: React.RefObject<TextInput | null>;
    readonly promptAsync: () => void;
    readonly modalVisible: boolean;
    readonly modalConfig: {
      type: 'loading' | 'success' | 'error' | 'info';
      title: string;
      message: string;
      onClose?: () => void;
    };
    readonly hideModal: () => void;
  };
}

export function AuthView({ controller }: AuthViewProps) {
  const { 
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
    hideModal
  } = controller;

  const { t } = useTranslation();
  const { theme } = useTheme();
  const styles = getAuthViewStyles(theme);

  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'} 
      style={styles.container}
    >
      <AppHeader />
      
      <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        <View style={styles.headerSection}>
          <ThemedText type="title" style={styles.title}>{t('auth.welcomeBack')}</ThemedText>
          <ThemedText style={styles.subtitle}>{t('auth.loginDesc')}</ThemedText>
        </View>
        
        <View style={styles.formContainer}>
          <AuthInput
            icon="mail-outline"
            placeholder={t('auth.email')}
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
            editable={!loading}
            returnKeyType="next"
            onSubmitEditing={() => passwordInputRef.current?.focus()}
          />
          
          <AuthInput
            ref={passwordInputRef}
            icon="lock-closed-outline"
            placeholder={t('auth.password')}
            value={password}
            onChangeText={setPassword}
            secureTextEntry={!showPassword}
            showEyeIcon
            onEyePress={togglePasswordVisibility}
            editable={!loading}
            returnKeyType="done"
            onSubmitEditing={handleLogin}
          />
          
          <AuthButton 
            title={t('auth.login')} 
            onPress={handleLogin} 
            loading={loading}
          />

          <AuthButton 
            title={t('auth.google')} 
            onPress={promptAsync} 
            variant="google"
            icon="logo-google"
            disabled={loading}
          />

          <View style={styles.actionsContainer}>
            <AuthButton 
              title={t('auth.forgotPassword')} 
              onPress={handleResetPassword} 
              variant="outline"
              style={styles.resetButton}
              textStyle={styles.resetText}
              disabled={loading}
            />

            <View style={styles.registerLink}>
              <Text style={styles.noAccountText}>{t('auth.noAccount')}</Text>
              <Text style={styles.linkText} onPress={handleNavigateToRegister}>{t('auth.register')}</Text>
            </View>
          </View>
        </View>
      </ScrollView>

      <StatusModal 
        visible={modalVisible}
        type={modalConfig.type}
        title={modalConfig.title}
        message={modalConfig.message}
        onClose={modalConfig.onClose || hideModal}
      />
    </KeyboardAvoidingView>
  );
}


