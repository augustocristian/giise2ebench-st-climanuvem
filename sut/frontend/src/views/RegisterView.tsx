import React from 'react';
import { View, Text, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { useTheme } from '@/src/contexts/ThemeContext';
import { getRegisterViewStyles } from '@/src/styles/globalStyles';
import { ThemedText } from '@/components/themed-text';
import { AuthInput } from '@/components/ui/AuthInput';
import { AuthButton } from '@/components/ui/AuthButton';
import { AppHeader } from '@/components/ui/AppHeader';
import { StatusModal } from '@/components/ui/StatusModal';
import { useTranslation } from 'react-i18next';
import type { useRegister } from '@/src/controllers/useRegister';

interface RegisterViewProps {
  readonly controller: ReturnType<typeof useRegister>;
}

export function RegisterView({ controller }: RegisterViewProps) {
  const { 
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
    hideModal
  } = controller;

  const { t } = useTranslation();
  const { theme } = useTheme();
  const styles = getRegisterViewStyles(theme);

  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'} 
      style={styles.container}
    >
      <AppHeader onBack={handleNavigateToLogin} />
      
      <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        <View style={styles.headerSection}>
          <ThemedText type="title" style={styles.title}>{t('auth.createAccount')}</ThemedText>
          <ThemedText style={styles.subtitle}>{t('auth.registerDesc')}</ThemedText>
        </View>
        
        <View style={styles.formContainer}>
          <AuthInput
            icon="person-outline"
            placeholder={t('auth.username')}
            value={username}
            onChangeText={setUsername}
            autoCapitalize="none"
            editable={!loading}
            maxLength={20}
            returnKeyType="next"
            onSubmitEditing={() => emailInputRef.current?.focus()}
          />

          <AuthInput
            ref={emailInputRef}
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
            returnKeyType="next"
            onSubmitEditing={() => confirmPasswordInputRef.current?.focus()}
          />

          <AuthInput
            ref={confirmPasswordInputRef}
            icon="shield-checkmark-outline"
            placeholder={t('auth.confirmPassword')}
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            secureTextEntry={!showConfirmPassword}
            showEyeIcon
            onEyePress={toggleConfirmPasswordVisibility}
            editable={!loading}
            returnKeyType="done"
            onSubmitEditing={handleRegister}
          />
          
          <AuthButton 
            title={t('auth.doRegister')} 
            onPress={handleRegister} 
            loading={loading}
            style={styles.registerButton}
          />

          <View style={styles.loginLink}>
            <Text style={styles.alreadyHaveAccountText}>{t('auth.haveAccount')}</Text>
            <Text style={styles.linkText} onPress={handleNavigateToLogin}>{t('auth.doLogin')}</Text>
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


