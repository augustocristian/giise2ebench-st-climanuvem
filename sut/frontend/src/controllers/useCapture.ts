import { useState } from 'react';
import { DeviceEventEmitter } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { router } from 'expo-router';
import { AnalysisService } from '@/src/services/AnalysisService';
import { Logger } from '@/src/services/LoggerService';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useTranslation } from 'react-i18next';
import { useStatusModal } from '@/src/hooks/useStatusModal';
import {
  getFCMToken,
  getImageSize,
  getLocationData,
  IMAGE_TOO_LARGE_CODE,
  MAX_IMAGE_SIZE_BYTES,
  optimizeImage,
  validateIsJpg,
} from '@/src/utils/captureUtils';

export const useCapture = () => {
  const { t } = useTranslation();
  
  // Estado para explicabilidad
  const [includeExplainability, setIncludeExplainability] = useState(false);
  const { modalVisible, modalConfig, showModal, hideModal } = useStatusModal();

  const pickImage = async (source: 'camera' | 'gallery') => {
    const permission = source === 'camera'
      ? await ImagePicker.requestCameraPermissionsAsync()
      : await ImagePicker.requestMediaLibraryPermissionsAsync();
    
    if (permission.status !== 'granted') {
      showModal(
        'error', 
        t('auth.permissionDenied'), 
        source === 'camera' ? t('auth.cameraPermissionRequired') : t('auth.galleryPermissionRequired'),
        () => router.replace('/' as any),
      );
      return;
    }

    const pickerOptions = {
      mediaTypes: ['images'] as ImagePicker.MediaType[],
      allowsEditing: false,
      quality: 1,
    };
    const result = source === 'camera'
      ? await ImagePicker.launchCameraAsync(pickerOptions)
      : await ImagePicker.launchImageLibraryAsync(pickerOptions);

    if (!result.canceled) {
      void processImage(result.assets[0].uri);
    }
  };

  const handleCameraCapture = async () => pickImage('camera');

  const handleGallerySelection = async () => pickImage('gallery');

  const validateImageSize = (uri: string) => {
    try {
      const fileSize = getImageSize(uri);
      if (fileSize == null) {
        showModal('error', t('common.error'), t('capture.uploadError'));
        return false;
      }

      if (fileSize > MAX_IMAGE_SIZE_BYTES) {
        showModal('error', t('common.error'), t('capture.imageTooLarge'));
        return false;
      }
    } catch (error) {
      Logger.warn('No se pudo validar el tamaño de la imagen antes de subirla', error);
    }
    return true;
  };

  const processImage = async (uri: string) => {
    if (!validateIsJpg(uri)) {
      showModal('error', t('auth.invalidFormat'), t('auth.invalidJpg'));
      return;
    }

    const isSizeValid = validateImageSize(uri);
    if (!isSizeValid) {
      return;
    }

    const hasSeenPrompt = await AsyncStorage.getItem('hasSeenPermissionPrompt');
    if (hasSeenPrompt) {
      await continueProcessing(uri);
    } else {
      showModal(
        'confirm',
        t('auth.betterExperience'),
        t('auth.permissionPrompt'),
        async () => {
          await AsyncStorage.setItem('hasSeenPermissionPrompt', 'true');
          await continueProcessing(uri);
        },
        () => {
          hideModal();
        }
      );
    }
  };

  const continueProcessing = async (uri: string) => {
    showModal('loading', t('capture.obtainingLocation'), t('common.wait'));
    const { locationStr, latitude, longitude } = await getLocationData({
      unknownLocation: t('capture.unknownLocation'),
      unknownCity: t('capture.unknownCity'),
      unknownCountry: t('capture.unknownCountry'),
    });

    showModal('loading', t('capture.preparingUpload'), t('capture.obtainingNotifications'));
    const fcmToken = await getFCMToken();

    showModal('loading', t('capture.preparingImage'), t('capture.optimizingFormat'));
    const processedUri = await optimizeImage(uri);

    showModal('loading', t('capture.uploadingImage'), t('capture.secondsWait'));
    try {
      await AnalysisService.uploadImage(processedUri, locationStr, latitude, longitude, fcmToken, includeExplainability);
      DeviceEventEmitter.emit('refresh_history');
      showModal(
        'success',
        t('capture.imageSent'),
        t('capture.imageSentDesc'),
        () => {
          hideModal();
          router.back();
        }
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : '';
      if (message === IMAGE_TOO_LARGE_CODE) {
        showModal('error', t('common.error'), t('capture.imageTooLarge'));
      } else {
        showModal('error', t('common.error'), message || t('capture.uploadError'));
      }
      Logger.error('Error al subir imagen para análisis', error);
    }
  };

  return {
    handleCameraCapture,
    handleGallerySelection,
    modalVisible,
    modalConfig,
    hideModal,
    includeExplainability,
    setIncludeExplainability,
  };
};
