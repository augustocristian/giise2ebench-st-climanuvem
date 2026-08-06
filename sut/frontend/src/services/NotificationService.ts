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
        Logger.warn('Notification permissions were not granted.');
        return undefined;
      }
      
      try {
        // Get the native device push token (FCM on Android) because the backend uses firebase-admin directly
        const tokenData = await Notifications.getDevicePushTokenAsync();
        token = tokenData.data;
      } catch (error) {
        Logger.error('Error getting the device push token', error);
      }
    } else {
      Logger.info('Push notifications require a physical device.');
    }
    
    return token;
  },
};
