import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Logger } from '@/src/services/LoggerService';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldPlaySound: true,
    shouldSetBadge: false,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

export const NotificationService = {
  getPushTokenAsync: async (): Promise<string | undefined> => {
    let token;
    
    if (Device.isDevice) {
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;
      
      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }
      
      if (finalStatus !== 'granted') {
        Logger.warn('Los permisos de notificaciones no fueron concedidos.');
        return undefined;
      }
      
      try {
        // Obtenemos el device push token nativo (FCM en Android) porque el backend usa firebase-admin directamente
        const tokenData = await Notifications.getDevicePushTokenAsync();
        token = tokenData.data;
      } catch (error) {
        Logger.error('Error al obtener el push token del dispositivo', error);
      }
    } else {
      Logger.info('Las notificaciones push requieren de un dispositivo físico.');
    }
    
    return token;
  },
};
