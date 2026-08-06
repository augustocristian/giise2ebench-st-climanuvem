import React from 'react';
import { View, TouchableOpacity, Text } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useTheme } from '@/src/contexts/ThemeContext';
import { getAppHeaderStyles } from '@/src/styles/globalStyles';
import { useTranslation } from 'react-i18next';

interface AppHeaderProps {
  title?: string;
  showBack?: boolean;
  onBack?: () => void;
  transparent?: boolean;
}

export const AppHeader = ({ title, showBack = true, onBack, transparent }: AppHeaderProps) => {
  const { theme } = useTheme();
  const { t } = useTranslation();
  const styles = getAppHeaderStyles(theme);

  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      router.back();
    }
  };

  return (
    <View style={[styles.header, transparent && styles.transparent]}>
      {showBack && (
        <TouchableOpacity style={styles.backButton} onPress={handleBack}>
          <Ionicons name="arrow-back" size={24} color={theme.colors.primary} />
          <Text style={styles.backText}>{t('common.back')}</Text>
        </TouchableOpacity>
      )}
      {title && <Text style={[styles.title, !showBack && styles.titleCentered]}>{title}</Text>}
    </View>
  );
};


