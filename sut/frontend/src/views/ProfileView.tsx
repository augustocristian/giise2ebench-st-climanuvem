import React from 'react';
import { View, Text, TextInput, ScrollView, TouchableOpacity } from 'react-native';
import { ThemeMode, useTheme } from '@/src/contexts/ThemeContext';
import { getProfileViewStyles } from '@/src/styles/globalStyles';
import { AppHeader } from '@/components/ui/AppHeader';
import { AuthButton } from '@/components/ui/AuthButton';
import { StatusModal } from '@/components/ui/StatusModal';
import { Ionicons } from '@expo/vector-icons';
import { ThemedText } from '@/components/themed-text';
import { useTranslation } from 'react-i18next';
import { LanguageMode, useLanguage } from '@/src/contexts/LanguageContext';
import type { Theme } from '@/src/styles/theme';
import type { useProfile } from '@/src/controllers/useProfile';

interface ProfileViewProps {
  readonly controller: ReturnType<typeof useProfile>;
}

type PickerOption<T extends string> = {
  value: T;
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
};

interface OptionPickerProps<T extends string> {
  readonly options: PickerOption<T>[];
  readonly value: T;
  readonly onChange: (value: T) => void;
  readonly theme: Theme;
  readonly styles: ReturnType<typeof getProfileViewStyles>;
}

const OptionPicker = <T extends string>({ options, value, onChange, theme, styles }: OptionPickerProps<T>) => (
  <View style={{ flexDirection: 'row', gap: 10 }}>
    {options.map((option) => (
      <TouchableOpacity
        key={option.value}
        style={[styles.themeButton, value === option.value && styles.themeButtonActive]}
        onPress={() => onChange(option.value)}
      >
        <Ionicons name={option.icon} size={18} color={value === option.value ? theme.colors.primary : theme.colors.textSecondary} />
        <Text style={[styles.themeButtonText, value === option.value && { color: theme.colors.primary }]}>{option.label}</Text>
      </TouchableOpacity>
    ))}
  </View>
);

const AppearanceSection = ({ theme, themeMode, setThemeMode, t, styles }: {
  theme: Theme;
  themeMode: ThemeMode;
  setThemeMode: (mode: ThemeMode) => void;
  t: (key: string) => string;
  styles: ReturnType<typeof getProfileViewStyles>;
}) => (
  <View style={styles.card}>
    <Text style={styles.sectionTitle}>{t('profile.appearance')}</Text>
    <Text style={styles.warningText}>
      {t('profile.appearanceDesc')}
    </Text>
    <OptionPicker<ThemeMode>
      theme={theme}
      styles={styles}
      value={themeMode}
      onChange={setThemeMode}
      options={[
        { value: 'light', label: t('common.light'), icon: 'sunny-outline' },
        { value: 'dark', label: t('common.dark'), icon: 'moon-outline' },
        { value: 'system', label: t('common.system'), icon: 'phone-portrait-outline' },
      ]}
    />
  </View>
);

const LanguageSection = ({ theme, languageMode, setLanguageMode, t, styles }: {
  theme: Theme;
  languageMode: LanguageMode;
  setLanguageMode: (mode: LanguageMode) => void;
  t: (key: string) => string;
  styles: ReturnType<typeof getProfileViewStyles>;
}) => (
  <View style={styles.card}>
    <Text style={styles.sectionTitle}>{t('profile.language')}</Text>
    <Text style={styles.warningText}>
      {t('profile.languageDesc')}
    </Text>
    <OptionPicker<LanguageMode>
      theme={theme}
      styles={styles}
      value={languageMode}
      onChange={setLanguageMode}
      options={[
        { value: 'en', label: t('common.english'), icon: 'language-outline' },
        { value: 'es', label: t('common.spanish'), icon: 'language-outline' },
        { value: 'system', label: t('common.system'), icon: 'phone-portrait-outline' },
      ]}
    />
  </View>
);

const DangerZoneSection = ({ confirmDeleteAccount, deleting, t, styles }: {
  confirmDeleteAccount: () => void;
  deleting: boolean;
  t: (key: string) => string;
  styles: ReturnType<typeof getProfileViewStyles>;
}) => (
  <View style={[styles.card, styles.dangerCard]}>
    <Text style={[styles.sectionTitle, styles.dangerText]}>{t('profile.dangerZone')}</Text>
    <Text style={styles.warningText}>
      {t('profile.dangerDesc')}
    </Text>
    <TouchableOpacity 
      style={styles.dangerButton} 
      onPress={confirmDeleteAccount}
      disabled={deleting}
    >
      <Ionicons name="trash-outline" size={20} color="white" />
      <Text style={styles.dangerButtonText}>{t('profile.deleteAccount')}</Text>
    </TouchableOpacity>
  </View>
);

const GuestInfoSection = ({ t, styles }: {
  t: (key: string) => string;
  styles: ReturnType<typeof getProfileViewStyles>;
}) => (
  <View style={styles.card}>
    <Text style={styles.sectionTitle}>{t('profile.guestPreferencesTitle')}</Text>
    <Text style={styles.warningText}>{t('profile.guestPreferencesDesc')}</Text>
  </View>
);

export function ProfileView({ controller }: Readonly<ProfileViewProps>) {
  const {
    userName,
    userEmail,
    newName,
    isGuest,
    setNewName,
    saving,
    deleting,
    canSaveName,
    handleUpdateName,
    confirmDeleteAccount,
    handleGoBack,
    modalVisible,
    modalConfig,
    closeModal,
  } = controller;

  const { theme, themeMode, setThemeMode } = useTheme();
  const { languageMode, setLanguageMode } = useLanguage();
  const { t } = useTranslation();
  const styles = getProfileViewStyles(theme);
  const displayName = isGuest ? t('common.guest') : userName;

  return (
    <View style={styles.container}>
      <AppHeader title={t('profile.title')} showBack={true} onBack={handleGoBack} />
      
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.avatarContainer}>
          <View style={styles.avatarCircle}>
            <Ionicons name="person" size={48} color={theme.colors.primary} />
          </View>
          <ThemedText style={styles.emailText}>
            {isGuest ? displayName : userEmail}
          </ThemedText>
        </View>

        {isGuest ? (
          <GuestInfoSection t={t} styles={styles} />
        ) : (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>{t('profile.username')}</Text>
            <TextInput
              style={styles.input}
              value={newName}
              onChangeText={setNewName}
              placeholder={t('profile.usernamePlaceholder')}
              placeholderTextColor="#999"
            />
            <View style={styles.saveAction}>
              <AuthButton
                title={saving ? t('common.saving') : t('common.save')}
                onPress={handleUpdateName}
                variant="primary"
                disabled={!canSaveName}
                textStyle={{ fontSize: 14 }}
                style={{ paddingVertical: 12, paddingHorizontal: 20 }}
              />
            </View>
          </View>
        )}

        <AppearanceSection theme={theme} themeMode={themeMode} setThemeMode={setThemeMode} t={t} styles={styles} />

        <LanguageSection theme={theme} languageMode={languageMode} setLanguageMode={setLanguageMode} t={t} styles={styles} />

        {!isGuest && (
          <DangerZoneSection confirmDeleteAccount={confirmDeleteAccount} deleting={deleting} t={t} styles={styles} />
        )}
      </ScrollView>

      <StatusModal
        visible={modalVisible}
        type={modalConfig.type}
        title={modalConfig.title}
        message={modalConfig.message}
        onClose={modalConfig.onClose || closeModal}
        onCancel={modalConfig.onCancel || closeModal}
        confirmText={modalConfig.type === 'confirm' ? t('profile.yesDelete') : undefined}
      />
    </View>
  );
}
