import React from 'react';
import { View, Text, ScrollView, Switch } from 'react-native';
import { useTheme } from '@/src/contexts/ThemeContext';
import { getCaptureViewStyles } from '@/src/styles/globalStyles';
import { ThemedText } from '@/components/themed-text';
import { Ionicons } from '@expo/vector-icons';
import { AppHeader } from '@/components/ui/AppHeader';
import { StatusModal } from '@/components/ui/StatusModal';
import { useTranslation } from 'react-i18next';
import { ListActionRow } from '@/components/ui/ListActionRow';
import type { useCapture } from '@/src/controllers/useCapture';

interface CaptureViewProps {
  readonly controller: ReturnType<typeof useCapture>;
}

export function CaptureView({ controller }: CaptureViewProps) {
  const { 
    handleCameraCapture, 
    handleGallerySelection,
    modalVisible,
    modalConfig,
    hideModal,
    includeExplainability,
    setIncludeExplainability
  } = controller;

  const { theme } = useTheme();
  const { t } = useTranslation();
  const styles = getCaptureViewStyles(theme);

  return (
    <View style={styles.container}>
      <AppHeader title={t('capture.analyze')} />
      
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.illustrationContainer}>
          <View style={styles.illustrationCircle}>
            <Ionicons name="cloud-upload-outline" size={80} color={theme.colors.primary} />
          </View>
        </View>

        <ThemedText style={styles.subtitle}>
          {t('capture.subtitle')}
        </ThemedText>

        <View style={styles.optionsContainer}>
          <ListActionRow
            icon="camera"
            title={t('capture.title')}
            description={t('capture.cameraDesc')}
            onPress={handleCameraCapture}
            iconColor={theme.colors.primary}
            iconBackgroundColor={theme.mode === 'dark' ? 'rgba(33, 150, 243, 0.1)' : '#E3F2FD'}
            chevronColor={theme.colors.primary}
            size={32}
            cardStyle={styles.optionCard}
            iconContainerStyle={styles.iconCircle}
            textContainerStyle={styles.optionTextContainer}
            titleStyle={styles.optionTitle}
            descriptionStyle={styles.optionDescription}
          />

          <ListActionRow
            icon="image"
            title={t('capture.gallery')}
            description={t('capture.galleryDesc')}
            onPress={handleGallerySelection}
            iconColor={theme.mode === 'dark' ? '#CE93D8' : '#9C27B0'}
            iconBackgroundColor={theme.mode === 'dark' ? 'rgba(156, 39, 176, 0.1)' : '#F3E5F5'}
            chevronColor={theme.mode === 'dark' ? '#CE93D8' : '#9C27B0'}
            size={32}
            cardStyle={styles.optionCard}
            iconContainerStyle={styles.iconCircle}
            textContainerStyle={styles.optionTextContainer}
            titleStyle={styles.optionTitle}
            descriptionStyle={styles.optionDescription}
          />
        </View>

        <View style={[styles.optionCard, { paddingVertical: 12, marginTop: 16, flexDirection: 'column', alignItems: 'stretch' }]}>
          <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
              <View style={[styles.iconCircle, { backgroundColor: theme.mode === 'dark' ? 'rgba(255, 152, 0, 0.1)' : '#FFF3E0', width: 40, height: 40, marginRight: 12 }]}>
                <Ionicons name="eye" size={20} color="#FF9800" />
              </View>
              <View>
                <Text style={[styles.optionTitle, { fontSize: 16 }]}>{t('capture.explainabilityName')}</Text>
                <Text style={[styles.optionDescription, { fontSize: 12 }]}>{t('capture.explainability')}</Text>
              </View>
            </View>
            <Switch
              value={includeExplainability}
              onValueChange={setIncludeExplainability}
              trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
              thumbColor="#fff"
            />
          </View>
          {includeExplainability && (
            <View style={{ marginTop: 12, padding: 8, backgroundColor: theme.mode === 'dark' ? 'rgba(244, 67, 54, 0.1)' : '#FFEBEE', borderRadius: 8, flexDirection: 'row', alignItems: 'center' }}>
              <Ionicons name="warning" size={16} color={theme.colors.danger} style={{ marginRight: 8 }} />
              <Text style={{ color: theme.colors.danger, fontSize: 11, flex: 1 }}>
                {t('capture.explainabilityWarning')}
              </Text>
            </View>
          )}
        </View>

        <View style={styles.infoBox}>
          <Ionicons name="information-circle-outline" size={20} color={theme.colors.textSecondary} style={{marginRight: 8}} />
          <View style={{ flex: 1 }}>
            <Text style={styles.infoText}>{t('capture.formatInfo')}</Text>
            <Text style={styles.infoText}>{t('capture.maxSizeInfo')}</Text>
          </View>
        </View>
      </ScrollView>

      <StatusModal 
        visible={modalVisible}
        type={modalConfig.type}
        title={modalConfig.title}
        message={modalConfig.message}
        onClose={modalConfig.onClose || hideModal}
        onCancel={modalConfig.onCancel || hideModal}
      />
    </View>
  );
}

