import { useState } from 'react';
import { Alert } from 'react-native';
import { useTranslation } from 'react-i18next';
import { AnalysisHistoryItem, AnalysisService } from '@/src/services/AnalysisService';
import { Logger } from '@/src/services/LoggerService';

export const useAnalysisDetail = (
  analysis: AnalysisHistoryItem,
  onDeleteSuccess?: () => void,
) => {
  const { t } = useTranslation();
  const [isDeleting, setIsDeleting] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [showCancelModal, setShowCancelModal] = useState(false);

  const executeDelete = async () => {
    setShowConfirmModal(false);
    setIsDeleting(true);
    try {
      await AnalysisService.deleteAnalysis(analysis.id);
      onDeleteSuccess?.();
    } catch (error) {
      Logger.error('Error deleting analysis', error);
      Alert.alert(t('common.error'), t('analysisDetail.deleteError'));
      setIsDeleting(false);
    }
  };

  const executeCancel = async () => {
    setShowCancelModal(false);
    setIsDeleting(true);
    try {
      await AnalysisService.cancelAnalysis(analysis.id);
      onDeleteSuccess?.();
    } catch (error) {
      Logger.error('Error cancelling analysis', error);
      Alert.alert(t('common.error'), t('analysisDetail.cancelError'));
      setIsDeleting(false);
    }
  };

  return {
    isDeleting,
    showConfirmModal,
    showCancelModal,
    setShowConfirmModal,
    setShowCancelModal,
    executeDelete,
    executeCancel,
  };
};
