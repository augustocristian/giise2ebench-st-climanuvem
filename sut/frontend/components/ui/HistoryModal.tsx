import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AnalysisHistoryItem } from '@/src/services/AnalysisService';
import { AnalysisDetail } from './AnalysisDetail';
import { GestureDetector, Gesture, GestureHandlerRootView } from 'react-native-gesture-handler';
import Animated, { 
  useSharedValue, 
  useAnimatedStyle, 
  withSpring, 
  interpolate
} from 'react-native-reanimated';
import { scheduleOnRN } from 'react-native-worklets';
import * as Haptics from 'expo-haptics';
import { useTheme } from '@/src/contexts/ThemeContext';
import { getHistoryModalStyles } from '@/src/styles/globalStyles';
import { formatDate, getStatusColor, getStatusText } from '@/src/utils/statusUtils';
import { useTranslation } from 'react-i18next';

interface HistoryModalProps {
  visible: boolean;
  onClose: () => void;
  history: AnalysisHistoryItem[];
  loading: boolean;
  onRefresh?: () => void;
  initialSelectedAnalysisId?: string | null;
}

const HandleBar = () => {
  const { theme } = useTheme();
  const styles = getHistoryModalStyles(theme);
  return (
    <View style={styles.handleContainer}>
      <View style={styles.handle} />
    </View>
  );
};



const RenderHistoryItem = ({ item, onSelect }: { item: AnalysisHistoryItem, onSelect: (item: AnalysisHistoryItem) => void }) => {
  const { theme } = useTheme();
  const { t, i18n } = useTranslation();
  const styles = getHistoryModalStyles(theme);
  
  return (
    <TouchableOpacity 
      style={styles.historyItem} 
      onPress={() => onSelect(item)}
    >
      <View style={styles.itemHeader}>
        <View style={styles.statusContainer}>
          <View style={[styles.statusDot, { backgroundColor: getStatusColor(item.status, theme) }]} />
          <Text style={[styles.statusText, { color: getStatusColor(item.status, theme) }]}>
            {t(`analysisDetail.${item.status}`, { defaultValue: getStatusText(item.status) })}
          </Text>
        </View>
        <Text style={styles.dateText}>{formatDate(item.date, i18n.language)}</Text>
      </View>
      <View style={styles.itemFooter}>
        <View style={styles.locationContainer}>
          {item.location && (
            <View style={styles.locationRow}>
              <Ionicons name="location-outline" size={14} color={theme.colors.textSecondary} />
              <Text style={styles.locationText}>{item.location}</Text>
            </View>
          )}
          {item.latitude != null && item.longitude != null && (
            <Text style={styles.coordsText}>{t('common.latitude')}: {item.latitude.toFixed(4)}, {t('common.longitude')}: {item.longitude.toFixed(4)}</Text>
          )}
        </View>
        <Ionicons name="chevron-forward" size={16} color={theme.colors.border} />
      </View>
    </TouchableOpacity>
  );
};

const Separator = () => {
  const { theme } = useTheme();
  const styles = getHistoryModalStyles(theme);
  return <View style={styles.separator} />;
};

interface HistoryContentProps {
  loading: boolean;
  history: AnalysisHistoryItem[];
  selectedAnalysis: AnalysisHistoryItem | null;
  setSelectedAnalysis: (item: AnalysisHistoryItem | null) => void;
  onRefresh?: () => void;
}

const HistoryContent = ({ 
  loading, 
  history, 
  selectedAnalysis, 
  setSelectedAnalysis,
  onRefresh
}: HistoryContentProps) => {
  const { theme } = useTheme();
  const { t } = useTranslation();
  const styles = getHistoryModalStyles(theme);

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Text style={styles.loadingText}>{t('common.loading')}</Text>
      </View>
    );
  }

  if (selectedAnalysis) {
    return (
      <AnalysisDetail 
        analysis={selectedAnalysis} 
        onBack={() => setSelectedAnalysis(null)} 
        onDeleteSuccess={() => {
          setSelectedAnalysis(null);
          onRefresh?.();
        }}
      />
    );
  }

  if (history.length === 0) {
    return (
      <View style={styles.centerContainer}>
        <Ionicons name="list-outline" size={48} color={theme.colors.border} />
        <Text style={styles.emptyText}>{t('analysisDetail.noList')}</Text>
      </View>
    );
  }

  return (
    <FlatList
      data={history}
      renderItem={({ item }) => <RenderHistoryItem item={item} onSelect={setSelectedAnalysis} />}
      keyExtractor={(item) => item.id}
      contentContainerStyle={styles.listContent}
      ItemSeparatorComponent={Separator}
    />
  );
};

export const HistoryModal = ({ visible, onClose, history, loading, onRefresh, initialSelectedAnalysisId }: HistoryModalProps) => {
  const { theme } = useTheme();
  const { t } = useTranslation();
  const styles = getHistoryModalStyles(theme);
  
  const [selectedAnalysis, setSelectedAnalysis] = useState<AnalysisHistoryItem | null>(null);
  const translateY = useSharedValue(0);

  React.useEffect(() => {
    if (initialSelectedAnalysisId && history.length > 0) {
      const found = history.find(a => a.id === initialSelectedAnalysisId);
      if (found) setSelectedAnalysis(found);
    }
  }, [initialSelectedAnalysisId, history]);

  const handleClose = () => {
    translateY.value = 0;
    setSelectedAnalysis(null);
    onClose();
  };

  const panGesture = Gesture.Pan()
    .onUpdate((event) => {
      'worklet';
      if (event.translationY > 0) {
        translateY.value = event.translationY;
      }
    })
    .onEnd((event) => {
      'worklet';
      if (event.translationY > 150 || event.velocityY > 500) {
        scheduleOnRN(Haptics.notificationAsync, Haptics.NotificationFeedbackType.Success);
        scheduleOnRN(handleClose);
      } else {
        translateY.value = withSpring(0, { damping: 20, stiffness: 90 });
      }
    });

  const animatedStyle = useAnimatedStyle(() => {
    return {
      transform: [{ translateY: translateY.value }],
    };
  });

  const backdropStyle = useAnimatedStyle(() => {
    const opacity = interpolate(
      translateY.value,
      [0, 300],
      [0.5, 0],
      'clamp'
    );
    return {
      backgroundColor: `rgba(0,0,0,${opacity})`,
    };
  });

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={() => {
        if (selectedAnalysis) {
          setSelectedAnalysis(null);
        } else {
          handleClose();
        }
      }}
    >
      <GestureHandlerRootView style={{ flex: 1 }}>
        <Animated.View style={[styles.overlay, backdropStyle]}>
          <Animated.View style={[styles.modalContainer, animatedStyle]}>
            <GestureDetector gesture={panGesture}>
              <View style={styles.gestureHeader}>
                <HandleBar />
                {!selectedAnalysis && (
                  <View style={styles.header}>
                    <Text style={styles.title}>{t('home.history')}</Text>
                    <View style={styles.headerActions}>
                      {onRefresh && (
                        <TouchableOpacity onPress={onRefresh} style={styles.actionButton} disabled={loading}>
                          <Ionicons name="refresh" size={24} color={loading ? theme.colors.textSecondary : theme.colors.text} />
                        </TouchableOpacity>
                      )}
                      <TouchableOpacity onPress={onClose} style={styles.actionButton}>
                        <Ionicons name="close" size={24} color={theme.colors.text} />
                      </TouchableOpacity>
                    </View>
                  </View>
                )}
              </View>
            </GestureDetector>

            <HistoryContent 
              loading={loading}
              history={history}
              selectedAnalysis={selectedAnalysis}
              setSelectedAnalysis={setSelectedAnalysis}
              onRefresh={onRefresh}
            />
          </Animated.View>
        </Animated.View>
      </GestureHandlerRootView>
    </Modal>
  );
};
