import React from 'react';
import { View, Text } from 'react-native';
import { useTheme } from '@/src/contexts/ThemeContext';
import { getWelcomeViewStyles } from '@/src/styles/globalStyles';
import { ThemedText } from '@/components/themed-text';
import { AuthButton } from '@/components/ui/AuthButton';
import { StatusModal, ModalType } from '@/components/ui/StatusModal';
import { useTranslation } from 'react-i18next';

interface WelcomeViewProps {
  readonly controller: {
    readonly handleNavigateToLogin: () => void;
    readonly handleContinueAsGuest: () => void;
    readonly modalVisible: boolean;
    readonly modalConfig: {
      readonly type: ModalType;
      readonly title: string;
      readonly message: string;
    };
    readonly hideModal: () => void;
  };
}

export function WelcomeView({ controller }: WelcomeViewProps) {
  const { 
    handleNavigateToLogin, 
    handleContinueAsGuest,
    modalVisible,
    modalConfig,
    hideModal,
  } = controller;

  const { t } = useTranslation();
  const { theme } = useTheme();
  const styles = getWelcomeViewStyles(theme);

  return (
    <View style={styles.container}>
      <View style={styles.overlay}>
        <View style={styles.content}>
          <View style={styles.logoContainer}>
            <Text style={styles.logoEmoji}>☁️</Text>
            <ThemedText style={styles.logoText}>ClimaNuvem</ThemedText>
          </View>
          
          <ThemedText type="title" style={styles.title}>{t('welcome.title')}</ThemedText>
          <ThemedText style={styles.subtitle}>
            {t('welcome.subtitle')}
          </ThemedText>

          <View style={styles.buttonContainer}>
            <AuthButton 
              title={t('auth.login')} 
              onPress={handleNavigateToLogin} 
              variant="primary"
              icon="log-in-outline"
            />

            <AuthButton 
              title={t('welcome.guest')} 
              onPress={handleContinueAsGuest} 
              variant="google"
              icon="person-outline"
            />
          </View>
        </View>
      </View>
      <StatusModal
        visible={modalVisible}
        type={modalConfig.type}
        title={modalConfig.title}
        message={modalConfig.message}
        onClose={hideModal}
      />
    </View>
  );
}


