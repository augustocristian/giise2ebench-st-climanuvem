import React from 'react';
import { View, TouchableOpacity, Text, ScrollView } from 'react-native';
import { useTheme } from '@/src/contexts/ThemeContext';
import { getHomeViewStyles } from '@/src/styles/globalStyles';
import { ThemedText } from '@/components/themed-text';
import { Ionicons } from '@expo/vector-icons';
import { AppHeader } from '@/components/ui/AppHeader';
import { useTranslation } from 'react-i18next';
import { HistoryModal } from '@/components/ui/HistoryModal';
import type { useHome } from '@/src/controllers/useHome';
import { ListActionRow } from '@/components/ui/ListActionRow';

interface HomeViewProps {
    readonly controller: ReturnType<typeof useHome>;
}

export function HomeView({ controller }: HomeViewProps) {
  const { 
    handleLogout, 
    handleNavigateToCapture,
    handleNavigateToProfile,
    historyModalVisible,
    history,
    loadingHistory,
    loadHistory,
    closeHistoryModal,
    initialSelectedAnalysisId,
    userDisplayName,
    userEmail,
    isGuest,
  } = controller;

  const { theme } = useTheme();
  const { t } = useTranslation();
  const styles = getHomeViewStyles(theme);
  const userName = isGuest ? t('common.guest') : (userDisplayName || userEmail || t('common.user'));

  return (
    <View style={styles.container}>
      <AppHeader title={t('home.title')} showBack={false} />
      
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <TouchableOpacity 
          style={styles.welcomeCard}
          onPress={handleNavigateToProfile}
          accessibilityRole="button"
          activeOpacity={0.7}
        >
          <View style={styles.welcomeHeader}>
            <View style={styles.avatarCircle}>
              <Ionicons name="person" size={32} color={theme.colors.primary} />
            </View>
            <View style={styles.welcomeTextContainer}>
              <ThemedText type="title" style={styles.title}>{t('home.welcome')}</ThemedText>
              <ThemedText style={styles.subtitle}>{userName}</ThemedText>
            </View>
            <Ionicons name="chevron-forward" size={24} color={theme.colors.border} />
          </View>
        </TouchableOpacity>

        <Text style={styles.sectionTitle}>{t('home.quickActions')}</Text>
        
        <ListActionRow
          icon="camera"
          title={t('home.analyzeImage')}
          description={t('home.analyzeDesc')}
          onPress={handleNavigateToCapture}
          iconColor={theme.colors.primary}
          iconBackgroundColor={theme.mode === 'dark' ? 'rgba(33, 150, 243, 0.1)' : '#E3F2FD'}
          chevronColor={theme.colors.border}
          cardStyle={styles.actionCard}
          iconContainerStyle={styles.iconContainer}
          textContainerStyle={styles.actionTextContainer}
          titleStyle={styles.actionTitle}
          descriptionStyle={styles.actionDescription}
        />

        <ListActionRow
          icon="list"
          title={t('home.history')}
          description={t('home.historyDesc')}
          onPress={() => loadHistory()}
          iconColor={theme.mode === 'dark' ? '#CE93D8' : '#9C27B0'}
          iconBackgroundColor={theme.mode === 'dark' ? 'rgba(156, 39, 176, 0.1)' : '#F3E5F5'}
          chevronColor={theme.colors.border}
          cardStyle={styles.actionCard}
          iconContainerStyle={styles.iconContainer}
          textContainerStyle={styles.actionTextContainer}
          titleStyle={styles.actionTitle}
          descriptionStyle={styles.actionDescription}
        />

        <TouchableOpacity style={[styles.actionCard, styles.logoutCard]} onPress={handleLogout} accessibilityRole="button">
          <View style={[styles.iconContainer, { backgroundColor: theme.mode === 'dark' ? 'rgba(244, 67, 54, 0.1)' : '#FFEBEE' }]}>
            <Ionicons name="log-out" size={28} color={theme.colors.danger} />
          </View>
          <View style={styles.actionTextContainer}>
            <Text style={[styles.actionTitle, { color: theme.colors.danger }]}>{t('home.logout')}</Text>
            <Text style={styles.actionDescription}>{t('home.logoutDesc')}</Text>
          </View>
        </TouchableOpacity>

      </ScrollView>

      <HistoryModal 
        visible={historyModalVisible}
        onClose={closeHistoryModal}
        history={history}
        loading={loadingHistory}
        onRefresh={() => loadHistory(true)}
        initialSelectedAnalysisId={initialSelectedAnalysisId}
      />
    </View>
  );
}


